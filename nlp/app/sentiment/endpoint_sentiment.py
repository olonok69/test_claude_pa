from keybert import KeyBERT
import os
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from detectaicore import lfilenames_types, NpEncoder, index_response

try:
    from nlp.app.sentiment.src.utils_sentiment import (
        extract_docs,
        extract_sentiment,
    )

    from nlp.app.sentiment.src.detoxify import Detoxify

except:
    from src.utils_sentiment import (
        extract_docs,
        extract_sentiment,
    )
    from src.detoxify import Detoxify


from starlette.concurrency import run_in_threadpool

import uvicorn
from transformers import pipeline
import json
import platform
import spacy
from dotenv import load_dotenv

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")

# Path when runing in cloud
if MODEL_PATH == None:
    MODEL_PATH = "/home/detectai/models/sentiment"
# only for local docker
if LOCAL_ENV != None and int(LOCAL_ENV) == 1:
    MODEL_PATH = "/sentiment/models/sentiment"
print(MODEL_PATH)

# Load Spacy model
sp = spacy.load("en_core_web_lg")
all_stopwords = sp.Defaults.stop_words
my_stop_words = [" "]

endpoint = FastAPI()
endpoint.dicc_embeddings = {}

# output folder

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "output")

if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "sentiment")
elif platform.system() == "Linux":
    MODELS_PATH = MODEL_PATH

classifier_path = os.path.join(MODELS_PATH, "multilingual-MiniLMv2-L6-mnli-xnli")
# if folder with model exists read from disk, is not read from https://huggingface.co
if Path(classifier_path).is_dir():
    # General Multilabel/ Multi-language Classifier
    classifier_multi = pipeline("zero-shot-classification", model=classifier_path)
else:
    classifier_multi = pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
    )

classifier_path = os.path.join(MODELS_PATH, "bart-large-mnli")
# General Multilabel/ Multi-language Classifier
if Path(classifier_path).is_dir():
    classifier = pipeline("zero-shot-classification", model=classifier_path)
else:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# keyword extractor Model

keybert_path = os.path.join(MODELS_PATH, "paraphrase-multilingual-MiniLM-L12-v2")
if Path(keybert_path).is_dir():
    kw_model = KeyBERT(model=keybert_path)
else:
    kw_model = KeyBERT(
        model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

# toxify_model
multilingual_debiased_path = os.path.join(
    MODELS_PATH, "multilingual_debiased-0b549669.ckpt"
)
toxic_model = Detoxify("multilingual", checkpoint=multilingual_debiased_path)


@endpoint.get("/test")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"test endpoint is": "OK"})


@endpoint.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@endpoint.post("/process")
async def process_tika(
    request: Request, background_tasks: BackgroundTasks, out: index_response
):
    """
    Process TIKA output received from Detect
    """

    response = await request.json()
    labels = response.get("labels")

    list_docs = response.get("docs").get("documents")
    print(len(list_docs))

    docs_with_languages = await run_in_threadpool(
        extract_docs,
        list_docs=list_docs,
        list_pii_docs=[],
        file_types_all=True,
        filenames_types=lfilenames_types,
    )

    chunck = await extract_sentiment(
        docs_with_languages,
        all_stopwords,
        my_stop_words,
        labels,
        classifier,
        classifier_multi,
        kw_model,
        toxic_model,
    )

    data = json.dumps(
        jsonable_encoder(chunck),
        cls=NpEncoder,
        indent=4,
        ensure_ascii=True,
    )

    out.status = {"code": 200, "message": "Success"}
    out.data = chunck
    json_compatible_item_data = jsonable_encoder(out)
    return JSONResponse(content=json_compatible_item_data)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_sentiment:endpoint",
        reload=True,
        host="127.0.0.1",
        port=5005,
        log_level="info",
    )
