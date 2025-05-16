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
    libgl1 \
    make \
    gcc \
    libmagic1 \
    poppler-utils \
    unrtf \
    libpoppler-cpp-dev \
    pkg-config \
    libreoffice \
    nano \
    net-tools \
    procps\
    curl

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

ENV LOCAL_ENV="0"
ENV DOCS_PATH=/app/docs
ARG API_VERSION
ENV APPLICATIONVERSION=${API_VERSION}

# Echo the build version for verification
RUN echo "Build version: [v $API_VERSION ]"
RUN echo "Application version: [v $APPLICATIONVERSION ]"

COPY . .

CMD ["python", "endpoint_ocr_nats.py"]