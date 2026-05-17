"""eCH-0021 Person Additional Data v8.0.

Standard: eCH-0021 v8.0 (Person additional data)
Version stability: Used in eCH-0020 v3.0/v5.0

This component provides additional person data structures including:
- Birth addon data (parent names)
- Marital data addon (place of marriage)
- Person additional data (salutation, language)
- Place of origin addon (naturalization dates)
- Lock data (data/paper/address locks)
- Relationships (marital, parental, guardian)
- Job data
- Military/civil service data

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from openmun_ech.core import NS

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


class ECH0021LockData(BaseModel):
    """eCH-0021 v8 Lock data.

    v8 split the v7 dataLockType: addressLock is now a separate field,
    and dataLock uses simple yesNo instead of the 3-value DataLockType.
    See RFC 2021-41, PDF v8.1.0 Anhang D.

    XML Schema: eCH-0021 lockDataType
    """

    address_lock: YesNo = Field(..., description="Address lock (required: yes/no)")
    address_lock_valid_from: Optional[date] = None
    address_lock_valid_till: Optional[date] = None

    data_lock: YesNo = Field(..., description="Data lock (required: yes/no)")
    data_lock_valid_from: Optional[date] = None
    data_lock_valid_till: Optional[date] = None

    paper_lock: YesNo = Field(..., description="Paper lock (required: yes/no)")
    paper_lock_valid_from: Optional[date] = None
    paper_lock_valid_till: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V8,
               element_name: str = 'lockData') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Address lock (required)
        addr_lock = ET.SubElement(elem, f'{{{namespace}}}addressLock')
        addr_lock.text = self.address_lock.value

        if self.address_lock_valid_from:
            addr_from = ET.SubElement(elem, f'{{{namespace}}}addressLockValidFrom')
            addr_from.text = self.address_lock_valid_from.isoformat()

        if self.address_lock_valid_till:
            addr_till = ET.SubElement(elem, f'{{{namespace}}}addressLockValidTill')
            addr_till.text = self.address_lock_valid_till.isoformat()

        # Data lock (required)
        data_lock = ET.SubElement(elem, f'{{{namespace}}}dataLock')
        data_lock.text = self.data_lock.value

        if self.data_lock_valid_from:
            data_from = ET.SubElement(elem, f'{{{namespace}}}dataLockValidFrom')
            data_from.text = self.data_lock_valid_from.isoformat()

        if self.data_lock_valid_till:
            data_till = ET.SubElement(elem, f'{{{namespace}}}dataLockValidTill')
            data_till.text = self.data_lock_valid_till.isoformat()

        # Paper lock (required)
        paper_lock = ET.SubElement(elem, f'{{{namespace}}}paperLock')
        paper_lock.text = self.paper_lock.value

        if self.paper_lock_valid_from:
            paper_from = ET.SubElement(elem, f'{{{namespace}}}paperLockValidFrom')
            paper_from.text = self.paper_lock_valid_from.isoformat()

        if self.paper_lock_valid_till:
            paper_till = ET.SubElement(elem, f'{{{namespace}}}paperLockValidTill')
            paper_till.text = self.paper_lock_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021LockData':
        ns = {'eCH-0021': NS.ECH0021_V8}

        def get_text(path: str) -> Optional[str]:
            elem = element.find(path, ns)
            return elem.text if elem is not None else None

        def get_date(path: str) -> Optional[date]:
            text = get_text(path)
            return date.fromisoformat(text) if text else None

        return cls(
            address_lock=YesNo(get_text('eCH-0021:addressLock')),
            address_lock_valid_from=get_date('eCH-0021:addressLockValidFrom'),
            address_lock_valid_till=get_date('eCH-0021:addressLockValidTill'),
            data_lock=YesNo(get_text('eCH-0021:dataLock')),
            data_lock_valid_from=get_date('eCH-0021:dataLockValidFrom'),
            data_lock_valid_till=get_date('eCH-0021:dataLockValidTill'),
            paper_lock=YesNo(get_text('eCH-0021:paperLock')),
            paper_lock_valid_from=get_date('eCH-0021:paperLockValidFrom'),
            paper_lock_valid_till=get_date('eCH-0021:paperLockValidTill')
        )


class ECH0021NameOfParent(BaseModel):
    """eCH-0021 v8 Name of parent.

    v8 always emits typeOfRelationship (unlike v7 which suppresses it
    when element name encodes it). Uses generic nameOfParent element.

    XML Schema: eCH-0021 nameOfParentType
    """

    first_name: Optional[str] = Field(None, max_length=100)
    official_name: Optional[str] = Field(None, max_length=100)
    first_name_only: Optional[str] = Field(None, max_length=100)
    official_name_only: Optional[str] = Field(None, max_length=100)

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

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V8,
               element_name: str = 'nameOfParent') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.first_name and self.official_name:
            fn_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
            fn_elem.text = self.first_name
            on_elem = ET.SubElement(elem, f'{{{namespace}}}officialName')
            on_elem.text = self.official_name
        elif self.first_name_only:
            fno_elem = ET.SubElement(elem, f'{{{namespace}}}firstNameOnly')
            fno_elem.text = self.first_name_only
        elif self.official_name_only:
            ono_elem = ET.SubElement(elem, f'{{{namespace}}}officialNameOnly')
            ono_elem.text = self.official_name_only

        if self.type_of_relationship:
            rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
            rel_elem.text = self.type_of_relationship.value

        if self.official_proof_of_name_of_parents_yes_no is not None:
            proof_elem = ET.SubElement(elem, f'{{{namespace}}}officialProofOfNameOfParentsYesNo')
            proof_elem.text = 'true' if self.official_proof_of_name_of_parents_yes_no else 'false'

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021NameOfParent':
        ns = {'eCH-0021': NS.ECH0021_V8}

        fn_elem = element.find('eCH-0021:firstName', ns)
        on_elem = element.find('eCH-0021:officialName', ns)
        fno_elem = element.find('eCH-0021:firstNameOnly', ns)
        ono_elem = element.find('eCH-0021:officialNameOnly', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        proof_elem = element.find('eCH-0021:officialProofOfNameOfParentsYesNo', ns)

        return cls(
            first_name=fn_elem.text if fn_elem is not None else None,
            official_name=on_elem.text if on_elem is not None else None,
            first_name_only=fno_elem.text if fno_elem is not None else None,
            official_name_only=ono_elem.text if ono_elem is not None else None,
            type_of_relationship=TypeOfRelationship(rel_elem.text) if rel_elem is not None else None,
            official_proof_of_name_of_parents_yes_no=(proof_elem.text == 'true') if proof_elem is not None else None
        )


class ECH0021BirthAddonData(BaseModel):
    """eCH-0021 v8 Birth addon data.

    v8 uses generic nameOfParent element (0..2).
    v7 used nameOfFather/nameOfMother with sorting.

    XML Schema: eCH-0021 birthAddonDataType
    """

    name_of_parent: List[ECH0021NameOfParent] = Field(
        default_factory=list,
        max_length=2,
        description="Names of parents (max 2: father and mother)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V8,
               element_name: str = 'birthAddonData') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        for parent_name in self.name_of_parent:
            parent_name.to_xml(parent=elem, namespace=namespace)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021BirthAddonData':
        ns = {'eCH-0021': NS.ECH0021_V8}

        parent_elems = element.findall('eCH-0021:nameOfParent', ns)

        return cls(
            name_of_parent=[ECH0021NameOfParent.from_xml(elem) for elem in parent_elems]
        )


class ECH0021ParentalRelationship(BaseModel):
    """eCH-0021 v8 Parental relationship.

    v8 removed relationshipValidFrom (RFC 2018-33).

    XML Schema: eCH-0021 parentalRelationshipType
    """

    partner: ECH0021Partner = Field(..., description="Parent information")
    type_of_relationship: TypeOfRelationship = Field(
        ...,
        description="Type of parental relationship (3=mother, 4=father, 5=foster father, 6=foster mother)"
    )
    care: CareType = Field(..., description="Care/custody arrangement")

    @field_validator('type_of_relationship')
    @classmethod
    def validate_parental_relationship_type(cls, v: TypeOfRelationship) -> TypeOfRelationship:
        parental_types = (
            TypeOfRelationship.MOTHER,
            TypeOfRelationship.FATHER,
            TypeOfRelationship.FOSTER_FATHER,
            TypeOfRelationship.FOSTER_MOTHER
        )
        if v not in parental_types:
            raise ValueError(
                f"Parental relationship must be MOTHER (3), FATHER (4), "
                f"FOSTER_FATHER (5), or FOSTER_MOTHER (6), got: {v}"
            )
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V8,
               element_name: str = 'parentalRelationship') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        self.partner.to_xml(parent=elem, namespace=namespace)

        rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
        rel_elem.text = self.type_of_relationship.value

        care_elem = ET.SubElement(elem, f'{{{namespace}}}care')
        care_elem.text = self.care.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021ParentalRelationship':
        ns = {'eCH-0021': NS.ECH0021_V8}

        partner_elem = element.find('eCH-0021:partner', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        care_elem = element.find('eCH-0021:care', ns)

        return cls(
            partner=ECH0021Partner.from_xml(partner_elem),
            type_of_relationship=TypeOfRelationship(rel_elem.text),
            care=CareType(care_elem.text)
        )
