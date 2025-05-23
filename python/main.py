from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from transformers.pipelines.audio_utils import ffmpeg_read

import time
import datetime
import pprint
from src.utils import (
    forward_ov_time,
    create_ov_pipeline,
    extract_input_features,
    create_processor,
    create_ov_model,
)


warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="The attention mask is not set and cannot be inferred from input because pad token is same as eos token.",
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="openvino.runtime"
)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="The attention mask is not set...")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


model_id = "distil-whisper/distil-small.en"
BATCH_SIZE = 16
MAX_AUDIO_MINS = 30  # maximum audio input in minutes


model_path = os.path.join(ROOT_DIR, "distil-whisper_distil-small.en")

ov_config = {"CACHE_DIR": ""}
app = FastAPI(title="AUdio Transcription Whispher with OpenVino")
app.processor = create_processor(model_id)
app.ov_model = create_ov_model(model_path=model_path, ov_config=ov_config)
app.ov_pipe = create_ov_pipeline(
    ov_model=app.ov_model, processor=app.processor, model_id=model_id
)


@app.post("/transcribe/")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe Audio English Language
    """

    def _forward_ov_time(*args, **kwargs):

        global ov_time
        start_time = time.time()
        result = ov_pipe_forward(*args, **kwargs)
        ov_time = time.time() - start_time
        ov_time = round(ov_time, 2)
        return result

    try:
        # Read the audio file
        contents = await audio_file.read()
        inputs = ffmpeg_read(contents, 16000)

        # Extract features
        # input_features = extract_input_features(inputs)
        ov_pipe_forward = app.ov_pipe._forward

        # Perform transcription
        time1 = datetime.datetime.now()
        inputs = {
            "array": inputs,
            "sampling_rate": app.ov_pipe.feature_extractor.sampling_rate,
        }
        app.ov_pipe._forward = _forward_ov_time

        transcription = app.ov_pipe(inputs.copy(), batch_size=BATCH_SIZE)["text"]
        time2 = datetime.datetime.now()
        processing_time = (time2 - time1).seconds

        # Return JSON response
        return JSONResponse(
            {
                "transcription": transcription,
                "processing_time": processing_time,
                "ov_time": ov_time,
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# input_features = extract_input_features(inputs)


# ov_pipe_forward = ov_pipe._forward


# # embed()
# def _forward_ov_time(*args, **kwargs):
#     global ov_time
#     start_time = time.time()
#     result = pipe_forward(*args, **kwargs)
#     ov_time = time.time() - start_time
#     ov_time = round(ov_time, 2)
#     return result


# time1 = datetime.datetime.now()
# quantized = False
# pipe = None if quantized else ov_pipe
# pipe_forward = None if quantized else ov_pipe_forward

# audio_length_mins = len(inputs) / pipe.feature_extractor.sampling_rate / 60


# inputs = {"array": inputs, "sampling_rate": pipe.feature_extractor.sampling_rate}

# pipe._forward = _forward_ov_time
# ov_text = pipe(inputs.copy(), batch_size=BATCH_SIZE)["text"]
# time2 = datetime.datetime.now()
# ("#### TEXT ####")
# print("+" * 100)
# print("\n")
# pprint.pprint(ov_text)
# print("\n")
# print("#### TEXT ####")

# print(f"Processing Time {(time2-time1).seconds} Seconds")
