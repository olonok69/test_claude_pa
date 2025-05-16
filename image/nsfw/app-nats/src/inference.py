"""
ONNX-only inference utilities.
"""

from typing import List, Dict
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import onnxruntime
import logging
import os

# Prevent OpenCV from trying to access display
# This prevents errors when running in headless environments
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
if not os.environ.get("DISPLAY", None):
    os.environ["OPENCV_IO_ENABLE_HEADLESS"] = "1"

global label_dic
label_dic = {"drawings": 0, "hentai": 1, "neutral": 2, "porn": 3, "sexy": 4}


def get_key(dict, value):
    """
    Return key given a value from a dictionary
    """
    for key, val in dict.items():
        if val == value:
            return key
    return "Value not found"


def load_onnx_model(model_path: str):
    """
    Load ONNX model

    Args:
        model_path (str): Path to ONNX model file

    Returns:
        ONNX inference session
    """
    try:
        # Try with CUDA provider first, fall back to CPU if not available
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        model = onnxruntime.InferenceSession(model_path, providers=providers)
        logging.info(f"ONNX model loaded with providers: {model.get_providers()}")
    except Exception as e:
        logging.warning(f"Failed to load with CUDA, falling back to CPU only: {str(e)}")
        model = onnxruntime.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        logging.info("ONNX model loaded with CPU provider only")

    return model


def load_img(path):
    """
    Load and preprocess image for ONNX model

    Args:
        path (str): Path to image file

    Returns:
        numpy.ndarray: Preprocessed image as numpy array
    """
    try:
        image = Image.open(path).convert("RGB")
        image = image.resize((224, 224), Image.BILINEAR)
        img = np.array(image, dtype=np.float32)
        img /= 255.0
        img = np.transpose(img, (2, 0, 1))
        return img
    except Exception as e:
        logging.error(f"Error loading image {path}: {str(e)}")
        raise


def predict_image_onnx(image_path: str, model) -> Dict:
    """
    Make NSFW prediction for a single image using ONNX model

    Args:
        image_path (str): Path to image file
        model: ONNX model inference session

    Returns:
        Dict: Dictionary with class probabilities
    """
    logging.info(f"Inference with ONNX model on file {image_path}")
    try:
        input_name = model.get_inputs()[0].name
        output_name = model.get_outputs()[0].name

        # Load and preprocess the image
        inputs = np.array([load_img(image_path)])

        # Run inference
        outputs = model.run([output_name], {input_name: inputs})[0]
        logits = np.array(outputs)

        # Convert logits to probabilities
        probabilities = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        probs = probabilities[0]

        # Create output dictionary with class probabilities
        output_probs = {}
        for prob, key in zip(probs, range(0, len(probs))):
            label = get_key(label_dic, key)
            output_probs[label] = float(prob)

        return output_probs
    except Exception as e:
        logging.error(f"Error during image inference: {str(e)}")
        raise


def predict_video_frames_onnx(
    video_path: str,
    model,
    progress_bar: bool = True,
) -> List[float]:
    """
    Make NSFW prediction for each video frame using ONNX model

    Args:
        video_path (str): Path to video file
        model: ONNX model inference session
        progress_bar (bool): Whether to show progress bar

    Returns:
        List[float]: List of NSFW probabilities for each frame
    """
    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            logging.error(f"Failed to open video file: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        logging.info(f"Frames per second: {fps}")
        nsfw_probabilities = []
        frame_count = 0
        images = []

        if progress_bar:
            try:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                pbar = tqdm(total=total_frames)
            except:
                logging.warning(
                    "Could not determine frame count, disabling progress bar"
                )
                pbar = None
                progress_bar = False
        else:
            pbar = None

        # Process and collect all frames
        while True:
            ret, bgr_frame = cap.read()
            if not ret:
                break

            if pbar is not None:
                pbar.update(1)

            frame_count += 1
            try:
                frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (224, 224), cv2.INTER_AREA)
                img = np.array(frame, dtype=np.float32)
                img /= 255.0
                img = np.transpose(img, (2, 0, 1))
                images.append(img)
            except Exception as e:
                logging.warning(f"Error processing frame {frame_count}: {str(e)}")
                continue

        logging.info(f"Processed {frame_count} frames, now running inference")

        # Release capture resources but don't call destroyAllWindows
        cap.release()

        # Explicitly avoid the call to destroyAllWindows which causes issues in headless environments
        # cv2.destroyAllWindows() - REMOVED THIS LINE

        if pbar is not None:
            pbar.close()

        if not images:
            logging.warning("No frames were extracted from the video")
            return []

        # Run inference on all collected frames
        input_name = model.get_inputs()[0].name
        output_name = model.get_outputs()[0].name

        # Process frames in batches if there are many frames to avoid memory issues
        batch_size = 32
        for i in range(0, len(images), batch_size):
            try:
                batch = np.array(images[i : i + batch_size])
                outputs = model.run([output_name], {input_name: batch})[0]
                logits = np.array(outputs)

                # Convert logits to probabilities
                probabilities = np.exp(logits) / np.sum(
                    np.exp(logits), axis=1, keepdims=True
                )

                # Calculate NSFW score for each frame in the batch
                for probs in probabilities:
                    output_probs = {}
                    for prob, key in zip(probs, range(0, len(probs))):
                        label = get_key(label_dic, key)
                        output_probs[label] = prob

                    # Aggregate probabilities for "sexy", "hentai", and "porn" classes
                    prob_nsfw = (
                        output_probs["sexy"]
                        + output_probs["hentai"]
                        + output_probs["porn"]
                    )
                    nsfw_probabilities.append(prob_nsfw)
            except Exception as e:
                logging.error(f"Error processing batch {i//batch_size}: {str(e)}")
                continue

        return nsfw_probabilities
    except Exception as e:
        logging.error(f"Error during video inference: {str(e)}")
        return []
