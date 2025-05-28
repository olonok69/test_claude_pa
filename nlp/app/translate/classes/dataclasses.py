import pydantic
from datetime import datetime, timedelta
from pydantic.json import timedelta_isoformat

import orjson

import json
import numpy as np
from datetime import date, datetime, timedelta


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


class pii_doc(pydantic.BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    doc_raw: str = ""  # raw document after html parsing
    doc_only_text: str = ""  # raw document without special chars and numbers
    request_raw: str = ""  # raw document coming from Elasticsearch content tag
    language: str = "en"  # default language document
    pii_hits: dict = {}  # PII entities recognized
    file_name: str = ""  # file name from Elastic Search
    file_type: str = ""  # file type from Elastic Search
    scan_id: str = ""  # id from Elastic Search
    file_uri: str = ""  # uri from Elastic search
    index: str = ""  # index where this file is located
    embedding: list[float] = []  # embeddings model after encode model transformers
    classification_labels: dict = {}
    keywords: dict = {}
    toxic_labels: dict = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class classification_doc(pydantic.BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    doc_raw: str = ""  # raw document after html parsing
    doc_only_text: str = ""  # raw document without special chars and numbers
    request_raw: str = ""  # raw document coming from Elasticsearch content tag
    language: str = "en"  # default language document
    pii_hits: dict = {}  # PII entities recognized
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
        json_loads = orjson.loads
        json_dumps = orjson_dumps
