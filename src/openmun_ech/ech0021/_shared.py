"""eCH-0021 shared implementation for v7/v8.

Contains factory functions that produce namespace-parameterized classes
shared between eCH-0021 v7 and v8. Only namespace URIs differ between
versions; structural logic is identical.

Pattern: ECH0021VersionConfig dataclass + factory functions.
Precedent: eCH-0058 _shared.py (Phase 4b).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Self, Union

from pydantic import Field, field_validator, model_validator

from openmun_ech.core import NS, ECHModel, xml_field
from openmun_ech.ech0010 import (
    ECH0010AddressInformation,
    ECH0010MailAddress,
    ECH0010OrganisationMailAddress,
    ECH0010OrganisationMailAddressInfo,
    ECH0010PersonMailAddress,
)
from openmun_ech.ech0011.enums import LanguageCode
from openmun_ech.ech0011.v8 import ECH0011GeneralPlace, ECH0011PartnerIdOrganisation
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
)

from .enums import (
    CareType,
    KindOfEmployment,
    MrMrs,
    TypeOfRelationship,
    UIDOrganisationIdCategory,
    YesNo,
)


# ============================================================================
# Version Configuration
# ============================================================================


@dataclass(frozen=True)
class ECH0021VersionConfig:
    """Namespace configuration for eCH-0021 version-specific classes."""

    ns: str  # eCH-0021 namespace URI
    ns_ech0010: str  # eCH-0010 namespace URI
    ns_ech0011: str  # eCH-0011 namespace URI
    ns_ech0006: str  # eCH-0006 namespace URI


V7_CONFIG = ECH0021VersionConfig(
    ns=NS.ECH0021_V7,
    ns_ech0010=NS.ECH0010_V5,
    ns_ech0011=NS.ECH0011_V8,
    ns_ech0006=NS.ECH0006_V2,
)

V8_CONFIG = ECH0021VersionConfig(
    ns=NS.ECH0021_V8,
    ns_ech0010=NS.ECH0010_V8,
    ns_ech0011=NS.ECH0011_V9,
    ns_ech0006=NS.ECH0006_V3,
)


# ============================================================================
# Independent Simple Factories (only cfg.ns)
# ============================================================================


def _make_person_additional_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021PersonAdditionalData class parameterized by namespace config."""

    class ECH0021PersonAdditionalData(ECHModel):
        """eCH-0021 Person additional data.

        XML Schema: eCH-0021 personAdditionalData
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'personAdditionalData'

        mr_mrs: Optional[MrMrs] = xml_field('mrMrs', default=None)
        title: Optional[str] = xml_field('title', default=None, max_length=50)
        language_of_correspondance: Optional[LanguageCode] = xml_field(
            'languageOfCorrespondance', default=None,
        )

    return ECH0021PersonAdditionalData


def _make_place_of_origin_addon_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021PlaceOfOriginAddonData class parameterized by namespace config."""

    class ECH0021PlaceOfOriginAddonData(ECHModel):
        """eCH-0021 Place of origin addon data.

        XML Schema: eCH-0021 placeOfOriginAddonDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'placeOfOriginAddonData'

        naturalization_date: Optional[date] = xml_field(
            'naturalizationDate', default=None,
        )
        expatriation_date: Optional[date] = xml_field(
            'expatriationDate', default=None,
        )

    return ECH0021PlaceOfOriginAddonData


def _make_place_of_origin_addon_restricted_undo(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021PlaceOfOriginAddonRestrictedUnDo class.

    XSD restriction of placeOfOriginAddonDataType: only expatriationDate (required).
    Used in eventUndoCitizen (eCH-0020 §3.4.5 Bürgerrechtsentlassung).
    """

    class ECH0021PlaceOfOriginAddonRestrictedUnDo(ECHModel):
        """eCH-0021 Place of origin addon — restricted for undo citizen events.

        XML Schema: eCH-0021 placeOfOriginAddonRestrictedUnDoDataType
        Only expatriationDate (required). naturalizationDate is NOT allowed.
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'placeOfOriginAddonData'

        expatriation_date: date = xml_field('expatriationDate')

    return ECH0021PlaceOfOriginAddonRestrictedUnDo


def _make_armed_forces_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021ArmedForcesData class parameterized by namespace config."""

    class ECH0021ArmedForcesData(ECHModel):
        """eCH-0021 Armed forces data.

        XML Schema: eCH-0021 armedForcesDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'armedForcesData'

        armed_forces_service: Optional[YesNo] = xml_field(
            'armedForcesService', default=None,
        )
        armed_forces_liability: Optional[YesNo] = xml_field(
            'armedForcesLiability', default=None,
        )
        armed_forces_valid_from: Optional[date] = xml_field(
            'armedForcesValidFrom', default=None,
        )

    return ECH0021ArmedForcesData


def _make_civil_defense_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021CivilDefenseData class parameterized by namespace config."""

    class ECH0021CivilDefenseData(ECHModel):
        """eCH-0021 Civil defense data.

        XML Schema: eCH-0021 civilDefenseDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'civilDefenseData'

        civil_defense: Optional[YesNo] = xml_field(
            'civilDefense', default=None,
        )
        civil_defense_valid_from: Optional[date] = xml_field(
            'civilDefenseValidFrom', default=None,
        )

    return ECH0021CivilDefenseData


def _make_fire_service_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021FireServiceData class parameterized by namespace config."""

    class ECH0021FireServiceData(ECHModel):
        """eCH-0021 Fire service data.

        XML Schema: eCH-0021 fireServiceDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'fireServiceData'

        fire_service: Optional[YesNo] = xml_field(
            'fireService', default=None,
        )
        fire_service_liability: Optional[YesNo] = xml_field(
            'fireServiceLiability', default=None,
        )
        fire_service_valid_from: Optional[date] = xml_field(
            'fireServiceValidFrom', default=None,
        )

    return ECH0021FireServiceData


def _make_matrimonial_inheritance_arrangement_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021MatrimonialInheritanceArrangementData class."""

    class ECH0021MatrimonialInheritanceArrangementData(ECHModel):
        """eCH-0021 Matrimonial inheritance arrangement data.

        XML Schema: eCH-0021 matrimonialInheritanceArrangementDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'matrimonialInheritanceArrangementData'

        matrimonial_inheritance_arrangement: YesNo = xml_field(
            'matrimonialInheritanceArrangement',
        )
        matrimonial_inheritance_arrangement_valid_from: Optional[date] = xml_field(
            'matrimonialInheritanceArrangementValidFrom', default=None,
        )

    return ECH0021MatrimonialInheritanceArrangementData


# ============================================================================
# Cross-Namespace Factory (cfg.ns + cfg.ns_ech0011)
# ============================================================================


def _make_marital_data_addon(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021MaritalDataAddon class parameterized by namespace config."""

    class ECH0021MaritalDataAddon(ECHModel):
        """eCH-0021 Marital data addon.

        XML Schema: eCH-0021 maritalDataAddonType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'maritalDataAddon'

        place_of_marriage: Optional[ECH0011GeneralPlace] = xml_field(
            'placeOfMarriage', wrapper=True, child_ns=cfg.ns_ech0011, default=None,
        )

    return ECH0021MaritalDataAddon


# ============================================================================
# Grouped Factory: Job Classes (UIDStructure -> OccupationData -> JobData)
# ============================================================================


def _make_job_classes(cfg: ECH0021VersionConfig) -> tuple:
    """Create UIDStructure, OccupationData, JobData (interdependent).

    Returns:
        Tuple of (ECH0021UIDStructure, ECH0021OccupationData, ECH0021JobData)
    """

    class ECH0021UIDStructure(ECHModel):
        """eCH-0021 UID structure (Swiss business identifier).

        Custom to_xml/from_xml: uidOrganisationId requires zero-padded 9-digit format.

        XML Schema: eCH-0021 uidStructureType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'UID'

        uid_organisation_id_categorie: UIDOrganisationIdCategory = Field(
            ..., description="UID category (CHE=enterprise, ADM=administration)"
        )
        uid_organisation_id: int = Field(
            ..., ge=1, le=999999999, description="9-digit UID organization ID"
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str | None = None,
            element_name: str | None = None,
            wrapper_namespace: str | None = None,
        ) -> ET.Element:
            ns = namespace or self.__xml_ns__
            el_name = element_name or self.__xml_element__
            root_ns = wrapper_namespace or ns

            tag = f'{{{root_ns}}}{el_name}'
            elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

            cat_elem = ET.SubElement(elem, f'{{{ns}}}uidOrganisationIdCategorie')
            cat_elem.text = self.uid_organisation_id_categorie.value

            id_elem = ET.SubElement(elem, f'{{{ns}}}uidOrganisationId')
            id_elem.text = f'{self.uid_organisation_id:09d}'

            return elem

        @classmethod
        def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
            ns = namespace or cls.__xml_ns__

            cat_elem = elem.find(f'{{{ns}}}uidOrganisationIdCategorie')
            id_elem = elem.find(f'{{{ns}}}uidOrganisationId')

            return cls(
                uid_organisation_id_categorie=cat_elem.text,
                uid_organisation_id=int(id_elem.text),
            )

    class ECH0021OccupationData(ECHModel):
        """eCH-0021 Occupation data.

        XML Schema: eCH-0021 occupationDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'occupationData'

        uid: Optional[ECH0021UIDStructure] = xml_field('UID', default=None)
        employer: Optional[str] = xml_field('employer', default=None, max_length=100)
        place_of_work: Optional[ECH0010AddressInformation] = xml_field(
            'placeOfWork', wrapper=True, child_ns=cfg.ns_ech0010, default=None,
        )
        place_of_employer: Optional[ECH0010AddressInformation] = xml_field(
            'placeOfEmployer', wrapper=True, child_ns=cfg.ns_ech0010, default=None,
        )
        occupation_valid_from: Optional[date] = xml_field(
            'occupationValidFrom', default=None,
        )
        occupation_valid_till: Optional[date] = xml_field(
            'occupationValidTill', default=None,
        )

    class ECH0021JobData(ECHModel):
        """eCH-0021 Job data.

        XML Schema: eCH-0021 jobDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'jobData'

        kind_of_employment: KindOfEmployment = xml_field('kindOfEmployment')
        job_title: Optional[str] = xml_field('jobTitle', default=None, max_length=100)
        occupation_data: List[ECH0021OccupationData] = xml_field(
            'occupationData', is_list=True, default_factory=list,
        )

    return ECH0021UIDStructure, ECH0021OccupationData, ECH0021JobData


# ============================================================================
# Grouped Factory: Partner + MaritalRelationship
# ============================================================================


def _make_partner_and_marital(cfg: ECH0021VersionConfig) -> tuple:
    """Create Partner and MaritalRelationship (interdependent).

    Returns:
        Tuple of (ECH0021Partner, ECH0021MaritalRelationship)
    """

    class ECH0021Partner(ECHModel):
        """eCH-0021 Partner information.

        Custom to_xml/from_xml: isinstance dispatch for PersonIdentification
        vs PersonIdentificationLight with different XML element names.

        XML Schema: Inline complexType in maritalRelationshipType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'partner'

        person_identification: Union[
            ECH0044PersonIdentification, ECH0044PersonIdentificationLight
        ] = Field(
            ...,
            description="Person identification of partner (full or light version)",
        )

        address: Optional[ECH0010PersonMailAddress] = Field(
            None, description="Partner's mail address (personMailAddressType per XSD)"
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str | None = None,
            element_name: str | None = None,
            wrapper_namespace: str | None = None,
        ) -> ET.Element:
            ns = namespace or self.__xml_ns__
            el_name = element_name or self.__xml_element__
            root_ns = wrapper_namespace or ns

            tag = f'{{{root_ns}}}{el_name}'
            elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

            # isinstance dispatch: Light before Full (Light is subclass check order)
            if isinstance(self.person_identification, ECH0044PersonIdentificationLight):
                self.person_identification.to_xml(
                    parent=elem,
                    namespace=NS.ECH0044_V4,
                    element_name='personIdentificationPartner',
                    wrapper_namespace=ns,
                )
            else:
                self.person_identification.to_xml(
                    parent=elem,
                    namespace=NS.ECH0044_V4,
                    element_name='personIdentification',
                    wrapper_namespace=ns,
                )

            if self.address:
                self.address.to_xml(
                    parent=elem,
                    namespace=cfg.ns_ech0010,
                    element_name='address',
                    wrapper_namespace=ns,
                )

            return elem

        @classmethod
        def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
            ns = namespace or cls.__xml_ns__

            pers_elem = elem.find(f'{{{ns}}}personIdentification')
            if pers_elem is not None:
                person_id = ECH0044PersonIdentification.from_xml(pers_elem)
            else:
                pers_light_elem = elem.find(f'{{{ns}}}personIdentificationPartner')
                if pers_light_elem is not None:
                    person_id = ECH0044PersonIdentificationLight.from_xml(pers_light_elem)
                else:
                    raise ValueError(
                        "Missing required field: personIdentification "
                        "or personIdentificationPartner"
                    )

            addr_elem = elem.find(f'{{{ns}}}address')

            return cls(
                person_identification=person_id,
                address=ECH0010PersonMailAddress.from_xml(addr_elem, namespace=cfg.ns_ech0010)
                if addr_elem is not None
                else None,
            )

    class ECH0021MaritalRelationship(ECHModel):
        """eCH-0021 Marital relationship.

        XML Schema: eCH-0021 maritalRelationshipType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'maritalRelationship'

        partner: ECH0021Partner = xml_field('partner')
        type_of_relationship: TypeOfRelationship = xml_field('typeOfRelationship')

        @field_validator('type_of_relationship')
        @classmethod
        def validate_marital_relationship_type(
            cls, v: TypeOfRelationship,
        ) -> TypeOfRelationship:
            if v not in (
                TypeOfRelationship.SPOUSE,
                TypeOfRelationship.REGISTERED_PARTNER,
            ):
                raise ValueError(
                    f"Marital relationship must be SPOUSE (1) or "
                    f"REGISTERED_PARTNER (2), got: {v}"
                )
            return v

    return ECH0021Partner, ECH0021MaritalRelationship


# ============================================================================
# Grouped Factory: Guardian Classes
# ============================================================================


def _make_guardian_classes(cfg: ECH0021VersionConfig) -> tuple:
    """Create GuardianMeasureInfo and GuardianRelationship (interdependent).

    Returns:
        Tuple of (ECH0021GuardianMeasureInfo, ECH0021GuardianRelationship)
    """

    class ECH0021GuardianMeasureInfo(ECHModel):
        """eCH-0021 Guardian measure information.

        XML Schema: eCH-0021 guardianMeasureInfoType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'guardianMeasureInfo'

        based_on_law: List[str] = xml_field(
            'basedOnLaw', is_list=True, default_factory=list,
        )
        based_on_law_add_on: Optional[str] = xml_field(
            'basedOnLawAddOn', default=None, min_length=1, max_length=100,
        )
        guardian_measure_valid_from: date = xml_field('guardianMeasureValidFrom')

        @field_validator('based_on_law')
        @classmethod
        def validate_based_on_law(cls, v: List[str]) -> List[str]:
            valid_articles = {
                "306", "310", "311", "312", "327-a", "363", "368", "369",
                "370", "371", "372", "393", "394", "395", "396", "397",
                "398", "399",
            }
            for article in v:
                if article not in valid_articles:
                    raise ValueError(
                        f"Invalid ZGB article '{article}'. "
                        f"Must be one of: {sorted(valid_articles)}"
                    )
            return v

    class ECH0021GuardianRelationship(ECHModel):
        """eCH-0021 Guardian relationship.

        Custom to_xml/from_xml: nested partner element with xs:choice
        (person/personLight/organization) + address inside.

        XML Schema: eCH-0021 guardianRelationshipType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'guardianRelationship'

        guardian_relationship_id: str = Field(
            ..., min_length=1, max_length=36,
            description="Guardian relationship identifier",
        )

        # Partner (optional) — xs:choice: person OR organization
        person_identification: Optional[ECH0044PersonIdentification] = Field(
            None, description="Guardian as person (full identification)"
        )
        person_identification_partner: Optional[ECH0044PersonIdentificationLight] = Field(
            None, description="Guardian as person (light identification)"
        )
        partner_id_organisation: Optional[ECH0011PartnerIdOrganisation] = Field(
            None, description="Guardian as organization (e.g., KESB)"
        )
        partner_address: Optional[ECH0010MailAddress] = Field(
            None, description="Guardian's mailing address (optional)"
        )

        type_of_relationship: TypeOfRelationship = Field(
            ...,
            description="Type of guardian relationship (7-10)",
        )

        guardian_measure_info: ECH0021GuardianMeasureInfo = Field(
            ..., description="Guardian measure information (required)"
        )

        care: Optional[CareType] = Field(None, description="Care arrangement")

        @field_validator('type_of_relationship')
        @classmethod
        def validate_guardian_relationship_type(
            cls, v: TypeOfRelationship,
        ) -> TypeOfRelationship:
            guardian_types = (
                TypeOfRelationship.LEGAL_ASSISTANT,
                TypeOfRelationship.ADVISOR,
                TypeOfRelationship.GUARDIAN,
                TypeOfRelationship.HEALTHCARE_PROXY,
            )
            if v not in guardian_types:
                raise ValueError(
                    f"Guardian relationship must be LEGAL_ASSISTANT (7), "
                    f"ADVISOR (8), GUARDIAN (9), or HEALTHCARE_PROXY (10), "
                    f"got: {v}"
                )
            return v

        @model_validator(mode='after')
        def validate_partner_choice(self) -> Self:
            partner_count = sum([
                self.person_identification is not None,
                self.person_identification_partner is not None,
                self.partner_id_organisation is not None,
            ])
            if partner_count > 1:
                raise ValueError(
                    "Guardian partner must be at most ONE of: "
                    "person_identification, person_identification_partner, "
                    f"or partner_id_organisation. Got {partner_count} partner types."
                )
            return self

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str | None = None,
            element_name: str | None = None,
            wrapper_namespace: str | None = None,
        ) -> ET.Element:
            ns = namespace or self.__xml_ns__
            el_name = element_name or self.__xml_element__
            root_ns = wrapper_namespace or ns

            tag = f'{{{root_ns}}}{el_name}'
            elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

            # guardianRelationshipId (required)
            id_elem = ET.SubElement(elem, f'{{{ns}}}guardianRelationshipId')
            id_elem.text = self.guardian_relationship_id

            # partner (optional) — xs:choice + optional address
            if (
                self.person_identification
                or self.person_identification_partner
                or self.partner_id_organisation
                or self.partner_address
            ):
                partner_elem = ET.SubElement(elem, f'{{{ns}}}partner')

                if self.person_identification:
                    self.person_identification.to_xml(
                        parent=partner_elem,
                        element_name='personIdentification',
                        wrapper_namespace=ns,
                    )
                elif self.person_identification_partner:
                    self.person_identification_partner.to_xml(
                        parent=partner_elem,
                        element_name='personIdentificationPartner',
                        wrapper_namespace=ns,
                    )
                elif self.partner_id_organisation:
                    self.partner_id_organisation.to_xml(
                        parent=partner_elem,
                        tag='partnerIdOrganisation',
                        wrapper_namespace=ns,
                    )

                if self.partner_address:
                    self.partner_address.to_xml(
                        parent=partner_elem,
                        namespace=cfg.ns_ech0010,
                        element_name='address',
                        wrapper_namespace=ns,
                    )

            # typeOfRelationship (required)
            rel_elem = ET.SubElement(elem, f'{{{ns}}}typeOfRelationship')
            rel_elem.text = self.type_of_relationship.value

            # guardianMeasureInfo (required)
            self.guardian_measure_info.to_xml(parent=elem, namespace=ns)

            # care (optional)
            if self.care:
                care_elem = ET.SubElement(elem, f'{{{ns}}}care')
                care_elem.text = self.care.value

            return elem

        @classmethod
        def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
            ns = namespace or cls.__xml_ns__

            # guardianRelationshipId (required)
            id_elem = elem.find(f'{{{ns}}}guardianRelationshipId')
            guardian_relationship_id = id_elem.text

            # partner (optional) — parse xs:choice
            partner_elem = elem.find(f'{{{ns}}}partner')
            person_identification = None
            person_identification_partner = None
            partner_id_organisation = None
            partner_address = None

            if partner_elem is not None:
                person_id_elem = partner_elem.find(f'{{{ns}}}personIdentification')
                if person_id_elem is not None:
                    person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

                person_partner_elem = partner_elem.find(f'{{{ns}}}personIdentificationPartner')
                if person_partner_elem is not None:
                    person_identification_partner = (
                        ECH0044PersonIdentificationLight.from_xml(person_partner_elem)
                    )

                org_elem = partner_elem.find(f'{{{ns}}}partnerIdOrganisation')
                if org_elem is not None:
                    partner_id_organisation = ECH0011PartnerIdOrganisation.from_xml(org_elem)

                addr_elem = partner_elem.find(f'{{{ns}}}address')
                if addr_elem is not None:
                    partner_address = ECH0010MailAddress.from_xml(
                        addr_elem, namespace=cfg.ns_ech0010,
                    )

            # typeOfRelationship (required)
            rel_elem = elem.find(f'{{{ns}}}typeOfRelationship')
            type_of_relationship = TypeOfRelationship(rel_elem.text)

            # guardianMeasureInfo (required)
            measure_elem = elem.find(f'{{{ns}}}guardianMeasureInfo')
            guardian_measure_info = ECH0021GuardianMeasureInfo.from_xml(
                measure_elem, namespace=ns,
            )

            # care (optional)
            care_elem = elem.find(f'{{{ns}}}care')
            care = CareType(care_elem.text) if care_elem is not None else None

            return cls(
                guardian_relationship_id=guardian_relationship_id,
                person_identification=person_identification,
                person_identification_partner=person_identification_partner,
                partner_id_organisation=partner_id_organisation,
                partner_address=partner_address,
                type_of_relationship=type_of_relationship,
                guardian_measure_info=guardian_measure_info,
                care=care,
            )

    return ECH0021GuardianMeasureInfo, ECH0021GuardianRelationship


# ============================================================================
# Cross-Namespace Factory: HealthInsuranceData (cfg.ns + cfg.ns_ech0010)
# ============================================================================


def _make_health_insurance_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021HealthInsuranceData class parameterized by namespace config."""

    class ECH0021HealthInsuranceData(ECHModel):
        """eCH-0021 Health insurance data.

        Custom to_xml/from_xml: nested insurance element with xs:choice
        (insuranceName OR insuranceAddress with organisation+addressInformation).

        XML Schema: eCH-0021 healthInsuranceDataType
        """

        __xml_ns__ = cfg.ns
        __xml_element__ = 'healthInsuranceData'

        health_insured: YesNo = Field(..., description="Health insurance status")

        # Choice: insurance name OR insurance address
        insurance_name: Optional[str] = Field(
            None, max_length=100, description="Insurance company name"
        )
        insurance_address: Optional[ECH0010OrganisationMailAddress] = Field(
            None, description="Insurance company full address",
        )

        health_insurance_valid_from: Optional[date] = Field(None)

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str | None = None,
            element_name: str | None = None,
            wrapper_namespace: str | None = None,
        ) -> ET.Element:
            ns = namespace or self.__xml_ns__
            el_name = element_name or self.__xml_element__
            root_ns = wrapper_namespace or ns

            tag = f'{{{root_ns}}}{el_name}'
            elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

            hi_elem = ET.SubElement(elem, f'{{{ns}}}healthInsured')
            hi_elem.text = self.health_insured.value

            # Insurance: choice of name OR address
            if self.insurance_name or self.insurance_address:
                ins_elem = ET.SubElement(elem, f'{{{ns}}}insurance')

                if self.insurance_name:
                    name_elem = ET.SubElement(ins_elem, f'{{{ns}}}insuranceName')
                    name_elem.text = self.insurance_name
                elif self.insurance_address:
                    addr_wrapper = ET.SubElement(ins_elem, f'{{{ns}}}insuranceAddress')
                    ns_010 = cfg.ns_ech0010

                    self.insurance_address.organisation.to_xml(
                        parent=addr_wrapper,
                        namespace=ns_010,
                        element_name='organisation',
                    )
                    self.insurance_address.address_information.to_xml(
                        parent=addr_wrapper,
                        namespace=ns_010,
                        element_name='addressInformation',
                    )

            if self.health_insurance_valid_from:
                from_elem = ET.SubElement(elem, f'{{{ns}}}healthInsuranceValidFrom')
                from_elem.text = self.health_insurance_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
            ns = namespace or cls.__xml_ns__

            hi_elem = elem.find(f'{{{ns}}}healthInsured')
            ins_elem = elem.find(f'{{{ns}}}insurance')

            insurance_name = None
            insurance_address = None
            if ins_elem is not None:
                name_elem = ins_elem.find(f'{{{ns}}}insuranceName')
                if name_elem is not None:
                    insurance_name = name_elem.text
                else:
                    addr_elem = ins_elem.find(f'{{{ns}}}insuranceAddress')
                    if addr_elem is not None:
                        ns_010 = cfg.ns_ech0010
                        org_elem = addr_elem.find(f'{{{ns_010}}}organisation')
                        addr_info_elem = addr_elem.find(f'{{{ns_010}}}addressInformation')

                        if org_elem is not None and addr_info_elem is not None:
                            org_info = ECH0010OrganisationMailAddressInfo.from_xml(
                                org_elem, namespace=ns_010,
                            )
                            addr_info = ECH0010AddressInformation.from_xml(
                                addr_info_elem, namespace=ns_010,
                            )
                            insurance_address = ECH0010OrganisationMailAddress(
                                organisation=org_info,
                                address_information=addr_info,
                            )

            from_elem = elem.find(f'{{{ns}}}healthInsuranceValidFrom')

            return cls(
                health_insured=YesNo(hi_elem.text),
                insurance_name=insurance_name,
                insurance_address=insurance_address,
                health_insurance_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
            )

    return ECH0021HealthInsuranceData
