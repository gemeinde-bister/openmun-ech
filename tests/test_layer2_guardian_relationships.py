"""Tests 23-25: Guardian Relationships

Tests Layer 2 handling of guardian relationships:
- Test 23: Person guardian (individual guardian with full identification)
- Test 24: Organization guardian (KESB - Kindes- und Erwachsenenschutzbehörde)
- Test 25: Partner guardian (person_identification_partner type)

These tests validate the three guardian types and their CHOICE constraints.

Tests verify:
1. Layer 2 construction with guardians list
2. to_ech0020() conversion (Layer 2 → Layer 1 guardian_relationship list)
3. from_ech0020() conversion (Layer 1 → Layer 2 guardians list)
4. Full roundtrip with zero data loss
5. CHOICE constraints (person vs organization vs partner)

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, ZGB articles)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType, PersonIdentification, GuardianInfo, GuardianType


class TestGuardianRelationships:
    """Test Layer 2 guardian relationship fields."""

    def test_person_guardian_with_full_identification(self):
        """Test 23: Person guardian with full identification.

        Tests:
        - guardians list with 1 entry (GuardianInfo model)
        - guardian_type=PERSON
        - person field (PersonIdentification with VN, local_person_id)
        - NO organization fields (CHOICE constraint)
        - relationship_type="7" (guardian_person)
        - guardian_measure_based_on_law (list of ZGB articles: 310, 327-a)
        - guardian_measure_valid_from (required date)
        - care=None (optional, testing without it)
        - Use case: Individual appointed as guardian for minor
        - Stored in ECH0021GuardianRelationship with person_identification
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (minor child) with person guardian
        person_guardian = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schneider",
            first_name="Sophie",
            sex="2",  # female
            date_of_birth=date(2015, 8, 10),  # minor child

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="1",  # unmarried (child)

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship (required - Swiss)
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Guardian: Person guardian
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-001",
                    guardian_type=GuardianType.PERSON,
                    person=PersonIdentification(
                        vn="7569871234567",
                        local_person_id="guard-001",
                        local_person_id_category="MU.6172",
                        official_name="Weber",
                        first_name="Thomas",
                        original_name=None,
                        sex="1",  # male
                        date_of_birth=date(1978, 3, 20)
                    ),
                    organization_uid=None,  # Not organization guardian
                    organization_name=None,
                    relationship_type="7",  # guardian_person
                    guardian_measure_based_on_law=["310", "327-a"],  # ZGB articles
                    guardian_measure_valid_from=date(2020, 1, 15),
                    care=None  # Optional, testing without it
                )
            ]
        )

        # Convert to Layer 1
        layer1_person_guardian = person_guardian.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_person_guardian.guardian_relationship is not None, \
            "guardian_relationship should be present"
        assert len(layer1_person_guardian.guardian_relationship) == 1, \
            f"Expected 1 guardian, got {len(layer1_person_guardian.guardian_relationship)}"

        guardian_rel = layer1_person_guardian.guardian_relationship[0]

        # Verify this is a PERSON guardian (person_identification field set)
        assert guardian_rel.person_identification is not None, \
            "person_identification should be present for PERSON guardian"
        assert guardian_rel.person_identification_partner is None, \
            "person_identification_partner should be None for PERSON guardian"
        assert guardian_rel.partner_id_organisation is None, \
            "partner_id_organisation should be None for PERSON guardian"

        # Verify guardian person identification
        guardian_person_id = guardian_rel.person_identification
        assert guardian_person_id.official_name == "Weber", \
            f"Expected guardian official_name='Weber', got {guardian_person_id.official_name}"
        assert guardian_person_id.first_name == "Thomas", \
            f"Expected guardian first_name='Thomas', got {guardian_person_id.first_name}"
        assert guardian_person_id.vn == "7569871234567", \
            f"Expected guardian vn='7569871234567', got {guardian_person_id.vn}"

        # Verify sex
        guardian_sex = guardian_person_id.sex.value if hasattr(guardian_person_id.sex, 'value') else str(guardian_person_id.sex)
        assert guardian_sex == "1", f"Expected guardian sex='1', got {guardian_sex}"

        # Verify date_of_birth
        guardian_dob = guardian_person_id.date_of_birth
        if hasattr(guardian_dob, 'year_month_day'):
            actual_guardian_dob = guardian_dob.year_month_day
        else:
            actual_guardian_dob = guardian_dob
        assert actual_guardian_dob == date(1978, 3, 20), \
            f"Expected guardian DOB=1978-03-20, got {actual_guardian_dob}"

        # Verify local_person_id
        assert guardian_person_id.local_person_id is not None, \
            "guardian local_person_id should be present"
        assert guardian_person_id.local_person_id.person_id == "guard-001", \
            f"Expected guardian local_person_id='guard-001', got {guardian_person_id.local_person_id.person_id}"

        # Verify relationship metadata
        assert guardian_rel.guardian_relationship_id == "guardian-rel-001", \
            f"Expected guardian_relationship_id='guardian-rel-001', got {guardian_rel.guardian_relationship_id}"
        assert guardian_rel.type_of_relationship == "7", \
            f"Expected type_of_relationship='7', got {guardian_rel.type_of_relationship}"

        # Verify guardian_measure_info
        assert guardian_rel.guardian_measure_info is not None, \
            "guardian_measure_info should be present"
        assert guardian_rel.guardian_measure_info.based_on_law == ["310", "327-a"], \
            f"Expected based_on_law=['310', '327-a'], got {guardian_rel.guardian_measure_info.based_on_law}"
        assert guardian_rel.guardian_measure_info.guardian_measure_valid_from == date(2020, 1, 15), \
            f"Expected guardian_measure_valid_from=2020-01-15, got {guardian_rel.guardian_measure_info.guardian_measure_valid_from}"

        # Verify care is None (optional field not provided)
        assert guardian_rel.care is None, \
            f"Expected care=None, got {guardian_rel.care}"

        # Roundtrip: Layer 1 → Layer 2
        person_guardian_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_person_guardian)

        # Verify guardians list preserved
        assert person_guardian_roundtrip.guardians is not None, \
            "guardians should be preserved"
        assert len(person_guardian_roundtrip.guardians) == 1, \
            f"Expected 1 guardian in roundtrip, got {len(person_guardian_roundtrip.guardians)}"

        # Verify guardian data preserved
        guardian_roundtrip = person_guardian_roundtrip.guardians[0]

        assert guardian_roundtrip.guardian_type == GuardianType.PERSON, \
            f"Expected guardian_type=PERSON, got {guardian_roundtrip.guardian_type}"
        assert guardian_roundtrip.guardian_relationship_id == "guardian-rel-001", \
            f"Expected guardian_relationship_id='guardian-rel-001', got {guardian_roundtrip.guardian_relationship_id}"
        assert guardian_roundtrip.relationship_type == "7", \
            f"Expected relationship_type='7', got {guardian_roundtrip.relationship_type}"

        # Verify guardian person
        assert guardian_roundtrip.person is not None, \
            "Guardian person should be present"
        assert guardian_roundtrip.person.official_name == "Weber", \
            f"Expected official_name='Weber', got {guardian_roundtrip.person.official_name}"
        assert guardian_roundtrip.person.first_name == "Thomas", \
            f"Expected first_name='Thomas', got {guardian_roundtrip.person.first_name}"
        assert guardian_roundtrip.person.vn == "7569871234567", \
            f"Expected vn='7569871234567', got {guardian_roundtrip.person.vn}"
        assert guardian_roundtrip.person.sex == "1", \
            f"Expected sex='1', got {guardian_roundtrip.person.sex}"
        assert guardian_roundtrip.person.date_of_birth == date(1978, 3, 20), \
            f"Expected DOB=1978-03-20, got {guardian_roundtrip.person.date_of_birth}"
        assert guardian_roundtrip.person.local_person_id == "guard-001", \
            f"Expected local_person_id='guard-001', got {guardian_roundtrip.person.local_person_id}"

        # Verify no organization fields (CHOICE constraint)
        assert guardian_roundtrip.organization_uid is None, \
            "organization_uid should be None for PERSON guardian"
        assert guardian_roundtrip.organization_name is None, \
            "organization_name should be None for PERSON guardian"

        # Verify guardian measure info
        assert guardian_roundtrip.guardian_measure_based_on_law == ["310", "327-a"], \
            f"Expected based_on_law=['310', '327-a'], got {guardian_roundtrip.guardian_measure_based_on_law}"
        assert guardian_roundtrip.guardian_measure_valid_from == date(2020, 1, 15), \
            f"Expected guardian_measure_valid_from=2020-01-15, got {guardian_roundtrip.guardian_measure_valid_from}"

        # Verify care is None (optional)
        assert guardian_roundtrip.care is None, \
            f"Expected care=None, got {guardian_roundtrip.care}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = person_guardian_roundtrip.to_ech0020()
        assert layer1_roundtrip.guardian_relationship is not None
        assert len(layer1_roundtrip.guardian_relationship) == 1
        assert layer1_roundtrip.guardian_relationship[0].type_of_relationship == "7"

    def test_organization_guardian_kesb(self):
        """Test 24: Organization guardian (KESB).

        Tests:
        - guardians list with 1 entry (GuardianInfo model)
        - guardian_type=ORGANISATION
        - NO person field (CHOICE constraint)
        - organization_uid (CHE-XXX.XXX.XXX format)
        - organization_name (KESB name) - preserved in roundtrip ✅
        - relationship_type="8" (guardian_org)
        - guardian_measure_based_on_law (list of ZGB articles: 310, 311)
        - guardian_measure_valid_from (required date)
        - care="1" (joint custody/care)
        - Use case: KESB (Child and Adult Protection Authority) as guardian
        - Stored in ECH0021GuardianRelationship with partner_id_organisation
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (minor child) with KESB guardian
        organization_guardian = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="77890",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Emma",
            sex="2",  # female
            date_of_birth=date(2016, 11, 22),  # minor child

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried (child)

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship (required - Swiss)
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Guardian: Organization guardian (KESB)
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-002",
                    guardian_type=GuardianType.ORGANISATION,
                    person=None,  # Not person guardian
                    organization_uid="CHE-123.456.789",  # KESB UID
                    organization_name="KESB Zürich",  # Kindes- und Erwachsenenschutzbehörde
                    # Address required to preserve organization_name (per eCH-0011 standard)
                    address_street="Weststrasse",
                    address_house_number="10",
                    address_postal_code="8003",
                    address_town="Zürich",
                    relationship_type="8",  # guardian_org
                    guardian_measure_based_on_law=["310", "311"],  # ZGB articles
                    guardian_measure_valid_from=date(2021, 6, 1),
                    care="1"  # joint custody/care (common for KESB)
                )
            ]
        )

        # Convert to Layer 1
        layer1_org_guardian = organization_guardian.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_org_guardian.guardian_relationship is not None, \
            "guardian_relationship should be present"
        assert len(layer1_org_guardian.guardian_relationship) == 1, \
            f"Expected 1 guardian, got {len(layer1_org_guardian.guardian_relationship)}"

        guardian_rel = layer1_org_guardian.guardian_relationship[0]

        # Verify this is an ORGANISATION guardian (partner_id_organisation field set)
        assert guardian_rel.partner_id_organisation is not None, \
            "partner_id_organisation should be present for ORGANISATION guardian"
        assert guardian_rel.person_identification is None, \
            "person_identification should be None for ORGANISATION guardian"
        assert guardian_rel.person_identification_partner is None, \
            "person_identification_partner should be None for ORGANISATION guardian"

        # Verify organization identification
        org_id = guardian_rel.partner_id_organisation
        assert org_id.local_person_id is not None, \
            "local_person_id (UID container) should be present"
        assert org_id.local_person_id.person_id == "CHE-123.456.789", \
            f"Expected UID='CHE-123.456.789', got {org_id.local_person_id.person_id}"
        assert org_id.local_person_id.person_id_category == "UID", \
            f"Expected person_id_category='UID', got {org_id.local_person_id.person_id_category}"

        # Verify relationship metadata
        assert guardian_rel.guardian_relationship_id == "guardian-rel-002", \
            f"Expected guardian_relationship_id='guardian-rel-002', got {guardian_rel.guardian_relationship_id}"
        assert guardian_rel.type_of_relationship == "8", \
            f"Expected type_of_relationship='8', got {guardian_rel.type_of_relationship}"

        # Verify guardian_measure_info
        assert guardian_rel.guardian_measure_info is not None, \
            "guardian_measure_info should be present"
        assert guardian_rel.guardian_measure_info.based_on_law == ["310", "311"], \
            f"Expected based_on_law=['310', '311'], got {guardian_rel.guardian_measure_info.based_on_law}"
        assert guardian_rel.guardian_measure_info.guardian_measure_valid_from == date(2021, 6, 1), \
            f"Expected guardian_measure_valid_from=2021-06-01, got {guardian_rel.guardian_measure_info.guardian_measure_valid_from}"

        # Verify care is set
        assert guardian_rel.care == "1", \
            f"Expected care='1', got {guardian_rel.care}"

        # Roundtrip: Layer 1 → Layer 2
        org_guardian_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_org_guardian)

        # Verify guardians list preserved
        assert org_guardian_roundtrip.guardians is not None, \
            "guardians should be preserved"
        assert len(org_guardian_roundtrip.guardians) == 1, \
            f"Expected 1 guardian in roundtrip, got {len(org_guardian_roundtrip.guardians)}"

        # Verify guardian data preserved
        guardian_roundtrip = org_guardian_roundtrip.guardians[0]

        assert guardian_roundtrip.guardian_type == GuardianType.ORGANISATION, \
            f"Expected guardian_type=ORGANISATION, got {guardian_roundtrip.guardian_type}"
        assert guardian_roundtrip.guardian_relationship_id == "guardian-rel-002", \
            f"Expected guardian_relationship_id='guardian-rel-002', got {guardian_roundtrip.guardian_relationship_id}"
        assert guardian_roundtrip.relationship_type == "8", \
            f"Expected relationship_type='8', got {guardian_roundtrip.relationship_type}"

        # Verify organization fields
        assert guardian_roundtrip.organization_uid == "CHE-123.456.789", \
            f"Expected organization_uid='CHE-123.456.789', got {guardian_roundtrip.organization_uid}"

        # Verify organization_name is preserved
        # NOTE: The original test noted this "may be None due to Layer 1 limitation",
        # but it turns out organization_name IS being preserved correctly now!
        assert guardian_roundtrip.organization_name == "KESB Zürich", \
            f"Expected organization_name='KESB Zürich', got {guardian_roundtrip.organization_name}"

        # Verify no person field (CHOICE constraint)
        assert guardian_roundtrip.person is None, \
            "person should be None for ORGANISATION guardian"

        # Verify guardian measure info
        assert guardian_roundtrip.guardian_measure_based_on_law == ["310", "311"], \
            f"Expected based_on_law=['310', '311'], got {guardian_roundtrip.guardian_measure_based_on_law}"
        assert guardian_roundtrip.guardian_measure_valid_from == date(2021, 6, 1), \
            f"Expected guardian_measure_valid_from=2021-06-01, got {guardian_roundtrip.guardian_measure_valid_from}"

        # Verify care preserved
        assert guardian_roundtrip.care == "1", \
            f"Expected care='1', got {guardian_roundtrip.care}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = org_guardian_roundtrip.to_ech0020()
        assert layer1_roundtrip.guardian_relationship is not None
        assert len(layer1_roundtrip.guardian_relationship) == 1
        assert layer1_roundtrip.guardian_relationship[0].type_of_relationship == "8"

    def test_partner_guardian_with_person_identification(self):
        """Test 25: Partner guardian with person identification.

        Tests:
        - guardians list with 1 entry (GuardianInfo model)
        - guardian_type=PERSON_PARTNER
        - person field (PersonIdentification)
        - NO organization fields (CHOICE constraint)
        - relationship_type="7" (guardian_person - same as PERSON type)
        - guardian_measure_based_on_law (list of ZGB articles: 310)
        - guardian_measure_valid_from (required date)
        - care="2" (sole custody mother)
        - Use case: Partner/spouse appointed as guardian
        - Stored in ECH0021GuardianRelationship with person_identification_partner
        - person_identification_partner uses ECH0044PersonIdentificationLight
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (minor child) with partner guardian
        partner_guardian = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="88901",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Liam",
            sex="1",  # male
            date_of_birth=date(2017, 3, 5),  # minor child

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried (child)

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship (required - Swiss)
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Guardian: Partner guardian (uses person_identification_partner in Layer 1)
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-003",
                    guardian_type=GuardianType.PERSON_PARTNER,
                    person=PersonIdentification(
                        vn="7569872345678",
                        local_person_id="guard-partner-001",
                        local_person_id_category="MU.6172",
                        official_name="Keller",
                        first_name="Anna",
                        original_name=None,
                        sex="2",  # female
                        date_of_birth=date(1982, 9, 12)
                    ),
                    organization_uid=None,  # Not organization guardian
                    organization_name=None,
                    relationship_type="7",  # guardian_person (same as PERSON type)
                    guardian_measure_based_on_law=["310"],  # ZGB article for guardianship
                    guardian_measure_valid_from=date(2022, 2, 10),
                    care="2"  # sole custody mother
                )
            ]
        )

        # Convert to Layer 1
        layer1_partner_guardian = partner_guardian.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_partner_guardian.guardian_relationship is not None, \
            "guardian_relationship should be present"
        assert len(layer1_partner_guardian.guardian_relationship) == 1, \
            f"Expected 1 guardian, got {len(layer1_partner_guardian.guardian_relationship)}"

        guardian_rel = layer1_partner_guardian.guardian_relationship[0]

        # Verify this is a PERSON_PARTNER guardian (person_identification_partner field set)
        assert guardian_rel.person_identification_partner is not None, \
            "person_identification_partner should be present for PERSON_PARTNER guardian"
        assert guardian_rel.person_identification is None, \
            "person_identification should be None for PERSON_PARTNER guardian"
        assert guardian_rel.partner_id_organisation is None, \
            "partner_id_organisation should be None for PERSON_PARTNER guardian"

        # Verify guardian person identification
        guardian_person_id = guardian_rel.person_identification_partner
        assert guardian_person_id.official_name == "Keller", \
            f"Expected guardian official_name='Keller', got {guardian_person_id.official_name}"
        assert guardian_person_id.first_name == "Anna", \
            f"Expected guardian first_name='Anna', got {guardian_person_id.first_name}"

        # Note: person_identification_partner uses ECH0044PersonIdentificationLight
        # VN might be in named_person_id
        guardian_vn = None
        if hasattr(guardian_person_id, 'vn') and guardian_person_id.vn:
            guardian_vn = guardian_person_id.vn
        elif hasattr(guardian_person_id, 'named_person_id') and guardian_person_id.named_person_id:
            guardian_vn = guardian_person_id.named_person_id.vn

        assert guardian_vn == "7569872345678", \
            f"Expected guardian vn='7569872345678', got {guardian_vn}"

        # Verify sex
        guardian_sex = guardian_person_id.sex.value if hasattr(guardian_person_id.sex, 'value') else str(guardian_person_id.sex)
        assert guardian_sex == "2", f"Expected guardian sex='2', got {guardian_sex}"

        # Verify date_of_birth
        guardian_dob = guardian_person_id.date_of_birth
        if hasattr(guardian_dob, 'year_month_day'):
            actual_guardian_dob = guardian_dob.year_month_day
        else:
            actual_guardian_dob = guardian_dob
        assert actual_guardian_dob == date(1982, 9, 12), \
            f"Expected guardian DOB=1982-09-12, got {actual_guardian_dob}"

        # Verify relationship metadata
        assert guardian_rel.guardian_relationship_id == "guardian-rel-003", \
            f"Expected guardian_relationship_id='guardian-rel-003', got {guardian_rel.guardian_relationship_id}"
        assert guardian_rel.type_of_relationship == "7", \
            f"Expected type_of_relationship='7', got {guardian_rel.type_of_relationship}"

        # Verify guardian_measure_info
        assert guardian_rel.guardian_measure_info is not None, \
            "guardian_measure_info should be present"
        assert guardian_rel.guardian_measure_info.based_on_law == ["310"], \
            f"Expected based_on_law=['310'], got {guardian_rel.guardian_measure_info.based_on_law}"
        assert guardian_rel.guardian_measure_info.guardian_measure_valid_from == date(2022, 2, 10), \
            f"Expected guardian_measure_valid_from=2022-02-10, got {guardian_rel.guardian_measure_info.guardian_measure_valid_from}"

        # Verify care is set
        assert guardian_rel.care == "2", \
            f"Expected care='2', got {guardian_rel.care}"

        # Roundtrip: Layer 1 → Layer 2
        partner_guardian_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_partner_guardian)

        # Verify guardians list preserved
        assert partner_guardian_roundtrip.guardians is not None, \
            "guardians should be preserved"
        assert len(partner_guardian_roundtrip.guardians) == 1, \
            f"Expected 1 guardian in roundtrip, got {len(partner_guardian_roundtrip.guardians)}"

        # Verify guardian data preserved
        guardian_roundtrip = partner_guardian_roundtrip.guardians[0]

        assert guardian_roundtrip.guardian_type == GuardianType.PERSON_PARTNER, \
            f"Expected guardian_type=PERSON_PARTNER, got {guardian_roundtrip.guardian_type}"
        assert guardian_roundtrip.guardian_relationship_id == "guardian-rel-003", \
            f"Expected guardian_relationship_id='guardian-rel-003', got {guardian_roundtrip.guardian_relationship_id}"
        assert guardian_roundtrip.relationship_type == "7", \
            f"Expected relationship_type='7', got {guardian_roundtrip.relationship_type}"

        # Verify guardian person
        assert guardian_roundtrip.person is not None, \
            "Guardian person should be present"
        assert guardian_roundtrip.person.official_name == "Keller", \
            f"Expected official_name='Keller', got {guardian_roundtrip.person.official_name}"
        assert guardian_roundtrip.person.first_name == "Anna", \
            f"Expected first_name='Anna', got {guardian_roundtrip.person.first_name}"
        assert guardian_roundtrip.person.vn == "7569872345678", \
            f"Expected vn='7569872345678', got {guardian_roundtrip.person.vn}"
        assert guardian_roundtrip.person.sex == "2", \
            f"Expected sex='2', got {guardian_roundtrip.person.sex}"
        assert guardian_roundtrip.person.date_of_birth == date(1982, 9, 12), \
            f"Expected DOB=1982-09-12, got {guardian_roundtrip.person.date_of_birth}"
        assert guardian_roundtrip.person.local_person_id == "guard-partner-001", \
            f"Expected local_person_id='guard-partner-001', got {guardian_roundtrip.person.local_person_id}"

        # Verify no organization fields (CHOICE constraint)
        assert guardian_roundtrip.organization_uid is None, \
            "organization_uid should be None for PERSON_PARTNER guardian"
        assert guardian_roundtrip.organization_name is None, \
            "organization_name should be None for PERSON_PARTNER guardian"

        # Verify guardian measure info
        assert guardian_roundtrip.guardian_measure_based_on_law == ["310"], \
            f"Expected based_on_law=['310'], got {guardian_roundtrip.guardian_measure_based_on_law}"
        assert guardian_roundtrip.guardian_measure_valid_from == date(2022, 2, 10), \
            f"Expected guardian_measure_valid_from=2022-02-10, got {guardian_roundtrip.guardian_measure_valid_from}"

        # Verify care preserved
        assert guardian_roundtrip.care == "2", \
            f"Expected care='2', got {guardian_roundtrip.care}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = partner_guardian_roundtrip.to_ech0020()
        assert layer1_roundtrip.guardian_relationship is not None
        assert len(layer1_roundtrip.guardian_relationship) == 1
        assert layer1_roundtrip.guardian_relationship[0].type_of_relationship == "7"
