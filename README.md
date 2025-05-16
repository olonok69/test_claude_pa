# Introduction

This repository contains Computer Vision Detect-AI components. Initially this repository contained everything, so git contains the history of all commits since May 2023 when we start this app.
Currently we have the following models hosted here:

- [NSFW (Non-Safe/Suitable for work)](image\nsfw): Model to detect content (Images and Video) not suitable for a working environment (porn, hentai, sexy images and videos).
- [Image Captioning](image\image_captioning): Model that return a text description of a given Image,
- [Image Tagger](image\image_tagger): Classification Model that give you from a given Image, the n labels among of the 1000 Classes of ImageNet Dataset.
- [OCR](image\ocr) Extract text from Images and Images in documents


# Description Models

## NSWF Non-Safe/Suitable for work
This model classify an image versus 5 different classes ("drawings", "hentai", "neutral", "porn", "sexy"). The model it is based in google/vit-base-patch16-224-in21, https://huggingface.co/google/vit-base-patch16-224-in21k as fundational model and it was fine tuned with a specific dataset specialized on this matter. After that, the model has been converted to onnx to be able to run it in a cpu. 
Fine tuned model is in folder (ai-models / image / nsfw / nsfw_pytorch) of https://datadetect.blob.core.windows.net/ai-models. ONNX version is in (ai-models / image / nsfw / onnx) same folder. Default use is ONNX model
[in folder](docs\Notebooks\nsfw) we have the relevant Notebooks to do
- [Fine tuning  model](docs\Notebooks\nsfw\Image_classification_NSWF_full_training.ipynb) (Done in Google Colab and Weight And Biases)
- [Inference](docs\Notebooks\nsfw\Inference_image_classification_NSWF_full.ipynb)(Done in Google Colab and Weight And Biases)
- [Log Fine tuned model to MLFLOW](docs\Notebooks\nsfw\FineTuned_Vit_save_to_MLFLOW.ipynb). Experiment */Users/jhuertas@capaxdiscovery.com/nsfw_pytorch* in Databricks
- [Convert Fine Tune model to ONNX and save MLFLOW](docs\Notebooks\nsfw\FineTuned_Vit_to_ONNX_save_to_MLFLOW.ipynb). Experiment */Users/jhuertas@capaxdiscovery.com/nsfw_onnx* in Databricks. RunID b697725fbb6e407d963a318c159deda5
- [Dataset Fine Tuning](https://datadetect.blob.core.windows.net/ai-models/datasets/nsfw/) Blob Store Azure dadadetect. RunID 6da60b5150064cc5a9081e9ddd809596

## Image Captioning
This CV model returns you the caption or description of a given Image. There are two models. First for GPU  is a  https://huggingface.co/Salesforce/blip-image-captioning-large and second one is Florence2 base converted to Openvino IR format https://huggingface.co/microsoft/Florence-2-base to run in CPU. Default Model Florence 2.
Folders
- BLIP (ai-models / image / image_captioning / blip-image-captioning-large)
- Florence (ai-models / image / image_captioning / Florence-2-base-ft)

### Image Tagging
This CV model provide you a vector of probabilities of a image to belong to the [1000 Classes](image\image_tagger\conf\imagenet_classes.txt) available in ImageNet Dataset https://www.image-net.org/update-mar-11-2021.php
There is two versions of the model. For GPU, we use a pretrained RestNet18 Network https://pytorch.org/vision/main/models/generated/torchvision.models.resnet18.html, and for CPU we use the same but transformed to ONNX format. Default use is ONNX model.

Folders
- RestNet18  (ai-models / image /  image_tagger / pytorch-vision-300a8a4)
- Florence (ai-models / image /  image_tagger / onnx)

### OCR
This model return you the text content in an Image or multiple images in a document. We user Tesseract python Wrapper to do this in combination with multiple libraries which allow us to work with multiple formats.
Supported formats in [file](image\ocr\app\utils\utils.py)
```
    if ext in ["jpg", "png", "jpeg", "gif", "bmp"]:
        utf8_text, document = extract_from_single_image(document, app)
    elif ext in ["tif", "tiff"]:
        utf8_text = extract_text_from_tiff(document, app)
    elif ext == "pdf":
        utf8_text = extract_text_from_pdf(document, app)
    elif ext in ["doc", "docx"]:
        utf8_text = extract_text_from_doc(document, app)
    elif ext in ["ppt", "pptx"]:
        utf8_text = extract_text_from_ppt(document, app)
    elif ext in ["htm", "html"]:
        utf8_text = extract_text_from_html(document, app)
    elif ext in ["odt"]:
        utf8_text = extract_text_from_odt(document, app)
    elif ext in ["rtf"]:
        utf8_text = extract_text_from_rtf(document, app)
```
OCR Language models are in the folder (ai-models / image /  ocr / tessdata). Here we have all available in tesseract, but default is English


1. Installation Process
   Each component has a Dockerfile and a requirements.txt file to create the container.

2. Software Dependencies

   - Python 3.11
   - Files requirements.txt

3. Latest Releases
   N/A

4. API References
   N/A

# Build and Test

In the test folder, we have different unit test cases for each component. Tests are included as part of the CI pipeline, which is configured in the [azure-pipelines.yml](azure-pipelines.yml)
For tests, we use the unittest and pytest Python libraries.

# Running Locally with Docker Compose

in the folder `C:\git\Detect-AI\docker` there are 2 compose files - use the file `docker-compose-local` for local API development.

these images are large so will take a number of minutes.

you can run the models in docker using the compose command

> cls; cd C:\git\Detect-AI\docker; docker-compose -f docker-compose-local.yml up -d

you can test the services using the health check endpoints

classification

> curl --location 'http://localhost:5000/health-check'


# PremCloud Development

To contribute to this repository, you need to have experience in Python, serverless applications using FastAPI, and a number of deep learning and machine learning technologies like PyTorch, spaCy, scikit-learn, HuggingFace Transformers, OpenVino Runtime, ONNX Runtime and OpenCV.

# Setup Development Environment

    - Install Visual Studio Code or PyCharm.
    - Install Anaconda. Example for Windows: Anaconda Installation Guide for Windows.
    - Clone the repository to your local machine: git clone https://dev.azure.com/sceven/DataDetect/_git/Detect-AI.

    - Create a Conda environment from the environment.yml file (located at the root of our repository):
      - conda env create --file environment.yml
      - conda activate detect-ai
    - Launch Jupyter Notebook with the command: jupyter notebook inside the environment.

    - If you want to use Visual Studio Code, navigate to the root of the repo in a command line window, run conda activate detect-ai, and then code ..

# Endpoints / APIs

We use FastAPI, a web framework for building APIs with Python 3.7+ based on standard Python type hints. Documentation: FastAPI Documentation. https://fastapi.tiangolo.com/

A description of all APIs and endpoints developed in these applications is included in [here](docs/ENDPOINTS.md)
