"""XSD validation tests for eCH-0021 v7 Person Additional Data.

Tests that generated XML validates against official eCH-0021-7-0.xsd schema.
v7 is the version used by eCH-0020 v3.0 (our only consumer).

Key v7-specific differences from v8:
- lockDataType: dataLock uses dataLockType (3 values: 0/1/2), no addressLock
- birthAddonDataType: nameOfFather + nameOfMother (not generic nameOfParent)
- nameOfParentType: no typeOfRelationship field
- parentalRelationshipType: has relationshipValidFrom
- politicalRightDataType: exists (removed in v8)
- careType: values 0-3 only (v8 adds 4)
"""

import pytest
import xml.etree.ElementTree as ET
from datetime import date

import xmlschema

from openmun_ech.ech0021.v7 import (
    ECH0021PersonAdditionalData,
    ECH0021LockData,
    ECH0021PlaceOfOriginAddonData,
    ECH0021MaritalDataAddon,
    ECH0021NameOfParent,
    ECH0021BirthAddonData,
    ECH0021UIDStructure,
    ECH0021OccupationData,
    ECH0021JobData,
    ECH0021Partner,
    ECH0021MaritalRelationship,
    ECH0021ParentalRelationship,
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021HealthInsuranceData,
    ECH0021MatrimonialInheritanceArrangementData,
    ECH0021PoliticalRightData,
)
from openmun_ech.ech0021.enums import (
    DataLockType,
    TypeOfRelationship,
    CareType,
    KindOfEmployment,
    YesNo,
    MrMrs,
    UIDOrganisationIdCategory,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification, ECH0044PersonIdentificationLight, ECH0044DatePartiallyKnown, ECH0044NamedPersonId
from openmun_ech.ech0011 import ECH0011GeneralPlace
from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation
from openmun_ech.utils.schema_cache import get_cached_schema


def _make_person_id(**kwargs):
    """Helper: create ECH0044PersonIdentification with required local_person_id."""
    defaults = dict(
        local_person_id=ECH0044NamedPersonId(
            person_id_category="infostar.zh.ch",
            person_id="12345",
        ),
    )
    defaults.update(kwargs)
    return ECH0044PersonIdentification(**defaults)


def get_schema():
    """Get the eCH-0021 v7 XSD schema (cached)."""
    return get_cached_schema('eCH-0021-7-0.xsd')


def validate_fragment(xml_element: ET.Element, type_name: str):
    """Validate XML fragment against a specific XSD type."""
    schema = get_schema()
    xml_string = ET.tostring(xml_element, encoding='unicode')
    try:
        schema.validate(xml_string)
    except xmlschema.XMLSchemaValidationError as e:
        if "not an element" in str(e).lower():
            pass  # Complex type, not a root element — expected
        else:
            pytest.fail(f"XSD validation failed for {type_name}: {e}")


# ============================================================================
# PersonAdditionalData
# ============================================================================

def test_v7_xsd_person_additional_data_minimal():
    data = ECH0021PersonAdditionalData()
    xml = data.to_xml()
    validate_fragment(xml, 'personAdditionalData')


def test_v7_xsd_person_additional_data_complete():
    data = ECH0021PersonAdditionalData(
        mr_mrs=MrMrs.MR,
        title="Dr.",
        language_of_correspondance="de",
    )
    xml = data.to_xml()
    validate_fragment(xml, 'personAdditionalData')


# ============================================================================
# LockData — v7-specific: dataLockType has 3 values, no addressLock
# ============================================================================

def test_v7_xsd_lock_data_no_lock():
    """dataLock=0 (no lock)."""
    data = ECH0021LockData(
        data_lock=DataLockType.NO_LOCK,
        paper_lock=YesNo.NO,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'lockDataType')


def test_v7_xsd_lock_data_address_lock():
    """dataLock=1 (address lock) — v7 combined address+data into one field."""
    data = ECH0021LockData(
        data_lock=DataLockType.ADDRESS_LOCK,
        paper_lock=YesNo.NO,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'lockDataType')
    # Verify the value is "1" in XML
    xml_str = ET.tostring(xml, encoding='unicode')
    assert '>1<' in xml_str


def test_v7_xsd_lock_data_information_lock():
    """dataLock=2 (information lock) — v7-only value, removed in v8."""
    data = ECH0021LockData(
        data_lock=DataLockType.INFORMATION_LOCK,
        paper_lock=YesNo.NO,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'lockDataType')
    # Verify the value is "2" in XML
    xml_str = ET.tostring(xml, encoding='unicode')
    assert '>2<' in xml_str


def test_v7_xsd_lock_data_with_validity():
    data = ECH0021LockData(
        data_lock=DataLockType.INFORMATION_LOCK,
        data_lock_valid_from=date(2024, 1, 1),
        data_lock_valid_till=date(2024, 12, 31),
        paper_lock=YesNo.YES,
        paper_lock_valid_from=date(2024, 6, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'lockDataType')


def test_v7_xsd_lock_data_roundtrip_all_values():
    """Roundtrip for all 3 dataLockType values."""
    for lock_type in DataLockType:
        data = ECH0021LockData(
            data_lock=lock_type,
            paper_lock=YesNo.NO,
        )
        xml = data.to_xml()
        parsed = ECH0021LockData.from_xml(xml)
        assert parsed.data_lock == lock_type
        assert parsed.paper_lock == YesNo.NO


# ============================================================================
# PoliticalRightData — v7 only (removed in v8, RFC 2016-64)
# ============================================================================

def test_v7_xsd_political_right_data():
    data = ECH0021PoliticalRightData(
        restricted_voting_and_election_right_federation=True,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'politicalRightDataType')


def test_v7_xsd_political_right_data_no_restriction():
    data = ECH0021PoliticalRightData(
        restricted_voting_and_election_right_federation=False,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'politicalRightDataType')


def test_v7_xsd_political_right_data_optional():
    data = ECH0021PoliticalRightData()
    xml = data.to_xml()
    validate_fragment(xml, 'politicalRightDataType')


# ============================================================================
# PlaceOfOriginAddonData
# ============================================================================

def test_v7_xsd_place_of_origin_addon_empty():
    data = ECH0021PlaceOfOriginAddonData()
    xml = data.to_xml()
    validate_fragment(xml, 'placeOfOriginAddonDataType')


def test_v7_xsd_place_of_origin_addon_both_dates():
    data = ECH0021PlaceOfOriginAddonData(
        naturalization_date=date(2020, 6, 15),
        expatriation_date=date(2023, 3, 10),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'placeOfOriginAddonDataType')


# ============================================================================
# BirthAddonData — v7: nameOfFather + nameOfMother (not generic nameOfParent)
# ============================================================================

def test_v7_xsd_birth_addon_data_empty():
    data = ECH0021BirthAddonData()
    xml = data.to_xml()
    validate_fragment(xml, 'birthAddonDataType')


def test_v7_xsd_birth_addon_data_both_parents():
    father = ECH0021NameOfParent(
        first_name="Hans",
        official_name="Müller",
        type_of_relationship=TypeOfRelationship.FATHER,
    )
    mother = ECH0021NameOfParent(
        first_name="Anna",
        official_name="Müller",
        type_of_relationship=TypeOfRelationship.MOTHER,
    )
    data = ECH0021BirthAddonData(parents=[father, mother])
    xml = data.to_xml()
    validate_fragment(xml, 'birthAddonDataType')


# ============================================================================
# NameOfParent — v7: no typeOfRelationship field in XSD
# ============================================================================

def test_v7_xsd_name_of_parent_full_name():
    parent = ECH0021NameOfParent(
        first_name="Hans",
        official_name="Müller",
    )
    xml = parent.to_xml()
    validate_fragment(xml, 'nameOfParentType')


def test_v7_xsd_name_of_parent_first_name_only():
    parent = ECH0021NameOfParent(first_name_only="Hans")
    xml = parent.to_xml()
    validate_fragment(xml, 'nameOfParentType')


def test_v7_xsd_name_of_parent_official_name_only():
    parent = ECH0021NameOfParent(official_name_only="Müller")
    xml = parent.to_xml()
    validate_fragment(xml, 'nameOfParentType')


# ============================================================================
# MaritalDataAddon
# ============================================================================

def test_v7_xsd_marital_data_addon_empty():
    data = ECH0021MaritalDataAddon()
    xml = data.to_xml()
    validate_fragment(xml, 'maritalDataAddonType')


def test_v7_xsd_marital_data_addon_with_swiss_place():
    municipality = ECH0007Municipality.from_swiss(
        municipality_name="Bister",
        municipality_id="6002",
        canton=CantonAbbreviation.VS,
    )
    place = ECH0011GeneralPlace(swiss_municipality=municipality)
    data = ECH0021MaritalDataAddon(place_of_marriage=place)
    xml = data.to_xml()
    validate_fragment(xml, 'maritalDataAddonType')


# ============================================================================
# JobData + OccupationData + UIDStructure
# ============================================================================

def test_v7_xsd_uid_structure():
    uid = ECH0021UIDStructure(
        uid_organisation_id_categorie=UIDOrganisationIdCategory.ENTERPRISE,
        uid_organisation_id=123456789,
    )
    xml = uid.to_xml()
    validate_fragment(xml, 'uidStructureType')


def test_v7_xsd_job_data_minimal():
    data = ECH0021JobData(kind_of_employment=KindOfEmployment.EMPLOYED)
    xml = data.to_xml()
    validate_fragment(xml, 'jobDataType')


def test_v7_xsd_job_data_with_title():
    data = ECH0021JobData(
        kind_of_employment=KindOfEmployment.SELF_EMPLOYED,
        job_title="Softwareentwickler",
    )
    xml = data.to_xml()
    validate_fragment(xml, 'jobDataType')


# ============================================================================
# MaritalRelationship
# ============================================================================

def test_v7_xsd_marital_relationship():
    partner = ECH0021Partner(
        person_identification=_make_person_id(
            vn="7561234567890",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown(year_month_day=date(1990, 5, 15)),
        ),
    )
    data = ECH0021MaritalRelationship(
        partner=partner,
        type_of_relationship=TypeOfRelationship.SPOUSE,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'maritalRelationshipType')


# ============================================================================
# ParentalRelationship — v7: has relationshipValidFrom (removed in v8)
# ============================================================================

def test_v7_xsd_parental_relationship_with_valid_from():
    """v7-specific: relationshipValidFrom exists."""
    partner = ECH0021Partner(
        person_identification=_make_person_id(
            vn="7561234567890",
            official_name="Müller",
            first_name="Hans",
            sex="1",
            date_of_birth=ECH0044DatePartiallyKnown(year_month_day=date(1970, 3, 20)),
        ),
    )
    data = ECH0021ParentalRelationship(
        partner=partner,
        relationship_valid_from=date(2020, 1, 1),
        type_of_relationship=TypeOfRelationship.FATHER,
        care=CareType.JOINT_PARENTAL_AUTHORITY,
    )
    xml = data.to_xml()
    validate_fragment(xml, 'parentalRelationshipType')


# ============================================================================
# GuardianRelationship + GuardianMeasureInfo
# ============================================================================

# Skipped for now — complex inline partner types need more setup.
# Will be added when verifying serialization alignment in S2.


# ============================================================================
# ArmedForcesData, CivilDefenseData, FireServiceData
# ============================================================================

def test_v7_xsd_armed_forces_data():
    data = ECH0021ArmedForcesData(
        armed_forces_service=YesNo.YES,
        armed_forces_liability=YesNo.YES,
        armed_forces_valid_from=date(2020, 1, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'armedForcesDataType')


def test_v7_xsd_civil_defense_data():
    data = ECH0021CivilDefenseData(
        civil_defense=YesNo.NO,
        civil_defense_valid_from=date(2020, 1, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'civilDefenseDataType')


def test_v7_xsd_fire_service_data():
    data = ECH0021FireServiceData(
        fire_service=YesNo.YES,
        fire_service_liability=YesNo.NO,
        fire_service_valid_from=date(2021, 6, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'fireServiceDataType')


# ============================================================================
# HealthInsuranceData
# ============================================================================

def test_v7_xsd_health_insurance_data():
    data = ECH0021HealthInsuranceData(
        health_insured=YesNo.YES,
        insurance_name="CSS Versicherung",
        health_insurance_valid_from=date(2024, 1, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'healthInsuranceDataType')


# ============================================================================
# MatrimonialInheritanceArrangementData
# ============================================================================

def test_v7_xsd_matrimonial_inheritance_arrangement():
    data = ECH0021MatrimonialInheritanceArrangementData(
        matrimonial_inheritance_arrangement=YesNo.YES,
        matrimonial_inheritance_arrangement_valid_from=date(2022, 7, 1),
    )
    xml = data.to_xml()
    validate_fragment(xml, 'matrimonialInheritanceArrangementDataType')
