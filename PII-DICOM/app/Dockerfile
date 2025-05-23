FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt requirements.txt


RUN apt-get update && \
    apt-get install -y \
    build-essential \
    python3-dev \
    python3-setuptools \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    make \
    gcc \
    libmagic1 \
    poppler-utils \
    unrtf \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    libreoffice

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt
RUN python -m spacy download en_core_web_lg

COPY . .
EXPOSE 8155

CMD ["sh", "-c", "uvicorn endpoint_dicom:app --host 0.0.0.0 --port 8155"]