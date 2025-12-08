"""Tests for Citizenship CHOICE Constraint (Priority 1)

Tests the fundamental CHOICE constraint in eCH-0020 person data:
- Swiss citizens: MUST have places_of_origin (XOR)
- Foreign nationals: MUST have residence_permit

Tests:
- Test 1: Minimal Swiss person with places_of_origin
- Test 2: Foreign person with residence_permit and dates

CHOICE constraint verification:
- Swiss: places_of_origin present, residence_permit None
- Foreign: residence_permit present, places_of_origin None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, country codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestCitizenshipChoice:
    """Test citizenship CHOICE constraint: places_of_origin XOR residence_permit."""

    def test_minimal_swiss_person_with_places_of_origin(self):
        """Test 1: Minimal Swiss person with places_of_origin (all required fields only).

        Tests:
        - Swiss citizenship (nationality_status = 1)
        - places_of_origin present (Zürich)
        - residence_permit None (CHOICE constraint)
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Type 1 field duplication (official_name, first_name, sex)
        - Zero data loss verification
        """
        # Create minimal Swiss person (all required fields only)
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1980, 5, 15),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',   # Switzerland (ISO 2-letter code)
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required) - Swiss citizen
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",  # No lock
            paper_lock="0"  # No paper lock
        )

        # Convert to Layer 1
        layer1_person = person.to_ech0020()

        # Verify basic structure
        assert layer1_person.person_identification.official_name == "Müller"
        assert layer1_person.person_identification.first_name == "Hans"
        assert layer1_person.person_identification.local_person_id.person_id == "12345"

        # Verify Type 1 duplication worked
        assert layer1_person.person_identification.official_name == layer1_person.name_info.name_data.official_name, \
            "Type 1 duplication failed for official_name"
        assert layer1_person.person_identification.first_name == layer1_person.name_info.name_data.first_name, \
            "Type 1 duplication failed for first_name"
        assert layer1_person.person_identification.sex == layer1_person.birth_info.birth_data.sex, \
            "Type 1 duplication failed for sex"

        # Verify CHOICE constraint: Swiss citizen has places_of_origin, NOT residence_permit
        assert layer1_person.place_of_origin_info is not None, "places_of_origin missing"
        assert len(layer1_person.place_of_origin_info) == 1, "Should have 1 place of origin"
        assert layer1_person.place_of_origin_info[0].place_of_origin.place_of_origin_id == 261
        assert layer1_person.residence_permit_data is None, "residence_permit_data should be None for Swiss citizen"

        # Roundtrip: Layer 1 → Layer 2
        person_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_person)

        # Verify key fields preserved
        assert person_roundtrip.official_name == person.official_name, "official_name not preserved"
        assert person_roundtrip.first_name == person.first_name, "first_name not preserved"
        assert person_roundtrip.sex == person.sex, "sex not preserved"
        assert person_roundtrip.date_of_birth == person.date_of_birth, "date_of_birth not preserved"
        assert person_roundtrip.birth_place_type == person.birth_place_type, "birth_place_type not preserved"
        assert person_roundtrip.birth_municipality_bfs == person.birth_municipality_bfs, "birth_municipality_bfs not preserved"
        assert person_roundtrip.religion == person.religion, "religion not preserved"
        assert person_roundtrip.marital_status == person.marital_status, "marital_status not preserved"
        assert person_roundtrip.nationality_status == person.nationality_status, "nationality_status not preserved"
        assert person_roundtrip.data_lock == person.data_lock, "data_lock not preserved"

        # Verify citizenship CHOICE preserved
        assert person_roundtrip.places_of_origin is not None, "places_of_origin lost in roundtrip"
        assert len(person_roundtrip.places_of_origin) == 1, "places_of_origin count changed"
        assert person_roundtrip.places_of_origin[0]['bfs_code'] == '261', "place of origin bfs_code not preserved"
        assert person_roundtrip.residence_permit is None, "residence_permit should be None for Swiss citizen"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = person_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_roundtrip.person_identification.official_name == layer1_person.person_identification.official_name
        assert layer1_roundtrip.person_identification.first_name == layer1_person.person_identification.first_name
        assert layer1_roundtrip.person_identification.sex == layer1_person.person_identification.sex
        assert layer1_roundtrip.birth_info.birth_data.place_of_birth.swiss_municipality is not None
        assert layer1_roundtrip.religion_data.religion == layer1_person.religion_data.religion
        assert layer1_roundtrip.place_of_origin_info is not None
        assert layer1_roundtrip.residence_permit_data is None

    def test_foreign_person_with_residence_permit(self):
        """Test 2: Foreign person with residence_permit.

        Tests:
        - Foreign citizenship (nationality_status = 2, German)
        - Foreign birth place (München, Germany)
        - residence_permit present (type 03 = Niederlassungsbewilligung C)
        - residence_permit_valid_from and valid_till dates
        - places_of_origin None (CHOICE constraint)
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create foreign person with residence permit
        foreign_person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1985, 8, 20),

            # Birth info (required) - foreign birth place
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8207",  # Germany (BFS 4-digit code)
            birth_country_iso="DE",   # Germany (ISO 2-letter code)
            birth_country_name_short="Deutschland",
            birth_town="München",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="2",  # married

            # Nationality (required) - German
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8207',  # Germany (BFS 4-digit code)
                    'country_iso': 'DE',   # Germany (ISO 2-letter code)
                    'country_name_short': 'Deutschland'
                }
            ],

            # Citizenship CHOICE (required) - Foreign citizen with residence permit
            residence_permit='03',  # Settlement permit (Niederlassungsbewilligung C)
            residence_permit_valid_from=date(2010, 1, 1),
            residence_permit_valid_till=date(2030, 12, 31),

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_foreign = foreign_person.to_ech0020()

        # Verify CHOICE constraint: has residence_permit, NOT places_of_origin
        assert layer1_foreign.residence_permit_data is not None, "residence_permit_data missing"
        assert layer1_foreign.residence_permit_data.residence_permit == '03', "residence_permit type wrong"
        assert layer1_foreign.residence_permit_data.residence_permit_valid_from == date(2010, 1, 1)
        assert layer1_foreign.residence_permit_data.residence_permit_valid_till == date(2030, 12, 31)
        assert layer1_foreign.place_of_origin_info is None, "place_of_origin_info should be None for foreign citizen"

        # Verify foreign birth place
        assert layer1_foreign.birth_info.birth_data.place_of_birth.foreign_country is not None
        assert layer1_foreign.birth_info.birth_data.place_of_birth.foreign_country.country_id_iso2 == "DE"
        assert layer1_foreign.birth_info.birth_data.place_of_birth.foreign_town == "München"

        # Roundtrip: Layer 1 → Layer 2
        foreign_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_foreign)

        # Verify key fields preserved
        assert foreign_roundtrip.official_name == foreign_person.official_name
        assert foreign_roundtrip.first_name == foreign_person.first_name
        assert foreign_roundtrip.birth_place_type == PlaceType.FOREIGN
        assert foreign_roundtrip.birth_country_id == "8207"
        assert foreign_roundtrip.birth_country_iso == "DE"
        assert foreign_roundtrip.birth_town == "München"
        assert foreign_roundtrip.nationality_status == "2"

        # Verify CHOICE constraint in Layer 2
        assert foreign_roundtrip.residence_permit is not None, "residence_permit lost in roundtrip"
        assert foreign_roundtrip.residence_permit == '03', "permit_type not preserved"
        assert foreign_roundtrip.residence_permit_valid_from == date(2010, 1, 1), "permit_valid_from not preserved"
        assert foreign_roundtrip.residence_permit_valid_till == date(2030, 12, 31), "permit_valid_till not preserved"
        assert foreign_roundtrip.places_of_origin is None, "places_of_origin should be None for foreign citizen"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_foreign_roundtrip = foreign_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_foreign_roundtrip.residence_permit_data is not None
        assert layer1_foreign_roundtrip.residence_permit_data.residence_permit == '03'
        assert layer1_foreign_roundtrip.place_of_origin_info is None
