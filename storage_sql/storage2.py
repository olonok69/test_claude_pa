import os

from azure.storage.blob import BlobServiceClient

from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from dotenv import dotenv_values

status = load_dotenv(".env")
config = dotenv_values(".env")

token_credential = ManagedIdentityCredential(client_id="")
client = SecretClient(
    "https://strategicai-kv-uks-dev.vault.azure.net/", token_credential
)


AZURE_CLIENT_SECRET = client.get_secret("strategicai-svp-app-client-secret-01")
AZURE_TENANT_ID = "3540e7dc-31b3-4057-9e31-43e9fe938179"
# AZURE_CLIENT_ID = "e77fcc8e-5551-47b6-a600-1d5633c81e31"
AZURE_CLIENT_ID = "6f835e21-b21f-4fdb-8c03-e285a3107b86"

os.environ["AZURE_CLIENT_SECRET"] = AZURE_CLIENT_SECRET.value
os.environ["AZURE_TENANT_ID"] = AZURE_TENANT_ID
os.environ["AZURE_CLIENT_ID"] = AZURE_CLIENT_ID

blob_service_client = BlobServiceClient(
    account_url="https://strategicaistuksdev01.blob.core.windows.net",
    credential=token_credential,
)
# Get and print account information
account_info = blob_service_client.get_account_information()
print(account_info)
