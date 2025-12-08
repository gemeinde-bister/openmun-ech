"""Priority 5: Rare Fields Tests

Tests Layer 2 rare field handling - fields that are infrequently used but
REQUIRED for 100% roundtrip and production XML compatibility.

**Note**: Tests 28-29 (foreign names) are already covered by Tests 8a-8b in
test_layer2_basic.py, so this file implements Tests 30-32 only.

Tests:
- Test 30: Place of origin with naturalization date and historical BFS codes
- Test 31: Birth with parent names from birth certificate
- Test 32: Marital proof flag (official_proof_of_marital_status_yes_no)

Tests verify:
1. Layer 2 construction with rare fields
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss
5. Rare fields are preserved (Rule #11: rare fields are non-negotiable)

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, canton codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestLayer2RareFields:
    """Test Layer 2 rare field handling."""

    def test_place_of_origin_with_naturalization(self):
        """Test 30: Place of origin with naturalization date and historical BFS codes.

        Tests:
        - naturalization_date in places_of_origin
        - history_municipality_id in places_of_origin
        - Use case: Naturalized Swiss citizens (born abroad, became Swiss)
        - Use case: Historical BFS codes for municipalities that changed
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with naturalization data
        person_naturalized = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1975, 3, 10),

            # Birth info (required) - born in Germany, naturalized Swiss
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8207",  # Germany (BFS 4-digit code)
            birth_country_iso="DE",  # Germany (ISO 2-letter code)
            birth_country_name_short="Deutschland",
            birth_town="Berlin",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="2",  # married

            # Nationality (required) - Naturalized Swiss
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',  # Switzerland (ISO 2-letter code)
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required) - Swiss citizen with place of origin
            # Including naturalization_date and history_municipality_id (rare fields)
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH',
                    'naturalization_date': date(2005, 6, 15),  # Became Swiss citizen in 2005
                    'history_municipality_id': '261'  # Historical BFS code (same as current in this case)
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_naturalized = person_naturalized.to_ech0020()

        # Verify place_of_origin_info structure in Layer 1
        assert layer1_naturalized.place_of_origin_info is not None, "place_of_origin_info missing"
        assert len(layer1_naturalized.place_of_origin_info) == 1, "Should have 1 place of origin"

        origin = layer1_naturalized.place_of_origin_info[0]
        assert origin.place_of_origin.place_of_origin_id == 261, "BFS code not preserved"
        assert origin.place_of_origin.origin_name == 'Zürich', "Origin name not preserved"
        assert origin.place_of_origin.history_municipality_id == "261", "history_municipality_id not preserved"

        # Verify naturalization date in addon data
        assert origin.place_of_origin_addon_data is not None, "place_of_origin_addon_data missing"
        assert origin.place_of_origin_addon_data.naturalization_date == date(2005, 6, 15), \
            "naturalization_date not preserved"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_naturalized = BaseDeliveryPerson.from_ech0020(layer1_naturalized)

        # Verify place of origin preserved with rare fields
        assert roundtrip_naturalized.places_of_origin is not None, "places_of_origin lost"
        assert len(roundtrip_naturalized.places_of_origin) == 1, "places_of_origin count changed"

        origin_rt = roundtrip_naturalized.places_of_origin[0]
        origin_orig = person_naturalized.places_of_origin[0]
        assert origin_rt['bfs_code'] == origin_orig['bfs_code'], "bfs_code not preserved"
        assert origin_rt['name'] == origin_orig['name'], "name not preserved"
        assert origin_rt['canton'] == origin_orig['canton'], "canton not preserved"
        assert origin_rt['naturalization_date'] == origin_orig['naturalization_date'], \
            "naturalization_date not preserved in roundtrip"
        assert origin_rt['history_municipality_id'] == origin_orig['history_municipality_id'], \
            "history_municipality_id not preserved in roundtrip"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_nat = roundtrip_naturalized.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_roundtrip_nat.place_of_origin_info[0].place_of_origin.place_of_origin_id == \
               layer1_naturalized.place_of_origin_info[0].place_of_origin.place_of_origin_id
        assert layer1_roundtrip_nat.place_of_origin_info[0].place_of_origin_addon_data.naturalization_date == \
               layer1_naturalized.place_of_origin_info[0].place_of_origin_addon_data.naturalization_date

    def test_birth_with_parent_names_from_certificate(self):
        """Test 31: Birth with parent names from birth certificate.

        Tests:
        - birth_father_name, birth_father_first_name
        - birth_mother_name, birth_mother_first_name
        - Use case: Parent names from birth certificate (different from parental relationship data)
        - Note: This is NOT the same as parents in ParentalRelationship (Tests 20-22)
        - These are historical names from birth certificate, often used for genealogy
        - Stored in ECH0021BirthAddonData.name_of_parent with TypeOfRelationship enum
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with birth parent names
        person_with_birth_parents = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1990, 7, 25),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="351",  # Bern
            birth_municipality_name="Bern",

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
            paper_lock="0",

            # Rare fields: Parent names from birth certificate
            # These are historical names recorded on the birth certificate
            # Different from current parental relationship (parents field)
            birth_father_name="Schmidt",
            birth_father_first_name="Peter",
            birth_mother_name="Meier",  # Mother's maiden name on birth certificate
            birth_mother_first_name="Anna"
        )

        # Convert to Layer 1
        layer1_birth_parents = person_with_birth_parents.to_ech0020()

        # Verify birth_info.birth_addon_data contains parent names
        assert layer1_birth_parents.birth_info is not None, "birth_info missing"
        assert layer1_birth_parents.birth_info.birth_addon_data is not None, "birth_addon_data missing"
        assert layer1_birth_parents.birth_info.birth_addon_data.name_of_parent is not None, \
            "name_of_parent list missing"
        assert len(layer1_birth_parents.birth_info.birth_addon_data.name_of_parent) == 2, \
            "Should have 2 parent names (father + mother)"

        # Verify father name (TypeOfRelationship.FATHER = 4)
        parents = layer1_birth_parents.birth_info.birth_addon_data.name_of_parent
        father = next((p for p in parents if p.type_of_relationship.value == "4"), None)
        mother = next((p for p in parents if p.type_of_relationship.value == "3"), None)

        assert father is not None, "Father name entry missing"
        assert father.official_name == "Schmidt", "Father official_name not preserved"
        assert father.first_name == "Peter", "Father first_name not preserved"

        # Verify mother name (TypeOfRelationship.MOTHER = 3)
        assert mother is not None, "Mother name entry missing"
        assert mother.official_name == "Meier", "Mother official_name not preserved"
        assert mother.first_name == "Anna", "Mother first_name not preserved"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_birth_parents = BaseDeliveryPerson.from_ech0020(layer1_birth_parents)

        # Verify parent names preserved
        assert roundtrip_birth_parents.birth_father_name == "Schmidt", \
            "birth_father_name not preserved"
        assert roundtrip_birth_parents.birth_father_first_name == "Peter", \
            "birth_father_first_name not preserved"
        assert roundtrip_birth_parents.birth_mother_name == "Meier", \
            "birth_mother_name not preserved"
        assert roundtrip_birth_parents.birth_mother_first_name == "Anna", \
            "birth_mother_first_name not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_bp = roundtrip_birth_parents.to_ech0020()

        # Verify Layer 1 models equivalent
        father_rt = next((p for p in layer1_roundtrip_bp.birth_info.birth_addon_data.name_of_parent
                          if p.type_of_relationship.value == "4"), None)
        mother_rt = next((p for p in layer1_roundtrip_bp.birth_info.birth_addon_data.name_of_parent
                          if p.type_of_relationship.value == "3"), None)

        assert father_rt.official_name == father.official_name
        assert father_rt.first_name == father.first_name
        assert mother_rt.official_name == mother.official_name
        assert mother_rt.first_name == mother.first_name

    def test_marital_proof_flag(self):
        """Test 32: Marital proof flag (official_proof_of_marital_status_yes_no).

        Tests:
        - official_proof_of_marital_status_yes_no field
        - Use case: Indicates whether official proof of marital status exists
        - Stored in ECH0011MaritalData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with marital proof flag
        person_marital_proof = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="11111",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1982, 11, 5),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="2",  # married

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
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Rare field: Marital proof flag
            official_proof_of_marital_status_yes_no=True  # Official marriage certificate exists
        )

        # Convert to Layer 1
        layer1_marital_proof = person_marital_proof.to_ech0020()

        # Verify marital_info contains proof flag
        assert layer1_marital_proof.marital_info is not None, "marital_info missing"
        assert layer1_marital_proof.marital_info.marital_data is not None, "marital_data missing"
        assert layer1_marital_proof.marital_info.marital_data.official_proof_of_marital_status_yes_no is True, \
            "official_proof_of_marital_status_yes_no not preserved"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_marital_proof = BaseDeliveryPerson.from_ech0020(layer1_marital_proof)

        # Verify proof flag preserved
        assert roundtrip_marital_proof.official_proof_of_marital_status_yes_no is True, \
            "official_proof_of_marital_status_yes_no not preserved in roundtrip"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_mp = roundtrip_marital_proof.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_roundtrip_mp.marital_info.marital_data.official_proof_of_marital_status_yes_no == \
               layer1_marital_proof.marital_info.marital_data.official_proof_of_marital_status_yes_no
