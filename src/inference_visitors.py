from langchain_ollama import ChatOllama
from typing import List
import json
import os
from src.classes import LLama_PromptTemplate
import random
from src.conf import merged_data_json, merged_data_status_json, cat_examples_json
from src.conf import (
    nomenclature,
    input_data_folder,
    classification_data_folder,
    output_data_folder,
)
import logging


def classify_visitors_sequencial(
    root_dir: str,
    config: dict,
    num_samples: int = 100000000,
    model: str = "llama3.1:latest",
    temperature: float = 0.5,
    top_p: float = 0.9,
    top_k: int = 30,
    repetition_penalty: float = 1.1,
    do_sample: bool = True,
    num_ctx: int = 16184,
    format: str = "json",
    base_url: List[str] = ["http://localhost:11434", "http://localhost:11435"],
    include_examples: bool = True,
    timestamp_str: str = None,
    create_files: str = "no",
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

    llm = ChatOllama(
        model=model,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        do_sample=num_ctx,
        num_ctx=num_ctx,
        format=format,
        base_url=base_url[0],
    )

    logging.info(f"Model: {model}")
    logging.info(f"Temperature: {temperature}")
    logging.info(f"Top P: {top_p}")
    logging.info(f"Top K: {top_k}")
    logging.info(f"Repetition Penalty: {repetition_penalty}")
    logging.info(f"Do Sample: {do_sample}")
    logging.info(f"Number of Context: {num_ctx}")
    logging.info(f"Format: {format}")

    logging.info(f"Base URL: {base_url[0]}")
    csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

    include_examples = True

    list_profiles = list(merged_data.keys())
    list_profiles_status = list(merged_data_status.keys())
    random.shuffle(list_profiles)

    logging.info(f"Number of profiles: {len(list_profiles)}")
    list_profiles = list_profiles[:num_samples]
    output = []
    for p in list_profiles:
        profile = merged_data.get(p)
        status = merged_data_status.get(p)
        if status == "Enought_data":

            profile_template = csm_template_2.generate_clustering_prompt(
                profile, include_examples=include_examples
            )
            logging.info(f"length of profile: {len(profile_template)}")
            # If you want to see send the  prompt to the model uncomment the next 4 lines
            if create_files == "no":
                ai_msg = llm.invoke(profile_template)
                output.append(
                    {"profile_id": p, "response": ai_msg.content, "input": profile}
                )
                logging.info(f"Profile: {p} Category : {ai_msg.content}")
                logging.info("-" * 100)
            elif create_files == "yes":
                ### Next two lines are commented out to avoid calling the API
                response = json.dumps(
                    {"category": status, "ranked_categories": "NA", "certainty": "NA"}
                )
                output.append({"profile_id": p, "response": response, "input": profile})

        else:
            logging.info(f"Profile: {p} Status: {status}")
            logging.info("-" * 100)
            response = json.dumps(
                {"category": status, "ranked_categories": "NA", "certainty": "NA"}
            )
            output.append({"profile_id": p, "response": response, "input": profile})

    model = model.split(":")[0]
    model = model.replace(".", "_")
    if bool(include_examples):
        filename = os.path.join(
            root_dir,
            input_data_folder,
            classification_data_folder,
            f"{model}_{post_event_process}_{include_previous_scan_data}_{timestamp_str}.json",
        )
    else:
        filename = os.path.join(
            root_dir,
            input_data_folder,
            classification_data_folder,
            f"{model}_{post_event_process}_{include_previous_scan_data}_noexamples_{timestamp_str}.json",
        )
    logging.info(f"Saving output to {filename}")
    with open(filename, "w") as f:
        json.dump(output, f, indent=4)

    return
