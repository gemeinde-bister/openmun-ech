"""Tests for Marriage Place CHOICE Constraint (Priority 1)

Tests the marriage place CHOICE constraint in eCH-0020 person data:
- Swiss marriage: swiss_municipality with BFS code
- Foreign marriage: foreign_country + foreign_town
- Unknown marriage: unknown = True

Tests:
- Test 6: Marriage place SWISS with municipality
- Test 7: Marriage place FOREIGN with country and town

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


class TestMarriagePlaceChoice:
    """Test marriage place CHOICE constraint: Swiss/Foreign/Unknown."""

    def test_marriage_place_swiss(self):
        """Test 6: Marriage place SWISS.

        Tests:
        - marital_status = 2 (married)
        - marriage_place_type = SWISS
        - marriage_municipality_bfs and marriage_municipality_name
        - CHOICE constraint: swiss_municipality present, others None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person married in Switzerland
        """
        # Create married person with SWISS marriage place
        married_swiss = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="44444",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Peter",
            sex="1",  # male
            date_of_birth=date(1982, 9, 5),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required) - married
            marital_status="2",  # married

            # Marriage place (optional) - SWISS
            marriage_place_type=PlaceType.SWISS,
            marriage_municipality_bfs="351",  # Bern
            marriage_municipality_name="Bern",

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
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_married = married_swiss.to_ech0020()

        # Verify marriage place is SWISS (has swiss_municipality, NOT foreign_country or unknown)
        assert layer1_married.marital_info.marital_data_addon is not None, \
            "marital_data_addon should exist"
        assert layer1_married.marital_info.marital_data_addon.place_of_marriage is not None, \
            "place_of_marriage should exist"
        place_of_marriage = layer1_married.marital_info.marital_data_addon.place_of_marriage
        assert place_of_marriage.swiss_municipality is not None, \
            "swiss_municipality should exist for SWISS marriage"
        assert place_of_marriage.foreign_country is None, \
            "foreign_country should be None for SWISS marriage"
        assert place_of_marriage.unknown is None, \
            "unknown should be None for SWISS marriage"

        # Roundtrip: Layer 1 → Layer 2
        married_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_married)

        # Verify marriage place preserved
        assert married_roundtrip.marriage_place_type == PlaceType.SWISS, \
            f"Expected PlaceType.SWISS, got {married_roundtrip.marriage_place_type}"
        assert married_roundtrip.marriage_municipality_bfs == "351", \
            f"Expected '351', got {married_roundtrip.marriage_municipality_bfs}"
        assert married_roundtrip.marriage_municipality_name == "Bern", \
            f"Expected 'Bern', got {married_roundtrip.marriage_municipality_name}"
        assert married_roundtrip.marriage_country_iso is None, \
            "marriage_country_iso should be None for SWISS"
        assert married_roundtrip.marriage_town is None, \
            "marriage_town should be None for SWISS"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_married_roundtrip = married_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_married_roundtrip.marital_info.marital_data_addon.place_of_marriage.swiss_municipality is not None
        assert layer1_married_roundtrip.marital_info.marital_data_addon.place_of_marriage.foreign_country is None
        assert layer1_married_roundtrip.marital_info.marital_data_addon.place_of_marriage.unknown is None

    def test_marriage_place_foreign(self):
        """Test 7: Marriage place FOREIGN.

        Tests:
        - marital_status = 2 (married)
        - marriage_place_type = FOREIGN
        - marriage_country_id, marriage_country_iso, marriage_town
        - CHOICE constraint: foreign_country present, others None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Person married abroad (Italy in this test)
        """
        # Create married person with FOREIGN marriage place
        married_foreign = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="55555",
            local_person_id_category="MU.6172",
            official_name="Rossi",
            first_name="Lucia",
            sex="2",  # female
            date_of_birth=date(1987, 4, 18),

            # Birth info (required)
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8211",  # Italy (BFS 4-digit code)
            birth_country_iso="IT",   # Italy (ISO 2-letter code)
            birth_country_name_short="Italia",
            birth_town="Milano",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required) - married
            marital_status="2",  # married

            # Marriage place (optional) - FOREIGN (married in Italy)
            marriage_place_type=PlaceType.FOREIGN,
            marriage_country_id="8211",  # Italy (BFS 4-digit code)
            marriage_country_iso="IT",   # Italy (ISO 2-letter code)
            marriage_country_name_short="Italia",
            marriage_town="Roma",

            # Nationality (required) - Italian
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8211',  # Italy (BFS 4-digit code)
                    'country_iso': 'IT',   # Italy (ISO 2-letter code)
                    'country_name_short': 'Italia'
                }
            ],

            # Citizenship CHOICE (required) - Foreign with residence permit
            residence_permit='03',  # Settlement permit C
            residence_permit_valid_from=date(2012, 6, 1),

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_married_foreign = married_foreign.to_ech0020()

        # Verify marriage place is FOREIGN (has foreign_country and town, NOT swiss_municipality or unknown)
        assert layer1_married_foreign.marital_info.marital_data_addon is not None, \
            "marital_data_addon should exist"
        assert layer1_married_foreign.marital_info.marital_data_addon.place_of_marriage is not None, \
            "place_of_marriage should exist"
        place_of_marriage_foreign = layer1_married_foreign.marital_info.marital_data_addon.place_of_marriage
        assert place_of_marriage_foreign.foreign_country is not None, \
            "foreign_country should exist for FOREIGN marriage"
        assert place_of_marriage_foreign.foreign_town == "Roma", \
            f"Expected 'Roma', got {place_of_marriage_foreign.foreign_town}"
        assert place_of_marriage_foreign.swiss_municipality is None, \
            "swiss_municipality should be None for FOREIGN marriage"
        assert place_of_marriage_foreign.unknown is None, \
            "unknown should be None for FOREIGN marriage"

        # Verify country ID
        assert place_of_marriage_foreign.foreign_country.country_id == "8211", \
            f"Expected '8211', got {place_of_marriage_foreign.foreign_country.country_id}"

        # Roundtrip: Layer 1 → Layer 2
        married_foreign_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_married_foreign)

        # Verify marriage place preserved
        assert married_foreign_roundtrip.marriage_place_type == PlaceType.FOREIGN, \
            f"Expected PlaceType.FOREIGN, got {married_foreign_roundtrip.marriage_place_type}"
        assert married_foreign_roundtrip.marriage_country_id == "8211", \
            f"Expected '8211', got {married_foreign_roundtrip.marriage_country_id}"
        assert married_foreign_roundtrip.marriage_country_iso == "IT", \
            f"Expected 'IT', got {married_foreign_roundtrip.marriage_country_iso}"
        assert married_foreign_roundtrip.marriage_town == "Roma", \
            f"Expected 'Roma', got {married_foreign_roundtrip.marriage_town}"
        assert married_foreign_roundtrip.marriage_municipality_bfs is None, \
            "marriage_municipality_bfs should be None for FOREIGN"
        assert married_foreign_roundtrip.marriage_municipality_name is None, \
            "marriage_municipality_name should be None for FOREIGN"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_married_foreign_roundtrip = married_foreign_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_married_foreign_roundtrip.marital_info.marital_data_addon.place_of_marriage.foreign_country is not None
        assert layer1_married_foreign_roundtrip.marital_info.marital_data_addon.place_of_marriage.foreign_town == "Roma"
        assert layer1_married_foreign_roundtrip.marital_info.marital_data_addon.place_of_marriage.swiss_municipality is None
        assert layer1_married_foreign_roundtrip.marital_info.marital_data_addon.place_of_marriage.unknown is None
