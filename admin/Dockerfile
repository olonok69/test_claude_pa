# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y python3-pip  ffmpeg libsm6 libxext6 git net-tools  nano procps && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
# Set the working directory to /app
WORKDIR /admin

# Copy the requirements file into the image
COPY ./requirements.txt /admin/requirements.txt
# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy every content from the local folder to the image
COPY . .

EXPOSE 5016
# Run server
CMD ["uvicorn", "endpoint_admin_models:endpoint", "--host=0.0.0.0", "--port=5016"]
