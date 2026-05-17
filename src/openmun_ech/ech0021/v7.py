"""eCH-0021 Person Additional Data v7.0.

Standard: eCH-0021 v7.0 (Person additional data)
Version stability: Required for eCH-0020 v3.0 compatibility

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


class ECH0021LockData(ECHModel):
    """eCH-0021 v7 Lock data.

    v7 dataLockType has 3 values (0=no lock, 1=address lock, 2=information lock).
    In v8 this was split: addressLock became its own field, dataLock simplified to yesNo.
    See RFC 2021-41, PDF v8.1.0 Anhang D.

    XML Schema: eCH-0021-7-0 lockDataType
    """

    __xml_ns__ = NS.ECH0021_V7
    __xml_element__ = 'lockData'

    data_lock: DataLockType = xml_field('dataLock')
    data_lock_valid_from: Optional[date] = xml_field('dataLockValidFrom', default=None)
    data_lock_valid_till: Optional[date] = xml_field('dataLockValidTill', default=None)
    paper_lock: YesNo = xml_field('paperLock')
    paper_lock_valid_from: Optional[date] = xml_field('paperLockValidFrom', default=None)
    paper_lock_valid_till: Optional[date] = xml_field('paperLockValidTill', default=None)


class ECH0021NameOfParent(ECHModel):
    """eCH-0021 v7 Name of parent.

    Custom to_xml/from_xml: v7 uses nameOfFather/nameOfMother element names
    and suppresses typeOfRelationship when element name already encodes it.
    from_xml infers relationship type from element name.

    XML Schema: eCH-0021 nameOfParentType
    """

    __xml_ns__ = NS.ECH0021_V7
    __xml_element__ = 'nameOfParent'

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

        # Only export typeOfRelationship if using generic element_name
        # (nameOfFather/nameOfMother already encode the relationship type)
        if self.type_of_relationship and el_name not in ('nameOfFather', 'nameOfMother'):
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

        # Infer type_of_relationship from element name if not explicitly provided
        type_of_relationship = None
        if rel_elem is not None:
            type_of_relationship = TypeOfRelationship(rel_elem.text)
        else:
            element_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if element_tag == 'nameOfFather':
                type_of_relationship = TypeOfRelationship.FATHER
            elif element_tag == 'nameOfMother':
                type_of_relationship = TypeOfRelationship.MOTHER

        return cls(
            first_name=fn_elem.text if fn_elem is not None else None,
            official_name=on_elem.text if on_elem is not None else None,
            first_name_only=fno_elem.text if fno_elem is not None else None,
            official_name_only=ono_elem.text if ono_elem is not None else None,
            type_of_relationship=type_of_relationship,
            official_proof_of_name_of_parents_yes_no=(proof_elem.text == 'true') if proof_elem is not None else None,
        )


class ECH0021BirthAddonData(ECHModel):
    """eCH-0021 v7 Birth addon data.

    Custom to_xml/from_xml: v7 uses nameOfFather/nameOfMother element names
    with strict XSD ordering (father before mother). from_xml collects all three
    element name variants.

    XML Schema: eCH-0021 birthAddonDataType
    """

    __xml_ns__ = NS.ECH0021_V7
    __xml_element__ = 'birthAddonData'

    name_of_parent: List[ECH0021NameOfParent] = Field(
        default_factory=list,
        max_length=2,
        description="Names of parents (max 2: father and mother)",
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

        # XSD requires strict ordering: nameOfFather (0..1) before nameOfMother (0..1)
        def sort_key(p):
            if p.type_of_relationship:
                if p.type_of_relationship.value == '4':  # FATHER
                    return 0
                elif p.type_of_relationship.value == '3':  # MOTHER
                    return 1
            return 2

        for parent_name in sorted(self.name_of_parent, key=sort_key):
            if parent_name.type_of_relationship and parent_name.type_of_relationship.value == '4':
                child_name = 'nameOfFather'
            elif parent_name.type_of_relationship and parent_name.type_of_relationship.value == '3':
                child_name = 'nameOfMother'
            else:
                child_name = 'nameOfParent'
            parent_name.to_xml(parent=elem, namespace=ns, element_name=child_name)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
        ns = namespace or cls.__xml_ns__

        father_elems = elem.findall(f'{{{ns}}}nameOfFather')
        mother_elems = elem.findall(f'{{{ns}}}nameOfMother')
        parent_elems = elem.findall(f'{{{ns}}}nameOfParent')

        all_parents = father_elems + mother_elems + parent_elems

        return cls(
            name_of_parent=[ECH0021NameOfParent.from_xml(e, namespace=ns) for e in all_parents],
        )


class ECH0021ParentalRelationship(ECHModel):
    """eCH-0021 v7 Parental relationship.

    v7 includes relationshipValidFrom (removed in v8, RFC 2018-33).

    XML Schema: eCH-0021 parentalRelationshipType
    """

    __xml_ns__ = NS.ECH0021_V7
    __xml_element__ = 'parentalRelationship'

    partner: ECH0021Partner = xml_field('partner')
    relationship_valid_from: Optional[date] = xml_field(
        'relationshipValidFrom', default=None,
    )
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


class ECH0021PoliticalRightData(ECHModel):
    """eCH-0021 v7 Political rights data.

    NOTE: This type was REMOVED in v8 (federal voting restrictions removed).
    Only exists in v7 for compatibility with eCH-0020 v3.0.

    XML Schema: eCH-0021-7-0 politicalRightDataType
    """

    __xml_ns__ = NS.ECH0021_V7
    __xml_element__ = 'politicalRightData'

    restricted_voting_and_election_right_federation: Optional[bool] = xml_field(
        'restrictedVotingAndElectionRightFederation', default=None,
        alias='restrictedVotingAndElectionRightFederation',
    )
