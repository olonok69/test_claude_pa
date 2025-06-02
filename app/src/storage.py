import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient


def setup_env(config):
    # Define your service principal credentials
    tenant_id = config.get("AZURE_TENANT_ID")
    client_id = config.get("AZURE_TENANT_ID")
    client_secret = config.get("AZURE_CLIENT_SECRET")

    # Set the environment variables
    os.environ["AZURE_TENANT_ID"] = config.get("AZURE_TENANT_ID")
    os.environ["AZURE_CLIENT_ID"] = config.get("AZURE_TENANT_ID")
    os.environ["AZURE_CLIENT_SECRET"] = config.get("AZURE_CLIENT_SECRET")

    return ClientSecretCredential(
        tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
    )


def get_blob_service_client(
    credential, storage_account_name: str = "strategicaistuksdev01"
):
    # Create the BlobServiceClient

    return BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=credential,
    )


def download_new_data(
    config: dict,
    container_name: str,
    root_dir: str,
    data_dir: str,
    storage_account_name: str = "strategicaistuksdev01",
):
    # Specify blob container
    credential = setup_env(config)
    blob_service_client = get_blob_service_client(credential, storage_account_name)
    container_client = blob_service_client.get_container_client(container_name)

    # List of Blobs
    blobs_list = container_client.list_blobs()
    # Download Blobs
    for blob in blobs_list:
        filename = str(blob.name).split("/")[-1]

        if filename.endswith(".json"):
            print(f"Downloading {filename}...")
            blob_client = container_client.get_blob_client(blob)
            final_filename = os.path.join(root_dir, data_dir, filename)
            with open(final_filename, "wb") as my_blob:
                stream = blob_client.download_blob()
                data = stream.readall()
                my_blob.write(data)
    return
