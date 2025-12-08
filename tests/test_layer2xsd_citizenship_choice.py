"""XSD Validation Tests for Citizenship CHOICE Constraint (Priority 8)

Extends test_layer2_citizenship_choice.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Citizenship CHOICE constraint:
- Swiss: places_of_origin present, residence_permit None
- Foreign: residence_permit present, places_of_origin None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, country codes)
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


class TestLayer2XSDCitizenshipChoice:
    """XSD validation tests for citizenship CHOICE constraint."""

    def test_swiss_person_with_places_of_origin_xsd_validation(self):
        """Test Swiss person with places_of_origin with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 Swiss person with places_of_origin
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
            sender_id="sedex://T1-TEST-XSD-SWISS",
            manufacturer="XSDTest",
            product="CitizenshipTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 Swiss person with places_of_origin
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1980, 5, 15),
            vn="7561234567890",  # Required for XSD validation

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

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Bahnhofstrasse",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8001,
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

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 citizenship CHOICE: Swiss person has places_of_origin
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.place_of_origin_info is not None, "places_of_origin missing"
        assert len(layer1_person.place_of_origin_info) == 1, "Should have 1 place of origin"
        assert layer1_person.place_of_origin_info[0].place_of_origin.place_of_origin_id == 261
        assert layer1_person.residence_permit_data is None, \
            "residence_permit_data should be None for Swiss citizen"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "swiss_citizenship_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Müller' in xml_content, "Person name should be in XML"
            assert 'Hans' in xml_content, "First name should be in XML"
            assert 'Zürich' in xml_content, "Place of origin should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 citizenship CHOICE still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.place_of_origin_info is not None, \
                "places_of_origin should be preserved after XML roundtrip"
            assert len(roundtrip_layer1_person.place_of_origin_info) == 1
            assert roundtrip_layer1_person.place_of_origin_info[0].place_of_origin.place_of_origin_id == 261
            assert roundtrip_layer1_person.residence_permit_data is None, \
                "residence_permit_data should still be None after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.nationality_status == person.nationality_status

            # Verify citizenship CHOICE preserved
            assert roundtrip_event.person.places_of_origin is not None, \
                "places_of_origin lost in full roundtrip"
            assert len(roundtrip_event.person.places_of_origin) == 1
            assert roundtrip_event.person.places_of_origin[0]['bfs_code'] == '261'
            assert roundtrip_event.person.places_of_origin[0]['name'] == 'Zürich'
            assert roundtrip_event.person.places_of_origin[0]['canton'] == 'ZH'
            assert roundtrip_event.person.residence_permit is None, \
                "residence_permit should be None for Swiss citizen"

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_foreign_person_with_residence_permit_xsd_validation(self):
        """Test foreign person with residence_permit with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 foreign person with residence_permit
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
            sender_id="sedex://T1-TEST-XSD-FOREIGN",
            manufacturer="XSDTest",
            product="CitizenshipTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 foreign person with residence_permit
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1985, 8, 20),
            vn="7569876543210",  # Required for XSD validation

            # Birth info (required) - foreign birth place
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8207",  # Germany (BFS 4-digit code)
            birth_country_iso="DE",   # Germany (ISO 2-letter code)
            birth_country_name_short="Deutschland",
            birth_town="München",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="2",  # married

            # Nationality (required) - German
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8207',  # Germany (BFS 4-digit code)
                    'country_iso': 'DE',   # Germany (ISO 2-letter code)
                    'country_name_short': 'Deutschland'
                }
            ],

            # Citizenship CHOICE (required) - Foreign citizen with residence permit
            residence_permit='03',  # Settlement permit (Niederlassungsbewilligung C)
            residence_permit_valid_from=date(2010, 1, 1),
            residence_permit_valid_till=date(2030, 12, 31),

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Hauptstrasse",
            house_number="10",
            town="Bern",
            swiss_zip_code=3000,
            type_of_household="2"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="351",  # Bern
            reporting_municipality_name="Bern",
            arrival_date=date(2024, 2, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 citizenship CHOICE: Foreign person has residence_permit
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.residence_permit_data is not None, "residence_permit_data missing"
        assert layer1_person.residence_permit_data.residence_permit == '03'
        assert layer1_person.residence_permit_data.residence_permit_valid_from == date(2010, 1, 1)
        assert layer1_person.residence_permit_data.residence_permit_valid_till == date(2030, 12, 31)
        assert layer1_person.place_of_origin_info is None, \
            "place_of_origin_info should be None for foreign citizen"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "foreign_citizenship_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Schmidt' in xml_content, "Person name should be in XML"
            assert 'Maria' in xml_content, "First name should be in XML"
            assert 'München' in xml_content, "Birth town should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 citizenship CHOICE still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.residence_permit_data is not None, \
                "residence_permit_data should be preserved after XML roundtrip"
            assert roundtrip_layer1_person.residence_permit_data.residence_permit == '03'
            assert roundtrip_layer1_person.residence_permit_data.residence_permit_valid_from == date(2010, 1, 1)
            assert roundtrip_layer1_person.residence_permit_data.residence_permit_valid_till == date(2030, 12, 31)
            assert roundtrip_layer1_person.place_of_origin_info is None, \
                "place_of_origin_info should still be None after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.birth_place_type == PlaceType.FOREIGN
            assert roundtrip_event.person.birth_country_iso == "DE"
            assert roundtrip_event.person.birth_town == "München"
            assert roundtrip_event.person.nationality_status == "2"

            # Verify citizenship CHOICE preserved
            assert roundtrip_event.person.residence_permit is not None, \
                "residence_permit lost in full roundtrip"
            assert roundtrip_event.person.residence_permit == '03'
            assert roundtrip_event.person.residence_permit_valid_from == date(2010, 1, 1)
            assert roundtrip_event.person.residence_permit_valid_till == date(2030, 12, 31)
            assert roundtrip_event.person.places_of_origin is None, \
                "places_of_origin should be None for foreign citizen"

            # SUCCESS: Complete chain validated with zero data loss! 🎉
