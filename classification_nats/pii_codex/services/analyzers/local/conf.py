from presidio_anonymizer.entities import OperatorConfig
from ....config import (
    DEFAULT_TOKEN_REPLACEMENT_VALUE,
)

operators = {
    "DEFAULT": OperatorConfig(
        "replace", {"new_value": DEFAULT_TOKEN_REPLACEMENT_VALUE}
    ),
    "AGE": OperatorConfig("replace", {"new_value": "AGE"}),
    "ABA_ROUTING_NUMBER": OperatorConfig(
        "replace", {"new_value": "ABA_ROUTING_NUMBER"}
    ),
    "AU_ABN": OperatorConfig("replace", {"new_value": "AU_ABN"}),
    "AU_ACN": OperatorConfig("replace", {"new_value": "AU_ACN"}),
    "AU_MEDICARE": OperatorConfig("replace", {"new_value": "AU_MEDICARE"}),
    "DATE": OperatorConfig("replace", {"new_value": "DATE"}),
    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "CREDIT_CARD"}),
    "CRYPTO": OperatorConfig("replace", {"new_value": "CRYPTO"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "DATE_TIME"}),
    "US_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "US_DRIVER_LICENSE"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "EMAIL_ADDRESS"}),
    "GENDER": OperatorConfig("replace", {"new_value": "GENDER"}),
    "DE_ID_NUMBER": OperatorConfig("replace", {"new_value": "DE_ID_NUMBER"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "LOCATION"}),
    "HEALTH_INSURANCE_ID": OperatorConfig(
        "replace", {"new_value": "HEALTH_INSURANCE_ID"}
    ),
    "HEIGHT": OperatorConfig("replace", {"new_value": "HEIGHT"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "PHONE_NUMBER"}),
    "IBAN_CODE": OperatorConfig("replace", {"new_value": "IBAN_CODE"}),
    "IP_ADDRESS": OperatorConfig("replace", {"new_value": "IP_ADDRESS"}),
    "JOB_TITLE": OperatorConfig("replace", {"new_value": "JOB_TITLE"}),
    "MARITAL_STATUS": OperatorConfig("replace", {"new_value": "MARITAL_STATUS"}),
    "MEDICAL_LICENSE": OperatorConfig("replace", {"new_value": "MEDICAL_LICENSE"}),
    "NRP": OperatorConfig("replace", {"new_value": "NRP"}),
    "OCCUPATION": OperatorConfig("replace", {"new_value": "OCCUPATION"}),
    "US_PASSPORT": OperatorConfig("replace", {"new_value": "US_PASSPORT"}),
    "PERSON": OperatorConfig("replace", {"new_value": "PERSON"}),
    "RACE": OperatorConfig("replace", {"new_value": "RACE"}),
    "SEXUAL_PREFERENCE": OperatorConfig("replace", {"new_value": "SEXUAL_PREFERENCE"}),
    "SOCIAL_NETWORK_PROFILE": OperatorConfig(
        "replace", {"new_value": "SOCIAL_NETWORK_PROFILE"}
    ),
    "ES_NIF": OperatorConfig("replace", {"new_value": "ES_NIF"}),
    "ES_NIE": OperatorConfig("replace", {"new_value": "ES_NIE"}),
    "SWIFT_CODE": OperatorConfig("replace", {"new_value": "SWIFT_CODE"}),
    "AU_TFN": OperatorConfig("replace", {"new_value": "AU_TFN"}),
    "TITLE": OperatorConfig("replace", {"new_value": "TITLE"}),
    "UK_NHS": OperatorConfig("replace", {"new_value": "UK_NHS"}),
    "US_BANK_NUMBER": OperatorConfig("replace", {"new_value": "US_BANK_NUMBER"}),
    "US_ITIN": OperatorConfig("replace", {"new_value": "US_ITIN"}),
    "URL": OperatorConfig("replace", {"new_value": "URL"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "US_SSN"}),
    "WEIGHT": OperatorConfig("replace", {"new_value": "WEIGHT"}),
    "ZIPCODE": OperatorConfig("replace", {"new_value": "ZIPCODE"}),
    "TITLE_EN": OperatorConfig("replace", {"new_value": "TITLE_EN"}),
    "IT_FISCAL_CODE": OperatorConfig("replace", {"new_value": "IT_FISCAL_CODE"}),
    "IT_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "IT_DRIVER_LICENSE"}),
    "IT_VAT_CODE": OperatorConfig("replace", {"new_value": "IT_VAT_CODE"}),
    "IT_PASSPORT": OperatorConfig("replace", {"new_value": "IT_PASSPORT"}),
    "IT_IDENTITY_CARD": OperatorConfig("replace", {"new_value": "IT_IDENTITY_CARD"}),
}

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
