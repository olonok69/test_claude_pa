from typing import List, Tuple, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class De_Id_NumberRecognizer(PatternRecognizer):
    """
    Recognize German Id number using regex and checksum.

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
            "DE_ID_NUMBER_SORT",
            r"\b(?i:\b[0-9A-Z]{9}[0-9]D?\b)\b",
            0.5,
        ),
        Pattern(
            "DE_ID_NUMBER",
            r"\b(?i:\b[0-9A-Z]{9}[0-9]D?[ -]?[0-9]{6}[0-9][ -MF]?[0-9]{6}[0-9][ -]?[0-9]\b)\b",
            0.5,
        ),
    ]

    CONTEXT = ["Personalausweis", "Rentenversicherungsnummer"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "de",
        supported_entity: str = "DE_ID_NUMBER",
        replacement_pairs: Optional[List[Tuple[str, str]]] = None,
    ):
        self.replacement_pairs = (
            replacement_pairs if replacement_pairs else [("-", ""), (" ", "")]
        )
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> bool:  # noqa D102
        if len(pattern_text) < 29:
            pattern_text = De_Id_NumberRecognizer.__sanitize_value(pattern_text)

        return len(pattern_text) == 11 or len(pattern_text)

    @staticmethod
    def __sanitize_value(text: str) -> str:
        return text.replace("-", "").replace(" ", "")
