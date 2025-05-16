# Build Stage - used by devops pipeline
ARG API_VERSION

FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    python3-dev \
    python3-setuptools \
    tesseract-ocr \
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

ARG API_VERSION
ENV APPLICATIONVERSION=${API_VERSION}

# Echo the build version for verification
RUN echo "Build version: [v $API_VERSION ]"
RUN echo "Application version: [v $APPLICATIONVERSION ]"

COPY . .
EXPOSE 5003

CMD ["sh", "-c", "uvicorn endpoint_ocr:app --host 0.0.0.0 --port 5003 --workers 2"]