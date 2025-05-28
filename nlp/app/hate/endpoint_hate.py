import os
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import uvicorn
import orjson
from pathlib import Path
import spacy
import platform
from pysentimiento.preprocessing import preprocess_tweet
from pysentimiento import create_analyzer
from dotenv import load_dotenv
from transformers import (
    TextClassificationPipeline,
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")

if MODEL_PATH == None:
    MODEL_PATH = "/home/detectai/models/hate"

# only for local docker
if LOCAL_ENV != None and int(LOCAL_ENV) == 1:
    MODEL_PATH = "/hate/models/hate"
print(MODEL_PATH)

sp = spacy.load("en_core_web_lg")
all_stopwords = sp.Defaults.stop_words
my_stop_words = [" "]

endpoint = FastAPI()
endpoint.dicc_embeddings = {}

# output folder
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "output")

if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "hate")
elif platform.system() == "Linux":
    MODELS_PATH = MODEL_PATH


hate_model_path = os.path.join(MODELS_PATH, "bert-base-uncased-hatexplain")

# if folder with model exists read from disk, is not read from https://huggingface.co
if Path(hate_model_path).is_dir():
    tokenizer = AutoTokenizer.from_pretrained(hate_model_path)
    model = AutoModelForSequenceClassification.from_pretrained(hate_model_path)
else:
    tokenizer = AutoTokenizer.from_pretrained(
        "Hate-speech-CNERG/bert-base-uncased-hatexplain"
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        "Hate-speech-CNERG/bert-base-uncased-hatexplain"
    )

pipe = TextClassificationPipeline(model=model, tokenizer=tokenizer)

# get number of labels model
labels = model.config.id2label


pysentimiento_model_path = os.path.join(MODELS_PATH, "robertuito-sentiment-analysis")
if Path(pysentimiento_model_path).is_dir():
    pysentimiento_tokenizer = AutoTokenizer.from_pretrained(pysentimiento_model_path)
# pysentimento
else:
    pysentimiento_tokenizer = AutoTokenizer.from_pretrained(
        "pysentimiento/robertuito-base-cased"
    )


@endpoint.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@endpoint.post("/hate-analyzer")
async def hate_analyzer_endpoint(request: Request):
    """
    End point hate analyzer
    """
    text_to_anonymize: bytes = await request.body()

    prediction = pipe([text_to_anonymize.decode()], top_k=len(labels))

    out = {}
    out["source"] = text_to_anonymize.decode()
    out["hate_prediction"] = prediction

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


@endpoint.post("/pysentimento-analyzer")
async def pysentimento_endpoint(request: Request):
    """
    End point hate analyzer
    """
    text_to_anonymize: bytes = await request.body()
    text = text_to_anonymize.decode()
    preprocessed_text = preprocess_tweet(text, lang="en")

    prediction = tokenizer.tokenize(preprocessed_text)

    out = {}
    out["source"] = text_to_anonymize.decode()
    out["preprocessed_text"] = prediction

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


@endpoint.post("/pysentimento-analyzer-2")
async def pysentimento_endpoint_2(request: Request):
    """
    End point hate analyzer
    """
    req = await request.json()
    # get startlette data form content. We expect data

    type_query = req.get("type")  # sentiment, emotion, hate_speech
    language = req.get("language")
    text = req.get("text")

    if Path(pysentimiento_model_path).is_dir():
        analyzer = create_analyzer(
            task=type_query, lang=language, model_name=pysentimiento_model_path
        )
    else:
        analyzer = create_analyzer(task=type_query, lang=language)
    output = analyzer.predict(text)

    out = {}
    out["source"] = text
    out["prediction"] = output.output
    out["probabilities"] = output.probas

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_hate:endpoint",
        workers=2,
        host="127.0.0.1",
        port=5004,
        log_level="info",
    )
