import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Union
import uvicorn
from dotenv import load_dotenv
import spacy
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from pii_codex.config import (
    APP_LANGUAGES,
    FILTER_DETECTION,
    GLOBAL_DOCUMENT_MIN_SCORE,
    MAX_LENGTH,
    file_v1,
    mapping_file_name,
    version,
)
from pii_codex.services.analysis_service import PIIAnalysisService
from pii_codex.utils.pii_mapping_util import PIIMapper
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from detectaicore import (
    Job,
    image_file_names,
    index_response,
    lfilenames_types,
    print_stack,
    set_up_logging,
)
from src.utils import extract_docs, get_pii_phi_v2_no_proxy

# Constants and Configuration
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_PATH = os.path.join(ROOT_DIR, "logs")
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
LOG_FILE = os.path.join(LOGS_PATH, "debug.log")

# Load environment variables
load_dotenv(os.path.join("keys", ".env"))

# Environment settings
LANGUAGE_ENGINE = os.getenv("LANGUAGE_ENGINE", "en")
DOCKER = os.getenv("DOCKER", "NO")
MODEL_PATH = os.getenv("MODEL_PATH", "/home/detectai/models/classification")
IS_TEST = int(os.getenv("IS_TEST", "0")) == 1

# Setup logging
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=LOG_FILE,
    logfile_log_level="debug",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
):
    raise AttributeError("Failed to set up logging")

logging.info(f"Language Analysis Engine: {LANGUAGE_ENGINE}")
logging.info(f"Docker Container: {DOCKER}")
logging.info(f"Model path: {MODEL_PATH}")

# Load configuration
cfg_path = os.path.join(
    ROOT_DIR, "config", "config_docker.json" if DOCKER == "YES" else "config.json"
)
config = json.load(open(cfg_path, "r"))

# Setup NLP models
try:
    sp = spacy.load("en_core_web_lg")
    sp.max_length = MAX_LENGTH

    # Model specialized in NER
    nlp = spacy.load("xx_ent_wiki_sm")
    nlp.max_length = MAX_LENGTH
    all_stopwords = sp.Defaults.stop_words
    my_stop_words = [" "]
    logging.info(f"Configured Language Models {LANGUAGE_ENGINE} and NER")
except Exception as e:
    logging.error(f"Failed to load NLP models: {e}")
    raise

# Initialize PII Analyzer Engines
pii_analysis = {}
if LANGUAGE_ENGINE in APP_LANGUAGES:
    pii_analysis[LANGUAGE_ENGINE] = PIIAnalysisService(language_code=LANGUAGE_ENGINE)

# Create FastAPI app
app = FastAPI()
app.mapper_version = version
app.file_name = mapping_file_name
app.language_engine = LANGUAGE_ENGINE
app.config = config
logging.info("Created FastAPI App")

# Jobs tracking
jobs: Dict[str, Job] = {}


# Endpoints
@app.get("/test")
async def test():
    return JSONResponse(status_code=200, content={"test endpoint is": "OK"})


@app.get("/health-check")
async def health_check():
    return JSONResponse(status_code=200, content={"message": "OK"})


@app.get("/work/status")
async def status_handler():
    return jobs


@app.post("/process")
async def process_tika(request: Request, out: index_response):
    """
    Process TIKA output received from Detect
    """
    new_task = Job()
    jobs[new_task.uid] = new_task
    jobs[new_task.uid].status = "Job started"
    jobs[new_task.uid].type_job = "Classification Model Analysis"

    try:
        response = await request.json()

        # Validate and extract documents
        if not isinstance(response.get("documents"), list):
            logging.error("Expected a list of Documents")
            raise ValueError("Expected a list of Documents")

        list_docs = response.get("documents")

        # Extract and normalize parameters
        ocr = _parse_ocr(response.get("ocr", 0))
        weights = _parse_weights(response.get("weights", ""))
        score = _parse_score(response.get("score"), GLOBAL_DOCUMENT_MIN_SCORE)

        # Determine mapper version
        app.mapper_version = _determine_version(response.get("version"))

        # Initialize appropriate mapper
        mapper = _initialize_mapper(app.mapper_version, app.file_name, weights)

        logging.info(
            f"Processing Front API PII Model Engine. Number of Documents {len(list_docs)}"
        )
        logging.info(f"Processing Front API PII Model Engine. Score: {score}")
        logging.info(
            f"Processing Front API PII Model Engine. Version: {app.mapper_version}"
        )
        logging.info(
            f"Processing Front API PII Model Engine. Length Weights: {len(weights) if weights else 0}"
        )
        logging.info(f"Filter Detection status {FILTER_DETECTION}")

        # Extract Metadata
        docs_with_languages, documents_non_processed = await run_in_threadpool(
            extract_docs,
            list_docs=list_docs,
            list_pii_docs=[],
            jobs=jobs,
            new_task=new_task,
            file_types_all=False,
            filenames_types=lfilenames_types,
            image_file_names=image_file_names,
            ocr=ocr,
            version=app.mapper_version,
            language_engine=LANGUAGE_ENGINE,
        )

        logging.info(f"Documents extracted for analysis: {len(docs_with_languages)}")

        if not docs_with_languages:
            return _create_error_response(
                out,
                "No Documents with Information or supported language in this batch",
                documents_non_processed,
            )

        # Process documents with appropriate version
        if app.mapper_version == "v2":
            logging.info("Starting analysis with Risk Model Version v2")
            chunck, _, documents_non_processed = await get_pii_phi_v2_no_proxy(
                nlp=nlp,
                docs_with_languages=docs_with_languages,
                documents_non_teathred=documents_non_processed,
                all_stopwords=all_stopwords,
                my_stop_words=my_stop_words,
                jobs=jobs,
                new_task=new_task,
                score=score,
                filter_detection=FILTER_DETECTION,
                language_engine=LANGUAGE_ENGINE,
                pii_mapper=mapper,
                pii_analysys_engine=pii_analysis.get(LANGUAGE_ENGINE),
            )

        # Log results
        logging.info("Analysis process complete")
        logging.info(f"Documents received: {len(list_docs)}")
        logging.info(f"Documents successfully analyzed: {len(docs_with_languages)}")
        logging.warning(f"Documents not analyzed: {len(documents_non_processed)}")

        for d in documents_non_processed:
            for key, value in d.items():
                logging.warning(f"Document {key} not processed, Reason: {value}")

        # Prepare success response
        out.status = {"code": 200, "message": "Success"}
        out.data = chunck
        out.number_documents_treated = len(docs_with_languages)
        out.number_documents_non_treated = len(documents_non_processed)
        out.list_id_not_treated = documents_non_processed
        out.error = (
            "Batch Processed without error"
            if not documents_non_processed
            else f"Batch Processed with {len(documents_non_processed)} not processed"
        )

        json_response = jsonable_encoder(out)
        jobs[new_task.uid].status = f"Job {new_task.uid} Finished"

        return JSONResponse(content=json_response, status_code=200)

    except Exception:
        json_response = print_stack(out)
        logging.error(json_response.get("error"))
        return JSONResponse(content=json_response, status_code=500)


# Helper functions
def _parse_ocr(ocr_value) -> int:
    """Parse and validate OCR parameter"""
    if isinstance(ocr_value, str):
        try:
            return int(ocr_value)
        except (ValueError, TypeError):
            return 0
    elif isinstance(ocr_value, int):
        return ocr_value
    return 0


def _parse_weights(weights_value) -> Union[List, str]:
    """Parse and validate weights parameter"""
    if isinstance(weights_value, list):
        return weights_value
    elif isinstance(weights_value, str):
        return weights_value
    return ""


def _parse_score(score_value, default_score) -> float:
    """Parse and validate score parameter"""
    if isinstance(score_value, str) and score_value:
        try:
            score = float(score_value)
            return max(score, default_score)
        except (ValueError, TypeError):
            return default_score
    elif isinstance(score_value, float):
        return max(score_value, default_score)
    return default_score


def _determine_version(version_value) -> str:
    """Determine which mapper version to use"""
    if isinstance(version_value, str) and version_value:
        if version_value in ["v1", "v2"]:
            return version_value

    # Default based on environment
    return "v1" if IS_TEST else "v2"


def _initialize_mapper(mapper_version, file_name, weights) -> PIIMapper:
    """Initialize the appropriate mapper"""
    if mapper_version == "v2":
        if weights:
            logging.info("V2 Using Custom Weights")
            return PIIMapper(
                version=mapper_version,
                mapping_file_name=file_name,
                test=False,
                reload=True,
                weigths=weights,
            )
        else:
            logging.info("V2 Using Default Weights")
            return PIIMapper(
                version=mapper_version,
                mapping_file_name=file_name,
                test=False,
                reload=False,
            )
    else:  # v1
        logging.info("Using V1 Mapper")
        return PIIMapper(
            version=mapper_version,
            mapping_file_name=file_v1,
            test=False,
            reload=False,
        )


def _create_error_response(out, error_message, documents_non_processed):
    """Create an error response"""
    out.status = {"code": 500, "message": "Error"}
    out.data = []
    out.error = error_message

    # Log reasons for non-processed documents
    for d in documents_non_processed:
        for key, value in d.items():
            logging.error(f"Document {key} not processed, Reason: {value}")

    json_response = jsonable_encoder(out)
    logging.error(json_response.get("error"))
    return JSONResponse(content=json_response, status_code=500)


if __name__ == "__main__":
    # reload=True if need it
    if DOCKER == "NO":

        uvicorn.run(
            "endpoint_classification_no_proxy:app",
            host="127.0.0.1",
            port=5000,
            log_level="info",
        )
