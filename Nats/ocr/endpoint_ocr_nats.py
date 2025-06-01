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
from dotenv import load_dotenv
import json
import requests
import urllib.parse
from pathlib import Path
from urllib.parse import urlparse
from utils.utils import process_request_nat
from utils.environment import detect_environment

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


async def process_ocr_from_nats(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    config_path,
    doc_path,
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
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()
        engine = create_engine_rapidocr(
            config_path=config_path
        )  # Initialize OCR engine

        async def cb(msg):
            try:
                time1 = datetime.datetime.now()

                # Parse the message as JSON
                message_data = json.loads(msg.data.decode("utf-8"))
                logging.warning(f"Received message: {message_data}")

                # Extract URI from the message
                uri = message_data["source"]["uri"]
                filename = (
                    msg.headers.get("file-name", ["unknown"])
                    if msg.headers
                    else "unknown"
                )
                logging.warning(f"Processing file: {filename} from URI: {uri}")

                # Download or open the file based on the URI scheme
                file_data = None
                if uri.startswith("http://") or uri.startswith("https://"):
                    # Handle HTTP URLs
                    response = requests.get(uri)
                    if response.status_code == 200:
                        file_data = response.content
                    else:
                        logging.error(
                            f"Failed to download file from {uri}, status code: {response.status_code}"
                        )
                        await msg.nak()
                        return
                elif uri.startswith("file://"):
                    # Handle local file paths
                    file_path = uri[7:]  # Remove 'file://' prefix
                    filename = os.path.basename(file_path)
                    logging.warning(f"Local file path: {file_path}")
                    file_path = os.path.join(doc_path, filename)
                    logging.warning(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")
                        await msg.nak()
                        return
                else:
                    logging.error(f"Unsupported URI scheme: {uri}")
                    await msg.nak()
                    return

                logging.warning(f"Downloaded file data of size: {len(file_data)} bytes")

                # Process the file data using process_request
                try:
                    # Apply any pre-processing steps specified in the message
                    pre_processing = message_data.get("ocrOptions", {}).get(
                        "preProcessing", []
                    )
                    extracted_text = process_request_nat(
                        file_data, engine, pre_processing
                    )

                    # Create response in the required format
                    languages = message_data.get("ocrOptions", {}).get(
                        "languages", ["en"]
                    )

                    result_data = {
                        "version": "1.0",
                        "batchId": message_data.get("batchId"),
                        "source": message_data.get(
                            "source", {}
                        ),  # Preserve the original source information
                        "outcome": {
                            "success": True,
                            "texts": [
                                {
                                    "language": languages[0] if languages else "en",
                                    "text": extracted_text,
                                }
                            ],
                        },
                        "state": {
                            "fileId": message_data.get("state", {}).get("fileId"),
                            "scanId": message_data.get("state", {}).get("index", ""),
                        },
                    }

                    await js.publish(
                        output_subject,
                        json.dumps(result_data).encode(),
                        stream=output_stream,
                        headers={
                            "file-name": filename,
                            "batch-id": message_data.get("batchId"),
                        },
                    )
                    logging.warning(f"Published processing result in: {output_subject}")

                except Exception as e:
                    # Handle error case
                    error_data = {
                        "version": "1.0",
                        "batchId": message_data.get("batchId"),
                        "source": message_data.get("source", {}),
                        "outcome": {
                            "success": False,
                            "errorMessage": f"Processing error: {str(e)}",
                        },
                        "state": {
                            "fileId": message_data.get("state", {}).get("fileId"),
                            "scanId": message_data.get("state", {}).get("index", ""),
                        },
                    }

                    await js.publish(
                        output_subject,
                        json.dumps(error_data).encode(),
                        stream=output_stream,
                        headers={
                            "file-name": filename,
                            "batch-id": message_data.get("batchId"),
                        },
                    )
                    logging.error(f"Processing error: {str(e)}")

                time2 = datetime.datetime.now()
                time_diff = time2 - time1
                tf = time_diff.total_seconds()
                logging.warning(f"Processing time: {tf} seconds")
                await msg.ack()

            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON message: {e}")
                await msg.nak()
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await msg.nak()

        sub = await js.subscribe(input_subject, stream=input_stream, cb=cb)
        logging.warning(f"Subscribed to {input_subject} in stream {input_stream}")
        await asyncio.Future()  # Keep the subscriber running

    except Exception as e:
        logging.error(f"Error in NATS subscription: {e}")
    finally:
        await nc.close()


async def setup_stream(nats_url, stream_name, subjects):
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        try:
            await js.stream_info(stream_name)
            logging.warning(f"Stream '{stream_name}' already exists.")
        except:
            await js.add_stream(name=stream_name, subjects=subjects)
            logging.warning(f"Stream '{stream_name}' created with subjects: {subjects}")

    except Exception as e:
        logging.error(f"Error setting up stream: {e}")
    finally:
        await nc.close()


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
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config.yaml")
    PROD_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config_prod.yaml")

    async def run_nats_ocr(
        nats_url,
        input_stream,
        input_subject,
        output_stream,
        output_subject,
        config_path,
        doc_path,
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
        """
        await setup_stream(nats_url, input_stream, [input_subject])
        await setup_stream(nats_url, output_stream, [output_subject])
        await process_ocr_from_nats(
            nats_url,
            input_stream,
            input_subject,
            output_stream,
            output_subject,
            config_path,
            doc_path,
        )

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
    NAT_URL = os.getenv("NAT_URL") if "NAT_URL" in os.environ else args.nats_url
    if NAT_URL is None:
        raise AttributeError("NAT_URL not found in environment variables")
    LOCAL_ENV = os.getenv("LOCAL_ENV")
    INPUT_STREAM = (
        os.getenv("INPUT_STREAM") if "INPUT_STREAM" in os.environ else args.input_stream
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
    DEFAULT_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config.yaml")
    PROD_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config_prod.yaml")

    env = detect_environment()
    logging.info(f"Environment detected: {env}")

    if (
        env in ["Local Windows", "Windows Subsystem for Linux (WSL)"]
        and LOCAL_ENV == "0"
    ):
        CFG_PATH = DEFAULT_CFG_PATH
    else:
        CFG_PATH = PROD_CFG_PATH

    DOCS_PATH = os.getenv("DOCS_PATH")
    if DOCS_PATH is None:
        raise AttributeError("DOCS_PATH not found in environment variables")
    logging.info(f"Configuration path: {CFG_PATH}")
    logging.info(f"NATS URL: {NAT_URL}")
    logging.info(f"Input Stream: {INPUT_STREAM}")
    logging.info(f"Input Subject: {INPUT_SUBJECT}")
    logging.info(f"Output Stream: {OUTPUT_STREAM}")
    logging.info(f"Output Subject: {OUTPUT_SUBJECT}")
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
        )
    )
