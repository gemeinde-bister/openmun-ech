"""Tests for eCH-0021 v8 Person Additional Data models.

Tests roundtrip XML serialization/deserialization and data validation.
"""

import pytest
import xml.etree.ElementTree as ET
from datetime import date

from openmun_ech.ech0021 import (
    TypeOfRelationship,
    CareType,
    KindOfEmployment,
    YesNo,
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
    ECH0021GuardianMeasureInfo,
    ECH0021GuardianRelationship,
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021HealthInsuranceData,
    ECH0021MatrimonialInheritanceArrangementData,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification, ECH0044DatePartiallyKnown, ECH0044NamedPersonId
from openmun_ech.ech0011 import ECH0011GeneralPlace
from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation


# ============================================================================
# PersonAdditionalData Tests
# ============================================================================

def test_person_additional_data_minimal():
    """Test minimal person additional data."""
    data = ECH0021PersonAdditionalData()

    xml = data.to_xml()
    assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0021/8}personAdditionalData'

    roundtrip = ECH0021PersonAdditionalData.from_xml(xml)
    assert roundtrip.mr_mrs is None
    assert roundtrip.title is None
    assert roundtrip.language_of_correspondance is None


def test_person_additional_data_complete():
    """Test complete person additional data."""
    from openmun_ech.ech0021 import MrMrs

    data = ECH0021PersonAdditionalData(
        mr_mrs=MrMrs.MR,
        title="Dr.",
        language_of_correspondance="de"
    )

    xml = data.to_xml()
    roundtrip = ECH0021PersonAdditionalData.from_xml(xml)

    assert roundtrip.mr_mrs == MrMrs.MR
    assert roundtrip.title == "Dr."
    assert roundtrip.language_of_correspondance == "de"


# ============================================================================
# LockData Tests
# ============================================================================

def test_lock_data_minimal():
    """Test minimal lock data with all locks set to NO."""
    data = ECH0021LockData(
        address_lock=YesNo.NO,
        data_lock=YesNo.NO,
        paper_lock=YesNo.NO
    )

    xml = data.to_xml()
    assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0021/8}lockData'

    roundtrip = ECH0021LockData.from_xml(xml)
    assert roundtrip.address_lock == YesNo.NO
    assert roundtrip.data_lock == YesNo.NO
    assert roundtrip.paper_lock == YesNo.NO


def test_lock_data_with_validity():
    """Test lock data with validity dates."""
    data = ECH0021LockData(
        address_lock=YesNo.YES,
        address_lock_valid_from=date(2024, 1, 1),
        address_lock_valid_till=date(2024, 12, 31),
        data_lock=YesNo.YES,
        data_lock_valid_from=date(2024, 1, 1),
        paper_lock=YesNo.NO
    )

    xml = data.to_xml()
    roundtrip = ECH0021LockData.from_xml(xml)

    assert roundtrip.address_lock == YesNo.YES
    assert roundtrip.address_lock_valid_from == date(2024, 1, 1)
    assert roundtrip.address_lock_valid_till == date(2024, 12, 31)
    assert roundtrip.data_lock == YesNo.YES
    assert roundtrip.data_lock_valid_from == date(2024, 1, 1)
    assert roundtrip.paper_lock == YesNo.NO


# ============================================================================
# PlaceOfOriginAddonData Tests
# ============================================================================

def test_place_of_origin_addon_empty():
    """Test empty place of origin addon."""
    data = ECH0021PlaceOfOriginAddonData()

    xml = data.to_xml()
    roundtrip = ECH0021PlaceOfOriginAddonData.from_xml(xml)

    assert roundtrip.naturalization_date is None
    assert roundtrip.expatriation_date is None


def test_place_of_origin_addon_naturalization():
    """Test place of origin addon with naturalization date."""
    data = ECH0021PlaceOfOriginAddonData(
        naturalization_date=date(2020, 6, 15)
    )

    xml = data.to_xml()
    roundtrip = ECH0021PlaceOfOriginAddonData.from_xml(xml)

    assert roundtrip.naturalization_date == date(2020, 6, 15)
    assert roundtrip.expatriation_date is None


def test_place_of_origin_addon_expatriation():
    """Test place of origin addon with expatriation date."""
    data = ECH0021PlaceOfOriginAddonData(
        expatriation_date=date(2021, 3, 10)
    )

    xml = data.to_xml()
    roundtrip = ECH0021PlaceOfOriginAddonData.from_xml(xml)

    assert roundtrip.naturalization_date is None
    assert roundtrip.expatriation_date == date(2021, 3, 10)


# ============================================================================
# MaritalDataAddon Tests
# ============================================================================

def test_marital_data_addon_empty():
    """Test empty marital data addon."""
    data = ECH0021MaritalDataAddon()

    xml = data.to_xml()
    roundtrip = ECH0021MaritalDataAddon.from_xml(xml)

    assert roundtrip.place_of_marriage is None


def test_marital_data_addon_with_place():
    """Test marital data addon with Swiss place of marriage."""
    municipality = ECH0007Municipality.from_swiss(
        municipality_name="Bern",
        municipality_id="351",
        canton=CantonAbbreviation.BE
    )
    place = ECH0011GeneralPlace(swiss_municipality=municipality)

    data = ECH0021MaritalDataAddon(
        place_of_marriage=place
    )

    xml = data.to_xml()
    roundtrip = ECH0021MaritalDataAddon.from_xml(xml)

    assert roundtrip.place_of_marriage is not None
    assert roundtrip.place_of_marriage.swiss_municipality is not None
    assert roundtrip.place_of_marriage.swiss_municipality.name == "Bern"


# ============================================================================
# NameOfParent Tests
# ============================================================================

def test_name_of_parent_full_name():
    """Test name of parent with both first and official name."""
    parent = ECH0021NameOfParent(
        first_name="Hans",
        official_name="Müller",
        type_of_relationship=TypeOfRelationship.FATHER,
        official_proof_of_name_of_parents_yes_no=True
    )

    xml = parent.to_xml()
    roundtrip = ECH0021NameOfParent.from_xml(xml)

    assert roundtrip.first_name == "Hans"
    assert roundtrip.official_name == "Müller"
    assert roundtrip.type_of_relationship == TypeOfRelationship.FATHER
    assert roundtrip.official_proof_of_name_of_parents_yes_no is True


def test_name_of_parent_first_name_only():
    """Test name of parent with first name only."""
    parent = ECH0021NameOfParent(
        first_name_only="Maria",
        type_of_relationship=TypeOfRelationship.MOTHER
    )

    xml = parent.to_xml()
    roundtrip = ECH0021NameOfParent.from_xml(xml)

    assert roundtrip.first_name_only == "Maria"
    assert roundtrip.official_name_only is None
    assert roundtrip.type_of_relationship == TypeOfRelationship.MOTHER


def test_name_of_parent_official_name_only():
    """Test name of parent with official name only."""
    parent = ECH0021NameOfParent(
        official_name_only="Schmidt"
    )

    xml = parent.to_xml()
    roundtrip = ECH0021NameOfParent.from_xml(xml)

    assert roundtrip.official_name_only == "Schmidt"
    assert roundtrip.first_name_only is None


def test_name_of_parent_invalid_relationship():
    """Test that invalid relationship type raises error."""
    with pytest.raises(ValueError):
        ECH0021NameOfParent(
            first_name="Test",
            official_name="Test",
            type_of_relationship=TypeOfRelationship.SPOUSE  # Invalid for parent
        )


# ============================================================================
# BirthAddonData Tests
# ============================================================================

def test_birth_addon_data_empty():
    """Test empty birth addon data."""
    data = ECH0021BirthAddonData()

    xml = data.to_xml()
    roundtrip = ECH0021BirthAddonData.from_xml(xml)

    assert len(roundtrip.name_of_parent) == 0


def test_birth_addon_data_both_parents():
    """Test birth addon data with both parents."""
    father = ECH0021NameOfParent(
        first_name="Hans",
        official_name="Müller",
        type_of_relationship=TypeOfRelationship.FATHER
    )
    mother = ECH0021NameOfParent(
        first_name="Maria",
        official_name="Müller",
        type_of_relationship=TypeOfRelationship.MOTHER
    )

    data = ECH0021BirthAddonData(
        name_of_parent=[father, mother]
    )

    xml = data.to_xml()
    roundtrip = ECH0021BirthAddonData.from_xml(xml)

    assert len(roundtrip.name_of_parent) == 2
    assert roundtrip.name_of_parent[0].type_of_relationship == TypeOfRelationship.FATHER
    assert roundtrip.name_of_parent[1].type_of_relationship == TypeOfRelationship.MOTHER


# ============================================================================
# JobData Tests
# ============================================================================

def test_uid_structure():
    """Test UID structure."""
    uid = ECH0021UIDStructure(
        uid_organisation_id_categorie="CHE",
        uid_organisation_id=123456789
    )

    xml = uid.to_xml()
    roundtrip = ECH0021UIDStructure.from_xml(xml)

    assert roundtrip.uid_organisation_id_categorie == "CHE"
    assert roundtrip.uid_organisation_id == 123456789


def test_job_data_minimal():
    """Test minimal job data."""
    data = ECH0021JobData(
        kind_of_employment=KindOfEmployment.EMPLOYED
    )

    xml = data.to_xml()
    roundtrip = ECH0021JobData.from_xml(xml)

    assert roundtrip.kind_of_employment == KindOfEmployment.EMPLOYED
    assert roundtrip.job_title is None
    assert len(roundtrip.occupation_data) == 0


def test_job_data_complete():
    """Test complete job data."""
    uid = ECH0021UIDStructure(
        uid_organisation_id_categorie="CHE",
        uid_organisation_id=123456789
    )
    occupation = ECH0021OccupationData(
        uid=uid,
        employer="Test AG",
        occupation_valid_from=date(2024, 1, 1)
    )

    data = ECH0021JobData(
        kind_of_employment=KindOfEmployment.EMPLOYED,
        job_title="Software Engineer",
        occupation_data=[occupation]
    )

    xml = data.to_xml()
    roundtrip = ECH0021JobData.from_xml(xml)

    assert roundtrip.kind_of_employment == KindOfEmployment.EMPLOYED
    assert roundtrip.job_title == "Software Engineer"
    assert len(roundtrip.occupation_data) == 1
    assert roundtrip.occupation_data[0].employer == "Test AG"


# ============================================================================
# Relationship Tests
# ============================================================================

def test_partner_minimal():
    """Test minimal partner with person identification only."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="123"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1980, 5, 15))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Müller",
        first_name="Hans",
        sex="1",
        date_of_birth=dob
    )

    partner = ECH0021Partner(
        person_identification=person_id
    )

    xml = partner.to_xml()
    roundtrip = ECH0021Partner.from_xml(xml)

    assert roundtrip.person_identification.official_name == "Müller"
    assert roundtrip.person_identification.first_name == "Hans"
    assert roundtrip.address is None


def test_marital_relationship():
    """Test marital relationship."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="124"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1982, 8, 20))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Schmidt",
        first_name="Maria",
        sex="2",
        date_of_birth=dob
    )

    partner = ECH0021Partner(
        person_identification=person_id
    )

    relationship = ECH0021MaritalRelationship(
        partner=partner,
        type_of_relationship=TypeOfRelationship.SPOUSE
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021MaritalRelationship.from_xml(xml)

    assert roundtrip.partner.person_identification.official_name == "Schmidt"
    assert roundtrip.type_of_relationship == TypeOfRelationship.SPOUSE


def test_parental_relationship():
    """Test parental relationship."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="125"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1980, 5, 15))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Müller",
        first_name="Hans",
        sex="1",
        date_of_birth=dob
    )

    partner = ECH0021Partner(
        person_identification=person_id
    )

    relationship = ECH0021ParentalRelationship(
        partner=partner,
        type_of_relationship=TypeOfRelationship.FATHER,
        care=CareType.JOINT_PARENTAL_AUTHORITY
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021ParentalRelationship.from_xml(xml)

    assert roundtrip.partner.person_identification.official_name == "Müller"
    assert roundtrip.type_of_relationship == TypeOfRelationship.FATHER
    assert roundtrip.care == CareType.JOINT_PARENTAL_AUTHORITY


# ============================================================================
# Guardian Relationship Tests
# ============================================================================

def test_guardian_measure_info_minimal():
    """Test minimal guardian measure info with no legal basis."""
    data = ECH0021GuardianMeasureInfo(
        guardian_measure_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0021/8}guardianMeasureInfo'

    roundtrip = ECH0021GuardianMeasureInfo.from_xml(xml)
    assert len(roundtrip.based_on_law) == 0
    assert roundtrip.based_on_law_add_on is None
    assert roundtrip.guardian_measure_valid_from == date(2024, 1, 1)


def test_guardian_measure_info_with_legal_basis():
    """Test guardian measure info with ZGB articles."""
    data = ECH0021GuardianMeasureInfo(
        based_on_law=["398", "363"],  # Umfassende Beistandschaft + Vorsorgeauftrag
        based_on_law_add_on="Additional legal context",
        guardian_measure_valid_from=date(2024, 6, 15)
    )

    xml = data.to_xml()
    roundtrip = ECH0021GuardianMeasureInfo.from_xml(xml)

    assert len(roundtrip.based_on_law) == 2
    assert "398" in roundtrip.based_on_law
    assert "363" in roundtrip.based_on_law
    assert roundtrip.based_on_law_add_on == "Additional legal context"
    assert roundtrip.guardian_measure_valid_from == date(2024, 6, 15)


def test_guardian_measure_info_all_zgb_articles():
    """Test guardian measure info with all 18 valid ZGB articles."""
    all_articles = [
        "306", "310", "311", "312", "327-a", "363", "368", "369", "370",
        "371", "372", "393", "394", "395", "396", "397", "398", "399"
    ]

    data = ECH0021GuardianMeasureInfo(
        based_on_law=all_articles,
        guardian_measure_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    roundtrip = ECH0021GuardianMeasureInfo.from_xml(xml)

    assert len(roundtrip.based_on_law) == 18
    for article in all_articles:
        assert article in roundtrip.based_on_law


def test_guardian_measure_info_invalid_article():
    """Test that invalid ZGB article raises validation error."""
    with pytest.raises(ValueError, match="Invalid ZGB article"):
        ECH0021GuardianMeasureInfo(
            based_on_law=["999"],  # Invalid article number
            guardian_measure_valid_from=date(2024, 1, 1)
        )


def test_guardian_relationship_person_guardian():
    """Test guardian relationship with legal assistant (Beistand)."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="200"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1975, 3, 10))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Weber",
        first_name="Anna",
        sex="2",
        date_of_birth=dob
    )

    measure_info = ECH0021GuardianMeasureInfo(
        based_on_law=["398"],  # Umfassende Beistandschaft
        guardian_measure_valid_from=date(2024, 1, 1)
    )

    relationship = ECH0021GuardianRelationship(
        guardian_relationship_id="GUARD-001",
        person_identification=person_id,
        type_of_relationship=TypeOfRelationship.LEGAL_ASSISTANT,
        guardian_measure_info=measure_info,
        care=CareType.SOLE_PARENTAL_AUTHORITY
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021GuardianRelationship.from_xml(xml)

    assert roundtrip.guardian_relationship_id == "GUARD-001"
    assert roundtrip.person_identification is not None
    assert roundtrip.person_identification.official_name == "Weber"
    assert roundtrip.type_of_relationship == TypeOfRelationship.LEGAL_ASSISTANT
    assert roundtrip.guardian_measure_info.based_on_law == ["398"]
    assert roundtrip.care == CareType.SOLE_PARENTAL_AUTHORITY


def test_guardian_relationship_organization_guardian():
    """Test guardian relationship with advisor organization (deprecated)."""
    from openmun_ech.ech0011 import ECH0011PartnerIdOrganisation

    org_local_id = ECH0044NamedPersonId(
        person_id_category="UID",
        person_id="CHE123456789"
    )

    org = ECH0011PartnerIdOrganisation(
        local_person_id=org_local_id
    )

    measure_info = ECH0021GuardianMeasureInfo(
        based_on_law=["310", "311"],  # Entziehung elterliche Obhut + Sorge
        based_on_law_add_on="KESB-Entscheid vom 2024-01-15",
        guardian_measure_valid_from=date(2024, 1, 15)
    )

    relationship = ECH0021GuardianRelationship(
        guardian_relationship_id="KESB-2024-001",
        partner_id_organisation=org,
        type_of_relationship=TypeOfRelationship.ADVISOR,
        guardian_measure_info=measure_info
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021GuardianRelationship.from_xml(xml)

    assert roundtrip.guardian_relationship_id == "KESB-2024-001"
    assert roundtrip.partner_id_organisation is not None
    assert roundtrip.partner_id_organisation.local_person_id.person_id == "CHE123456789"
    assert roundtrip.type_of_relationship == TypeOfRelationship.ADVISOR
    assert "310" in roundtrip.guardian_measure_info.based_on_law
    assert "311" in roundtrip.guardian_measure_info.based_on_law


def test_guardian_relationship_invalid_type():
    """Test that invalid guardian type raises validation error."""
    measure_info = ECH0021GuardianMeasureInfo(
        guardian_measure_valid_from=date(2024, 1, 1)
    )

    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="200"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1975, 3, 10))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Weber",
        first_name="Anna",
        sex="2",
        date_of_birth=dob
    )

    with pytest.raises(ValueError, match="Guardian relationship must be"):
        ECH0021GuardianRelationship(
            guardian_relationship_id="GUARD-001",
            person_identification=person_id,
            type_of_relationship=TypeOfRelationship.SPOUSE,  # Invalid - not guardian type
            guardian_measure_info=measure_info
        )


def test_guardian_relationship_multiple_partner_types():
    """Test that having multiple partner types raises validation error."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="200"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1975, 3, 10))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Weber",
        first_name="Anna",
        sex="2",
        date_of_birth=dob
    )

    from openmun_ech.ech0011 import ECH0011PartnerIdOrganisation
    org_local_id = ECH0044NamedPersonId(
        person_id_category="UID",
        person_id="CHE123456789"
    )
    org = ECH0011PartnerIdOrganisation(local_person_id=org_local_id)

    measure_info = ECH0021GuardianMeasureInfo(
        guardian_measure_valid_from=date(2024, 1, 1)
    )

    # This should fail - can't have both person and organization
    with pytest.raises(ValueError, match="at most ONE"):
        ECH0021GuardianRelationship(
            guardian_relationship_id="GUARD-001",
            person_identification=person_id,
            partner_id_organisation=org,  # Both set - should fail
            type_of_relationship=TypeOfRelationship.LEGAL_ASSISTANT,
            guardian_measure_info=measure_info
        )


def test_guardian_relationship_legal_representative():
    """Test guardian relationship with legal representative (type 9)."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="201"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1970, 8, 25))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Fischer",
        first_name="Thomas",
        sex="1",
        date_of_birth=dob
    )

    measure_info = ECH0021GuardianMeasureInfo(
        based_on_law=["393", "394"],  # Begleit- + Vertretungsbeistandschaft
        guardian_measure_valid_from=date(2024, 3, 1)
    )

    relationship = ECH0021GuardianRelationship(
        guardian_relationship_id="REP-2024-005",
        person_identification=person_id,
        type_of_relationship=TypeOfRelationship.GUARDIAN,
        guardian_measure_info=measure_info
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021GuardianRelationship.from_xml(xml)

    assert roundtrip.type_of_relationship == TypeOfRelationship.GUARDIAN
    assert roundtrip.person_identification.first_name == "Thomas"


def test_guardian_relationship_curator():
    """Test guardian relationship with curator (type 10)."""
    local_id = ECH0044NamedPersonId(
        person_id_category="MU.6172",
        person_id="202"
    )
    dob = ECH0044DatePartiallyKnown.from_date(date(1968, 12, 5))

    person_id = ECH0044PersonIdentification(
        local_person_id=local_id,
        official_name="Meier",
        first_name="Elisabeth",
        sex="2",
        date_of_birth=dob
    )

    measure_info = ECH0021GuardianMeasureInfo(
        based_on_law=["396"],  # Mitwirkungsbeistandschaft
        guardian_measure_valid_from=date(2024, 5, 10)
    )

    relationship = ECH0021GuardianRelationship(
        guardian_relationship_id="CUR-2024-012",
        person_identification=person_id,
        type_of_relationship=TypeOfRelationship.HEALTHCARE_PROXY,
        guardian_measure_info=measure_info
    )

    xml = relationship.to_xml()
    roundtrip = ECH0021GuardianRelationship.from_xml(xml)

    assert roundtrip.type_of_relationship == TypeOfRelationship.HEALTHCARE_PROXY
    assert roundtrip.guardian_relationship_id == "CUR-2024-012"


# ============================================================================
# Optional Data Tests
# ============================================================================

def test_armed_forces_data():
    """Test armed forces data."""
    data = ECH0021ArmedForcesData(
        armed_forces_service=YesNo.YES,
        armed_forces_liability=YesNo.YES,
        armed_forces_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    roundtrip = ECH0021ArmedForcesData.from_xml(xml)

    assert roundtrip.armed_forces_service == YesNo.YES
    assert roundtrip.armed_forces_liability == YesNo.YES
    assert roundtrip.armed_forces_valid_from == date(2024, 1, 1)


def test_civil_defense_data():
    """Test civil defense data."""
    data = ECH0021CivilDefenseData(
        civil_defense=YesNo.NO,
        civil_defense_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    roundtrip = ECH0021CivilDefenseData.from_xml(xml)

    assert roundtrip.civil_defense == YesNo.NO
    assert roundtrip.civil_defense_valid_from == date(2024, 1, 1)


def test_fire_service_data():
    """Test fire service data."""
    data = ECH0021FireServiceData(
        fire_service=YesNo.YES,
        fire_service_liability=YesNo.NO
    )

    xml = data.to_xml()
    roundtrip = ECH0021FireServiceData.from_xml(xml)

    assert roundtrip.fire_service == YesNo.YES
    assert roundtrip.fire_service_liability == YesNo.NO


def test_health_insurance_data():
    """Test health insurance data."""
    data = ECH0021HealthInsuranceData(
        health_insured=YesNo.YES,
        insurance_name="CSS Versicherung",
        health_insurance_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    roundtrip = ECH0021HealthInsuranceData.from_xml(xml)

    assert roundtrip.health_insured == YesNo.YES
    assert roundtrip.insurance_name == "CSS Versicherung"
    assert roundtrip.health_insurance_valid_from == date(2024, 1, 1)


def test_matrimonial_inheritance_arrangement_data():
    """Test matrimonial inheritance arrangement data."""
    data = ECH0021MatrimonialInheritanceArrangementData(
        matrimonial_inheritance_arrangement=YesNo.YES,
        matrimonial_inheritance_arrangement_valid_from=date(2024, 1, 1)
    )

    xml = data.to_xml()
    roundtrip = ECH0021MatrimonialInheritanceArrangementData.from_xml(xml)

    assert roundtrip.matrimonial_inheritance_arrangement == YesNo.YES
    assert roundtrip.matrimonial_inheritance_arrangement_valid_from == date(2024, 1, 1)
