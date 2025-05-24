from typing import List
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from presidio_analyzer import PatternRecognizer
from typing import List, Optional


# READ THIS for Context
# https://github.com/microsoft/presidio/blob/main/presidio-analyzer/presidio_analyzer/analyzer_engine.py
class analisys_it(object):
    """
    Analisys Engine Italian
    """

    def __init__(
        self,
        supported_entities: Optional[List[str]] = None,
        nlp_configuration: Optional[dict] = None,
        name: str = None,
        supported_language: Optional[List[str]] = None,
        version: str = "0.0.1",
        custom_pattern_recognizers: Optional[List[dict]] = None,
        context: Optional[List[str]] = None,
    ):
        self.supported_language = supported_language
        self.supported_languages = supported_language
        self.nlp_configuration = nlp_configuration
        self.supported_entities = supported_entities
        self.nlp_engine = None
        self.custom_pattern_recognizers = None
        self.list_custom_pattern_recognizers = custom_pattern_recognizers
        self.provider = RecognizerRegistryProvider(
            registry_configuration={"supported_languages": self.supported_languages}
        )
        self.list_custom_pattern_recognizers = custom_pattern_recognizers
        self.registry = self.provider.create_recognizer_registry()
        self.AnalyzerEngine = None

        self.create_analyzer()

    def create_AnalyzerEngine(self):
        self.AnalyzerEngine = AnalyzerEngine(
            registry=self.registry,
            nlp_engine=self.nlp_engine,
            supported_languages=self.supported_language,
        )

    def create_nlp_engine(self, configuration):
        provider = NlpEngineProvider(nlp_configuration=configuration)
        self.nlp_engine = provider.create_engine()

    def create_patern_recognizer(self, conf: dict):
        titles_recognizer = PatternRecognizer(
            supported_entity=conf.get("supported_entity"),
            supported_language=conf.get("language"),
            deny_list=conf.get("deny_list"),
        )
        return titles_recognizer

    def create_custom_patern_recognizers(self, list_recognizers: List[dict]):
        custom_pattern_recognizers = []
        for rec in list_recognizers:
            custom_pattern_recognizers.append(self.create_patern_recognizer(rec))
        self.custom_pattern_recognizers = custom_pattern_recognizers

    def load_custom_recognizers(self):
        for rec in self.custom_pattern_recognizers:
            self.registry.add_recognizer(rec)

    def create_analyzer(self):
        """
        create analyzer after initialization
        """
        self.create_custom_patern_recognizers(self.list_custom_pattern_recognizers)
        self.create_nlp_engine(self.nlp_configuration)
        self.registry.load_predefined_recognizers(
            languages=self.supported_language, nlp_engine=self.nlp_engine
        )
        self.load_custom_recognizers()
        self.create_AnalyzerEngine()
