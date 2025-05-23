# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg git libmagic1 libsm6 libxext6 nano net-tools procps python3-pip virtualenv wget zlib1g



# Set the working directory to /app
WORKDIR /elastic_llm
COPY ./requirements.txt /elastic_llm/requirements.txt
# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt 




# Copy every content from the local folder to the image
COPY . .

EXPOSE 8133
# Run server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8133 "]