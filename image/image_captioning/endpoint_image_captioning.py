import os
from fastapi import FastAPI, Request
import uvicorn
import torch
import gc
import psutil
import copy
import logging
from pathlib import Path
from src.utils import load_model, process_request
import datetime
import platform
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from detectaicore import (
    Job,
    set_up_logging,
    print_stack,
)
from dotenv import load_dotenv
from src.schemas import Index_Response, Settings

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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# load transformers models
device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Pytorch device cuda|cpu: {device}")
# load credentials and Environment variables
env_path = os.path.join("keys", ".env_file")
status = load_dotenv(env_path)
logging.info(f"Status load .env file {str(status)}")

MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USE_OPENVINO = os.getenv("USE_OPENVINO")
DEVICE_OV = os.getenv("DEVICE_OV")

if "DOCKER" in os.environ:
    DOCKER = os.getenv("DOCKER")
else:
    DOCKER = "NO"

# Models
if platform.system() == "Linux" and MODEL_PATH == None and LOCAL_ENV == 0:
    MODEL_PATH = "/image_captioning/models"
    MODELS_PATH = MODEL_PATH
elif platform.system() == "Linux" or platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")

logging.info(f"I am working in a Docker Container: {DOCKER}")
logging.info(f"Models path: {MODELS_PATH}")
logging.info(f"Use OpenVino: {USE_OPENVINO}")
logging.info(f"Device OpenVino: {DEVICE_OV}")


# Create Jobs object
global jobs
jobs = {}

# Create APP
settings = Settings()
app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

logging.info("Loading Model......................")
processor, model = load_model(
    models_path=MODELS_PATH, use_openvino=USE_OPENVINO, device_openvino=DEVICE_OV
)
logging.info("!!!!!! Model Loaded !!!!!!!!!!!")


@app.get("/test")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"test endpoint is": "OK"})


@app.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@app.get("/work/status")
async def status_handler(request: Request):
    return jobs


@app.post("/process", response_model=Index_Response)
async def predict_image(request: Request):
    try:
        time1 = datetime.datetime.now()
        new_task = Job()
        # Capture Job and apply status
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "Image Captioning Model Analysis"
        response = await request.json()

        if isinstance(response.get("documents"), list):
            list_docs = response.get("documents")
        else:
            raise AttributeError("Expected a list of Documents")
        # max_new_tokens
        if isinstance(response.get("max_new_tokens"), str) or isinstance(
            response.get("max_new_tokens"), int
        ):
            if (
                isinstance(response.get("max_new_tokens"), str)
                and len(response.get("max_new_tokens")) > 0
            ):
                max_new_tokens = int(response.get("max_new_tokens"))
            elif isinstance(response.get("max_new_tokens"), int):
                max_new_tokens = response.get("max_new_tokens")
        else:
            max_new_tokens = 30
        # min_new_tokens
        if isinstance(response.get("min_new_tokens"), str) or isinstance(
            response.get("min_new_tokens"), int
        ):
            if (
                isinstance(response.get("min_new_tokens"), str)
                and len(response.get("min_new_tokens")) > 0
            ):
                min_new_tokens = int(response.get("min_new_tokens"))
            elif isinstance(response.get("min_new_tokens"), int):
                min_new_tokens = response.get("min_new_tokens")
        else:
            min_new_tokens = 20
        # no_repeat_ngram_size
        if isinstance(response.get("no_repeat_ngram_size"), str) or isinstance(
            response.get("no_repeat_ngram_size"), int
        ):
            if (
                isinstance(response.get("no_repeat_ngram_size"), str)
                and len(response.get("no_repeat_ngram_size")) > 0
            ):
                no_repeat_ngram_size = int(response.get("no_repeat_ngram_size"))
            elif isinstance(response.get("no_repeat_ngram_size"), int):
                no_repeat_ngram_size = response.get("no_repeat_ngram_size")
        else:
            no_repeat_ngram_size = 3

        if isinstance(response.get("num_beams"), str) or isinstance(
            response.get("num_beams"), int
        ):
            if (
                isinstance(response.get("num_beams"), str)
                and len(response.get("num_beams")) > 0
            ):
                num_beams = int(response.get("num_beams"))
            elif isinstance(response.get("num_beams"), int):
                num_beams = response.get("num_beams")
        else:
            num_beams = 1
        # temperature
        if isinstance(response.get("temperature"), str) or isinstance(
            response.get("temperature"), float
        ):
            if (
                isinstance(response.get("temperature"), str)
                and len(response.get("temperature")) > 0
            ):
                temperature = float(response.get("temperature"))
            elif isinstance(response.get("temperature"), float):
                temperature = response.get("temperature")
        else:
            temperature = 1.0

        # diversity_penalty
        if isinstance(response.get("diversity_penalty"), str) or isinstance(
            response.get("diversity_penalty"), float
        ):
            if (
                isinstance(response.get("diversity_penalty"), str)
                and len(response.get("diversity_penalty")) > 0
            ):
                diversity_penalty = float(response.get("diversity_penalty"))
            elif isinstance(response.get("diversity_penalty"), float):
                diversity_penalty = response.get("diversity_penalty")
        else:
            diversity_penalty = 0.1

        # repetition_penalty
        if isinstance(response.get("repetition_penalty"), str) or isinstance(
            response.get("repetition_penalty"), float
        ):
            if (
                isinstance(response.get("repetition_penalty"), str)
                and len(response.get("repetition_penalty")) > 0
            ):
                repetition_penalty = float(response.get("repetition_penalty"))
            elif isinstance(response.get("repetition_penalty"), float):
                repetition_penalty = response.get("repetition_penalty")
        else:
            repetition_penalty = 0.8
        # pront only for Florence2
        if isinstance(response.get("prompt"), str) and len(response.get("prompt")) > 0:
            prompt = "<" + response.get("prompt") + ">"

        else:
            prompt = "<MORE_DETAILED_CAPTION>"
        # print parameters
        logging.info(f"Number of IMAGES received: {len(list_docs)}")
        logging.info(f"Parameter (ONLY BLIP MODEL) max_new_tokens: {max_new_tokens}")
        logging.info(f"Parameter (ONLY BLIP MODEL) min_new_tokens: {min_new_tokens}")
        logging.info(f"Parameter (ONLY BLIP MODEL) temperature: {temperature}")
        logging.info(
            f"Parameter (ONLY BLIP MODEL) diversity_penalty: {diversity_penalty}"
        )
        logging.info(
            f"Parameter (ONLY BLIP MODEL) repetition_penalty: {repetition_penalty}"
        )
        logging.info(
            f"Parameter (ONLY BLIP MODEL) no_repeat_ngram_size: {no_repeat_ngram_size}"
        )
        logging.info(f"Parameter (ONLY BLIP MODEL) num_beams: {num_beams}")
        logging.info(f"Parameter (ONLY Florence 2) prompt: {prompt}")

        data, documents_non_teathred = await run_in_threadpool(
            process_request,
            list_docs=list_docs,
            processor=processor,
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            temperature=temperature,
            diversity_penalty=diversity_penalty,
            repetition_penalty=repetition_penalty,
            no_repeat_ngram_size=no_repeat_ngram_size,
            num_beams=num_beams,
            model=model,
            jobs=jobs,
            new_task=new_task,
            device=device,
            prompt=prompt,
            use_openvino=USE_OPENVINO,
        )

        # Print whole recognized text

        time2 = datetime.datetime.now()
        t = time2 - time1
        tempo = t.seconds * 1000000 + t.microseconds
        logging.info("Finish Analisys Process")
        logging.info(f"Processing Time {tempo}")
        if len(data) == 0:
            logging.warning(
                f"We did not process any IMAGE in this batch containing: {len(list_docs)} Images"
            )

        # create response
        out = Index_Response(
            status={"code": 200, "message": "Success"},
            data=copy.deepcopy(data),
            error="",
            number_documents_treated=len(data),
            number_documents_non_treated=len(documents_non_teathred),
            list_id_not_treated=documents_non_teathred,
            memory_used=str(psutil.virtual_memory()[2]),  # Memory used in the process
            ram_used=str(round(psutil.virtual_memory()[3] / 1000000000, 2)),
        )
        logging.warning(f"Percentage of memory use: {out.memory_used} %")
        logging.warning(f"RAM used in GB: {out.ram_used} GB")
        # log to error to console
        for doc in documents_non_teathred:
            key = list(doc.keys())[0]
            logging.error(f"document with id: {key} reason: {doc.get(key)}")

        json_compatible_item_data = jsonable_encoder(out)
        # Update jobs interface
        jobs[new_task.uid].status = f"Job {new_task.uid} Finished code {200}"
        # delete objects to free memory
        del response
        del data
        del out
        gc.collect()
        return JSONResponse(content=json_compatible_item_data, status_code=200)
    except Exception:
        # cath exception with sys and return the error stack
        out = Index_Response()
        json_compatible_item_data = print_stack(out)
        logging.error(json_compatible_item_data.get("error"))
        return JSONResponse(content=json_compatible_item_data, status_code=500)


# if __name__ == "__main__":
#     USER = os.getenv("USER")
#     if platform.system() == "Windows" or (
#         platform.system() == "Linux" and USER == "olonok"
#     ):
#         uvicorn.run(
#             "endpoint_image_captioning:app",
#             host="127.0.0.1",
#             port=5010,
#             log_level="info",
#         )
