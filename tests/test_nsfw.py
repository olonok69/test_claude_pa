import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dotenv import load_dotenv

import json
import os
import platform

# Mark all tests in this file as nsfw tests
pytestmark = pytest.mark.nsfw

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
IS_TEST = os.getenv("IS_TEST")
LOCAL_ENV = os.getenv("LOCAL_ENV")

os.environ["IS_TEST"] = "1"

# IS_TEST = "1"
# LOCAL_ENV= "1"

if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
    from image.nsfw.app.endpoint_nsfw import endpoint

    client = TestClient(endpoint)


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_api_object():
    """
    Test endpoint FastAPI class
    """
    endpoint = FastAPI()
    assert type(endpoint) == FastAPI


def test_endpoint_nsfw_image():
    """
    Test endpoint image
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_nsfw","image_jpg.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        content = response.get("data")[0]['source']['content']
        assert set(list(content[0].get("data").keys()))  ==   {'drawings', 'hentai', 'neutral', 'porn', 'sexy'}    

def test_endpoint_nsfw_video():
    """
    Test endpoint image
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_nsfw","video_mov.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        content = response.get("data")[0]['source']['content']
        assert set(list(content[0].keys()))  ==   set(list(content[0].keys())) 
        
def test_endpoint_error():
    """
    Test endpoint image
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_nsfw","nsfw_error.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        content = response.get("error")
        assert  "object of type 'NoneType' has no len()" in content

def test_endpoint_no_data():
    """
    Test endpoint image
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_nsfw","nsfw_no_data.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        content = response.get("number_documents_non_treated")
        assert  1 == int(content)
        
def test_endpoint_wrong_extension():
    """
    Test endpoint image
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_nsfw","nsfw_wrong_extension.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    if platform.system() == "Linux" and IS_TEST == "1" and LOCAL_ENV == "1":
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        content = response.get("number_documents_non_treated")
        assert  1 == int(content)