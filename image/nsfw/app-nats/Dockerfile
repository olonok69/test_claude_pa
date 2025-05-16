FROM python:3.12-slim

ARG API_VERSION

RUN apt-get update && apt-get install -y python3-pip  ffmpeg libsm6 libxext6 git \
    nano \
    net-tools \
    procps\
    curl

# Set the working directory to /app
WORKDIR /app
# Copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
RUN pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu121

# Copy every content from the local folder to the image
COPY . .


ENV DOCS_PATH=/app/images

ARG API_VERSION
ENV APPLICATIONVERSION=${API_VERSION}

# Echo the build version for verification
RUN echo "Build version: [v $API_VERSION ]"
RUN echo "Application version: [v $APPLICATIONVERSION ]"


CMD ["python", "endpoint_nsfw-nats.py"]