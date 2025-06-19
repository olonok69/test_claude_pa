from openai import AzureOpenAI
import json
import os
from src.classes import LLama_PromptTemplate
from typing import List
import time
import datetime
import random
from src.conf import (
    merged_data_json,
    merged_data_status_json,
    input_data_folder,
    batch_data_folder,
    classification_data_folder,
    cat_examples_json,
    nomenclature,
    output_data_folder,
)
from src.conf import nomenclature
import logging
import sys
import traceback


def print_stack():
    # cath exception with sys and return the error stack

    ex_type, ex_value, ex_traceback = sys.exc_info()
    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)

    # Format stacktrace
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )

    error = ex_type.__name__ + "\n" + str(ex_value) + "\n"
    for err in stack_trace:
        error = error + str(err) + "\n"

    return error


def create_chunks(input_file, max_chunk_size, output_dir):
    """
    Create Chunks
    Args:
    input_file: str: Input File
    max_chunk_size: int: Max Chunk Size
    output_dir: str: Output Directory
    return: list: List of Files
    """

    with open(input_file, "r") as file:
        chunk_index = 0
        current_chunk_size = 0
        current_chunk = []
        list_files = []
        for line in file:
            line_size = len(line.encode("utf-8"))  # Get the size of the line in bytes

            # Check if adding this line exceeds the max chunk size
            if current_chunk_size + line_size > max_chunk_size:
                # Write the current chunk to a new file
                filename = f"chunk_{chunk_index}.jsonl"
                list_files.append(filename)
                chunk_filename = os.path.join(output_dir, filename)

                with open(chunk_filename, "w") as chunk_file:
                    chunk_file.writelines(current_chunk)

                logging.info(
                    f"Created: {chunk_filename} ({current_chunk_size / (1024 * 1024):.2f} MB)"
                )

                # Reset for the next chunk
                chunk_index += 1
                current_chunk_size = 0
                current_chunk = []

            # Add the current line to the chunk
            current_chunk.append(line)
            current_chunk_size += line_size

        # Write the final chunk if it has data
        if current_chunk:
            filename = f"chunk_{chunk_index}.jsonl"
            list_files.append(filename)
            chunk_filename = os.path.join(output_dir, filename)
            with open(chunk_filename, "w") as chunk_file:
                chunk_file.writelines(current_chunk)

            logging.info(
                f"Created: {chunk_filename} ({current_chunk_size / (1024 * 1024):.2f} MB)"
            )
    return list_files


def process_batch(
    root_dir: str,
    records: List[dict],
    output: List[dict],
    client: AzureOpenAI,
    merged_data: dict,
):
    """
    Process Batch
    Args:
    root_dir: str: Root Directory
    records: List[dict]: Records
    output: List[dict]: Output
    client: AzureOpenAI: Azure OpenAI
    merged_data: dict: Merged Data"""
    ## Write JSONL file and upload to Azure Batch API
    # Filepath for the JSONL file
    file_path = os.path.join(
        root_dir, input_data_folder, batch_data_folder, "records.jsonl"
    )
    logging.info(f"File Path: {file_path}")
    # Writing records to the JSONL file
    with open(file_path, "w") as file:
        for record in records:
            file.write(f"{json.dumps(record)}\n")

    # Upload a file with a purpose of "batch" Uncomment this line to upload the file
    file = client.files.create(file=open(file_path, "rb"), purpose="batch")

    # FILE ID
    file_id = file.id
    logging.info(f"File ID: {file_id}")

    ### Create a batch job
    # Submit a batch job with the file
    batch_response = client.batches.create(
        input_file_id=file_id,
        endpoint="/chat/completions",
        completion_window="24h",
    )

    # Save batch ID for later use
    batch_id = batch_response.id
    logging.info(f"Batch ID: {batch_id}")

    status = "validating"
    while status not in ("completed", "failed", "canceled"):
        time.sleep(60)
        batch_response = client.batches.retrieve(batch_id)
        status = batch_response.status
        logging.info(
            f"{datetime.datetime.now()} Batch Id: {batch_id},  Status: {status}"
        )

    if batch_response.status == "failed":
        for error in batch_response.errors.data:
            logging.error(f"Error code {error.code} Message {error.message}")

    # Get the output file ID and extracting Responses

    output_file_id = batch_response.output_file_id
    logging.info(f"Output File ID: {output_file_id}")

    if not output_file_id:
        output_file_id = batch_response.error_file_id

    if output_file_id:
        file_response = client.files.content(output_file_id)
        raw_responses = file_response.text.strip().split("\n")

        for raw_response in raw_responses:
            json_response = json.loads(raw_response)
            # formatted_json = json.dumps(json_response, indent=2)
            response = json.loads(
                json_response.get("response")["body"]["choices"][0]["message"][
                    "content"
                ]
            )
            p = json_response["custom_id"].split("-")[-1]
            profile = merged_data.get(p)
            output.append({"profile_id": p, "response": response, "input": profile})
    return output


def send_chunks_to_batch(
    root_dir: str,
    chunk_files: List[str],
    output: List[dict],
    client: AzureOpenAI,
    merged_data: dict,
):
    """
    Sends JSONL chunks to the Azure Batch API
    Args:
        root_dir: str: Root directory containing JSONL chunks
        chunk_files: List[str]: List of chunk filenames
        output: List[dict]: List to store the outputs
        client: AzureOpenAI: Azure OpenAI client instance
        merged_data: dict: Data to merge with the response
    """
    for filename in chunk_files:
        try:
            # Get the full path for the chunk file
            file_path = os.path.join(root_dir, filename)
            logging.info(f"Processing file: {file_path}")

            # Upload the JSONL file to Azure Batch API
            file = client.files.create(file=open(file_path, "rb"), purpose="batch")
            file_id = file.id
            logging.info(f"Uploaded file. File ID: {file_id}")

            # Submit a batch job
            batch_response = client.batches.create(
                input_file_id=file_id,
                endpoint="/chat/completions",
                completion_window="24h",
            )
            batch_id = batch_response.id
            logging.info(f"Batch job created. Batch ID: {batch_id}")

            # Monitor the batch job status
            status = "validating"
            while status not in ("completed", "failed", "canceled"):
                time.sleep(60)  # Wait for 60 seconds before checking the status again
                batch_response = client.batches.retrieve(batch_id)
                status = batch_response.status
                logging.info(
                    f"{datetime.datetime.now()} Batch ID: {batch_id}, Status: {status}"
                )

            # Handle failure case
            if batch_response.status == "failed":
                for error in batch_response.errors.data:
                    logging.error(f"Error code {error.code}, Message: {error.message}")
                continue

            # Extract responses
            output_file_id = batch_response.output_file_id
            logging.info(f"Output File ID: {output_file_id}")

            if not output_file_id:
                output_file_id = batch_response.error_file_id

            if output_file_id:
                file_response = client.files.content(output_file_id)
                raw_responses = file_response.text.strip().split("\n")

                for raw_response in raw_responses:

                    try:
                        json_response = json.loads(raw_response)

                    except json.JSONDecodeError:
                        error = print_stack()
                        logging.error(f"Invalid JSON: {raw_response},  {str(error)}")
                        continue
                    # get output of the model
                    response = json_response.get("response")["body"]["choices"][0][
                        "message"
                    ]["content"]
                    # Get Id_visitor
                    custom_id = json_response["custom_id"].split("-")[-1]
                    # get the profile
                    profile = merged_data.get(custom_id)
                    output.append(
                        {
                            "profile_id": custom_id,
                            "response": response,
                            "input": profile,
                        }
                    )
            # chunk remove

        except Exception as e:
            error = print_stack()
            logging.error(f"Error processing file {filename}: {str(error)}")

    return output


def classify_visitors_sequencial_batch(
    root_dir: str,
    config: dict,
    num_samples: int = 100000000,
    model: str = "gpt-4o-mini-2",
    temperature: float = 0.5,
    top_p: float = 0.9,
    top_k: int = 30,
    repetition_penalty: float = 1.1,
    do_sample: bool = True,
    num_ctx: int = 16184,
    format: str = "json",
    include_examples: bool = True,
    timestamp_str: str = None,
    create_files: str = "no",
    max_chunk_size: int = 100,
    post_event_process: str = "no",
    include_previous_scan_data: str = "no",
):
    """
    Classify Visitors
    Args:
    root_dir: str: Root Directory
    config: dict: Configuration
    num_samples: int: Number of Samples
    model: str: Model
    temperature: float: Temperature
    top_p: float: Top P
    top_k: int: Top K
    repetition_penalty: float: Repetition Penalty
    do_sample: bool: Do Sample
    num_ctx: int: Number of Context
    format: str: Format
    base_url: List[str]: Base URL
    include_examples: bool: Include Examples
    timestamp_str: str: Timestamp
    create_files: str: Flag to create files
    """
    # Paths
    examples_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, cat_examples_json
    )
    merger_data_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, merged_data_json
    )
    merger_data_status_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, merged_data_status_json
    )

    # OPEN FILES
    with open(examples_path, "r") as f:
        examples = json.load(f)
    with open(merger_data_path, "r") as f:
        merged_data = json.load(f)
    with open(merger_data_status_path, "r") as f:
        merged_data_status = json.load(f)

    # "llama3.1:latest"

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_ENDPOINT"],
        api_key=os.environ["AZURE_API_KEY"],
        api_version=os.environ["AZURE_API_VERSION_BATCH"],
    )

    azure_deployment = model

    logging.info(f"Client: {client}")
    logging.info(f"Azure Deployment: {azure_deployment}")
    csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

    include_examples = True

    list_profiles = list(merged_data.keys())
    list_profiles_status = list(merged_data_status.keys())
    random.shuffle(list_profiles)

    logging.info(f"Number of profiles: {len(list_profiles)}")
    list_profiles = list_profiles[:num_samples]
    output = []
    #### MEssage format ####
    # {"custom_id": "task-0",
    # "method": "POST",
    # "url": "/chat/completions",
    # "body": {"model": "REPLACE-WITH-MODEL-DEPLOYMENT-NAME",
    #           "messages": [{"role": "system", "content": "You are an AI assistant that helps people find information."},
    #               {"role": "user", "content": "When was Microsoft founded?"}]}}
    #

    ### Create JSONL for Batch API
    records = []
    for p, i in zip(list_profiles, range(len(list_profiles))):
        profile = merged_data.get(p)
        status = merged_data_status.get(p)
        if status == "Enought_data":

            profile_template = csm_template_2.generate_clustering_prompt(
                profile, include_examples=include_examples
            )
            logging.info(f"length of profile: {len(profile_template)}")
            # If you want to see send the  prompt to the model uncomment the next 4 lines
            if create_files == "no":
                system_prompt = csm_template_2.generate_llama_prompt()
                logging.info(f"length of profile {p}: {len(profile)}")
                prompt = {
                    "custom_id": f"task-{p}",
                    "method": "POST",
                    "url": "/chat/completions",
                    "body": {
                        "model": azure_deployment,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": profile},
                        ],
                    },
                }

                records.append(prompt)
                logging.info("-" * 100)
            elif create_files == "yes":
                ### Next two lines are commented out to avoid calling the API
                response = json.dumps(
                    {"category": status, "ranked_categories": "NA", "certainty": "NA"}
                )
                output.append({"profile_id": p, "response": response, "input": profile})

        else:
            # if status != "Enought_data": simply introduce the profile to the output
            logging.info(f"Profile: {p} Status: {status}")
            logging.info("-" * 100)
            response = json.dumps(
                {"category": status, "ranked_categories": "NA", "certainty": "NA"}
            )
            output.append({"profile_id": p, "response": response, "input": profile})

    # Send Batch API
    if create_files == "no":
        file_path = os.path.join(
            root_dir, input_data_folder, batch_data_folder, "records.jsonl"
        )
        logging.info(f"File Path: {file_path}")
        # Writing records to the JSONL file
        with open(file_path, "w") as file:
            for record in records:
                file.write(f"{json.dumps(record)}\n")

        # Directory to store output chunks
        chuncks_output_dir = os.path.join(
            root_dir, input_data_folder, batch_data_folder, "jsonl_chunks"
        )
        # Maximum chunk size in bytes (100MB)
        max_chunk_size = max_chunk_size * 1024 * 1024  # 100 MB
        os.makedirs(chuncks_output_dir, exist_ok=True)

        chunk_files = create_chunks(file_path, max_chunk_size, chuncks_output_dir)

        output = send_chunks_to_batch(
            root_dir=chuncks_output_dir,
            chunk_files=chunk_files,
            output=output,
            client=client,
            merged_data=merged_data,
        )
        # output = process_batch(root_dir, records, output, client, merged_data)

    if bool(include_examples):
        filename = os.path.join(
            root_dir,
            input_data_folder,
            classification_data_folder,
            f"{azure_deployment}_{post_event_process}_{include_previous_scan_data}_{timestamp_str}.json",
        )
    else:
        filename = os.path.join(
            root_dir,
            input_data_folder,
            classification_data_folder,
            f"{azure_deployment}_{post_event_process}_{include_previous_scan_data}_noexamples_{timestamp_str}.json",
        )
    logging.info(f"Saving output to {filename}")
    with open(filename, "w") as f:
        json.dump(output, f, indent=4)

    return
