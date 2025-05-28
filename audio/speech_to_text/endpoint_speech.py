from fastapi import Request
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder

from classes.dataclasses import NpEncoder
import uvicorn

import os
import io
import speech_recognition as sr
from src.constants import *
import spacy

# model english
sp = spacy.load("en_core_web_lg")
all_stopwords = sp.Defaults.stop_words
my_stop_words = [" "]

# create audio recognizer

r = sr.Recognizer()

endpoint = FastAPI()

# output folder

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "output")


@endpoint.post("/speech_to_text")
async def basic_predict(request: Request):
    """
    extract text from audio file
    """
    file: bytes = await request.body()

    with sr.AudioFile(io.BytesIO(file)) as source:
        audio = r.record(source)

    text = r.recognize_sphinx(audio)

    return text


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_speech:endpoint",
        host="127.0.0.1",
        port=5002,
        log_level="info",
    )
