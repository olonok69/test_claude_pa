import asyncio
import argparse
import base64
import copy
import datetime
import gc
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import FastAPI
import psutil
from dotenv import load_dotenv

from detectaicore import Job, print_stack, set_up_logging
from utils.ocr_c import create_cffi, initialize_tesseract_api, setup_path_library_names
from utils.schemas import Index_Response, Settings, OCR_Request
from utils.utils import create_engine_rapidocr, process_request
from IPython import embed

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
settings = Settings()

LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
script_name = os.path.join(LOGS_PATH, "debug.log")

if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="debug",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s%(color_off)s",  # Added filename and line number
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")

env_path = os.path.join("keys", ".env_file")
status = load_dotenv(env_path)
logging.info(f"Status load .env file {str(status)}")

MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USE_RAPID_OCR = os.getenv("USE_RAPID_OCR")
MEM_PERCENTAGE = os.getenv("MEM_PERCENTAGE")
NUM_WORKERS = os.getenv("NUM_WORKERS")
app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

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

if MODEL_PATH is None and LOCAL_ENV == "0":
    MODEL_PATH = "/app/tessdata"
    TESSDATA = MODEL_PATH
    os.environ["TESSDATA_PREFIX"] = TESSDATA
else:
    TESSDATA = os.path.join(ROOT_DIR, "tessdata")
    os.environ["TESSDATA_PREFIX"] = TESSDATA

logging.info(f"Tesseract Models path: {TESSDATA}")

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

jobs = {}


def restart_ocr_engine(use_rapid_ocr: str, app: FastAPI):
    """Restart OCR Engine"""

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
    except Exception as e:
        logging.error(f"Error restarting OCR engine: {e}")


async def process_elastic_request(input_documents, cypher):
    """Process Elastic Detect OCR extraction request"""

    this_request = OCR_Request(
        documents=[],
        cypher=cypher,
        req={"documents": input_documents, "cypher": cypher},
        documents_non_teathred=[],
        data=[],
        list_docs=input_documents.get("documents"),
    )
    try:
        time1 = datetime.datetime.now()
        new_task = Job()
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "OCR Model Extraction"

        logging.info(f"Tesseract Models path: {os.getenv('TESSDATA_PREFIX')}")
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

        out = Index_Response(
            status={"code": 200, "message": "Success"},
            data=copy.deepcopy(this_request.data),
            error="",
            number_documents_treated=len(this_request.data),
            number_documents_non_treated=len(this_request.documents_non_teathred),
            list_id_not_treated=this_request.documents_non_teathred,
            memory_used=str(psutil.virtual_memory()[2]),
            ram_used=str(round(psutil.virtual_memory()[3] / 1000000000, 2)),
            processing_time=str(tf),
        )
        logging.warning(f"Percentage of memory use: {out.memory_used} %")
        logging.warning(f"RAM used in GB: {out.ram_used} GB")

        for doc in this_request.documents_non_teathred:
            key = list(doc.keys())[0]
            logging.error(f"document with id: {key} reason: {doc.get(key)}")

        jobs[new_task.uid].status = f"Job {new_task.uid} Finished code {200}"

        del this_request, pool
        gc.collect()

        if psutil.virtual_memory()[2] > float(MEM_PERCENTAGE):
            logging.warning(
                f"Memory usage is above allowed: {MEM_PERCENTAGE}%. Restarting OCR Engine"
            )
            restart_ocr_engine(USE_RAPID_OCR)

        return json.dumps(out.model_dump()), 200
    except Exception:
        out = Index_Response()
        json_compatible_item_data = print_stack(out)
        logging.error(json_compatible_item_data.get("error"))
        try:
            del this_request, out
        except Exception:
            pass
        finally:
            gc.collect()
        return json.dumps(json_compatible_item_data, indent=4), 500


async def main(input_file, output_file, cypher):
    # def main(input_file, output_file, cypher):
    try:
        with open(input_file, "r") as f:
            documents = json.load(f)
        if not documents:
            logging.warning("No documents to process.")
            return
        if documents.get("cypher") is None:
            cypher = documents.get("cypher")

        result, code = await process_elastic_request(documents, int(cypher))
        # result, code = process_elastic_request(documents, int(cypher))
        if code == 500:
            with open(output_file, "w") as f:
                f.write(result)
            return
        with open(output_file, "w") as f:
            f.write(result)

    except Exception as e:
        logging.error(f"Error in main: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process OCR requests from a JSON file."
    )
    parser.add_argument("input_file", type=str, help="Path to the input JSON file.")
    parser.add_argument("output_file", type=str, help="Path to the output JSON file.")
    parser.add_argument(
        "--cypher", type=int, default=0, help="Cypher value (default: 0)."
    )
    args = parser.parse_args()
    # main(args.input_file, args.output_file, args.cypher)
    asyncio.run(main(args.input_file, args.output_file, args.cypher))
