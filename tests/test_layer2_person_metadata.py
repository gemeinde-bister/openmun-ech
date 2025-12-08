"""Tests for Person Metadata Fields (Priority 2)

Tests Layer 2 person metadata fields - additional data and lock variations:

Tests:
- Test 10: Person additional data (mr_mrs, title, language_of_correspondance)
- Test 11: Lock data with validity dates (data_lock/paper_lock with date ranges)

Tests verify:
1. Layer 2 construction with metadata fields
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss
5. Optional metadata field handling

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestPersonMetadata:
    """Test person metadata fields: additional data and lock data."""

    def test_person_additional_data(self):
        """Test 10: Person additional data fields.

        Tests:
        - mr_mrs field (salutation: 2 = Mr/Herr)
        - title field (academic title: Dr.)
        - language_of_correspondance field (de = German)
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person with academic title and preferred correspondence language
        """
        # Create person with additional metadata
        person_additional = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10002",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Elisabeth",
            sex="2",  # female
            date_of_birth=date(1975, 4, 20),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="121",  # Roman Catholic

            # Marital status (required)
            marital_status="2",  # married

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
            data_lock="0",
            paper_lock="0",

            # Person additional data (optional) - mr_mrs, title, language
            mr_mrs="2",  # Mr/Herr
            title="Dr.",
            language_of_correspondance="de"  # German
        )

        # Convert to Layer 1
        layer1_additional = person_additional.to_ech0020()

        # Verify person additional data structure
        assert layer1_additional.person_additional_data is not None, \
            "person_additional_data should exist"
        assert layer1_additional.person_additional_data.mr_mrs == "2", "mr_mrs should be '2'"
        assert layer1_additional.person_additional_data.title == "Dr.", "title should be 'Dr.'"
        assert layer1_additional.person_additional_data.language_of_correspondance == "de", \
            "language should be 'de'"

        # Roundtrip: Layer 1 → Layer 2
        additional_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_additional)

        # Verify person additional data preserved
        assert additional_roundtrip.mr_mrs == "2", "mr_mrs not preserved"
        assert additional_roundtrip.title == "Dr.", "title not preserved"
        assert additional_roundtrip.language_of_correspondance == "de", \
            "language_of_correspondance not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_additional_roundtrip = additional_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_additional_roundtrip.person_additional_data is not None
        assert layer1_additional_roundtrip.person_additional_data.mr_mrs == "2"
        assert layer1_additional_roundtrip.person_additional_data.title == "Dr."
        assert layer1_additional_roundtrip.person_additional_data.language_of_correspondance == "de"

    def test_lock_data_with_validity_dates(self):
        """Test 11: Lock data with validity dates.

        Tests:
        - data_lock field with value "1" (locked)
        - data_lock_valid_from and data_lock_valid_till dates
        - paper_lock field with boolean True (locked)
        - paper_lock_valid_from and paper_lock_valid_till dates
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person record with temporary data and paper locks
        """
        # Create person with lock data including validity dates
        person_lock_dates = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10003",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1988, 9, 12),

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

            # Lock data (required) - with validity dates
            data_lock="1",  # Locked
            data_lock_valid_from=date(2024, 1, 1),
            data_lock_valid_till=date(2025, 12, 31),
            paper_lock=True,  # Locked
            paper_lock_valid_from=date(2024, 6, 1),
            paper_lock_valid_till=date(2024, 12, 31)
        )

        # Convert to Layer 1
        layer1_lock = person_lock_dates.to_ech0020()

        # Verify lock data structure
        assert layer1_lock.lock_data is not None, "lock_data should exist"
        assert layer1_lock.lock_data.data_lock == "1", "data_lock should be '1'"
        assert layer1_lock.lock_data.data_lock_valid_from == date(2024, 1, 1), \
            "data_lock_valid_from should match"
        assert layer1_lock.lock_data.data_lock_valid_till == date(2025, 12, 31), \
            "data_lock_valid_till should match"
        assert layer1_lock.lock_data.paper_lock == "1", "paper_lock should be '1'"
        assert layer1_lock.lock_data.paper_lock_valid_from == date(2024, 6, 1), \
            "paper_lock_valid_from should match"
        assert layer1_lock.lock_data.paper_lock_valid_till == date(2024, 12, 31), \
            "paper_lock_valid_till should match"

        # Roundtrip: Layer 1 → Layer 2
        lock_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_lock)

        # Verify lock data preserved
        assert lock_roundtrip.data_lock == "1", "data_lock not preserved"
        assert lock_roundtrip.data_lock_valid_from == date(2024, 1, 1), \
            "data_lock_valid_from not preserved"
        assert lock_roundtrip.data_lock_valid_till == date(2025, 12, 31), \
            "data_lock_valid_till not preserved"
        assert lock_roundtrip.paper_lock is True, "paper_lock not preserved"
        assert lock_roundtrip.paper_lock_valid_from == date(2024, 6, 1), \
            "paper_lock_valid_from not preserved"
        assert lock_roundtrip.paper_lock_valid_till == date(2024, 12, 31), \
            "paper_lock_valid_till not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_lock_roundtrip = lock_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_lock_roundtrip.lock_data.data_lock == "1"
        assert layer1_lock_roundtrip.lock_data.paper_lock == "1"
        assert layer1_lock_roundtrip.lock_data.data_lock_valid_from == date(2024, 1, 1)
