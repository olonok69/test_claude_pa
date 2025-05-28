# Introduction 
In this Repository we have Demos and test we have done different use cases and Technologies


# Folder Databricks-mlflow
## Databricks MLflow Demos

### Fine-Tuning Llama 3.2 with QLoRA
**Notebook**: `Datablricks-mlflow/Llama3.2-qlora/LLama3_2_3B_fine_tuning_QLORA_DORA_customer_service.ipynb`

This notebook demonstrates fine-tuning Meta's Llama 3.2 (3B parameters) model for customer service applications using advanced optimization techniques:

**Key Features:**
- **Model**: meta-llama/Llama-3.2-3B-Instruct - A multilingual LLM optimized for dialogue, retrieval, and summarization tasks
- **Dataset**: Bitext Customer Service Training Dataset with 27 intents across 10 categories (26,872 Q&A pairs)
- **Optimization Techniques**:
  - QLoRA (Quantized Low-Rank Adaptation) for 4-bit quantization
  - DoRA (Weight-Decomposed Low-Rank Adaptation) for improved performance
  - PEFT (Parameter-Efficient Fine-Tuning) integration
- **MLflow Integration**: Full experiment tracking, model versioning, and deployment

**How to Use:**
1. Set up Databricks credentials in environment variables
2. Configure MLflow tracking URI and experiment path
3. Run cells sequentially to:
   - Load and prepare the customer service dataset
   - Initialize the model with 4-bit quantization
   - Configure LoRA/DoRA parameters
   - Train the model with MLflow tracking
   - Log the fine-tuned model to MLflow Model Registry
   - Test inference with custom prompts

### Phi-3 Vision with OpenVINO Optimization
**Notebook**: `Datablricks-mlflow/openvino-Phi3/MLFLOW_OpenVino_Phi3_Vision.ipynb`

This notebook showcases deploying Microsoft's Phi-3 Vision multimodal model with OpenVINO optimization for efficient inference:

**Key Features:**
- **Model**: Phi-3-Vision/Phi-3.5-Vision - State-of-the-art multimodal model for image understanding
- **OpenVINO Integration**: 
  - Model conversion to OpenVINO IR format
  - INT4 weight compression using NNCF
  - Optimized inference on CPU/GPU
- **MLflow Deployment**: Custom PythonModel wrapper for serving
- **Capabilities**: Image captioning, visual Q&A, scene understanding

**How to Use:**
1. Install required dependencies (OpenVINO, NNCF, transformers)
2. Select model variant (Phi-3-vision or Phi-3.5-vision)
3. Run conversion pipeline to:
   - Convert PyTorch model to OpenVINO format
   - Apply INT4 quantization for memory efficiency
   - Save optimized model components
4. Deploy with MLflow:
   - Create custom inference wrapper
   - Log model with artifacts and dependencies
   - Test with image inputs
5. Load from Model Registry for production use

**Performance Benefits:**
- Reduced model size (up to 75% compression)
- Faster inference on edge devices
- Lower memory footprint while maintaining accuracy


# Folder PII-DICOM
## Detailed readme
Detailed readme [here](PII-DICOM/readme.md)
### DICOM
DICOM® — Digital Imaging and Communications in Medicine — is the international standard for medical images and related information. It defines the formats for medical images that can be exchanged with the data and quality necessary for clinical use.

DICOM® is implemented in almost every radiology, cardiology imaging, and radiotherapy device (X-ray, CT, MRI, ultrasound, etc.), and increasingly in devices in other medical domains such as ophthalmology and dentistry. With hundreds of thousands of medical imaging devices in use, DICOM® is one of the most widely deployed healthcare messaging Standards in the world. There are literally billions of DICOM® images currently in use for clinical care.

Since its first publication in 1993, DICOM® has revolutionized the practice of radiology, allowing the replacement of X-ray film with a fully digital workflow. Much as the Internet has become the platform for new consumer information applications, DICOM® has enabled advanced medical imaging applications that have “changed the face of clinical medicine”. From the emergency department, to cardiac stress testing, to breast cancer detection, DICOM® is the standard that makes medical imaging work — for doctors and for patients.

DICOM® is recognized by the International Organization for Standardization as the ISO 12052 standard.

https://www.dicomstandard.org/about


###  FHIR
FHIR (Fast Healthcare Interoperability Resources) Specification, which is a standard for exchanging healthcare information electronically. 

https://www.hl7.org/fhir/overview.html

###  De-identifying sensitive burnt-in text in DICOM images

1. Redact text Personal Health Information (PHI) present as pixels in DICOM images
2. Visually compare original DICOM images with their redacted versions


### Tools for Health Data Anonymization c#
https://github.com/microsoft/Tools-for-Health-Data-Anonymization/tree/master

- DICOM intructions [here](PII-DICOM\Tools-for-Health-Data-Anonymization\docs\DICOM-anonymization.md)
- FHIR Instructions [here](PII-DICOM\Tools-for-Health-Data-Anonymization\docs\FHIR-anonymization.md)

###  Demo
This Demo has been done in a Debian 9 in WSL2 with python 3.11. Dotnet 8 for the C# tools.

## Prerequisites
Before getting started, make sure presidio and the latest version of Tesseract OCR are installed. For detailed documentation, see the [installation docs](https://microsoft.github.io/presidio/installation).


#### Tesseract

```
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

```
tesseract --version

OUTPUT
tesseract 5.3.0
 leptonica-1.82.0
  libgif 5.2.1 : libjpeg 6b (libjpeg-turbo 2.1.2) : libpng 1.6.39 : libtiff 4.5.0 : zlib 1.2.13 : libwebp 1.2.4 : libopenjp2 2.5.0
 Found AVX2
 Found AVX
 Found FMA
 Found SSE4.1
 Found OpenMP 201511
 Found libarchive 3.6.2 zlib/1.2.13 liblzma/5.4.1 bz2lib/1.0.8 liblz4/1.9.4 libzstd/1.5.4
 Found libcurl/7.88.1 OpenSSL/3.0.14 zlib/1.2.13 brotli/1.0.9 zstd/1.5.4 libidn2/2.3.3 libpsl/0.21.2 (+libidn2/2.3.3) libssh2/1.10.0 nghttp2/1.52.0 librtmp/2.3 OpenLDAP/2.5.13
```

```
!pip install presidio_analyzer presidio_anonymizer presidio_image_redactor -q
!python -m spacy download en_core_web_lg -q 
```

Notebook [Demo](PII-DICOM\example_dicom_image_redactor.ipynb)

# Folder Tika
## Detailed readme
Detailed readme [here](tika/readme.md)


Demo of tika OCR, Language Detection and Mime Detection

### Apache Tika a content analysis toolkit

The Apache Tika™ toolkit detects and extracts metadata and text from over a thousand different file types (such as PPT, XLS, and PDF). All of these file types can be parsed through a single interface, making Tika useful for search engine indexing, content analysis, translation, and much more. 

### Install
- https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-InstallationofTikaServer
- https://github.com/apache/tika-docker  (docker pull apache/tika:latest-full)
- https://pypi.org/project/tika/
- https://tika.apache.org/1.10/formats.html
  
### Documentation 
https://cwiki.apache.org/confluence/display/tika

[Notebook](tika\tika_test.ipynb)

# Folder Nats
## Detailed readme
Detailed readme [here](Nats/readme.md)

Test Nats Python client working with Server in docker container
- [Publisher](Nats\publisher.ipynb)
- [Consumer](Nats\consumer.ipynb)


# Folder Elastic
## Detailed readme
Detailed readme [here](elastic/readme.md)