"""Image classification API server code"""
from fastapi import FastAPI, File, UploadFile
import uvicorn
from PIL import Image
from io import BytesIO
import cv2
from fastapi.responses import FileResponse
import numpy as np
import pytesseract
from utils import preprocess
import re
import os

import sys

if sys.platform.startswith("linux"):  # could be "linux", "linux2", "linux3", ...
    pass  # linux
elif sys.platform == "darwin":
    pass  # MAC OS X
elif os.name == "nt":
    # Windows, Cygwin, etc. (either 32-bit or 64-bit)
    pytesseract.pytesseract.tesseract_cmd = r"D:\\Tesseract-OCR\\tesseract"

# Create FAST API
app = FastAPI(
    title="Image OCR API",
    description="API for OCR images with tesseract.",
    version="1.0",
)


@app.post("/api/ocr")
async def predict_image(image: bytes = File(...)):
    # Read image

    nparr = np.fromstring(image, np.uint8)
    # Preprocess image
    image = preprocess(nparr)
    image_bytes = image.tobytes()
    custom_config = r"-l eng --oem 3 --psm 6"
    text = pytesseract.image_to_string(image)  # , config=custom_config)
    try:
        osd = pytesseract.image_to_osd(image)
        angle = re.search("(?<=Rotate: )\d+", osd).group(0)
        script = re.search("(?<=Script: )\w+", osd).group(0)
    except:
        angle = 0
        script = ""
    return {"text": text, "angle": angle, "script": script}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5003, log_level="info")
