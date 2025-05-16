import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import json
import os
import platform

# Mark all tests in this file as OCR tests
pytestmark = pytest.mark.ocr

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["IS_TEST"] = "1"


CONDA_ENV = os.getenv("CONDA_DEFAULT_ENV") if os.getenv("CONDA_DEFAULT_ENV") in ['ocr','pii'] else "no"

IS_LOCAL = 1 if CONDA_ENV in  ['ocr','pii'] else 0

if platform.system() == "Linux" and int(IS_LOCAL) == 1:
    from image.ocr.app.endpoint_ocr import app
    client = TestClient(app)


def test_api_object():
    """
    Test endpoint FastAPI class
    """
    endpoint = FastAPI()
    assert type(endpoint) == FastAPI


def test_endpoint_ocr():
    """
    Test endpoint OCR image to extract text
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_ocr", "ocr_1_file.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())
    # get documents from TIKA output
    list_docs = docs.get("documents")
    
    if platform.system() == "Linux" and int(IS_LOCAL) == 1:
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        out = response.get("data")
        # correct keys
        assert set(list(out[0].keys())) == {'id', 'index', 'source'}
        # Number of document treated
        assert response['number_documents_treated'] == 1


def test_endpoint_ocr_error():
    """
    Test endpoint OCR documents contains errors
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_ocr", "ocr_1_file_error.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    
    if platform.system() == "Linux" and int(IS_LOCAL) == 1:
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        # assert return code
        assert response['status'] == {'code': 500, 'message': 'Error'}
        # assert content in error
        assert len(response['error']) > 0

def test_endpoint_ocr_image_no_data():
    """
    Test endpoint OCR No images in Document to process
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_ocr", "ocr_2_no_image.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    
    if platform.system() == "Linux" and int(IS_LOCAL) == 1:
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        # assert return code
        assert response['status'] == {'code': 200, 'message': 'Success'}
        # assert content in error
        assert len(response['error']) == 0
        # list of documents not treated
        assert set(response['list_id_not_treated'][0]) ==set({'c5613d504ddd3367d15ba6ab9245c062018fa21135aec4d452f9b3e4d88c441b': 'No Images in this document to process'})
        # number of documents not treated
        assert response['number_documents_non_treated'] == 1
        # number of documents  treated
        assert response['number_documents_treated'] == 0



def test_endpoint_ocr_image_no_valid_document():
    """
    Test endpoint ocr no valid document
    """

    with open(os.path.join(ROOT_DIR, "dummy_data", "test_ocr", "ocr_no_valid_documents.json"), "rb") as f:
        docs = f.read()

    docs = json.loads(docs.decode())

    
    if platform.system() == "Linux" and int(IS_LOCAL) == 1:
        # post the document to endpoint
        response = client.post(
            "/process",
            json=docs,
        )
        assert response.status_code == 200
        response = response.json()
        # assert return code
        assert response['status'] == {'code': 200, 'message': 'Success'}
        # assert content in error
        assert len(response['error']) == 0
        # list of documents not treated
        assert set(response['list_id_not_treated'][0]) ==set({
            "7587bcb2-4ea6-4a64-a426-040b40bf414b": "File type not valid"
        })
        # number of documents not treated
        assert response['number_documents_non_treated'] == 1
        # number of documents  treated
        assert response['number_documents_treated'] == 0
