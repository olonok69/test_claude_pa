import uvicorn
from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

# Using run_in_executor
import asyncio
from concurrent.futures import ThreadPoolExecutor


import os
import datetime
from pathlib import Path
from detectaicore import Job, myconverter, set_up_logging, print_stack
import copy
import gc
import psutil
from dotenv import load_dotenv
import logging
from utils.ocr_c import (
    create_cffi,
    setup_path_library_names,
    initialize_tesseract_api,
)
from utils.schemas import Index_Response, Settings, OCR_Request
from utils.utils import process_request, create_engine_rapidocr

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
settings = Settings()

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
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")


# load credentials
env_path = os.path.join("keys", ".env_file")
status = load_dotenv(env_path)
logging.info(f"Status load .env file {str(status)}")
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USE_RAPID_OCR = os.getenv("USE_RAPID_OCR")
MEM_PERCENTAGE = os.getenv("MEM_PERCENTAGE")
NUM_WORKERS = os.getenv("NUM_WORKERS")
if "DOCKER" in os.environ:
    DOCKER = os.getenv("DOCKER")
else:
    DOCKER = "NO"

logging.info(f"I am working in a Docker Container: {DOCKER}")
logging.info(f"Models Path: {MODEL_PATH}")
logging.info(f"It is Local Environment?: {LOCAL_ENV}")
logging.info(f"Use Rapid OCR Engine: {USE_RAPID_OCR}")
logging.info(f"Memory Percentage Threshold: {MEM_PERCENTAGE} %")
logging.info(f"Number of Workers: {NUM_WORKERS}")

if MODEL_PATH == None and LOCAL_ENV == 0:
    MODEL_PATH = "/app/tessdata"
    app.tessdata = MODEL_PATH
    os.environ["TESSDATA_PREFIX"] = app.tessdata
else:
    # Use project tessdata
    app.tessdata = os.path.join(ROOT_DIR, "tessdata")
    os.environ["TESSDATA_PREFIX"] = app.tessdata

logging.info(f"Tesseract Models path: {app.tessdata}")


# Create Rapid OCR Engine
if USE_RAPID_OCR == "YES":
    app.engine = create_engine_rapidocr()
    logging.warning("Rapid OCR Engine has been initialized. Using Rapid OCR Engine")
    os.environ["USE_RAPID_OCR"] = "YES"
else:
    # create cffi tesseract application
    app.ffi = create_cffi()
    app.tesseract, app.leptonica = setup_path_library_names(app.ffi)

    # Create tesseract API
    app.api = app.tesseract.TessBaseAPICreate()

    # Initialize  Tesseract API
    app.tesseract = initialize_tesseract_api(app.api, app.tesseract, app.tessdata)

    logging.warning(
        "Tesseract API, ccfi and Leptonica have been initialized. Using Tesseract Engine"
    )
# Create Jobs object
global jobs
jobs = {}


@app.get("/test")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"test endpoint is": "OK"})


def restart_ocr_engine(use_rapid_ocr: str, app: FastAPI):
    """
    Restart OCR Engine
    """
    try:
        if use_rapid_ocr == "YES":
            if hasattr(app, "engine"):
                del app.engine
                gc.collect()
            app.engine = create_engine_rapidocr()
            logging.warning(
                "Rapid OCR Engine has been initialized. Using Rapid OCR Engine"
            )
            os.environ["USE_RAPID_OCR"] = "YES"
        else:
            # create cffi tesseract application
            if hasattr(app, "ffi"):
                del app.ffi
                del app.tesseract
                del app.leptonica
                del app.api
                gc.collect()
            app.ffi = create_cffi()
            app.tesseract, app.leptonica = setup_path_library_names(app.ffi)

            # Create tesseract API
            app.api = app.tesseract.TessBaseAPICreate()

            # Initialize  Tesseract API
            app.tesseract = initialize_tesseract_api(
                app.api, app.tesseract, app.tessdata
            )

            logging.warning(
                "Tesseract API, ccfi and Leptonica have been initialized. Using Tesseract Engine"
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error: {e}"})


@app.get("/restart_ocr")
async def restart_ocr(request: Request):
    """
    Restart OCR Engine
    Parameters:
    request: Request: Request object
    Returns:
    JSONResponse: Index_Response object
    """
    try:
        restart_ocr_engine(USE_RAPID_OCR, app)
        return JSONResponse(
            status_code=200, content={"message": "OCR Engine has been restarted"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error: {e}"})


@app.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@app.get("/work/status")
async def status_handler(request: Request):
    return jobs


@app.post("/process", response_model=Index_Response)
async def process_elastic_request(request: Request):
    """
    Process Elastic Detect OCR extraction request
    Parameters:
    request: Request: Request object
    Returns:
    JSONResponse: Index_Response object
    """
    this_request = OCR_Request(
        documents=[],
        cypher=0,
        req={},
        documents_non_teathred=[],
        data=[],
        list_docs=[],
    )
    try:
        time1 = datetime.datetime.now()
        new_task = Job()

        # Capture Job and apply status
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "OCR Model Extraction"
        # get the base64 encoded string
        this_request.req = await request.json()

        logging.info(f"Tesseract Models path: {os.getenv('TESSDATA_PREFIX')}")
        if isinstance(this_request.req.get("documents"), list):
            this_request.list_docs = this_request.req.get("documents")
        else:
            raise AttributeError("Expected a list of Documents")
        # convert it into bytes
        this_request.cypher = this_request.req.get("cypher")

        # Extract response elements
        if isinstance(this_request.req.get("cypher"), int) or isinstance(
            this_request.req.get("cypher"), str
        ):
            if isinstance(this_request.req.get("cypher"), str):
                this_request.cypher = int(this_request.req.get("cypher"))
            elif isinstance(this_request.req.get("cypher"), int):
                this_request.cypher = this_request.req.get("cypher")
            else:
                this_request.cypher = 0
        else:
            this_request.cypher = 0
        logging.info(f"Number of IMAGES received: {len(this_request.list_docs)}")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=int(NUM_WORKERS)) as pool:
            this_request.data, this_request.documents_non_teathred = (
                await loop.run_in_executor(
                    pool,
                    process_request,
                    this_request.list_docs,
                    app,
                    jobs,
                    new_task,
                    this_request.cypher,
                )
            )

        time2 = datetime.datetime.now()
        t = time2 - time1
        tf = t.seconds * 1000000 + t.microseconds
        logging.info(f"Processing Time: {tf}")
        if len(this_request.data) == 0:
            logging.warning(
                f"We did not process any IMAGE in this batch containing: {len(this_request.list_docs)} Images"
            )
        # create response
        out = Index_Response(
            status={"code": 200, "message": "Success"},
            data=copy.deepcopy(this_request.data),
            error="",
            number_documents_treated=len(this_request.data),
            number_documents_non_treated=len(this_request.documents_non_teathred),
            list_id_not_treated=this_request.documents_non_teathred,
            memory_used=str(psutil.virtual_memory()[2]),  # Memory used in the process
            ram_used=str(round(psutil.virtual_memory()[3] / 1000000000, 2)),
            processing_time=str(tf),
        )
        logging.warning(f"Percentage of memory use: {out.memory_used} %")
        logging.warning(f"RAM used in GB: {out.ram_used} GB")

        for doc in this_request.documents_non_teathred:
            key = list(doc.keys())[0]
            logging.error(f"document with id: {key} reason: {doc.get(key)}")

        json_compatible_item_data = jsonable_encoder(out)
        # Update jobs interface
        jobs[new_task.uid].status = f"Job {new_task.uid} Finished code {200}"
        # delete objects to free memory
        del this_request
        del out
        del pool

        gc.collect()
        if psutil.virtual_memory()[2] > float(MEM_PERCENTAGE):
            logging.warning(
                f"Memory usage is above allowed: {MEM_PERCENTAGE}%. Restarting OCR Engine"
            )
            restart_ocr_engine(USE_RAPID_OCR, app)

        return JSONResponse(content=json_compatible_item_data, status_code=200)

    except Exception:
        # cath exception with sys and return the error stack
        out = Index_Response()
        json_compatible_item_data = print_stack(out)
        logging.error(json_compatible_item_data.get("error"))
        try:
            del this_request
            del out

        except Exception:
            pass
        finally:
            gc.collect()
        return JSONResponse(content=json_compatible_item_data, status_code=500)


# if __name__ == "__main__":
#     USER = os.getenv("USER")
#     if platform.system() == "Windows" or (
#         platform.system() == "Linux" and USER == "olonok"
#     ):
#         uvicorn.run(
#             "endpoint_ocr:app",
#             reload=True,
#             host="0.0.0.0",
#             port=5003,
#             log_level="info",
#         )
