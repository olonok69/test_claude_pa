import asyncio
import argparse
from rapidocr_onnxruntime import RapidOCR
import datetime
import logging
import os
from pathlib import Path
from detectaicore import set_up_logging
import asyncio
import nats
from nats.js.api import ConsumerConfig, AckPolicy, RetentionPolicy, DiscardPolicy, StreamConfig
from dotenv import load_dotenv
import json
import requests
import socket
import psutil
from utils.utils import process_request_nat
from utils.environment import detect_environment
from utils.ssl_utils import NatsSSLContextBuilder
from utils.schemas import (
    handle_error_and_acknowledge,
    handle_success_and_acknowledge,
)
import signal

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_engine_rapidocr(config_path: str = None):
    """
    Create RapidOCR Engine
    return:
    RapidOCR Engine
    """
    # create RapidOCR Engine
    engine = RapidOCR(config_path=config_path)
    return engine


def get_health_check_subject_formatted():
    """
    Constructs the health check subject using the pod hostname.

    Returns:
        str: Formatted health check subject including hostname
    """
    base_subject = get_health_check_subject()
    hostname = socket.gethostname()
    return f"{base_subject}.{hostname}"


def get_health_check_subject():
    """
    gets the health check subject from the environment.

    Returns:
        str: health check subject
    """
    base_subject = os.getenv("HEALTH_CHECK_SUBJECT", "ocr.app.health.check")
    return base_subject


async def setup_version_endpoint(nc):
    """
    Sets up a NATS endpoint that responds with the application version.

    Args:
        nc: NATS connection
    """
    version_subject = os.getenv("VERSION_SUBJECT", "ocr.app.version")
    queue_group = os.getenv("VERSION_QUEUE_GROUP", "ocr.version.queue.group")

    async def version_handler(msg):
        try:
            app_version = os.getenv("APPLICATIONVERSION", "unknown")
            response = {
                "version": app_version,
                "hostname": socket.gethostname(),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await msg.respond(json.dumps(response).encode())
            logging.debug(f"Version request handled: {app_version}")
        except Exception as e:
            logging.error(f"Error handling version request: {e}")
            error_response = {
                "error": "Failed to get version information",
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await msg.respond(json.dumps(error_response).encode())

    # Subscribe to the version subject with queue group
    await nc.subscribe(version_subject, queue=queue_group, cb=version_handler)
    logging.debug(
        f"Version endpoint setup complete. Subject: {version_subject}, Queue: {queue_group}"
    )


async def setup_health_check_endpoint(nc):
    """
    Sets up NATS endpoints that respond to both specific and broadcast health check requests.

    Args:
        nc: NATS connection
    """
    hostname = socket.gethostname()
    instance_subject = get_health_check_subject_formatted()
    broadcast_subject = os.getenv(
        "HEALTH_CHECK_SUBJECT_TEMPLATE", "ocr.app.health.check.>"
    )

    async def health_check_handler(msg):
        try:
            response = {
                "status": "OK",
                "hostname": hostname,
                "timestamp": datetime.datetime.now().isoformat(),
                "uptime": psutil.boot_time(),
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(),
            }

            await msg.respond(json.dumps(response).encode())
            logging.debug(f"Health check handled for subject: {msg.subject}")
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            error_response = {
                "status": "ERROR",
                "hostname": hostname,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
            }

            await msg.respond(json.dumps(error_response).encode())

    await nc.subscribe(instance_subject, cb=health_check_handler)
    logging.debug(f"Health check endpoint setup on subject: {instance_subject}")

    await nc.subscribe(broadcast_subject, cb=health_check_handler)
    logging.debug(
        f"Health check endpoint setup on broadcast subject: {broadcast_subject}"
    )


async def process_ocr_from_nats(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    config_path,
    doc_path,
    local_env,
    language,
):
    """
    Receives document metadata from NATS, downloads the document, processes it,
    and publishes the result.
    args:
        nats_url (str): The NATS server URL.
        input_stream (str): The input stream name.
        input_subject (str): The input subject.
        output_stream (str): The output stream name.
        output_subject (str): The output subject.
        config_path (str): The path to the configuration file.
        doc_path (str): The path to the documents directory.
        local_env (str): Local environment flag.
        language (str): Language for OCR processing.
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
        # Connect to NATS using certificate if local_env is "0"
        if local_env == "0":
            ssl_builder = NatsSSLContextBuilder()
            ssl_context = ssl_builder.create_ssl_context()
            nc = await nats.connect(nats_url, tls=ssl_context)
        else:
            nc = await nats.connect(nats_url)

        js = nc.jetstream()
        engine = create_engine_rapidocr(
            config_path=config_path
        )  # Initialize OCR engine

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
                        logging.error(
                            f"Failed to download file from {uri}, status code: {response.status_code}"
                        )

                        # Http download error
                        error_message = f"Failed to download file: HTTP status {response.status_code}"
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "download-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                # Local remote
                elif uri.startswith("file://") and LOCAL_ENV == "1":
                    # Handle local file paths. Here the file is in the local environment (volume mount) and we use the env variable DOCS_PATH
                    file_path = uri[7:]  # Remove 'file://' prefix
                    filename = os.path.basename(file_path)
                    logging.info(f"Local file path: {file_path}")
                    file_path = os.path.join(doc_path, filename)
                    logging.info(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")

                        # Local file read error
                        error_message = (
                            f"Failed to read local file {file_path}: {str(e)}"
                        )
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "file-read-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                elif uri.startswith("file://") and LOCAL_ENV == "0":
                    # Handle local file paths
                    file_path = uri[7:]  # Remove 'file://' prefix
                    logging.info(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")

                        # File read error response
                        error_message = (
                            f"Failed to read local file {file_path}: {str(e)}"
                        )
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "file-read-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                else:
                    logging.error(f"Unsupported URI scheme: {uri}")

                    # URI scheme not supported
                    error_message = f"Unsupported URI scheme: {uri}"
                    await handle_error_and_acknowledge(
                        js,
                        msg,
                        message_data,
                        error_message,
                        "unsupported-uri",
                        output_stream,
                        output_subject,
                        local_env,
                    )
                    return

                logging.warning(f"Downloaded file data of size: {len(file_data)} bytes")

                # Determine output stream and subject using reply-to header when local_env is "0"
                actual_output_stream = output_stream
                actual_output_subject = output_subject

                if local_env == "0" and msg.headers and "reply-to" in msg.headers:
                    # the Output subject comes in the header reply-to
                    actual_output_subject = msg.headers["reply-to"]
                    logging.info(
                        f"Using reply-to header for output: stream={actual_output_stream}, subject={actual_output_subject}"
                    )

                # Process the file data using process_request
                try:
                    # Apply any pre-processing steps specified in the message
                    pre_processing = message_data.get("options", {}).get(
                        "preProcessing", []
                    )
                    # ocr file
                    loop = asyncio.get_running_loop()
                    logging.info("Submitting OCR task to executor...")
                    extracted_text = await loop.run_in_executor(
                        None,                   # Use default ThreadPoolExecutor
                        process_request_nat,
                        file_data,
                        engine,
                        pre_processing
                    )
                    logging.info("OCR task completed with extracted text.")

                    # success response
                    await handle_success_and_acknowledge(
                        js,
                        msg,
                        message_data,
                        extracted_text,
                        language,
                        output_stream,
                        output_subject,
                        local_env,
                    )
                except Exception as e:
                    logging.error(f"Processing error: {str(e)}")

                    # Process the error and send an error response
                    error_message = f"Processing error: {str(e)}"
                    await handle_error_and_acknowledge(
                        js,
                        msg,
                        message_data,
                        error_message,
                        "processing-error",
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
                await handle_error_and_acknowledge(
                    js,
                    msg,
                    empty_message,
                    error_message,
                    "json-decode-error",
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
                await handle_error_and_acknowledge(
                    js,
                    msg,
                    message_info,
                    error_message,
                    "general-error",
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

        consumer_config = ConsumerConfig(
            durable_name="ocr-processor-start",             # Durable state
            deliver_group="ocr-processing-start-group",     # For scaling (queue group)
            ack_wait=600,                                   # 10 min ack timeout
            max_deliver=3,                                  # Limit redeliveries
            ack_policy=AckPolicy.EXPLICIT                  # Optional: Be explicit about ack policy
        )

        try:
            consumer_info = await js.add_consumer(stream=input_stream, config=consumer_config)
            logging.info(f"Consumer '{consumer_info.config.durable_name}' is configured on stream '{input_stream}'.")
        except Exception as e:
            logging.error(f"Error creating/updating consumer '{consumer_config.durable_name}': {e}")
            raise

        # Setup version endpoint
        await setup_version_endpoint(nc)

        # Setup health check endpoint
        await setup_health_check_endpoint(nc)

        # Pull messages from the stream
        sub = await js.pull_subscribe(input_subject, stream=input_stream, durable=consumer_config.durable_name)

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

async def run_nats_ocr(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    config_path,
    doc_path,
    local_env,
    language,
):
    """Run the NATS OCR processing.
    Args:
        nats_url (str): The NATS server URL.
        input_stream (str): The input stream name.
        input_subject (str): The input subject.
        output_stream (str): The output stream name.
        output_subject (str): The output subject.
        config_path (str): The path to the configuration file.
        doc_path (str): The path to the documents directory.
        local_env (str): Local environment flag.
        language (str): Language for OCR processing.
    """
    await setup_stream(
        nats_url=nats_url,
        local_env=local_env,
        stream_name=input_stream,
        subjects=[input_subject],
    )

    await process_ocr_from_nats(
        nats_url,
        input_stream,
        input_subject,
        output_stream,
        output_subject,
        config_path,
        doc_path,
        local_env,
        language,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process OCR requests from NATS.")
    parser.add_argument(
        "--nats-url", type=str, default="nats://localhost:4222", help="NATS server URL."
    )
    parser.add_argument(
        "--input-stream",
        type=str,
        default="IMAGE_STREAM",
        help="NATS input stream name.",
    )
    parser.add_argument(
        "--input-subject",
        type=str,
        default="images.process",
        help="NATS input subject.",
    )
    parser.add_argument(
        "--output-stream",
        type=str,
        default="TEXT_STREAM",
        help="NATS output stream name.",
    )
    parser.add_argument(
        "--output-subject",
        type=str,
        default="text.results",
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
        log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s%(color_off)s",  # Added filename and line number
    ):
        print("Failed to set up logging, aborting.")
        raise AttributeError("failed to create logging")
    # load credentials
    env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "keys", ".env_file"
    )
    status = load_dotenv(env_path)
    logging.info(f"Status load .env file {str(status)}")

    #### setup ENV variables
    LOCAL_ENV = os.getenv("LOCAL_ENV") if "LOCAL_ENV" in os.environ else "1"
    IS_LOCAL = os.getenv("IS_LOCAL") if "IS_LOCAL" in os.environ else "0"
    LANGUAGE = os.getenv("LANGUAGE") if "LANGUAGE" in os.environ else "en"
    NATS_VERIFY_CERT = (
        os.getenv("NATS_VERBOSECERTIFICATEVERIFICATION", "true").lower() == "true"
    )

    # working in local computer
    if IS_LOCAL == "1":
        NAT_URL = os.getenv("NAT_URL") if "NAT_URL" in os.environ else args.nats_url
        if NAT_URL is None:
            raise AttributeError("NAT_URL not found in environment variables")
        INPUT_STREAM = (
            os.getenv("INPUT_STREAM")
            if "INPUT_STREAM" in os.environ
            else args.input_stream
        )
        INPUT_SUBJECT = (
            os.getenv("INPUT_SUBJECT")
            if "INPUT_SUBJECT" in os.environ
            else args.input_subject
        )
        OUTPUT_STREAM = (
            os.getenv("OUTPUT_STREAM")
            if "OUTPUT_STREAM" in os.environ
            else args.output_stream
        )
        OUTPUT_SUBJECT = (
            os.getenv("OUTPUT_SUBJECT")
            if "OUTPUT_SUBJECT" in os.environ
            else args.output_subject
        )
    elif LOCAL_ENV == "0":
        # IN prod environment NATS server variables are in AKS environment variables
        NAT_URL = os.getenv("NATS_ENDPOINT") if "NATS_ENDPOINT" in os.environ else None
        INPUT_STREAM = (
            os.getenv("INPUT_STREAM") if "INPUT_STREAM" in os.environ else None
        )
        INPUT_SUBJECT = (
            os.getenv("INPUT_SUBJECT") if "INPUT_SUBJECT" in os.environ else None
        )
        OUTPUT_STREAM = (
            os.getenv("OUTPUT_STREAM") if "OUTPUT_STREAM" in os.environ else None
        )
        OUTPUT_SUBJECT = None
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
            raise AttributeError("NAT_URL not found in environment variables")

    DEFAULT_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config.yaml")
    PROD_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config_prod.yaml")
    # Check which type of environtment we are running in
    env = detect_environment()
    logging.info(f"Environment detected: {env}")

    VERSION_SUBJECT = os.getenv("VERSION_SUBJECT", "ocr.app.version")
    VERSION_QUEUE_GROUP = os.getenv("VERSION_QUEUE_GROUP", "ocr.version.queue.group")
    HEALTH_CHECK_SUBJECT = get_health_check_subject_formatted()
    HEALTH_CHECK_SUBJECT_TEMPLATE = f"{get_health_check_subject()}.>"

    if (
        env in ["Local Windows", "Windows Subsystem for Linux (WSL)"]
        and IS_LOCAL == "1"
    ):
        CFG_PATH = DEFAULT_CFG_PATH
    else:
        CFG_PATH = PROD_CFG_PATH

    DOCS_PATH = os.getenv("DOCS_PATH")
    if DOCS_PATH is None:
        raise AttributeError("DOCS_PATH not found in environment variables")
    logging.info(f"Configuration path: {CFG_PATH}")
    logging.info(f"NATS URL: {NAT_URL}")
    logging.info("Application Version is:" + os.getenv("APPLICATIONVERSION"))
    logging.info("CERTIFICATES_PATH:" + os.getenv("CERTIFICATES_PATH"))
    logging.info(f"NATS Certificate Verification Enabled: {NATS_VERIFY_CERT}")
    logging.info(f"Input Stream: {INPUT_STREAM}")
    logging.info(f"Input Subject: {INPUT_SUBJECT}")
    logging.info(f"Output Stream: {OUTPUT_STREAM}")
    logging.info(f"Output Subject: {OUTPUT_SUBJECT}")
    logging.info(f"Version Subject: {VERSION_SUBJECT}")
    logging.info(f"Version Queue Group: {VERSION_QUEUE_GROUP}")
    logging.info(f"Health Check Subject: {HEALTH_CHECK_SUBJECT}")
    logging.info(f"Health Check Subject Template: {HEALTH_CHECK_SUBJECT_TEMPLATE}")

    # Run the NATS OCR processing
    asyncio.run(
        run_nats_ocr(
            nats_url=NAT_URL,
            input_stream=INPUT_STREAM,
            input_subject=INPUT_SUBJECT,
            output_stream=OUTPUT_STREAM,
            output_subject=OUTPUT_SUBJECT,
            config_path=CFG_PATH,
            doc_path=DOCS_PATH,
            local_env=LOCAL_ENV,
            language=LANGUAGE,
        )
    )
