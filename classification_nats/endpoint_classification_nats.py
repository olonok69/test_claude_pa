import asyncio
import argparse
import json
import logging
import os
import socket
import psutil
import datetime
from pathlib import Path
from typing import Dict, List, Union
from fastapi.encoders import jsonable_encoder

import nats
from nats.js.api import (
    ConsumerConfig,
    AckPolicy,
    RetentionPolicy,
    DiscardPolicy,
    StreamConfig,
)
import spacy
from dotenv import load_dotenv
import requests
import signal

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

from detectaicore import (
    Job,
    image_file_names,
    index_response,
    lfilenames_types,
    print_stack,
    set_up_logging,
    setup_health_check_endpoint,
    setup_version_endpoint,
    NatsSSLContextBuilder
)
from src.utils import extract_docs, get_pii_phi_v2_no_proxy
from utils.environment import detect_environment

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

# Jobs tracking
jobs: Dict[str, Job] = {}


def get_health_check_subject():
    """
    Gets the health check subject from the environment.

    Returns:
        str: health check subject
    """
    base_subject = os.getenv("HEALTH_CHECK_SUBJECT", "pii.app.health.check")
    return base_subject


def get_health_check_subject_formatted():
    """
    Constructs the health check subject using the pod hostname.

    Returns:
        str: Formatted health check subject including hostname
    """
    base_subject = get_health_check_subject()
    hostname = socket.gethostname()
    return f"{base_subject}.{hostname}"


async def setup_stream(
    nats_url,
    local_env,
    stream_name,
    subjects,
):
    """
    Set up a NATS stream with the specified name and subjects.
    args:
        nats_url (str): The NATS server URL.
        local_env (str): Local environment flag.
        stream_name (str): The name of the stream to create.
        subjects (list): List of subjects for the stream.
    """
    nc = None
    try:
        # Connect to NATS using certificate if local_env is "0"
        if local_env == "0":
            ssl_builder = NatsSSLContextBuilder()
            ssl_context = ssl_builder.create_ssl_context()
            nc = await nats.connect(nats_url, tls=ssl_context)
        else:
            nc = await nats.connect(nats_url)

        js = nc.jetstream()
        try:
            await js.stream_info(stream_name)
            logging.warning(f"Stream '{stream_name}' already exists.")
        except Exception as e:
            stream_config = StreamConfig(
                name=stream_name,
                subjects=subjects,
                retention=RetentionPolicy.WORK_QUEUE,
                max_age=30 * 24 * 60 * 60,  # 30 days
                duplicate_window=6 * 60,  # 6 minutes
                discard=DiscardPolicy.NEW,  # Discard new messages if the stream is full
            )
            await js.add_stream(config=stream_config)
            logging.info(f"Stream '{stream_name}' created with subjects: {subjects}")

        # Return the connection so it can be closed later
        return nc
    except Exception as e:
        logging.error(f"Error setting up stream: {e}")
        if nc:
            await nc.close()
        raise


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


async def _create_error_response(
    js,
    msg,
    message_data,
    error_message,
    documents_non_processed,
    output_stream,
    output_subject,
    local_env,
):
    """Create an error response and publish to NATS"""
    # Log reasons for non-processed documents
    for d in documents_non_processed:
        for key, value in d.items():
            logging.error(f"Document {key} not processed, Reason: {value}")

    out = index_response()
    out.status = {"code": 500, "message": "Error"}
    out.data = []
    out.error = error_message

    # Prepare the response
    json_response = jsonable_encoder(out)
    logging.error(json_response.get("error"))

    # Determine output subject using reply-to header when local_env is "0"
    actual_output_subject = output_subject
    if local_env == "0" and msg.headers and "reply-to" in msg.headers:
        actual_output_subject = msg.headers["reply-to"]
        logging.info(
            f"Using reply-to header for output: stream={output_stream}, subject={actual_output_subject}"
        )

    # Add metadata to response
    response_data = {
        "batchId": message_data.get("batchId", "unknown"),
        "source": message_data.get("source", {}),
        "state": {
            "status": "FAILED",
            "errorReason": error_message,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        "result": json_response,
    }

    # Publish to output stream
    try:
        await js.publish(actual_output_subject, json.dumps(response_data).encode())
        logging.info(f"Error response published to {actual_output_subject}")
        await msg.ack()
    except Exception as e:
        logging.error(f"Failed to publish error response: {e}")
        await msg.nak()


async def _create_success_response(
    js, msg, message_data, result_data, output_stream, output_subject, local_env
):
    """Create a success response and publish to NATS"""
    # Determine output subject using reply-to header when local_env is "0"
    actual_output_subject = output_subject
    if local_env == "0" and msg.headers and "reply-to" in msg.headers:
        actual_output_subject = msg.headers["reply-to"]
        logging.info(
            f"Using reply-to header for output: stream={output_stream}, subject={actual_output_subject}"
        )

    # Add metadata to response
    response_data = {
        "batchId": message_data.get("batchId", "unknown"),
        "source": message_data.get("source", {}),
        "state": {
            "status": "COMPLETED",
            "timestamp": datetime.datetime.now().isoformat(),
        },
        "result": result_data,
    }

    # Publish to output stream
    try:
        await js.publish(actual_output_subject, json.dumps(response_data).encode())
        logging.info(f"Success response published to {actual_output_subject}")
        await msg.ack()
    except Exception as e:
        logging.error(f"Failed to publish success response: {e}")
        await msg.nak()


async def process_pii_from_nats(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    local_env,
):
    """
    Receives file path from NATS, downloads/reads the file, processes the PII data,
    and publishes the result.
    args:
        nats_url (str): The NATS server URL.
        input_stream (str): The input stream name.
        input_subject (str): The input subject.
        output_stream (str): The output stream name.
        output_subject (str): The output subject.
        local_env (str): Local environment flag.
    """
    # Create an event to handle shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}. Starting graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
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
            pii_analysis[LANGUAGE_ENGINE] = PIIAnalysisService(
                language_code=LANGUAGE_ENGINE
            )

        mapper_version = version
        file_name = mapping_file_name

        # Connect to NATS using certificate if local_env is "0"
        if local_env == "0":
            ssl_builder = NatsSSLContextBuilder()
            ssl_context = ssl_builder.create_ssl_context()
            nc = await nats.connect(nats_url, tls=ssl_context)
        else:
            nc = await nats.connect(nats_url)

        js = nc.jetstream()

        async def cb(msg):
            ack_wait_seconds = 600  # Match your consumer config ack_wait
            heartbeat_interval = ack_wait_seconds / 2
            stop_heartbeat = asyncio.Event()
            heartbeat_task = None

            try:

                async def send_heartbeat():
                    while not stop_heartbeat.is_set():
                        try:
                            await asyncio.sleep(heartbeat_interval)
                            if not stop_heartbeat.is_set():
                                logging.info("Sending working ack for msg.")
                                await msg.in_progress()
                        except asyncio.CancelledError:
                            logging.info("Heartbeat task cancelled.")
                            break
                        except Exception as e:
                            logging.error(f"Error sending working ack: {e}")
                            break

                heartbeat_task = asyncio.create_task(send_heartbeat())
                time1 = datetime.datetime.now()

                # Create job tracking
                new_task = Job()
                jobs[new_task.uid] = new_task
                jobs[new_task.uid].status = "Job started"
                jobs[new_task.uid].type_job = "PII Analysis"

                # Parse the message as JSON
                message_data = json.loads(msg.data.decode("utf-8"))
                logging.info(f"Received message: {message_data}")

                # Extract URI from the message
                uri = message_data["source"]["uri"]
                logging.info(f"Processing file from URI: {uri}")

                # Download or open the file based on the URI scheme
                file_data = None
                if uri.startswith("http://") or uri.startswith("https://"):
                    # Handle HTTP URLs
                    response = requests.get(uri, verify=False)
                    if response.status_code == 200:
                        file_data = response.content
                    else:
                        logging.error(f"Failed to download file from {uri}, status code: {response.status_code}")
                        # Http download error
                        error_message = f"Failed to download file: HTTP status {response.status_code}"
                        await _create_error_response(
                            js,
                            msg,
                            message_data,
                            error_message,
                            [],
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                # Local file for local environment
                elif uri.startswith("file://") and local_env == "1":
                    # Handle local file paths with volume mount
                    file_path = uri[7:]  # Remove 'file://' prefix
                    filename = os.path.basename(file_path)
                    logging.info(f"Local file path: {file_path}")
                    docs_path = os.getenv("DOCS_PATH", "/mnt/d/repos2/pii-nats")
                    # input
                    file_path = os.path.join(
                        docs_path, filename.split("\\")[-2], filename.split("\\")[-1]
                    )
                    logging.info(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")
                        # Local file read error
                        error_message = (f"Failed to read local file {file_path}: {str(e)}")
                        await _create_error_response(
                            js,
                            msg,
                            message_data,
                            error_message,
                            [],
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                # Local file for production environment
                elif uri.startswith("file://") and local_env == "0":
                    # Handle direct file paths
                    file_path = uri[7:]  # Remove 'file://' prefix
                    logging.info(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")
                        # File read error response
                        error_message = (f"Failed to read local file {file_path}: {str(e)}")
                        await _create_error_response(
                            js,
                            msg,
                            message_data,
                            error_message,
                            [],
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                else:
                    logging.error(f"Unsupported URI scheme: {uri}")
                    # URI scheme not supported
                    error_message = f"Unsupported URI scheme: {uri}"
                    await _create_error_response(
                        js,
                        msg,
                        message_data,
                        error_message,
                        [],
                        output_stream,
                        output_subject,
                        local_env,
                    )
                    return

                logging.info(f"Downloaded file data of size: {len(file_data)} bytes")

                try:
                    # Parse the JSON file content
                    json_content = json.loads(file_data.decode("utf-8"))

                    # Extract the data that would normally come in the request
                    list_docs = json_content.get("documents", [])

                    if not isinstance(list_docs, list):
                        logging.error("Expected a list of Documents")
                        raise ValueError("Expected a list of Documents")

                    # Extract and normalize parameters
                    ocr = _parse_ocr(json_content.get("ocr", 0))
                    weights = _parse_weights(json_content.get("weights", ""))
                    score = _parse_score(
                        json_content.get("score"), GLOBAL_DOCUMENT_MIN_SCORE
                    )

                    # Determine mapper version
                    mapper_version = _determine_version(json_content.get("version"))

                    # Initialize appropriate mapper
                    mapper = _initialize_mapper(mapper_version, file_name, weights)

                    logging.info(f"Processing PII Analysis. Number of Documents {len(list_docs)}")
                    logging.info(f"Processing PII Analysis. Score: {score}")
                    logging.info(f"Processing PII Analysis. Version: {mapper_version}")
                    logging.info(f"Processing PII Analysis. Length Weights: {len(weights) if weights else 0}"                    )
                    logging.info(f"Filter Detection status {FILTER_DETECTION}")

                    # Extract Metadata
                    (
                        docs_with_languages,
                        documents_non_processed,
                    ) = await asyncio.get_event_loop().run_in_executor(
                        None,  # Use default executor
                        lambda: extract_docs(
                            list_docs=list_docs,
                            list_pii_docs=[],
                            jobs=jobs,
                            new_task=new_task,
                            file_types_all=False,
                            filenames_types=lfilenames_types,
                            image_file_names=image_file_names,
                            ocr=ocr,
                            version=mapper_version,
                            language_engine=LANGUAGE_ENGINE,
                        ),
                    )

                    logging.info(f"Documents extracted for analysis: {len(docs_with_languages)}"
                    )

                    if not docs_with_languages:
                        await _create_error_response(
                            js,
                            msg,
                            message_data,
                            "No Documents with Information or supported language in this batch",
                            documents_non_processed,
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return

                    # Process documents with appropriate version
                    if mapper_version == "v2":
                        logging.info("Starting analysis with Risk Model Version v2")
                        chunck, _, documents_non_processed = (
                            await get_pii_phi_v2_no_proxy(
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
                        )

                    # Log results
                    logging.info("Analysis process complete")
                    logging.info(f"Documents received: {len(list_docs)}")
                    logging.info(
                        f"Documents successfully analyzed: {len(docs_with_languages)}"
                    )
                    logging.warning(
                        f"Documents not analyzed: {len(documents_non_processed)}"
                    )

                    for d in documents_non_processed:
                        for key, value in d.items():
                            logging.warning(
                                f"Document {key} not processed, Reason: {value}"
                            )

                    # Prepare success response
                    out = index_response()
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

                    # Publish success response
                    await _create_success_response(
                        js,
                        msg,
                        message_data,
                        json_response,
                        output_stream,
                        output_subject,
                        local_env,
                    )

                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON file: {e}")
                    error_message = f"Error parsing JSON file: {str(e)}"
                    await _create_error_response(
                        js,
                        msg,
                        message_data,
                        error_message,
                        [],
                        output_stream,
                        output_subject,
                        local_env,
                    )
                except Exception as e:
                    stack_trace = print_stack(index_response())
                    logging.error(f"Processing error: {str(e)}")
                    error_message = f"Error processing PII analysis: {str(e)}"
                    await _create_error_response(
                        js,
                        msg,
                        message_data,
                        error_message,
                        [],
                        output_stream,
                        output_subject,
                        local_env,
                    )

                time2 = datetime.datetime.now()
                time_diff = time2 - time1
                tf = time_diff.total_seconds()
                logging.info(f"Processing time: {tf} seconds")

            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON message: {e}")
                # Create empty message_data for JSON decode errors
                empty_message = {"batchId": "unknown", "source": {}, "state": {}}
                # Json decode error response
                error_message = f"Error parsing message: {str(e)}"
                await _create_error_response(
                    js,
                    msg,
                    empty_message,
                    error_message,
                    [],
                    output_stream,
                    output_subject,
                    local_env,
                )
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                # Create empty message_data for other errors
                message_info = {"batchId": "unknown", "source": {}, "state": {}}
                try:
                    if "message_data" in locals() and message_data:
                        message_info = message_data
                except:
                    pass  # If we can't get message_data, use defaults
                # Generate error response
                error_message = f"Error processing message: {str(e)}"
                await _create_error_response(
                    js,
                    msg,
                    message_info,
                    error_message,
                    [],
                    output_stream,
                    output_subject,
                    local_env,
                )
            finally:
                if heartbeat_task:
                    stop_heartbeat.set()
                    try:
                        heartbeat_task.cancel()  # Cancel the heartbeat task
                        await heartbeat_task  # Ensure heartbeat task finishes cleanly
                    except Exception as e:
                        logging.error(f"Error cleaning up heartbeat task: {e}")

        # Setup version endpoint
        await setup_version_endpoint(nc, 
            os.getenv("VERSION_SUBJECT", "pii.app.version"),
            os.getenv("VERSION_QUEUE_GROUP", "pii.version.queue.group")
        )

        # Setup health check endpoint
        await setup_health_check_endpoint(nc, get_health_check_subject())

        # Configure the consumer
        consumer_config = ConsumerConfig(
            durable_name="pii-processor-start",
            deliver_group="pii-processing-start-group",
            ack_wait=600,  # 10 min ack timeout
            max_deliver=3,  # Limit redeliveries
            ack_policy=AckPolicy.EXPLICIT,
        )

        # Pull messages from the stream
        sub = await js.pull_subscribe(
            input_subject,
            stream=input_stream,
            durable=consumer_config.durable_name,
            config=consumer_config,
        )

        logging.info(f"Subscribed to {input_subject} in stream {input_stream}")

        while nc.is_connected and not shutdown_event.is_set():
            try:
                messages = await sub.fetch(batch=1)
                for msg in messages:
                    if shutdown_event.is_set():
                        logging.info("Shutdown requested, stopping message processing")
                        break
                    await cb(msg)
            except nats.errors.TimeoutError:
                pass  # Silently ignore timeout errors

        logging.info("Exiting message processing loop")

    except Exception as e:
        logging.error(f"Error in NATS subscription: {e}")
    finally:
        logging.info("Closing NATS connection...")
        await nc.close()
        logging.info("NATS connection closed")


async def run_nats_pii(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    local_env,
):
    """Run the NATS PII processing.
    Args:
        nats_url (str): The NATS server URL.
        input_stream (str): The input stream name.
        input_subject (str): The input subject.
        output_stream (str): The output stream name.
        output_subject (str): The output subject.
        local_env (str): Local environment flag.
    """
    # Setup input stream
    await setup_stream(
        nats_url=nats_url,
        local_env=local_env,
        stream_name=input_stream,
        subjects=[input_subject],
    )

    # Setup output stream
    await setup_stream(
        nats_url=nats_url,
        local_env=local_env,
        stream_name=output_stream,
        subjects=[output_subject],
    )

    # Start processing messages
    await process_pii_from_nats(
        nats_url,
        input_stream,
        input_subject,
        output_stream,
        output_subject,
        local_env,
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process PII requests from NATS.")
    parser.add_argument(
        "--nats-url", type=str, default="nats://localhost:4222", help="NATS server URL."
    )
    parser.add_argument(
        "--input-stream",
        type=str,
        default="PII-TASKS",
        help="NATS input stream name.",
    )
    parser.add_argument(
        "--input-subject",
        type=str,
        default="pii.tasks.started.>",
        help="NATS input subject.",
    )
    parser.add_argument(
        "--output-stream",
        type=str,
        default="PII-RESULTS",
        help="NATS output stream name.",
    )
    parser.add_argument(
        "--output-subject",
        type=str,
        default="pii.results.completed.>",
        help="NATS output subject.",
    )

    args = parser.parse_args()

    # Root directory of the project
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Set up logging
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
        log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s%(color_off)s",
    ):
        print("Failed to set up logging, aborting.")
        raise AttributeError("Failed to create logging")

    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys", ".env")
    status = load_dotenv(env_path)
    logging.info(f"Status load .env file {str(status)}")

    # Setup ENV variables
    LOCAL_ENV = os.getenv("LOCAL_ENV") if "LOCAL_ENV" in os.environ else "1"
    IS_LOCAL = os.getenv("IS_LOCAL") if "IS_LOCAL" in os.environ else "0"
    LANGUAGE_ENGINE = os.getenv("LANGUAGE_ENGINE", "en")
    TURN_ON_CERT_LOGGING = os.getenv("TURN_ON_CERT_LOGGING", "NO")

    logging.info(f"IS LOCAL ENVIRONMENT {LOCAL_ENV}")

    # Set NATS variables
    if IS_LOCAL == "1":
        NAT_URL = os.getenv("NAT_URL") if "NAT_URL" in os.environ else args.nats_url
        if NAT_URL is None:
            raise AttributeError("NAT_URL not found in environment variables")
        INPUT_STREAM = (os.getenv("INPUT_STREAM") if "INPUT_STREAM" in os.environ else args.input_stream)
        INPUT_SUBJECT = (os.getenv("INPUT_SUBJECT") if "INPUT_SUBJECT" in os.environ else args.input_subject)
        OUTPUT_STREAM = (os.getenv("OUTPUT_STREAM") if "OUTPUT_STREAM" in os.environ else args.output_stream)
        OUTPUT_SUBJECT = (os.getenv("OUTPUT_SUBJECT") if "OUTPUT_SUBJECT" in os.environ else args.output_subject)
    elif LOCAL_ENV == "0":
        # IN prod environment NATS server variables are in AKS environment variables
        NAT_URL = os.getenv("NATS_ENDPOINT") if "NATS_ENDPOINT" in os.environ else None
        INPUT_STREAM = (os.getenv("INPUT_STREAM") if "INPUT_STREAM" in os.environ else None)
        INPUT_SUBJECT = (os.getenv("INPUT_SUBJECT") if "INPUT_SUBJECT" in os.environ else None)
        OUTPUT_STREAM = (os.getenv("OUTPUT_STREAM") if "OUTPUT_STREAM" in os.environ else None)
        OUTPUT_SUBJECT = (os.getenv("OUTPUT_SUBJECT") if "OUTPUT_SUBJECT" in os.environ else None)
        CERTIFICATES_PATH = os.getenv("CERTIFICATES_PATH")
        if CERTIFICATES_PATH is None:
            raise AttributeError("CERTIFICATES_PATH not found in environment variables")

        if any(
            var is None
            for var in [
                NAT_URL,
                INPUT_STREAM,
                INPUT_SUBJECT,
                OUTPUT_STREAM,
                CERTIFICATES_PATH,
            ]
        ):
            raise AttributeError("Required NATS environment variables not found")

    # Set version and health check subjects
    VERSION_SUBJECT = os.getenv("VERSION_SUBJECT", "pii.app.version")
    VERSION_QUEUE_GROUP = os.getenv("VERSION_QUEUE_GROUP", "pii.version.queue.group")
    HEALTH_CHECK_SUBJECT = get_health_check_subject_formatted()
    HEALTH_CHECK_SUBJECT_TEMPLATE = f"{get_health_check_subject()}.>"
    NATS_VERIFY_CERT = (
        os.getenv("NATS_VERBOSECERTIFICATEVERIFICATION", "true").lower() == "true"
    )
    NATS_CERT_LOGGING = os.getenv("NATS_CERTIFICATE_LOGGING", "NO").lower() == "yes"

    # Detect environment
    env = detect_environment()
    logging.info(f"Environment detected: {env}")

    # Log configuration
    logging.info(f"NATS URL: {NAT_URL}")
    logging.info("Application Version is:" + os.getenv("APPLICATIONVERSION"))
    logging.info("CERTIFICATES_PATH:" + os.getenv("CERTIFICATES_PATH"))
    logging.info(f"NATS Certificate Verification Enabled: {NATS_VERIFY_CERT}")
    logging.info(f"NATS Certificate Logging Enabled: {NATS_CERT_LOGGING}")
    logging.info(f"Certificate Logging: {TURN_ON_CERT_LOGGING}")
    logging.info(f"Input Stream: {INPUT_STREAM}")
    logging.info(f"Input Subject: {INPUT_SUBJECT}")
    logging.info(f"Output Stream: {OUTPUT_STREAM}")
    logging.info(f"Output Subject: {OUTPUT_SUBJECT}")
    logging.info(f"Version Subject: {VERSION_SUBJECT}")
    logging.info(f"Version Queue Group: {VERSION_QUEUE_GROUP}")
    logging.info(f"Health Check Subject: {HEALTH_CHECK_SUBJECT}")
    logging.info(f"Health Check Subject Template: {HEALTH_CHECK_SUBJECT_TEMPLATE}")

    # Run the NATS PII processing
    asyncio.run(
        run_nats_pii(
            nats_url=NAT_URL,
            input_stream=INPUT_STREAM,
            input_subject=INPUT_SUBJECT,
            output_stream=OUTPUT_STREAM,
            output_subject=OUTPUT_SUBJECT,
            local_env=LOCAL_ENV,
        )
    )
