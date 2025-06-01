from presidio_image_redactor import DicomImageRedactorEngine
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from src.utils import process_dicom_images, process_dicom_folder
from pathlib import Path
import shutil
from starlette.responses import JSONResponse
import json
import os
import base64
from detectaicore import set_up_logging

# Create Paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
TEMP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
Path(TEMP_PATH).mkdir(parents=True, exist_ok=True)
Path(INPUT_PATH).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

script_name = os.path.join(LOGS_PATH, "debug.log")
# create loggers
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="debug",
    logfile_log_color=False,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")


app = FastAPI(title="DICOM API", version="0.1.0")
app.engine = DicomImageRedactorEngine()


@app.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


# Image endpoints
@app.post(
    "/process-dicom-image",
)
async def process_dicom_image(
    file: UploadFile = File(...),
):
    """
    Upload and process a PDF file, converting its pages to images.
    """
    if not file.filename.lower().endswith(".dcm"):
        raise HTTPException(status_code=400, detail="Only dicom Images are allowed")

    dcm_path = Path(TEMP_PATH) / file.filename
    with dcm_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    redacted_instance, bboxes = process_dicom_images(dcm_path, app.engine)
    redacted_instance.save_as(str(dcm_path))
    # Convert DICOM instance and bounding boxes to string format
    with open(dcm_path, "rb") as f:
        encoded_dicom = base64.b64encode(f.read()).decode("utf-8")
    bboxes_str = json.dumps(bboxes)

    return {"redacted_instance": encoded_dicom, "bboxes": bboxes_str}


# Image endpoints
@app.post(
    "/process-dicom-folder",
)
async def process_dicom_folder_images(
    request: Request,
):
    """
    Upload and process a PDF file, converting its pages to images.
    """

    req = await request.json()

    if isinstance(req.get("folder_in"), str):
        folder_in = req.get("folder_in")
    else:
        raise AttributeError("Expected a input folder")

    if isinstance(req.get("folder_out"), str):
        folder_out = req.get("folder_out")
    else:
        raise AttributeError("Expected a output folder")

    status = process_dicom_folder(
        folder_in=folder_in,
        folder_out=folder_out,
        engine=app.engine,
        root_folder=ROOT_DIR,
    )
    return {"status": status}
