from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
import json
import os
from src.classes import LLama_PromptTemplate
from datetime import datetime
import random
from src.conf import merged_data_json, merged_data_status_json
from src.conf import nomenclature
from langchain_openai import ChatOpenAI
from IPython import embed

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

# "llama3.1:latest"
inference_server_url = "http://localhost:8000/v1"

llm = ChatOpenAI(
    model="/mnt/wolverine/home/samtukra/juan/models/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    openai_api_key="EMPTY",
    openai_api_base=inference_server_url,
    temperature=0.5,
    top_p=0.9,
)
# llm = ChatOllama(
#     model="llama3.1:latest",
#     temperature=0.5,
#     top_p=0.9,
#     top_k=30,
#     repetition_penalty=1.1,
#     do_sample=True,
#     num_ctx=16184,
#     format="json",
# )


csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

include_examples = True

list_profiles = list(merged_data.keys())
list_profiles_status = list(merged_data_status.keys())
random.shuffle(list_profiles)
list_profiles = list_profiles[:10]
output = []
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
        print(f"length of profile: {len(prompt.template)}")
        ai_msg = chain.invoke({"profile": profile})

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
    json.dump(output, f, indent=4)
