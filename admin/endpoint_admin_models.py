from fastapi import Request
from fastapi import FastAPI, Request
import uvicorn
import os
import json
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from detectaicore import index_response

from src.utils import (
    get_ollama_models,
    print_stack,
    list_ollama_models,
    show_ollama_model,
    delete_ollama_model,
)

from dotenv import load_dotenv
import platform
import warnings

warnings.filterwarnings("ignore")

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
# env variables
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USER = os.getenv("USER")
print(USER)

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
OLLAMA_SHOW_URL = config.get("OLLAMA_SHOW_URL")
OLLAMA_DELETE_URL = config.get("OLLAMA_DELETE_URL")
# documents vars
CHUNK = config.get("CHUNK")
NUM_DOCUMENTS = config.get("NUM_DOCUMENTS")
MIN_NUM_TOKENS = config.get("MIN_NUM_TOKENS")


if platform.system() == "Windows":
    OLLAMA_TAGS_URL = OLLAMA_TAGS_URL.replace("ollama", "localhost")
    OLLAMA_MODELS_URL = OLLAMA_MODELS_URL.replace("ollama", "localhost")
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("ollama", "localhost")
    OLLAMA_SHOW_URL = OLLAMA_SHOW_URL.replace("ollama", "localhost")
    OLLAMA_DELETE_URL = OLLAMA_DELETE_URL.replace("ollama", "localhost")


print(OLLAMA_TAGS_URL)
print(OLLAMA_MODELS_URL)
print(OLLAMA_BASE_URL)
print(OLLAMA_SHOW_URL)
print(OLLAMA_DELETE_URL)


# Create APP
endpoint = FastAPI()

# folders

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


@endpoint.get("/list_models_ollama")
async def list_models(request: Request):
    list_models = list_ollama_models(ollama_url=OLLAMA_TAGS_URL)
    return JSONResponse(status_code=200, content=list_models)


@endpoint.post("/get_model_ollama")
async def get_model_ollama(request: Request, out: index_response):
    """
    Process request pull model ollama
    """

    try:
        response = await request.json()

        if isinstance(response.get("model"), str):
            model = response.get("model")
        else:
            raise AttributeError("Expected a model")

        status = get_ollama_models(
            ollama_url=OLLAMA_TAGS_URL,
            ollama_embeddings=model,
            ollama_url_get_model=OLLAMA_MODELS_URL,
        )

        docs_with_languages = []
        documents_non_processed = []
        out.status = {"code": 200, "message": "Success"}
        out.data = f"Model {model} pull status {status}"
        out.number_documents_treated = len(docs_with_languages)
        out.number_documents_non_treated = len(documents_non_processed)
        out.list_id_not_treated = documents_non_processed

        json_compatible_item_data = jsonable_encoder(out)
        return JSONResponse(content=json_compatible_item_data, status_code=200)

    except Exception:
        # cath exception with sys and return the error stack
        json_compatible_item_data = print_stack(out)
        return JSONResponse(content=json_compatible_item_data, status_code=500)


@endpoint.post("/show_model_ollama")
async def show_model_ollama(request: Request, out: index_response):
    """
    Process request pull model ollama
    """

    try:
        response = await request.json()

        if isinstance(response.get("model"), str):
            model = response.get("model")
        else:
            raise AttributeError("Expected a model")

        show = show_ollama_model(
            model=model,
            ollama_url=OLLAMA_SHOW_URL,
        )

        docs_with_languages = []
        documents_non_processed = []
        out.status = {"code": 200, "message": "Success"}
        out.data = show
        out.number_documents_treated = len(docs_with_languages)
        out.number_documents_non_treated = len(documents_non_processed)
        out.list_id_not_treated = documents_non_processed

        json_compatible_item_data = jsonable_encoder(out)
        return JSONResponse(content=json_compatible_item_data, status_code=200)

    except Exception:
        # cath exception with sys and return the error stack
        json_compatible_item_data = print_stack(out)
        return JSONResponse(content=json_compatible_item_data, status_code=500)


@endpoint.post("/delete_model_ollama")
async def delete_model_ollama(request: Request, out: index_response):
    """
    Process request pull model ollama
    """

    try:
        response = await request.json()

        if isinstance(response.get("model"), str):
            model = response.get("model")
        else:
            raise AttributeError("Expected a model")

        status = delete_ollama_model(
            model=model,
            ollama_url=OLLAMA_DELETE_URL,
        )

        docs_with_languages = []
        documents_non_processed = []
        out.status = {"code": 200, "message": "Success"}
        out.data = status
        out.number_documents_treated = len(docs_with_languages)
        out.number_documents_non_treated = len(documents_non_processed)
        out.list_id_not_treated = documents_non_processed

        json_compatible_item_data = jsonable_encoder(out)
        return JSONResponse(content=json_compatible_item_data, status_code=200)

    except Exception:
        # cath exception with sys and return the error stack
        json_compatible_item_data = print_stack(out)
        return JSONResponse(content=json_compatible_item_data, status_code=500)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_admin_models:endpoint",
        host="127.0.0.1",
        reload=True,
        port=5016,
        log_level="info",
    )
