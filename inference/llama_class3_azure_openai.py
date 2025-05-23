from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
import json
import os
from src.classes import LLama_PromptTemplate
from datetime import datetime
import random
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature
from langchain_openai import ChatOpenAI, AzureChatOpenAI, AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import dotenv_values
from IPython import embed

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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

# OPEN FILES
with open(examples_path, "r") as f:
    examples = json.load(f)
with open(merger_data_path, "r") as f:
    merged_data = json.load(f)
with open(merger_data_status_path, "r") as f:
    merged_data_status = json.load(f)


# Prepare the chat prompt


llm = AzureChatOpenAI(
    azure_endpoint=config["AZURE_ENDPOINT"],
    azure_deployment=config["AZURE_DEPLOYMENT"],
    api_key=config["AZURE_API_KEY"],
    api_version=config["AZURE_API_VERSION"],
    temperature=0.5,
    top_p=0.9,
)


csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

include_examples = True

list_profiles = list(merged_data.keys())
list_profiles_status = list(merged_data_status.keys())
random.shuffle(list_profiles)
list_profiles = list_profiles[:30]
output = []
total_cost = []
for p in list_profiles:
    profile = merged_data.get(p)
    status = merged_data_status.get(p)
    if status == "Enought_data":

        system_prompt = csm_template_2.generate_llama_prompt()

        prompt = PromptTemplate(
            input_variables=["profile"],
            template=system_prompt
            + """[INST] Classify and provide an output of this profile according to the instructions provided: \n\n {profile} [/INST]""",
        )

        chain = prompt | llm
        print(f"length of profile: {len(profile)}")
        ai_msg = chain.invoke({"profile": profile})
        cost, total_tokens = calculate_cost(ai_msg)
        total_cost.append({p: cost, "total_tokens": total_tokens})
        print(f"Profile: {p} Category : {cost}")
        output.append({"profile_id": p, "response": ai_msg.content, "input": profile})
        print(f"Profile: {p} Category : {ai_msg.content}")
        print("-" * 100)
    else:
        print(f"Profile: {p} Status: {status}")
        print("-" * 100)
        response = json.dumps(
            {"category": status, "ranked_categories": "NA", "certainty": "NA"}
        )
        output.append({"profile_id": p, "response": response, "input": profile})
