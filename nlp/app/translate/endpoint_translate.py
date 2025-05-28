from fastapi import Request
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# from src.utils import (
#     filter_pii_scores,
#     post_processing,
#     write_and_post_array,
#     remove_mystopwords_enhanced,
#     MINIMUN_CHAR_LENGTH,
#     get_docs_from_elasticsearch_query_get_documents_v2,
# )
from classes.dataclasses import NpEncoder
import uvicorn
import orjson
import os
import dl_translate as dlt

from src.constants import *
import spacy
from pathlib import Path

# model english
sp = spacy.load("en_core_web_lg")
# model specialized in NER

all_stopwords = sp.Defaults.stop_words
my_stop_words = [" "]


# Create APP
endpoint = FastAPI()

# output folder

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "output")

# Chinese to English Translate
chinese_english_path = os.path.join(ROOT_DIR, "models", "opus-mt-zh-en")
if Path(chinese_english_path).is_dir():
    tokenizerchen = AutoTokenizer.from_pretrained(chinese_english_path)
    modelchen = AutoModelForSeq2SeqLM.from_pretrained(chinese_english_path)
else:
    tokenizerchen = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-zh-en")
    modelchen = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-zh-en")

# ENglist to Chinese Translate
english_chinese_path = os.path.join(ROOT_DIR, "models", "trans-opus-mt-en-zh")
if Path(english_chinese_path).is_dir():
    modelench = AutoModelForSeq2SeqLM.from_pretrained(english_chinese_path)
    tokenizerench = AutoTokenizer.from_pretrained(english_chinese_path)
    translation = pipeline(
        "translation_en_to_ch", model=modelench, tokenizer=tokenizerench
    )
else:
    mode_name = "liam168/trans-opus-mt-en-zh"
    modelench = AutoModelForSeq2SeqLM.from_pretrained(mode_name)
    tokenizerench = AutoTokenizer.from_pretrained(mode_name)
    translation = pipeline(
        "translation_en_to_ch", model=modelench, tokenizer=tokenizerench
    )


# Universal Translator
mt = dlt.TranslationModel(device="auto", tokenizer_options={"max_new_tokens": 200})


@endpoint.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@endpoint.post("/translate-chinese-english")
async def translate_chinese_en(request: Request):
    """
    End point Spanish test
    """
    text_to_anonymize: bytes = await request.body()

    batch = tokenizerchen([text_to_anonymize.decode()], return_tensors="pt")

    generated_ids = modelchen.generate(**batch, max_new_tokens=1024)

    text = tokenizerchen.batch_decode(generated_ids, skip_special_tokens=True)[0]

    out = {}
    out["source"] = text_to_anonymize.decode()
    out["translate"] = text

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


@endpoint.post("/translate-english-chinese")
async def translate_en_chinese(request: Request):
    """
    End point Spanish test
    """
    text_to_anonymize: bytes = await request.body()

    text = translation(text_to_anonymize.decode(), max_length=1024)

    out = {}
    out["source"] = text_to_anonymize.decode()
    out["translate"] = text

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


@endpoint.post("/translate")
async def translate_doc(request: Request):
    """
    End point translate
    """
    req = await request.json()

    text_to_translate = req.get("source")
    print(text_to_translate)
    origin = req.get("origin")
    target = req.get("target")
    text = mt.translate(text_to_translate, source=origin, target=target)
    out = {}
    out["source"] = text_to_translate
    out["translate"] = text

    return orjson.dumps(out, option=orjson.OPT_INDENT_2)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_translate:endpoint",
        host="127.0.0.1",
        port=5007,
        log_level="info",
    )
