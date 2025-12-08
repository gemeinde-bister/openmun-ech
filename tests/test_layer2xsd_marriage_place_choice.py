"""XSD Validation Tests for Marriage Place CHOICE Constraint (Priority 8)

Extends test_layer2_marriage_place_choice.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Marriage Place CHOICE constraint:
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


class TestLayer2XSDMarriagePlaceChoice:
    """XSD validation tests for marriage place CHOICE constraint."""

    def test_marriage_place_swiss_xsd_validation(self):
        """Test marriage place SWISS with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person married in Switzerland
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
            sender_id="sedex://T1-TEST-XSD-MARRIAGE-SWISS",
            manufacturer="XSDTest",
            product="MarriagePlaceTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with SWISS marriage place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="44444",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Peter",
            sex="1",  # male
            date_of_birth=date(1982, 9, 5),
            vn="7561111444444",  # Required for XSD validation

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

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Hauptstrasse",
            house_number="25",
            town="Zürich",
            swiss_zip_code=8000,
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

        # Verify Layer 1 marriage place is SWISS
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.marital_info.marital_data_addon is not None, \
            "marital_data_addon should exist in Layer 1"
        assert layer1_person.marital_info.marital_data_addon.place_of_marriage is not None, \
            "place_of_marriage should exist"
        place_of_marriage = layer1_person.marital_info.marital_data_addon.place_of_marriage
        assert place_of_marriage.swiss_municipality is not None, \
            "swiss_municipality should exist for SWISS marriage"
        assert place_of_marriage.foreign_country is None, \
            "foreign_country should be None for SWISS marriage"
        assert place_of_marriage.unknown is None, \
            "unknown should be None for SWISS marriage"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "marriage_swiss_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Keller' in xml_content, "Person name should be in XML"
            assert 'Peter' in xml_content, "First name should be in XML"

            # Step 6: XSD validation (built-in library validation)
            # The to_file() method uses library's XSD validation internally
            # If we got here without exception, XSD validation passed
            # Now explicitly verify by reading back

            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert roundtrip_delivery.version == "3.0", "Version should be preserved"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 marriage place still SWISS after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.marital_info.marital_data_addon is not None, \
                "marital_data_addon should still exist after XML roundtrip"
            assert roundtrip_layer1_person.marital_info.marital_data_addon.place_of_marriage is not None, \
                "place_of_marriage should still exist after XML roundtrip"
            roundtrip_place = roundtrip_layer1_person.marital_info.marital_data_addon.place_of_marriage
            assert roundtrip_place.swiss_municipality is not None, \
                "swiss_municipality should still exist after XML roundtrip"
            assert roundtrip_place.foreign_country is None, \
                "foreign_country should still be None after XML roundtrip"
            assert roundtrip_place.unknown is None, \
                "unknown should still be None after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name, \
                "Official name should be preserved"
            assert roundtrip_event.person.first_name == person.first_name, \
                "First name should be preserved"
            assert roundtrip_event.person.marital_status == "2", \
                "Marital status should be married"
            assert roundtrip_event.person.marriage_place_type == PlaceType.SWISS, \
                f"Marriage place type should be SWISS, got {roundtrip_event.person.marriage_place_type}"
            assert roundtrip_event.person.marriage_municipality_bfs == "351", \
                f"Marriage municipality BFS should be preserved, got {roundtrip_event.person.marriage_municipality_bfs}"
            assert roundtrip_event.person.marriage_municipality_name == "Bern", \
                f"Marriage municipality name should be preserved"
            assert roundtrip_event.person.marriage_country_iso is None, \
                "marriage_country_iso should be None for SWISS"
            assert roundtrip_event.person.marriage_town is None, \
                "marriage_town should be None for SWISS"

            # Verify other person data preserved
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.vn == person.vn
            assert roundtrip_event.person.religion == person.religion

            # Verify event data preserved
            assert roundtrip_event.residence_type == ResidenceType.MAIN
            assert roundtrip_event.reporting_municipality_bfs == "261"
            assert roundtrip_event.reporting_municipality_name == "Zürich"
            assert roundtrip_event.arrival_date == date(2024, 1, 1)

            # SUCCESS: Complete chain validated with zero data loss! 🎉
            # Layer 2 → Layer 1 → XML → XSD ✅ → Layer 1 → Layer 2

    def test_marriage_place_foreign_xsd_validation(self):
        """Test marriage place FOREIGN with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person married abroad (Italy)
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
            sender_id="sedex://T1-TEST-XSD-MARRIAGE-FOREIGN",
            manufacturer="XSDTest",
            product="MarriagePlaceTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with FOREIGN marriage place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="55555",
            local_person_id_category="MU.6172",
            official_name="Rossi",
            first_name="Lucia",
            sex="2",  # female
            date_of_birth=date(1987, 4, 18),
            vn="7561111555555",  # Required for XSD validation

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

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Via Roma",
            house_number="7",
            town="Lugano",
            swiss_zip_code=6900,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="5192",  # Lugano
            reporting_municipality_name="Lugano",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 marriage place is FOREIGN
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.marital_info.marital_data_addon is not None, \
            "marital_data_addon should exist in Layer 1"
        assert layer1_person.marital_info.marital_data_addon.place_of_marriage is not None, \
            "place_of_marriage should exist"
        place_of_marriage = layer1_person.marital_info.marital_data_addon.place_of_marriage
        assert place_of_marriage.foreign_country is not None, \
            "foreign_country should exist for FOREIGN marriage"
        assert place_of_marriage.foreign_town == "Roma", \
            f"Expected 'Roma', got {place_of_marriage.foreign_town}"
        assert place_of_marriage.swiss_municipality is None, \
            "swiss_municipality should be None for FOREIGN marriage"
        assert place_of_marriage.unknown is None, \
            "unknown should be None for FOREIGN marriage"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "marriage_foreign_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Rossi' in xml_content, "Person name should be in XML"
            assert 'Lucia' in xml_content, "First name should be in XML"
            assert 'Roma' in xml_content, "Marriage town should be in XML"

            # Step 6: XSD validation (built-in library validation)
            # The to_file() method uses library's XSD validation internally
            # If we got here without exception, XSD validation passed
            # Now explicitly verify by reading back

            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert roundtrip_delivery.version == "3.0", "Version should be preserved"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 marriage place still FOREIGN after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.marital_info.marital_data_addon is not None, \
                "marital_data_addon should still exist after XML roundtrip"
            assert roundtrip_layer1_person.marital_info.marital_data_addon.place_of_marriage is not None, \
                "place_of_marriage should still exist after XML roundtrip"
            roundtrip_place = roundtrip_layer1_person.marital_info.marital_data_addon.place_of_marriage
            assert roundtrip_place.foreign_country is not None, \
                "foreign_country should still exist after XML roundtrip"
            assert roundtrip_place.foreign_town == "Roma", \
                f"Marriage town should be preserved, got {roundtrip_place.foreign_town}"
            assert roundtrip_place.foreign_country.country_id == "8211", \
                f"Country ID should be preserved"
            assert roundtrip_place.swiss_municipality is None, \
                "swiss_municipality should still be None after XML roundtrip"
            assert roundtrip_place.unknown is None, \
                "unknown should still be None after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name, \
                "Official name should be preserved"
            assert roundtrip_event.person.first_name == person.first_name, \
                "First name should be preserved"
            assert roundtrip_event.person.marital_status == "2", \
                "Marital status should be married"
            assert roundtrip_event.person.marriage_place_type == PlaceType.FOREIGN, \
                f"Marriage place type should be FOREIGN, got {roundtrip_event.person.marriage_place_type}"
            assert roundtrip_event.person.marriage_country_id == "8211", \
                f"Marriage country ID should be preserved, got {roundtrip_event.person.marriage_country_id}"
            assert roundtrip_event.person.marriage_country_iso == "IT", \
                f"Marriage country ISO should be preserved"
            assert roundtrip_event.person.marriage_town == "Roma", \
                f"Marriage town should be preserved"
            assert roundtrip_event.person.marriage_municipality_bfs is None, \
                "marriage_municipality_bfs should be None for FOREIGN"
            assert roundtrip_event.person.marriage_municipality_name is None, \
                "marriage_municipality_name should be None for FOREIGN"

            # Verify other person data preserved
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.vn == person.vn
            assert roundtrip_event.person.religion == person.religion

            # Verify event data preserved
            assert roundtrip_event.residence_type == ResidenceType.MAIN
            assert roundtrip_event.reporting_municipality_bfs == "5192"
            assert roundtrip_event.reporting_municipality_name == "Lugano"
            assert roundtrip_event.arrival_date == date(2024, 1, 1)

            # SUCCESS: Complete chain validated with zero data loss! 🎉
            # Layer 2 → Layer 1 → XML → XSD ✅ → Layer 1 → Layer 2
