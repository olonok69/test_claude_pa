from langchain_ollama import ChatOllama
import json
import os
from src.classes import LLama_PromptTemplate
from datetime import datetime
import asyncio
from ollama import AsyncClient  # Import AsyncClient
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature
import random
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

model_id = "llama3.1:latest"  # or "llama3:8b"

csm_template_2 = LLama_PromptTemplate(nomenclature, examples)
include_examples = True

ollama_servers = [
    "http://localhost:11434",
    "http://localhost:11435",
]


async def chat(profile, profile_id, position, server_url):
    logging.info(
        f"Sending profile {profile_id} (position {position}) to LLM at {server_url}..."
    )
    params = {
        "num_ctx": 16184,
        "temperature": 0.5,
        "top_p": 0.9,
        "top_k": 30,
        "num_thread": 100,
    }
    message = {"role": "user", "content": profile}
    try:
        logging.debug(f"httpx version: {httpx.__version__}")  # log httpx version
        logging.debug(f"Creating AsyncClient with base_url: {server_url}")
        client = AsyncClient(base_url=server_url)
        logging.debug(f"AsyncClient created: {client}")
        async with client:
            logging.debug(f"Sending request to {server_url}")
            response = await client.chat(
                model=model_id, format="json", options=params, messages=[message]
            )
            logging.debug(f"Received response from {server_url}")
        logging.info(
            f"Received response for profile {profile_id} (position {position}) from {server_url}"
        )
        return response.message.content
    except Exception as e:
        logging.error(
            f"Error during chat for profile {profile_id} (position {position}) at {server_url}: {e}"
        )
        return json.dumps(
            {"category": "Error", "ranked_categories": "NA", "certainty": "NA"}
        )


async def process_profiles(profiles_with_ids, batch_size: int = 1):
    output = []

    async def process_batch(batch):
        llm_batch = [
            (profile, profile_id, status, position)
            for profile, profile_id, status, position in batch
            if status == "Enought_data"
        ]
        other_batch = [
            (profile, profile_id, status, position)
            for profile, profile_id, status, position in batch
            if status != "Enought_data"
        ]

        llm_tasks = []
        if llm_batch:  # Only proceed if there are LLM tasks
            # Choose a server for the entire batch
            server_url = ollama_servers[len(llm_batch) % len(ollama_servers)]

            for profile, profile_id, _, position in llm_batch:
                llm_tasks.append(chat(profile, profile_id, position, server_url))

            llm_responses = await asyncio.gather(*llm_tasks)

            for (profile, profile_id, _, position), response in zip(
                llm_batch, llm_responses
            ):
                output.append(
                    {
                        "profile_id": profile_id,
                        "input": profile,
                        "response": response,
                    }
                )

        for profile, profile_id, status, position in other_batch:
            logging.info(
                f"Profile {profile_id} (position {position}) does not have 'Enought_data' status: {status}. Skipping LLM."
            )
            response = json.dumps(
                {"category": status, "ranked_categories": "NA", "certainty": "NA"}
            )
            output.append(
                {"profile_id": profile_id, "response": response, "input": profile}
            )

    for i in range(0, len(profiles_with_ids), batch_size):
        batch = profiles_with_ids[i : i + batch_size]
        logging.info(
            f"Processing batch {i//batch_size + 1} of {len(profiles_with_ids)//batch_size + (1 if len(profiles_with_ids)%batch_size > 0 else 0)}"
        )
        await process_batch(batch)

    return output


async def main():
    list_profiles = list(merged_data.keys())
    random.shuffle(list_profiles)
    list_profiles[:100]

    profiles_with_ids = []
    for i, p in enumerate(list_profiles):
        profile = merged_data.get(p)
        status = merged_data_status.get(p)
        if status == "Enought_data":
            profile_template = csm_template_2.generate_clustering_prompt(
                profile, include_examples=include_examples
            )
            profiles_with_ids.append((profile_template, p, status, i))
        else:
            profiles_with_ids.append((profile, p, status, i))

    output = await process_profiles(profiles_with_ids)

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    model_id_safe = model_id.replace(":", "_")
    filename = os.path.join(
        ROOT_DIR,
        "classification",
        f"{model_id_safe}{'_noexamples_' if not include_examples else ''}{timestamp_str}.json",
    )

    with open(filename, "w") as f:
        json.dump(output, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
