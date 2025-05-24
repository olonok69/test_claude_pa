# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Counter, Optional


from .common import (
    RiskLevel,
    RiskLevelDefinition,
    RiskLevel_Identificable_GDPR,
    RiskLevel_Identificable_PII,
    RiskLevel_GDPR,
    RiskLevel_PII,
)

# DATACLASSES PII detection, risk assessment, and analysis models


@dataclass
class RiskAssessment:
    pii_type_detected: Optional[str] = None
    risk_level: int = RiskLevel.LEVEL_ONE.value
    risk_level_definition: str = (
        RiskLevelDefinition.LEVEL_ONE.value
    )  # Default if it's not semi or fully identifiable
    cluster_membership_type: Optional[str] = None
    hipaa_category: Optional[str] = None
    dhs_category: Optional[str] = None
    nist_category: Optional[str] = None


@dataclass
class RiskAssessment_v2:
    pii_type_detected: Optional[str] = None
    country: Optional[str] = None
    risk_level_gdpr_definition: str = RiskLevel_Identificable_GDPR.MEDIUM.value
    risk_level_gdpr: int = RiskLevel_GDPR.MEDIUM.value
    gdpr_sensitivity: Optional[str] = None
    gdpr_likelihood: Optional[str] = None
    gdpr_impact: Optional[str] = None
    gdpr_importance_weighting: Optional[str] = None
    gdpr_risk_score: Optional[str] = None
    risk_level_pii_definition: str = RiskLevel_Identificable_PII.MEDIUM.value
    risk_level_pii: int = RiskLevel_PII.MEDIUM.value
    pii_sensitivity: Optional[str] = None
    pii_likelihood: Optional[str] = None
    pii_impact: Optional[str] = None
    pii_importance_weighting: Optional[str] = None
    pii_risk_score: Optional[str] = None
    cluster_membership_type: Optional[str] = None
    dhs_category: Optional[str] = None
    nist_category: Optional[str] = None
    pii_category: Optional[str] = None
    gdpr_category: Optional[str] = None
    hipaa_category: Optional[str] = None


@dataclass
class RiskAssessmentList:
    risk_assessments: List[RiskAssessment]
    average_risk_score: float


@dataclass
class RiskAssessmentList_v2:
    risk_assessments: List[RiskAssessment_v2]
    average_risk_score_pii: float
    average_risk_score_gdpr: float


@dataclass
class DetectionResultItem:
    """
    Type associated with a singular PII detection (e.g. detection of an email in a string), its associated risk score,
    and where it is located in a string.
    """

    entity_type: str
    score: float = 0.0  # metadata detections don't have confidence score values
    start: int = 0  # metadata detections don't have offset values
    end: int = 0  # metadata detections don't have offset values


@dataclass
class DetectionResult:
    detections: List[DetectionResultItem]
    index: int = 0


@dataclass
class AnalysisResultItem:
    """
    The results associated to a single detection of a single string (e.g. Social Media Post, SMS, etc.)
    """

    detection: Optional[DetectionResultItem]
    risk_assessment: RiskAssessment

    def to_dict(self):
        return {
            "riskAssessment": self.risk_assessment.__dict__,
            "detection": self.detection.__dict__,
        }

    def to_flattened_dict(self):
        assessment = self.risk_assessment.__dict__.copy()

        if self.detection:
            assessment.update(self.detection.__dict__)

        return assessment


@dataclass
class AnalysisResultItem_v2:
    """
    The results associated to a single detection of a single string (e.g. Social Media Post, SMS, etc.)
    """

    detection: Optional[DetectionResultItem]
    risk_assessment: RiskAssessment_v2

    def to_dict(self):
        return {
            "riskAssessment": self.risk_assessment.__dict__,
            "detection": self.detection.__dict__,
        }

    def to_flattened_dict(self):
        assessment = self.risk_assessment.__dict__.copy()

        if self.detection:
            assessment.update(self.detection.__dict__)

        return assessment


@dataclass
class AnalysisResult:
    """
    The analysis results associated with several detections within a single string (e.g. Social Media Post, SMS, etc.)
    """

    analysis: List[AnalysisResultItem]
    index: int = 0
    risk_score_mean: float = 0.0
    sanitized_text: str = ""

    def to_dict(self):
        return {
            "analysis": [item.to_flattened_dict() for item in self.analysis],
            "index": self.index,
            "risk_score_mean": self.risk_score_mean,
            "sanitized_text": self.sanitized_text,
        }

    def get_detected_types(self) -> List[str]:
        return [pii.detection.entity_type for pii in self.analysis if pii.detection]


@dataclass
class AnalysisResult_v2:
    """
    The analysis results associated with several detections within a single string (e.g. Social Media Post, SMS, etc.)
    """

    analysis: List[AnalysisResultItem_v2]
    index: int = 0
    risk_score_gdpr_mean: float = 0.0
    risk_score_pii_mean: float = 0.0
    sanitized_text: str = ""

    def to_dict(self):
        return {
            "analysis": [item.to_flattened_dict() for item in self.analysis],
            "index": self.index,
            "risk_score_gdpr_mean": self.risk_score_gdpr_mean,
            "risk_score_pii_mean": self.risk_score_pii_mean,
            "sanitized_text": self.sanitized_text,
        }

    def get_detected_types(self) -> List[str]:
        return [pii.detection.entity_type for pii in self.analysis if pii.detection]


@dataclass
class AnalysisResultSet:
    """
    The analysis results associated with a collection of strings or documents (e.g. Social Media Posts, forum thread,
    etc.). Includes most/least detected PII types within the collection, average risk score of analyses,
    """

    analyses: List[AnalysisResult]
    detection_count: int = 0
    detected_pii_types: set[str] = field(default_factory=set)
    detected_pii_type_frequencies: Counter = None  # type: ignore
    risk_scores: List[float] = field(default_factory=list)
    risk_score_mean: float = 1.0  # Default is 1 for non-identifiable
    risk_score_mode: float = 0.0
    risk_score_median: float = 0.0
    risk_score_standard_deviation: float = 0.0
    risk_score_variance: float = 0.0
    collection_name: Optional[str] = (
        None  # Optional ability for analysts to name a set (see analysis storage step in notebooks)
    )
    collection_type: str = "POPULATION"  # Other option is SAMPLE

    def to_dict(self):
        return {
            "collection_name": self.collection_name,
            "collection_type": self.collection_type,
            "analyses": [item.to_dict() for item in self.analyses],
            "detection_count": self.detection_count,
            "risk_scores": self.risk_scores,
            "risk_score_mean": self.risk_score_mean,
            "risk_score_mode": self.risk_score_mode,
            "risk_score_median": self.risk_score_median,
            "risk_score_standard_deviation": self.risk_score_standard_deviation,
            "risk_score_variance": self.risk_score_variance,
            "detected_pii_types": self.detected_pii_types,
            "detected_pii_type_frequencies": dict(self.detected_pii_type_frequencies),
        }


@dataclass
class AnalysisResultSet_v2:
    """
    The analysis results associated with a collection of strings or documents (e.g. Social Media Posts, forum thread,
    etc.). Includes most/least detected PII types within the collection, average risk score of analyses,
    """

    analyses: List[AnalysisResult_v2]
    detection_count: int = 0
    detected_pii_types: set[str] = field(default_factory=set)
    detected_pii_type_frequencies: Counter = None  # type: ignore
    risk_scores_gdpr: List[float] = field(default_factory=list)
    risk_score_mean_gdpr: float = 1.0  # Default is 1 for non-identifiable
    risk_score_mode_gdpr: float = 0.0
    risk_score_median_gdpr: float = 0.0
    risk_score_standard_deviation_gdpr: float = 0.0
    risk_score_variance_gdpr: float = 0.0
    risk_scores_pii: List[float] = field(default_factory=list)
    risk_score_mean_pii: float = 1.0  # Default is 1 for non-identifiable
    risk_score_mode_pii: float = 0.0
    risk_score_median_pii: float = 0.0
    risk_score_standard_deviation_pii: float = 0.0
    risk_score_variance_pii: float = 0.0
    collection_name: Optional[str] = (
        None  # Optional ability for analysts to name a set (see analysis storage step in notebooks)
    )
    collection_type: str = "POPULATION"  # Other option is SAMPLE

    def to_dict(self):
        return {
            "collection_name": self.collection_name,
            "collection_type": self.collection_type,
            "analyses": [item.to_dict() for item in self.analyses],
            "detection_count": self.detection_count,
            "risk_scores_gdpr": self.risk_scores_gdpr,
            "risk_score_mean_gdpr": self.risk_score_mean_gdpr,
            "risk_score_mode_gdpr": self.risk_score_mode_gdpr,
            "risk_score_median_gdpr": self.risk_score_median_gdpr,
            "risk_score_standard_deviation_gdpr": self.risk_score_standard_deviation_gdpr,
            "risk_score_variance_gdpr": self.risk_score_variance_gdpr,
            "risk_scores_pii": self.risk_scores_pii,
            "risk_score_mean_pii": self.risk_score_mean_pii,
            "risk_score_mode_pii": self.risk_score_mode_pii,
            "risk_score_median_pii": self.risk_score_median_pii,
            "risk_score_standard_deviation_pii": self.risk_score_standard_deviation_pii,
            "risk_score_variance_pii": self.risk_score_variance_pii,
            "detected_pii_types": self.detected_pii_types,
            "detected_pii_type_frequencies": dict(self.detected_pii_type_frequencies),
        }
