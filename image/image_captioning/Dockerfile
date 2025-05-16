# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg git libmagic1 libsm6 libxext6 nano net-tools procps python3-pip virtualenv wget zlib1g

# Copy the requirements file into the image
COPY ./requirements.txt /image_captioning/requirements.txt

# Set the working directory to /app
WORKDIR /image_captioning

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt 
RUN pip install "openvino>=2024.3.0" "einops" "torch>2.1" "torchvision" "timm>=0.9.8" \
                "transformers>=4.41" "pillow" --extra-index-url https://download.pytorch.org/whl/cpu



# Copy every content from the local folder to the image
COPY . .

EXPOSE 5010
# Run server
CMD ["sh", "-c", "uvicorn endpoint_image_captioning:app --host 0.0.0.0 --port 5010 --workers 2"]
#CMD ["sh", "-c", "uvicorn endpoint_image_captioning:app --host 0.0.0.0 --port 5010 "]