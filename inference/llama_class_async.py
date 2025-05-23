from langchain_ollama import ChatOllama

import json
import os
from src.classes import LLama_PromptTemplate
from datetime import datetime
import asyncio
from ollama import AsyncClient
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature
from IPython import embed
import random

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

examples_path = os.path.join(ROOT_DIR, "output", "cat_examples.json")
merger_data_path = os.path.join(ROOT_DIR, "output", merged_data_json)
merger_data_status_path = os.path.join(ROOT_DIR, "output", merged_data_status_json)

model_id = "llama3.1:latest"  # llama3:8b # llama3.1:latest


# OPEN FILES
with open(examples_path, "r") as f:
    examples = json.load(f)
with open(merger_data_path, "r") as f:
    merged_data = json.load(f)
with open(merger_data_status_path, "r") as f:
    merged_data_status = json.load(f)


csm_template_2 = LLama_PromptTemplate(nomenclature, examples)
include_examples = True


async def chat(profile):
    params = {
        "num_ctx": 16184,
        "temperature": 0.5,
        "top_p": 0.9,
        "top_k": 30,
        "num_thread": 100,
        "repetition_penalty": 1.1,
        "do_sample": True,
    }
    message = {"role": "user", "content": profile}
    response = await AsyncClient().chat(
        model=model_id, format="json", options=params, messages=[message]
    )
    return response


async def process_profiles(profiles, list_profiles):
    output = []

    async def process_batch(batch, batch_ids):
        tasks = [chat(profile) for profile in batch]
        responses = await asyncio.gather(*tasks)
        for p, response, profile_id in zip(batch, responses, batch_ids):
            output.append(
                {
                    "profile_id": profile_id,
                    "input": p,
                    "response": response.message.content,
                }
            )

    batch_size = 6
    batches = [
        (profiles[i : i + batch_size], list_profiles[i : i + batch_size])
        for i in range(0, len(profiles), batch_size)
    ]

    for batch, batch_ids in batches:
        await process_batch(batch, batch_ids)

    return output


# Assuming merged_data is your dictionary of profiles
list_profiles = list(merged_data.keys())
# Shuffle the list randomly
random.shuffle(list_profiles)


profiles = [
    csm_template_2.generate_clustering_prompt(
        merged_data.get(profile), include_examples=include_examples
    )
    for profile in list_profiles
]

# Run the main function
output = asyncio.run(process_profiles(profiles, list_profiles))


# Get the current datetime
now = datetime.now()

# Format the datetime as a string including up to seconds
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
model_id = model_id.replace(":", "_")
if include_examples:
    filename = os.path.join(
        ROOT_DIR, "classification", f"{model_id}_{timestamp_str}.json"
    )
else:
    filename = os.path.join(
        ROOT_DIR, "classification", f"{model_id}_noexamples_{timestamp_str}.json"
    )

with open(filename, "w") as f:
    json.dump(output, f, indent=4)
