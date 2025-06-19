import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from dotenv import dotenv_values
import logging

status = load_dotenv(".env")
config = dotenv_values(".env")
logging.info(f"Load Environment {status}")
 
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "csm_data")
# Define your service principal credentials
tenant_id =  config.get("AZURE_TENANT_ID")
client_id = config.get("AZURE_TENANT_ID")
client_secret = config.get("AZURE_CLIENT_SECRET")
 
# Set the environment variables
os.environ["AZURE_TENANT_ID"] = config.get("AZURE_TENANT_ID")
os.environ["AZURE_CLIENT_ID"] = config.get("AZURE_TENANT_ID")
os.environ["AZURE_CLIENT_SECRET"] = config.get("AZURE_CLIENT_SECRET")
 
# Create a credential explicitly using the service principal details
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)
 
# Create the BlobServiceClient
blob_service_client = BlobServiceClient(
    account_url="https://strategicaistuksdev01.blob.core.windows.net",
    credential=credential
)
 
# Specify blob container
container_name = "landing"
container_client = blob_service_client.get_container_client(container_name)
 
blobs_list = container_client.list_blobs()
for blob in blobs_list:
    filename = str(blob.name).split("/")[-1]

    if filename.endswith(".json"):
        print(f"Downloading {filename}...")
        blob_client = container_client.get_blob_client(blob)
        final_filename = os.path.join(DATA_DIR, filename)
        with open(final_filename, "wb") as my_blob:
            stream = blob_client.download_blob()
            data = stream.readall()
            my_blob.write(data)
