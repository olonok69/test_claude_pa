# pylint: disable=broad-except,unused-argument,import-outside-toplevel,unused-variable
from typing import List, Tuple

from ...config import (
    DEFAULT_LANG,
    DEFAULT_TOKEN_REPLACEMENT_VALUE,
    NLP_CONFIGURATION_EN,
    SUPPORTED_LANGUAGES_EN,
    SUPPORTED_LANGUAGES_ES,
    NLP_CONFIGURATION_ES,
    SUPPORTED_LANGUAGES_DE,
    NLP_CONFIGURATION_DE,
    SUPPORTED_LANGUAGES_IT,
    NLP_CONFIGURATION_IT,
    MAX_LENGTH,
)
from ...models.analysis import DetectionResultItem, DetectionResult
from ...utils.package_installer_util import install_spacy_package
from ...utils.logging import logger, timed_operation
from .local.recognizers_en import (
    titles_recognizer,
    gender_recognizer,
    sex_orientation_recognizer,
    occupation_recognizer,
    jobs_recognizer,
    race_recognizer,
    marital_recognizer,
    swift_recognizer,
    aba_recognizer,
    snp_recognizer,
    weight_recognizer,
    height_recognizer,
    age_recognizer,
)
import copy
import logging


class PresidioPIIAnalyzer:
    def __init__(
        self,
        pii_token_replacement_value: str = DEFAULT_TOKEN_REPLACEMENT_VALUE,
        language: str = "en",
        pii_mapper=None,
        max_length: int = MAX_LENGTH,
    ):
        """
        Since installing Spacy, the en_core_web_lg model, and the MSFT Presidio package are optional installs
        the imports are wrapped to prevent any failures
        @param pii_token_replacement_value: str to replace detected pii token with (e.g. <REDACTED>)
        """
        self.max_length = max_length
        try:
            import spacy
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            from presidio_anonymizer.entities import OperatorConfig
            from .local.conf import operators

            if not spacy.util.is_package("en_core_web_lg") and language == "en":
                # Last resort. Will install the en_core_web_lg package if end-user hadn't already.
                install_spacy_package("en_core_web_lg")
            if not spacy.util.is_package("es_core_news_lg") and language == "es":
                # Last resort. Will install the en_core_web_lg package if end-user hadn't already.
                install_spacy_package("es_core_news_lg")
            if not spacy.util.is_package("de_core_news_lg") and language == "de":
                # Last resort. Will install the en_core_web_lg package if end-user hadn't already.
                install_spacy_package("de_core_news_lg")
            if not spacy.util.is_package("it_core_news_lg") and language == "it":
                # Last resort. Will install the en_core_web_lg package if end-user hadn't already.
                install_spacy_package("it_core_news_lg")

            # create AnalyzerEngine
            if language == "es":
                self.get_build_es_engine()
            elif language == "de":
                self.get_build_de_engine()
            elif language == "it":
                self.get_build_it_engine()
            elif language == "en":
                self.get_build_en_engine()

            self.analyzer = self.analyzerl
            self.anonymizer = AnonymizerEngine()
            self.pii_mapper = pii_mapper

            self.operators = operators

        except ImportError:
            raise AttributeError(
                'Missing dependencies from extras. Install the PII-Codex extras: "detections"'
            )

    def add_pattern_recognizers_en(self):
        """
        ADD recognizer EN analyzer engine
        """
        self.analyzerl.registry.add_recognizer(titles_recognizer)
        self.analyzerl.registry.add_recognizer(gender_recognizer)
        self.analyzerl.registry.add_recognizer(sex_orientation_recognizer)
        self.analyzerl.registry.add_recognizer(occupation_recognizer)
        self.analyzerl.registry.add_recognizer(jobs_recognizer)
        self.analyzerl.registry.add_recognizer(race_recognizer)
        self.analyzerl.registry.add_recognizer(marital_recognizer)
        self.analyzerl.registry.add_recognizer(swift_recognizer)
        self.analyzerl.registry.add_recognizer(aba_recognizer)
        self.analyzerl.registry.add_recognizer(snp_recognizer)
        self.analyzerl.registry.add_recognizer(height_recognizer)
        self.analyzerl.registry.add_recognizer(weight_recognizer)
        self.analyzerl.registry.add_recognizer(age_recognizer)

    def get_build_en_engine(self):
        """
        create ENglish analysis services
        """
        from .analysis_en import analisys_en
        from .local.recognizers import mister
        from .local.date_custom import Date_Custom_Recognizer
        from .local.en_zipcode import EnZipcode
        from .local.en_health_number import HEALTH_INSURANCE_ID_Recognizer
        from .local.conf import REMOVE_RECOGNIZERS_EN, LABELS_TO_IGNORE_EN

        # custom  PatternRecognizer
        date_of_birth = Date_Custom_Recognizer()
        zipcode = EnZipcode()
        health_id = HEALTH_INSURANCE_ID_Recognizer()
        self.w_analyzer = analisys_en(
            nlp_configuration=NLP_CONFIGURATION_EN,
            custom_pattern_recognizers=[mister],
            supported_language=SUPPORTED_LANGUAGES_EN,
        )

        self.w_analyzer.create_custom_patern_recognizers(
            self.w_analyzer.list_custom_pattern_recognizers
        )
        self.w_analyzer.create_nlp_engine(self.w_analyzer.nlp_configuration)
        self.w_analyzer.registry.add_recognizer(titles_recognizer)
        self.w_analyzer.registry.add_recognizer(date_of_birth)
        self.w_analyzer.registry.add_recognizer(zipcode)
        self.w_analyzer.registry.add_recognizer(health_id)
        self.w_analyzer.registry.add_recognizer(gender_recognizer)
        self.w_analyzer.registry.add_recognizer(sex_orientation_recognizer)
        self.w_analyzer.registry.add_recognizer(occupation_recognizer)
        self.w_analyzer.registry.add_recognizer(jobs_recognizer)
        self.w_analyzer.registry.add_recognizer(race_recognizer)
        self.w_analyzer.registry.add_recognizer(marital_recognizer)
        self.w_analyzer.registry.add_recognizer(swift_recognizer)
        self.w_analyzer.registry.add_recognizer(aba_recognizer)
        self.w_analyzer.registry.add_recognizer(snp_recognizer)
        self.w_analyzer.registry.add_recognizer(height_recognizer)
        self.w_analyzer.registry.add_recognizer(weight_recognizer)
        self.w_analyzer.registry.add_recognizer(age_recognizer)
        for rec in REMOVE_RECOGNIZERS_EN:
            logging.warn(f"Removing Recognizer {rec} from engine EN")
            self.w_analyzer.registry.remove_recognizer(rec)
        for label in LABELS_TO_IGNORE_EN:
            logging.warn(f"Adding Label to Ignore {label} to engine EN")
            self.w_analyzer.nlp_engine.ner_model_configuration.labels_to_ignore.add(
                label
            )
        self.w_analyzer.load_custom_recognizers()
        self.w_analyzer.create_AnalyzerEngine()

        self.analyzerl = self.w_analyzer.AnalyzerEngine
        self.analyzerl.nlp_engine.nlp["en"].max_length = self.max_length

    def get_build_es_engine(self):
        """
        create spanish analysis services
        """
        from .analysis_es import analisys_es
        from .local.recognizers import mister_es
        from .local.es_phone_number import EsNumberRecognizer
        from .local.recognizers_en import SWIFTRecognizer, Social_Network_Recognizer
        from .local.conf import REMOVE_RECOGNIZERS_ES, LABELS_TO_IGNORE_ES

        # custom  PatternRecognizer
        swift_recognizer = SWIFTRecognizer(
            supported_entities=["SWIFT_CODE"], supported_language="es"
        )
        snp_recognizer = Social_Network_Recognizer(
            supported_entities=["SOCIAL_NETWORK_PROFILE"], supported_language="es"
        )
        es_number = EsNumberRecognizer()
        self.w_analyzer = analisys_es(
            nlp_configuration=NLP_CONFIGURATION_ES,
            custom_pattern_recognizers=[mister_es],
            supported_language=SUPPORTED_LANGUAGES_ES,
        )

        self.w_analyzer.create_custom_patern_recognizers(
            self.w_analyzer.list_custom_pattern_recognizers
        )
        self.w_analyzer.create_nlp_engine(self.w_analyzer.nlp_configuration)
        self.w_analyzer.registry.add_recognizer(es_number)
        self.w_analyzer.registry.add_recognizer(swift_recognizer)
        self.w_analyzer.registry.add_recognizer(snp_recognizer)
        self.w_analyzer.load_custom_recognizers()
        self.w_analyzer.create_AnalyzerEngine()
        for rec in REMOVE_RECOGNIZERS_ES:
            logging.warn(f"Removing Recognizer {rec} from engine ES")
            self.w_analyzer.registry.remove_recognizer(rec)
        for label in LABELS_TO_IGNORE_ES:
            logging.warn(f"Adding Label to Ignore {label} to engine ES")
            self.w_analyzer.nlp_engine.ner_model_configuration.labels_to_ignore.add(
                label
            )

        self.analyzerl = self.w_analyzer.AnalyzerEngine
        self.analyzerl.nlp_engine.nlp["es"].max_length = self.max_length

    def get_build_de_engine(self):
        """
        create german analysis services
        """
        from .analysis_de import analisys_de
        from .local.recognizers import mister_de
        from .local.de_id_number import De_Id_NumberRecognizer
        from .local.recognizers_en import SWIFTRecognizer, Social_Network_Recognizer
        from .local.conf import REMOVE_RECOGNIZERS_DE, LABELS_TO_IGNORE_DE

        swift_recognizer = SWIFTRecognizer(
            supported_entities=["SWIFT_CODE"], supported_language="de"
        )
        snp_recognizer = Social_Network_Recognizer(
            supported_entities=["SOCIAL_NETWORK_PROFILE"], supported_language="de"
        )

        # custom  PatternRecognizer
        de_number = De_Id_NumberRecognizer()
        self.w_analyzer = analisys_de(
            nlp_configuration=NLP_CONFIGURATION_DE,
            custom_pattern_recognizers=[mister_de],
            supported_language=SUPPORTED_LANGUAGES_DE,
        )
        self.w_analyzer.create_custom_patern_recognizers(
            self.w_analyzer.list_custom_pattern_recognizers
        )
        self.w_analyzer.create_nlp_engine(self.w_analyzer.nlp_configuration)
        self.w_analyzer.registry.add_recognizer(de_number)
        self.w_analyzer.registry.add_recognizer(swift_recognizer)
        self.w_analyzer.registry.add_recognizer(snp_recognizer)
        for rec in REMOVE_RECOGNIZERS_DE:
            logging.warn(f"Removing Recognizer {rec} from engine DE")
            self.w_analyzer.registry.remove_recognizer(rec)
        for label in LABELS_TO_IGNORE_DE:
            logging.warn(f"Adding Label to Ignore {label} to engine DE")
            self.w_analyzer.nlp_engine.ner_model_configuration.labels_to_ignore.add(
                label
            )

        self.w_analyzer.load_custom_recognizers()
        self.w_analyzer.create_AnalyzerEngine()

        self.analyzerl = self.w_analyzer.AnalyzerEngine
        self.analyzerl.nlp_engine.nlp["de"].max_length = self.max_length

    def get_build_it_engine(self):
        """
        create italian analysis services
        """
        from .analysis_it import analisys_it
        from .local.recognizers import mister_it
        from .local.recognizers_en import SWIFTRecognizer, Social_Network_Recognizer
        from .local.conf import REMOVE_RECOGNIZERS_IT, LABELS_TO_IGNORE_IT

        swift_recognizer = SWIFTRecognizer(
            supported_entities=["SWIFT_CODE"], supported_language="it"
        )
        snp_recognizer = Social_Network_Recognizer(
            supported_entities=["SOCIAL_NETWORK_PROFILE"], supported_language="it"
        )

        # custom  PatternRecognizer
        self.w_analyzer = analisys_it(
            nlp_configuration=NLP_CONFIGURATION_IT,
            custom_pattern_recognizers=[mister_it],
            supported_language=SUPPORTED_LANGUAGES_IT,
        )
        self.w_analyzer.create_custom_patern_recognizers(
            self.w_analyzer.list_custom_pattern_recognizers
        )
        self.w_analyzer.create_nlp_engine(self.w_analyzer.nlp_configuration)
        self.w_analyzer.registry.add_recognizer(swift_recognizer)
        self.w_analyzer.registry.add_recognizer(snp_recognizer)
        for rec in REMOVE_RECOGNIZERS_IT:
            logging.warn(f"Removing Recognizer {rec} from engine IT")
            self.w_analyzer.registry.remove_recognizer(rec)
        for label in LABELS_TO_IGNORE_IT:
            logging.warn(f"Adding Label to Ignore {label} to engine IT")
            self.w_analyzer.nlp_engine.ner_model_configuration.labels_to_ignore.add(
                label
            )
        self.w_analyzer.load_custom_recognizers()
        self.w_analyzer.create_AnalyzerEngine()
        self.analyzerl = self.w_analyzer.AnalyzerEngine
        self.analyzerl.nlp_engine.nlp["it"].max_length = self.max_length

    def get_supported_entities(self, language_code=DEFAULT_LANG) -> List[str]:
        """
        Retrieves a list of supported entities, this will narrow down what is available for a given language

        @param language_code: str - defaults to "en"
        @return: List[str]
        """
        return self.analyzer.get_supported_entities(language=language_code)  # type: ignore

    def get_loaded_recognizers(self, language_code: str = DEFAULT_LANG):
        """
        Retrieves a list of loaded recognizers, narrowing down the list of what is available for a given language
        @param language_code:
        @return:
        """
        return self.analyzer.get_recognizers(language=language_code)  # type: ignore

    @timed_operation
    def analyze_item(
        self,
        text: str,
        language_code: str = DEFAULT_LANG,
        entities: List[str] = None,
        ad_hoc_recognizers=None,
        score_threshold: float = 0.01,
        filter_detection: bool = True,
    ) -> Tuple[List[DetectionResultItem], str]:
        """
        Uses Microsoft Presidio (spaCy module) to analyze given a set of entities to analyze the provided text against.
        Will log an error if the identifier or entity recognizer is not added to Presidio's base recognizers or
        a custom recognizer created. Returns the list of detected items and the sanitized string

        @param language_code: str "en" is default
        @param entities: str - List[MSFTPresidioPIIType.name]
        @param text: str
        @return: Tuple[List[DetectionResultItem], str]
        """

        detections = []

        if not entities:
            entities = self.get_supported_entities(language_code)

        try:
            # Engine Setup - spaCy model setup and PII recognizers
            detections = self.analyzer.analyze(  # type: ignore
                text=text,
                entities=entities,
                language=language_code,
                ad_hoc_recognizers=ad_hoc_recognizers,
                score_threshold=score_threshold,
            )

        except Exception as ex:
            logger.error(ex)
        # create list of DetectionResultItem
        list_detections = [
            DetectionResultItem(
                entity_type=result.entity_type,
                score=result.score,
                start=result.start,
                end=result.end,
            )
            for result in detections
        ]
        if filter_detection:
            final_ents = []
            list_detections_bis = copy.deepcopy(list_detections)
            not_copy = []
            for ent in list_detections:
                finalent = copy.deepcopy(ent)
                for ent2 in list_detections_bis:
                    if (
                        ent.start == ent2.start
                        and ent.end == ent2.end
                        and ent2.score > ent.score
                    ):
                        finalent = copy.deepcopy(ent2)
                    elif (
                        ent.start == ent2.start
                        and ent.end == ent2.end
                        and ent2.score < ent.score
                        and ent2 not in not_copy
                    ):
                        not_copy.append(ent2)
                if finalent not in final_ents and finalent not in not_copy:
                    final_ents.append(finalent)
            logging.info(
                f"Initial length Detections: {len(list_detections)}, Final length Detections: {len(final_ents)}"
            )
            list_detections = copy.deepcopy(final_ents)

        # Return analyzer results in formatted Analysis Result List object
        return list_detections, self.sanitize_text(text=text, analysis_items=detections)

    def sanitize_text(
        self, text: str, analysis_items: List[DetectionResultItem]
    ) -> str:
        """
        Sanitizes the text analyzed with MSFT Presidio's Anonymizer
        @param text:
        @param analysis_items:
        @return:
        """
        try:
            anonymization_result = self.anonymizer.anonymize(
                text=text, analyzer_results=analysis_items, operators=self.operators
            )

            return anonymization_result.text

        except Exception as ex:
            logger.error(f"An error occurred sanitizing the string. Exception {ex}")
            return ""

    @timed_operation
    def analyze_collection(
        self, texts: List[str], language_code: str = "en", entities: List[str] = None
    ) -> List[DetectionResult]:
        """
        Uses Microsoft Presidio (spaCy module) to analyze given a set of entities to analyze the provided text against.
        Will log an error if the identifier or entity recognizer is not added to Presidio's base recognizers or
        a custom recognizer created.

        @param language_code: str "en" is default
        @param entities: List[MSFTPresidioPIIType.name] defaults to all possible entities for selected language
        @param texts: List[str]
        @return: List[DetectionResult]
        """

        detection_results = []
        try:
            if not entities:
                entities = self.get_supported_entities(language_code)

            # Engine Setup - spaCy model setup and PII recognizers
            for i, text in enumerate(texts):
                text_analysis = self.analyzer.analyze(  # type: ignore
                    text=text, entities=entities, language=language_code
                )

                # Every analysis by the analyzer will have a set of detections within
                detections = [
                    DetectionResultItem(
                        entity_type=self.pii_mapper.convert_msft_presidio_pii_to_common_pii_type(
                            result.entity_type
                        ).name,
                        score=result.score,
                        start=result.start,
                        end=result.end,
                    )
                    for result in text_analysis
                ]
                detection_results.append(
                    DetectionResult(index=i, detections=detections)
                )

            # Return analyzer results in formatted Analysis Result List object

        except Exception as ex:
            logger.error(ex)

        return detection_results

    @classmethod
    @timed_operation
    def convert_analyzed_item(cls, pii_detection) -> List[DetectionResultItem]:
        """
        Converts a single Presidio analysis attempt into a collection of DetectionResultItem objects. One string
        analysis by Presidio returns an array of RecognizerResult objects.

        @param pii_detection: RecognizerResult from presidio analyzer
        @return: List[DetectionResultItem]
        """

        return [
            DetectionResultItem(
                entity_type=PresidioPIIAnalyzer.pii_mapper.convert_msft_presidio_pii_to_common_pii_type(
                    result.entity_type
                ).name,
                score=result.score,
                start=result.start,
                end=result.end,
            )
            for result in pii_detection
        ]

    @classmethod
    @timed_operation
    def convert_analyzed_collection(cls, pii_detections) -> List[DetectionResult]:
        """
        Converts a collection of Presidio analysis results to a collection of DetectionResult. A collection of Presidio
        analysis results ends up being a 2D array.

        @param pii_detections: List[RecognizerResult] from Presidio analyzer

        """

        detection_results: List[DetectionResult] = []
        for i, result in enumerate(pii_detections):
            # Return results in formatted Analysis Result List object
            detections = []
            for entity in result:
                detections.append(
                    DetectionResultItem(
                        entity_type=PresidioPIIAnalyzer.pii_mapper.convert_msft_presidio_pii_to_common_pii_type(
                            entity.entity_type
                        ).name,
                        score=entity.score,
                        start=entity.start,
                        end=entity.end,
                    )
                )

            detection_results.append(DetectionResult(index=i, detections=detections))

        return detection_results
