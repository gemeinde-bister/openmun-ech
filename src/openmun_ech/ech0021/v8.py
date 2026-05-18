"""eCH-0021 Person Additional Data v8.0.

Standard: eCH-0021 v8.0 (Person additional data)
Version stability: Used in eCH-0020 v3.0/v5.0

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from datetime import date
from typing import List, Optional, Self

from pydantic import Field, field_validator

from openmun_ech.core import ECHModel, NS, xml_field

from .enums import (
    CareType,
    TypeOfRelationship,
    YesNo,
)
from ._shared import (
    V8_CONFIG,
    _make_armed_forces_data,
    _make_civil_defense_data,
    _make_fire_service_data,
    _make_guardian_classes,
    _make_health_insurance_data,
    _make_job_classes,
    _make_marital_data_addon,
    _make_matrimonial_inheritance_arrangement_data,
    _make_partner_and_marital,
    _make_person_additional_data,
    _make_place_of_origin_addon_data,
)


# ============================================================================
# Shared Classes (namespace-parameterized via V8_CONFIG)
# ============================================================================

ECH0021PersonAdditionalData = _make_person_additional_data(V8_CONFIG)
ECH0021PlaceOfOriginAddonData = _make_place_of_origin_addon_data(V8_CONFIG)
ECH0021MaritalDataAddon = _make_marital_data_addon(V8_CONFIG)
ECH0021ArmedForcesData = _make_armed_forces_data(V8_CONFIG)
ECH0021CivilDefenseData = _make_civil_defense_data(V8_CONFIG)
ECH0021FireServiceData = _make_fire_service_data(V8_CONFIG)
ECH0021MatrimonialInheritanceArrangementData = (
    _make_matrimonial_inheritance_arrangement_data(V8_CONFIG)
)
ECH0021HealthInsuranceData = _make_health_insurance_data(V8_CONFIG)
ECH0021UIDStructure, ECH0021OccupationData, ECH0021JobData = (
    _make_job_classes(V8_CONFIG)
)
ECH0021Partner, ECH0021MaritalRelationship = (
    _make_partner_and_marital(V8_CONFIG)
)
ECH0021GuardianMeasureInfo, ECH0021GuardianRelationship = (
    _make_guardian_classes(V8_CONFIG)
)


# ============================================================================
# Delta Classes (v8-specific — structural differences from v7)
# ============================================================================


class ECH0021LockData(ECHModel):
    """eCH-0021 v8 Lock data.

    v8 split the v7 dataLockType: addressLock is now a separate field,
    and dataLock uses simple yesNo instead of the 3-value DataLockType.
    See RFC 2021-41, PDF v8.1.0 Anhang D.

    XML Schema: eCH-0021 lockDataType
    """

    __xml_ns__ = NS.ECH0021_V8
    __xml_element__ = 'lockData'

    address_lock: YesNo = xml_field('addressLock')
    address_lock_valid_from: Optional[date] = xml_field('addressLockValidFrom', default=None)
    address_lock_valid_till: Optional[date] = xml_field('addressLockValidTill', default=None)
    data_lock: YesNo = xml_field('dataLock')
    data_lock_valid_from: Optional[date] = xml_field('dataLockValidFrom', default=None)
    data_lock_valid_till: Optional[date] = xml_field('dataLockValidTill', default=None)
    paper_lock: YesNo = xml_field('paperLock')
    paper_lock_valid_from: Optional[date] = xml_field('paperLockValidFrom', default=None)
    paper_lock_valid_till: Optional[date] = xml_field('paperLockValidTill', default=None)


class ECH0021NameOfParent(ECHModel):
    """eCH-0021 v8 Name of parent.

    Custom to_xml/from_xml: xs:choice between name variants.
    v8 always emits typeOfRelationship (unlike v7 which suppresses it
    when element name encodes it). Uses generic nameOfParent element.

    XML Schema: eCH-0021 nameOfParentType
    """

    __xml_ns__ = NS.ECH0021_V8
    __xml_element__ = 'nameOfParent'

    first_name: Optional[str] = Field(None, max_length=100)
    official_name: Optional[str] = Field(None, min_length=1, max_length=100)
    first_name_only: Optional[str] = Field(None, max_length=100)
    official_name_only: Optional[str] = Field(None, min_length=1, max_length=100)

    type_of_relationship: Optional[TypeOfRelationship] = Field(
        None, description="Type of relationship (3=mother, 4=father)"
    )
    official_proof_of_name_of_parents_yes_no: Optional[bool] = Field(
        None, description="Official proof of parent names exists"
    )

    @field_validator('type_of_relationship')
    @classmethod
    def validate_parent_relationship(cls, v):
        if v is not None and v not in [TypeOfRelationship.MOTHER, TypeOfRelationship.FATHER]:
            raise ValueError(f"Parent relationship must be mother (3) or father (4), got {v}")
        return v

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

        # xs:choice: firstName+officialName OR firstNameOnly OR officialNameOnly
        if self.first_name and self.official_name:
            fn_elem = ET.SubElement(elem, f'{{{ns}}}firstName')
            fn_elem.text = self.first_name
            on_elem = ET.SubElement(elem, f'{{{ns}}}officialName')
            on_elem.text = self.official_name
        elif self.first_name_only:
            fno_elem = ET.SubElement(elem, f'{{{ns}}}firstNameOnly')
            fno_elem.text = self.first_name_only
        elif self.official_name_only:
            ono_elem = ET.SubElement(elem, f'{{{ns}}}officialNameOnly')
            ono_elem.text = self.official_name_only

        if self.type_of_relationship:
            rel_elem = ET.SubElement(elem, f'{{{ns}}}typeOfRelationship')
            rel_elem.text = self.type_of_relationship.value

        if self.official_proof_of_name_of_parents_yes_no is not None:
            proof_elem = ET.SubElement(elem, f'{{{ns}}}officialProofOfNameOfParentsYesNo')
            proof_elem.text = 'true' if self.official_proof_of_name_of_parents_yes_no else 'false'

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
        ns = namespace or cls.__xml_ns__

        fn_elem = elem.find(f'{{{ns}}}firstName')
        on_elem = elem.find(f'{{{ns}}}officialName')
        fno_elem = elem.find(f'{{{ns}}}firstNameOnly')
        ono_elem = elem.find(f'{{{ns}}}officialNameOnly')
        rel_elem = elem.find(f'{{{ns}}}typeOfRelationship')
        proof_elem = elem.find(f'{{{ns}}}officialProofOfNameOfParentsYesNo')

        return cls(
            first_name=fn_elem.text if fn_elem is not None else None,
            official_name=on_elem.text if on_elem is not None else None,
            first_name_only=fno_elem.text if fno_elem is not None else None,
            official_name_only=ono_elem.text if ono_elem is not None else None,
            type_of_relationship=TypeOfRelationship(rel_elem.text) if rel_elem is not None else None,
            official_proof_of_name_of_parents_yes_no=(proof_elem.text == 'true') if proof_elem is not None else None,
        )


class ECH0021BirthAddonData(ECHModel):
    """eCH-0021 v8 Birth addon data.

    v8 uses generic nameOfParent element (0..2).

    XML Schema: eCH-0021 birthAddonDataType
    """

    __xml_ns__ = NS.ECH0021_V8
    __xml_element__ = 'birthAddonData'

    name_of_parent: List[ECH0021NameOfParent] = xml_field(
        'nameOfParent', is_list=True, default_factory=list,
    )


class ECH0021ParentalRelationship(ECHModel):
    """eCH-0021 v8 Parental relationship.

    v8 removed relationshipValidFrom (RFC 2018-33).

    XML Schema: eCH-0021 parentalRelationshipType
    """

    __xml_ns__ = NS.ECH0021_V8
    __xml_element__ = 'parentalRelationship'

    partner: ECH0021Partner = xml_field('partner')
    type_of_relationship: TypeOfRelationship = xml_field('typeOfRelationship')
    care: CareType = xml_field('care')

    @field_validator('type_of_relationship')
    @classmethod
    def validate_parental_relationship_type(cls, v: TypeOfRelationship) -> TypeOfRelationship:
        parental_types = (
            TypeOfRelationship.MOTHER,
            TypeOfRelationship.FATHER,
            TypeOfRelationship.FOSTER_FATHER,
            TypeOfRelationship.FOSTER_MOTHER,
        )
        if v not in parental_types:
            raise ValueError(
                f"Parental relationship must be MOTHER (3), FATHER (4), "
                f"FOSTER_FATHER (5), or FOSTER_MOTHER (6), got: {v}"
            )
        return v
