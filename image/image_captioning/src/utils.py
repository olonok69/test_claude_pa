from PIL import Image
import torch
from detectaicore import Job
import base64
import tempfile
from typing import List, Dict
import os
import logging
from .ov_florence2_helper import OVFlorence2Model
from transformers import BlipForConditionalGeneration, BlipProcessor, AutoProcessor


# this list it is purely image formats , diferent to what we use in OCR
image_file_names = ["jpeg", "jpg", "tiff", "png", "tif", "gif", "bmp"]


def load_model(models_path: str, use_openvino: str = "YES", device_openvino="CPU"):
    """
    Load Model  Salesforce/blip-image-captioning-large  or Microsoft/Florence2 with OpenVino
    Args:
        models_path: str --> path to models
        use_openvino : str --> whether to use or no OpenVino . if yes we load Florence2
        device_openvino : str --> CPU,GPU, AUTO. default CPU
    """
    model_path = ""
    if use_openvino == "YES":
        model_path = os.path.join(models_path, "Florence-2-base-ft")
        model = OVFlorence2Model(model_path, "AUTO")
        processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    else:
        model_path = os.path.join(models_path, "blip-image-captioning-large")
        try:
            processor = BlipProcessor.from_pretrained(model_path)
            model = BlipForConditionalGeneration.from_pretrained(model_path)
        except Exception as e:
            logging.warning(
                f"Model Local not found Produced Exception {str(e)}. We loud Model from HF"
            )
            model_path = "Salesforce/blip-image-captioning-large"
            processor = BlipProcessor.from_pretrained(model_path)
            model = BlipForConditionalGeneration.from_pretrained(model_path)
    logging.info(f"Model Path: {model_path}")
    return processor, model


def analyse_image(
    data,
    processor,
    model,
    max_new_tokens,
    min_new_tokens,
    temperature,
    diversity_penalty,
    repetition_penalty,
    no_repeat_ngram_size,
    num_beams,
    device,
    prompt,
    use_openvino,
):
    """
    Process image and get a caption o description of that picture
    params:
    data: list of documents from detect AI
    processor : tokenizer,
    model :model,
    max_new_tokens: The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    min_new_tokens: The minimum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    temperature: The value used to modulate the next token probabilities.
    repetition_penalty:The parameter for repetition penalty. 1.0 means no penalty. See this paper for more details.
    diversity_penalty: This value is subtracted from a beam’s score if it generates a token same as any beam from other group at a particular time. Note that diversity_penalty is only effective if group beam search is enabled
    no_repeat_ngram_size: If set to int > 0, all ngrams of that size can only occur once.
    num_beams:  Number of beams for beam search. 1 means no beam search
    device: Device to load model
    use_openvino: if to use Florence 2 with OpenVino or Salesforce Blip
    prompt: Instruction to use only with Florence2
    return:
    text extracted and Documents
    """
    im_b64 = data.get("source").get("content")
    ext = data.get("source").get("file_type")
    file_name = data.get("source").get("file_name")
    img_bytes = base64.b64decode(im_b64.encode("utf-8"))

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(img_bytes)
        temp_filename = f.name

    logging.info(
        f"Image file name: {file_name}, extension: {ext}, length: {len(img_bytes)}"
    )
    logging.info(f"Image saved to: {temp_filename}")
    try:
        if use_openvino == "YES":
            # Read image
            image = Image.open(temp_filename).convert("RGB")
            inputs = processor(text=prompt, images=image, return_tensors="pt")

            generated_ids = model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                do_sample=False,
                num_beams=2,
            )
            generated_text = processor.batch_decode(
                generated_ids, skip_special_tokens=False
            )[0]

            parsed_answer = processor.post_process_generation(
                generated_text,
                task=prompt,
                image_size=(image.width, image.height),
            )
            chunck = f"Image Summary for {file_name} is : {parsed_answer.get(prompt)}"
        else:

            # Read image
            raw_image = Image.open(temp_filename).convert("RGB")
            # conditional image captioning
            model = model.eval()
            if device == "cuda":
                inputs = processor(raw_image, return_tensors="pt").to(
                    device, torch.float16
                )
                model = model.to(device, torch.float16)
                logging.info("procesed with GPU")
            else:
                inputs = processor(raw_image, return_tensors="pt").to(device)
                model = model.to(device)
                logging.info("procesed with CPU")

            # Predict
            if num_beams > 1:
                out = model.generate(
                    max_new_tokens=int(max_new_tokens),
                    min_new_tokens=int(min_new_tokens),
                    temperature=float(temperature),
                    diversity_penalty=float(diversity_penalty),
                    repetition_penalty=float(repetition_penalty),
                    no_repeat_ngram_size=int(no_repeat_ngram_size),
                    num_beams=num_beams,
                    **inputs,
                )
            else:
                out = model.generate(
                    max_new_tokens=int(max_new_tokens),
                    min_new_tokens=int(min_new_tokens),
                    temperature=float(temperature),
                    no_repeat_ngram_size=int(no_repeat_ngram_size),
                    num_beams=num_beams,
                    **inputs,
                )
            predictions = processor.decode(out[0], skip_special_tokens=True)
            chunck = f"Image Summary for {file_name} is : {predictions}"

    except Exception as e:

        chunck = ""
        logging.error(f"There was an Exception {str(e)} in Image: {file_name}")

    logging.info(chunck)
    data["source"]["content"] = [chunck]
    return chunck, data


def captioning_analisys_documents_from_request(
    document,
    processor,
    model,
    max_new_tokens,
    min_new_tokens,
    temperature,
    diversity_penalty,
    repetition_penalty,
    no_repeat_ngram_size,
    num_beams,
    device,
    prompt,
    use_openvino,
):
    """
    Process documents depending of their file type
    params:
    document: list of documents from detect AI
    processor : tokenizer,
    model :model,
    max_new_tokens: The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    min_new_tokens: The minimum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    temperature: The value used to modulate the next token probabilities.
    repetition_penalty:The parameter for repetition penalty. 1.0 means no penalty. See this paper for more details.
    diversity_penalty: This value is subtracted from a beam’s score if it generates a token same as any beam from other group at a particular time. Note that diversity_penalty is only effective if group beam search is enabled
    no_repeat_ngram_size: If set to int > 0, all ngrams of that size can only occur once.
    num_beams:  Number of beams for beam search. 1 means no beam search
    device: GPU or CPU for pytorch Models
    prompt: Task to do (ONLY florence2)
    use_openvino: if to use Floernec with OpenVino or not
    return:
    text extracted and Documents

    """
    # get extension of document from request
    ext = document.get("source").get("file_type")

    if ext in image_file_names:
        utf8_text, document = analyse_image(
            document,
            processor,
            model,
            max_new_tokens,
            min_new_tokens,
            temperature,
            diversity_penalty,
            repetition_penalty,
            no_repeat_ngram_size,
            num_beams,
            device,
            prompt,
            use_openvino,
        )

    return utf8_text, document


def process_request(
    list_docs: List[Dict],
    processor,
    max_new_tokens,
    min_new_tokens,
    temperature,
    diversity_penalty,
    repetition_penalty,
    no_repeat_ngram_size,
    num_beams,
    model,
    jobs: Dict,
    new_task: Job,
    device: str,
    prompt: str,
    use_openvino: str,
):
    """
    process list of base64 Image/Documents captioning model

    params:
    list_docs: list of documents from detect AI. List of dictionaries containing metadata and data of documents
    processor : tokenizer,
    max_new_tokens: The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    min_new_tokens: The minimum numbers of tokens to generate, ignoring the number of tokens in the prompt.
    temperature: The value used to modulate the next token probabilities.
    repetition_penalty:The parameter for repetition penalty. 1.0 means no penalty. See this paper for more details.
    diversity_penalty: This value is subtracted from a beam’s score if it generates a token same as any beam from other group at a particular time. Note that diversity_penalty is only effective if group beam search is enabled
    no_repeat_ngram_size: If set to int > 0, all ngrams of that size can only occur once.
    num_beams:  Number of beams for beam search. 1 means no beam search
    model pytorch vision model
    jobs: dictionary to hold status of the Job
    new_task: Job object
    device: GPU or CPU for pytorch Models
    prompt: Task to do (ONLY florence2)
    use_openvino: if to use Floernec with OpenVino or not
    return:
    processed_docs : list of dictionaries containing document processed , this is pass trought OCR and text extracted. The extracted text replace the original base64 content
    documents_non_teathred : list of dictionaries containing {id : reason of not treating this id}
    """
    jobs[new_task.uid].status = "Start Captioning model Analysis of Files"
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
            logging.warning(f"File : {file_name}  No Valid Extension")
            continue

        utf8_text, data = captioning_analisys_documents_from_request(
            data,
            processor,
            model,
            max_new_tokens,
            min_new_tokens,
            temperature,
            diversity_penalty,
            repetition_penalty,
            no_repeat_ngram_size,
            num_beams,
            device,
            prompt,
            use_openvino,
        )
        # if no text extracted doc to documents_non_teathred
        if len(utf8_text) < 3:
            documents_non_teathred.append(
                {data.get("id"): "No Image/Video suitable for Captioning analysis "}
            )
            logging.warning(
                f"File : {data.get('id')}  No Caption produced for this Image"
            )
            continue

        processed_docs.append(data)
        jobs[new_task.uid].status = (
            f"Produced Captions for {len(processed_docs)} Images"
        )
        logging.info(f"Produced Captions for {len(processed_docs)} Images")
    return processed_docs, documents_non_teathred
