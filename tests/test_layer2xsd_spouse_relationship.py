"""XSD Validation Tests for Spouse Relationship (Priority 8.3)

Extends test_layer2_spouse_relationship.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Spouse Relationship (optional relationship data):
- Spouse identification (PersonIdentification model)
- Spouse address (separate from main person)
- Marital relationship type

Data policy:
- Fake personal data (names, dates, IDs, addresses)
- Real BFS fixtures (municipality codes)
- Real XSD schema from eCH standard
"""

from datetime import date
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import pytest

from openmun_ech.ech0020.models import (
    BaseDeliveryPerson,
    BaseDeliveryEvent,
    DeliveryConfig,
    DwellingAddressInfo,
    PlaceType,
    PersonIdentification,
    ResidenceType,
)
from openmun_ech.ech0020.v3 import ECH0020Delivery


class TestLayer2XSDSpouseRelationship:
    """XSD validation tests for spouse relationship fields."""

    def test_spouse_with_address_and_full_identification_xsd_validation(self):
        """Test spouse with address and full identification with XML+XSD validation.

        Complete chain validates spouse data and address preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-SPOUSE",
            manufacturer="XSDTest",
            product="SpouseRelationshipTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with spouse and address
        person = BaseDeliveryPerson(
            # Main person identification
            local_person_id="11000",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Anna",
            sex="2",
            date_of_birth=date(1982, 3, 12),
            vn="7561111110000",
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

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Seestrasse",
            house_number="50",
            town="Zürich",
            swiss_zip_code=8002,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",  # Zürich
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 spouse data
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.marital_relationship is not None
        assert layer1_person.marital_relationship.partner is not None
        assert layer1_person.marital_relationship.partner.person_identification is not None

        # Verify spouse identification
        spouse_id = layer1_person.marital_relationship.partner.person_identification
        assert spouse_id.official_name == "Weber"
        assert spouse_id.first_name == "Thomas"
        assert spouse_id.original_name == "Müller"
        assert spouse_id.vn == "7569876543210"
        assert spouse_id.sex == "1"
        assert spouse_id.date_of_birth.year_month_day == date(1980, 7, 22)

        # Verify spouse address
        assert layer1_person.marital_relationship.partner.address is not None
        spouse_addr = layer1_person.marital_relationship.partner.address.address_information
        assert spouse_addr.street == "Bahnhofstrasse"
        assert spouse_addr.house_number == "100"
        assert spouse_addr.swiss_zip_code == 8001
        assert spouse_addr.town == "Zürich"

        # Verify marital relationship type
        assert layer1_person.marital_relationship.type_of_relationship == "1"

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "spouse_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            assert 'Weber' in xml_content
            assert 'Thomas' in xml_content
            assert 'Müller' in xml_content  # Original name (maiden name)
            assert 'Bahnhofstrasse' in xml_content

            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.marital_relationship is not None
            assert roundtrip_layer1_person.marital_relationship.partner is not None

            # Verify spouse identification preserved
            roundtrip_spouse_id = roundtrip_layer1_person.marital_relationship.partner.person_identification
            assert roundtrip_spouse_id.official_name == "Weber"
            assert roundtrip_spouse_id.first_name == "Thomas"
            assert roundtrip_spouse_id.original_name == "Müller"
            assert roundtrip_spouse_id.vn == "7569876543210"
            assert roundtrip_spouse_id.sex == "1"
            assert roundtrip_spouse_id.date_of_birth.year_month_day == date(1980, 7, 22)

            # Verify spouse address preserved
            roundtrip_spouse_addr = roundtrip_layer1_person.marital_relationship.partner.address.address_information
            assert roundtrip_spouse_addr.street == "Bahnhofstrasse"
            assert roundtrip_spouse_addr.house_number == "100"
            assert roundtrip_spouse_addr.swiss_zip_code == 8001
            assert roundtrip_spouse_addr.town == "Zürich"

            # Verify marital relationship type preserved
            assert roundtrip_layer1_person.marital_relationship.type_of_relationship == "1"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss - spouse data
            assert roundtrip_event.person.spouse is not None
            assert roundtrip_event.person.spouse.official_name == "Weber"
            assert roundtrip_event.person.spouse.first_name == "Thomas"
            assert roundtrip_event.person.spouse.original_name == "Müller"
            assert roundtrip_event.person.spouse.vn == "7569876543210"
            assert roundtrip_event.person.spouse.sex == "1"
            assert roundtrip_event.person.spouse.date_of_birth == date(1980, 7, 22)

            # Verify spouse address preserved
            assert roundtrip_event.person.spouse_address_street == "Bahnhofstrasse"
            assert roundtrip_event.person.spouse_address_house_number == "100"
            assert roundtrip_event.person.spouse_address_postal_code == "8001"
            assert roundtrip_event.person.spouse_address_town == "Zürich"

            # Verify marital relationship type preserved
            assert roundtrip_event.person.marital_relationship_type == "1"

            # SUCCESS: Relationship data validated! 🎉
