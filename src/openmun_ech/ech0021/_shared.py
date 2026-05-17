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
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from openmun_ech.core import NS
from openmun_ech.ech0010 import (
    ECH0010AddressInformation,
    ECH0010MailAddress,
    ECH0010OrganisationMailAddress,
    ECH0010OrganisationMailAddressInfo,
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

    class ECH0021PersonAdditionalData(BaseModel):
        """eCH-0021 Person additional data.

        Contains salutation, title, and language of correspondence.

        XML Schema: eCH-0021 personAdditionalData
        """

        mr_mrs: Optional[MrMrs] = Field(
            None,
            description="Salutation: 1=Mrs/Frau, 2=Mr/Herr (eCH-0010 mrMrsType)",
        )
        title: Optional[str] = Field(
            None,
            max_length=50,
            description="Title (Dr., Prof., etc.) (eCH-0010 titleType)",
        )
        language_of_correspondance: Optional[LanguageCode] = Field(
            None,
            description="Language code: de, fr, it, rm, en (eCH-0011 languageType)",
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "personAdditionalData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.mr_mrs:
                mr_mrs_elem = ET.SubElement(elem, f"{{{namespace}}}mrMrs")
                mr_mrs_elem.text = self.mr_mrs.value

            if self.title:
                title_elem = ET.SubElement(elem, f"{{{namespace}}}title")
                title_elem.text = self.title

            if self.language_of_correspondance:
                lang_elem = ET.SubElement(
                    elem, f"{{{namespace}}}languageOfCorrespondance"
                )
                lang_elem.text = self.language_of_correspondance.value

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021PersonAdditionalData":
            ns = {"eCH-0021": cfg.ns}

            mr_mrs_elem = element.find("eCH-0021:mrMrs", ns)
            title_elem = element.find("eCH-0021:title", ns)
            lang_elem = element.find("eCH-0021:languageOfCorrespondance", ns)

            return cls(
                mr_mrs=MrMrs(mr_mrs_elem.text)
                if mr_mrs_elem is not None
                else None,
                title=title_elem.text if title_elem is not None else None,
                language_of_correspondance=lang_elem.text
                if lang_elem is not None
                else None,
            )

    return ECH0021PersonAdditionalData


def _make_place_of_origin_addon_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021PlaceOfOriginAddonData class parameterized by namespace config."""

    class ECH0021PlaceOfOriginAddonData(BaseModel):
        """eCH-0021 Place of origin addon data.

        Contains naturalization and expatriation dates.

        XML Schema: eCH-0021 placeOfOriginAddonDataType
        """

        naturalization_date: Optional[date] = Field(
            None, description="Date of naturalization"
        )
        expatriation_date: Optional[date] = Field(
            None, description="Date of expatriation"
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "placeOfOriginAddonData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.naturalization_date:
                nat_elem = ET.SubElement(elem, f"{{{namespace}}}naturalizationDate")
                nat_elem.text = self.naturalization_date.isoformat()

            if self.expatriation_date:
                exp_elem = ET.SubElement(elem, f"{{{namespace}}}expatriationDate")
                exp_elem.text = self.expatriation_date.isoformat()

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021PlaceOfOriginAddonData":
            ns = {"eCH-0021": cfg.ns}

            nat_elem = element.find("eCH-0021:naturalizationDate", ns)
            exp_elem = element.find("eCH-0021:expatriationDate", ns)

            return cls(
                naturalization_date=date.fromisoformat(nat_elem.text)
                if nat_elem is not None
                else None,
                expatriation_date=date.fromisoformat(exp_elem.text)
                if exp_elem is not None
                else None,
            )

    return ECH0021PlaceOfOriginAddonData


def _make_armed_forces_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021ArmedForcesData class parameterized by namespace config."""

    class ECH0021ArmedForcesData(BaseModel):
        """eCH-0021 Armed forces data.

        XML Schema: eCH-0021 armedForcesDataType
        """

        armed_forces_service: Optional[YesNo] = None
        armed_forces_liability: Optional[YesNo] = None
        armed_forces_valid_from: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "armedForcesData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.armed_forces_service:
                service_elem = ET.SubElement(
                    elem, f"{{{namespace}}}armedForcesService"
                )
                service_elem.text = self.armed_forces_service.value

            if self.armed_forces_liability:
                liability_elem = ET.SubElement(
                    elem, f"{{{namespace}}}armedForcesLiability"
                )
                liability_elem.text = self.armed_forces_liability.value

            if self.armed_forces_valid_from:
                from_elem = ET.SubElement(
                    elem, f"{{{namespace}}}armedForcesValidFrom"
                )
                from_elem.text = self.armed_forces_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021ArmedForcesData":
            ns = {"eCH-0021": cfg.ns}

            service_elem = element.find("eCH-0021:armedForcesService", ns)
            liability_elem = element.find("eCH-0021:armedForcesLiability", ns)
            from_elem = element.find("eCH-0021:armedForcesValidFrom", ns)

            return cls(
                armed_forces_service=YesNo(service_elem.text)
                if service_elem is not None
                else None,
                armed_forces_liability=YesNo(liability_elem.text)
                if liability_elem is not None
                else None,
                armed_forces_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
            )

    return ECH0021ArmedForcesData


def _make_civil_defense_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021CivilDefenseData class parameterized by namespace config."""

    class ECH0021CivilDefenseData(BaseModel):
        """eCH-0021 Civil defense data.

        XML Schema: eCH-0021 civilDefenseDataType
        """

        civil_defense: Optional[YesNo] = None
        civil_defense_valid_from: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "civilDefenseData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.civil_defense:
                cd_elem = ET.SubElement(elem, f"{{{namespace}}}civilDefense")
                cd_elem.text = self.civil_defense.value

            if self.civil_defense_valid_from:
                from_elem = ET.SubElement(
                    elem, f"{{{namespace}}}civilDefenseValidFrom"
                )
                from_elem.text = self.civil_defense_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021CivilDefenseData":
            ns = {"eCH-0021": cfg.ns}

            cd_elem = element.find("eCH-0021:civilDefense", ns)
            from_elem = element.find("eCH-0021:civilDefenseValidFrom", ns)

            return cls(
                civil_defense=YesNo(cd_elem.text)
                if cd_elem is not None
                else None,
                civil_defense_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
            )

    return ECH0021CivilDefenseData


def _make_fire_service_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021FireServiceData class parameterized by namespace config."""

    class ECH0021FireServiceData(BaseModel):
        """eCH-0021 Fire service data.

        XML Schema: eCH-0021 fireServiceDataType
        """

        fire_service: Optional[YesNo] = None
        fire_service_liability: Optional[YesNo] = None
        fire_service_valid_from: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "fireServiceData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.fire_service:
                fs_elem = ET.SubElement(elem, f"{{{namespace}}}fireService")
                fs_elem.text = self.fire_service.value

            if self.fire_service_liability:
                liability_elem = ET.SubElement(
                    elem, f"{{{namespace}}}fireServiceLiability"
                )
                liability_elem.text = self.fire_service_liability.value

            if self.fire_service_valid_from:
                from_elem = ET.SubElement(
                    elem, f"{{{namespace}}}fireServiceValidFrom"
                )
                from_elem.text = self.fire_service_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021FireServiceData":
            ns = {"eCH-0021": cfg.ns}

            fs_elem = element.find("eCH-0021:fireService", ns)
            liability_elem = element.find("eCH-0021:fireServiceLiability", ns)
            from_elem = element.find("eCH-0021:fireServiceValidFrom", ns)

            return cls(
                fire_service=YesNo(fs_elem.text)
                if fs_elem is not None
                else None,
                fire_service_liability=YesNo(liability_elem.text)
                if liability_elem is not None
                else None,
                fire_service_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
            )

    return ECH0021FireServiceData


def _make_matrimonial_inheritance_arrangement_data(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021MatrimonialInheritanceArrangementData class."""

    class ECH0021MatrimonialInheritanceArrangementData(BaseModel):
        """eCH-0021 Matrimonial inheritance arrangement data.

        XML Schema: eCH-0021 matrimonialInheritanceArrangementDataType
        """

        matrimonial_inheritance_arrangement: YesNo = Field(
            ..., description="Matrimonial inheritance arrangement exists"
        )
        matrimonial_inheritance_arrangement_valid_from: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "matrimonialInheritanceArrangementData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            mia_elem = ET.SubElement(
                elem, f"{{{namespace}}}matrimonialInheritanceArrangement"
            )
            mia_elem.text = self.matrimonial_inheritance_arrangement.value

            if self.matrimonial_inheritance_arrangement_valid_from:
                from_elem = ET.SubElement(
                    elem,
                    f"{{{namespace}}}matrimonialInheritanceArrangementValidFrom",
                )
                from_elem.text = (
                    self.matrimonial_inheritance_arrangement_valid_from.isoformat()
                )

            return elem

        @classmethod
        def from_xml(
            cls, element: ET.Element
        ) -> "ECH0021MatrimonialInheritanceArrangementData":
            ns = {"eCH-0021": cfg.ns}

            mia_elem = element.find(
                "eCH-0021:matrimonialInheritanceArrangement", ns
            )
            from_elem = element.find(
                "eCH-0021:matrimonialInheritanceArrangementValidFrom", ns
            )

            return cls(
                matrimonial_inheritance_arrangement=YesNo(mia_elem.text),
                matrimonial_inheritance_arrangement_valid_from=date.fromisoformat(
                    from_elem.text
                )
                if from_elem is not None
                else None,
            )

    return ECH0021MatrimonialInheritanceArrangementData


# ============================================================================
# Cross-Namespace Factory (cfg.ns + cfg.ns_ech0011)
# ============================================================================


def _make_marital_data_addon(cfg: ECH0021VersionConfig) -> type:
    """Create ECH0021MaritalDataAddon class parameterized by namespace config."""

    class ECH0021MaritalDataAddon(BaseModel):
        """eCH-0021 Marital data addon.

        Contains place of marriage information.

        XML Schema: eCH-0021 maritalDataAddonType
        """

        place_of_marriage: Optional[ECH0011GeneralPlace] = Field(
            None,
            description="Place where marriage occurred (Swiss municipality or foreign country)",
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "maritalDataAddon",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.place_of_marriage:
                # Create wrapper in eCH-0021 namespace
                place_wrapper = ET.SubElement(
                    elem, f"{{{namespace}}}placeOfMarriage"
                )
                # Generate eCH-0011 content
                place_content = self.place_of_marriage.to_xml(
                    namespace=cfg.ns_ech0011
                )
                # Move children to wrapper
                for child in place_content:
                    place_wrapper.append(child)

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021MaritalDataAddon":
            ns = {"eCH-0021": cfg.ns}

            # Look for wrapper in eCH-0021 namespace
            place_elem = element.find("eCH-0021:placeOfMarriage", ns)

            return cls(
                place_of_marriage=ECH0011GeneralPlace.from_xml(
                    place_elem, namespace=cfg.ns_ech0011
                )
                if place_elem is not None
                else None,
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

    class ECH0021UIDStructure(BaseModel):
        """eCH-0021 UID structure (Swiss business identifier).

        XML Schema: eCH-0021 uidStructureType
        """

        uid_organisation_id_categorie: UIDOrganisationIdCategory = Field(
            ..., description="UID category (CHE=enterprise, ADM=administration)"
        )
        uid_organisation_id: int = Field(
            ..., ge=1, le=999999999, description="9-digit UID organization ID"
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "UID",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            cat_elem = ET.SubElement(
                elem, f"{{{namespace}}}uidOrganisationIdCategorie"
            )
            cat_elem.text = self.uid_organisation_id_categorie.value

            id_elem = ET.SubElement(
                elem, f"{{{namespace}}}uidOrganisationId"
            )
            id_elem.text = f"{self.uid_organisation_id:09d}"

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021UIDStructure":
            ns = {"eCH-0021": cfg.ns}

            cat_elem = element.find("eCH-0021:uidOrganisationIdCategorie", ns)
            id_elem = element.find("eCH-0021:uidOrganisationId", ns)

            return cls(
                uid_organisation_id_categorie=cat_elem.text,
                uid_organisation_id=int(id_elem.text),
            )

    class ECH0021OccupationData(BaseModel):
        """eCH-0021 Occupation data.

        XML Schema: eCH-0021 occupationDataType
        """

        uid: Optional[ECH0021UIDStructure] = None
        employer: Optional[str] = Field(None, max_length=100)
        place_of_work: Optional[ECH0010AddressInformation] = None
        place_of_employer: Optional[ECH0010AddressInformation] = None
        occupation_valid_from: Optional[date] = None
        occupation_valid_till: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "occupationData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            if self.uid:
                self.uid.to_xml(parent=elem, namespace=namespace)

            if self.employer:
                emp_elem = ET.SubElement(elem, f"{{{namespace}}}employer")
                emp_elem.text = self.employer

            if self.place_of_work:
                self.place_of_work.to_xml(
                    parent=elem,
                    namespace=cfg.ns_ech0010,
                    element_name="placeOfWork",
                    wrapper_namespace=namespace,
                )

            if self.place_of_employer:
                self.place_of_employer.to_xml(
                    parent=elem,
                    namespace=cfg.ns_ech0010,
                    element_name="placeOfEmployer",
                    wrapper_namespace=namespace,
                )

            if self.occupation_valid_from:
                from_elem = ET.SubElement(
                    elem, f"{{{namespace}}}occupationValidFrom"
                )
                from_elem.text = self.occupation_valid_from.isoformat()

            if self.occupation_valid_till:
                till_elem = ET.SubElement(
                    elem, f"{{{namespace}}}occupationValidTill"
                )
                till_elem.text = self.occupation_valid_till.isoformat()

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021OccupationData":
            ns_0021 = {"eCH-0021": cfg.ns}

            uid_elem = element.find("eCH-0021:UID", ns_0021)
            emp_elem = element.find("eCH-0021:employer", ns_0021)

            # placeOfWork and placeOfEmployer are wrappers in eCH-0021 namespace
            pow_wrapper = element.find("eCH-0021:placeOfWork", ns_0021)
            poe_wrapper = element.find("eCH-0021:placeOfEmployer", ns_0021)

            from_elem = element.find("eCH-0021:occupationValidFrom", ns_0021)
            till_elem = element.find("eCH-0021:occupationValidTill", ns_0021)

            return cls(
                uid=ECH0021UIDStructure.from_xml(uid_elem)
                if uid_elem is not None
                else None,
                employer=emp_elem.text if emp_elem is not None else None,
                place_of_work=ECH0010AddressInformation.from_xml(
                    pow_wrapper, namespace=cfg.ns_ech0010
                )
                if pow_wrapper is not None
                else None,
                place_of_employer=ECH0010AddressInformation.from_xml(
                    poe_wrapper, namespace=cfg.ns_ech0010
                )
                if poe_wrapper is not None
                else None,
                occupation_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
                occupation_valid_till=date.fromisoformat(till_elem.text)
                if till_elem is not None
                else None,
            )

    class ECH0021JobData(BaseModel):
        """eCH-0021 Job data.

        XML Schema: eCH-0021 jobDataType
        """

        kind_of_employment: KindOfEmployment = Field(
            ...,
            description="Kind of employment (employed, self-employed, unemployed, etc.)",
        )
        job_title: Optional[str] = Field(None, max_length=100)
        occupation_data: List[ECH0021OccupationData] = Field(
            default_factory=list
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "jobData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            kind_elem = ET.SubElement(
                elem, f"{{{namespace}}}kindOfEmployment"
            )
            kind_elem.text = self.kind_of_employment.value

            if self.job_title:
                title_elem = ET.SubElement(elem, f"{{{namespace}}}jobTitle")
                title_elem.text = self.job_title

            for occ in self.occupation_data:
                occ.to_xml(parent=elem, namespace=namespace)

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021JobData":
            ns = {"eCH-0021": cfg.ns}

            kind_elem = element.find("eCH-0021:kindOfEmployment", ns)
            title_elem = element.find("eCH-0021:jobTitle", ns)
            occ_elems = element.findall("eCH-0021:occupationData", ns)

            return cls(
                kind_of_employment=KindOfEmployment(kind_elem.text),
                job_title=title_elem.text if title_elem is not None else None,
                occupation_data=[
                    ECH0021OccupationData.from_xml(elem) for elem in occ_elems
                ],
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

    class ECH0021Partner(BaseModel):
        """eCH-0021 Partner information.

        Contains person identification (full or light version) and optional address.
        Used in marital and parental relationships.

        XML Schema: Inline complexType in maritalRelationshipType and parentalRelationshipType
        """

        person_identification: Union[
            ECH0044PersonIdentification, ECH0044PersonIdentificationLight
        ] = Field(
            ...,
            description="Person identification of partner (full or light version)",
        )

        address: Optional[ECH0010MailAddress] = Field(
            None, description="Partner's mail address"
        )

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "partner",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            # Person identification (full or light)
            if isinstance(
                self.person_identification, ECH0044PersonIdentificationLight
            ):
                self.person_identification.to_xml(
                    parent=elem,
                    namespace=NS.ECH0044_V4,
                    element_name="personIdentificationPartner",
                    wrapper_namespace=namespace,
                )
            else:
                self.person_identification.to_xml(
                    parent=elem,
                    namespace=NS.ECH0044_V4,
                    element_name="personIdentification",
                    wrapper_namespace=namespace,
                )

            # Optional address
            if self.address:
                self.address.to_xml(
                    parent=elem,
                    namespace=cfg.ns_ech0010,
                    element_name="address",
                    wrapper_namespace=namespace,
                )

            return elem

        @classmethod
        def from_xml(cls, element: ET.Element) -> "ECH0021Partner":
            ns_0021 = {"eCH-0021": cfg.ns}

            # Try full person identification first
            pers_elem = element.find("eCH-0021:personIdentification", ns_0021)
            if pers_elem is not None:
                person_id = ECH0044PersonIdentification.from_xml(pers_elem)
            else:
                # Try light person identification
                pers_light_elem = element.find(
                    "eCH-0021:personIdentificationPartner", ns_0021
                )
                if pers_light_elem is not None:
                    person_id = ECH0044PersonIdentificationLight.from_xml(
                        pers_light_elem
                    )
                else:
                    raise ValueError(
                        "Missing required field: personIdentification "
                        "or personIdentificationPartner"
                    )

            # Address (wrapper in eCH-0021, content in eCH-0010)
            addr_elem = element.find("eCH-0021:address", ns_0021)

            return cls(
                person_identification=person_id,
                address=ECH0010MailAddress.from_xml(
                    addr_elem, namespace=cfg.ns_ech0010
                )
                if addr_elem is not None
                else None,
            )

    class ECH0021MaritalRelationship(BaseModel):
        """eCH-0021 Marital relationship.

        Contains partner information and type of relationship (married/partnership).

        XML Schema: eCH-0021 maritalRelationshipType
        """

        partner: ECH0021Partner = Field(..., description="Partner information")
        type_of_relationship: TypeOfRelationship = Field(
            ...,
            description="Type of marital relationship (1=spouse, 2=registered partner)",
        )

        @field_validator("type_of_relationship")
        @classmethod
        def validate_marital_relationship_type(
            cls, v: TypeOfRelationship
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

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "maritalRelationship",
            wrapper_namespace: Optional[str] = None,
        ) -> ET.Element:
            # Use wrapper_namespace for wrapper element, namespace for content
            wrapper_ns = (
                wrapper_namespace if wrapper_namespace is not None else namespace
            )

            if parent is not None:
                elem = ET.SubElement(
                    parent, f"{{{wrapper_ns}}}{element_name}"
                )
            else:
                elem = ET.Element(f"{{{wrapper_ns}}}{element_name}")

            self.partner.to_xml(parent=elem, namespace=namespace)

            rel_elem = ET.SubElement(
                elem, f"{{{namespace}}}typeOfRelationship"
            )
            rel_elem.text = self.type_of_relationship.value

            return elem

        @classmethod
        def from_xml(
            cls, element: ET.Element
        ) -> "ECH0021MaritalRelationship":
            ns = {"eCH-0021": cfg.ns}

            partner_elem = element.find("eCH-0021:partner", ns)
            rel_elem = element.find("eCH-0021:typeOfRelationship", ns)

            return cls(
                partner=ECH0021Partner.from_xml(partner_elem),
                type_of_relationship=TypeOfRelationship(rel_elem.text),
            )

    return ECH0021Partner, ECH0021MaritalRelationship


# ============================================================================
# Grouped Factory: Guardian Classes
# ============================================================================


def _make_guardian_classes(cfg: ECH0021VersionConfig) -> tuple:
    """Create GuardianMeasureInfo and GuardianRelationship (interdependent).

    Returns:
        Tuple of (ECH0021GuardianMeasureInfo, ECH0021GuardianRelationship)
    """

    class ECH0021GuardianMeasureInfo(BaseModel):
        """eCH-0021 Guardian measure information.

        Contains legal basis (ZGB articles) and validity information for
        child and adult protection measures (KESR).

        XML Schema: eCH-0021 guardianMeasureInfoType
        """

        based_on_law: List[str] = Field(
            default_factory=list,
            description="ZGB article numbers for KESR measures (optional, unbounded)",
        )
        based_on_law_add_on: Optional[str] = Field(
            None,
            min_length=1,
            max_length=100,
            description="Additional legal basis information (optional, 1-100 chars)",
        )
        guardian_measure_valid_from: date = Field(
            ..., description="Date when guardian measure becomes valid (required)"
        )

        @field_validator("based_on_law")
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

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "guardianMeasureInfo",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            for article in self.based_on_law:
                law_elem = ET.SubElement(elem, f"{{{namespace}}}basedOnLaw")
                law_elem.text = article

            if self.based_on_law_add_on:
                addon_elem = ET.SubElement(
                    elem, f"{{{namespace}}}basedOnLawAddOn"
                )
                addon_elem.text = self.based_on_law_add_on

            valid_from_elem = ET.SubElement(
                elem, f"{{{namespace}}}guardianMeasureValidFrom"
            )
            valid_from_elem.text = self.guardian_measure_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(
            cls, element: ET.Element
        ) -> "ECH0021GuardianMeasureInfo":
            ns = {"eCH-0021": cfg.ns}

            law_elems = element.findall("eCH-0021:basedOnLaw", ns)
            based_on_law = [elem.text for elem in law_elems if elem.text]

            addon_elem = element.find("eCH-0021:basedOnLawAddOn", ns)
            based_on_law_add_on = (
                addon_elem.text if addon_elem is not None else None
            )

            valid_from_elem = element.find(
                "eCH-0021:guardianMeasureValidFrom", ns
            )
            guardian_measure_valid_from = date.fromisoformat(
                valid_from_elem.text
            )

            return cls(
                based_on_law=based_on_law,
                based_on_law_add_on=based_on_law_add_on,
                guardian_measure_valid_from=guardian_measure_valid_from,
            )

    class ECH0021GuardianRelationship(BaseModel):
        """eCH-0021 Guardian relationship.

        Contains guardian information for child and adult protection measures.
        Guardian can be a person OR an organization (e.g., KESB).

        XML Schema: eCH-0021 guardianRelationshipType
        """

        guardian_relationship_id: str = Field(
            ...,
            min_length=1,
            max_length=36,
            description="Guardian relationship identifier (required, 1-36 chars)",
        )

        # Partner (optional) - xs:choice: person OR organization
        person_identification: Optional[ECH0044PersonIdentification] = Field(
            None, description="Guardian as person (full identification)"
        )
        person_identification_partner: Optional[
            ECH0044PersonIdentificationLight
        ] = Field(
            None, description="Guardian as person (light identification)"
        )
        partner_id_organisation: Optional[ECH0011PartnerIdOrganisation] = (
            Field(None, description="Guardian as organization (e.g., KESB)")
        )

        # Partner address (optional, inside partner element)
        partner_address: Optional[ECH0010MailAddress] = Field(
            None, description="Guardian's mailing address (optional)"
        )

        type_of_relationship: TypeOfRelationship = Field(
            ...,
            description="Type of guardian relationship (7=legal assistant, 8=advisor, 9=guardian, 10=healthcare proxy)",
        )

        guardian_measure_info: ECH0021GuardianMeasureInfo = Field(
            ..., description="Guardian measure information (required)"
        )

        care: Optional[CareType] = Field(
            None, description="Care arrangement (optional)"
        )

        @field_validator("type_of_relationship")
        @classmethod
        def validate_guardian_relationship_type(
            cls, v: TypeOfRelationship
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

        @model_validator(mode="after")
        def validate_partner_choice(self):
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
            namespace: str = cfg.ns,
            element_name: str = "guardianRelationship",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            # guardianRelationshipId (required)
            id_elem = ET.SubElement(
                elem, f"{{{namespace}}}guardianRelationshipId"
            )
            id_elem.text = self.guardian_relationship_id

            # partner (optional) - xs:choice + optional address
            if (
                self.person_identification
                or self.person_identification_partner
                or self.partner_id_organisation
                or self.partner_address
            ):
                partner_elem = ET.SubElement(
                    elem, f"{{{namespace}}}partner"
                )

                # xs:choice: person OR organization
                if self.person_identification:
                    self.person_identification.to_xml(
                        parent=partner_elem,
                        element_name="personIdentification",
                        wrapper_namespace=namespace,
                    )
                elif self.person_identification_partner:
                    self.person_identification_partner.to_xml(
                        parent=partner_elem,
                        element_name="personIdentificationPartner",
                        wrapper_namespace=namespace,
                    )
                elif self.partner_id_organisation:
                    self.partner_id_organisation.to_xml(
                        parent=partner_elem,
                        tag="partnerIdOrganisation",
                        wrapper_namespace=namespace,
                    )

                # address (optional, inside partner)
                if self.partner_address:
                    self.partner_address.to_xml(
                        parent=partner_elem,
                        namespace=cfg.ns_ech0010,
                        element_name="address",
                        wrapper_namespace=namespace,
                    )

            # typeOfRelationship (required)
            rel_elem = ET.SubElement(
                elem, f"{{{namespace}}}typeOfRelationship"
            )
            rel_elem.text = self.type_of_relationship.value

            # guardianMeasureInfo (required)
            self.guardian_measure_info.to_xml(
                parent=elem, namespace=namespace
            )

            # care (optional)
            if self.care:
                care_elem = ET.SubElement(elem, f"{{{namespace}}}care")
                care_elem.text = self.care.value

            return elem

        @classmethod
        def from_xml(
            cls, element: ET.Element
        ) -> "ECH0021GuardianRelationship":
            ns = {
                "eCH-0021": cfg.ns,
                "eCH-0044": NS.ECH0044_V4,
                "eCH-0011": cfg.ns_ech0011,
            }

            # guardianRelationshipId (required)
            id_elem = element.find(
                "eCH-0021:guardianRelationshipId", ns
            )
            guardian_relationship_id = id_elem.text

            # partner (optional) - parse xs:choice
            partner_elem = element.find("eCH-0021:partner", ns)
            person_identification = None
            person_identification_partner = None
            partner_id_organisation = None
            partner_address = None

            if partner_elem is not None:
                person_id_elem = partner_elem.find(
                    "eCH-0021:personIdentification", ns
                )
                if person_id_elem is not None:
                    person_identification = (
                        ECH0044PersonIdentification.from_xml(person_id_elem)
                    )

                person_partner_elem = partner_elem.find(
                    "eCH-0021:personIdentificationPartner", ns
                )
                if person_partner_elem is not None:
                    person_identification_partner = (
                        ECH0044PersonIdentificationLight.from_xml(
                            person_partner_elem
                        )
                    )

                org_elem = partner_elem.find(
                    "eCH-0021:partnerIdOrganisation", ns
                )
                if org_elem is not None:
                    partner_id_organisation = (
                        ECH0011PartnerIdOrganisation.from_xml(org_elem)
                    )

                addr_elem = partner_elem.find("eCH-0021:address", ns)
                if addr_elem is not None:
                    partner_address = ECH0010MailAddress.from_xml(
                        addr_elem, namespace=cfg.ns_ech0010
                    )

            # typeOfRelationship (required)
            rel_elem = element.find("eCH-0021:typeOfRelationship", ns)
            type_of_relationship = TypeOfRelationship(rel_elem.text)

            # guardianMeasureInfo (required)
            measure_elem = element.find("eCH-0021:guardianMeasureInfo", ns)
            guardian_measure_info = ECH0021GuardianMeasureInfo.from_xml(
                measure_elem
            )

            # care (optional)
            care_elem = element.find("eCH-0021:care", ns)
            care = (
                CareType(care_elem.text) if care_elem is not None else None
            )

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

    class ECH0021HealthInsuranceData(BaseModel):
        """eCH-0021 Health insurance data.

        Contains health insurance status and optional insurance information.
        Insurance can be specified either as a name (string) or as an
        organization address (full contact details).

        XML Schema: eCH-0021 healthInsuranceDataType
        """

        health_insured: YesNo = Field(
            ..., description="Health insurance status"
        )

        # Choice: insurance name OR insurance address
        insurance_name: Optional[str] = Field(
            None, max_length=100, description="Insurance company name"
        )
        insurance_address: Optional[ECH0010OrganisationMailAddress] = Field(
            None,
            description="Insurance company full address (organisation + address)",
        )

        health_insurance_valid_from: Optional[date] = None

        def to_xml(
            self,
            parent: Optional[ET.Element] = None,
            namespace: str = cfg.ns,
            element_name: str = "healthInsuranceData",
        ) -> ET.Element:
            if parent is not None:
                elem = ET.SubElement(parent, f"{{{namespace}}}{element_name}")
            else:
                elem = ET.Element(f"{{{namespace}}}{element_name}")

            hi_elem = ET.SubElement(elem, f"{{{namespace}}}healthInsured")
            hi_elem.text = self.health_insured.value

            # Insurance: choice of name OR address
            if self.insurance_name or self.insurance_address:
                ins_elem = ET.SubElement(elem, f"{{{namespace}}}insurance")

                if self.insurance_name:
                    name_elem = ET.SubElement(
                        ins_elem, f"{{{namespace}}}insuranceName"
                    )
                    name_elem.text = self.insurance_name
                elif self.insurance_address:
                    # insuranceAddress wrapper in eCH-0021 namespace,
                    # content (organisation + addressInformation) in eCH-0010
                    addr_wrapper = ET.SubElement(
                        ins_elem, f"{{{namespace}}}insuranceAddress"
                    )
                    ns_010 = cfg.ns_ech0010

                    self.insurance_address.organisation.to_xml(
                        parent=addr_wrapper,
                        namespace=ns_010,
                        element_name="organisation",
                    )
                    self.insurance_address.address_information.to_xml(
                        parent=addr_wrapper,
                        namespace=ns_010,
                        element_name="addressInformation",
                    )

            if self.health_insurance_valid_from:
                from_elem = ET.SubElement(
                    elem, f"{{{namespace}}}healthInsuranceValidFrom"
                )
                from_elem.text = self.health_insurance_valid_from.isoformat()

            return elem

        @classmethod
        def from_xml(
            cls, element: ET.Element
        ) -> "ECH0021HealthInsuranceData":
            ns_0021 = {"eCH-0021": cfg.ns}
            ns_0010 = {"eCH-0010": cfg.ns_ech0010}

            hi_elem = element.find("eCH-0021:healthInsured", ns_0021)
            ins_elem = element.find("eCH-0021:insurance", ns_0021)

            insurance_name = None
            insurance_address = None
            if ins_elem is not None:
                name_elem = ins_elem.find("eCH-0021:insuranceName", ns_0021)
                if name_elem is not None:
                    insurance_name = name_elem.text
                else:
                    addr_elem = ins_elem.find(
                        "eCH-0021:insuranceAddress", ns_0021
                    )
                    if addr_elem is not None:
                        org_elem = addr_elem.find(
                            "eCH-0010:organisation", ns_0010
                        )
                        addr_info_elem = addr_elem.find(
                            "eCH-0010:addressInformation", ns_0010
                        )

                        if (
                            org_elem is not None
                            and addr_info_elem is not None
                        ):
                            org_info = (
                                ECH0010OrganisationMailAddressInfo.from_xml(
                                    org_elem, namespace=cfg.ns_ech0010
                                )
                            )
                            addr_info = (
                                ECH0010AddressInformation.from_xml(
                                    addr_info_elem, namespace=cfg.ns_ech0010
                                )
                            )
                            insurance_address = (
                                ECH0010OrganisationMailAddress(
                                    organisation=org_info,
                                    address_information=addr_info,
                                )
                            )

            from_elem = element.find(
                "eCH-0021:healthInsuranceValidFrom", ns_0021
            )

            return cls(
                health_insured=YesNo(hi_elem.text),
                insurance_name=insurance_name,
                insurance_address=insurance_address,
                health_insurance_valid_from=date.fromisoformat(from_elem.text)
                if from_elem is not None
                else None,
            )

    return ECH0021HealthInsuranceData
