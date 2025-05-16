import torch
from detectaicore import Job, image_file_names
import base64
import tempfile
from typing import List, Dict
import json

import logging
import copy
import gc
import torch
from detectaicore import Job

from src.predictor import (
    read_image,
    preprocess,
    predict,
)

# this list it is purely image formats , diferent to what we use in OCR
image_file_names = ["jpeg", "jpg", "tiff", "png", "tif", "gif", "bmp"]

import logging
import copy
import gc
import torch
from detectaicore import Job


def process_request_nat(
    file_data, model, processor, num_labels=5, prompt="<OD>", use_openvino="YES"
):
    """
    Process an image file and extract tags from it

    params:
    file_data: binary data of the image file
    model: prediction model
    processor: image processor
    num_labels: number of tags to extract
    prompt: prompt for the model (used only with Florence2)
    use_openvino: whether to use OpenVINO

    return:
    result: extracted tags from the image
    """
    try:
        # Create a Job instance for tracking
        new_task = Job()
        jobs = {}
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "Image Tagging Model Analysis"

        # Create a list document structure similar to what process_request expects
        list_doc = {"id": "image_from_nats", "document": file_data}
        list_docs = [list_doc]

        # No need for run_in_threadpool since we're already in a thread executor context
        data, documents_non_treated = process_request(
            list_docs=list_docs,
            num_labels=num_labels,
            model=model,
            processor=processor,
            jobs=jobs,
            new_task=new_task,
            use_onnx="NO",  # We're using OpenVINO for NATS version
            device=torch.device("cpu"),
            prompt=prompt,
            use_openvino=use_openvino,
        )

        # Check if we successfully processed the image
        if len(data) == 0:
            logging.warning("Failed to process the image")
            return {"error": "Failed to process the image", "data": []}

        # Update job status
        jobs[new_task.uid].status = f"Job {new_task.uid} Finished code {200}"

        # Clean up to free memory
        result = copy.deepcopy(data)
        del data
        gc.collect()

        return result
    except Exception as e:
        logging.error(f"Error in process_request_nat: {str(e)}")
        return {"error": str(e), "data": []}


def analyse_image(
    data,
    model,
    processor,
    num_labels,
    use_onnx,
    device,
    prompt,
    use_openvino,
):
    """
    Process image and get tagging labels and probabilities score
    params:
    data: list of documents from detect AI
    model: pytorch vision model
    processor: Processor object
    use_onnx : IF use ONNX model or not
    device: Device to load BLIP model
    use_openvino: if to use Florence 2 with OpenVino or Salesforce Blip
    prompt: Instruction to use only with Florence2
    return:
    text extracted and endpoint
    """
    im_b64 = data.get("source").get("content")
    ext = data.get("source").get("file_type")
    file_name = data.get("source").get("file_name")
    img_bytes = base64.b64decode(im_b64.encode("utf-8"))
    logging.info(
        f"Image File name: {file_name}, length: {len(img_bytes)}, extension: {ext}"
    )

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(img_bytes)
        temp_filename = f.name

    logging.info(f"Image saved to:{file_name}. Processing Image")
    try:

        # Read image
        image = read_image(temp_filename)
        # Preprocess image
        if use_openvino != "YES":
            image = preprocess(image)
        # Predict
        predictions = predict(
            input_image=image,
            model=model,
            processor=processor,
            num_labels=num_labels,
            use_onnx=use_onnx,
            device=device,
            prompt=prompt,
            use_openvino=use_openvino,
            image_path=temp_filename,
        )
        # create string with predictions
        chunck = json.dumps(predictions, indent=2)
        logging.info(f"Sucessfuly predicted: {num_labels}, for Image: {file_name}")

    except Exception as e:

        chunck = ""
        predictions = ""
        logging.error(
            f"There was an Exception {str(e)} predicting: {num_labels}, for Image: {file_name}"
        )

    data["source"]["content"] = predictions
    del predictions
    del img_bytes
    del image
    return chunck, data


def tag_analisys_documents_from_request(
    document,
    model,
    processor,
    num_labels,
    use_onnx,
    device,
    prompt,
    use_openvino,
):
    """
    Process documents depending of their file type
    params:
    document: dictionary containing metadata and data of a document
    weights_path paths weights RestNet Model
    model keras model for Multiclass Classification
    processor : Processor object
    use_onnx : IF use ONNX model or not
    device: GPU or CPU for pytorch Models
    prompt: Task to do (ONLY florence2)
    use_openvino: if to use Floernec with OpenVino or not
    return:
    text extracted and endpoint

    """
    # get extension of document from request
    ext = document.get("source").get("file_type")

    if ext in image_file_names:
        utf8_text, document = analyse_image(
            data=document,
            model=model,
            processor=processor,
            num_labels=num_labels,
            use_onnx=use_onnx,
            device=device,
            prompt=prompt,
            use_openvino=use_openvino,
        )

    return utf8_text, document


def process_request(
    list_docs: List[Dict],
    model,
    processor,
    num_labels,
    jobs: Dict,
    new_task: Job,
    use_onnx: str = "NO",
    device: str = "CPU",
    prompt: str = "<OD>",
    use_openvino: str = "YES",
):
    """ "
    process list of base64 Image/Documents Tagging model

    params:
    list_docs: list of documents from detect AI. List of dictionaries containing metadata and data of documents
    model pytorch vision model
    processor : Processor object
    jobs: dictionary to hold status of the Job
    new_task: Job object
    use_onnx : IF use ONNX model or not
    return:
    processed_docs : list of dictionaries containing document processed , this is pass trought OCR and text extracted. The extracted text replace the original base64 content
    documents_non_teathred : list of dictionaries containing {id : reason of not treating this id}

    """
    jobs[new_task.uid].status = "Start tagging model Analysis"
    documents_non_teathred = []
    processed_docs = []
    for data in list_docs:
        file_type = data.get("source").get("file_type")
        file_name = data.get("source").get("file_name")

        logging.info(
            f"Processing file : {file_name} length : {len(data.get('source').get('content'))}"
        )
        # if file type not valid
        if not file_type or not (file_type in image_file_names):
            documents_non_teathred.append({data.get("id"): "File type not valid"})
            logging.warning(
                f"File : {file_name}  Id {data.get('id')}. No Valid Extension. Continue to next file"
            )
            continue

        utf8_text, data = tag_analisys_documents_from_request(
            document=data,
            model=model,
            processor=processor,
            num_labels=num_labels,
            use_onnx=use_onnx,
            device=device,
            prompt=prompt,
            use_openvino=use_openvino,
        )
        # if no text extracted doc to documents_non_teathred
        if len(utf8_text) < 3:
            documents_non_teathred.append(
                {data.get("id"): "No Image/Video suitable for tagging analysis "}
            )

            logging.warning(
                f"File : {file_name}  Id {data.get('id')}. No Text in this file. Continue to next file"
            )
            continue

        processed_docs.append(data)
        jobs[new_task.uid].status = (
            f"Extracted Text From {len(processed_docs)} Documents"
        )
        logging.info(f"Extracted Text From {len(processed_docs)} Documents")
    return processed_docs, documents_non_teathred
