from langchain_ollama import ChatOllama
import json
import os
from src.classes import LLama_PromptTemplate
from datetime import datetime
import random
import asyncio
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature
from pathlib import Path
from detectaicore import (
    set_up_logging,
)
import shutil
import logging
import httpx

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Set up logging
LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
dirpath = Path(LOGS_PATH)
if dirpath.exists() and dirpath.is_dir():
    shutil.rmtree(dirpath)
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
script_name = os.path.join(LOGS_PATH, "debug.log")
# create loggers
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="info",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")


examples_path = os.path.join(ROOT_DIR, "output", "cat_examples.json")
merger_data_path = os.path.join(ROOT_DIR, "output", merged_data_json)
merger_data_status_path = os.path.join(ROOT_DIR, "output", merged_data_status_json)


# OPEN FILES
with open(examples_path, "r") as f:
    examples = json.load(f)
with open(merger_data_path, "r") as f:
    merged_data = json.load(f)
with open(merger_data_status_path, "r") as f:
    merged_data_status = json.load(f)

csm_template_2 = LLama_PromptTemplate(nomenclature, examples)
include_examples = True

ollama_servers = [
    "http://localhost:11434",
    "http://localhost:11435",
]


async def process_profiles_for_server(profiles, server_url, result_queue):
    for profile_id in profiles:
        profile = merged_data.get(profile_id)
        status = merged_data_status.get(profile_id)
        if status == "Enought_data":
            profile_template = csm_template_2.generate_clustering_prompt(
                profile, include_examples=include_examples
            )
            logging.info(f"length of profile: {len(profile_template)}")

            llm = ChatOllama(
                model="llama3.1:latest",
                temperature=0.5,
                top_p=0.9,
                top_k=30,
                repetition_penalty=1.1,
                do_sample=True,
                num_ctx=16184,
                format="json",
                base_url=server_url,
            )

            ai_msg = await llm.ainvoke(profile_template)
            logging.info(f"Profile: {profile_id} Category : {ai_msg.content}")
            logging.info("-" * 100)
            result_queue.append(
                {"profile_id": profile_id, "response": ai_msg.content, "input": profile}
            )
        else:
            logging.info(f"Profile: {profile_id} Status: {status}")
            logging.info("-" * 100)
            response = json.dumps(
                {"category": status, "ranked_categories": "NA", "certainty": "NA"}
            )
            result_queue.append(
                {"profile_id": profile_id, "response": response, "input": profile}
            )


async def main():
    list_profiles = list(merged_data.keys())
    random.shuffle(list_profiles)
    list_profiles = list_profiles[:100]

    logging.info(f"Number of profiles: {len(list_profiles)}")

    server1_profiles = list_profiles[: len(list_profiles) // 2]
    server2_profiles = list_profiles[len(list_profiles) // 2 :]

    result_queue = []

    tasks = [
        process_profiles_for_server(server1_profiles, ollama_servers[0], result_queue),
        process_profiles_for_server(server2_profiles, ollama_servers[1], result_queue),
    ]

    await asyncio.gather(*tasks)

    # Get the current datetime
    now = datetime.now()

    # Format the datetime as a string including up to seconds
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if include_examples:
        filename = os.path.join(
            ROOT_DIR, "classification", f"llama3_8B_{timestamp_str}.json"
        )
    else:
        filename = os.path.join(
            ROOT_DIR, "classification", f"llama3_8B_noexamples_{timestamp_str}.json"
        )

    with open(filename, "w") as f:
        json.dump(result_queue, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
