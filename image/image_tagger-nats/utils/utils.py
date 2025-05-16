import os
import platform
import logging
import json
from pathlib import Path


def setup_config_paths():
    """
    Setup and return configuration paths based on environment
    """
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGS_PATH = os.path.join(ROOT_DIR, "logs")
    Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)

    # Setup paths for models
    if platform.system() == "Windows":
        MODELS_PATH = os.path.join(ROOT_DIR, "models")
    elif (
        platform.system() == "Linux"
        and os.getenv("MODEL_PATH") is None
        and os.getenv("LOCAL_ENV") == "0"
    ):
        MODELS_PATH = "/app/models"
    else:
        MODELS_PATH = os.path.join(ROOT_DIR, "models")

    # Set images path
    IMAGES_PATH = os.getenv("IMAGES_PATH", os.path.join(ROOT_DIR, "images"))

    return {
        "ROOT_DIR": ROOT_DIR,
        "LOGS_PATH": LOGS_PATH,
        "MODELS_PATH": MODELS_PATH,
        "IMAGES_PATH": IMAGES_PATH,
    }


def setup_env_variables():
    """
    Load and setup environment variables
    """
    paths = setup_config_paths()
    env_path = os.path.join(paths["ROOT_DIR"], "keys", ".env_file")

    # Import here to avoid circular imports
    from dotenv import load_dotenv

    status = load_dotenv(env_path)
    logging.info(f"Status load .env file {str(status)}")

    # Return important environment variables
    return {
        "MODEL_PATH": os.getenv("MODEL_PATH"),
        "LOCAL_ENV": os.getenv("LOCAL_ENV"),
        "USE_ONNX": os.getenv("USE_ONNX", "NO"),
        "USE_OPENVINO": os.getenv("USE_OPENVINO", "YES"),
        "DEVICE_OV": os.getenv("DEVICE_OV", "CPU"),
        "INPUT_STREAM": os.getenv("INPUT_STREAM"),
        "INPUT_SUBJECT": os.getenv("INPUT_SUBJECT"),
        "INPUT_SUBJECT_TAGGER": os.getenv(
            "INPUT_SUBJECT_TAGGER", "tagger.tasks.started.>"
        ),
        "INPUT_SUBJECT_CAPTIONING": os.getenv(
            "INPUT_SUBJECT_CAPTIONING", "caption.tasks.started.>"
        ),
        "OUTPUT_STREAM": os.getenv("OUTPUT_STREAM"),
        "OUTPUT_SUBJECT": os.getenv("OUTPUT_SUBJECT"),
        "OUTPUT_SUBJECT_TAGGER": os.getenv(
            "OUTPUT_SUBJECT_TAGGER", "tagger.results.completed.>"
        ),
        "OUTPUT_SUBJECT_CAPTIONING": os.getenv(
            "OUTPUT_SUBJECT_CAPTIONING", "caption.results.completed.>"
        ),
        "NAT_URL": os.getenv("NAT_URL"),
        "CERTIFICATES_PATH": os.getenv("CERTIFICATES_PATH"),
        "VERSION_SUBJECT": os.getenv("VERSION_SUBJECT"),
        "VERSION_QUEUE_GROUP": os.getenv("VERSION_QUEUE_GROUP"),
        "HEALTH_CHECK_SUBJECT": os.getenv("HEALTH_CHECK_SUBJECT"),
    }
