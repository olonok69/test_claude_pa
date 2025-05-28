FROM python:3.10.11

RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
    && pip install --no-cache-dir uvicorn 

COPY ./app .

RUN rm -rf notebooks archive models out output out_semantic __pycache__ .ipynb_checkpoints requirements.txt *.ipynb
RUN mkdir out

EXPOSE 5007
CMD ["uvicorn", "endpoint_rot:endpoint", "--host", "0.0.0.0", "--port", "5007", "--reload"]
