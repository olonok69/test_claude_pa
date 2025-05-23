#####################################################
# This Script is to classify the profiles using the langchain model using async.
# Tecnology used: asyncio, json, os, datetime, random, langchain_ollama, LLama_PromptTemplate
# Language: Python
# Author: Juan Huertas
# Date: 2025-02-20
#
# This script is part of the project AI
# The purpose of this script is to classify the profiles using the langchain model using async.
# The script will classify the profiles using the langchain model using async.
##############################################################################
import asyncio
import json
import os
from src.classes import LLama_PromptTemplate  # Make sure this import is correct
from datetime import datetime
import random
from langchain_ollama import ChatOllama
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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

model_id = "llama3.1:latest"

llm = ChatOllama(  # Initialize outside the async function
    model="llama3.1:latest",  # or llama3:8b
    temperature=0.5,
    top_p=0.9,
    top_k=30,
    repetition_penalty=1.1,
    do_sample=True,
    num_ctx=16184,
    format="json",
)

csm_template_2 = LLama_PromptTemplate(nomenclature, examples)
include_examples = True


async def process_profile(p: str, i: int) -> dict:  # Type hint for clarity
    """
    Process a single profile
    Args:
        p: Profile ID
        i: Index of the profile
    """
    profile = merged_data.get(p)
    status = merged_data_status.get(p)
    if status == "Enought_data":
        profile_template = csm_template_2.generate_clustering_prompt(
            profile, include_examples=include_examples
        )
        print(f"length of profile: {len(profile_template)}")
        ai_msg = await asyncio.to_thread(
            llm.invoke, profile_template
        )  # Make the Langchain call async
        print(f"Index {i} Profile: {p} Category : {ai_msg.content}")
        print("-" * 100)
        return {"profile_id": p, "response": ai_msg.content, "input": profile}
    else:
        print(f"Index {i} Profile: {p} Status: {status}")
        print("-" * 100)
        response = json.dumps(
            {"category": status, "ranked_categories": "NA", "certainty": "NA"}
        )
        return {"profile_id": p, "response": response, "input": profile}


async def process_all_profiles(list_profiles: list) -> list:
    tasks = [process_profile(p, list_profiles.index(p)) for p in list_profiles]
    output = await asyncio.gather(*tasks)
    return output


async def main():
    list_profiles = list(merged_data.keys())
    random.shuffle(list_profiles)
    # list_profiles = list_profiles[:100]  # Adjust as needed

    output = await process_all_profiles(list_profiles)

    #
    now = datetime.now()
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    model_id = "llama3_8B"  # or "llama3_8B"
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


if __name__ == "__main__":
    asyncio.run(main())
