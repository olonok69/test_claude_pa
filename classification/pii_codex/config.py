from .utils.pii_mapping_util import PIIMapper
import os

# application languages supported
GLOBAL_DOCUMENT_MIN_SCORE = 0.01
FILTER_DETECTION = 1
# When we move the app outside American Market we can include german and Italian, with others APP_LANGUAGES = ["en", "it", "de", "es"]
APP_LANGUAGES = ["en", "es"]

MAX_LENGTH = 1000000
CHUNK_LENGTH = 499999
MAX_LENGTH_PRINT = 1000000
version = "v2"
file_v1 = "pii_type_mappings"
file_v2 = "pii_gdpr_mapping"


# RISK MODEL VERSION and PII MAPPER version
if int(os.environ.get("IS_TEST", "0")) == 1:
    version = "v1"
else:
    version = "v2"

if version == "v1":
    mapping_file_name = file_v1
elif version == "v2":
    mapping_file_name = file_v2

PII_MAPPER = PIIMapper(version=version, mapping_file_name=mapping_file_name)

DEFAULT_LANG = "en"
DEFAULT_ANALYSIS_MODE = "POPULATION"
DEFAULT_TOKEN_REPLACEMENT_VALUE = "<REDACTED>"
# Spanish
SUPPORTED_LANGUAGES_EN = ["en"]
NLP_CONFIGURATION_EN = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_lg"},
    ],
}
# Spanish
SUPPORTED_LANGUAGES_ES = ["es", "en"]
NLP_CONFIGURATION_ES = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "es", "model_name": "es_core_news_lg"},
    ],
}
# German
SUPPORTED_LANGUAGES_DE = ["de", "en"]
NLP_CONFIGURATION_DE = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "de", "model_name": "de_core_news_lg"},
    ],
}
# ITALIAN
SUPPORTED_LANGUAGES_IT = ["it", "en"]
NLP_CONFIGURATION_IT = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "it", "model_name": "it_core_news_lg"},
    ],
}
