from pydantic import BaseModel
from typing import Union, List, Dict, Optional

from pydantic_settings import BaseSettings


class Index_Response(BaseModel):
    """
    this class contains the response from the NSFW Model
    """

    status: Dict = {}  # status code and message
    data: Optional[Union[dict, List]] = None  # Data extracted from the OCR process
    error: str = ""  # Error message
    number_documents_treated: int = 0  # Number of documents treated
    number_documents_non_treated: int = 0  # Number of documents not treated
    list_id_not_treated: List = []  # List of documents not treated
    memory_used: str = ""  # Memory used in the process
    ram_used: str = ""  # RAM used in the process


class Elastic_Data(BaseModel):
    id: str
    index: str
    source: Dict[str, Union[str, Dict[str, Dict[str, Union[float, str]]]]]


class OCR_Request(BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    documents: List[Elastic_Data]  # List of Dictionaries from Elastic
    cypher: Optional[int]  # If the content it is encripted or not


class Settings(BaseSettings):
    """
    this class contains the settings for the OCR process
    """

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NoN Safe for Work API"
