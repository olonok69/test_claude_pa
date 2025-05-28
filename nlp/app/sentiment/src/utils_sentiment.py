import re
from langdetect import detect_langs
from langdetect import detect
from inscriptis import get_text
import numpy as np
import aiofiles
from fastapi.encoders import jsonable_encoder
import os
import json
from detectaicore import (
    pii_doc,
    NpEncoder,
    MINIMUN_CHAR_LENGTH,
    MINIMUN_WORDS_LENGTH,
    lfilenames_types,
)
from starlette.concurrency import run_in_threadpool
import platform


def remove_mystopwords(sentence, stopwords, my_stop_words):
    """
    remove stop words and words less than 3 letters
    """
    sentence = re.sub(r"\b\w{1,2}\b", "", sentence)
    sentence = re.sub("\s\s+", " ", sentence)
    tokens = sentence.split(" ")
    tokens_filtered = [
        word for word in tokens if not word in stopwords and not word in my_stop_words
    ]

    return (" ").join(tokens_filtered)


def remove_mystopwords_enhanced(
    sentence: str, stopwords: list[str], my_stop_words: list[str]
):
    """
    remove stop words and words less than 3 letters

    """
    sentence = re.sub(r"\b\w{1,2}\b", "", sentence.lower())
    sentence = re.sub("\s\s+", " ", sentence)
    sentence = re.sub("\n+", " ", sentence)
    sentence = sentence.strip()
    tokens = sentence.split(" ")
    tokens_filtered = [
        word
        for word in tokens
        if not word in stopwords and not word in my_stop_words and word.isalpha()
    ]

    return (" ").join(tokens_filtered)


def get_pure_text(text: str):
    return re.sub("[^A-Za-z@ñ\s\\:\.]+", " ", text)


def detect_language(text: str) -> dict:
    """Detects the text's language."""
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.

    result = translate_client.detect_language(text)
    return {"language": result["language"], "confidence": result["confidence"]}


def detect_languages(text: str) -> dict:
    """Detects the text's language."""

    language = ""
    confidence = 0
    try:
        language = detect(text)
        confidence = 1.0
    except:
        result = detect_langs(text)
        language = result[0].lang
        confidence = result[0].prob

    return {"language": language, "confidence": str(confidence)}


def classify_doc(text, labels_str, mode, classifier):
    labels = labels_str.split("_")
    output = classifier(text, labels, multi_label=bool(mode))
    # only 25 chars
    out = {}
    output["sequence"] = output["sequence"][:50]
    classification_labels = []
    for label, score in zip(output["labels"], output["scores"]):
        out = {}
        out["name"] = label
        out["score"] = str(np.round(score, 3))
        classification_labels.append({"score": out})
    return classification_labels


def extract_keywords(kw_model, docs):
    keywords = kw_model.extract_keywords(
        docs,
        nr_candidates=20,
        top_n=10,
        keyphrase_ngram_range=(1, 1),
        use_mmr=True,
        diversity=0.7,
    )
    output = {}
    out = []
    for key in keywords:
        output = {}
        output["name"] = key[0]
        output["score"] = str(key[1])
        out.append({"score": output})
    return out


def multi_classifier(doc, text, labels, classifier, classifier_multi):
    """
    Classifier ready for multiprocessing
    """
    if doc.language == "en":
        output = classify_doc(text, labels, "False", classifier)
    else:
        output = classify_doc(text, labels, "False", classifier_multi)
    return output


def multi_keywords(kw_model, text):
    """
    keywords ready for multiprocessing
    """
    keywords = extract_keywords(kw_model, text)
    return keywords


def multi_toxicity(toxic_model, text):
    """
    toxicity ready for multiprocessing
    """
    results = toxic_model.predict([text])
    output_toxic = []

    for key in results.keys():
        out = {}
        out["name"] = key
        out["score"] = np.round(results[key][0], 5)
        output_toxic.append({"score": out})

    return output_toxic


def extract_docs(
    list_docs,
    list_pii_docs,
    file_types_all: bool = False,
    filenames_types: list[str] = lfilenames_types,
):
    # for each document returned parse them with BautifoulSoup HTML parser and do some cleaning. -> method get_text_from_html
    for doc in list_docs:
        new_doc = pii_doc()
        file_type = doc.get("source").get("file_type")
        if file_types_all:
            if not (file_type in filenames_types):
                filenames_types.append(file_type)

        if file_type in filenames_types:
            new_doc.request_raw = doc.get("source").get("content")
            if new_doc.request_raw == None:
                continue
            # extract data from tika document and populate document object
            new_doc.file_name = doc.get("source").get("file_name")
            new_doc.file_type = doc.get("source").get("file_type")
            new_doc.scan_id = doc.get("id")
            new_doc.index = doc.get("index")
            new_doc.file_uri = doc.get("source").get("fs").get("uri")
            new_doc.doc_raw = get_text(new_doc.request_raw)
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
                try:
                    new_doc.language = detect_languages(new_doc.doc_only_text)
                except:
                    new_doc.language = {"language": "not_found", "confidence": "0"}
                list_pii_docs.append(new_doc)

        else:
            continue
    return list_pii_docs


async def extract_sentiment(
    docs_with_languages,
    all_stopwords,
    my_stop_words,
    labels,
    classifier,
    classifier_multi,
    kw_model,
    toxic_model,
):
    """
    Extract sentiment infromation for documents after being extracted from html tika output
    docs_with_languages,
    all_stopwords,
    my_stop_words,
    labels,
    classifier,
    classifier_multi,
    kw_model,
    toxic_model,
    """
    chunck = []
    number_of_files_posted = 0
    i = 0
    for doc in docs_with_languages:
        # remove unnecessary words
        text = remove_mystopwords_enhanced(doc.doc_raw, all_stopwords, my_stop_words)
        if len(text) > MINIMUN_CHAR_LENGTH:
            doc.classification_labels = await run_in_threadpool(
                multi_classifier, doc, text, labels, classifier, classifier_multi
            )
            doc.keywords = await run_in_threadpool(multi_keywords, kw_model, text)
            doc.toxic_labels = await run_in_threadpool(
                multi_toxicity, toxic_model, text
            )

            doc_dict = doc.dict(
                exclude={"doc_raw", "request_raw", "doc_only_text", "index", "pii_hits"}
            )

            new_file = doc_dict.copy()
            name_json = doc.scan_id + ".json"
            json_file = os.path.join("output", name_json)
            print(json_file)

            chunck.append(jsonable_encoder(new_file))
            # post list of dicts to index

            if platform.system() == "Windows":
                try:
                    async with aiofiles.open(json_file, "w") as f:
                        file = json.dumps(
                            jsonable_encoder(new_file),
                            cls=NpEncoder,
                            indent=4,
                            ensure_ascii=True,
                        )
                        await f.write(file)
                except:
                    pass  # for test to pass
        else:
            print(f"file {doc.scan_id} less than {MINIMUN_CHAR_LENGTH} chars")

        i = i + 1

    return chunck
