from collections import defaultdict
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class HEALTH_INSURANCE_ID_Recognizer(PatternRecognizer):
    """Recognize US Social Security Number (SSN) using regex.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        Pattern("SSN1 (very weak)", r"\b([0-9]{5})-([0-9]{4})\b", 0.05),  # noqa E501
        Pattern("SSN2 (very weak)", r"\b([0-9]{3})-([0-9]{6})\b", 0.05),  # noqa E501
        Pattern(
            "SSN3 (very weak)", r"\b(([0-9]{3})-([0-9]{2})-([0-9]{4}))\b", 0.05
        ),  # noqa E501
        Pattern(
            "SSN3 bis (very weak) Standardized Format with Optional Dashes ",
            r"\b(([0-9]{3})-([0-9]{3})-([0-9]{4}))\b",
            0.1,
        ),
        Pattern("SSN4 (very weak)", r"\b[0-9]{9}\b", 0.05),
        Pattern("SSN5 (medium)", r"\b([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})\b", 0.3),
        Pattern(
            "SSN6 Alpha-Numeric with Specific Segments",
            r"\b([A-Za-z]{3})[- .]([0-9]{7})\b",
            0.3,
        ),
        Pattern(
            "SSN7 Segmented Alphanumeric",
            r"\b([A-Za-z]{2,3})[- .]([0-9]{4})[- .]([0-9]{4})\b",
            0.3,
        ),
        Pattern(
            "SSN8 Alphanumeric with Variable Length",
            r"\b([A-Za-z0-9]{4,})[- .]([0-9]{4})\b",
            0.3,
        ),
        Pattern(
            "SSN9 Comprehensive Alphanumeric with Optional Dashes",
            r"\b([A-Za-z0-9]{20})[- .]([A-Za-z0-9]{10})\b",
            0.3,
        ),
    ]

    CONTEXT = [
        "social security",
        "security",
        "social",
        "social sec",
        "ssn",
        "ssns",
        "ssn#",
        "ss#",
        "ssid",
        "policy number",
        "member id",
        "insurance id",
        "policy id",
        "coverage number",
        "plan id",
        "subscriber id",
        "insurance card number",
        "health plan",
        "health insurance",
        "benefits card",
        "provider id",
        "coverage id",
        "medical id",
        "health record",
        "patient id",
        "medical insurance",
        "claims number",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "HEALTH_INSURANCE_ID",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern text cannot be validated as a US_SSN entity.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated
        """
        # if there are delimiters, make sure both delimiters are the same
        delimiter_counts = defaultdict(int)
        for c in pattern_text:
            if c in (".", "-", " "):
                delimiter_counts[c] += 1
        if len(delimiter_counts.keys()) > 1:
            # mismatched delimiters
            return True

        only_digits = "".join(c for c in pattern_text if c.isdigit())
        if all(only_digits[0] == c for c in only_digits):
            # cannot be all same digit
            return True

        if only_digits[3:5] == "00" or only_digits[5:] == "0000":
            # groups cannot be all zeros
            return True

        for sample_ssn in ("000", "666", "123456789", "98765432", "078051120"):
            if only_digits.startswith(sample_ssn):
                return True

        return False
