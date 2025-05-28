import re
from langdetect import detect_langs
from langdetect import detect
from classes.dataclasses import classification_doc
from inscriptis import get_text
import orjson
import json
import spacy
from starlette.concurrency import run_in_threadpool
import requests
from src.constants import (
    MINIMUN_CHAR_LENGTH,
    MINIMUN_WORDS_LENGTH,
    lfilenames_types,
    l_array,
)


def write_and_post(filename: str = None, index: str = None):
    # # post to classification API
    url2 = f"http://localhost:8080/api/Index/{index}/classification/AddDocument"
    fin = open(filename, "rb")
    data = fin.read()

    # files = {'file': fin}
    try:
        r = requests.post(url2, data=data)  # files=files)
        print(f"file {filename}  status {r.status_code}")
    finally:
        fin.close()


def write_and_post_bulk(list_files: list, l_array: list, url2: str) -> int:
    """
    write list of individual outcomes to url2, bulky API
    """

    array_json = []
    number_of_files_posted = 0
    for file, i in zip(list_files, range(len(list_files))):
        with open(file, "r") as f:
            json_file = json.load(f)
        array_json.append(json_file)

        if len(array_json) == l_array:
            data = json.dumps(array_json).encode()
            try:
                r = requests.post(url2, data=data)  # files=files)

            except:
                print("An exception Has Occurred")

            print(f"status {r.status_code}")
            if r.status_code == 201:
                number_of_files_posted = number_of_files_posted + len(array_json)
            array_json = []

    # post rest of the files
    if len(array_json) > 0:
        data = json.dumps(array_json).encode()
        try:
            r = requests.post(url2, data=data)  # files=files)

        except:
            print("An exception Has Occurred")

        print(f"status {r.status_code}")
        if r.status_code == 201:
            number_of_files_posted = number_of_files_posted + len(array_json)
        array_json = []
    return number_of_files_posted


def post_processing(pii: dict, nlp: spacy.lang.xx.MultiLanguage) -> int:
    """
    filtering PII entities
    pii : dict-> dictionary with a PII/PHI ocurrence
    return :  int status 0 and 1 consider this entity. 2 dont process it
    """
    status = 0
    if pii.get("entity_type") == "PERSON":
        # create spacy document with specialized model
        doc = nlp(pii.get("pii_text"))
        # create list of entities persons extracted from document
        persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        # check with specialized model if PERSON IT is an entity recognized as it
        if (
            pii.get("pii_text") in persons
            and len(pii.get("pii_text")) > 3
            and pii.get("score") > 0.85
        ):
            per = pii.get("pii_text")
            print(f"Person match  to be included in entities {per}")
            return 1
        else:
            return 2

    elif len(pii.get("pii_text")) < 3:  # All entities with size lower than 3 remove
        return 2
    elif (
        pii.get("entity_type") == "CREDIT_CARD_NUMBER"
        or pii.get("entity_type") == "CREDIT_CARD"
    ):
        # check if credit cards are Visa, Master Card or American Express
        if pii["pii_text"][:1] in ["5", "4", "3"]:
            return 1
        else:
            return 2
    elif (
        pii.get("entity_type") == "US_DRIVERS_LICENSE_NUMBER"
        or pii.get("entity_type") == "US_DRIVER_LICENSE"
    ):
        # Only interested in Driver Licenses Numbers above 0.85 score
        if pii.get("score") > 0.85:
            return 1
        else:
            return 2

    else:
        return status


def write_and_post_array(list_dics: list[dict], l_array: list, url2: str) -> int:
    """
    Post array of json files to url in URL2
    """

    number_of_files_posted = 0
    # encode list of dics and a json
    data = json.dumps(list_dics).encode()

    try:
        r = requests.post(url2, data=data)  # files=files)

    except:
        print("An exception Has Occurred")

    print(f"status {r.status_code}")
    if r.status_code == 201:
        number_of_files_posted = number_of_files_posted + len(list_dics)

    return number_of_files_posted


def remove_mystopwords_enhanced(
    sentence: str, stopwords: list[str], my_stop_words: list[str]
) -> str:
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


def get_pure_text(text: str) -> str:
    """
    remove numbers and special characters from text
    """
    return re.sub("[^A-Za-zñ\s]+", "", text)


def get_language_list_documents(list_docs: list[classification_doc], n: int = 30):
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
        try:
            doc.language = detect_languages(doc.doc_only_text)
        except:
            doc.language = {"language": "not_found", "confidence": "0"}
            pass

        list_docs_with_language_detected.append(doc)
    return list_docs_with_language_detected


def detect_languages(text: str) -> dict:
    """
    Detects the text's language.
    """
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


def extract_docs(
    list_docs: list[dict],
    list_pii_docs: list[classification_doc],
    file_types_all: bool = False,
    filenames_types: list[str] = lfilenames_types,
) -> list[classification_doc]:
    """
    for each document returned parse them with get_text HTML parser and do some cleaning. -> method get_text_from_html
    list_docs --> list[dict] list with documents obtained from Tika
    list_pii_docs --> list[pii_doc] list of pii_doc objects comming from previous iterations

    return list[pii_doc] , lits of pii_doc objects after this iteration
    """
    for doc in list_docs:
        new_doc = classification_doc()
        file_type = doc.get("source").get("file_type")
        if file_types_all:
            if not (file_type in filenames_types):
                filenames_types.append(file_type)
        # only files in filenames _types
        if file_type in filenames_types:
            new_doc.request_raw = doc.get("source").get("content")
            if new_doc.request_raw == None:
                continue
            new_doc.file_name = doc.get("source").get("file_name")
            new_doc.file_type = doc.get("source").get("file_type")
            new_doc.scan_id = doc.get("id")
            new_doc.index = doc.get("index")
            new_doc.file_uri = doc.get("source").get("fs").get("uri")
            # new_doc.doc_raw = get_text_from_html(new_doc.request_raw, blacklist)
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


def get_docs_from_elasticsearch_query(elasticsearch_response_json: dict) -> list[str]:
    """
    this method expect a dictionary with all Documents returned from ElastcicSearch
    in the dictionary we have the matching docs in the key hits and then hits again.
    params:
    elasticsearch_response_json: dict. Dictionary returned from ElasticSearch
    return : list of strings , each string correspond to a document in the input dictionary
    """

    list_docs = elasticsearch_response_json["hits"]["hits"]

    list_pii_docs = []
    filenames_types = ["pdf", "doc", "docx", "txt"]
    # for each document returned parse them with BautifoulSoup HTML parser and do some cleaning. -> method get_text_from_html
    for doc in list_docs:
        new_doc = classification_doc()
        file_type = doc["_source"]["file_type"]
        if file_type in filenames_types:
            new_doc.request_raw = doc["_source"]["content"]
            new_doc.file_name = doc["_source"]["file_name"]
            new_doc.file_type = doc["_source"]["file_type"]
            new_doc.scan_id = doc.get("_id")
            new_doc.index = doc.get("_index")
            new_doc.file_uri = doc.get("_source").get("fs").get("uri")
            # new_doc.doc_raw = get_text_from_html(new_doc.request_raw, blacklist)
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
                list_pii_docs.append(new_doc)

        else:
            continue
    return list_pii_docs


def get_text_from_html(page: str, blacklist: list) -> str:
    """
    use BeautifoulSoup to extract text from HTML received from ElasticSearch. TIKA output

    params:
    page : html extracted from request
    blacklist : tags to be excluded from html
    return : String , html parsed with Beautiful soup and some formating like remove multiple \n and spaces
    """
    output = ""
    if len(page) > 0:
        soup = BeautifulSoup(page, "html.parser")
        text = soup.find_all(string=True)
        for t in text:
            if t.parent.name not in blacklist:
                output += "{} ".format(t)
        output = re.sub(r"\n+", "\n", output).strip()
        output = re.sub(r"(\n )+", "\n", output).strip()
        output = output.replace("\n", " ")
        output = output.replace(r"\\", "")
        output = re.sub(r" {2,}", " ", output)
        return output
    else:
        raise ValueError("An empty page was sent to get_text_from_html method")


def filter_pii_scores(
    doc: classification_doc, score_th: float = 0.6, remove_duplicates: bool = False
):
    """ "
    Filter the pii hit based on a threshold score_th and select the hit with max score when a text score in multiple categories
    params doc: pii_doc object
    score_th: float threshold
    """
    analysis = doc.pii_hits["analyses"]
    filtered_scores = []
    # create a dictionaty with unique hits with maximum score
    hits = {}
    for a in analysis[0]["analysis"]:
        start = a.get("start")
        end = a.get("end")
        if not (str(start) + str(end) in hits.keys()):
            hits[str(start) + str(end)] = a.get("score")
        else:
            if a.get("score") > hits[str(start) + str(end)]:
                hits[str(start) + str(end)] = a.get("score")
    # filter for those that a higher than threshold score_th
    for a in analysis[0]["analysis"]:
        start = a.get("start")
        end = a.get("end")
        score = a.get("score")
        # Filter based in score and removed duplicates
        if (
            score
            and score > score_th
            and score >= hits[str(start) + str(end)]
            and remove_duplicates == True
        ):
            # Add texto to Pii entity
            texto = doc.doc_raw[start:end]
            a["pii_text"] = texto.strip()
            a["pii_text"] = a["pii_text"].encode().decode("utf-8")
            filtered_scores.append(a)
        elif remove_duplicates == False:
            texto = doc.doc_raw[start:end]
            a["pii_text"] = texto.strip()
            a["pii_text"] = a["pii_text"].encode().decode("utf-8")
            filtered_scores.append(a)

    doc.pii_hits = filtered_scores
    return doc


async def get_docs_from_elasticsearch_query_get_documents_v2(
    query: dict,
    url: str,
    file_types_all: bool = False,
    filenames_types: list[str] = lfilenames_types,
) -> list[str]:
    """
    this method expect a dictionary with all Documents returned from ElastcicSearch
    in the dictionary we have the matching docs in the key hits and then hits again.
    params:
    elasticsearch_response_json: dict. Dictionary returned from ElasticSearch
    return : list of strings , each string correspond to a document in the input dictionary
    """
    list_pii_docs = []
    data1 = json.dumps(query).encode()
    r = requests.post(url, data=data1)
    if r.status_code == 200:
        elasticsearch_response_json = r.json()
        list_docs = elasticsearch_response_json.get("documents")

        if len(list_docs) > 0:
            searchAfter = elasticsearch_response_json.get("documents")[-1]["sorts"][0]
        else:
            return "List of Documents empty"
    else:
        return f"{url} return error code {r.status_code}"

    # extract documents from list of docs
    list_pii_docs = await run_in_threadpool(
        extract_docs,
        list_docs,
        list_pii_docs,
        file_types_all=file_types_all,
        filenames_types=filenames_types,
    )

    l_num_document = len(list_pii_docs)
    num_docs = 1
    while num_docs > 0:
        query["search_after"] = [searchAfter]
        query["size"] = l_array
        data1 = json.dumps(query).encode()
        try:
            resp1 = requests.post(url, data=data1)
        except:
            return f"Exception  {resp1.status_code}"

        if resp1.status_code == 200:
            json_resp = orjson.loads(resp1.text)
            num_docs = json_resp.get("documentCount")

            if num_docs == 0:
                break
            list_docs = json_resp.get("documents")
            list_pii_docs = await run_in_threadpool(
                extract_docs,
                list_docs,
                list_pii_docs,
                file_types_all=file_types_all,
                filenames_types=filenames_types,
            )
            # list_pii_docs = extract_docs(list_docs, list_pii_docs)
            searchAfter = json_resp.get("documents")[-1]["sorts"][0]
            l_num_document = l_num_document + num_docs
            print(f"Read next {num_docs} documents. Total {l_num_document}")

        else:
            return f"Exception  {resp1.status_code}"

    return list_pii_docs
