from typing import List, Tuple, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class EnZipcode(PatternRecognizer):
    """
    Recognize Zipcode in US.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    :param replacement_pairs: List of tuples with potential replacement values
    for different strings to be used during pattern matching.
    This can allow a greater variety in input, for example by removing dashes or spaces.
    """

    PATTERNS = [
        Pattern(
            "ZIPCODE Medium",
            r"\b[1-9]{1}[0-9]{4}(\-\d{4})?\b",
            0.5,
        ),
    ]

    CONTEXT = ["Postal Code", "zipcode", "Zip Code", "Post Code"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "ZIPCODE",
    ):

        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
