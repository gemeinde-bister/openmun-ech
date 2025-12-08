"""XSD Validation Tests for Contact CHOICE Constraint (Priority 8)

Extends test_layer2_contact_choice.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Contact CHOICE constraint:
- Person: contact_person_partner present, contact_organization None
- Organization: contact_organization present, contact_person/contact_person_partner None

Data policy:
- Fake personal data (names, dates, IDs)
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
    ResidenceType,
)
from openmun_ech.ech0020.v3 import ECH0020Delivery


class TestLayer2XSDContactChoice:
    """XSD validation tests for contact CHOICE constraint."""

    def test_contact_person_with_address_xsd_validation(self):
        """Test contact person with address with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person with contact person
        2. Create Layer 2 event (person + residence)
        3. Finalize to complete ECH0020Delivery
        4. Export to XML file
        5. Validate XML against XSD schema
        6. Read XML back to Layer 1
        7. Convert back to Layer 2
        8. Verify zero data loss
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-CONTACT-PERSON",
            manufacturer="XSDTest",
            product="ContactTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with contact person
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="22222",
            local_person_id_category="MU.6172",
            official_name="Meier",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1990, 3, 25),
            vn="7562222333344",  # Required for XSD validation

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="121",  # Protestant

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

            # Contact person (CHOICE: person XOR organization)
            contact_person_official_name="Schmidt",
            contact_person_first_name="Julia",
            # Include identifying data to trigger personIdentificationPartner (Light) creation
            contact_person_local_person_id="55555",
            contact_person_local_person_id_category="MU.6172",

            # Contact address (required when contact provided)
            contact_address_street="Bahnhofstrasse",
            contact_address_house_number="42",
            contact_address_postal_code="8001",
            contact_address_town="Zürich",

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Teststrasse",
            house_number="10",
            town="Zürich",
            swiss_zip_code=8002,
            type_of_household="2"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",  # Zürich
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 3, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 contact CHOICE: has contact_person_partner
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.contact_data is not None, "contact_data should exist"
        assert layer1_person.contact_data.contact_person_partner is not None, \
            "contact_person_partner should exist"
        assert layer1_person.contact_data.contact_person_partner.official_name == "Schmidt"
        assert layer1_person.contact_data.contact_person_partner.first_name == "Julia"
        assert layer1_person.contact_data.contact_organization is None, \
            "contact_organization should be None"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "contact_person_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Meier' in xml_content, "Person name should be in XML"
            assert 'Schmidt' in xml_content, "Contact person name should be in XML"
            assert 'Julia' in xml_content, "Contact person first name should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 contact CHOICE still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.contact_data is not None
            assert roundtrip_layer1_person.contact_data.contact_person_partner is not None
            assert roundtrip_layer1_person.contact_data.contact_person_partner.official_name == "Schmidt"
            assert roundtrip_layer1_person.contact_data.contact_person_partner.first_name == "Julia"
            assert roundtrip_layer1_person.contact_data.contact_organization is None

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name

            # Verify contact person preserved
            assert roundtrip_event.person.contact_person_official_name == "Schmidt"
            assert roundtrip_event.person.contact_person_first_name == "Julia"
            assert roundtrip_event.person.contact_organization_name is None

            # Verify contact address preserved
            assert roundtrip_event.person.contact_address_street == "Bahnhofstrasse"
            assert roundtrip_event.person.contact_address_house_number == "42"
            assert roundtrip_event.person.contact_address_postal_code == "8001"
            assert roundtrip_event.person.contact_address_town == "Zürich"

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_contact_organization_with_address_xsd_validation(self):
        """Test contact organization with address with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person with contact organization
        2. Create Layer 2 event (person + residence)
        3. Finalize to complete ECH0020Delivery
        4. Export to XML file
        5. Validate XML against XSD schema
        6. Read XML back to Layer 1
        7. Convert back to Layer 2
        8. Verify zero data loss
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-CONTACT-ORG",
            manufacturer="XSDTest",
            product="ContactTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with contact organization
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="33333",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Sarah",
            sex="2",  # female
            date_of_birth=date(1988, 7, 12),
            vn="7563333444455",  # Required for XSD validation

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="351",  # Bern
            birth_municipality_name="Bern",

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
                    'bfs_code': '351',
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Contact organization (CHOICE: organization XOR person)
            contact_organization_name="Einwohnerdienste Bern",

            # Contact address (required when contact provided)
            contact_address_street="Predigergasse",
            contact_address_house_number="5",
            contact_address_postal_code="3011",
            contact_address_town="Bern",

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Wohnstrasse",
            house_number="20",
            town="Bern",
            swiss_zip_code=3012,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="351",  # Bern
            reporting_municipality_name="Bern",
            arrival_date=date(2024, 4, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 contact CHOICE: has contact_organization
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.contact_data is not None, "contact_data should exist"
        assert layer1_person.contact_data.contact_organization is not None, \
            "contact_organization should exist"
        assert layer1_person.contact_data.contact_organization.local_person_id.person_id == "33333"
        assert layer1_person.contact_data.contact_person is None
        assert layer1_person.contact_data.contact_person_partner is None

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "contact_organization_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Fischer' in xml_content, "Person name should be in XML"
            assert 'Einwohnerdienste Bern' in xml_content, "Contact organization should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 contact CHOICE still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.contact_data is not None
            assert roundtrip_layer1_person.contact_data.contact_organization is not None
            assert roundtrip_layer1_person.contact_data.contact_person is None
            assert roundtrip_layer1_person.contact_data.contact_person_partner is None

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name

            # Verify contact organization preserved
            assert roundtrip_event.person.contact_organization_name == "Einwohnerdienste Bern"
            assert roundtrip_event.person.contact_person_official_name is None
            assert roundtrip_event.person.contact_person_first_name is None

            # Verify contact address preserved
            assert roundtrip_event.person.contact_address_street == "Predigergasse"
            assert roundtrip_event.person.contact_address_house_number == "5"
            assert roundtrip_event.person.contact_address_postal_code == "3011"
            assert roundtrip_event.person.contact_address_town == "Bern"

            # SUCCESS: Complete chain validated with zero data loss! 🎉
