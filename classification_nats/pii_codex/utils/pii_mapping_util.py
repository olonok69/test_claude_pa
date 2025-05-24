# pylint: disable=broad-except, unused-variable
from typing import Optional
from ..models.aws_pii import AWSComprehendPIIType
from ..models.azure_pii import AzurePIIType
from ..models.common import (
    RiskLevel,
    ClusterMembershipType,
    HIPAACategory,
    DHSCategory,
    NISTCategory,
    PIIType,
    MetadataType,
    RiskLevelDefinition,
    RiskLevel_Identificable_GDPR,
    RiskLevel_Identificable_PII,
    RiskLevel_GDPR,
    RiskLevel_PII,
    PIICategory,
    GDPRCategory,
)
from ..models.analysis import RiskAssessment, RiskAssessment_v2
from ..models.microsoft_presidio_pii import MSFTPresidioPIIType

from .file_util import (
    open_pii_type_mapping_csv,
    open_pii_type_mapping_csv_test,
    open_pii_type_mapping_csv_reload,
)


class PIIMapper:
    """
    Mapping NER entities to the Different RISK models, PII, GDPR , NIST
    """

    def __init__(
        self,
        version: str = "v1",
        mapping_file_name: str = "pii_type_mappings",
        test=False,
        reload=False,
        weigths=None,
    ):
        if test and reload == False:
            self._pii_mapping_data_frame = open_pii_type_mapping_csv_test(
                mapping_file_version=version, mapping_file_name=mapping_file_name
            )
        elif test == False and reload == False:
            self._pii_mapping_data_frame = open_pii_type_mapping_csv(
                mapping_file_version=version, mapping_file_name=mapping_file_name
            )
        elif test == False and reload == True:
            self._pii_mapping_data_frame = open_pii_type_mapping_csv_reload(
                mapping_file_version=version,
                mapping_file_name=mapping_file_name,
                weignts=weigths,
            )
        self.mapping_file_name = mapping_file_name
        self.version = version

    def map_pii_type(self, pii_type: str):
        """
        Maps the PII Type to a full RiskAssessment including categories it belongs to, risk level, and
        its location in the text. This cross-references some of the types listed by Milne et al. (2016)

        @param pii_type:
        @return:
        """

        information_detail_lookup = self._pii_mapping_data_frame[
            self._pii_mapping_data_frame.PII_Type == pii_type
        ]

        # Retrieve the risk_level name by the value of the risk definition enum entry
        if information_detail_lookup.empty:
            raise AttributeError(
                f"An error occurred while processing the detected entity {pii_type}"
            )
        if self.version == "v1":
            risk_level_definition = RiskLevelDefinition(
                information_detail_lookup.Risk_Level.item()
            )

            return RiskAssessment(
                pii_type_detected=pii_type,
                risk_level=RiskLevel[risk_level_definition.name].value,
                risk_level_definition=risk_level_definition.value,
                cluster_membership_type=ClusterMembershipType(
                    information_detail_lookup.Cluster_Membership_Type.item()
                ).value,
                hipaa_category=HIPAACategory[
                    information_detail_lookup.HIPAA_Protected_Health_Information_Category.item()
                ].value,
                dhs_category=DHSCategory(
                    information_detail_lookup.DHS_Category.item()
                ).value,
                nist_category=NISTCategory(
                    information_detail_lookup.NIST_Category.item()
                ).value,
            )
        elif self.version == "v2":
            risk_level_definition_GDPR = RiskLevel_Identificable_GDPR(
                information_detail_lookup.Risk_Level_GDPR.item()
            )
            risk_level_definition_PII = RiskLevel_Identificable_PII(
                information_detail_lookup.Risk_Level_PII.item()
            )
            return RiskAssessment_v2(
                pii_type_detected=str(pii_type),
                country=information_detail_lookup.Country.values[0],
                pii_category=str(
                    PIICategory(information_detail_lookup.PII_Category.item()).value
                ),
                gdpr_category=str(
                    GDPRCategory(information_detail_lookup.GDPR_Category.item()).value
                ),
                risk_level_gdpr=RiskLevel_GDPR[risk_level_definition_GDPR.name].value,
                risk_level_pii=RiskLevel_PII[risk_level_definition_PII.name].value,
                risk_level_gdpr_definition=str(
                    RiskLevel_Identificable_GDPR[risk_level_definition_GDPR.name].value
                ),
                risk_level_pii_definition=str(
                    RiskLevel_Identificable_PII[risk_level_definition_PII.name].value
                ),
                cluster_membership_type=str(
                    ClusterMembershipType(
                        information_detail_lookup.Cluster_Membership_Type.item()
                    ).value
                ),
                dhs_category=str(
                    DHSCategory(information_detail_lookup.DHS_Category.item()).value
                ),
                nist_category=str(
                    NISTCategory(information_detail_lookup.NIST_Category.item()).value
                ),
                hipaa_category=str(
                    HIPAACategory(
                        information_detail_lookup.HIPAA_Protected_Health_Information_Category.item()
                    ).value
                ),
                gdpr_sensitivity=int(
                    information_detail_lookup.GDPR_Sensitivity.values[0]
                ),
                gdpr_likelihood=int(
                    information_detail_lookup.GRPR_Likelihood.values[0]
                ),
                gdpr_impact=int(information_detail_lookup.GDPR_Impact.values[0]),
                gdpr_importance_weighting=float(
                    information_detail_lookup.GDPR_Importance_Weighting.values[0]
                ),
                gdpr_risk_score=float(
                    information_detail_lookup.GDPR_Risk_Score.values[0]
                ),
                pii_sensitivity=int(
                    information_detail_lookup.PII_Sensitivity_Score.values[0]
                ),
                pii_likelihood=int(
                    information_detail_lookup.PII_Likelihood_Score.values[0]
                ),
                pii_impact=int(information_detail_lookup.PII_Impact_Score.values[0]),
                pii_importance_weighting=float(
                    information_detail_lookup.PII_Importance_Weighting.values[0]
                ),
                pii_risk_score=float(
                    information_detail_lookup.PII_Risk_Score.values[0]
                ),
            )

    @classmethod
    def convert_common_pii_to_msft_presidio_type(
        cls, pii_type: PIIType
    ) -> MSFTPresidioPIIType:
        """
        Converts a common PII Type to a MSFT Presidio Type
        @param pii_type:
        @return:
        """

        try:
            converted_type = MSFTPresidioPIIType[pii_type.name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception {ex}"
            )

        return converted_type

    @classmethod
    def convert_common_pii_to_azure_pii_type(cls, pii_type: PIIType) -> AzurePIIType:
        """
        Converts a common PII Type to an Azure PII Type
        @param pii_type:
        @return:
        """
        try:
            return AzurePIIType[pii_type.name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception {ex}"
            )

    @classmethod
    def convert_common_pii_to_aws_comprehend_type(
        cls,
        pii_type: PIIType,
    ) -> AWSComprehendPIIType:
        """
        Converts a common PII Type to an AWS PII Type
        @param pii_type:
        @return:
        """
        try:
            return AWSComprehendPIIType[pii_type.name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception: {ex}"
            )

    @classmethod
    def convert_azure_pii_to_common_pii_type(cls, pii_type: str) -> PIIType:
        """
        Converts an Azure PII Type to a common PII Type
        @param pii_type:
        @return:
        """
        try:
            if pii_type == AzurePIIType.USUK_PASSPORT_NUMBER.value:
                # Special case, map to USUK for all US and UK Passport types
                return PIIType.US_PASSPORT_NUMBER

            return PIIType[AzurePIIType(pii_type).name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception: {ex}"
            )

    @classmethod
    def convert_aws_comprehend_pii_to_common_pii_type(
        cls,
        pii_type: str,
    ) -> PIIType:
        """
        Converts an AWS PII Type to a common PII Type
        @param pii_type: str from AWS Comprehend (maps to value of AWSComprehendPIIType)
        @return:
        """
        try:
            return PIIType[AWSComprehendPIIType(pii_type).name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception: {ex}"
            )

    @classmethod
    def convert_msft_presidio_pii_to_common_pii_type(
        cls,
        pii_type: str,
    ) -> PIIType:
        """
        Converts a Microsoft Presidio PII Type to a common PII Type
        @param pii_type: str from Presidio (maps to value of PIIType)
        @return:
        """
        try:
            return PIIType[MSFTPresidioPIIType(pii_type).name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception: {ex}"
            )

    @classmethod
    def convert_metadata_type_to_common_pii_type(
        cls, metadata_type: str
    ) -> Optional[PIIType]:
        """
        Converts metadata type str entry to common PII type
        @param metadata_type:
        @return: PIIType
        """

        try:
            if metadata_type.lower() == "name":
                return PIIType.PERSON

            if metadata_type.lower() == "user_id":
                # If dealing with public data, user_id can be used to pull down
                # social network profile
                return PIIType.SOCIAL_NETWORK_PROFILE

            return PIIType[MetadataType(metadata_type.lower()).name]
        except Exception as ex:
            raise AttributeError(
                f"The current version does not support this PII Type conversion. Exception: {ex}"
            )
