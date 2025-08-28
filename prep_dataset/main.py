# imports
import os
import mlflow
import argparse
from dotenv import dotenv_values
from dotenv import load_dotenv
import pandas as pd
import logging
import shutil
from pathlib import Path
from datetime import datetime
from utils.login import get_ws_client
from azureml.fsspec import AzureMachineLearningFileSystem
import mltable
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from src.conf import (
    input_data_folder, 
    output_csv_folder, 
    output_data_folder,
    classification_data_folder,
    regdata,
    regdata_refresh,
    demodata,
    seminar_reference_24,
    seminar_reference_25,
    badge_scan_24,
    badge_scan_25
)
from src.create_dataframes import create_dataframe

def setup_logging():
    """Set up logging configuration"""
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"azure_ml_job_{timestamp_str}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_local_folders(root_dir):
    """Create necessary local folders for data processing"""
    logger = logging.getLogger(__name__)
    
    # Create main data folder
    data_dir = os.path.join(root_dir, input_data_folder)
    os.makedirs(data_dir, exist_ok=True)
    
    # Create subfolders
    csv_dir = os.path.join(data_dir, output_csv_folder)
    output_dir = os.path.join(data_dir, output_data_folder)
    classification_dir = os.path.join(data_dir, classification_data_folder)
    
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(classification_dir, exist_ok=True)
    
    logger.info(f"Created local folders:")
    logger.info(f"  Data folder: {data_dir}")
    logger.info(f"  CSV folder: {csv_dir}")
    logger.info(f"  Output folder: {output_dir}")
    logger.info(f"  Classification folder: {classification_dir}")
    
    return data_dir, csv_dir, output_dir, classification_dir

def download_blob_data(uri, local_data_dir):
    """Download data from Azure Blob Storage to local directories"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the Azure ML file system
        fs = AzureMachineLearningFileSystem(uri)
        
        # Define file mappings: (blob_path, local_path)
        file_mappings = [
            # Root level files
            (f"landing/csm_data/{regdata}", os.path.join(local_data_dir, regdata)),
            (f"landing/csm_data/{regdata_refresh}", os.path.join(local_data_dir, regdata_refresh)),
            (f"landing/csm_data/{demodata}", os.path.join(local_data_dir, demodata)),
            
            # CSV files
            (f"landing/csm_data/csv/{seminar_reference_24}", os.path.join(local_data_dir, output_csv_folder, seminar_reference_24)),
            (f"landing/csm_data/csv/{seminar_reference_25}", os.path.join(local_data_dir, output_csv_folder, seminar_reference_25)),
            (f"landing/csm_data/csv/{badge_scan_24}", os.path.join(local_data_dir, output_csv_folder, badge_scan_24)),
            (f"landing/csm_data/csv/{badge_scan_25}", os.path.join(local_data_dir, output_csv_folder, badge_scan_25)),
        ]
        
        downloaded_files = []
        
        for blob_path, local_path in file_mappings:
            try:
                logger.info(f"Downloading {blob_path} to {local_path}")
                
                # Ensure the local directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download the file
                with fs.open(blob_path, 'rb') as blob_file:
                    with open(local_path, 'wb') as local_file:
                        local_file.write(blob_file.read())
                
                # Verify file was downloaded
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    logger.info(f"Successfully downloaded {blob_path} ({file_size} bytes)")
                    downloaded_files.append(local_path)
                else:
                    logger.error(f"Failed to download {blob_path}")
                    
            except Exception as e:
                logger.error(f"Error downloading {blob_path}: {str(e)}")
                # Continue with other files even if one fails
                continue
        
        logger.info(f"Downloaded {len(downloaded_files)} files successfully")
        return downloaded_files
        
    except Exception as e:
        logger.error(f"Error in download_blob_data: {str(e)}")
        raise

def process_dataframes(root_dir, config_env):
    """Process the dataframes using the existing create_dataframes function"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting dataframe processing...")
        
        # Call the existing create_dataframe function
        create_dataframe(
            create_dataframe="yes",  # Always create dataframes in this job
            root_dir=root_dir,
            config=config_env,
            post_event_process="no",  # You can make this configurable if needed
            include_previous_scan_data="no"  # You can make this configurable if needed
        )
        
        logger.info("Dataframe processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in process_dataframes: {str(e)}")
        raise

def prepare_artifacts(root_dir):
    """Prepare output artifacts for Azure ML Studio"""
    logger = logging.getLogger(__name__)
    
    try:
        # Create an outputs directory for artifacts
        outputs_dir = os.path.join(root_dir, "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        
        # Define source directories to copy as artifacts
        source_dirs = [
            (os.path.join(root_dir, input_data_folder, output_csv_folder), "csv_outputs"),
            (os.path.join(root_dir, input_data_folder, output_data_folder), "processed_data"),
            (os.path.join(root_dir, input_data_folder, classification_data_folder), "classification_data")
        ]
        
        artifact_files = []
        
        for source_dir, artifact_name in source_dirs:
            if os.path.exists(source_dir):
                dest_dir = os.path.join(outputs_dir, artifact_name)
                
                # Copy the directory
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir)
                shutil.copytree(source_dir, dest_dir)
                
                # Log the files copied
                for root, dirs, files in os.walk(dest_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        relative_path = os.path.relpath(file_path, outputs_dir)
                        logger.info(f"Artifact: {relative_path} ({file_size} bytes)")
                        artifact_files.append(relative_path)
        
        logger.info(f"Prepared {len(artifact_files)} artifact files in {outputs_dir}")
        return outputs_dir, artifact_files
        
    except Exception as e:
        logger.error(f"Error preparing artifacts: {str(e)}")
        raise

def log_mlflow_metrics(downloaded_files, artifact_files):
    """Log metrics to MLflow for tracking"""
    logger = logging.getLogger(__name__)
    
    try:
        # Log basic metrics
        mlflow.log_metric("files_downloaded", len(downloaded_files))
        mlflow.log_metric("artifacts_created", len(artifact_files))
        
        # Log parameters
        mlflow.log_param("input_data_folder", input_data_folder)
        mlflow.log_param("processing_timestamp", datetime.now().isoformat())
        
        logger.info("MLflow metrics logged successfully")
        
    except Exception as e:
        logger.error(f"Error logging MLflow metrics: {str(e)}")
        # Don't raise here as this is not critical for the main process

# define functions
def main(args):
    """Main function to orchestrate the data processing pipeline"""
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Azure ML data processing job")
    
    try:
        # enable auto logging
        mlflow.autolog()
        
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
        
        uri = str(args.uri)
        ROOT = os.path.dirname(os.path.abspath(__file__))
        
        logger.info(f"Root path: {ROOT}")
        logger.info(f"URI: {uri}")
        
        # Step 1: Create local folder structure
        logger.info("Step 1: Creating local folder structure")
        data_dir, csv_dir, output_dir, classification_dir = create_local_folders(ROOT)
        
        # Step 2: Download data from blob storage
        logger.info("Step 2: Downloading data from blob storage")
        downloaded_files = download_blob_data(uri, data_dir)
        
        if not downloaded_files:
            raise Exception("No files were downloaded successfully")
        
        # Step 3: Process the dataframes
        logger.info("Step 3: Processing dataframes")
        process_dataframes(ROOT, config)
        
        # Step 4: Prepare artifacts for Azure ML Studio
        logger.info("Step 4: Preparing artifacts")
        outputs_dir, artifact_files = prepare_artifacts(ROOT)
        
        # Step 5: Log metrics to MLflow
        logger.info("Step 5: Logging metrics to MLflow")
        log_mlflow_metrics(downloaded_files, artifact_files)
        
        logger.info("Azure ML data processing job completed successfully")
        logger.info(f"Outputs available in: {outputs_dir}")
        
        # Print summary
        print("\n" + "="*50)
        print("JOB SUMMARY")
        print("="*50)
        print(f"Files downloaded: {len(downloaded_files)}")
        print(f"Artifacts created: {len(artifact_files)}")
        print(f"Output directory: {outputs_dir}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")
        print(f"JOB FAILED: {str(e)}")
        raise

def parse_args():
    # setup arg parser
    parser = argparse.ArgumentParser(description="Azure ML data processing job")
    
    # add arguments
    parser.add_argument("--uri", type=str, required=True, 
                       help="URI of the Azure ML datastore containing the input data")
    
    # Optional arguments for flexibility
    parser.add_argument("--post_event_process", type=str, default="no", 
                       choices=["yes", "no"],
                       help="Whether to include post event processing")
    parser.add_argument("--include_previous_scan_data", type=str, default="no", 
                       choices=["yes", "no"],
                       help="Whether to include previous scan data")
    
    # parse args
    args = parser.parse_args()
    
    # return args
    return args

# run script
if __name__ == "__main__":
    # parse args
    args = parse_args()
    
    # load variables from .env file to request token for Service Principal Account
    load_dotenv(".env")
    config = dotenv_values(".env")
    
    # run main function
    main(args)