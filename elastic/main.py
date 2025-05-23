from fastapi import FastAPI, Request, HTTPException
from starlette.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
import os
import datetime
from pathlib import Path
from detectaicore import index_response, Job, myconverter, set_up_logging, print_stack
import copy
from src.prompts import *
from src.utils import *
from dotenv import load_dotenv, dotenv_values
import logging


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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
env_path = os.path.join("conf", ".env_file")
status = load_dotenv(env_path)
config = dotenv_values(env_path)
logging.info(f"Status of loading .env file: {str(status)}")

app = FastAPI()
app.elastic_client = get_elastic(config)


@app.post("/process")
async def ask_question(request: Request):
    """
    Endpoint to receive a question and process it.

    Args:
        host (str): The Elasticsearch host.
        index (str): The Elasticsearch index.
        question (str): The question to ask.

    Returns:
        dict: A JSON response with the answer or an error message.
    """
    try:
        # 1. Validate the input (optional)
        request = await request.json()
        host = request.get("host")
        index = request.get("index")
        question = request.get("question")
        model = request.get("model")

        if not host or not index or not question:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        logging.info(f"HostName: {host}")
        logging.info(f"Index Name: {index}")
        logging.info(f"Question: {question}")
        logging.info(f"Model: {model}")
        # 2. Process the question (replace with your actual logic)
        # This is where you would use the host, index, and question
        # to query Elasticsearch or perform any other necessary actions.
        answer = process_question(host, index, question, model)  # Placeholder function

        # 3. Return the response
        return {"answer": answer}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
