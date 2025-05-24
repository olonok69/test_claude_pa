# pylint: disable=too-many-arguments
from typing import List, Optional, Tuple
import pandas as pd


from ..models.common import (
    AnalysisProviderType,
    RiskLevel,
    RiskLevel_GDPR,
)
from ..models.analysis import (
    DetectionResultItem,
    AnalysisResultItem,
    AnalysisResultItem_v2,
    AnalysisResult,
    AnalysisResultSet,
    AnalysisResult_v2,
    AnalysisResultSet_v2,
    DetectionResult,
    RiskAssessment,
    RiskAssessment_v2,
)

from ..models.common import PIIType_ES, PIIType_DE, PIIType, PIIType_IT
from ..services.analyzers.presidio_analysis import (
    PresidioPIIAnalyzer,
)
from ..services.assessment_service import (
    PIIAssessmentService,
)
from ..utils.statistics_util import (
    get_mean,
    get_standard_deviation,
    get_variance,
    get_mode,
    get_median,
)

from ..utils.logging import timed_operation

from ..config import (
    DEFAULT_ANALYSIS_MODE,
    DEFAULT_TOKEN_REPLACEMENT_VALUE,
)
from ..models.common import (
    AnalysisProviderType,
    RiskLevel,
    RiskLevel_GDPR,
)


class PIIAnalysisService:
    def __init__(
        self,
        pii_token_replacement_value: str = DEFAULT_TOKEN_REPLACEMENT_VALUE,
        analysis_provider: str = AnalysisProviderType.PRESIDIO.name,
        language_code: str = "en",
        pii_mapper=None,
        filter_detection: bool = True,
    ):
        """
        PIIAnalysisService constructor.
        @param pii_token_replacement_value: PII Token replacement string (default is <REDACTED>)
        @param analysis_provider: Default provider is PRESIDIO, pass in another analysis provider
        when using the adapters.
        """
        self._analysis_provider = analysis_provider
        self._language_code = language_code
        self._pii_assessment_service = PIIAssessmentService(pii_mapper=pii_mapper)
        self._analyzer = (
            PresidioPIIAnalyzer(
                pii_token_replacement_value=pii_token_replacement_value,
                language=language_code,
                pii_mapper=pii_mapper,
            )
            if analysis_provider == AnalysisProviderType.PRESIDIO.name
            else None
        )
        self.pii_mapper = pii_mapper
        self.filter_detection = filter_detection

    @timed_operation
    def analyze_item(
        self,
        text: str,
        metadata: dict = None,
        language_code: str = "en",
        score_threshold: float = 0.4,
    ) -> AnalysisResult | AnalysisResult_v2:
        """
        Runs an analysis given an analysis provider, text, and language code. This method defaults
        to all entity types when using presidio analyzer. Will return an AnalysisResultList object.

        @param text: input text to analyze
        @param language_code: "en" is default value
        @param metadata: dict - {
                                    "location": True
                                }
        @return: AnalysisResult
        """

        analysis, sanitized_text = self._perform_text_analysis(
            text=text, language_code=language_code, score_threshold=score_threshold
        )

        if metadata is not None:
            # Retrieve analyses for metadata entries
            analysis.extend(self.analyze_metadata(metadata=metadata))

        if self.pii_mapper.version == "v1":
            return AnalysisResult(
                index=0,
                analysis=analysis,
                sanitized_text=sanitized_text,
                risk_score_mean=get_mean(
                    [item.risk_assessment.risk_level for item in analysis]
                ),
            )
        elif self.pii_mapper.version == "v2":
            return AnalysisResult_v2(
                index=0,
                analysis=analysis,
                sanitized_text=sanitized_text,
                risk_score_mean=get_mean(
                    [item.risk_assessment.risk_level for item in analysis]
                ),
            )

    @timed_operation
    def analyze_collection(
        self,
        texts: Optional[List[str]] = None,
        data: Optional[pd.DataFrame] = None,
        language_code: str = "en",
        collection_name: str = "",
        collection_type: str = "population",
        score_threshold: float = 0.4,
        filter_detection: bool = True,
    ) -> AnalysisResultSet:
        """
        Runs an analysis given an analysis provider, text, and language code. This method defaults
        to all entity types when using presidio analyzer. Will return an AnalysisResultList object.

        @param texts: List[str] - input texts to analyze
        @param data: dataframe - dataframe of text and metadata where text is a string and metadata is a dict
        @param language_code: str - "en" is default value
        @param collection_name: str - name of population or collection
        @param collection_type: str - population or sample
        @return: AnalysisResultList
        """

        # Will raise exceptions or invalid input
        self._validate_data(texts, data)
        self._language_code = language_code

        if self.pii_mapper.version == "v1":
            analysis_set: List[AnalysisResult] = []
        elif self.pii_mapper.version == "v2":
            analysis_set: List[AnalysisResult_v2] = []

        if data is not None:
            data = data.reset_index()

            analysis_set = [
                self._analyze_data_collection_row(idx, collection_entry)
                for idx, collection_entry in data.iterrows()
            ]

        if texts:
            analysis_set = [
                self._analyze_text_collection_item(
                    idx,
                    collection_entry,
                    score_threshold=score_threshold,
                    filter_detection=filter_detection,
                )
                for idx, collection_entry in enumerate(texts)
            ]

        return self._build_analysis_result_set(
            collection_name=collection_name,
            collection_type=collection_type,
            analysis_set=analysis_set,
        )

    def _analyze_data_collection_row(self, idx, collection_row):
        """
        Parallelized task to process dataframe
        @param idx:
        @param collection_row:
        @return:
        """
        analysis, sanitized_text = self._perform_text_analysis(
            language_code=self._language_code,
            text=collection_row["text"],
        )

        if collection_row["metadata"] is not None:
            # Perform analyses for metadata entries
            analysis.extend(self.analyze_metadata(metadata=collection_row["metadata"]))

        return self._format_result_set_item(
            analysis_items=analysis,
            sanitized_text=sanitized_text,
            index=idx,
            mapper=self.pii_mapper,
        )

    def _analyze_text_collection_item(
        self, idx, text, score_threshold: float = 0.01, filter_detection: bool = True
    ):
        """
        Parallelized task to text array
        @param idx:
        @param text:
        @return:
        """

        analysis, sanitized_text = self._perform_text_analysis(
            language_code=self._language_code,
            text=text,
            score_threshold=score_threshold,
            filter_detection=filter_detection,
        )

        return self._format_result_set_item(
            analysis_items=analysis,
            sanitized_text=sanitized_text,
            index=idx,
            mapper=self.pii_mapper,
        )

    @timed_operation
    def analyze_detection_collection(
        self,
        detection_collection: List[DetectionResult],
        collection_name: str = "",
        collection_type: str = "population",
    ) -> AnalysisResultSet | AnalysisResultItem_v2:
        """
        Transforms a set of Detection Results to an AnalysisResultSet with RiskAssessments for all detections
        found for every string/document. Each analysis result is provided an index to aid in tracking the
        string/document transformed.

        @param detection_collection: List[DetectionResult] - Set of detection results
        @param collection_name: str - name of collection
        @param collection_type: str - population(default) or sample
        @return: AnalysisResultList
        """
        if self.pii_mapper.version == "v1":
            analysis_set: List[AnalysisResult] = []
        elif self.pii_mapper.version == "v2":
            analysis_set: List[AnalysisResult_v2] = []
        for i, detection_result in enumerate(detection_collection):
            analysis_set.append(
                self.analyze_detection_result(
                    detection_result=detection_result, index=i
                )
            )

        return self._build_analysis_result_set(
            collection_name=collection_name,
            collection_type=collection_type,
            analysis_set=analysis_set,
        )

    @timed_operation
    def analyze_detection_result(
        self, detection_result: DetectionResult, index: int = 0
    ) -> AnalysisResult:
        """
        Transforms a Detection Result to an AnalysisResult with RiskAssessments for all detections
        found in a string/document.

        @param detection_result:
        @param index: (Optional) the current index of the detection result to transform
        @return: AnalysisResult
        """
        detection_analyses = [
            self.analyze_detection_result_item(detection_result_item=detection)
            for detection in detection_result.detections
        ]
        return AnalysisResult(
            index=index,
            analysis=detection_analyses,
            risk_score_mean=get_mean(
                [analysis.risk_assessment.risk_level for analysis in detection_analyses]
            ),
        )

    @timed_operation
    def analyze_detection_result_item(
        self,
        detection_result_item: DetectionResultItem,
    ) -> AnalysisResultItem | AnalysisResultItem_v2:
        """
        Transforms a Detection Result Item to an AnalysisResultItem with its associated RiskAssessment for the singular
        detection within a string/document.

        @param detection_result_item:
        @return:  AnalysisResultItem
        """
        if self.pii_mapper.version == "v1":
            return AnalysisResultItem(
                detection=detection_result_item,
                risk_assessment=self._pii_assessment_service.assess_pii_type(
                    detected_pii_type=detection_result_item.entity_type.upper()
                ),
            )
        elif self.pii_mapper.version == "v2":
            return AnalysisResultItem_v2(
                detection=detection_result_item,
                risk_assessment=self._pii_assessment_service.assess_pii_type(
                    detected_pii_type=detection_result_item.entity_type.upper()
                ),
            )

    def _perform_text_analysis(
        self,
        text: str,
        language_code: str = "en",
        score_threshold: float = 0.4,
        filter_detection: bool = True,
    ) -> Tuple[List[AnalysisResultItem] | List[AnalysisResultItem_v2], str]:
        """
        Transforms detections into AnalysisResult objects

        @param text: input text to analyze
        @param language_code: "en" is default value
        @return: Tuple[List[AnalysisResult], str]
        """

        def get_entities(PIIType, list_pii):
            """
            Transforms PIIType enum to list of strings according the definitive list of PII in PIImapper dataframe. This can be modified for weights
            @param PIIType:
            @param list_pii:
            @return:
            """
            list_entities = []
            for pii_type in PIIType:
                if pii_type.value in list_pii:
                    list_entities.append(pii_type.value)
            return list_entities

        if self._analysis_provider.upper() == AnalysisProviderType.PRESIDIO.name:
            # get list of definitive list of PII entities in PIIMapper dataframe. Risk model

            list_pii = list(self.pii_mapper._pii_mapping_data_frame.PII_Type.unique())
            if language_code == "en":
                detections, sanitized_text = self._analyzer.analyze_item(  # type: ignore
                    entities=get_entities(PIIType, list_pii),
                    text=text,
                    language_code=language_code,
                    score_threshold=score_threshold,
                    filter_detection=filter_detection,
                )
            elif language_code == "es":
                detections, sanitized_text = self._analyzer.analyze_item(  # type: ignore
                    entities=get_entities(PIIType_ES, list_pii),
                    text=text,
                    language_code=language_code,
                    score_threshold=score_threshold,
                    filter_detection=self.filter_detection,
                )
            elif language_code == "de":
                detections, sanitized_text = self._analyzer.analyze_item(  # type: ignore
                    entities=get_entities(PIIType_DE, list_pii),
                    text=text,
                    language_code=language_code,
                    score_threshold=score_threshold,
                    filter_detection=self.filter_detection,
                )
            elif language_code == "it":
                detections, sanitized_text = self._analyzer.analyze_item(  # type: ignore
                    entities=get_entities(PIIType_IT, list_pii),
                    text=text,
                    language_code=language_code,
                    score_threshold=score_threshold,
                    filter_detection=self.filter_detection,
                )
        elif (
            self._analysis_provider.upper() == AnalysisProviderType.AZURE.name
            or self._analysis_provider.upper() == AnalysisProviderType.AWS.name
        ):
            raise AttributeError(
                "Unsupported operation. Use detection converters followed by analyze_detection_result()."
            )
        else:
            raise AttributeError(
                "Unsupported operation. Only the Presidio analyzer is supported at this time."
            )
        if self.pii_mapper.version == "v1":
            return (
                [
                    AnalysisResultItem(
                        detection=detection,
                        risk_assessment=self._pii_assessment_service.assess_pii_type(
                            detected_pii_type=detection.entity_type.upper()
                        ),
                    )
                    for detection in detections
                ]
                if detections
                else [
                    AnalysisResultItem(detection=None, risk_assessment=RiskAssessment())
                ]
            ), sanitized_text
        elif self.pii_mapper.version == "v2":
            return (
                [
                    AnalysisResultItem_v2(
                        detection=detection,
                        risk_assessment=self._pii_assessment_service.assess_pii_type(
                            detected_pii_type=detection.entity_type.upper()
                        ),
                    )
                    for detection in detections
                ]
                if detections
                else [
                    AnalysisResultItem_v2(
                        detection=None, risk_assessment=RiskAssessment_v2()
                    )
                ]
            ), sanitized_text

    @timed_operation
    def analyze_metadata(self, metadata: dict):
        """
        Create an analysis result item per metadata entry

        @param metadata:
        @return:
        """
        if self.pii_mapper.version == "v1":
            analysis_result_items: List[AnalysisResultItem] = []
        elif self.pii_mapper.version == "v2":
            analysis_result_items: List[AnalysisResultItem_v2] = []
        for key, value in metadata.items():
            if value is True:
                metadata_pii_mapping = (
                    self.pii_mapper.convert_metadata_type_to_common_pii_type(key)
                )
                if metadata_pii_mapping:
                    # Run analyses on supported metadata types only
                    detection = DetectionResultItem(
                        entity_type=metadata_pii_mapping.name
                    )
                    if self.pii_mapper.version == "v1":
                        analysis_item = AnalysisResultItem(
                            detection=detection,
                            risk_assessment=self._pii_assessment_service.assess_pii_type(
                                detected_pii_type=detection.entity_type.upper()
                            ),
                        )
                    elif self.pii_mapper.version == "v2":
                        analysis_item = AnalysisResultItem_v2(
                            detection=detection,
                            risk_assessment=self._pii_assessment_service.assess_pii_type(
                                detected_pii_type=detection.entity_type.upper()
                            ),
                        )
                    analysis_result_items.append(analysis_item)

        return analysis_result_items

    @staticmethod
    def summarize_analysis_result_items(
        analyses: List[AnalysisResultItem] | List[AnalysisResultItem_v2],
        index=0,
        mapper=None,
    ):
        """
        Summarize analysis result items into a singular AnalysisResult object

        @param analyses:
        @param index:
        @return:
        """
        if mapper.version == "v1":
            return AnalysisResult(
                index=index,
                analysis=analyses,
                risk_score_mean=get_mean(
                    [analysis.risk_assessment.risk_level for analysis in analyses]
                ),
            )
        elif mapper.version == "v2":
            return AnalysisResult_v2(
                index=index,
                analysis=analyses,
                risk_score_gdpr_mean=get_mean(
                    [analysis.risk_assessment.risk_level_gdpr for analysis in analyses]
                ),
                risk_score_pii_mean=get_mean(
                    [analysis.risk_assessment.risk_level_pii for analysis in analyses]
                ),
            )

    def _build_analysis_result_set(
        self,
        analysis_set: List[AnalysisResult],
        collection_name: str = "",
        collection_type: str = DEFAULT_ANALYSIS_MODE,
    ):
        (
            detected_types,
            detected_type_frequencies,
        ) = self._pii_assessment_service.get_detected_pii_types(analysis_set)
        if self.pii_mapper.version == "v1":
            collection_risk_score_means = [
                analysis.risk_score_mean for analysis in analysis_set
            ]

            return AnalysisResultSet(
                collection_name=collection_name,
                analyses=analysis_set,
                risk_score_mean=get_mean(collection_risk_score_means),
                risk_scores=collection_risk_score_means,
                risk_score_standard_deviation=get_standard_deviation(
                    collection_risk_score_means, collection_type
                ),
                risk_score_variance=get_variance(
                    collection_risk_score_means, collection_type
                ),
                risk_score_mode=get_mode(collection_risk_score_means),
                risk_score_median=get_median(collection_risk_score_means),
                detection_count=self._pii_assessment_service.get_detected_pii_count(
                    analysis_set
                ),
                detected_pii_type_frequencies=detected_type_frequencies,
                detected_pii_types=detected_types,
            )
        elif self.pii_mapper.version == "v2":
            """ "risk_score_gdpr_mean": self.risk_score_gdpr_mean,
            "risk_score_pii_mean": self.risk_score_pii_mean,
            """
            collection_risk_score_means_gdpr = [
                analysis.risk_score_gdpr_mean for analysis in analysis_set
            ]
            collection_risk_score_means_pii = [
                analysis.risk_score_pii_mean for analysis in analysis_set
            ]

            return AnalysisResultSet_v2(
                collection_name=collection_name,
                analyses=analysis_set,
                risk_score_mean_gdpr=get_mean(collection_risk_score_means_gdpr),
                risk_scores_gdpr=collection_risk_score_means_gdpr,
                risk_score_standard_deviation_gdpr=get_standard_deviation(
                    collection_risk_score_means_gdpr, collection_type
                ),
                risk_score_variance_gdpr=get_variance(
                    collection_risk_score_means_gdpr, collection_type
                ),
                risk_score_mode_gdpr=get_mode(collection_risk_score_means_gdpr),
                risk_score_median_gdpr=get_median(collection_risk_score_means_gdpr),
                risk_score_mean_pii=get_mean(collection_risk_score_means_pii),
                risk_scores_pii=collection_risk_score_means_pii,
                risk_score_standard_deviation_pii=get_standard_deviation(
                    collection_risk_score_means_pii, collection_type
                ),
                risk_score_variance_pii=get_variance(
                    collection_risk_score_means_pii, collection_type
                ),
                risk_score_mode_pii=get_mode(collection_risk_score_means_pii),
                risk_score_median_pii=get_median(collection_risk_score_means_pii),
                detection_count=self._pii_assessment_service.get_detected_pii_count(
                    analysis_set
                ),
                detected_pii_type_frequencies=detected_type_frequencies,
                detected_pii_types=detected_types,
            )

    @staticmethod
    def _format_result_set_item(
        analysis_items: List[AnalysisResultItem] | List[AnalysisResultItem_v2],
        sanitized_text: str = "",
        index: int = 0,
        mapper=None,
    ) -> AnalysisResult | AnalysisResult_v2:
        """
        Formats the analysis items for a single row in a collection to an AnalysisResult object
        @param analysis_items:
        @param index:
        @return:
        """
        if mapper.version == "v1":
            return AnalysisResult(
                index=index,
                analysis=analysis_items,
                sanitized_text=sanitized_text,
                risk_score_mean=(
                    get_mean(
                        [
                            analysis.risk_assessment.risk_level
                            for analysis in analysis_items
                        ]
                    )
                    if analysis_items
                    else float(RiskLevel.LEVEL_ONE.value)
                ),
            )
        elif mapper.version == "v2":
            return AnalysisResult_v2(
                index=index,
                analysis=analysis_items,
                sanitized_text=sanitized_text,
                risk_score_gdpr_mean=get_mean(
                    [
                        analysis.risk_assessment.risk_level_gdpr
                        for analysis in analysis_items
                    ]
                ),
                risk_score_pii_mean=(
                    get_mean(
                        [
                            analysis.risk_assessment.risk_level_pii
                            for analysis in analysis_items
                        ]
                    )
                    if analysis_items
                    else float(RiskLevel_GDPR.VERY_LOW.value)
                ),
            )

    @staticmethod
    def _validate_data(texts, data):
        """
        Validates text and data types and shapes passed in for collection analyses
        @param texts:
        @param data:
        @return:
        """
        if texts and data is not None:
            raise AttributeError("Cannot supply both 'texts' and 'data' params.")

        if texts and not isinstance(texts, list):
            raise AttributeError("'texts' param must be a list of strings.")

        if data is not None and isinstance(data, pd.DataFrame):
            if "text" not in data and "metadata" not in data:
                raise AttributeError(
                    "Data shape error. 'text' and 'metadata' columns are required."
                )

        if data is not None and not isinstance(data, pd.DataFrame):
            raise AttributeError("Data param must be a dataframe.")
