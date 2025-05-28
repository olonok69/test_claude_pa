FROM python:3.10.11

RUN apt-get update && apt-get install python3-pip -y

# create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /translate

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir --prefer-binary  -r requirements.txt \
    && pip3 install --no-cache-dir --prefer-binary  torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116  \
    && pip3 install --no-cache-dir --prefer-binary  paste packaging opencv-python-headless \
    && pip3 install --no-cache-dir --prefer-binary  https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl \
    && pip3 install --no-cache-dir uvicorn    

COPY . .

RUN rm -rf notebooks __pycache__ .ipynb_checkpoints requirements.txt *.ipynb output out out_translate \
    models/stsb-xlm-r-multilingual models/sentence-t5-large models/sentiment-roberta-large-english \
    archive pii_codex

RUN mkdir output

EXPOSE 5007
CMD ["uvicorn", "endpoint_translate:endpoint", "--host", "0.0.0.0", "--port", "5007", "--reload"]
