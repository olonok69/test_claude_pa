import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "csm_data")
# Define your service principal credentials
tenant_id = ""
client_id = ""
client_secret = ""

# Set the environment variables
os.environ["AZURE_TENANT_ID"] = tenant_id
os.environ["AZURE_CLIENT_ID"] = client_id
os.environ["AZURE_CLIENT_SECRET"] = client_secret

# Create a credential explicitly using the service principal details
credential = ClientSecretCredential(
    tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
)

# Create the BlobServiceClient
blob_service_client = BlobServiceClient(
    account_url="https://strategicaistuksdev01.blob.core.windows.net",
    credential=credential,
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
