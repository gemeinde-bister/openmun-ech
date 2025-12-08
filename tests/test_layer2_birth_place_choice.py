"""Tests for Birth Place CHOICE Constraint (Priority 1)

Tests the birth place CHOICE constraint in eCH-0020 person data:
- Swiss birth: swiss_municipality
- Foreign birth: foreign_country + foreign_town
- Unknown birth: unknown = True

Test 3: Birth place UNKNOWN with CHOICE constraint validation

CHOICE constraint verification:
- UNKNOWN: unknown=True, swiss_municipality=None, foreign_country=None
- SWISS: swiss_municipality present, unknown=None, foreign_country=None
- FOREIGN: foreign_country present, unknown=None, swiss_municipality=None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestBirthPlaceChoice:
    """Test birth place CHOICE constraint: Swiss/Foreign/Unknown."""

    def test_birth_place_unknown(self):
        """Test 3: Birth place UNKNOWN.

        Tests:
        - birth_place_type = UNKNOWN
        - No municipality data (swiss or foreign)
        - CHOICE constraint: unknown=True, others=None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Birth place not recorded or lost in historical records
        """
        # Create person with UNKNOWN birth place
        person_unknown_birth = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="11111",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Anna",
            sex="2",  # female
            date_of_birth=date(1975, 12, 10),

            # Birth info (required) - UNKNOWN birth place
            birth_place_type=PlaceType.UNKNOWN,
            # No birth_municipality_bfs, no birth_country_iso

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
                    'bfs_code': '230',  # Bern
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_unknown = person_unknown_birth.to_ech0020()

        # Verify birth place is marked as UNKNOWN
        assert layer1_unknown.birth_info.birth_data.place_of_birth.unknown is True, \
            "Birth place should be marked as unknown"
        assert layer1_unknown.birth_info.birth_data.place_of_birth.swiss_municipality is None, \
            "Swiss municipality should be None"
        assert layer1_unknown.birth_info.birth_data.place_of_birth.foreign_country is None, \
            "Foreign country should be None"

        # Roundtrip: Layer 1 → Layer 2
        unknown_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_unknown)

        # Verify key fields preserved
        assert unknown_roundtrip.official_name == person_unknown_birth.official_name
        assert unknown_roundtrip.first_name == person_unknown_birth.first_name
        assert unknown_roundtrip.birth_place_type == PlaceType.UNKNOWN, \
            f"Expected UNKNOWN, got {unknown_roundtrip.birth_place_type}"
        assert unknown_roundtrip.birth_municipality_bfs is None, \
            "birth_municipality_bfs should be None for UNKNOWN"
        assert unknown_roundtrip.birth_country_iso is None, \
            "birth_country_iso should be None for UNKNOWN"
        assert unknown_roundtrip.birth_town is None, \
            "birth_town should be None for UNKNOWN"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_unknown_roundtrip = unknown_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_unknown_roundtrip.birth_info.birth_data.place_of_birth.unknown is True
        assert layer1_unknown_roundtrip.birth_info.birth_data.place_of_birth.swiss_municipality is None
        assert layer1_unknown_roundtrip.birth_info.birth_data.place_of_birth.foreign_country is None
