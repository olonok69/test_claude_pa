import re
from langdetect import detect_langs
from langdetect import detect
from inscriptis import get_text
from inscriptis.css_profiles import CSS_PROFILES
from inscriptis.model.config import ParserConfig
from typing import Union, List
import os
import json
import requests
import logging
from detectaicore import (
    classification_doc,
    classification_doc_v2,
    lfilenames_types,
    MINIMUN_CHAR_LENGTH,
    MINIMUN_WORDS_LENGTH,
    Job,
)
from src.summarization import get_classification_no_summarization

global version

version = "v2"

# Strict indentation handling getText  --> extract text from HTML
config = ParserConfig(css=CSS_PROFILES["strict"].copy())


def get_pure_text(text: str) -> str:
    """
    remove numbers and special characters from text
    """
    return re.sub("[^A-Za-zñ\s]+", "", text)


def get_language_list_documents(
    list_docs: list[classification_doc | classification_doc_v2], n: int = 30
):
    """
    Receive a list of strings and detect the language using google translate
    params
    list_docs: list[str] list of documents (text after being extracted from Elastic Search query and cleaning)
    n : int send only first n chars
    return dictionary with language detected and confidence score  ex. {'language': 'en', 'confidence': 0.9861727356910706}
    """
    list_docs_with_language_detected = []
    # for each document in the list of documents
    for doc in list_docs:
        # get only text. Remove special chars and numbers
        doc.doc_only_text = get_pure_text(doc.doc_raw)
        doc.language = detect_languages(doc.doc_only_text)
        list_docs_with_language_detected.append(doc)
    return list_docs_with_language_detected


def detect_languages(text: str) -> dict:
    """
    Detects the text's language.
    """

    confidence = 0
    language = detect(text)
    if language != None:
        confidence = 1.0
    else:
        result = detect_langs(text)
        language = result[0].lang
        confidence = result[0].prob

    return {"language": language, "confidence": float(confidence)}


def extract_docs(
    list_docs: list[dict],
    list_pii_docs: list[classification_doc | classification_doc_v2],
    jobs: dict,
    new_task: Job,
    file_types_all: bool = False,
    filenames_types: list[str] = lfilenames_types,
    image_file_names: list[str] = [],
    ocr: int = 0,
    version: "str" = version,
) -> List[Union[List[classification_doc | classification_doc_v2], List[str]]]:
    """
    for each document returned parse them with get_text HTML parser and do some cleaning. -> method get_text_from_html
    list_docs --> list[dict] list with documents obtained from Tika
    list_pii_docs --> list[pii_doc] list of pii_doc objects comming from previous iterations

    return
    ------
    list[pii_doc] , lits of pii_doc objects after this iteration
    documents_non_teathred list of document id Non trated for any reason
    """
    documents_non_teathred = []
    jobs[new_task.uid].status = "Extracting Metadata From request"
    for doc in list_docs:
        # Only documents with embedded_depth = 0. No nested content produced by Tika
        file_type = doc.get("source").get("file_type")
        # only files in filenames _types and not None
        if file_types_all and file_type != None:
            if file_type not in filenames_types:
                filenames_types.append(file_type)
        # Add Image File names in case this is not empty. This use for OCR extraction
        if len(image_file_names) > 0 and ocr == 1:
            for t in image_file_names:
                filenames_types.append(t)
        # Add the id of the document to list of document Non Treated
        if not file_type or file_type not in filenames_types:
            documents_non_teathred.append({doc.get("id"): "File type not valid"})
            continue
        # create document type depending of the version
        if version == "v1" or int(os.environ.get("IS_TEST", "0")) == 1:
            new_doc = classification_doc()
        elif version == "v2":
            new_doc = classification_doc_v2()

        # only files in filenames _types and not None
        if file_type in filenames_types:
            new_doc.request_raw = doc.get("source").get("content")
            if (
                new_doc.request_raw == None
                or len(new_doc.request_raw) < MINIMUN_CHAR_LENGTH
            ):
                documents_non_teathred.append(
                    {doc.get("id"): "No Input Text in documents"}
                )
                continue
            new_doc.file_name = doc.get("source").get("file_name")
            new_doc.file_type = doc.get("source").get("file_type")
            if version == "v1" or int(os.environ.get("IS_TEST", "0")) == 1:
                new_doc.scan_id = doc.get("id")
            else:
                new_doc.document_id = doc.get("id")
            new_doc.index = doc.get("index")
            new_doc.file_uri = doc.get("source").get("fs").get("uri")

            new_doc.doc_raw = get_text(new_doc.request_raw, config)
            # Remove condition which produce errors
            new_doc.doc_raw = re.sub("(\s\d{1,2})(\.)(\s)", r"\1 \3", new_doc.doc_raw)
            new_doc.file_name = (
                new_doc.file_name.split(".")[0] + f".{new_doc.file_type}"
            )

            # only if length of chars in text it is higher of MINIMUN_CHAR_LENGTH and more than MINIMUN_WORDS_LENGTH
            num_words = len(new_doc.doc_raw.split(" "))
            if (
                len(new_doc.doc_raw) > MINIMUN_CHAR_LENGTH
                and num_words >= MINIMUN_WORDS_LENGTH
            ):
                # extract only words for language detection
                new_doc.doc_only_text = get_pure_text(new_doc.doc_raw)
                language = detect_languages(new_doc.doc_only_text)
                if language != None:
                    new_doc.language = detect_languages(new_doc.doc_only_text)
                else:
                    new_doc.language = {"language": "not_found", "confidence": "0"}
                list_pii_docs.append(new_doc)
            jobs[new_task.uid].status = (
                f"Extracting Metadata.- number of document processed {len(list_pii_docs)}"
            )

        else:
            continue
    return list_pii_docs, documents_non_teathred


def request_summarization_docker(
    doc: str, url: str = "http://127.0.0.1:5015/process"
) -> str:
    """
    summarize text
    params:
    doc :str = String to sumarize
    url: str = Docker summarization URL entry point
    """
    # request to summarize text. Dont introduce in try/except to chath problems
    data = {}
    data["text"] = doc
    data1 = json.dumps(data).encode()
    r = requests.post(url, data=data1)
    return r.json()["data"]


async def get_top_n_classes_with_scores(
    endpoint,
    list_docs,
    docs_with_languages,
    documents_non_teathred,
    jobs: dict,
    new_task: Job,
    k: int = 5,
    url_summarization: str = "",
    chunk_length: int = 4800,
    use_summarization: bool = 1,
    overlap: int = 0,
):
    """
    Get top classes with scores

    params:
    endpoint = FastAPI Endpoint
    list_docs = List of Documents to score
    docs_with_languages = List of Documents to score with language
    documents_non_teathred = List of Documents Non treated
    jobs: dict = Jobs Dictionary
    new_task: Job = Job object
    k: int = 5 = Number of documents to return , default 4
    url_summarization: str = ""  URL docker summarization
    chunk_length: int = 4800 Length text which trigger summarization
    """
    chunck = []
    list_anonymized_docs = []

    jobs[new_task.uid].status = (
        f"Getting the most likely top {k} classes of documents....."
    )
    logging.info(f"Getting the most likely top {k} classes of documents.....")
    for doc in docs_with_languages:
        # length of the document
        lenght_doc = len(doc.doc_raw)
        if lenght_doc > MINIMUN_CHAR_LENGTH:

            doc_id = doc.document_id
            file_name = doc.file_name

            if lenght_doc > chunk_length:
                if int(use_summarization) == 1:
                    response = request_summarization_docker(
                        doc.doc_raw, url=url_summarization
                    )
                    res = endpoint.db.similarity_search_with_score(response, k=k)
                    logging.info(
                        f"file{file_name} has a lenght of {lenght_doc}, after summarization {len(response)}"
                    )

                else:
                    res, num_documentos = get_classification_no_summarization(
                        doc.doc_raw, chunk_length, overlap, endpoint, k=5
                    )

                    logging.info(
                        f"file{file_name} has a lenght of {lenght_doc}, number of chuncks {num_documentos}"
                    )

            else:
                res = endpoint.db.similarity_search_with_score(doc.doc_raw, k=k)
                logging.info(f"file{file_name} has a lenght of {lenght_doc} ")

            # create output
            output = []
            if int(use_summarization) == 1:
                for doc_result, score in res:
                    output.append({doc_result.metadata.get("classifier"): score})
            else:
                output = res
            # Avoid to treat again same document
            for doco in list_docs:
                id_or = doco.get("id")
                if doc_id == id_or:
                    doco["source"]["content"] = output
                    chunck.append(doco)
                    break
        else:
            # if no valid text , document id to documents_non_teathred
            documents_non_teathred.append(
                {doc.document_id: "No Enought text to process document"}
            )

    return chunck, list_anonymized_docs, documents_non_teathred
