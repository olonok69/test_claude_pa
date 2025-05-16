# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && apt-get install python3-pip  ffmpeg libsm6 libxext6 git -y

# Set the working directory to /app
WORKDIR /image_tagger


# Copy the requirements file into the image
COPY ./requirements.txt /image_tagger/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt 
RUN pip install "openvino>=2024.3.0" "einops" "torch>2.1" "torchvision" "timm>=0.9.8" \
                "transformers>=4.41" "pillow" --extra-index-url https://download.pytorch.org/whl/cpu

# Copy every content from the local folder to the image
COPY . .

EXPOSE 5011
# Run server

CMD ["sh", "-c", "uvicorn endpoint_image_tagger:app --host 0.0.0.0 --port 5011 --workers 2"]
#CMD ["sh", "-c", "uvicorn endpoint_image_tagger:app --host 0.0.0.0 --port 5011 "]