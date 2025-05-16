FROM python:3.11-slim

RUN apt-get update && apt-get install python3-pip  ffmpeg libsm6 libxext6 git -y

# Set the working directory to /app
WORKDIR /app
# Copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
RUN pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu121

# Copy every content from the local folder to the image
COPY . .

EXPOSE 5009
# Run server
CMD ["sh", "-c", "uvicorn endpoint_nsfw:endpoint --host 0.0.0.0 --port 5009 --workers 2"]
#CMD ["sh", "-c", "uvicorn endpoint_nsfw:endpoint --host 0.0.0.0 --port 5009 "]