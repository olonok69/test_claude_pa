FROM python:3.10.11

RUN apt-get update && apt-get install python3-pip -y

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /semantic

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
    && pip install --no-cache-dir --prefer-binary torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116 \
    && pip install --no-cache-dir --prefer-binary https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl \
    && pip install --no-cache-dir uvicorn

COPY . .

RUN rm -rf notebooks __pycache__ .ipynb_checkpoints requirements.txt *.ipynb output out out_semantic models/bart-large-mnli models/multilingual-MiniLMv2-L6-mnli-xnli models/sentiment-roberta-large-english models/*.ckpt archive pii_codex
RUN mkdir output

EXPOSE 5006
CMD ["uvicorn", "endpoint_semantic:endpoint", "--host", "0.0.0.0", "--port", "5006", "--reload"]
