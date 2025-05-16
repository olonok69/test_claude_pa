FROM python:3.10

RUN apt-get update && apt-get install python3-pip -y && apt-get -y install tesseract-ocr

# create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /ocr-scanner

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt 
RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116  
RUN pip3 install paste packaging opencv-python-headless
RUN pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl
RUN pip3 install presidio_analyzer presidio_anonymizer presidio_image_redactor
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

COPY ./ocr-scanner .

RUN rm -rf notebooks
RUN rm -rf __pycache__
RUN rm -rf .ipynb_checkpoints
RUN rm -f requirements.txt
RUN rm -f *.ipynb
RUN rm -f *.jpg

EXPOSE 5003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5003", "--reload"]