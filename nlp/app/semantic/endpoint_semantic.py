import numpy as np
import os
import pickle
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
import uvicorn
from sentence_transformers import SentenceTransformer, util
import platform
import json
import datetime
import spacy
from dotenv import load_dotenv
from detectaicore import lfilenames_types, NpEncoder, index_response

try:
    from nlp.app.semantic.src.utils import (
        extract_docs,
        extract_semantic,
    )

except:
    from src.utils import (
        extract_docs,
        extract_semantic,
    )


# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")

if MODEL_PATH == None:
    MODEL_PATH = "/home/detectai/models/semantic"

# only for local docker
if LOCAL_ENV != None and int(LOCAL_ENV) == 1:
    MODEL_PATH = "/semantic/models/semantic"
print(MODEL_PATH)

# load and setup spacy
sp = spacy.load("en_core_web_lg")
sp.max_length = 10000000
all_stopwords = sp.Defaults.stop_words
my_stop_words = [" "]

endpoint = FastAPI()
endpoint.dicc_embeddings = {}

# output folder
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "output")

if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "semantic")
elif platform.system() == "Linux":
    MODELS_PATH = MODEL_PATH

# keyword extractor Model
keybert_path = os.path.join(MODELS_PATH, "paraphrase-multilingual-MiniLM-L12-v2")

# sentence Transformer multilingual
keybert_path = os.path.join(MODELS_PATH, "stsb-xlm-r-multilingual")
keybert_path = os.path.join(MODELS_PATH, "sentence-t5-large")

endpoint.model = SentenceTransformer(keybert_path)


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
    Process Input received from Detect
    """

    response = await request.json()

    rindex = response.get("rindex")

    list_docs = response.get("docs").get("documents")
    print(len(list_docs))

    docs_with_languages = await run_in_threadpool(
        extract_docs,
        list_docs=list_docs,
        list_pii_docs=[],
        file_types_all=True,
        filenames_types=lfilenames_types,
    )

    chunck = await extract_semantic(
        docs_with_languages,
        all_stopwords,
        my_stop_words,
        endpoint.model,
        endpoint.dicc_embeddings,
        sp,
    )

    data = json.dumps(
        jsonable_encoder(chunck),
        cls=NpEncoder,
        indent=4,
        ensure_ascii=True,
    )

    with open(os.path.join(MODELS_PATH, f"{rindex}_dicc.pickle"), "wb") as handle:
        pickle.dump(endpoint.dicc_embeddings, handle, protocol=pickle.HIGHEST_PROTOCOL)

    out.status = {"code": 200, "message": "Success"}
    out.data = chunck
    json_compatible_item_data = jsonable_encoder(out)
    return JSONResponse(content=json_compatible_item_data)


@endpoint.post("/semantic-search-query-model")
async def semantic_search_query_model(
    request: Request, background_tasks: BackgroundTasks
):
    """
    API query Semantic similarity
    """
    # start mesuring time
    time1 = datetime.datetime.now()
    req = await request.json()
    # get startlette data form content. We expect data
    # get query to retrieve set of documents from ElasticSearch
    questions = req.get("questions")  # Labels to Classify Model
    rank = req.get("rank")
    rindex = req.get("index")

    with open(os.path.join("models", f"{rindex}_dicc.pickle"), "rb") as handle:
        b = pickle.load(handle)

    embedding_1 = endpoint.model.encode(questions, convert_to_tensor=True)

    doc1 = sp(questions)
    tokens2 = set([token.lemma_ for token in doc1])
    len_query = len(tokens2)

    for key in b.keys():
        cs = util.pytorch_cos_sim(embedding_1, b[key]["embedding"])

        b[key]["spacy_sim"] = doc1.similarity(b[key]["spacy_doc"])
        b[key]["cosine"] = cs.item()
        # exatc match in document
        intersetion = tokens2.intersection(b[key]["tokens"])

        b[key]["score"] = (
            ((b[key]["cosine"] + b[key]["spacy_sim"]) / 2)
            * (1 / np.log(b[key]["num_tokens"]))
            * (1 / np.log(b[key]["length_text"]))
            * len(intersetion)
        )
    # sort _dictionary
    sorted_keys = sorted(b, key=lambda x: b[x]["score"], reverse=True)
    output = sorted_keys[: int(rank)]

    json_output = []
    for key in output:
        ele = {
            "scan_id": str(key),
            "score": str(b[key]["score"]),
            "text": str(b[key]["text"]),
        }
        json_output.append(ele)
    return json.dumps(json_output)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_semantic:endpoint",
        reload=True,
        host="127.0.0.1",
        port=5006,
        log_level="info",
    )
