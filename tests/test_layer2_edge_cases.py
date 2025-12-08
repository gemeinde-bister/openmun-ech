"""Priority 6: Edge Cases Tests

Tests Layer 2 edge case handling - unusual but valid data patterns that must
work correctly for production compatibility.

Tests:
- Test 33: Multiple places of origin (3+ origins from different cantons)
- Test 34: Birth place UNKNOWN (no municipality, no country)
- Test 35: Residence permit without dates (minimal foreign national data)

Tests verify:
1. Layer 2 construction with edge cases
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss
5. List preservation and optional field handling

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, canton codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestLayer2EdgeCases:
    """Test Layer 2 edge case handling."""

    def test_multiple_places_of_origin(self):
        """Test 33: Multiple places of origin from different cantons.

        Tests:
        - places_of_origin list with 3+ entries
        - Different cantons: ZH, BE, BS
        - Use case: Swiss citizens can inherit citizenship from both parents
        - Validates Rule #5: Preserve lists even for "typical" cases
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with multiple places of origin
        person_multiple_origins = BaseDeliveryPerson(
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
                    'country_id': '8100',  # BFS 4-digit code (Switzerland)
                    'country_iso': 'CH',  # ISO 2-letter code
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required) - Multiple places of origin
            # Swiss citizens can inherit citizenship from both parents
            # and can have multiple places of origin from different cantons
            places_of_origin=[
                {
                    'bfs_code': '261',  # Zürich
                    'name': 'Zürich',
                    'canton': 'ZH'
                },
                {
                    'bfs_code': '351',  # Bern
                    'name': 'Bern',
                    'canton': 'BE'
                },
                {
                    'bfs_code': '2701',  # Basel
                    'name': 'Basel',
                    'canton': 'BS'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_multiple_origins = person_multiple_origins.to_ech0020()

        # Verify place_of_origin_info list in Layer 1
        assert layer1_multiple_origins.place_of_origin_info is not None, "place_of_origin_info missing"
        assert len(layer1_multiple_origins.place_of_origin_info) == 3, \
            f"Expected 3 places of origin, got {len(layer1_multiple_origins.place_of_origin_info)}"

        # Verify first origin (Zürich)
        origin1 = layer1_multiple_origins.place_of_origin_info[0]
        assert origin1.place_of_origin.place_of_origin_id == 261, "First origin BFS wrong"
        assert origin1.place_of_origin.origin_name == 'Zürich', "First origin name wrong"
        assert origin1.place_of_origin.canton == 'ZH', "First origin canton wrong"

        # Verify second origin (Bern)
        origin2 = layer1_multiple_origins.place_of_origin_info[1]
        assert origin2.place_of_origin.place_of_origin_id == 351, "Second origin BFS wrong"
        assert origin2.place_of_origin.origin_name == 'Bern', "Second origin name wrong"
        assert origin2.place_of_origin.canton == 'BE', "Second origin canton wrong"

        # Verify third origin (Basel)
        origin3 = layer1_multiple_origins.place_of_origin_info[2]
        assert origin3.place_of_origin.place_of_origin_id == 2701, "Third origin BFS wrong"
        assert origin3.place_of_origin.origin_name == 'Basel', "Third origin name wrong"
        assert origin3.place_of_origin.canton == 'BS', "Third origin canton wrong"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_multiple_origins = BaseDeliveryPerson.from_ech0020(layer1_multiple_origins)

        # Verify all places of origin preserved
        assert roundtrip_multiple_origins.places_of_origin is not None, "places_of_origin lost"
        assert len(roundtrip_multiple_origins.places_of_origin) == 3, \
            f"Expected 3 origins in roundtrip, got {len(roundtrip_multiple_origins.places_of_origin)}"

        # Verify each origin preserved (iterate to avoid repetition)
        for i, (origin_rt, origin_orig) in enumerate(zip(
            roundtrip_multiple_origins.places_of_origin,
            person_multiple_origins.places_of_origin
        )):
            assert origin_rt['bfs_code'] == origin_orig['bfs_code'], \
                f"Origin {i}: bfs_code not preserved"
            assert origin_rt['name'] == origin_orig['name'], \
                f"Origin {i}: name not preserved"
            assert origin_rt['canton'] == origin_orig['canton'], \
                f"Origin {i}: canton not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_mo = roundtrip_multiple_origins.to_ech0020()

        # Verify Layer 1 models equivalent
        assert len(layer1_roundtrip_mo.place_of_origin_info) == \
               len(layer1_multiple_origins.place_of_origin_info), \
               "Origin count changed in full roundtrip"

        for i, (origin_rt, origin_orig) in enumerate(zip(
            layer1_roundtrip_mo.place_of_origin_info,
            layer1_multiple_origins.place_of_origin_info
        )):
            assert origin_rt.place_of_origin.place_of_origin_id == \
                   origin_orig.place_of_origin.place_of_origin_id, \
                   f"Origin {i}: BFS code changed in full roundtrip"

    def test_birth_place_unknown(self):
        """Test 34: Birth place UNKNOWN with full roundtrip.

        Tests:
        - birth_place_type = UNKNOWN (no municipality, no country)
        - Use case: Birth place not recorded or lost in historical records
        - Validates CHOICE handling for unknown birth place
        - All birth details correctly None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with UNKNOWN birth place
        person_unknown_birth = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1985, 8, 20),

            # Birth info (required) - Birth place unknown
            birth_place_type=PlaceType.UNKNOWN,  # No details - this is the edge case
            # No birth_municipality_bfs, birth_municipality_name, birth_country_iso, etc.

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # BFS 4-digit code
                    'country_iso': 'CH',  # ISO 2-letter code
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required)
            places_of_origin=[
                {
                    'bfs_code': '351',
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_unknown_birth = person_unknown_birth.to_ech0020()

        # Verify birth_info structure in Layer 1
        assert layer1_unknown_birth.birth_info is not None, "birth_info missing"
        assert layer1_unknown_birth.birth_info.birth_data is not None, "birth_data missing"

        # Verify place_of_birth has unknown=True
        place_of_birth = layer1_unknown_birth.birth_info.birth_data.place_of_birth
        assert place_of_birth.unknown is True, "place_of_birth.unknown should be True"

        # Verify CHOICE constraint: no swiss_municipality, no foreign_country
        assert place_of_birth.swiss_municipality is None, \
            "swiss_municipality should be None for unknown birth"
        assert place_of_birth.foreign_country is None, \
            "foreign_country should be None for unknown birth"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_unknown_birth = BaseDeliveryPerson.from_ech0020(layer1_unknown_birth)

        # Verify birth place type preserved
        assert roundtrip_unknown_birth.birth_place_type == PlaceType.UNKNOWN, \
            "birth_place_type not preserved"

        # Verify no birth details present (edge case)
        assert roundtrip_unknown_birth.birth_municipality_bfs is None, \
            "birth_municipality_bfs should be None for unknown birth"
        assert roundtrip_unknown_birth.birth_municipality_name is None, \
            "birth_municipality_name should be None for unknown birth"
        assert roundtrip_unknown_birth.birth_country_iso is None, \
            "birth_country_iso should be None for unknown birth"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_ub = roundtrip_unknown_birth.to_ech0020()

        # Verify Layer 1 models equivalent
        place_rt = layer1_roundtrip_ub.birth_info.birth_data.place_of_birth
        assert place_rt.unknown is True
        assert place_rt.swiss_municipality is None
        assert place_rt.foreign_country is None

    def test_residence_permit_without_dates(self):
        """Test 35: Residence permit without dates.

        Tests:
        - residence_permit with no valid_from/valid_till dates
        - Use case: Minimal foreign national data (some permits don't have dates)
        - Validates optional field handling for foreign nationals
        - CHOICE constraint: residence_permit vs places_of_origin
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with residence permit (no dates)
        person_permit_no_dates = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="11111",
            local_person_id_category="MU.6172",
            official_name="Kovács",
            first_name="István",
            sex="1",  # male
            date_of_birth=date(1990, 3, 12),

            # Birth info (required) - Foreign birth
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8181",  # Hungary (BFS 4-digit code)
            birth_country_iso="HU",  # Hungary (ISO 2-letter code)
            birth_country_name_short="Ungarn",
            birth_town="Budapest",

            # Religion (required)
            religion="211",  # Other

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required) - Foreign
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8181',  # Hungary (BFS 4-digit code)
                    'country_iso': 'HU',  # Hungary (ISO 2-letter code)
                    'country_name_short': 'Ungarn'
                }
            ],

            # Citizenship CHOICE (required) - Foreign with residence permit
            # Edge case: No dates provided (some permit types don't have explicit dates)
            residence_permit='01',  # Temporary residence (Aufenthaltsbewilligung B)
            residence_permit_valid_from=None,  # No dates - this is the edge case
            residence_permit_valid_till=None,

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_permit_no_dates = person_permit_no_dates.to_ech0020()

        # Verify residence_permit_data structure in Layer 1
        assert layer1_permit_no_dates.residence_permit_data is not None, \
            "residence_permit_data missing"
        assert layer1_permit_no_dates.residence_permit_data.residence_permit == '01', \
            "residence_permit not preserved"

        # Verify dates are None (the edge case)
        assert layer1_permit_no_dates.residence_permit_data.residence_permit_valid_from is None, \
            "residence_permit_valid_from should be None"
        assert layer1_permit_no_dates.residence_permit_data.residence_permit_valid_till is None, \
            "residence_permit_valid_till should be None"

        # Verify CHOICE constraint: has residence_permit_data, NOT place_of_origin_info
        assert layer1_permit_no_dates.place_of_origin_info is None, \
            "place_of_origin_info should be None for foreign citizen"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_permit_no_dates = BaseDeliveryPerson.from_ech0020(layer1_permit_no_dates)

        # Verify residence permit preserved
        assert roundtrip_permit_no_dates.residence_permit == '01', \
            "residence_permit not preserved in roundtrip"
        assert roundtrip_permit_no_dates.residence_permit_valid_from is None, \
            "residence_permit_valid_from should remain None"
        assert roundtrip_permit_no_dates.residence_permit_valid_till is None, \
            "residence_permit_valid_till should remain None"

        # Verify CHOICE constraint preserved
        assert roundtrip_permit_no_dates.places_of_origin is None, \
            "places_of_origin should be None for foreign citizen"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_pnd = roundtrip_permit_no_dates.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_roundtrip_pnd.residence_permit_data.residence_permit == \
               layer1_permit_no_dates.residence_permit_data.residence_permit
        assert layer1_roundtrip_pnd.residence_permit_data.residence_permit_valid_from is None
        assert layer1_roundtrip_pnd.residence_permit_data.residence_permit_valid_till is None
