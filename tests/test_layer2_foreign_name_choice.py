"""Tests for Foreign Name CHOICE Constraint (Priority 1)

Tests the foreign name CHOICE constraint in eCH-0020 person data:
- Name on foreign passport: name_on_foreign_passport + name_on_foreign_passport_first
- Declared foreign name: declared_foreign_name + declared_foreign_name_first

Tests:
- Test 8a: name_on_foreign_passport (Chinese characters)
- Test 8b: declared_foreign_name (Korean characters)

CHOICE constraint verification:
- Passport: name_on_foreign_passport present, declared_foreign_name None
- Declared: declared_foreign_name present, name_on_foreign_passport None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (country codes)
- Unicode characters for foreign names (Chinese, Korean)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestForeignNameChoice:
    """Test foreign name CHOICE constraint: name_on_foreign_passport XOR declared_foreign_name."""

    def test_name_on_foreign_passport(self):
        """Test 8a: Foreign name on passport.

        Tests:
        - name_on_foreign_passport and name_on_foreign_passport_first fields
        - CHOICE constraint: name_on_foreign_passport present, declared_foreign_name None
        - Unicode character handling (Chinese characters)
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person's official name as written in foreign passport
        """
        # Create person with name on foreign passport
        person_passport_name = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="66666",
            local_person_id_category="MU.6172",
            official_name="Yang",
            first_name="Wei",
            sex="1",  # male
            date_of_birth=date(1992, 11, 8),

            # Birth info (required)
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8216",  # China (BFS 4-digit code)
            birth_country_iso="CN",   # China (ISO 2-letter code)
            birth_country_name_short="China",
            birth_town="Beijing",

            # Religion (required)
            religion="211",  # Other (non-Christian)

            # Marital status (required)
            marital_status="1",  # unmarried

            # Foreign name on passport (CHOICE: passport XOR declared)
            name_on_foreign_passport="杨",
            name_on_foreign_passport_first="伟",
            # declared_foreign_name should be None (CHOICE constraint)

            # Nationality (required) - Chinese
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8216',  # China (BFS 4-digit code)
                    'country_iso': 'CN',   # China (ISO 2-letter code)
                    'country_name_short': 'China'
                }
            ],

            # Citizenship CHOICE (required) - Foreign with residence permit
            residence_permit='01',  # Residence permit B
            residence_permit_valid_from=date(2020, 1, 1),

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_passport = person_passport_name.to_ech0020()

        # Verify foreign name CHOICE: has name_on_foreign_passport, NOT declared_foreign_name
        assert layer1_passport.name_info.name_data.name_on_foreign_passport is not None, \
            "name_on_foreign_passport should exist"
        assert layer1_passport.name_info.name_data.name_on_foreign_passport.name == "杨"
        assert layer1_passport.name_info.name_data.name_on_foreign_passport.first_name == "伟"
        assert layer1_passport.name_info.name_data.declared_foreign_name is None, \
            "declared_foreign_name should be None"

        # Roundtrip: Layer 1 → Layer 2
        passport_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_passport)

        # Verify foreign passport name preserved
        assert passport_roundtrip.name_on_foreign_passport == "杨"
        assert passport_roundtrip.name_on_foreign_passport_first == "伟"
        assert passport_roundtrip.declared_foreign_name is None, \
            "declared_foreign_name should be None"
        assert passport_roundtrip.declared_foreign_name_first is None, \
            "declared_foreign_name_first should be None"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_passport_roundtrip = passport_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_passport_roundtrip.name_info.name_data.name_on_foreign_passport is not None
        assert layer1_passport_roundtrip.name_info.name_data.name_on_foreign_passport.name == "杨"
        assert layer1_passport_roundtrip.name_info.name_data.declared_foreign_name is None

    def test_declared_foreign_name(self):
        """Test 8b: Declared foreign name.

        Tests:
        - declared_foreign_name and declared_foreign_name_first fields
        - CHOICE constraint: declared_foreign_name present, name_on_foreign_passport None
        - Unicode character handling (Korean characters)
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person declares preferred foreign name spelling
        """
        # Create person with declared foreign name
        person_declared_name = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="77777",
            local_person_id_category="MU.6172",
            official_name="Kim",
            first_name="Soo-Jin",
            sex="2",  # female
            date_of_birth=date(1989, 6, 14),

            # Birth info (required)
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8209",  # South Korea (BFS 4-digit code)
            birth_country_iso="KR",   # South Korea (ISO 2-letter code)
            birth_country_name_short="Korea (Republik)",
            birth_town="Seoul",

            # Religion (required)
            religion="211",  # Other

            # Marital status (required)
            marital_status="1",  # unmarried

            # Declared foreign name (CHOICE: declared XOR passport)
            declared_foreign_name="김",
            declared_foreign_name_first="수진",
            # name_on_foreign_passport should be None (CHOICE constraint)

            # Nationality (required) - Korean
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8209',  # South Korea (BFS 4-digit code)
                    'country_iso': 'KR',   # South Korea (ISO 2-letter code)
                    'country_name_short': 'Korea (Republik)'
                }
            ],

            # Citizenship CHOICE (required) - Foreign with residence permit
            residence_permit='02',  # Residence permit L
            residence_permit_valid_from=date(2021, 3, 15),

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_declared = person_declared_name.to_ech0020()

        # Verify foreign name CHOICE: has declared_foreign_name, NOT name_on_foreign_passport
        assert layer1_declared.name_info.name_data.declared_foreign_name is not None, \
            "declared_foreign_name should exist"
        assert layer1_declared.name_info.name_data.declared_foreign_name.name == "김"
        assert layer1_declared.name_info.name_data.declared_foreign_name.first_name == "수진"
        assert layer1_declared.name_info.name_data.name_on_foreign_passport is None, \
            "name_on_foreign_passport should be None"

        # Roundtrip: Layer 1 → Layer 2
        declared_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_declared)

        # Verify declared foreign name preserved
        assert declared_roundtrip.declared_foreign_name == "김"
        assert declared_roundtrip.declared_foreign_name_first == "수진"
        assert declared_roundtrip.name_on_foreign_passport is None, \
            "name_on_foreign_passport should be None"
        assert declared_roundtrip.name_on_foreign_passport_first is None, \
            "name_on_foreign_passport_first should be None"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_declared_roundtrip = declared_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_declared_roundtrip.name_info.name_data.declared_foreign_name is not None
        assert layer1_declared_roundtrip.name_info.name_data.declared_foreign_name.name == "김"
        assert layer1_declared_roundtrip.name_info.name_data.name_on_foreign_passport is None
