# FROM PII CONFIG

MAX_LENGTH = 1000000
CHUNK_LENGTH = 499999
MAX_LENGTH_PRINT = 1000000
version = "v2"
file_v1 = "pii_type_mappings"
file_v2 = "pii_gdpr_mapping"


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

# ANalisys ENgines Constants

REMOVE_RECOGNIZERS_EN = [
    "InPanRecognizer",
    "InAadhaarRecognizer",
    "InVehicleRegistrationRecognizer",
    "InVoterRecognizer",
    "InPassportRecognizer",
    "SgFinRecognizer",
]

LABELS_TO_IGNORE_EN = ["MISC", "FAC"]
REMOVE_RECOGNIZERS_ES = [
    "InPanRecognizer",
    "InAadhaarRecognizer",
    "InVehicleRegistrationRecognizer",
    "InVoterRecognizer",
    "InPassportRecognizer",
    "SgFinRecognizer",
    "UsBankRecognizer",
    "UsLicenseRecognizer",
    "UsItinRecognizer",
    "UsPassportRecognizer",
    "UsSsnRecognizer",
    "UsSsnRecognizer",
    "AuAbnRecognizer",
    "AuAcnRecognizer",
    "AuMedicareRecognizer",
    "AuTfnRecognizer",
    "NhsRecognizer",
]

LABELS_TO_IGNORE_ES = ["MISC"]

REMOVE_RECOGNIZERS_DE = [
    "InPanRecognizer",
    "InAadhaarRecognizer",
    "InVehicleRegistrationRecognizer",
    "InVoterRecognizer",
    "InPassportRecognizer",
    "SgFinRecognizer",
    "UsBankRecognizer",
    "UsLicenseRecognizer",
    "UsItinRecognizer",
    "UsPassportRecognizer",
    "UsSsnRecognizer",
    "UsSsnRecognizer",
    "AuAbnRecognizer",
    "AuAcnRecognizer",
    "AuMedicareRecognizer",
    "AuTfnRecognizer",
    "NhsRecognizer",
]
LABELS_TO_IGNORE_DE = ["MISC"]
REMOVE_RECOGNIZERS_IT = [
    "InPanRecognizer",
    "InAadhaarRecognizer",
    "InVehicleRegistrationRecognizer",
    "InVoterRecognizer",
    "InPassportRecognizer",
    "SgFinRecognizer",
    "UsBankRecognizer",
    "UsLicenseRecognizer",
    "UsItinRecognizer",
    "UsPassportRecognizer",
    "UsSsnRecognizer",
    "UsSsnRecognizer",
    "AuAbnRecognizer",
    "AuAcnRecognizer",
    "AuMedicareRecognizer",
    "AuTfnRecognizer",
    "NhsRecognizer",
]
LABELS_TO_IGNORE_IT = ["MISC"]
