FROM python:3.10.11

RUN apt-get update && apt-get install -y python3-pip

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /hate

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt \
    && pip install --no-cache-dir --prefer-binary torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118 \
    && pip install --no-cache-dir --prefer-binary paste packaging opencv-python-headless \
    && pip install --no-cache-dir --prefer-binary https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl \
    && pip install --no-cache-dir uvicorn

COPY . .

RUN rm -rf notebooks __pycache__ .ipynb_checkpoints requirements.txt *.ipynb output out out_hate \
    models/stsb-xlm-r-multilingual models/sentence-t5-large models/sentiment-roberta-large-english \
    archive pii_codex
    
RUN mkdir output

EXPOSE 5004
CMD ["uvicorn", "endpoint_hate:endpoint", "--host", "0.0.0.0", "--port", "5004", "--reload"]
