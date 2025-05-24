from __future__ import annotations

from enum import Enum

# All listed PII Types from Milne et al (2018) and a few others along with
# models used for PII categorization for DHS, NIST, and HIPAA


class AnalysisProviderType(Enum):
    AZURE: str = "AZURE"
    AWS: str = "AWS"
    PRESIDIO: str = "PRESIDIO"


class RiskLevel(Enum):
    LEVEL_ONE: int = 1  # Not-Identifiable
    LEVEL_TWO: int = 2  # Semi-Identifiable
    LEVEL_THREE: int = 3  # Identifiable


class RiskLevel_GDPR(Enum):
    VERY_LOW: int = 1  # Very Low
    LOW: int = 3  # Low
    MEDIUM: int = 5  # Medium
    HIGH: int = 7  # High
    VERY_HIGH: int = 9  # Very High


class RiskLevel_PII(Enum):
    LOW: int = 1  # Low
    MEDIUM: int = 5  # Medium
    HIGH: int = 9  # High


class RiskLevel_Identificable_GDPR(Enum):
    VERY_LOW: str = "Very Low"
    LOW: str = "Low"
    MEDIUM: str = "Medium"
    HIGH: str = "High"
    VERY_HIGH: str = "Very High"


class RiskLevel_Identificable_PII(Enum):
    LOW: str = "Low"
    MEDIUM: str = "Medium"
    HIGH: str = "High"


class RiskLevelDefinition(Enum):
    # Levels on the continuum presented by Schwartz and Solove (2011)
    LEVEL_ONE: str = (
        "Non-Identifiable"  # Default if no entities were detected, risk level is set to this
    )
    LEVEL_TWO: str = "Semi-Identifiable"
    LEVEL_THREE: str = (
        "Identifiable"  # Level associated with Directly PII, PHI, and Standalone PII info types
    )


class MetadataType(Enum):
    SCREEN_NAME: str = "screen_name"
    NAME: str = "name"
    LOCATION: str = "location"
    URL: str = "url"
    USER_ID: str = "user_id"


class PIIType(Enum):
    """
    PII ENTITIES English LANGUAGE
    """

    PHONE_NUMBER: str = "PHONE_NUMBER"  # I
    EMAIL_ADDRESS: str = "EMAIL_ADDRESS"  # I
    ABA_ROUTING_NUMBER: str = "ABA_ROUTING_NUMBER"  # I
    IP_ADDRESS: str = "IP_ADDRESS"  # I
    DATE: str = "DATE"  # I
    AGE: str = "AGE"  # I
    PERSON: str = "PERSON"  # I
    CREDIT_CARD: str = "CREDIT_CARD"  # I
    CRYPTO_ACCOUNT_NUMBER: str = "CRYPTO"  # I
    URL: str = "URL"  # I
    DATE_TIME: str = "DATE_TIME"  # I
    LOCATION: str = "LOCATION"  # I
    ZIPCODE: str = "ZIPCODE"  # I
    RACE: str = "RACE"  # I
    HEIGHT: str = "HEIGHT"  # I
    WEIGHT: str = "WEIGHT"  # I
    GENDER: str = "GENDER"  # I
    MARITAL_STATUS: str = "MARITAL_STATUS"  # I
    HEALTH_INSURANCE_ID: str = "HEALTH_INSURANCE_ID"  # I
    SEXUAL_PREFERENCE: str = "SEXUAL_PREFERENCE"  # I
    SOCIAL_NETWORK_PROFILE: str = "SOCIAL_NETWORK_PROFILE"  # I
    JOB_TITLE: str = "JOB_TITLE"  # I
    OCCUPATION: str = "OCCUPATION"  # I
    MEDICAL_LICENSE: str = "MEDICAL_LICENSE"  # I
    US_SOCIAL_SECURITY_NUMBER: str = "US_SSN"  # I
    US_BANK_ACCOUNT_NUMBER: str = "US_BANK_NUMBER"  # I
    US_DRIVERS_LICENSE_NUMBER: str = "US_DRIVER_LICENSE"  # I
    US_PASSPORT: str = "US_PASSPORT"  # I
    US_INDIVIDUAL_TAXPAYER_IDENTIFICATION: str = "US_ITIN"  # I
    INTERNATIONAL_BANKING_ACCOUNT_NUMBER: str = "IBAN_CODE"  # I
    SWIFT_CODE: str = "SWIFT_CODE"  # I
    NATIONALITY_RELIGION_POLITICAL: str = (
        "NRP"  # A person's nationality, religion, or political group  # I
    )
    AUSTRALIAN_COMPANY_NUMBER: str = "AU_ACN"  # I
    AUSTRALIAN_BUSINESS_NUMBER: str = "AU_ABN"  # I
    AUSTRALIAN_TAX_FILE_NUMBER: str = "AU_TFN"  # I
    AUSTRALIAN_MEDICARE_NUMBER: str = "AU_MEDICARE"  # I
    UK_SOCIAL_SECURITY_NUMBER: str = "UK_NHS"  # I
    TITLE: str = "TITLE_EN"  # I


class PIIType_ES(Enum):
    """
    PII ENTITIES Spanish LANGUAGE
    """

    PHONE_NUMBER: str = "PHONE_NUMBER"
    EMAIL_ADDRESS: str = "EMAIL_ADDRESS"
    IP_ADDRESS: str = "IP_ADDRESS"
    DATE: str = "DATE_TIME"
    ADDRESS: str = "LOCATION"
    AGE: str = "AGE"
    PERSON: str = "PERSON"
    CREDIT_CARD_NUMBER: str = "CREDIT_CARD"
    CRYPTO: str = "CRYPTO"
    URL: str = "URL"
    DATE_TIME: str = "DATE_TIME"
    LOCATION: str = "LOCATION"
    NRP: str = "NRP"
    INTERNATIONAL_BANKING_ACCOUNT_NUMBER: str = "IBAN_CODE"
    ES_NIF: str = "ES_NIF"
    ES_NIE: str = "ES_NIE"
    TITLE: str = "TITLE"
    SWIFT_CODE: str = "SWIFT_CODE"
    SOCIAL_NETWORK_PROFILE: str = "SOCIAL_NETWORK_PROFILE"


class PIIType_DE(Enum):
    """
    PII ENTITIES German LANGUAGE
    """

    PHONE_NUMBER: str = "PHONE_NUMBER"
    EMAIL_ADDRESS: str = "EMAIL_ADDRESS"
    IP_ADDRESS: str = "IP_ADDRESS"
    DATE: str = "DATE_TIME"
    ADDRESS: str = "LOCATION"
    AGE: str = "AGE"
    PERSON: str = "PERSON"
    CREDIT_CARD_NUMBER: str = "CREDIT_CARD"
    CRYPTO: str = "CRYPTO"
    URL: str = "URL"
    DATE_TIME: str = "DATE_TIME"
    LOCATION: str = "LOCATION"
    NRP: str = "NRP"
    INTERNATIONAL_BANKING_ACCOUNT_NUMBER: str = "IBAN_CODE"
    TITLE: str = "TITLE"
    DE_ID_NUMBER: str = "DE_ID_NUMBER"
    MEDICAL_LICENSE: str = "MEDICAL_LICENSE"
    SWIFT_CODE: str = "SWIFT_CODE"
    SOCIAL_NETWORK_PROFILE: str = "SOCIAL_NETWORK_PROFILE"


class PIIType_IT(Enum):
    """
    PII ENTITIES Italian LANGUAGE
    """

    PHONE_NUMBER: str = "PHONE_NUMBER"
    EMAIL_ADDRESS: str = "EMAIL_ADDRESS"
    IP_ADDRESS: str = "IP_ADDRESS"
    DATE: str = "DATE_TIME"
    ADDRESS: str = "LOCATION"
    AGE: str = "AGE"
    PERSON: str = "PERSON"
    CREDIT_CARD_NUMBER: str = "CREDIT_CARD"
    CRYPTO: str = "CRYPTO"
    URL: str = "URL"
    DATE_TIME: str = "DATE_TIME"
    LOCATION: str = "LOCATION"
    NRP: str = "NRP"
    INTERNATIONAL_BANKING_ACCOUNT_NUMBER: str = "IBAN_CODE"
    TITLE: str = "TITLE"
    IT_FISCAL_CODE: str = "IT_FISCAL_CODE"
    IT_DRIVER_LICENSE: str = "IT_DRIVER_LICENSE"
    IT_VAT_CODE: str = "IT_VAT_CODE"
    IT_PASSPORT: str = "IT_PASSPORT"
    IT_IDENTITY_CARD: str = "IT_IDENTITY_CARD"
    MEDICAL_LICENSE: str = "MEDICAL_LICENSE"
    SWIFT_CODE: str = "SWIFT_CODE"
    SOCIAL_NETWORK_PROFILE: str = "SOCIAL_NETWORK_PROFILE"


class NISTCategory(Enum):
    LINKABLE: str = "Linkable"
    DIRECTLY_PII: str = "Directly PII"


class DHSCategory(Enum):
    NOT_MENTIONED: str = "Not Mentioned"
    LINKABLE: str = "Linkable"
    STAND_ALONE_PII: str = "Stand Alone PII"
    SENSITIVE_PERSONALLY_IDENTIFABLE_INFORMATION: str = (
        "Sensitive Personally Identifiable Information"
    )


class HIPAACategory(Enum):
    NON_PHI: str = "Not Protected Health Information"
    PHI: str = "Protected Health Information"


class ClusterMembershipType(Enum):
    BASIC_DEMOGRAPHICS: str = "Basic Demographics"
    PERSONAL_PREFERENCES: str = "Personal Preferences"
    CONTACT_INFORMATION: str = "Contact Information"
    COMMUNITY_INTERACTION: str = "Community Interaction"
    FINANCIAL_INFORMATION: str = "Financial Information"
    SECURE_IDENTIFIERS: str = "Secure Identifiers"
    EDUCATIONAL_INFORMATION: str = "Educational Information"


class PIICategory(Enum):
    CONTACT_INFORMATION: str = "Contact Information"
    BASIC_IDENTIFIER: str = "Basic Identifier"
    BIOMETRIC_DATA: str = "Biometric Data"
    DEMOGRAPHIC_INFORMATION: str = "Demographic Information"
    EMPLOYMENT_INFORMATION: str = "Employment Information"
    FINANCIAL_INFORMATION: str = "Financial Information"
    GEOLOCATION_DATA: str = "Geolocation Data"
    HEALTH_INFORMATION: str = "Healthcare Information"
    ONLINE_CREDENTIALS: str = "Online Credentials"
    ONLINE_IDENTIFIER: str = "Online Identifier"
    PERSONAL_COMMUNICATIONS: str = "Personal Communications"
    PROFESSIONAL_LICENSE: str = "Professional Licenses"
    SECURITY_IDENTIFIER: str = "Security Identifiers"
    SENSITIVE_PERSONAL_INFORMATION: str = "Sensitive Personal Information"
    VEHICLE_IDENTIFIERS: str = "Vehicle Identifiers"


class GDPRCategory(Enum):
    ANONYMOUS_DATA: str = "Anonymous Data"
    PERSONAL_DATA: str = "Personal Data"
    PSEUDONYMOUS_DATA: str = "Pseudonymous Data"
    SENSITIVE_DATA: str = "Special Categories of Data (Sensitive Data)"
