"""
Inference utilities.
"""

from typing import List, Optional, Tuple, Dict
from transformers import ViTImageProcessor, ViTForImageClassification
import cv2
import numpy as np
from PIL import Image  # type: ignore
from tqdm import tqdm  # type: ignore
import torch
import onnxruntime
import logging

global label_dic
label_dic = {"drawings": 0, "hentai": 1, "neutral": 2, "porn": 3, "sexy": 4}


def get_key(dict, value):
    """
    return key given a value. From a dictionary
    """
    for key, val in dict.items():
        if val == value:
            return key
    return "Value not found"


def load_model(model_path: str, use_onnx: str, device: str):
    """
    Load model ONNX or pytorch

    Args:
        models_path (str): Path to model
        use_onnx (str): YES/NO use onnx format
        device (str): cuda or cpu

    Returns:
        _type_: Processor and ViT model
    """
    if use_onnx == "YES":
        processor = None
        model = onnxruntime.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )

    else:
        processor = ViTImageProcessor.from_pretrained(model_path)
        model = ViTForImageClassification.from_pretrained(model_path)
        model = model.to(device)
    return processor, model


def load_img(path):
    """Load Image for onnx

    Args:
        path (_type_): path of image

    Returns:
        _type_: numpy array
    """
    image = Image.open(path).convert("RGB")
    image = image.resize((224, 224), Image.BILINEAR)
    img = np.array(image, dtype=np.float32)
    img /= 255.0
    img = np.transpose(img, (2, 0, 1))
    return img


def predict_image_pytorch(
    image_path: str,
    processor: ViTImageProcessor = None,
    model: ViTForImageClassification = None,
    device: str = "cuda",
    use_onnx: str = "YES",
) -> Dict:
    """
    Pipeline from single image path to predicted NSFW probability.
    Optionally generate and save the Grad-CAM plot.
    """
    output_probs = {}
    if use_onnx == "YES":
        logging.info(f"infernce onnx file {image_path}")
        # onnx_style
        input_name = model.get_inputs()[0].name
        output_name = model.get_outputs()[0].name
        inputs = np.array([load_img(image_path)])
        outputs = model.run([output_name], {input_name: inputs})[0]
        logits = np.array(outputs)
        probabilities = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        probs = probabilities[0]
    else:
        logging.info(f"inference VIT file {image_path}")
        # VIT style
        image = Image.open(image_path)
        # Feature Transform with  ViTImageProcessor
        inputs = processor(images=image, return_tensors="pt")
        # data To device
        inputs = inputs.to(device)
        # get prediction
        outputs = model(**inputs)
        # get logits
        logits = outputs.logits
        # get probabilities
        probs = torch.softmax(logits, dim=1).cpu().detach().numpy()
        probs = list(probs[0])

    for prob, key in zip(probs, range(0, len(probs))):
        label = get_key(label_dic, key)
        output_probs[label] = float(prob)

    return output_probs


def predict_video_frames(
    video_path: str,
    model=None,
    processor=None,
    progress_bar: bool = True,
    device: str = "cuda",
    output_video_path: Optional[str] = None,
    threshold: float = 0.8,
) -> Tuple[List[float], List[float]]:
    """
    Make prediction for each video frame.
    """
    cap = cv2.VideoCapture(video_path)  # pylint: disable=no-member
    fps = cap.get(cv2.CAP_PROP_FPS)  # pylint: disable=no-member
    logging.info(f"Frames per second: {fps}")
    video_writer = None  # pylint: disable=no-member
    nsfw_probability = 0.0
    nsfw_probabilities: List[float] = []
    frame_count = 0

    if progress_bar:
        pbar = tqdm(
            total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        )  # pylint: disable=no-member
    else:
        pbar = None

    while cap.isOpened():
        ret, bgr_frame = cap.read()  # Get next video frame.
        if not ret:
            break  # End of given video.

        if pbar is not None:
            pbar.update(1)

        frame_count += 1
        frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member

        if video_writer is None and output_video_path is not None:
            video_writer = cv2.VideoWriter(
                output_video_path,
                cv2.VideoWriter_fourcc(*"MJPG"),
                fps,
                (frame.shape[1], frame.shape[0]),
            )
        # process frame
        inputs = processor(images=frame, return_tensors="pt")
        inputs = inputs.to(device)
        outputs = model(**inputs)
        logits = outputs.logits

        # get probabilities
        probs = torch.softmax(logits, dim=1).cpu().detach().numpy()
        probs = list(probs[0])
        output_probs = {}
        for prob, key in zip(probs, range(0, len(probs))):
            label = get_key(label_dic, key)
            output_probs[label] = prob
        # probability nsfw
        prob_nsfw = output_probs["sexy"] + output_probs["hentai"] + output_probs["porn"]
        nsfw_probabilities.append(prob_nsfw)

        if video_writer is not None:
            prob_str = str(np.round(nsfw_probability, 2))
            result_text = f"NSFW probability: {prob_str}"
            # RGB colour.
            colour = (255, 0, 0) if nsfw_probability >= threshold else (0, 0, 255)
            cv2.putText(  # pylint: disable=no-member
                frame,
                result_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,  # pylint: disable=no-member
                1,
                colour,
                2,
                cv2.LINE_AA,  # pylint: disable=no-member
            )
            video_writer.write(
                cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # pylint: disable=no-member
            )

    if video_writer is not None:
        video_writer.release()
    cap.release()
    cv2.destroyAllWindows()  # pylint: disable=no-member

    if pbar is not None:
        pbar.close()

    elapsed_seconds = (np.arange(1, len(nsfw_probabilities) + 1) / fps).tolist()
    return elapsed_seconds, nsfw_probabilities


def predict_video_frames_onnx(
    video_path: str,
    model=None,
    progress_bar: bool = True,
) -> Tuple[List[float], List[float]]:
    """
    Make prediction for each video frame with onnx model.
    """
    cap = cv2.VideoCapture(video_path)  # pylint: disable=no-member
    fps = cap.get(cv2.CAP_PROP_FPS)  # pylint: disable=no-member
    logging.info(f"Frames per second: {fps}")
    nsfw_probabilities: List[float] = []
    frame_count = 0
    images = []
    if progress_bar:
        pbar = tqdm(
            total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        )  # pylint: disable=no-member
    else:
        pbar = None

    while cap.isOpened():
        ret, bgr_frame = cap.read()  # Get next video frame.
        if not ret:
            break  # End of given video.

        if pbar is not None:
            pbar.update(1)

        frame_count += 1
        frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
        frame = cv2.resize(frame, (224, 224), cv2.INTER_AREA)
        img = np.array(frame, dtype=np.float32)
        img /= 255.0
        img = np.transpose(img, (2, 0, 1))

        images.append(img)

    logging.info("End of Video. Inference of Frames")

    cap.release()
    cv2.destroyAllWindows()  # pylint: disable=no-member

    if pbar is not None:
        pbar.close()
    # inference with ONNX model
    input_name = model.get_inputs()[0].name
    output_name = model.get_outputs()[0].name
    outputs = model.run([output_name], {input_name: images})[0]
    logits = np.array(outputs)

    probabilities = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)

    for probs in probabilities:
        output_probs = {}
        for prob, key in zip(probs, range(0, len(probs))):
            label = get_key(label_dic, key)
            output_probs[label] = prob

        # probability nsfw
        prob_nsfw = output_probs["sexy"] + output_probs["hentai"] + output_probs["porn"]
        nsfw_probabilities.append(prob_nsfw)

    return nsfw_probabilities
