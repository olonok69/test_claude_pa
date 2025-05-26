from fastapi import Request
from fastapi import FastAPI, Request
import uvicorn
import os
import json
from pathlib import Path
from starlette.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from detectaicore import (
    lfilenames_types,
    index_response,
    Job,
    image_file_names,
    set_up_logging,
    print_stack,
)
import torch
from src.vector_db import get_or_create_vector_db
from src.utils_doc import extract_docs, get_top_n_classes_with_scores
from src.summarization import (
    get_embedding_model,
    get_ollama_models,
)
from dotenv import load_dotenv
import platform
import warnings
import logging


warnings.filterwarnings("ignore")

# logging
# Set up logging
LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
script_name = os.path.join(LOGS_PATH, "debug.log")
# create loggers
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="debug",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USER = os.getenv("USER")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# load config
config_path = os.path.join(ROOT_DIR, "config", "config.json")
config = json.load(open(config_path))
MODEL_NAME = config.get("MODEL_NAME")
EMBEDDINGS_TYPE = config.get("EMBEDDINGS_TYPE")
BFLOAT16 = config.get("BFLOAT16")
# OLLAMA
# if we are working with docker compose we need to point to the name of the container rather that to localhost
USE_OLLAMA = int(config.get("USE_OLLAMA"))
OLLAMA_EMBEDDINGS = config.get("OLLAMA_EMBEDDINGS")
OLLAMA_TAGS_URL = config.get("OLLAMA_TAGS_URL")
OLLAMA_MODELS_URL = config.get("OLLAMA_MODELS_URL")
OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL")
# DOcument Summarization URL in docker compose SUMMARIZATION_URL
SUMMARIZATION_URL = config.get("SUMMARIZATION_URL")
# documents vars
CHUNK = config.get("CHUNK")
NUM_DOCUMENTS = config.get("NUM_DOCUMENTS")
MIN_NUM_TOKENS = config.get("MIN_NUM_TOKENS")

if platform.system() == "Linux" and MODEL_PATH == None and LOCAL_ENV == 0:
    MODEL_PATH = "/document_classification/models"
    MODELS_PATH = MODEL_PATH
elif platform.system() == "Linux" and USER in ["detectai", "olonok"]:
    # We are in VM under user detectai
    ROOT_DIR = "/home/detectai"
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "nlp", "document_classification")
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME.split("/")[-1])
    # if we are in local we need to point to localhost
    OLLAMA_TAGS_URL = OLLAMA_TAGS_URL.replace("ollama", "localhost")
    OLLAMA_MODELS_URL = OLLAMA_MODELS_URL.replace("ollama", "localhost")
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("ollama", "localhost")
    SUMMARIZATION_URL = SUMMARIZATION_URL.replace("document_summarization", "localhost")

elif platform.system() == "Linux" or platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME.split("/")[-1])

# Print URL,s OLLAMA
logging.info(f"Model Path start {MODEL_PATH}, local env {LOCAL_ENV}, user {USER}")
logging.info(f"Root Folder {ROOT_DIR}")
logging.info(
    f"Model Name:{MODEL_NAME}, Embeddings Type {EMBEDDINGS_TYPE}, Use Bfloat16 {BFLOAT16}"
)
logging.info(
    f"Use Ollama {USE_OLLAMA}, Ollama Embeddings {OLLAMA_EMBEDDINGS}, Ollama Tags URL {OLLAMA_TAGS_URL}"
)
logging.info(
    f"Ollama Models URL {OLLAMA_MODELS_URL}, Ollama Base URL {OLLAMA_BASE_URL}"
)
logging.info(
    f"Summarization URL {SUMMARIZATION_URL}, Chunk {CHUNK}, Num Documents {NUM_DOCUMENTS}"
)
# load transformers models
device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Device {device}")
# Create APP
endpoint = FastAPI()

# folders
data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_folder, exist_ok=True)
class_file = os.path.join(data_folder, "classes.csv")
output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

status = get_ollama_models(
    ollama_url=OLLAMA_TAGS_URL,
    ollama_embeddings=OLLAMA_EMBEDDINGS,
    ollama_url_get_model=OLLAMA_MODELS_URL,
)

if status != "success" and USE_OLLAMA:
    raise AttributeError("OLLAMA embedding model not present, we can't continue")

logging.info(f"Get OLLAMA Models Status: {status}")

endpoint.embeddings = get_embedding_model(
    MODEL_NAME,
    device=device,
    use_ollana=USE_OLLAMA,
    ollama_model=OLLAMA_EMBEDDINGS,
    base_url=OLLAMA_BASE_URL,
)

# path vector database, Always recreate
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")
os.makedirs(db_path, exist_ok=True)
endpoint.db = get_or_create_vector_db(
    class_file=class_file, db_path=db_path, embeddings=endpoint.embeddings
)
logging.info(f"Get or Create Vector Store: {status}")

# Create Jobs object
global jobs
jobs = {}


@endpoint.get("/test")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"test endpoint is": "OK"})


@endpoint.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@endpoint.get("/work/status")
async def status_handler(request: Request):
    return jobs


@endpoint.post("/process")
async def process_tika(request: Request, out: index_response):
    """
    Process TIKA output received from Detect
    """

    try:
        response = await request.json()
        new_task = Job()
        # Capture Job and apply status
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "Document Classification Model Task"

        if isinstance(response.get("documents"), list):
            list_docs = response.get("documents")
        else:
            raise AttributeError("Expected a list of Documents")

        logging.info(f"Number of Documents to classify: {len(list_docs)}")
        # Use Summarize
        if isinstance(response.get("summarize"), str) or isinstance(
            response.get("summarize"), int
        ):
            if (
                isinstance(response.get("summarize"), str)
                and len(response.get("summarize")) > 0
            ):
                summarize = int(response.get("summarize"))
            elif isinstance(response.get("summarize"), int):
                summarize = response.get("summarize")
            else:
                summarize = 1
        else:
            summarize = 1

        # Extract Metadata
        docs_with_languages, documents_non_processed = await run_in_threadpool(
            extract_docs,
            list_docs=list_docs,
            list_pii_docs=[],
            jobs=jobs,
            new_task=new_task,
            file_types_all=False,
            filenames_types=lfilenames_types,
            image_file_names=image_file_names,
            ocr=0,
            version="v2",
        )
        # Classify Individual Documents
        logging.info(f"Number of Documents to process = {len(docs_with_languages)}")

        if len(docs_with_languages) == 0:
            logging.error(
                f"Number of Documents to process = {len(docs_with_languages)}. We can't continue"
            )
            out.status = {
                "code": 500,
                "message": "Error",
            }
            out.data = []
            out.error = "No valid documents in these batch"
            json_compatible_item_data = jsonable_encoder(out)
            return JSONResponse(content=json_compatible_item_data, status_code=500)
        USE_SUMMARIZATION = summarize
        OVERLAP = config.get("OVERLAP")
        logging.info(
            f"Use Summarization {USE_SUMMARIZATION} chunk length {CHUNK} size of overlap {OVERLAP}"
        )
        chunck, _, documents_non_processed = await get_top_n_classes_with_scores(
            endpoint=endpoint,
            list_docs=list_docs,
            docs_with_languages=docs_with_languages,
            documents_non_teathred=documents_non_processed,
            jobs=jobs,
            new_task=new_task,
            k=5,
            url_summarization=SUMMARIZATION_URL,
            chunk_length=CHUNK,
            use_summarization=USE_SUMMARIZATION,
            overlap=OVERLAP,
        )

        docs_with_languages = []
        documents_non_processed = []
        out.status = {"code": 200, "message": "Success"}
        out.data = chunck
        out.number_documents_treated = len(docs_with_languages)
        out.number_documents_non_treated = len(documents_non_processed)
        out.list_id_not_treated = documents_non_processed

        json_compatible_item_data = jsonable_encoder(out)
        # update Job Status
        jobs[new_task.uid].status = f"Job {new_task.uid} Finished"
        return JSONResponse(content=json_compatible_item_data, status_code=200)

    except Exception:
        # cath exception with sys and return the error stack
        json_compatible_item_data = print_stack(out)
        logging.error(json_compatible_item_data.get("error"))
        return JSONResponse(content=json_compatible_item_data, status_code=500)


if __name__ == "__main__":
    USER = os.getenv("USER")
    if platform.system() == "Windows" or (
        platform.system() == "Linux" and USER == "olonok"
    ):
        uvicorn.run(
            "endpoint_doc_classification:endpoint",
            host="127.0.0.1",
            port=5014,
            log_level="info",
        )
