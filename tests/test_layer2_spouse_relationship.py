"""Test 19: Spouse Relationship

Tests Layer 2 handling of marital relationships (spouse data):
- Spouse identification (PersonIdentification model)
- Spouse address (separate from main person)
- Marital relationship type (married vs registered partnership)

Tests verify:
1. Layer 2 construction with spouse and address
2. to_ech0020() conversion (Layer 2 → Layer 1 marital_relationship)
3. from_ech0020() conversion (Layer 1 → Layer 2 spouse fields)
4. Full roundtrip with zero data loss

Data policy:
- Fake personal data (names, dates, IDs, addresses)
- Real BFS fixtures (municipality codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType, PersonIdentification


class TestSpouseRelationship:
    """Test Layer 2 spouse relationship fields."""

    def test_spouse_with_address_and_full_identification(self):
        """Test 19: Spouse with address and complete identification.

        Tests:
        - spouse field (PersonIdentification model with all fields)
        - spouse_address_* fields (street, house_number, postal_code, town)
        - marital_relationship_type ("1" = married, "2" = registered partnership)
        - Use case: Married couple with separate addresses
        - Stored in ECH0021MaritalRelationship with partner and address
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with spouse and address
        person_married = BaseDeliveryPerson(
            # Main person identification
            local_person_id="11000",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Anna",
            sex="2",
            date_of_birth=date(1982, 3, 12),
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

            # Spouse data (PersonIdentification with all optional fields)
            spouse=PersonIdentification(
                vn="7569876543210",  # AHV-13
                local_person_id="11001",
                local_person_id_category="MU.6172",
                official_name="Weber",
                first_name="Thomas",
                original_name="Müller",  # Maiden name (partner's previous name)
                sex="1",
                date_of_birth=date(1980, 7, 22)
            ),

            # Spouse address (different from main person)
            spouse_address_street="Bahnhofstrasse",
            spouse_address_house_number="100",
            spouse_address_postal_code="8001",
            spouse_address_town="Zürich",

            # Marital relationship type
            marital_relationship_type="1"  # 1=married, 2=registered partnership
        )

        # Convert to Layer 1
        layer1_married = person_married.to_ech0020()

        # Verify marital_relationship structure
        assert layer1_married.marital_relationship is not None, "marital_relationship should be present"
        assert layer1_married.marital_relationship.partner is not None, "partner should be present"
        assert layer1_married.marital_relationship.partner.person_identification is not None, \
            "person_identification should be present"

        # Verify spouse identification
        spouse_id = layer1_married.marital_relationship.partner.person_identification
        assert spouse_id.official_name == "Weber", f"Expected official_name='Weber', got {spouse_id.official_name}"
        assert spouse_id.first_name == "Thomas", f"Expected first_name='Thomas', got {spouse_id.first_name}"
        assert spouse_id.original_name == "Müller", f"Expected original_name='Müller', got {spouse_id.original_name}"
        assert spouse_id.vn == "7569876543210", f"Expected vn='7569876543210', got {spouse_id.vn}"
        assert spouse_id.sex == "1", f"Expected sex='1', got {spouse_id.sex}"
        assert spouse_id.date_of_birth.year_month_day == date(1980, 7, 22), \
            f"Expected DOB=1980-07-22, got {spouse_id.date_of_birth.year_month_day}"

        # Verify spouse address
        assert layer1_married.marital_relationship.partner.address is not None, "spouse address should be present"
        spouse_addr = layer1_married.marital_relationship.partner.address.address_information
        assert spouse_addr.street == "Bahnhofstrasse", f"Expected street='Bahnhofstrasse', got {spouse_addr.street}"
        assert spouse_addr.house_number == "100", f"Expected house_number='100', got {spouse_addr.house_number}"
        assert spouse_addr.swiss_zip_code == 8001, f"Expected postal_code=8001, got {spouse_addr.swiss_zip_code}"
        assert spouse_addr.town == "Zürich", f"Expected town='Zürich', got {spouse_addr.town}"

        # Verify marital relationship type
        assert layer1_married.marital_relationship.type_of_relationship == "1", \
            f"Expected type_of_relationship='1', got {layer1_married.marital_relationship.type_of_relationship}"

        # Roundtrip: Layer 1 → Layer 2
        married_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_married)

        # Verify spouse data preserved
        assert married_roundtrip.spouse is not None, "spouse should be preserved"
        assert married_roundtrip.spouse.official_name == "Weber", \
            f"Expected spouse official_name='Weber', got {married_roundtrip.spouse.official_name}"
        assert married_roundtrip.spouse.first_name == "Thomas", \
            f"Expected spouse first_name='Thomas', got {married_roundtrip.spouse.first_name}"
        assert married_roundtrip.spouse.original_name == "Müller", \
            f"Expected spouse original_name='Müller', got {married_roundtrip.spouse.original_name}"
        assert married_roundtrip.spouse.vn == "7569876543210", \
            f"Expected spouse vn='7569876543210', got {married_roundtrip.spouse.vn}"
        assert married_roundtrip.spouse.sex == "1", \
            f"Expected spouse sex='1', got {married_roundtrip.spouse.sex}"
        assert married_roundtrip.spouse.date_of_birth == date(1980, 7, 22), \
            f"Expected spouse DOB=1980-07-22, got {married_roundtrip.spouse.date_of_birth}"

        # Verify spouse address preserved
        assert married_roundtrip.spouse_address_street == "Bahnhofstrasse", \
            f"Expected spouse_address_street='Bahnhofstrasse', got {married_roundtrip.spouse_address_street}"
        assert married_roundtrip.spouse_address_house_number == "100", \
            f"Expected spouse_address_house_number='100', got {married_roundtrip.spouse_address_house_number}"
        assert married_roundtrip.spouse_address_postal_code == "8001", \
            f"Expected spouse_address_postal_code='8001', got {married_roundtrip.spouse_address_postal_code}"
        assert married_roundtrip.spouse_address_town == "Zürich", \
            f"Expected spouse_address_town='Zürich', got {married_roundtrip.spouse_address_town}"

        # Verify marital relationship type preserved
        assert married_roundtrip.marital_relationship_type == "1", \
            f"Expected marital_relationship_type='1', got {married_roundtrip.marital_relationship_type}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_married_roundtrip = married_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_married_roundtrip.marital_relationship is not None
        spouse_id_rt = layer1_married_roundtrip.marital_relationship.partner.person_identification
        assert spouse_id_rt.official_name == spouse_id.official_name
        assert spouse_id_rt.first_name == spouse_id.first_name
        assert spouse_id_rt.original_name == spouse_id.original_name
        assert spouse_id_rt.vn == spouse_id.vn

        # Verify address still present
        spouse_addr_rt = layer1_married_roundtrip.marital_relationship.partner.address.address_information
        assert spouse_addr_rt.street == spouse_addr.street
        assert spouse_addr_rt.house_number == spouse_addr.house_number
        assert spouse_addr_rt.swiss_zip_code == spouse_addr.swiss_zip_code
        assert spouse_addr_rt.town == spouse_addr.town
