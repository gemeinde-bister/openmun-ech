"""eCH-0021 Person Additional Data v7.0.

Standard: eCH-0021 v7.0 (Person additional data)
Version stability: Required for eCH-0020 v3.0 compatibility

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

from pydantic import BaseModel, ConfigDict, Field, field_validator

from openmun_ech.core import NS

from .enums import (
    CareType,
    DataLockType,
    TypeOfRelationship,
    YesNo,
)
from ._shared import (
    V7_CONFIG,
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
# Shared Classes (namespace-parameterized via V7_CONFIG)
# ============================================================================

ECH0021PersonAdditionalData = _make_person_additional_data(V7_CONFIG)
ECH0021PlaceOfOriginAddonData = _make_place_of_origin_addon_data(V7_CONFIG)
ECH0021MaritalDataAddon = _make_marital_data_addon(V7_CONFIG)
ECH0021ArmedForcesData = _make_armed_forces_data(V7_CONFIG)
ECH0021CivilDefenseData = _make_civil_defense_data(V7_CONFIG)
ECH0021FireServiceData = _make_fire_service_data(V7_CONFIG)
ECH0021MatrimonialInheritanceArrangementData = (
    _make_matrimonial_inheritance_arrangement_data(V7_CONFIG)
)
ECH0021HealthInsuranceData = _make_health_insurance_data(V7_CONFIG)
ECH0021UIDStructure, ECH0021OccupationData, ECH0021JobData = (
    _make_job_classes(V7_CONFIG)
)
ECH0021Partner, ECH0021MaritalRelationship = (
    _make_partner_and_marital(V7_CONFIG)
)
ECH0021GuardianMeasureInfo, ECH0021GuardianRelationship = (
    _make_guardian_classes(V7_CONFIG)
)


# ============================================================================
# Delta Classes (v7-specific — structural differences from v8)
# ============================================================================


class ECH0021LockData(BaseModel):
    """eCH-0021 v7 Lock data.

    Contains flags and validity dates for data and paper locks.

    v7 dataLockType has 3 values (0=no lock, 1=address lock, 2=information lock).
    In v8 this was split: addressLock became its own field, dataLock simplified to yesNo.
    See RFC 2021-41, PDF v8.1.0 Anhang D.

    XML Schema: eCH-0021-7-0 lockDataType
    """

    data_lock: DataLockType = Field(..., description="Data lock (0=none, 1=address, 2=information)")
    data_lock_valid_from: Optional[date] = None
    data_lock_valid_till: Optional[date] = None

    paper_lock: YesNo = Field(..., description="Paper lock (required: yes/no)")
    paper_lock_valid_from: Optional[date] = None
    paper_lock_valid_till: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V7,
               element_name: str = 'lockData') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        data_lock = ET.SubElement(elem, f'{{{namespace}}}dataLock')
        data_lock.text = self.data_lock.value

        if self.data_lock_valid_from:
            data_from = ET.SubElement(elem, f'{{{namespace}}}dataLockValidFrom')
            data_from.text = self.data_lock_valid_from.isoformat()

        if self.data_lock_valid_till:
            data_till = ET.SubElement(elem, f'{{{namespace}}}dataLockValidTill')
            data_till.text = self.data_lock_valid_till.isoformat()

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
        ns = {'eCH-0021': NS.ECH0021_V7}

        def get_text(path: str) -> Optional[str]:
            elem = element.find(path, ns)
            return elem.text if elem is not None else None

        def get_date(path: str) -> Optional[date]:
            text = get_text(path)
            return date.fromisoformat(text) if text else None

        return cls(
            data_lock=DataLockType(get_text('eCH-0021:dataLock')),
            data_lock_valid_from=get_date('eCH-0021:dataLockValidFrom'),
            data_lock_valid_till=get_date('eCH-0021:dataLockValidTill'),
            paper_lock=YesNo(get_text('eCH-0021:paperLock')),
            paper_lock_valid_from=get_date('eCH-0021:paperLockValidFrom'),
            paper_lock_valid_till=get_date('eCH-0021:paperLockValidTill')
        )


class ECH0021NameOfParent(BaseModel):
    """eCH-0021 v7 Name of parent.

    v7 uses nameOfFather/nameOfMother element names and suppresses
    typeOfRelationship when the element name already encodes it.

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
               namespace: str = NS.ECH0021_V7,
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

        # Only export typeOfRelationship if using generic element_name
        # (nameOfFather/nameOfMother already encode the relationship type)
        if self.type_of_relationship and element_name not in ('nameOfFather', 'nameOfMother'):
            rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
            rel_elem.text = self.type_of_relationship.value

        if self.official_proof_of_name_of_parents_yes_no is not None:
            proof_elem = ET.SubElement(elem, f'{{{namespace}}}officialProofOfNameOfParentsYesNo')
            proof_elem.text = 'true' if self.official_proof_of_name_of_parents_yes_no else 'false'

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021NameOfParent':
        ns = {'eCH-0021': NS.ECH0021_V7}

        fn_elem = element.find('eCH-0021:firstName', ns)
        on_elem = element.find('eCH-0021:officialName', ns)
        fno_elem = element.find('eCH-0021:firstNameOnly', ns)
        ono_elem = element.find('eCH-0021:officialNameOnly', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        proof_elem = element.find('eCH-0021:officialProofOfNameOfParentsYesNo', ns)

        # Infer type_of_relationship from element name if not explicitly provided
        type_of_relationship = None
        if rel_elem is not None:
            type_of_relationship = TypeOfRelationship(rel_elem.text)
        else:
            element_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            if element_name == 'nameOfFather':
                type_of_relationship = TypeOfRelationship.FATHER
            elif element_name == 'nameOfMother':
                type_of_relationship = TypeOfRelationship.MOTHER

        return cls(
            first_name=fn_elem.text if fn_elem is not None else None,
            official_name=on_elem.text if on_elem is not None else None,
            first_name_only=fno_elem.text if fno_elem is not None else None,
            official_name_only=ono_elem.text if ono_elem is not None else None,
            type_of_relationship=type_of_relationship,
            official_proof_of_name_of_parents_yes_no=(proof_elem.text == 'true') if proof_elem is not None else None
        )


class ECH0021BirthAddonData(BaseModel):
    """eCH-0021 v7 Birth addon data.

    v7 uses nameOfFather/nameOfMother element names with sort logic.
    v8 uses generic nameOfParent (0..2).

    XML Schema: eCH-0021 birthAddonDataType
    """

    name_of_parent: List[ECH0021NameOfParent] = Field(
        default_factory=list,
        max_length=2,
        description="Names of parents (max 2: father and mother)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V7,
               element_name: str = 'birthAddonData') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # XSD requires strict ordering: nameOfFather (0..1) before nameOfMother (0..1)
        def sort_key(p):
            if p.type_of_relationship:
                if p.type_of_relationship.value == '4':  # FATHER
                    return 0
                elif p.type_of_relationship.value == '3':  # MOTHER
                    return 1
            return 2

        sorted_parents = sorted(self.name_of_parent, key=sort_key)

        for parent_name in sorted_parents:
            if parent_name.type_of_relationship and parent_name.type_of_relationship.value == '4':
                elem_name = 'nameOfFather'
            elif parent_name.type_of_relationship and parent_name.type_of_relationship.value == '3':
                elem_name = 'nameOfMother'
            else:
                elem_name = 'nameOfParent'
            parent_name.to_xml(parent=elem, namespace=namespace, element_name=elem_name)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021BirthAddonData':
        ns = {'eCH-0021': NS.ECH0021_V7}

        father_elems = element.findall('eCH-0021:nameOfFather', ns)
        mother_elems = element.findall('eCH-0021:nameOfMother', ns)
        parent_elems = element.findall('eCH-0021:nameOfParent', ns)

        all_parents = father_elems + mother_elems + parent_elems

        return cls(
            name_of_parent=[ECH0021NameOfParent.from_xml(elem) for elem in all_parents]
        )


class ECH0021ParentalRelationship(BaseModel):
    """eCH-0021 v7 Parental relationship.

    v7 includes relationshipValidFrom (removed in v8, RFC 2018-33).

    XML Schema: eCH-0021 parentalRelationshipType
    """

    partner: ECH0021Partner = Field(..., description="Parent information")
    relationship_valid_from: Optional[date] = Field(
        None,
        alias='relationshipValidFrom',
        description="Date when parental relationship was established"
    )
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
               namespace: str = NS.ECH0021_V7,
               element_name: str = 'parentalRelationship') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        self.partner.to_xml(parent=elem, namespace=namespace)

        if self.relationship_valid_from:
            rel_from_elem = ET.SubElement(elem, f'{{{namespace}}}relationshipValidFrom')
            rel_from_elem.text = self.relationship_valid_from.isoformat()

        rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
        rel_elem.text = self.type_of_relationship.value

        care_elem = ET.SubElement(elem, f'{{{namespace}}}care')
        care_elem.text = self.care.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021ParentalRelationship':
        ns = {'eCH-0021': NS.ECH0021_V7}

        partner_elem = element.find('eCH-0021:partner', ns)
        rel_from_elem = element.find('eCH-0021:relationshipValidFrom', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        care_elem = element.find('eCH-0021:care', ns)

        return cls(
            partner=ECH0021Partner.from_xml(partner_elem),
            relationshipValidFrom=date.fromisoformat(rel_from_elem.text) if rel_from_elem is not None else None,
            type_of_relationship=TypeOfRelationship(rel_elem.text),
            care=CareType(care_elem.text)
        )


class ECH0021PoliticalRightData(BaseModel):
    """eCH-0021 v7 Political rights data.

    NOTE: This type was REMOVED in v8 (federal voting restrictions removed).
    Only exists in v7 for compatibility with eCH-0020 v3.0.

    XML Schema: eCH-0021-7-0 politicalRightDataType
    """

    model_config = ConfigDict(populate_by_name=True)

    restricted_voting_and_election_right_federation: Optional[bool] = Field(
        None,
        alias='restrictedVotingAndElectionRightFederation',
        description='Restriction of voting rights at federal level (deprecated in v8)'
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = NS.ECH0021_V7,
               element_name: str = 'politicalRightData') -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.restricted_voting_and_election_right_federation is not None:
            restriction_elem = ET.SubElement(
                elem, f'{{{namespace}}}restrictedVotingAndElectionRightFederation'
            )
            restriction_elem.text = 'true' if self.restricted_voting_and_election_right_federation else 'false'

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021PoliticalRightData':
        ns = {'eCH-0021': NS.ECH0021_V7}

        restriction_elem = element.find(
            'eCH-0021:restrictedVotingAndElectionRightFederation', ns
        )

        restricted = None
        if restriction_elem is not None and restriction_elem.text:
            restricted = restriction_elem.text.lower() == 'true'

        return cls(
            restricted_voting_and_election_right_federation=restricted
        )
