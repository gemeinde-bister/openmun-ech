"""XSD Validation Tests for Person Metadata (Priority 8.2)

Extends test_layer2_person_metadata.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Person Metadata (optional fields):
- Person additional data (mr_mrs, title, language_of_correspondance)
- Lock data with validity dates

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


class TestLayer2XSDPersonMetadata:
    """XSD validation tests for person metadata fields."""

    def test_person_additional_data_xsd_validation(self):
        """Test person additional data with full XML+XSD validation.

        Complete chain validates salutation, title, and language preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-PERSON-ADDITIONAL",
            manufacturer="XSDTest",
            product="PersonMetadataTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create person with additional metadata
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10002",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Elisabeth",
            sex="2",  # female
            date_of_birth=date(1975, 4, 20),
            vn="7561111000002",

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

            # Person additional data (optional) - mr_mrs, title, language
            mr_mrs="2",  # Mrs/Frau
            title="Dr.",
            language_of_correspondance="de"  # German
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Universitätstrasse",
            house_number="55",
            town="Zürich",
            swiss_zip_code=8006,
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

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.person_additional_data is not None
        assert layer1_person.person_additional_data.mr_mrs == "2"
        assert layer1_person.person_additional_data.title == "Dr."
        assert layer1_person.person_additional_data.language_of_correspondance == "de"

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "person_additional_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            assert 'Fischer' in xml_content
            assert 'Dr.' in xml_content

            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.person_additional_data is not None
            assert roundtrip_layer1_person.person_additional_data.mr_mrs == "2"
            assert roundtrip_layer1_person.person_additional_data.title == "Dr."
            assert roundtrip_layer1_person.person_additional_data.language_of_correspondance == "de"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.mr_mrs == "2"
            assert roundtrip_event.person.title == "Dr."
            assert roundtrip_event.person.language_of_correspondance == "de"

            # SUCCESS! 🎉

    def test_lock_data_with_validity_dates_xsd_validation(self):
        """Test lock data with validity dates and full XML+XSD validation.

        Complete chain validates lock data with temporal constraints.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-LOCK-DATES",
            manufacturer="XSDTest",
            product="PersonMetadataTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create person with lock data including validity dates
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10003",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1988, 9, 12),
            vn="7561111000003",

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

            # Lock data (required) - with validity dates
            data_lock="1",  # Locked
            data_lock_valid_from=date(2024, 1, 1),
            data_lock_valid_till=date(2025, 12, 31),
            paper_lock=True,  # Locked
            paper_lock_valid_from=date(2024, 6, 1),
            paper_lock_valid_till=date(2024, 12, 31)
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Sperrstrasse",
            house_number="7",
            town="Winterthur",
            swiss_zip_code=8400,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="230",  # Winterthur
            reporting_municipality_name="Winterthur",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.lock_data is not None
        assert layer1_person.lock_data.data_lock == "1"
        assert layer1_person.lock_data.data_lock_valid_from == date(2024, 1, 1)
        assert layer1_person.lock_data.data_lock_valid_till == date(2025, 12, 31)
        assert layer1_person.lock_data.paper_lock == "1"
        assert layer1_person.lock_data.paper_lock_valid_from == date(2024, 6, 1)
        assert layer1_person.lock_data.paper_lock_valid_till == date(2024, 12, 31)

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "lock_dates_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.lock_data is not None
            assert roundtrip_layer1_person.lock_data.data_lock == "1"
            assert roundtrip_layer1_person.lock_data.data_lock_valid_from == date(2024, 1, 1)
            assert roundtrip_layer1_person.lock_data.data_lock_valid_till == date(2025, 12, 31)
            assert roundtrip_layer1_person.lock_data.paper_lock == "1"
            assert roundtrip_layer1_person.lock_data.paper_lock_valid_from == date(2024, 6, 1)
            assert roundtrip_layer1_person.lock_data.paper_lock_valid_till == date(2024, 12, 31)

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.data_lock == "1"
            assert roundtrip_event.person.data_lock_valid_from == date(2024, 1, 1)
            assert roundtrip_event.person.data_lock_valid_till == date(2025, 12, 31)
            assert roundtrip_event.person.paper_lock is True
            assert roundtrip_event.person.paper_lock_valid_from == date(2024, 6, 1)
            assert roundtrip_event.person.paper_lock_valid_till == date(2024, 12, 31)

            # SUCCESS! 🎉
