import pydantic
from datetime import datetime, timedelta
from pydantic.json import timedelta_isoformat
from uuid import UUID, uuid4
from pydantic import Field
import orjson
from typing import Union, List, Set, Dict, Tuple, Optional

import json
import numpy as np
from datetime import date, datetime, timedelta


class Job(pydantic.BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    type_job: str = ""


def myconverter(obj):
    """
    HELPER TRANSFORM DICTIONARIES TO JSON
    """
    if isinstance(obj, np.string_):
        return str(obj)
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime.datetime):
        return obj.__str__()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.floating, np.complexfloating)):
        return float(obj)
    elif isinstance(obj, np.int32):
        return int(obj)
    elif isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.generic):
        return obj.item()


class NpEncoder(json.JSONEncoder):
    """
    Class to handle encoding datat types for compatibility with json dump
    """

    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.floating, np.complexfloating)):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.int32):
            return int(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.string_):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return str(obj)
        return super(NpEncoder, self).default(obj)


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class index_response(pydantic.BaseModel):
    status: Dict = {}  # status code and message
    data: Optional[Union[dict, List]] = None
    error: str = ""
    number_documents_treated: int = 0
    number_documents_non_treated: int = 0
    list_id_not_treated: List = []


class pii_doc(pydantic.BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    doc_raw: str = ""  # raw document after html parsing
    doc_only_text: str = ""  # raw document without special chars and numbers
    request_raw: str = ""  # raw document coming from Elasticsearch content tag
    language: str = "en"  # default language document
    pii_hits: Dict = {}  # PII entities recognized
    file_name: str = ""  # file name from Elastic Search
    file_type: str = ""  # file type from Elastic Search
    scan_id: str = ""  # id from Elastic Search
    file_uri: str = ""  # uri from Elastic search
    index: str = ""  # index where this file is located
    embedding: List[float] = []  # embeddings model after encode model transformers
    classification_labels: Dict = {}
    keywords: Dict = {}
    toxic_labels: Dict = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }


class redacted_doc(pydantic.BaseModel):
    redacted_text: str = ""  # raw document without special chars and numbers

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }


class classification_doc(pydantic.BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    doc_raw: str = ""  # raw document after html parsing
    doc_only_text: str = ""  # raw document without special chars and numbers
    request_raw: str = ""  # raw document coming from Elasticsearch content tag
    language: str = "en"  # default language document
    pii_hits: Dict = {}  # PII entities recognized
    file_name: str = ""  # file name from Elastic Search
    file_type: str = ""  # file type from Elastic Search
    scan_id: str = ""  # id from Elastic Search
    file_uri: str = ""  # uri from Elastic search
    index: str = ""  # index where this file is located

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }


class classification_doc_v2(pydantic.BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    doc_raw: str = ""  # raw document after html parsing
    doc_only_text: str = ""  # raw document without special chars and numbers
    request_raw: str = ""  # raw document coming from Elasticsearch content tag
    language: Union[str, Dict] = {
        "language": "en",
        "confidence": 1.0,
    }  # default language document
    pii_hits: Union[List[Dict], Dict] = []  # PII entities recognized
    detection_count: int = 0
    detected_pii_types: Union[Set[str], List[str]] = []
    detected_pii_type_frequencies: Dict = {}  # type: ignore
    risk_score_mean_gdpr: float = 1.0  # Default is 1 for non-identifiable
    risk_score_mode_gdpr: float = 0.0
    risk_score_median_gdpr: float = 0.0
    risk_score_standard_deviation_gdpr: float = 0.0
    risk_score_variance_gdpr: float = 0.0
    risk_score_mean_pii: float = 1.0  # Default is 1 for non-identifiable
    risk_score_mode_pii: float = 0.0
    risk_score_median_pii: float = 0.0
    risk_score_standard_deviation_pii: float = 0.0
    risk_score_variance_pii: float = 0.0
    sanitized_text: str = ""  #  Sanitized text
    file_name: str = ""  # file name from Elastic Search
    file_type: str = ""  # file type from Elastic Search
    document_id: str = ""  # id from Elastic Search
    file_uri: str = ""  # uri from Elastic search
    index: str = ""  # index where this file is located

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }


class rot_conf(pydantic.BaseModel):
    """ "
    Data Class ROT Configuration
    """

    redundant: Dict = {}
    obsolete: Dict = {}
    trivial: Dict = {}
