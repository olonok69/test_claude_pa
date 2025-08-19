import os
import mlflow
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv("keys/.env")  # Load environment variables from .env file

# Test direct storage access
def test_storage_access():
    try:
        # Use the same credentials MLflow uses
        storage_account = "strategicaistuksdev01"
        container = "landing"
        
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            
        )
        
        container_client = blob_service_client.get_container_client(container)
        
        # Try to list blobs (read permission test)
        blobs = list(container_client.list_blobs(name_starts_with="personal_agenda/"))
        print(f"✅ Read access confirmed. Found {len(blobs)} blobs")
        
        # Try to upload a test blob (write permission test)
        test_blob = container_client.get_blob_client("personal_agenda/test_permission.txt")
        test_blob.upload_blob("test", overwrite=True)
        print("✅ Write access confirmed")
        
        # Clean up
        test_blob.delete_blob()
        print("✅ Delete access confirmed")
        
        return True
    except Exception as e:
        print(f"❌ Storage access failed: {e}")
        return False

# Test MLflow artifact logging
def test_mlflow_artifacts():
    try:
        mlflow.set_tracking_uri("databricks")
        mlflow.set_experiment("/Users/b.relf@closerstillmedia.com/Personal_Agendas")
        
        with mlflow.start_run():
            # Try to log a simple artifact
            with open("test_artifact.txt", "w") as f:
                f.write("Test artifact content")
            
            mlflow.log_artifact("test_artifact.txt")
            print("✅ MLflow artifact logging successful")
            
            os.remove("test_artifact.txt")
            return True
    except Exception as e:
        print(f"❌ MLflow artifact logging failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Azure Storage Permissions...")
    test_storage_access()
    print("\nTesting MLflow Artifact Logging...")
    test_mlflow_artifacts()