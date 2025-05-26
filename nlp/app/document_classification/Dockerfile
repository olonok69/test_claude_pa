# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y python3-pip  ffmpeg libsm6 libxext6 git net-tools  nano procps && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
# Set the working directory to /app
WORKDIR /document_classification

# Copy the requirements file into the image
COPY ./requirements.txt /document_classification/requirements.txt
# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu124/torch_stable.html

# Copy every content from the local folder to the image
COPY . .

EXPOSE 5014
# Run server
CMD ["uvicorn", "endpoint_doc_classification:endpoint", "--host=0.0.0.0", "--port=5014"]
