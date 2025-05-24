from fastapi import FastAPI
from fastapi.testclient import TestClient
from detectaicore import classification_doc
from inscriptis import get_text
from inscriptis.css_profiles import CSS_PROFILES
from inscriptis.model.config import ParserConfig
from dataclasses import is_dataclass
from tests.dummy_data.test_classification.dummy_data import (
    ES_KEYS,
    text_to_analyse,
    text_to_analyse_de,
    v2_columns,
    v1_columns,
    PII_sample,
    PII_sample_extended,
    PII_sample_it,
    PII_sample_es,
    PII_sample_de,
    dummy_set_analysis_results,
    dummy_entity_types,
)
import json
import os
import platform
import re

config = ParserConfig(css=CSS_PROFILES["strict"].copy())
os.environ["IS_TEST"] = "1"


from tests.dummy_data.dummy_data import (
    dummy_doc,
    test_classification_v2,
    html1,
    html,
    html1_text,
    html_text,
)


if platform.system() == "Windows":
    from classification.endpoint_classification import endpoint
    from classification.pii_codex.services.analysis_service import (
        PIIAnalysisService,
    )
    from classification.pii_codex.utils.pii_mapping_util import PIIMapper
    from classification.pii_codex.models.analysis import RiskAssessment_v2

    client = TestClient(endpoint)


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

dummy_pii = set(test_classification_v2.keys())
dummpy_language = set(test_classification_v2.get("language").keys())


def test_api_object():
    """
    Test endpoint FastAPI class
    """
    endpoint = FastAPI()
    assert type(endpoint) == FastAPI


def test_doc():
    """
    Test if Document has the rigth model
    """
    test = classification_doc()
    test.dict() == dummy_doc


def test_spacy_models():
    """
    test spacy models
    """
    import spacy

    if platform.system() == "Windows":
        sp = spacy.load("en_core_web_lg")
        nlp = spacy.load("xx_ent_wiki_sm")
        es = spacy.load("es_core_news_lg")
        de = spacy.load("de_core_news_lg")
        assert type(sp) == spacy.lang.en.English
        assert type(nlp) == spacy.lang.xx.MultiLanguage
        assert type(es) == spacy.lang.es.Spanish
        assert type(de) == spacy.lang.de.German


def test_endpoint_health():
    if platform.system() == "Windows":
        # post the document to endpoint
        response = client.get(
            "/health-check/",
        )
        assert response.status_code == 200


def test_get_text():
    """
    Text get_text method extract text from html
    """

    text1 = get_text(html)
    assert text1 == html_text

    text2 = get_text(html1)
    assert text2 == html1_text


def test_spanish_PIIAnalysisService():
    """
    # Test the Spanish PIIAnalysisService
    """

    if platform.system() == "Windows":
        mapper = PIIMapper(
            version="v1",
            mapping_file_name="pii_type_mappings",
            test=False,
            reload=False,
        )
        pii_analysys = PIIAnalysisService(language_code="es", pii_mapper=mapper)
        out = pii_analysys.analyze_collection(
            texts=[text_to_analyse],
            language_code="es",
            collection_type="population",
            collection_name="PII Collection 1",
        )
        j = out.to_dict()
        assert set(j.keys()) == ES_KEYS
        assert j["detected_pii_types"] == {"ES_NIF", "PERSON", "PHONE_NUMBER", "TITLE"}
        assert j["detected_pii_type_frequencies"] == {
            "TITLE": 1,
            "PHONE_NUMBER": 2,
            "ES_NIF": 1,
            "PERSON": 1,
        }


def test_german_PIIAnalysisService():
    """
    # Test the German PIIAnalysisService
    """

    if platform.system() == "Windows":
        mapper = PIIMapper(
            version="v1",
            mapping_file_name="pii_type_mappings",
            test=False,
            reload=False,
        )
        pii_analysys = PIIAnalysisService(language_code="de", pii_mapper=mapper)
        out = pii_analysys.analyze_collection(
            texts=[text_to_analyse_de],
            language_code="de",
            collection_type="population",
            collection_name="PII Collection 1",
        )
        j = out.to_dict()
        assert set(j.keys()) == ES_KEYS
        assert j["detected_pii_types"] == {
            "DE_ID_NUMBER",
            "LOCATION",
            "PERSON",
            "TITLE",
        }
        assert j["detected_pii_type_frequencies"] == {
            "DE_ID_NUMBER": 1,
            "TITLE": 1,
            "PERSON": 3,
            "LOCATION": 1,
        }


def test_PIIMapper():
    """
    Create object PII_Mapper and assets the attributes
    """
    if platform.system() == "Windows":
        pii_mapper = PIIMapper(
            version="v1", mapping_file_name="pii_type_mappings", test=True
        )
        assert set(list(pii_mapper._pii_mapping_data_frame.columns)) == v1_columns
        os.environ["IS_TEST"] = "0"
        pii_mapper = PIIMapper(
            version="v2", mapping_file_name="pii_gdpr_mapping", test=True
        )
        assert set(list(pii_mapper._pii_mapping_data_frame.columns)) == v2_columns
        # get risk Assestment from a PII entity`    `
        pii = pii_mapper.map_pii_type("PERSON")
        assert (
            is_dataclass(RiskAssessment_v2) and isinstance(pii, RiskAssessment_v2)
        ) == True
        os.environ["IS_TEST"] = "1"


def test_PIIAnalysisService_v2():
    """
    Create object test_PIIAnalysisService version v2 and assets the attributes
    """
    if platform.system() == "Windows":
        pii_analysys = PIIAnalysisService(language_code="en")
        version = "v2"
        file_v2 = "pii_gdpr_mapping"
        pii_mapper = PIIMapper(
            version=version,
            mapping_file_name=file_v2,
            test=False,
            reload=False,
        )
        pii_analysys.pii_mapper = pii_mapper
        pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
        pii_analysys._analyzer.pii_mapper = pii_mapper

        assert len(pii_analysys._analyzer.get_supported_entities("en")) >= 23

        out = pii_analysys.analyze_collection(
            texts=[PII_sample],
            language_code="en",
            collection_type="population",
            collection_name="PII Collection 1",
            # score_threshold=0.01,  # WE can use this score to as minimun required to
        )
        # Test if the object has all keys
        analysis_results = out.to_dict()
        assert dummy_set_analysis_results == set(list(analysis_results.keys()))
        # test if detected PII types equal to 22 TODO INCLUDE entity SG_NRIC_FIN

        assert len(analysis_results["detected_pii_types"]) >= 22
        # test if the detected entities are all posible except  SG_NRIC_FIN
        assert dummy_entity_types.difference(
            analysis_results["detected_pii_types"]
        ) == {"SG_NRIC_FIN"}
        # test if detect more than or equal 50 entities in that document there are 52 including SG_NRIC_FIN, excluding 50
        assert analysis_results["detection_count"] >= 50


def test_PIIAnalysisService_v2_en():
    """
    Create object test_PIIAnalysisService version v2 and assets the attributes
    """
    if platform.system() == "Windows":
        pii_analysys = PIIAnalysisService(language_code="en")
        version = "v2"
        file_v2 = "pii_gdpr_mapping"
        pii_mapper = PIIMapper(
            version=version,
            mapping_file_name=file_v2,
            test=False,
            reload=False,
        )
        pii_analysys.pii_mapper = pii_mapper
        pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
        pii_analysys._analyzer.pii_mapper = pii_mapper

        assert len(pii_analysys._analyzer.get_supported_entities("en")) >= 23
        # use text with additional extension
        texto = PII_sample + "\n " + PII_sample_extended
        texto = re.sub("(\s{1}\d{1,2})(\.{1})(\s{1})", r"\1 \3", texto)
        out = pii_analysys.analyze_collection(
            texts=[texto],
            language_code="en",
            collection_type="population",
            collection_name="PII Collection 1",
            # score_threshold=0.01,  # WE can use this score to as minimun required to
        )
        # Test if the object has all keys
        analysis_results = out.to_dict()
        assert dummy_set_analysis_results == set(list(analysis_results.keys()))
        # test if detected PII types equal to 22 TODO INCLUDE entity SG_NRIC_FIN

        assert len(analysis_results["detected_pii_types"]) >= 22
        # test if the detected entities are all posible except  SG_NRIC_FIN
        assert dummy_entity_types.difference(
            analysis_results["detected_pii_types"]
        ) == {"SG_NRIC_FIN"}
        # test if detect more than or equal 50 entities in that document there are 52 including SG_NRIC_FIN, excluding 50
        assert analysis_results["detection_count"] >= 50


def test_PIIAnalysisService_v2_it():
    """
    Create object test_PIIAnalysisService version v2 and assets the attributes
    """
    if platform.system() == "Windows":
        pii_analysys = PIIAnalysisService(language_code="it")
        version = "v2"
        file_v2 = "pii_gdpr_mapping"
        pii_mapper = PIIMapper(
            version=version,
            mapping_file_name=file_v2,
            test=False,
            reload=False,
        )
        pii_analysys.pii_mapper = pii_mapper
        pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
        pii_analysys._analyzer.pii_mapper = pii_mapper

        assert len(pii_analysys._analyzer.get_supported_entities("it")) >= 18

        out = pii_analysys.analyze_collection(
            texts=[PII_sample_it],
            language_code="it",
            collection_type="population",
            collection_name="PII Collection 1",
            # score_threshold=0.01,  # WE can use this score to as minimun required to
        )
        # Test if the object has all keys
        analysis_results = out.to_dict()
        assert dummy_set_analysis_results == set(list(analysis_results.keys()))
        # test if detected PII types equal to 22 TODO INCLUDE entity SG_NRIC_FIN

        assert len(analysis_results["detected_pii_types"]) >= 6
        # test if the detected entities are all posible except  SG_NRIC_FIN

        # test if detect more than or equal 50 entities in that document there are 52 including SG_NRIC_FIN, excluding 50
        assert analysis_results["detection_count"] >= 14


def test_PIIAnalysisService_v2_es():
    """
    Create object test_PIIAnalysisService version v2 and assets the attributes
    """
    if platform.system() == "Windows":
        pii_analysys = PIIAnalysisService(language_code="es")
        version = "v2"
        file_v2 = "pii_gdpr_mapping"
        pii_mapper = PIIMapper(
            version=version,
            mapping_file_name=file_v2,
            test=False,
            reload=False,
        )
        pii_analysys.pii_mapper = pii_mapper
        pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
        pii_analysys._analyzer.pii_mapper = pii_mapper

        assert len(pii_analysys._analyzer.get_supported_entities("es")) >= 14

        out = pii_analysys.analyze_collection(
            texts=[PII_sample_es],
            language_code="es",
            collection_type="population",
            collection_name="PII Collection 1",
            # score_threshold=0.01,  # WE can use this score to as minimun required to
        )
        # Test if the object has all keys
        analysis_results = out.to_dict()
        assert dummy_set_analysis_results == set(list(analysis_results.keys()))
        # test if detected PII types equal to 22 TODO INCLUDE entity SG_NRIC_FIN

        assert len(analysis_results["detected_pii_types"]) >= 4
        # test if the detected entities are all posible except  SG_NRIC_FIN

        # test if detect more than or equal 50 entities in that document there are 52 including SG_NRIC_FIN, excluding 50
        assert analysis_results["detection_count"] >= 5


def test_PIIAnalysisService_v2_de():
    """
    Create object test_PIIAnalysisService version v2 and assets the attributes
    """
    if platform.system() == "Windows":
        pii_analysys = PIIAnalysisService(language_code="de")
        version = "v2"
        file_v2 = "pii_gdpr_mapping"
        pii_mapper = PIIMapper(
            version=version,
            mapping_file_name=file_v2,
            test=False,
            reload=False,
        )
        pii_analysys.pii_mapper = pii_mapper
        pii_analysys._pii_assessment_service.pii_mapper = pii_mapper
        pii_analysys._analyzer.pii_mapper = pii_mapper

        assert len(pii_analysys._analyzer.get_supported_entities("de")) >= 14

        out = pii_analysys.analyze_collection(
            texts=[PII_sample_de],
            language_code="de",
            collection_type="population",
            collection_name="PII Collection 1",
            # score_threshold=0.01,  # WE can use this score to as minimun required to
        )
        # Test if the object has all keys
        analysis_results = out.to_dict()
        assert dummy_set_analysis_results == set(list(analysis_results.keys()))
        # test if detected PII types equal to 22 TODO INCLUDE entity SG_NRIC_FIN

        assert len(analysis_results["detected_pii_types"]) >= 4
        # test if the detected entities are all posible except  SG_NRIC_FIN

        # test if detect more than or equal 50 entities in that document there are 52 including SG_NRIC_FIN, excluding 50
        assert analysis_results["detection_count"] >= 5
