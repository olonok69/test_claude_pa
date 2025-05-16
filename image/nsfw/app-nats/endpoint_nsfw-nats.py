import asyncio
import argparse
import datetime
import logging
import os
from pathlib import Path
from detectaicore import set_up_logging, Job
import asyncio
import nats
from nats.js.api import (
    ConsumerConfig,
    AckPolicy,
    RetentionPolicy,
    DiscardPolicy,
    StreamConfig,
)
from dotenv import load_dotenv
import json
import requests
import socket
import psutil
import signal
import sys
import gc
import copy
from src.inference import load_onnx_model
from utils.ssl_utils import NatsSSLContextBuilder
from utils.environment import detect_environment
from utils.schemas import (
    handle_error_and_acknowledge,
    handle_success_and_acknowledge,
)
from src.utils import process_request


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_nsfw_model(model_path):
    """
    Load ONNX NSFW model
    Args:
        model_path (str): Path to the ONNX model file
    Returns:
        ONNX model for inference
    """
    try:
        logging.info(f"Loading ONNX Model from {model_path}")
        # load model
        model = load_onnx_model(model_path=model_path)
        return model
    except Exception as e:
        ex_type, ex_value, ex_traceback = sys.exc_info()
        logging.error(f"Exception {ex_type} value {str(ex_value)}")
        raise


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
    base_subject = os.getenv("HEALTH_CHECK_SUBJECT", "nsfw.app.health.check")
    return base_subject


async def setup_version_endpoint(nc):
    """
    Sets up a NATS endpoint that responds with the application version.

    Args:
        nc: NATS connection
    """
    version_subject = os.getenv("VERSION_SUBJECT", "nsfw.app.version")
    queue_group = os.getenv("VERSION_QUEUE_GROUP", "nsfw.version.queue.group")

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
        "HEALTH_CHECK_SUBJECT_TEMPLATE", "nsfw.app.health.check.>"
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


async def process_nsfw_from_nats(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    models_path,
    local_env,
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
        models_path (str): The path to the models directory.
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
        # Load NSFW model
        model_path = os.path.join(models_path, "onnx", "vit_nsfw.onnx")
        model = load_nsfw_model(model_path)

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

                # Parse the message as JSON
                message_data = json.loads(msg.data.decode("utf-8"))
                logging.info(f"Received message: {message_data}")

                # Extract URI from the message
                uri = message_data["source"]["uri"]
                file_type = message_data["source"]["file_type"]
                file_name = message_data["source"].get("file_name", "unnamed_file")

                # Get threshold value if provided, otherwise use default
                threshold = 0.5
                if "options" in message_data and "threshold" in message_data["options"]:
                    threshold_value = message_data["options"]["threshold"]
                    if isinstance(threshold_value, (float, int)) or (
                        isinstance(threshold_value, str) and len(threshold_value) > 0
                    ):
                        try:
                            threshold = float(threshold_value)
                        except (ValueError, TypeError):
                            threshold = 0.5

                logging.info(
                    f"Processing file from URI: {uri} with threshold: {threshold}"
                )
                logging.info(f"Processing image from URI: {uri}")
                IS_DOCKER = os.getenv("IS_DOCKER", "0")
                IMAGES_PATH = os.getenv("IMAGES_PATH", "/app/images")
                logging.info(f"IS_DOCKER: {IS_DOCKER}")
                logging.info(f"IMAGES_PATH: {IMAGES_PATH}")
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
                elif uri.startswith("file://") and local_env == "1":
                    if IS_DOCKER == "1":
                        # Handle file paths in Docker environment
                        original_path = uri[7:]  # Remove 'file://' prefix
                        filename = os.path.basename(original_path)
                        file_path = os.path.join(IMAGES_PATH, filename)
                        logging.info(
                            f"Docker file path: {file_path} (original: {original_path})"
                        )
                    else:
                        # Handle local file paths in test environment
                        file_path = uri[7:]  # Remove 'file://' prefix
                        logging.info(f"Local file path: {file_path}")
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
                elif uri.startswith("file://") and local_env == "0":
                    # Handle local file paths in production
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

                # Process the file data using the NSFW model
                try:
                    # Create a list with one document as expected by process_request
                    document = {
                        "id": message_data.get("id", "unknown"),
                        "source": {
                            "content": base64.b64encode(file_data).decode("utf-8"),
                            "file_type": file_type,
                            "file_name": file_name,
                        },
                    }

                    list_docs = [document]

                    # Create a job object with a uid (fixes the error)
                    new_task = Job()
                    jobs = {new_task.uid: new_task}

                    # Initialize the job
                    jobs[new_task.uid].status = "Job started"
                    jobs[new_task.uid].type_job = "NSFW Model Analysis"

                    # Use the existing process_request function
                    loop = asyncio.get_running_loop()
                    logging.info("Submitting NSFW analysis task to executor...")
                    processed_docs, documents_non_treated = await loop.run_in_executor(
                        None,  # Use default ThreadPoolExecutor
                        process_request,
                        list_docs,
                        model,
                        threshold,
                        jobs,
                        new_task,
                    )

                    if processed_docs and len(processed_docs) > 0:
                        # Success response
                        result = processed_docs[0]

                        # Create a response structure
                        response_data = {
                            "id": message_data.get("id", "unknown"),
                            "batchId": message_data.get("batchId", "unknown"),
                            "nsfw_results": result["source"]["content"],
                            "file_name": file_name,
                            "file_type": file_type,
                            "threshold": threshold,
                        }

                        await js.publish(
                            actual_output_subject,
                            json.dumps(response_data).encode(),
                            stream=actual_output_stream,
                        )
                        await msg.ack()
                        logging.info(
                            f"NSFW analysis completed and result published to {actual_output_subject}"
                        )
                    else:
                        # No results were generated
                        error_message = "No NSFW analysis results were generated"
                        if documents_non_treated and len(documents_non_treated) > 0:
                            error_message += f": {documents_non_treated[0].get(document['id'], 'Unknown error')}"

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

                # Cleanup to avoid memory leaks
                del file_data
                if "processed_docs" in locals():
                    del processed_docs
                gc.collect()

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
            durable_name="nsfw-processor-start",  # Durable state
            deliver_group="nsfw-processing-start-group",  # For scaling (queue group)
            ack_wait=600,  # 10 min ack timeout
            max_deliver=3,  # Limit redeliveries
            ack_policy=AckPolicy.EXPLICIT,  # Optional: Be explicit about ack policy
        )

        # Setup version endpoint
        await setup_version_endpoint(nc)

        # Setup health check endpoint
        await setup_health_check_endpoint(nc)

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


async def run_nats_nsfw(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    models_path,
    local_env,
):
    """Run the NATS NSFW processing.
    Args:
        nats_url (str): The NATS server URL.
        input_stream (str): The input stream name.
        input_subject (str): The input subject.
        output_stream (str): The output stream name.
        output_subject (str): The output subject.
        models_path (str): The path to the models directory.
        local_env (str): Local environment flag.
    """
    # Ensure output stream exists as well
    await setup_stream(
        nats_url=nats_url,
        local_env=local_env,
        stream_name=output_stream,
        subjects=[output_subject],
    )

    # Setup input stream
    await setup_stream(
        nats_url=nats_url,
        local_env=local_env,
        stream_name=input_stream,
        subjects=[input_subject],
    )

    await process_nsfw_from_nats(
        nats_url,
        input_stream,
        input_subject,
        output_stream,
        output_subject,
        models_path,
        local_env,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process NSFW requests from NATS.")
    parser.add_argument(
        "--nats-url", type=str, default="nats://localhost:4222", help="NATS server URL."
    )
    parser.add_argument(
        "--input-stream",
        type=str,
        default="NSFW-TASKS",
        help="NATS input stream name.",
    )
    parser.add_argument(
        "--input-subject",
        type=str,
        default="nsfw.tasks.started.>",
        help="NATS input subject.",
    )
    parser.add_argument(
        "--output-stream",
        type=str,
        default="NSFW-RESULTS",
        help="NATS output stream name.",
    )
    parser.add_argument(
        "--output-subject",
        type=str,
        default="nsfw.results.completed.>",
        help="NATS output subject.",
    )

    args = parser.parse_args()

    # Import here to avoid circular import issues
    import base64

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
    LOCAL_ENV = os.getenv("LOCAL_ENV", "1")  # LOCAL_ENV from .env file
    HOME = os.getenv("HOME", "/home/detectai")
    USE_ONNX = os.getenv("USE_ONNX", "YES")
    NATS_VERIFY_CERT = os.getenv("TURN_ON_CERT_LOGGING", "YES").lower() == "yes"

    # NATS configuration
    NAT_URL = os.getenv("NATS_ENDPOINT") or os.getenv("NAT_URL")
    NATS_ENDPOINT = os.getenv("NATS_ENDPOINT")
    INPUT_STREAM = os.getenv("INPUT_STREAM", args.input_stream)
    INPUT_SUBJECT = os.getenv("INPUT_SUBJECT", args.input_subject)
    OUTPUT_STREAM = os.getenv("OUTPUT_STREAM", args.output_stream)
    OUTPUT_SUBJECT = os.getenv("OUTPUT_SUBJECT", args.output_subject)

    # Models path
    if os.getenv("MODEL_PATH"):
        MODELS_PATH = os.getenv("MODEL_PATH","/app/models")
    else:
        MODELS_PATH = os.path.join(ROOT_DIR, "models")

    VERSION_SUBJECT = os.getenv("VERSION_SUBJECT", "nsfw.app.version")
    VERSION_QUEUE_GROUP = os.getenv("VERSION_QUEUE_GROUP", "nsfw.version.queue.group")
    HEALTH_CHECK_SUBJECT = get_health_check_subject_formatted()
    HEALTH_CHECK_SUBJECT_TEMPLATE = f"{get_health_check_subject()}.>"

    # Check which type of environment we are running in
    env = detect_environment()
    logging.info(f"Environment detected: {env}")

    # Log configuration
    logging.info(f"NATS URL: {NAT_URL}")
    logging.info(f"NATS_ENDPOINT: {NATS_ENDPOINT}")
    logging.info(f"Models Path: {MODELS_PATH}")
    logging.info(f"NATS Certificate Verification Enabled: {NATS_VERIFY_CERT}")
    logging.info(f"Input Stream: {INPUT_STREAM}")
    logging.info(f"Input Subject: {INPUT_SUBJECT}")
    logging.info(f"Output Stream: {OUTPUT_STREAM}")
    logging.info(f"Output Subject: {OUTPUT_SUBJECT}")
    logging.info(f"Version Subject: {VERSION_SUBJECT}")
    logging.info(f"Version Queue Group: {VERSION_QUEUE_GROUP}")
    logging.info(f"Health Check Subject: {HEALTH_CHECK_SUBJECT}")
    logging.info(f"Health Check Subject Template: {HEALTH_CHECK_SUBJECT_TEMPLATE}")

    # Run the NATS NSFW processing
    asyncio.run(
        run_nats_nsfw(
            nats_url=NAT_URL,
            input_stream=INPUT_STREAM,
            input_subject=INPUT_SUBJECT,
            output_stream=OUTPUT_STREAM,
            output_subject=OUTPUT_SUBJECT,
            models_path=MODELS_PATH,
            local_env=LOCAL_ENV,
        )
    )
