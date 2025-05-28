# Introduction

This repository contains Detect-AI components. Essentially, Detect-AI consists of machine and deep learning applications that extract insights from data files in different formats (text, audio, and images). Each component is offered through an endpoint that can be queried via HTTP POST requests. Components use well-known deep learning, machine learning, and Python libraries to solve various use cases, such as:

- PII/PHI Detection in Multiple Languages [Moved here](https://dev.azure.com/sceven/DataDetect/_git/Detect-AI-PII-Classifier)
- Multi-Label Tagging for an Arbitrary Number of User-Defined Classes [Folder Semantic](nlp\app\sentiment)
- Toxicity/Profanity Analysis [Folder profanity](nlp\app\sentiment)
- Hate/Offensive Speech Analysis [Folder hate](nlp\app\hate)
- Keyword Detection and Document Summarization [Folder semantic](nlp\app\semantic)
- Semantic Similarity Search [Folder Similarity](nlp\app\sentiment)
- Document Similarity (Semantic Similarity / Fuzzy Similarity) [Folder Similarity](nlp\app\sentiment)
- Text Translation (Chinese to English, English to Chinese, and others) [Folder translate](D:\repos\Detect-AI-nlp\nlp\app\translate)
- Image Multi-Label Tagging [Moved to here](https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/image_tagger)
- Image Summarization (Description of Image Content) [Moved to here](https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/image_captioning)
- OCR (Optical Character Recognition) [Moved to here](https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/ocr)
- Not Suitable for Work Content Detection (Only for Images) [Moved to here](https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/nsfw)
- Audio-to-Text Extraction [Folder audio](D:\repos\Detect-AI-nlp\audio)

# Getting Started

The AI components are organized into different folders:

      Main Folders

      nlp: Package that uses Natural Language Processing to extract insights from documents.
      audio: Package that uses deep learning models and Huggingface Transformers to extract text from audio files.
      image: Package that uses deep learning models and Huggingface Transformers to extract text and insights from images.
      nlp: Contains 5 different components (text specialized components) with their related Docker files, divided into two folders:

      Folder App
      - Dockerfile_classification: PII/PHI analyzer detector Endpoint
      - Dockerfile_hate: Hate/Offensive Speech analyzer Endpoint
      - Dockerfile_semantic: Semantic Search Analyzer Endpoint
      - Dockerfile_sentiment: Multi-Label Tagging, Toxicity analyzer, Keyword Detector Endpoints
      Folder translate
      - Dockerfile_translate: Document Translation Endpoint

      audio: Contains 1 single component (audio specialized component) with its related Dockerfile:

      Folder speech_to_text
       - Dockerfile: Speech to text Endpoint

      image: Contains 2 components (image specialized components) with their related DockerFiles organized in two folders:

      Folder image_tagger
      - Dockerfile: Image tagging and Image description/summarization Endpoints
      Folder ocr
      - Dockerfile: OCR Endpoint

1. Installation Process
   Each component has a Dockerfile and a requirements.txt file to create the container.

2. Software Dependencies

   - Python 3.11.10
   - Files requirements.txt (One per docker/Model)

3. Latest Releases
   N/A

4. API References
   N/A

# Build and Test

In the test folder, we have different unit test cases for each component. Tests are included as part of the CI pipeline, which is configured in the azure-pipelines.yml file present at the root of our repository: -> https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?version=GB4820-Create-Readme-File&path=/azure-pipelines.yml

For tests, we use the unittest and pytest Python libraries.

# Running Locally with Docker Compose

in the folder `C:\git\Detect-AI\docker` there are 2 compose files - use the file `docker-compose-local` for local API development.
you can build the 2 main images (classification & ROT) with the command

> clear; Cd C:\git\Detect-AI; docker build -f "rot\Dockerfile" -t rot:latest "rot"; Cd C:\git\Detect-AI; docker build --pull --rm -f "nlp\app\classification\Dockerfile" -t classification:latest "nlp\app\classification"

these images are large so will take a number of minutes.

you can run the models in docker using the compose command

> cls; cd C:\git\Detect-AI\docker; docker-compose -f docker-compose-local.yml up -d

you can test the services using the health check endpoints

classification

> curl --location 'http://localhost:5000/health-check'

ROT

> curl --location 'http://localhost:5007/health-check'

# PremCloud Development

To contribute to this repository, you need to have experience in Python, serverless applications using FastAPI, and a number of deep learning and machine learning technologies like PyTorch, spaCy, scikit-learn, HuggingFace Transformers, and OpenCV.

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
