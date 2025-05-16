import os
from fastapi import FastAPI, Request
import uvicorn
import torch
import gc
import psutil
import copy
from src.utils import process_request
from src.predictor import (
    get_prediction_model,
)

import platform
import datetime
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from detectaicore import Job, set_up_logging, print_stack
import sys
from dotenv import load_dotenv
import logging
from pathlib import Path
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

# load credentials
env_path = os.path.join("keys", ".env_file")
status = load_dotenv(env_path)
logging.info(f"Status load .env file {str(status)}")

MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USE_ONNX = os.getenv("USE_ONNX")
USE_OPENVINO = os.getenv("USE_OPENVINO")
DEVICE_OV = os.getenv("DEVICE_OV")

logging.info(f"IS LOCAL ENVIRONMENT {LOCAL_ENV}")
logging.info(f"USE ONNX {USE_ONNX}")
logging.info(f"USE OPENVINO {USE_OPENVINO}")
logging.info(f"DEVICE OPENVINO {DEVICE_OV}")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


# Create APP
settings = Settings()
app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")
# Check device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"DEVICE CUDA or CPU {device}")
# Create Jobs object
global jobs
jobs = {}
# output folder
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logging.info(f"Root Application Path: {ROOT_DIR}")
output_folder = os.path.join(ROOT_DIR, "output")
# path to models depends of environment
if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
elif platform.system() == "Linux" and MODEL_PATH == None and LOCAL_ENV == 0:
    MODEL_PATH = "/image_tagger/models"
    MODELS_PATH = "/image_tagger/models"
elif platform.system() == "Linux":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
logging.info(f"Models Path {MODELS_PATH}")

# Load model USE_ONNX = YES ve load the onnx model if not our custom Resnet 18 model
try:
    if USE_ONNX == "YES":
        model_path = os.path.join(MODELS_PATH, "onnx", "resnet50.onnx")
        logging.info(f"Path Model ONNX {model_path}")
    elif USE_OPENVINO == "YES":
        model_path = os.path.join(MODELS_PATH, "Florence-2-base-ft")
        logging.info(f"Path Model OPENVINO {model_path}")
    else:
        model_path = os.path.join(MODELS_PATH, "pytorch-vision-300a8a4")
        logging.info(f"Path Model TORCH_VISION {model_path}")

    model, processor = get_prediction_model(
        model_path=model_path,
        use_onnx=USE_ONNX,
        use_openvino=USE_OPENVINO,
        device=device,
    )

except Exception as e:
    ex_type, ex_value, ex_traceback = sys.exc_info()
    logging.error(f"Exception {ex_type} value {str(ex_value)}")


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
        jobs[new_task.uid].type_job = "Image Tagging Model Analysis"
        response = await request.json()

        if isinstance(response.get("documents"), list):
            list_docs = response.get("documents")
        else:
            logging.error("Expected a list of Documents")
            raise AttributeError("Expected a list of Documents")

        if isinstance(response.get("num_labels"), str) or isinstance(
            response.get("num_labels"), int
        ):
            if (
                isinstance(response.get("num_labels"), str)
                and len(response.get("num_labels")) > 0
            ):
                num_labels = int(response.get("num_labels"))
            elif isinstance(response.get("num_labels"), int):
                num_labels = response.get("num_labels")
        else:
            num_labels = 5
            # pront only for Florence2
        if isinstance(response.get("prompt"), str) and len(response.get("prompt")) > 0:
            prompt = "<" + response.get("prompt") + ">"

        else:
            prompt = "<OD>"

        logging.info(f"Number of IMAGES received: {len(list_docs)}")
        logging.info(f"Parameter num_labels: {num_labels}")
        logging.info(f"Parameter (ONLY Florence 2) prompt: {prompt}")

        data, documents_non_teathred = await run_in_threadpool(
            process_request,
            list_docs=list_docs,
            num_labels=num_labels,
            model=model,
            processor=processor,
            jobs=jobs,
            new_task=new_task,
            use_onnx=USE_ONNX,
            device=device,
            prompt=prompt,
            use_openvino=USE_OPENVINO,
        )

        # Print whole recognized text

        divisior = 1000000
        time2 = datetime.datetime.now()
        t = time2 - time1
        tf = (t.seconds * divisior) + t.microseconds
        logging.info(f"Processing Time in seconds: {tf/divisior}")
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
#     uvicorn.run(
#         "endpoint_image_tagger:app", host="127.0.0.1", port=5011, log_level="info"
#     )
