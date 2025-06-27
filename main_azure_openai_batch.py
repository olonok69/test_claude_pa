from openai import AzureOpenAI

import json
import os
from src.classes import LLama_PromptTemplate
import time
import datetime
import random
from src.conf import (
    merged_data_json,
    merged_data_status_json,
    input_data_folder,
    batch_data_folder,
    classification_data_folder,
)
from src.conf import nomenclature
from dotenv import dotenv_values, load_dotenv
from IPython import embed
import shutil
from pathlib import Path
from detectaicore import set_up_logging
import logging

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set up logging
LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
dirpath = Path(LOGS_PATH)
if dirpath.exists() and dirpath.is_dir():
    shutil.rmtree(dirpath)
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)

timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
script_name = os.path.join(LOGS_PATH, f"debug_{timestamp_str}.log")
# create loggers
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="info",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] - %(filename)s:%(lineno)d - %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")


examples_path = os.path.join(ROOT_DIR, "csm_data", "output", "cat_examples.json")
merger_data_path = os.path.join(ROOT_DIR, "csm_data", "output", merged_data_json)
merger_data_status_path = os.path.join(
    ROOT_DIR, "csm_data", "output", merged_data_status_json
)


def calculate_cost(ai_msg):
    tokens_used = ai_msg.usage_metadata
    cost = (tokens_used["input_tokens"] * 0.150) / 10000000 + (
        tokens_used["output_tokens"] * 0.6
    ) / 10000000
    return cost, tokens_used["total_tokens"]


config = dotenv_values(".env")
status = load_dotenv(".env")
logging.info(f"Load Environment {status}")
# OPEN FILES
with open(examples_path, "r") as f:
    examples = json.load(f)
with open(merger_data_path, "r") as f:
    merged_data = json.load(f)
with open(merger_data_status_path, "r") as f:
    merged_data_status = json.load(f)


# Prepare the chat prompt


client = AzureOpenAI(
    azure_endpoint=config["AZURE_ENDPOINT"],
    api_key=config["AZURE_API_KEY"],
    api_version=config["AZURE_API_VERSION_BATCH"],
)

azure_deployment = config["AZURE_DEPLOYMENT_BATCH"]

logging.info(f"Client: {client}")
logging.info(f"Azure Deployment: {azure_deployment}")

csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

include_examples = True

list_profiles = list(merged_data.keys())
list_profiles_status = list(merged_data_status.keys())
random.shuffle(list_profiles)
list_profiles = list_profiles[:30]

logging.info(f"length of profiles: {len(list_profiles)}")
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
    else:
        logging.info(f"Profile: {p} Status: {status}")

        response = json.dumps(
            {"category": status, "ranked_categories": "NA", "certainty": "NA"}
        )
        output.append({"profile_id": p, "response": response, "input": profile})


## Write JSONL file and upload to Azure Batch API
# Filepath for the JSONL file
file_path = os.path.join(
    ROOT_DIR, input_data_folder, batch_data_folder, "records.jsonl"
)

# Writing records to the JSONL file
with open(file_path, "w") as file:
    for record in records:
        file.write(f"{json.dumps(record)}\n")

# Upload a file with a purpose of "batch" Uncomment this line to upload the file
file = client.files.create(file=open(file_path, "rb"), purpose="batch")

# print(file.model_dump_json(indent=2))
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
# print(batch_response.model_dump_json(indent=2))


status = "validating"
while status not in ("completed", "failed", "canceled"):
    time.sleep(60)
    batch_response = client.batches.retrieve(batch_id)
    status = batch_response.status
    logging.info(f"{datetime.datetime.now()} Batch Id: {batch_id},  Status: {status}")

if batch_response.status == "failed":
    for error in batch_response.errors.data:
        logging.error(f"Error code {error.code} Message {error.message}")

# Get the output file ID and extracting Responses
embed()
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
        response = json_response.get("response")["body"]["choices"][0]["message"][
            "content"
        ]
        p = json_response["custom_id"].split("-")[-1]
        profile = merged_data.get(p)
        output.append({"profile_id": p, "response": response, "input": profile})


filename = os.path.join(
    ROOT_DIR,
    input_data_folder,
    classification_data_folder,
    f"{azure_deployment}_{timestamp_str}.json",
)
logging.info(f"Saving output to {filename}")

with open(filename, "w") as f:
    json.dump(output, f, indent=4)
embed()
