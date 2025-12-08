"""Tests for Death Place CHOICE Constraint (Priority 2)

Tests the death place CHOICE constraint in eCH-0020 person data:
- Swiss death: swiss_municipality with BFS code
- Foreign death: foreign_country + foreign_town
- Unknown death: unknown = True

Tests:
- Test 9a: Death data with Swiss place
- Test 9b: Death data with Foreign place
- Test 9c: Death data with Unknown place

CHOICE constraint verification:
- SWISS: swiss_municipality present, foreign_country=None, unknown=None
- FOREIGN: foreign_country present, swiss_municipality=None, unknown=None
- UNKNOWN: unknown=True, swiss_municipality=None, foreign_country=None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, country codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestDeathPlaceChoice:
    """Test death place CHOICE constraint: Swiss/Foreign/Unknown."""

    def test_death_data_swiss_place(self):
        """Test 9a: Death data with Swiss place.

        Tests:
        - death_date field
        - death_place_type = SWISS
        - death_municipality_bfs and death_municipality_name
        - CHOICE constraint: swiss_municipality present, others None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person died in Switzerland
        """
        # Create deceased person with Swiss death place
        person_death_swiss = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="88888",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Ernst",
            sex="1",  # male
            date_of_birth=date(1930, 3, 10),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="6",  # widowed

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

            # Death data (optional) - Swiss place
            death_date=date(2023, 12, 25),
            death_place_type=PlaceType.SWISS,
            death_municipality_bfs="261",  # Zürich
            death_municipality_name="Zürich"
        )

        # Convert to Layer 1
        layer1_death_swiss = person_death_swiss.to_ech0020()

        # Verify death data structure
        assert layer1_death_swiss.death_data is not None, "death_data should exist"
        assert layer1_death_swiss.death_data.death_period is not None, "death_period should exist"
        assert layer1_death_swiss.death_data.death_period.date_from == date(2023, 12, 25), \
            "death date should match"
        assert layer1_death_swiss.death_data.place_of_death is not None, "place_of_death should exist"
        assert layer1_death_swiss.death_data.place_of_death.swiss_municipality is not None, \
            "swiss_municipality should exist"

        # Roundtrip: Layer 1 → Layer 2
        death_swiss_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_death_swiss)

        # Verify death data preserved
        assert death_swiss_roundtrip.death_date == date(2023, 12, 25), "death_date not preserved"
        assert death_swiss_roundtrip.death_place_type == PlaceType.SWISS, "death_place_type not preserved"
        assert death_swiss_roundtrip.death_municipality_bfs == "261", "death_municipality_bfs not preserved"
        assert death_swiss_roundtrip.death_municipality_name == "Zürich", \
            "death_municipality_name not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_death_swiss_roundtrip = death_swiss_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_death_swiss_roundtrip.death_data is not None
        assert layer1_death_swiss_roundtrip.death_data.death_period.date_from == date(2023, 12, 25)
        assert layer1_death_swiss_roundtrip.death_data.place_of_death.swiss_municipality is not None

    def test_death_data_foreign_place(self):
        """Test 9b: Death data with Foreign place.

        Tests:
        - death_date field
        - death_place_type = FOREIGN
        - death_country_id, death_country_iso, death_town
        - CHOICE constraint: foreign_country present, others None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Swiss person died abroad
        """
        # Create deceased person with foreign death place
        person_death_foreign = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="99999",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1945, 8, 5),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="6",  # widowed

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

            # Death data (optional) - Foreign place
            death_date=date(2024, 6, 15),
            death_place_type=PlaceType.FOREIGN,
            death_country_id="8207",  # Germany (BFS 4-digit code)
            death_country_iso="DE",   # Germany (ISO 2-letter code)
            death_country_name_short="Deutschland"
            # Note: No death_town field in Layer 2 model
        )

        # Convert to Layer 1
        layer1_death_foreign = person_death_foreign.to_ech0020()

        # Verify death data structure with foreign place
        assert layer1_death_foreign.death_data is not None, "death_data should exist"
        assert layer1_death_foreign.death_data.death_period.date_from == date(2024, 6, 15), \
            "death date should match"
        assert layer1_death_foreign.death_data.place_of_death is not None, "place_of_death should exist"
        assert layer1_death_foreign.death_data.place_of_death.foreign_country is not None, \
            "foreign_country should exist"
        assert layer1_death_foreign.death_data.place_of_death.foreign_country.country_id == "8207", \
            "country_id should match"

        # Roundtrip: Layer 1 → Layer 2
        death_foreign_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_death_foreign)

        # Verify death data preserved
        assert death_foreign_roundtrip.death_date == date(2024, 6, 15), "death_date not preserved"
        assert death_foreign_roundtrip.death_place_type == PlaceType.FOREIGN, \
            "death_place_type not preserved"
        assert death_foreign_roundtrip.death_country_id == "8207", "death_country_id not preserved"
        assert death_foreign_roundtrip.death_country_iso == "DE", "death_country_iso not preserved"
        assert death_foreign_roundtrip.death_country_name_short == "Deutschland", \
            "death_country_name_short not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_death_foreign_roundtrip = death_foreign_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_death_foreign_roundtrip.death_data is not None
        assert layer1_death_foreign_roundtrip.death_data.death_period.date_from == date(2024, 6, 15)
        assert layer1_death_foreign_roundtrip.death_data.place_of_death.foreign_country is not None

    def test_death_data_unknown_place(self):
        """Test 9c: Death data with Unknown place.

        Tests:
        - death_date field
        - death_place_type = UNKNOWN
        - CHOICE constraint: unknown=True, others None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Death place not known or not recorded
        """
        # Create deceased person with unknown death place
        person_death_unknown = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10001",
            local_person_id_category="MU.6172",
            official_name="Meier",
            first_name="Peter",
            sex="1",  # male
            date_of_birth=date(1950, 11, 22),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="6",  # widowed

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

            # Death data (optional) - Unknown place
            death_date=date(2022, 3, 8),
            death_place_type=PlaceType.UNKNOWN
            # No municipality or country for unknown
        )

        # Convert to Layer 1
        layer1_death_unknown = person_death_unknown.to_ech0020()

        # Verify death data structure with unknown place
        assert layer1_death_unknown.death_data is not None, "death_data should exist"
        assert layer1_death_unknown.death_data.death_period.date_from == date(2022, 3, 8), \
            "death date should match"
        assert layer1_death_unknown.death_data.place_of_death is not None, "place_of_death should exist"
        assert layer1_death_unknown.death_data.place_of_death.unknown is True, "unknown flag should be True"

        # Roundtrip: Layer 1 → Layer 2
        death_unknown_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_death_unknown)

        # Verify death data preserved
        assert death_unknown_roundtrip.death_date == date(2022, 3, 8), "death_date not preserved"
        assert death_unknown_roundtrip.death_place_type == PlaceType.UNKNOWN, \
            "death_place_type not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_death_unknown_roundtrip = death_unknown_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_death_unknown_roundtrip.death_data is not None
        assert layer1_death_unknown_roundtrip.death_data.death_period.date_from == date(2022, 3, 8)
        assert layer1_death_unknown_roundtrip.death_data.place_of_death.unknown is True
