from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
import json
import pprint
import os
from classes import LLama_PromptTemplate
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

examples_path =  os.path.join(ROOT_DIR, "output", "examples.json")
merger_data_path =  os.path.join(ROOT_DIR, "output", "merger_data.json")
nomenclature_path = os.path.join(ROOT_DIR, "output", "nomenclature.json")

# OPEN FILES
with open(examples_path, "r") as f:
    examples = json.load(f)
with open(nomenclature_path, "r") as f:
    nomenclature = json.load(f)
with open(merger_data_path, "r") as f:
    merged_data = json.load(f)
    
llm = ChatOllama(
    model="llama3:8b",
    temperature=.3,
    num_ctx=4096,
)
csm_template_2 = LLama_PromptTemplate(nomenclature, examples)

include_examples=False

list_profiles = list(merged_data.keys())
output=[]
for p in list_profiles:
    profile= merged_data.get(p)
    profile_template = csm_template_2.generate_clustering_prompt(profile, include_examples=include_examples)
    ai_msg = llm.invoke(profile_template)
    print(f"Profile: {p} Category : {ai_msg.content}")
    print("-"*100)
    
    output.append({p : ai_msg.content, "input" :profile})
    
# Get the current datetime
now = datetime.now()

# Format the datetime as a string including up to seconds
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

if include_examples:
    filename = os.path.join(ROOT_DIR, "classification", f"llama3_8B_{timestamp_str}.json" )
else:
    filename = os.path.join(ROOT_DIR, "classification", f"llama3_8B_noexamples_{timestamp_str}.json" )
    
with open(filename, "w") as f:
    json.dump(output, f, indent=4)