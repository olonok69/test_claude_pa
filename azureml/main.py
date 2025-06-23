from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from azure.ai.ml import Input
from azure.ai.ml.dsl import pipeline
from dotenv import dotenv_values
from dotenv import load_dotenv
from utils.login import get_ws_client
from utils.datasets import get_labels_dataset, create_datasets
from utils.computer import create_gpu_cluster
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes

import azureml.core
from azureml.core import Workspace
# Load env and login to Workspace
load_dotenv(".env")
config = dotenv_values(".env")


# Enter details of your Azure Machine Learning workspace
subscription_id = config.get("SUBSCRIPTION_ID")
resource_group = config.get("RESOURCE_GROUP")
workspace = config.get("AZUREML_WORKSPACE_NAME")

credential = DefaultAzureCredential()
# Check if given credential can get token successfully.
credential.get_token("https://management.azure.com/.default")


ml_client = get_ws_client(
    credential, subscription_id, resource_group, workspace
)
print(ml_client)

path_model ="/mnt/wolverine/home/samtukra/models/Meta-Llama-3.1-8B-Instruct-ONNX-INT4/model.onnx"

print("SDK version:", azureml.core.VERSION)

# read existing workspace from config.json
ws = Workspace(subscription_id=subscription_id, resource_group=resource_group, workspace_name=workspace)

print(ws.subscription_id, ws.location, ws.resource_group, sep = '\n')

# model_dir = "nsfw" # replace this with the location of your model files


# file_model = Model(
#     path= path_model,
#     type=AssetTypes.CUSTOM_MODEL,
#     name="llama_3.1_8B_onnx",
#     description= "LLama 3.1 8B model in ONNX format",
#     tags={"type": "llama", "format":"onnx"}
# )
# ml_client.models.create_or_update(file_model)


models = ws.models
for name, m in models.items():
    print("Name:", name,"\tVersion:", m.version, "\tDescription:", m.description, m.tags)


import onnxruntime