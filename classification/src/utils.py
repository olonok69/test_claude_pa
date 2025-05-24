import re
from langdetect import detect_langs
from langdetect import detect
import aiofiles
from inscriptis import get_text
from inscriptis.css_profiles import CSS_PROFILES
from inscriptis.model.config import ParserConfig
import json
import os
import spacy
from typing import Dict, List, Set, Tuple, Any, Optional

from detectaicore import index_response, print_stack
from fastapi.encoders import jsonable_encoder
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
import copy
import magic


from detectaicore import (
    classification_doc,
    classification_doc_v2,
    MINIMUN_CHAR_LENGTH,
    MINIMUN_WORDS_LENGTH,
    SCORE_NER,
    lfilenames_types,
    Job,
    NpEncoder,
)

from pii_codex.config import (
    version,
    APP_LANGUAGES,
    MAX_LENGTH_PRINT,
    CHUNK_LENGTH,
)
import logging


# Strict indentation handling getText  --> extract text from HTML
config = ParserConfig(css=CSS_PROFILES["strict"].copy())


def post_processing(
    pii: Dict[str, Any], nlp: spacy.language.Language, score: float = SCORE_NER
) -> int:
    """
    Filter PII entities based on various rules

    Args:
        pii: Dictionary with a PII/PHI occurrence
        nlp: spaCy language model
        score: Score threshold (default: SCORE_NER)

    Returns:
        Status code: 0 or 1 to keep entity, 2 to discard
    """
    # Skip entities with text length < 3
    if len(pii.get("pii_text", "")) < 3:
        return 2

    entity_type = pii.get("entity_type", "")
    pii_text = pii.get("pii_text", "")
    pii_score = pii.get("score", 0)

    # Special handling for PERSON entities
    if entity_type == "PERSON":
        doc = nlp(pii_text)
        persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]

        if pii_text in persons and len(pii_text) > 3 and pii_score > score:
            logging.info(f"Person match to be included in entities: {pii_text}")
            return 1
        return 2

    # Special handling for credit card numbers
    if entity_type in ["CREDIT_CARD_NUMBER", "CREDIT_CARD"]:
        if pii_text and pii_text[:1] in ["5", "4", "3"]:
            return 1
        return 2

    # Special handling for driver's licenses
    if entity_type in ["US_DRIVERS_LICENSE_NUMBER", "US_DRIVER_LICENSE"]:
        if pii_score > 0.85:
            return 1
        return 2

    return 0  # Default: keep the entity


def remove_mystopwords_enhanced(
    sentence: str, stopwords: Set[str], my_stop_words: List[str]
) -> str:
    """
    Remove stop words and words less than 3 letters

    Args:
        sentence: Input text
        stopwords: Set of stopwords to filter out
        my_stop_words: Additional stopwords to filter out

    Returns:
        Cleaned text with stopwords removed
    """
    # Remove words with 1-2 characters
    sentence = re.sub(r"\b\w{1,2}\b", "", sentence.lower())

    # Normalize whitespace and newlines in a single pass
    sentence = re.sub(r"[\s\n]+", " ", sentence).strip()

    # Split and filter tokens - use set operations for better performance
    tokens = sentence.split(" ")
    stopwords_set = set(stopwords) | set(my_stop_words)
    tokens_filtered = [
        word for word in tokens if word not in stopwords_set and word.isalpha()
    ]

    return " ".join(tokens_filtered)


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
        try:
            doc.language = detect_languages(doc.doc_only_text)
        except Exception as e:
            logging.warning(f"Language not detected. Exception {e}")
            doc.language = {"language": "not_found", "confidence": "0"}

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
    except Exception as e:
        logging.warning(f"Language not detected. Exception {e}")
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
    version: str = version,
    language_engine: str = "en",
) -> tuple[list, list]:
    """
    Extract and process documents for PII/PHI analysis.

    Args:
        list_docs: List of documents obtained from Tika
        list_pii_docs: List of pii_doc objects from previous iterations
        jobs: Dictionary with job status information
        new_task: Job object for the current task
        file_types_all: If True, include all file types; otherwise use filenames_types
        filenames_types: List of file types to include (ignored if file_types_all=True)
        image_file_names: List of image file names to include for OCR processing
        ocr: If 1, use OCR for image extraction; if 0, don't use OCR
        version: Application version ("v1" or "v2")
        language_engine: Language code for processing (en, es, etc.)

    Returns:
        Tuple containing:
        - Updated list of pii_doc objects
        - List of documents that couldn't be processed with reasons
    """
    documents_non_treated = []
    jobs[new_task.uid].status = "Extracting Metadata From request"

    # Update filenames_types if needed
    allowed_file_types = _update_allowed_file_types(
        file_types_all, filenames_types, image_file_names, ocr
    )

    for doc in list_docs:
        # Only process root documents (no nested content)
        doc_source = doc.get("source", {})
        file_type = doc_source.get("file_type")

        # Skip documents with invalid file types
        if not file_type or file_type not in allowed_file_types:
            documents_non_treated.append({doc.get("id"): "File type not valid"})
            continue

        try:
            # Process document based on its type and content
            processed_doc = _prepare_doc_for_processing(
                doc, version, language_engine, allowed_file_types
            )

            if processed_doc:
                list_pii_docs.append(processed_doc)
                # Update job status periodically
                jobs[new_task.uid].status = (
                    f"Extracting Metadata - {len(list_pii_docs)} documents processed"
                )
            else:
                documents_non_treated.append({doc.get("id"): "Processing failed"})

        except Exception as e:
            logging.warning(f"Error processing document {doc.get('id')}: {str(e)}")
            documents_non_treated.append({doc.get("id"): f"Error: {str(e)}"})

    return list_pii_docs, documents_non_treated


def _update_allowed_file_types(
    file_types_all: bool,
    filenames_types: list[str],
    image_file_names: list[str],
    ocr: int,
) -> list[str]:
    """Update and return the list of allowed file types."""
    allowed_types = filenames_types.copy()

    # Include all detected file types if requested
    if file_types_all:
        # Note: This will be populated as we process documents
        pass

    # Add image file types if OCR is enabled
    if ocr == 1 and image_file_names:
        allowed_types.extend(image_file_names)

    return allowed_types


def _prepare_doc_for_processing(
    doc: dict, version: str, language_engine: str, allowed_file_types: list[str]
) -> Optional[classification_doc | classification_doc_v2]:
    """Prepare a document for processing and return a classification document if successful."""
    doc_source = doc.get("source", {})
    doc_id = doc.get("id")

    # Create appropriate document type based on version
    if version == "v1" or int(os.environ.get("IS_TEST", "0")) == 1:
        new_doc = classification_doc()
    else:
        new_doc = classification_doc_v2()

    # Extract mime type
    mime_type = magic.from_buffer(doc_source.get("content", "").encode(), mime=True)

    # Extract content and basic metadata
    raw_content = doc_source.get("content")
    if not raw_content or len(raw_content) < MINIMUN_CHAR_LENGTH:
        logging.warning(f"Document {doc_id} has insufficient text content")
        return None

    # Set document metadata
    new_doc.request_raw = raw_content
    new_doc.file_name = doc_source.get("file_name", "")
    new_doc.file_type = doc_source.get("file_type", "")

    # Set document ID based on version
    if version == "v1" or int(os.environ.get("IS_TEST", "0")) == 1:
        new_doc.scan_id = doc_id
    else:
        new_doc.document_id = doc_id

    # Set additional metadata
    new_doc.index = doc.get("index")
    new_doc.file_uri = doc_source.get("fs", {}).get("uri", "")

    # Extract text based on mime type
    if not _extract_text_content(new_doc, mime_type):
        logging.warning(f"Document {doc_id} has unsupported mime type: {mime_type}")
        return None

    # Clean up text content
    new_doc.doc_raw = re.sub("(\s{1}\d{1,2})(\.{1})(\s{1})", r"\1 \3", new_doc.doc_raw)

    # Normalize filename
    if new_doc.file_name and new_doc.file_type:
        new_doc.file_name = f"{new_doc.file_name.split('.')[0]}.{new_doc.file_type}"

    # Check document length requirements
    num_words = len(new_doc.doc_raw.split())
    if len(new_doc.doc_raw) <= MINIMUN_CHAR_LENGTH or num_words < MINIMUN_WORDS_LENGTH:
        logging.warning(
            f"Document {doc_id} doesn't meet length criteria: "
            f"{len(new_doc.doc_raw)} chars, {num_words} words"
        )
        return None

    # Extract text for language detection and set language
    new_doc.doc_only_text = get_pure_text(new_doc.doc_raw)

    try:
        # Set language (using provided language engine with confidence=1)
        new_doc.language = {"language": language_engine, "confidence": "1"}
    except Exception as e:
        logging.warning(f"Language detection failed for document {doc_id}: {str(e)}")
        new_doc.language = {"language": "not_found", "confidence": "0"}

    # Check if language is supported
    if new_doc.language.get("language") not in APP_LANGUAGES:
        logging.warning(
            f"Document {doc_id} language {new_doc.language.get('language')} "
            f"not included in supported languages"
        )
        return None

    return new_doc


def _extract_text_content(
    new_doc: classification_doc | classification_doc_v2, mime_type: str
) -> bool:
    """Extract text from document based on mime type. Returns False if mime type not supported."""
    if mime_type == "text/html":
        new_doc.doc_raw = get_text(new_doc.request_raw, config)
        return True
    elif mime_type == "text/plain":
        new_doc.doc_raw = new_doc.request_raw
        return True
    else:
        return False


def filter_pii_scores(
    doc: Any, score_th: float = 0.6, remove_duplicates: bool = False
) -> Any:
    """
    Filter PII hits based on threshold score and optionally remove duplicates

    Args:
        doc: Document with PII hits
        score_th: Score threshold
        remove_duplicates: Whether to remove duplicate hits

    Returns:
        Document with filtered PII hits
    """
    analysis = doc.pii_hits.get("analyses", [{}])
    if not analysis:
        doc.pii_hits = []
        return doc

    filtered_scores = []

    # Create dictionary with unique hits with maximum score if removing duplicates
    hits = {}
    if remove_duplicates:
        for a in analysis[0].get("analysis", []):
            start, end = a.get("start", 0), a.get("end", 0)
            key = f"{start}:{end}"

            if key not in hits or a.get("score", 0) > hits[key]:
                hits[key] = a.get("score", 0)

    # Filter and process hits
    for a in analysis[0].get("analysis", []):
        start, end = a.get("start", 0), a.get("end", 0)
        score = a.get("score", 0)
        key = f"{start}:{end}"

        include_hit = True
        if remove_duplicates:
            # Only include if score is above threshold and it's the highest-scoring duplicate
            include_hit = score > score_th and score >= hits.get(key, 0)

        if include_hit or not remove_duplicates:
            # Add text to PII entity
            texto = doc.doc_raw[start:end].strip()
            a["pii_text"] = texto.encode().decode("utf-8")
            filtered_scores.append(a)

    doc.pii_hits = filtered_scores
    return doc


def update_doc_classification(doc: Any) -> Any:
    """
    Update document with document-level PII information

    Args:
        doc: Document to update

    Returns:
        Updated document
    """
    analysis = doc.pii_hits.get("analyses", [{}])[0]

    # Update GDPR risk scores
    doc.risk_score_mean_gdpr = analysis.get("risk_score_gdpr_mean", 0)
    doc.risk_score_mode_gdpr = doc.pii_hits.get("risk_score_mode_gdpr", 0)
    doc.risk_score_median_gdpr = doc.pii_hits.get("risk_score_median_gdpr", 0)
    doc.risk_score_standard_deviation_gdpr = doc.pii_hits.get(
        "risk_score_standard_deviation_gdpr", 0
    )
    doc.risk_score_variance_gdpr = doc.pii_hits.get("risk_score_variance_gdpr", 0)

    # Update PII risk scores
    doc.risk_score_mean_pii = analysis.get("risk_score_pii_mean", 0)
    doc.risk_score_mode_pii = doc.pii_hits.get("risk_score_mode_pii", 0)
    doc.risk_score_median_pii = doc.pii_hits.get("risk_score_median_pii", 0)
    doc.risk_score_standard_deviation_pii = doc.pii_hits.get(
        "risk_score_standard_deviation_pii", 0
    )
    doc.risk_score_variance_pii = doc.pii_hits.get("risk_score_variance_pii", 0)

    # Update detection information
    doc.sanitized_text = analysis.get("sanitized_text", "")
    doc.detection_count = doc.pii_hits.get("detection_count", 0)
    doc.detected_pii_types = doc.pii_hits.get("detected_pii_types", [])
    doc.detected_pii_type_frequencies = doc.pii_hits.get(
        "detected_pii_type_frequencies", {}
    )

    return doc


def update_object(
    file: Dict[str, Any],
    doc: Any,
    pii_entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Update document dictionary with PII analysis results

    Args:
        file: Dictionary to update
        doc: Document with PII information
        pii_entities: List of PII entities

    Returns:
        Updated dictionary
    """
    # Add PII entities
    file["entities"] = pii_entities

    # Add GDPR risk scores
    file["risk_score_mean_gdpr"] = int(doc.risk_score_mean_gdpr)
    file["risk_score_mode_gdpr"] = int(doc.risk_score_mode_gdpr)
    file["risk_score_median_gdpr"] = int(doc.risk_score_median_gdpr)
    file["risk_score_standard_deviation_gdpr"] = float(
        doc.risk_score_standard_deviation_gdpr
    )
    file["risk_score_variance_gdpr"] = float(doc.risk_score_variance_gdpr)

    # Add PII risk scores
    file["risk_score_mean_pii"] = int(doc.risk_score_mean_pii)
    file["risk_score_mode_pii"] = int(doc.risk_score_mode_pii)
    file["risk_score_median_pii"] = int(doc.risk_score_median_pii)
    file["risk_score_standard_deviation_pii"] = float(
        doc.risk_score_standard_deviation_pii
    )
    file["risk_score_variance_pii"] = float(doc.risk_score_variance_pii)

    # Add detection information
    file["detection_count"] = int(doc.detection_count)
    file["detected_pii_types"] = doc.detected_pii_types
    file["detected_pii_type_frequencies"] = doc.detected_pii_type_frequencies
    file["sanitized_text"] = doc.sanitized_text

    return file


#### Merge Output


def split_document(text: str, chunk_size: int) -> List[str]:
    """
    Split a document into manageable chunks

    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk

    Returns:
        List of text chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=0,
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
    )

    return text_splitter.split_text(text)


def sum_values_dict(dict1: Dict[str, int], dict2: Dict[str, int]) -> Dict[str, int]:
    """
    Sum values of two dictionaries by key

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        New dictionary with summed values
    """
    result = dict1.copy()
    for key, value in dict2.items():
        result[key] = result.get(key, 0) + value
    return result


# mean aggregated int flavor
def mean_aggregated(val1: int, val2: int) -> int:
    """
    Calculate mean of two integer values

    Args:
        val1: First value
        val2: Second value

    Returns:
        Mean value as integer
    """
    return (
        (val1 + val2) // 2
        if val1 is not None and val2 is not None
        else val1 or val2 or 0
    )


# mean aggregated float flavor
def mean_aggregated_float(val1: float, val2: float) -> float:
    """
    Calculate mean of two float values

    Args:
        val1: First value
        val2: Second value

    Returns:
        Mean value as float
    """
    return (
        (val1 + val2) / 2
        if val1 is not None and val2 is not None
        else val1 or val2 or 0.0
    )


def merge_entities(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge individual outputs of entity recognitions

    Args:
        docs: List of dictionaries with risk scoring model output

    Returns:
        Merged output dictionary
    """
    if not docs:
        return {}

    # Initialize output with first document
    output = {
        # Document metadata - take from first document only
        "language": docs[0].get("language", ""),
        "file_name": docs[0].get("file_name", ""),
        "file_type": docs[0].get("file_type", ""),
        "document_id": docs[0].get("document_id", ""),
        "file_uri": docs[0].get("file_uri", ""),
        # Initialize metrics
        "detection_count": docs[0].get("detection_count", 0),
        "detected_pii_types": set(docs[0].get("detected_pii_types", [])),
        "detected_pii_type_frequencies": docs[0].get(
            "detected_pii_type_frequencies", {}
        ),
        # GDPR scores
        "risk_score_mean_gdpr": docs[0].get("risk_score_mean_gdpr", 0),
        "risk_score_mode_gdpr": docs[0].get("risk_score_mode_gdpr", 0),
        "risk_score_median_gdpr": docs[0].get("risk_score_median_gdpr", 0),
        "risk_score_standard_deviation_gdpr": docs[0].get(
            "risk_score_standard_deviation_gdpr", 0.0
        ),
        "risk_score_variance_gdpr": docs[0].get("risk_score_variance_gdpr", 0.0),
        # PII scores
        "risk_score_mean_pii": docs[0].get("risk_score_mean_pii", 0),
        "risk_score_mode_pii": docs[0].get("risk_score_mode_pii", 0),
        "risk_score_median_pii": docs[0].get("risk_score_median_pii", 0),
        "risk_score_standard_deviation_pii": docs[0].get(
            "risk_score_standard_deviation_pii", 0.0
        ),
        "risk_score_variance_pii": docs[0].get("risk_score_variance_pii", 0.0),
        # Content
        "sanitized_text": docs[0].get("sanitized_text", ""),
        "entities": docs[0].get("entities", []),
    }

    # Merge data from subsequent documents
    for doc in docs[1:]:
        # Update detection count
        output["detection_count"] += doc.get("detection_count", 0)

        # Merge PII types
        output["detected_pii_types"].update(doc.get("detected_pii_types", []))

        # Merge frequency dictionaries
        output["detected_pii_type_frequencies"] = sum_values_dict(
            output["detected_pii_type_frequencies"],
            doc.get("detected_pii_type_frequencies", {}),
        )

        # Aggregate GDPR scores
        output["risk_score_mean_gdpr"] = mean_aggregated(
            output["risk_score_mean_gdpr"], doc.get("risk_score_mean_gdpr", 0)
        )
        output["risk_score_mode_gdpr"] = mean_aggregated(
            output["risk_score_mode_gdpr"], doc.get("risk_score_mode_gdpr", 0)
        )
        output["risk_score_median_gdpr"] = mean_aggregated(
            output["risk_score_median_gdpr"], doc.get("risk_score_median_gdpr", 0)
        )

        # Aggregate PII scores
        output["risk_score_mean_pii"] = mean_aggregated(
            output["risk_score_mean_pii"], doc.get("risk_score_mean_pii", 0)
        )
        output["risk_score_mode_pii"] = mean_aggregated(
            output["risk_score_mode_pii"], doc.get("risk_score_mode_pii", 0)
        )
        output["risk_score_median_pii"] = mean_aggregated(
            output["risk_score_median_pii"], doc.get("risk_score_median_pii", 0)
        )

        # Aggregate standard deviations and variances
        output["risk_score_standard_deviation_gdpr"] = mean_aggregated_float(
            output["risk_score_standard_deviation_gdpr"],
            doc.get("risk_score_standard_deviation_gdpr", 0.0),
        )
        output["risk_score_variance_gdpr"] = mean_aggregated_float(
            output["risk_score_variance_gdpr"], doc.get("risk_score_variance_gdpr", 0.0)
        )
        output["risk_score_standard_deviation_pii"] = mean_aggregated_float(
            output["risk_score_standard_deviation_pii"],
            doc.get("risk_score_standard_deviation_pii", 0.0),
        )
        output["risk_score_variance_pii"] = mean_aggregated_float(
            output["risk_score_variance_pii"], doc.get("risk_score_variance_pii", 0.0)
        )

        # Concatenate sanitized text
        output["sanitized_text"] += "\n" + doc.get("sanitized_text", "")

        # Extend entities list
        output["entities"].extend(doc.get("entities", []))

    return output


#####
async def get_pii_phi_v2(
    nlp,
    docs_with_languages,
    documents_non_teathred,
    all_stopwords,
    my_stop_words,
    config,
    jobs: dict,
    new_task: Job,
    score: float = 0.4,
    filter_detection: int = 1,
    weights: List = [],
):
    """
    PII analisys batch documents version 2
    Args:
        nlp : NER sPacy model
        docs_with_languages: list of Documents extracted from Elastic obje
        documents_non_teathred,
        all_stopwords,
        my_stop_words,
        config,
        jobs: dict,
        new_task: Job,

        score: float = 0.4,
        weights: List = [],

    """
    chunck = []
    list_anonymized_docs = []
    list_chucks = []
    j = 0
    jobs[new_task.uid].status = "Extracting PII/PHI....."

    for doc in docs_with_languages:
        # Extract text without stopwords
        text = remove_mystopwords_enhanced(doc.doc_raw, all_stopwords, my_stop_words)
        length_text = len(doc.doc_raw)
        if length_text > MAX_LENGTH_PRINT:
            logging.info(f"Document {doc.document_id} has {length_text} characters")

        if len(text) > MINIMUN_CHAR_LENGTH:
            # get language Document. If language not supported we use english
            if doc.language.get("language") in APP_LANGUAGES:
                lang = doc.language.get("language")
            else:
                print(
                    f"Document {doc.document_id} language {doc.language.get('language')} not supported. We use English"
                )
                lang = "en"
            # PII / PHI analisys.
            if length_text > CHUNK_LENGTH:
                splitted_docs = split_document(doc.doc_raw, chunk_size=CHUNK_LENGTH)
                logging.info(f"Splitted document into {len(splitted_docs)} chuncks")
            else:
                splitted_docs = [doc.doc_raw]
            # use a copy of the original doc
            copy_doc = copy.deepcopy(doc)
            for d in splitted_docs:
                logging.info(f"Analizing document chunck of length {len(d)}")
                # extract PII come already a dictionary

                analysis_results = await extract_pii_from_text_url(
                    lang=lang,
                    score=score,
                    text=d,
                    weights=weights,
                    config=config,
                    filter_detection=filter_detection,
                )

                copy_doc.pii_hits = analysis_results
                # Update document with attributes document Level
                copy_doc = update_doc_classification(copy_doc)
                # filter scores by default all returned by the tool are included. score_threshold = 0 and not remove duplicates
                copy_doc = filter_pii_scores(
                    copy_doc, score_th=0, remove_duplicates=False
                )

                # save to local
                # text_to_anonymize = copy_doc.doc_raw
                # split_text = list(text_to_anonymize)
                doc_dict = copy_doc.dict(
                    exclude={"doc_raw", "request_raw", "doc_only_text", "index"}
                )

                # get PII/PHI hits
                hits = doc_dict.get("pii_hits")
                # remove hits from dictionary
                del doc_dict["pii_hits"]
                # serialize and post hits from this document
                pii_entities = []
                for ele, i in zip(hits, range(len(hits))):
                    new_file = ele.copy()
                    new_file = {
                        key.replace('"', ""): val for key, val in new_file.items()
                    }

                    # Post processing cleaning
                    status = post_processing(new_file, nlp)
                    if status == 2:
                        continue

                    pii_entities.append(new_file)
                # file name individual hits
                file = doc_dict.copy()
                file = update_object(file, copy_doc, pii_entities)

                list_chucks.append(file)
            # merge output of individual chunks

            file = merge_entities(list_chucks)
            # name_json = doc.document_id + ".json"
            # replace  slash with _ BUG 5783
            # DISABLED
            # name_json = name_json.replace("/", "_")
            # json_file = os.path.join("output", name_json)
            # logging.info(json_file)
            # try:
            #     async with aiofiles.open(json_file, "w") as f:
            #         file1 = json.dumps(jsonable_encoder(file), cls=NpEncoder, indent=4)
            #         await f.write(file1)
            # except:
            #     raise Exception(f"Error writing file {json_file}")

            # update jobs
            logging.info(f"Document {doc.document_id}.Number of entities processed {j}")
            jobs[new_task.uid].status = (
                f"Extracting PII/PHI.- number of entities processed {j}"
            )
            j += 1

            chunck.append(file)
            list_chucks = []
        else:
            # if no valid text , document id to documents_non_teathred
            logging.warning(
                f"Document {doc.document_id}.No Enought text to process document"
            )
            documents_non_teathred.append(
                {doc.document_id: "No Enought text to process document"}
            )

    return chunck, list_anonymized_docs, documents_non_teathred


async def get_pii_phi_v2_no_proxy(
    nlp: spacy.language.Language,
    docs_with_languages: List[Any],
    documents_non_teathred: List[Dict[str, str]],
    all_stopwords: Set[str],
    my_stop_words: List[str],
    pii_mapper: Any,
    pii_analysys_engine: Any,
    jobs: Dict[str, Job],
    new_task: Job,
    score: float = 0.4,
    filter_detection: int = 1,
    language_engine: str = "en",
) -> Tuple[List[Dict], List[Dict], List[Dict[str, str]]]:
    """
    PII analysis for batch documents - version 2

    Args:
        nlp: NER spaCy model
        docs_with_languages: List of documents extracted from Elastic object
        documents_non_teathred: List of documents that couldn't be processed
        all_stopwords: Set of stopwords to filter out
        my_stop_words: Additional stopwords to filter out
        config: Configuration dictionary
        pii_mapper: PII mapping utility
        pii_analysys_engine: PII analysis service
        jobs: Dictionary of jobs
        new_task: Current job being processed
        score: Minimum score threshold (default: 0.4)
        filter_detection: Whether to filter detections (default: 1)
        weights: List of weights for PII types (default: None)
        language_engine: Language code (default: "en")

    Returns:
        Tuple containing processed chunks, anonymized docs, and non-processed docs
    """

    chunck = []
    list_anonymized_docs = []
    jobs[new_task.uid].status = "Extracting PII/PHI....."

    # Update PII mapper references in analysis engine
    _update_pii_mapper_references(pii_analysys_engine, pii_mapper)

    for doc in docs_with_languages:
        # Process document if it has sufficient text
        if await _process_document(
            doc=doc,
            nlp=nlp,
            all_stopwords=all_stopwords,
            my_stop_words=my_stop_words,
            pii_analysys_engine=pii_analysys_engine,
            language_engine=language_engine,
            score=score,
            filter_detection=filter_detection,
            jobs=jobs,
            new_task=new_task,
            chunck=chunck,
            documents_non_teathred=documents_non_teathred,
        ):
            jobs[new_task.uid].status = (
                f"Extracting PII/PHI - processing document {doc.document_id}"
            )

    return chunck, list_anonymized_docs, documents_non_teathred


def _update_pii_mapper_references(pii_analysys_engine: Any, pii_mapper: Any) -> None:
    """Update PII mapper references in the analysis engine components"""
    pii_analysys_engine.pii_mapper = pii_mapper
    pii_analysys_engine._pii_assessment_service.pii_mapper = pii_mapper
    pii_analysys_engine._analyzer.pii_mapper = pii_mapper


async def _process_document(
    doc: Any,
    nlp: spacy.language.Language,
    all_stopwords: Set[str],
    my_stop_words: List[str],
    pii_analysys_engine: Any,
    language_engine: str,
    score: float,
    filter_detection: int,
    jobs: Dict[str, Job],
    new_task: Job,
    chunck: List[Dict],
    documents_non_teathred: List[Dict[str, str]],
) -> bool:
    """Process a single document for PII extraction"""
    # Extract text without stopwords
    text = remove_mystopwords_enhanced(doc.doc_raw, all_stopwords, my_stop_words)
    length_text = len(doc.doc_raw)

    if length_text > MAX_LENGTH_PRINT:
        logging.info(f"Document {doc.document_id} has {length_text} characters")

    if len(text) <= MINIMUN_CHAR_LENGTH:
        logging.warning(
            f"Document {doc.document_id}: Not enough text to process document"
        )
        documents_non_teathred.append(
            {doc.document_id: "Not enough text to process document"}
        )
        return False

    # Determine document language
    lang = language_engine if language_engine in APP_LANGUAGES else "en"
    if lang != language_engine:
        logging.warning(
            f"Document {doc.document_id} language {language_engine} not supported. Using English."
        )

    # Split document if needed
    splitted_docs = (
        split_document(doc.doc_raw, chunk_size=CHUNK_LENGTH)
        if length_text > CHUNK_LENGTH
        else [doc.doc_raw]
    )
    if length_text > CHUNK_LENGTH:
        logging.info(f"Split document into {len(splitted_docs)} chunks")

    # Process each chunk
    processed_chunks = await _process_document_chunks(
        doc=doc,
        splitted_docs=splitted_docs,
        pii_analysys_engine=pii_analysys_engine,
        lang=lang,
        score=score,
        filter_detection=filter_detection,
        nlp=nlp,
    )

    if processed_chunks:
        # Merge all chunks into a single result
        merged_result = merge_entities(processed_chunks)
        chunck.append(merged_result)
        return True
    return False


async def _process_document_chunks(
    doc: Any,
    splitted_docs: List[str],
    pii_analysys_engine: Any,
    lang: str,
    score: float,
    filter_detection: int,
    nlp: spacy.language.Language,
) -> List[Dict]:
    """Process each chunk of a document and return the results"""
    list_chunks = []

    # Create a copy of the original doc to avoid modifying it
    copy_doc = copy.deepcopy(doc)

    for chunk_text in splitted_docs:
        logging.info(f"Analyzing document chunk of length {len(chunk_text)}")

        # Extract PII from text
        analysis_results = await extract_pii_from_text(
            pii_analysys=pii_analysys_engine,
            lang=lang,
            score=score,
            text=chunk_text,
            filter_detection=filter_detection,
        )

        # Update document with PII hits and classification
        copy_doc.pii_hits = analysis_results
        copy_doc = update_doc_classification(copy_doc)
        copy_doc = filter_pii_scores(copy_doc, score_th=0, remove_duplicates=False)

        # Convert document to dictionary format for output
        doc_dict = copy_doc.model_dump(
            exclude={"doc_raw", "request_raw", "doc_only_text", "index"}
        )

        # Process PII hits
        hits = doc_dict.get("pii_hits", [])
        del doc_dict["pii_hits"]

        # Process individual PII entities
        pii_entities = _process_pii_entities(hits, copy_doc.doc_raw, nlp)

        # Update and store the document
        file = update_object(doc_dict.copy(), copy_doc, pii_entities)
        list_chunks.append(file)

    return list_chunks


def _process_pii_entities(
    hits: List[Dict], doc_raw: str, nlp: spacy.language.Language
) -> List[Dict]:
    """Process PII entity hits and apply post-processing filters"""
    pii_entities = []

    for hit in hits:
        # Make a copy to avoid modifying the original
        new_entity = hit.copy()
        new_entity = {key.replace('"', ""): val for key, val in new_entity.items()}

        # Post-processing filtering
        if post_processing(new_entity, nlp) != 2:  # Status 2 means skip this entity
            pii_entities.append(new_entity)

    return pii_entities


async def get_pii_phi(
    pii_analysys_dict,
    nlp,
    docs_with_languages,
    documents_non_teathred,
    all_stopwords,
    my_stop_words,
    jobs: dict,
    new_task: Job,
    anonymize: bool = False,
    pii_mapper=None,
    score: float = 0.4,
    filter_detection: bool = True,
):
    chunck = []
    list_anonymized_docs = []

    j = 0
    jobs[new_task.uid].status = "Extracting PII/PHI....."

    for doc in docs_with_languages:
        text = remove_mystopwords_enhanced(doc.doc_raw, all_stopwords, my_stop_words)
        if len(text) > MINIMUN_CHAR_LENGTH:
            if doc.language == "es":
                lang = doc.language
                pii_analysys = pii_analysys_dict.get("es")
            elif doc.language == "de":
                lang = doc.language
                pii_analysys = pii_analysys_dict.get("de")
            else:
                lang = "en"
                pii_analysys = pii_analysys_dict.get("en")

            # definitive Mapper
            pii_analysys.pii_mapper = pii_mapper
            pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
            pii_analysys._analyzer.pii_mapper = pii_mapper

            # extract PII
            analysis_results = await extract_pii_from_text(
                pii_analysys=pii_analysys,
                lang=lang,
                score=score,
                text=doc.doc_raw,
                filter_detection=filter_detection,
            )

            doc.pii_hits = analysis_results
            # filter scores by default all returned by the tool are included. score_threshold = 0 and not remove duplicates
            doc = filter_pii_scores(doc, score_th=0, remove_duplicates=False)
            # save to local
            doc_dict = doc.dict(
                exclude={"doc_raw", "request_raw", "doc_only_text", "index"}
            )

            # save to local
            text_to_anonymize = doc.doc_raw
            split_text = list(text_to_anonymize)
            # get PII/PHI hits
            hits = doc_dict.get("pii_hits")
            # remove hits from dictionary
            del doc_dict["pii_hits"]
            # serialize and post hits from this document
            for ele, i in zip(hits, range(len(hits))):
                new_file = doc_dict.copy()
                new_file.update(ele)
                new_file = {key.replace('"', ""): val for key, val in new_file.items()}
                # anonymize doc
                if anonymize:
                    start = new_file.get("start")
                    end = new_file.get("end")
                    split_text[int(start)] = "[REDACTED]"
                    for i in range(int(start) + 1, int(end)):
                        split_text[i] = ""

                # Post processing cleaning
                status = post_processing(new_file, nlp)
                if status == 2:
                    continue

                # file name individual hits
                name_json = doc.scan_id + f"_{i}" + ".json"
                # replace  slash with _ BUG 5783
                name_json = name_json.replace("/", "_")
                json_file = os.path.join("output", name_json)
                print(json_file)

                try:
                    async with aiofiles.open(json_file, "w") as f:
                        file = json.dumps(
                            jsonable_encoder(new_file), cls=NpEncoder, indent=4
                        )
                        await f.write(file)
                except Exception as e:
                    raise AttributeError(
                        f"Error writing file {json_file}. Exception: {e}"
                    )

            chunck.append(new_file)
            j += 1
            if anonymize:
                text_to_anonymize = "".join(split_text)
                list_anonymized_docs.append(text_to_anonymize)
        else:
            documents_non_teathred.append(
                {doc.scan_id: "No Enought text to process document"}
            )

    return chunck, list_anonymized_docs, documents_non_teathred


def anonymize(text_to_anonymize, chunck):
    """
    Anonymize text
    """
    split_text = list(text_to_anonymize)
    for ent in chunck:
        start = ent.get("start")
        end = ent.get("end")
        split_text[int(start)] = "[REDACTED]"
        for i in range(int(start) + 1, int(end)):
            split_text[i] = ""
    return "".join(split_text)


async def extract_pii_from_text(
    pii_analysys: Any, lang: str, score: float, text: str, filter_detection: bool = True
) -> Dict:
    """
    Extract PII/PHI from text using the PII analysis service

    Args:
        pii_analysys: PII analysis service
        lang: Language code
        score: Minimum score threshold
        text: Text to analyze
        filter_detection: Whether to filter detections

    Returns:
        Dictionary of analysis results
    """
    analysis_results = pii_analysys.analyze_collection(
        texts=[text],
        language_code=lang,
        collection_type="population",
        collection_name="PII Collection 1",
        score_threshold=score,
        filter_detection=filter_detection,
    )

    return analysis_results.to_dict()


async def extract_pii_from_text_url(
    lang: str,
    score: float,
    text: str,
    weights: List = [],
    config: Dict = {},
    filter_detection: int = 1,
):
    """
    request to Analisys engine based on language
    Args:
        lang: str --> Language
        score: float --> Analisys Engine score
        text: str --> text to analyse
        weights: List --> Weights to use in Risk model
        lang: str --> Language
    """

    data = {}
    data["text"] = text
    data["lang"] = lang
    data["score"] = score
    data["weights"] = weights
    data["filter_detection"] = filter_detection

    data1 = json.dumps(data).encode()
    # get URL from config
    url = config.get(lang)
    r = {}
    try:
        # async with aiohttp.ClientSession() as session:
        r = requests.post(url, data=data1)  # files=files)
    except Exception as e:
        out = index_response()
        r = print_stack(out)
        logging.error(r.get("error"))

    return r.json()
