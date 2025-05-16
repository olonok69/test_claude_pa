import asyncio
import argparse
from rapidocr_onnxruntime import RapidOCR
import datetime
import logging
import os
from pathlib import Path
from detectaicore import set_up_logging


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


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


def create_engine_rapidocr():
    """
    Create RapidOCR Engine
    return:
    RapidOCR Engine
    """
    # create RapidOCR Engine
    engine = RapidOCR(det_model_type="DB", rec_model_type="CRNN")
    return engine


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


def ocr_image(path, engine):
    """
    Extract text from an Image using Leptonica and tessetact
    params:
    im: PIL image
    app: FastAPI endpoint. Contains global objects with tesseract and Leptonica C objects
    return:
    text extracted
    """

    result, _ = engine(path)
    # Extract text while preserving spaces and returns
    extracted_text = ocr_to_text(result)  # "\n".join([line[1] for line in result])

    return extracted_text


async def main(input_file, output_file, engine):
    # def main(input_file, output_file, cypher):
    try:
        time1 = datetime.datetime.now()
        result = ocr_image(input_file, engine)
        with open(output_file, "w") as f:
            f.write(result)
        time2 = datetime.datetime.now()
        time_diff = time2 - time1
        tf = time_diff.total_seconds()
        logging.warning(f"Processing time: {tf} seconds")
    except Exception as e:
        logging.error(f"Error in main: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process OCR requests from a JSON file."
    )
    parser.add_argument("input_file", type=str, help="Path to the input Image file.")
    parser.add_argument("output_file", type=str, help="Path to the output txt file.")

    args = parser.parse_args()
    # main(args.input_file, args.output_file, args.cypher)
    engine = create_engine_rapidocr()
    logging.warning("Rapid OCR Engine has been initialized. Using Rapid OCR Engine")
    asyncio.run(main(args.input_file, args.output_file, engine))
