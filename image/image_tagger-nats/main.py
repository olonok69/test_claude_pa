import os
import asyncio
import logging
import signal
import sys
import torch
import platform
from pathlib import Path
from dotenv import load_dotenv

from detectaicore import set_up_logging, setup_stream

# Import our new modularized code
from utils.message_handlers import process_image_from_nats


# Set up logging
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_PATH = os.path.join(ROOT_DIR, "logs")
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
    raise AttributeError("failed to create logging")

# Load environment variables
env_path = os.path.join(ROOT_DIR, "keys", ".env_file")
status = load_dotenv(env_path)
logging.info(f"Status load .env file {str(status)}")

# Get environment variables
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
USE_ONNX = os.getenv("USE_ONNX", "NO")
USE_OPENVINO = os.getenv("USE_OPENVINO", "YES")
DEVICE_OV = os.getenv("DEVICE_OV", "CPU")

# Get the DOCKER_TASK environment variable to determine operation mode
DOCKER_TASK = os.getenv("DOCKER_TASK", "tagger").lower()
if DOCKER_TASK not in ["tagger", "caption"]:
    logging.error(
        f"Invalid DOCKER_TASK value: {DOCKER_TASK}. Must be 'tagger' or 'caption'"
    )
    sys.exit(1)

logging.info(f"========== OPERATING MODE: {DOCKER_TASK.upper()} ==========")

# Set stream and subject variables based on the operation mode
if DOCKER_TASK == "tagger":
    INPUT_STREAM = os.getenv("INPUT_STREAM_TAGGER")
    INPUT_SUBJECT = os.getenv("INPUT_SUBJECT_TAGGER", "tagger.tasks.started.>")
    OUTPUT_STREAM = os.getenv("OUTPUT_STREAM_TAGGER")
    OUTPUT_SUBJECT = os.getenv("OUTPUT_SUBJECT_TAGGER", "tagger.results.completed.>")
    OPERATION_MODE = "tagging"
else:  # caption mode
    INPUT_STREAM = os.getenv("INPUT_STREAM_CAPTIONING")
    INPUT_SUBJECT = os.getenv("INPUT_SUBJECT_CAPTIONING", "caption.tasks.started.>")
    OUTPUT_STREAM = os.getenv("OUTPUT_STREAM_CAPTIONING")
    OUTPUT_SUBJECT = os.getenv(
        "OUTPUT_SUBJECT_CAPTIONING", "caption.results.completed.>"
    )
    OPERATION_MODE = "captioning"

IMAGES_PATH = os.getenv("IMAGES_PATH", os.path.join(ROOT_DIR, "images"))

NAT_URL = os.getenv("NATS_ENDPOINT") or os.getenv("NAT_URL")
NATS_ENDPOINT = os.getenv("NATS_ENDPOINT")
CERTIFICATES_PATH = os.getenv("CERTIFICATES_PATH")
VERSION_SUBJECT = os.getenv("VERSION_SUBJECT")
VERSION_QUEUE_GROUP = os.getenv("VERSION_QUEUE_GROUP")
HEALTH_CHECK_SUBJECT = os.getenv("HEALTH_CHECK_SUBJECT")

logging.info(f"IS LOCAL ENVIRONMENT {LOCAL_ENV}")
logging.info(f"USE ONNX {USE_ONNX}")
logging.info(f"USE OPENVINO {USE_OPENVINO}")
logging.info(f"DEVICE OPENVINO {DEVICE_OV}")

# Check device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"DEVICE CUDA or CPU {device}")

# Create global variables
global model, processor
model = None
processor = None

# Setup paths for models
if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
elif platform.system() == "Linux" and MODEL_PATH == None and LOCAL_ENV == "0":
    MODEL_PATH = "/app/models"
    MODELS_PATH = "/app/models"
elif platform.system() == "Linux":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
logging.info(f"Models Path {MODELS_PATH}")


async def run_single_mode_service():
    """
    Main function to run either the tagging or captioning service based on DOCKER_TASK.
    """
    logging.info(f"Setting up streams for {DOCKER_TASK} service only")

    # Set up the appropriate stream for the current operation mode
    logging.info(f"Ensuring input stream '{INPUT_STREAM}' exists")
    await setup_stream(
        nats_url=NAT_URL,
        local_env=LOCAL_ENV,
        stream_name=INPUT_STREAM,
        subjects=[INPUT_SUBJECT],
    )

    logging.info(f"Ensuring output stream '{OUTPUT_STREAM}' exists")
    await setup_stream(
        nats_url=NAT_URL,
        local_env=LOCAL_ENV,
        stream_name=OUTPUT_STREAM,
        subjects=[OUTPUT_SUBJECT],
    )

    # Start the appropriate service based on DOCKER_TASK
    logging.info(f"Starting image {OPERATION_MODE} service...")
    await process_image_from_nats(
        nats_url=NAT_URL,
        input_stream=INPUT_STREAM,
        input_subject=INPUT_SUBJECT,
        output_stream=OUTPUT_STREAM,
        output_subject=OUTPUT_SUBJECT,
        local_env=LOCAL_ENV,
        mode=OPERATION_MODE,
        models_path=MODELS_PATH,
    )


if __name__ == "__main__":
    logging.info(f"Starting image {OPERATION_MODE} service with NATS...")

    # Log environment variables
    logging.info("Environment configuration:")
    logging.info(f"  - MODEL_PATH: {MODEL_PATH}")
    logging.info(f"  - LOCAL_ENV: {LOCAL_ENV}")
    logging.info(f"  - USE_ONNX: {USE_ONNX}")
    logging.info(f"  - USE_OPENVINO: {USE_OPENVINO}")
    logging.info(f"  - DEVICE_OV: {DEVICE_OV}")
    logging.info(f"  - NATS URL: {NAT_URL}")
    logging.info(f"  - NATS_ENDPOINT: {NATS_ENDPOINT}")
    logging.info(f"  - DOCKER_TASK: {DOCKER_TASK}")

    # Log input/output streams and subjects
    logging.info("NATS streams and subjects:")
    logging.info(f"  - INPUT_STREAM: {INPUT_STREAM}")
    logging.info(f"  - INPUT_SUBJECT: {INPUT_SUBJECT}")
    logging.info(f"  - OUTPUT_STREAM: {OUTPUT_STREAM}")
    logging.info(f"  - OUTPUT_SUBJECT: {OUTPUT_SUBJECT}")

    # Log models and paths
    logging.info(f"  - Models Path: {MODELS_PATH}")
    logging.info(f"  - Images Path: {IMAGES_PATH}")
    logging.info(
        f"  - Running in {'LOCAL' if LOCAL_ENV == '1' else 'PRODUCTION'} environment"
    )
    logging.info(f"  - Operating in {DOCKER_TASK.upper()} mode ({OPERATION_MODE})")

    # Check if we're using OpenVINO as required
    if USE_OPENVINO != "YES":
        logging.warning(
            "This NATS version works best with OpenVINO. Setting USE_OPENVINO=YES is required for Florence-2."
        )
        # Not exiting with error in local environment to support more flexible development
        if LOCAL_ENV != "1":
            logging.error(
                "Exiting: USE_OPENVINO=YES is required in production environment."
            )
            sys.exit(1)

    try:
        # Run the asyncio event loop
        asyncio.run(run_single_mode_service())
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"Error running service: {e}")
        sys.exit(1)
