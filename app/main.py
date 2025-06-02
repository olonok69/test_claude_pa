from dotenv import load_dotenv
from dotenv import dotenv_values
import os
import logging
from pathlib import Path
from detectaicore import (
    set_up_logging,
)
import shutil
from datetime import datetime
import yaml
import importlib
from src.conf import *
import sys


def load_config(config_file):
    """Loads the configuration from a YAML file."""
    with open(config_file, "r") as file:
        return yaml.safe_load(file)


def execute_step(step_config):
    """Executes a single step based on the configuration."""
    name = step_config["name"]
    module_name = step_config["module"]
    function_name = step_config["function"]
    parameters = step_config.get("parameters", {})  # Default to empty dict if no params

    logging.info(f"Executing step: {name}")

    try:
        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
        if src_dir not in sys.path:
            sys.path.append(src_dir)

        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        result = function(**parameters)  # Pass parameters as keyword arguments
        logging.info(f"Step '{name}' completed successfully.")
        return result  # Return the result if needed.

    except ImportError:
        logging.error(f"Error: Module '{module_name}' not found.")
    except AttributeError:
        logging.error(
            f"Error: Function '{function_name}' not found in module '{module_name}'."
        )
    except Exception as e:
        logging.error(f"Error executing step '{name}': {e}")
    return None  # return none if error happened.


# First step is to download the data
# The data is stored in an Azure Blob Storage
# CONTAINER_NAME = config.get("CONTAINER_NAME")
# STORAGE_ACCOUNT_NAME = config.get("STORAGE_ACCOUNT_NAME")
# logging.info(f"Downloading Data from {CONTAINER_NAME} in {STORAGE_ACCOUNT_NAME}")

# DATA_DIR = os.path.join(ROOT_DIR, "csm_data")
# download_new_data(config, CONTAINER_NAME, DATA_DIR, STORAGE_ACCOUNT_NAME)


def main(config, root_dir, environment):
    """Main function to load and execute the steps."""

    if not config or "steps" not in config:
        logging.error("Invalid configuration file.")
        return

    steps = config["steps"]
    # Create a timestamp string to identify classification file
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    var_post_event_process = "no"
    var_include_previous_scan_data = "no"
    for step in steps:
        # Check if the step is active
        name = step["name"]
        if step.get("active", True):  # default active to true if not present.

            logging.info(f"Executing step: {name}")
            step["parameters"]["config"] = environment
            step["parameters"]["root_dir"] = root_dir
            if "timestamp_str" in step["parameters"].keys():
                step["parameters"]["timestamp_str"] = timestamp_str
            # manage post event process
            if name == "Preprocess Data":
                var_post_event_process = step["parameters"]["post_event_process"]
                var_include_previous_scan_data = step["parameters"][
                    "include_previous_scan_data"
                ]
            # after preprocess data we need to update the post_event_process and include_previous_scan_data
            if "post_event_process" in step["parameters"].keys() and name in [
                "Transform Output",
                "Inference Visitors Batch",
                "Inference Visitors",
            ]:
                step["parameters"]["post_event_process"] = var_post_event_process
            if "include_previous_scan_data" in step["parameters"].keys() and name in [
                "Transform Output",
                "Inference Visitors Batch",
                "Inference Visitors",
            ]:
                step["parameters"][
                    "include_previous_scan_data"
                ] = var_include_previous_scan_data
            # run the step
            execute_step(step)
        else:
            logging.info(f"Skipping step: {step['name']} (inactive)")


if __name__ == "__main__":

    """Main function to load and execute the steps."""
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Set up logging
    LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    dirpath = Path(LOGS_PATH)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath)
    Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    script_name = os.path.join(LOGS_PATH, f"debug_{timestamp_str}.log")
    # create loggers
    if not set_up_logging(
        console_log_output="stdout",
        console_log_level="info",
        console_log_color=True,
        logfile_file=script_name,
        logfile_log_level="info",
        logfile_log_color=False,
        log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] - %(filename)s:%(lineno)d - %(message)s%(color_off)s",
    ):
        print("Failed to set up logging, aborting.")
        raise AttributeError("failed to create logging")

    DATA_DIR = os.path.join(ROOT_DIR, input_data_folder)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, output_csv_folder), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, output_data_folder), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, classification_data_folder), exist_ok=True)

    status = load_dotenv("keys/.env")
    environment = dotenv_values("keys/.env")
    logging.info(f"Load Environment {status}")

    config = load_config(os.path.join(ROOT_DIR, "conf", "config_batch.yaml"))
    main(config=config, root_dir=ROOT_DIR, environment=environment)
