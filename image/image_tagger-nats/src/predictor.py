import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import torch
from torchvision.models import ResNet18_Weights
from PIL import Image
import onnxruntime
import logging
from torchvision import transforms
import logging
import numpy as np
from .ov_florence2_helper import OVFlorence2Model
from transformers import AutoProcessor
from collections import Counter


def get_prediction_model(
    model_path: str, use_onnx: str, use_openvino: str, device: str = "cpu"
):
    """
    Load model ONNX or pytorch

    Args:
        models_path (str): Path to model
        use_onnx (str): YES/NO use onnx format
        device (str): cuda or cpu

    Returns:
        _type_: Processor and ViT model
    """
    processor = None
    if use_onnx == "YES":
        logging.info(f"Loading model ONNX RestNet: {model_path} in CPU")
        model = onnxruntime.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )

    elif use_openvino == "YES":
        model = OVFlorence2Model(model_path, "AUTO")
        processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        logging.info(f"Loading model and processor Florence2: {model_path} in CPU")

    else:

        try:
            model_path = os.path.join(model_path, "pytorch-vision-300a8a4")
            model = torch.hub.load(
                model_path,
                "resnet18",
                weights=ResNet18_Weights.DEFAULT,
                source="local",
            )
            logging.info(f"Loading model resnet18 from : {model_path}")
        except:
            model = torch.hub.load(
                "pytorch/vision",
                "resnet18",
                weights=ResNet18_Weights.DEFAULT,
            )
            logging.info("Loading model: pytorch/vision resnet18 from HF")
        # switch model to evaluation mode
        model.eval()
    return model, processor


def read_image(image_encoded):
    image = Image.open(image_encoded)
    return image


def preprocess(input_image):
    preprocess = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(
        0
    )  # create a mini-batch as expected by the model
    return input_batch


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def run_sample(session, categories, inputs, num_labels):
    """
    Run Inference ONNX model
    """

    input_arr = inputs.cpu().detach().numpy()
    ort_outputs = session.run([], {"input": input_arr})[0]

    output = ort_outputs.flatten()
    output = softmax(output)  # this is optional
    top5_catid = np.argsort(-output)[:num_labels]
    results = []
    for catid in top5_catid:
        logging.info(f" Category: {categories[catid]}, Probability: {output[catid]}")
        r = {
            "label": categories[catid],
            "probability": float(output[catid]),
        }
        results.append(r)
    return results


def run_sample_ov(processor, model, image_path, prompt):
    """
    Run Inference ONNX model
    args:
    processor: Image Processor
    model: OV model
    iamge_path : path to Image
    prompt = prompt to be use with Florence 2
    """

    image = Image.open(image_path).convert("RGB")
    inputs = processor(text=prompt, images=image, return_tensors="pt")

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        do_sample=False,
        num_beams=2,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    parsed_answer = processor.post_process_generation(
        generated_text,
        task=prompt,
        image_size=(image.width, image.height),
    )
    output = parsed_answer.get(prompt)
    labels = output.get("labels")
    # Contar ocurrencias de cada etiqueta
    label_counts = Counter(labels)
    # # Convertir el Counter a una lista de diccionarios
    result = [{label: count} for label, count in label_counts.items()]

    return result


def predict(
    input_image,
    model,
    processor,
    num_labels,
    use_onnx,
    device,
    prompt,
    use_openvino,
    image_path,
):
    """
    Predict classes
    Args:
        input_image
        model
        processor
        num_labels
        use_onnx
        device: Device to load  model
        use_openvino: if to use Florence 2 with OpenVino or Salesforce Blip
        prompt: Instruction to use only with Florence2
        iamge_path: Path to image

    """
    # Read the categories
    with open("conf/imagenet_classes.txt", "r") as f:
        categories = [s.strip() for s in f.readlines()]
    # Inference
    results = []
    if use_openvino == "YES":
        results = run_sample_ov(processor, model, image_path, prompt)

    elif use_onnx == "YES":
        results = run_sample(model, categories, input_image, num_labels)
    else:
        # Move the input and model to GPU for speed if available
        if torch.cuda.is_available():
            input_image = input_image.to("cuda")
            model.to("cuda")

        with torch.no_grad():
            output = model(input_image)
        # The output has unnormalized scores. To get probabilities, you can run a softmax on it.
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        results = []
        # Show top categories per image
        top5_prob, top5_catid = torch.topk(probabilities, num_labels)
        for i in range(top5_prob.size(0)):
            r = {
                "label": categories[top5_catid[i]],
                "probability": float(top5_prob[i].item()),
            }
            results.append(r)

    return results
