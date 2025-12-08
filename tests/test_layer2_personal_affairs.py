"""Tests 16-18: Personal Affairs

Tests Layer 2 handling of personal affairs and family status fields:
- Test 16: Health insurance data
- Test 17: Matrimonial inheritance arrangement
- Test 18: Nationality fields (dual/multiple nationalities)

These are optional fields related to personal legal status.

Tests verify:
1. Layer 2 construction with personal affairs fields
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, canton codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestPersonalAffairs:
    """Test Layer 2 personal affairs fields."""

    def test_health_insurance_data(self):
        """Test 16: Health insurance data.

        Tests:
        - health_insured field (boolean → "1"/"0")
        - Use case: Track health insurance compliance (Swiss requirement)
        - Stored in ECH0011HealthInsuranceData
        - Boolean True/False in Layer 2, "1"/"0" string in Layer 1
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with health insurance data
        person_health = BaseDeliveryPerson(
            local_person_id="10008",
            local_person_id_category="MU.6172",
            official_name="Brunner",
            first_name="Anna",
            sex="2",
            date_of_birth=date(1991, 9, 8),
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,
            # Health insurance data (optional)
            health_insured=True
        )

        # Convert to Layer 1
        layer1_health = person_health.to_ech0020()
        assert layer1_health.health_insurance_data is not None
        # Layer 1 stores as string "1" or "0"
        assert layer1_health.health_insurance_data.health_insured == "1", \
            f"Expected '1', got {layer1_health.health_insurance_data.health_insured}"

        # Roundtrip: Layer 1 → Layer 2
        health_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_health)
        # Layer 2 converts back to boolean
        assert health_roundtrip.health_insured is True, \
            f"Expected True, got {health_roundtrip.health_insured}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_health_roundtrip = health_roundtrip.to_ech0020()
        assert layer1_health_roundtrip.health_insurance_data is not None
        assert layer1_health_roundtrip.health_insurance_data.health_insured == "1"

    def test_matrimonial_inheritance_arrangement(self):
        """Test 17: Matrimonial inheritance arrangement.

        Tests:
        - matrimonial_inheritance_arrangement field (marital property regime)
        - matrimonial_inheritance_arrangement_valid_from date
        - Use case: Swiss marital property law (Güterrecht)
        - Stored in ECH0011MatrimonialInheritanceArrangementData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with matrimonial inheritance arrangement
        person_matrimonial = BaseDeliveryPerson(
            local_person_id="10009",
            local_person_id_category="MU.6172",
            official_name="Frei",
            first_name="Sandra",
            sex="2",
            date_of_birth=date(1983, 2, 14),
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="2",  # married
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,
            # Matrimonial inheritance arrangement (optional)
            matrimonial_inheritance_arrangement="1",  # e.g., separation of property
            matrimonial_inheritance_arrangement_valid_from=date(2010, 6, 15)
        )

        # Convert to Layer 1
        layer1_matri = person_matrimonial.to_ech0020()
        assert layer1_matri.matrimonial_inheritance_arrangement_data is not None
        assert layer1_matri.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement == "1"
        assert layer1_matri.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement_valid_from == \
               date(2010, 6, 15)

        # Roundtrip: Layer 1 → Layer 2
        matri_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_matri)
        assert matri_roundtrip.matrimonial_inheritance_arrangement == "1"
        assert matri_roundtrip.matrimonial_inheritance_arrangement_valid_from == date(2010, 6, 15)

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_matri_roundtrip = matri_roundtrip.to_ech0020()
        assert layer1_matri_roundtrip.matrimonial_inheritance_arrangement_data is not None
        assert layer1_matri_roundtrip.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement == "1"
        assert layer1_matri_roundtrip.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement_valid_from == \
               date(2010, 6, 15)

    def test_multiple_nationalities(self):
        """Test 18: Nationality fields with dual nationality.

        Tests:
        - nationalities list with multiple countries
        - Use case: Dual/multiple citizenship (e.g., Swiss-Italian)
        - Validates Rule #5: Preserve lists even for "typical" cases
        - Stored in ECH0011NationalityData.country_info list
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with dual nationality
        person_dual = BaseDeliveryPerson(
            local_person_id="10010",
            local_person_id_category="MU.6172",
            official_name="Rossi",
            first_name="Marco",
            sex="1",
            date_of_birth=date(1985, 5, 30),
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",  # Swiss (primary)
            # Multiple nationalities: Swiss and Italian
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',   # ISO 2-letter code
                    'country_name_short': 'Schweiz'
                },
                {
                    'country_id': '8206',  # Italy (BFS 4-digit code)
                    'country_iso': 'IT',   # ISO 2-letter code
                    'country_name_short': 'Italien'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False
        )

        # Convert to Layer 1
        layer1_dual = person_dual.to_ech0020()
        assert layer1_dual.nationality_data is not None
        assert len(layer1_dual.nationality_data.country_info) == 2, \
            f"Expected 2 countries, got {len(layer1_dual.nationality_data.country_info)}"

        # Verify both countries present (order may vary)
        country_ids = [c.country.country_id for c in layer1_dual.nationality_data.country_info]
        assert "8100" in country_ids, "Switzerland (8100) missing from nationalities"
        assert "8206" in country_ids, "Italy (8206) missing from nationalities"

        # Roundtrip: Layer 1 → Layer 2
        dual_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_dual)
        assert len(dual_roundtrip.nationalities) == 2, \
            f"Expected 2 nationalities, got {len(dual_roundtrip.nationalities)}"

        # Verify both nationalities preserved
        roundtrip_country_ids = [n['country_id'] for n in dual_roundtrip.nationalities]
        assert '8100' in roundtrip_country_ids, "Switzerland (8100) lost in roundtrip"
        assert '8206' in roundtrip_country_ids, "Italy (8206) lost in roundtrip"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_dual_roundtrip = dual_roundtrip.to_ech0020()
        assert layer1_dual_roundtrip.nationality_data is not None
        assert len(layer1_dual_roundtrip.nationality_data.country_info) == 2

        # Verify countries still present after full roundtrip
        roundtrip_ids_final = [c.country.country_id for c in layer1_dual_roundtrip.nationality_data.country_info]
        assert "8100" in roundtrip_ids_final
        assert "8206" in roundtrip_ids_final
