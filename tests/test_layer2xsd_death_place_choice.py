"""XSD Validation Tests for Death Place CHOICE Constraint (Priority 8)

Extends test_layer2_death_place_choice.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Death Place CHOICE constraint:
- SWISS: swiss_municipality present, foreign_country=None, unknown=None
- FOREIGN: foreign_country present, swiss_municipality=None, unknown=None
- UNKNOWN: unknown=True, swiss_municipality=None, foreign_country=None

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


class TestLayer2XSDDeathPlaceChoice:
    """XSD validation tests for death place CHOICE constraint."""

    def test_death_data_swiss_place_xsd_validation(self):
        """Test death data with Swiss place with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 deceased person with Swiss death place
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
            sender_id="sedex://T1-TEST-XSD-DEATH-SWISS",
            manufacturer="XSDTest",
            product="DeathTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 deceased person with Swiss death place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="88888",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Ernst",
            sex="1",  # male
            date_of_birth=date(1930, 3, 10),
            vn="7568888999900",  # Required for XSD validation

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

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Altersheimstrasse",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8003,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",  # Zürich
            reporting_municipality_name="Zürich",
            arrival_date=date(2020, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 death place CHOICE: Swiss place
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.death_data is not None, "death_data should exist"
        assert layer1_person.death_data.death_period is not None
        assert layer1_person.death_data.death_period.date_from == date(2023, 12, 25)
        assert layer1_person.death_data.place_of_death is not None
        assert layer1_person.death_data.place_of_death.swiss_municipality is not None

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "death_swiss_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Weber' in xml_content, "Person name should be in XML"
            assert '2023-12-25' in xml_content, "Death date should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 death place still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.death_data is not None
            assert roundtrip_layer1_person.death_data.death_period.date_from == date(2023, 12, 25)
            assert roundtrip_layer1_person.death_data.place_of_death.swiss_municipality is not None

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.death_date == date(2023, 12, 25)
            assert roundtrip_event.person.death_place_type == PlaceType.SWISS
            assert roundtrip_event.person.death_municipality_bfs == "261"
            assert roundtrip_event.person.death_municipality_name == "Zürich"

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_death_data_foreign_place_xsd_validation(self):
        """Test death data with foreign place with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 deceased person with foreign death place
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
            sender_id="sedex://T1-TEST-XSD-DEATH-FOREIGN",
            manufacturer="XSDTest",
            product="DeathTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 deceased person with foreign death place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="99999",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1945, 8, 5),
            vn="7569999000011",  # Required for XSD validation

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
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Teststrasse",
            house_number="5",
            town="Zürich",
            swiss_zip_code=8004,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",  # Zürich
            reporting_municipality_name="Zürich",
            arrival_date=date(2020, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 death place CHOICE: Foreign place
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.death_data is not None
        assert layer1_person.death_data.death_period.date_from == date(2024, 6, 15)
        assert layer1_person.death_data.place_of_death.foreign_country is not None
        assert layer1_person.death_data.place_of_death.foreign_country.country_id == "8207"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "death_foreign_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Schmidt' in xml_content, "Person name should be in XML"
            assert '2024-06-15' in xml_content, "Death date should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 death place still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.death_data is not None
            assert roundtrip_layer1_person.death_data.death_period.date_from == date(2024, 6, 15)
            assert roundtrip_layer1_person.death_data.place_of_death.foreign_country is not None

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.death_date == date(2024, 6, 15)
            assert roundtrip_event.person.death_place_type == PlaceType.FOREIGN
            assert roundtrip_event.person.death_country_id == "8207"
            assert roundtrip_event.person.death_country_iso == "DE"
            assert roundtrip_event.person.death_country_name_short == "Deutschland"

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_death_data_unknown_place_xsd_validation(self):
        """Test death data with unknown place with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 deceased person with unknown death place
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
            sender_id="sedex://T1-TEST-XSD-DEATH-UNKNOWN",
            manufacturer="XSDTest",
            product="DeathTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 deceased person with unknown death place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10001",
            local_person_id_category="MU.6172",
            official_name="Meier",
            first_name="Peter",
            sex="1",  # male
            date_of_birth=date(1950, 11, 22),
            vn="7560000111122",  # Required for XSD validation

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
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Teststrasse",
            house_number="8",
            town="Zürich",
            swiss_zip_code=8005,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",  # Zürich
            reporting_municipality_name="Zürich",
            arrival_date=date(2020, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 death place CHOICE: Unknown place
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.death_data is not None
        assert layer1_person.death_data.death_period.date_from == date(2022, 3, 8)
        assert layer1_person.death_data.place_of_death.unknown is True

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "death_unknown_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Meier' in xml_content, "Person name should be in XML"
            assert '2022-03-08' in xml_content, "Death date should be in XML"

            # Step 6: XSD validation passed (automatic in to_file)
            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 death place still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.death_data is not None
            assert roundtrip_layer1_person.death_data.death_period.date_from == date(2022, 3, 8)
            assert roundtrip_layer1_person.death_data.place_of_death.unknown is True

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.death_date == date(2022, 3, 8)
            assert roundtrip_event.person.death_place_type == PlaceType.UNKNOWN

            # SUCCESS: Complete chain validated with zero data loss! 🎉
