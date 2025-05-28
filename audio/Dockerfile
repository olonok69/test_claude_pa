FROM python:3.10

RUN apt-get update && apt-get install python3-pip -y

# create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /speech_to_text

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt 
RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116  
RUN pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl



COPY ./speech_to_text .

RUN rm -rf notebooks
RUN rm -rf __pycache__
RUN rm -rf .ipynb_checkpoints
RUN rm -f requirements.txt
RUN rm -f *.ipynb
RUN rm -rf output
RUN rm -rf out
RUN rm -rf out_semantic
RUN rm -rf models/stsb-xlm-r-multilingual
RUN rm -rf models/sentence-t5-large
RUN rm -rf models/sentiment-roberta-large-english
RUN rm -rf archive
RUN rm -rf pii_codex
RUN mkdir output

EXPOSE 5002


CMD ["uvicorn", "endpoint_speech:endpoint", "--host", "0.0.0.0", "--port", "5002", "--reload"]