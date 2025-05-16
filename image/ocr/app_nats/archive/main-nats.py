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
from nats.errors import TimeoutError
from dotenv import load_dotenv
import pymupdf
from PIL import Image
import io
import gc

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config.yaml")


def create_engine_rapidocr(config_path: str = None):
    """
    Create RapidOCR Engine
    return:
    RapidOCR Engine
    """
    # create RapidOCR Engine
    engine = RapidOCR(config_path=config_path)
    return engine


def zoom_png(im, zoom_x=2.0, zoom_y=2.0):
    """
    Zoom in a PNG image
    params:
    im: PIL image
    """
    logging.info(f"Zooming Image")
    doc = pymupdf.open(stream=io.BytesIO(im))
    page = doc[0]
    # get pixel map
    pix = page.get_pixmap()
    # Zoom in the image
    zoom_x = zoom_x  # horizontal zoom
    zoom_y = zoom_y  # vertical zoom
    mat = pymupdf.Matrix(zoom_x, zoom_y)  # zoom factor 2 in each dimension
    pix = page.get_pixmap(matrix=mat)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im = im.tobytes("jpeg", "RGB")
    logging.info(f"Image Zoomed size: {len(im)} bytes")
    del doc
    del page
    del pix
    gc.collect()
    return im


def ocr_to_text(ocr_output):
    """
    # Sort the OCR output based on the y-coordinate of the bounding box
    each element of the list is another list wihich contain 3 elements

        element 0 bounding box coordinates

        element 1 Text extracted

        element 2 score

        Example:

        [[[529.0, 149.0], [577.0, 149.0], [577.0, 174.0], [529.0, 174.0]],
        'R&D',
        0.9749892751375834]
    Args:
        ocr_output : list of lists, output from Rapid OCR
    """
    # Sort the OCR output based on the y-coordinate of the bounding box
    sorted_ocr = sorted(ocr_output, key=lambda x: x[0][0][1])

    # Initialize variables
    lines = []
    current_line = []
    current_y = sorted_ocr[0][0][0][1]

    # Iterate through the sorted OCR output
    for item in sorted_ocr:
        bbox, text, score = item
        bbox_y = bbox[0][1]

        # Check if the bounding box is on the same line as the current line
        if abs(bbox_y - current_y) <= 3:
            current_line.append(text + " ")
        else:
            lines.append(" ".join(current_line))
            current_line = [text + " "]
            current_y = bbox_y

    # Append the last line
    if current_line:
        lines.append(" ".join(current_line))

    # Join all lines into a single text output
    text_output = "\n".join(lines)
    return text_output


def ocr_image(data, engine):
    """
    Extract text from an Image using Leptonica and tessetact
    params:
    im: PIL image
    app: FastAPI endpoint. Contains global objects with tesseract and Leptonica C objects
    return:
    text extracted
    """

    result, _ = engine(data)
    # Extract text while preserving spaces and returns
    extracted_text = ocr_to_text(result)  # "\n".join([line[1] for line in result])

    return extracted_text


async def process_ocr_from_nats(
    nats_url, input_stream, input_subject, output_stream, output_subject, config_path
):
    """
    Receives image data from NATS, performs OCR, and publishes the result.
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
                # image_data = msg.data  # Binary image data
                # image_data = zoom_png(msg.data)
                image_data = msg.data
                logging.warning(f"Received image data of size: {len(image_data)} bytes")
                filename = msg.headers.get("file-name", ["unknown"])
                logging.warning(f"Received image data with filename: {filename}")
                ocr_result = ocr_image(image_data, engine)

                if ocr_result is None:
                    logging.error("OCR failed to process the image.")
                    await js.publish(
                        output_subject,
                        "OCR Failed".encode(),
                        stream=output_stream,
                        headers={"file-name": filename},
                    )
                elif isinstance(ocr_result, str):
                    await js.publish(
                        output_subject,
                        ocr_result.encode(),
                        stream=output_stream,
                        headers={"file-name": filename},
                    )

                    logging.warning(f"Published OCR result in : {output_subject}")
                else:
                    logging.error(f"OCR returned an unexpected result:{ocr_result}")
                    await js.publish(
                        output_subject,
                        "OCR Returned Unexpected result".encode(),
                        stream=output_stream,
                        headers={"file-name": filename},
                    )
                time2 = datetime.datetime.now()
                time_diff = time2 - time1
                tf = time_diff.total_seconds()
                logging.warning(f"Processing time: {tf} seconds")
                await msg.ack()

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

    async def run_nats_ocr(
        nats_url,
        input_stream,
        input_subject,
        output_stream,
        output_subject,
        config_path,
    ):
        """Run the NATS OCR processing.
        Args:
            nats_url (str): The NATS server URL.
            input_stream (str): The input stream name.
            input_subject (str): The input subject.
            output_stream (str): The output stream name.
            output_subject (str): The output subject.
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
            config_path=DEFAULT_CFG_PATH,
        )
    )
