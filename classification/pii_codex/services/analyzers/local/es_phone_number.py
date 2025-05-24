from typing import List, Tuple, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class EsNumberRecognizer(PatternRecognizer):
    """
    Recognize telefone number using regex and checksum.

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
            "ES_NUMBER",
            r"\b[1-9]?[0-9]{8}\b",
            0.5,
        ),
    ]

    CONTEXT = ["Numero de telefono español", "identificación", "mobil", "telefono"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "PHONE_NUMBER",
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
        pattern_text = EsNumberRecognizer.__sanitize_value(pattern_text)

        return len(pattern_text) == 9

    @staticmethod
    def __sanitize_value(text: str) -> str:
        return text.replace("-", "").replace(" ", "")
