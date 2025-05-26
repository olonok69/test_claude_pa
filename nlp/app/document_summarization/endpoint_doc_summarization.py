from fastapi import Request
from fastapi import FastAPI, Request
import uvicorn
import os
import json
from starlette.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from detectaicore import index_response, Job, set_up_logging, print_stack
import sys
import traceback
from pathlib import Path
from src.summarization import (
    get_summarizer,
    get_fine_tuned_model,
    get_tokenizer,
    get_llm,
    split_text,
    get_vectors,
    get_embedding_model,
    get_kmeans_model,
    get_summary,
    get_final_summary,
    get_ollama_models,
)
import torch
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
# env variables
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USER = os.getenv("USER")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# load config
config_path = os.path.join(ROOT_DIR, "config", "config.json")
config = json.load(open(config_path))
MODEL_NAME = config.get("MODEL_NAME")
TOKENIZER = config.get("TOKENIZER")
BFLOAT16 = int(config.get("BFLOAT16"))
USE_OLLAMA = int(config.get("USE_OLLAMA"))
EMBEDDINGS = config.get("EMBEDDINGS")
# if we are working with docker compose we need to point to the name of the container rather that to localhost
OLLAMA_EMBEDDINGS = config.get("OLLAMA_EMBEDDINGS")
OLLAMA_TAGS_URL = config.get("OLLAMA_TAGS_URL")
OLLAMA_MODELS_URL = config.get("OLLAMA_MODELS_URL")
OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL")
# documents vars
CHUNK = config.get("CHUNK")
NUM_DOCUMENTS = config.get("NUM_DOCUMENTS")
MIN_NUM_TOKENS = config.get("MIN_NUM_TOKENS")

if platform.system() == "Linux" and MODEL_PATH == None and LOCAL_ENV == 0:
    MODELS_PATH = "/document_summarization/models"
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME)
    TOKENIZER = os.path.join(MODELS_PATH, TOKENIZER)

elif platform.system() == "Linux" and USER == "detectai":
    # We are in VM under user detectai
    ROOT_DIR = "/home/detectai"
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "nlp", "document_summarization")
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME)
    TOKENIZER = os.path.join(MODELS_PATH, TOKENIZER)
    # if we are in local we need to point to localhost
    OLLAMA_TAGS_URL = OLLAMA_TAGS_URL.replace("ollama", "localhost")
    OLLAMA_MODELS_URL = OLLAMA_MODELS_URL.replace("ollama", "localhost")
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("ollama", "localhost")

elif platform.system() == "Linux" or platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME)
    TOKENIZER = os.path.join(MODELS_PATH, TOKENIZER)


# Print URL,s OLLAMA
logging.info(f"Model Path start {MODEL_PATH}, local env {LOCAL_ENV}, user {USER}")
logging.info(f"Root Folder {ROOT_DIR}")
logging.info(f"Model Name:{MODEL_NAME}, Use Bfloat16 {BFLOAT16}")
logging.info(
    f"Use Ollama {USE_OLLAMA}, Ollama Embeddings {OLLAMA_EMBEDDINGS}, Ollama Tags URL {OLLAMA_TAGS_URL}"
)
logging.info(
    f"Ollama Models URL {OLLAMA_MODELS_URL}, Ollama Base URL {OLLAMA_BASE_URL}"
)

# load transformers models
device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Device {device}")

# Create APP
endpoint = FastAPI()

# Model and Tokenizer
endpoint.model = get_fine_tuned_model(path=MODEL_NAME, bfloat=bool(BFLOAT16))
endpoint.tokenizer = get_tokenizer(path=TOKENIZER)
endpoint.summarizer = get_summarizer(
    tokenizer=endpoint.tokenizer, model=endpoint.model, device=device
)
endpoint.llm = get_llm(endpoint.summarizer)
logging.info(f"Model Name:{MODEL_NAME}, Use Bfloat16 {BFLOAT16}, Tokenizer {TOKENIZER}")

status = get_ollama_models(
    ollama_url=OLLAMA_TAGS_URL,
    ollama_embeddings=OLLAMA_EMBEDDINGS,
    ollama_url_get_model=OLLAMA_MODELS_URL,
)
if status != "success" and USE_OLLAMA:
    raise AttributeError("OLLAMA embedding model not present, we can't continue")
logging.info(f"Get OLLAMA Models Status: {status}")

endpoint.embeddings = get_embedding_model(
    EMBEDDINGS,
    device=device,
    use_ollana=USE_OLLAMA,
    ollama_model=OLLAMA_EMBEDDINGS,
    base_url=OLLAMA_BASE_URL,
)

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
        jobs[new_task.uid].type_job = "Document Summarization Model Task"

        if isinstance(response.get("text"), str):
            text = response.get("text")
        else:
            raise AttributeError("Expected a Document")

        num_documents = 1
        summaries = ""
        if len(text) > CHUNK:
            docs, num_documents = split_text(text)
            logging.info(f"Number of Documents {num_documents}")
            if num_documents > NUM_DOCUMENTS:

                vectors = get_vectors(docs, endpoint.embeddings)

                selected_docs, selected_indices = get_kmeans_model(
                    vectors=vectors, docs=docs, n_clusters=8
                )
                logging.info(selected_docs[0].page_content)
                summary_list = get_summary(
                    selected_docs, endpoint.summarizer, selected_indices
                )

                summaries = "\n".join(summary_list)

                logging.info(
                    f"First Iteration Summarization get Documennt with a length of {len(summaries)}"
                )

            logging.info(f"Length text {len(text)} Number of chuncks = {num_documents}")

            # get final summary
            chunck = get_final_summary(
                summaries=summaries,
                endpoint=endpoint,
                chunck=CHUNK,
                min_num_tokens=MIN_NUM_TOKENS,
            )
        else:

            length_tokens = endpoint.llm.get_num_tokens(text)
            logging.info(
                f"Get Summarization of  Documennt with a length of {len(text)} and {length_tokens} tokens"
            )
            if length_tokens > MIN_NUM_TOKENS:
                response = endpoint.summarizer(
                    text, max_length=length_tokens - 10, temperature=0.01
                )

                chunck = response[0]["summary_text"]
            else:
                chunck = text

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
            "endpoint_doc_summarization:endpoint",
            host="127.0.0.1",
            port=5015,
            log_level="info",
        )
