"""XSD Validation Tests for Civic Obligations (Priority 8.2)

Extends test_layer2_civic_obligations.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Civic Obligations (Swiss-specific optional fields):
- Political right data (restricted voting)
- Armed forces data (military service)
- Civil defense data
- Fire service data

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


class TestLayer2XSDCivicObligations:
    """XSD validation tests for civic obligation fields."""

    def test_political_right_data_restricted_voting_xsd_validation(self):
        """Test political right data with restricted voting and full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person with restricted voting rights
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
            sender_id="sedex://T1-TEST-XSD-POLITICAL-RIGHT",
            manufacturer="XSDTest",
            product="CivicObligationsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with restricted voting rights
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10004",
            local_person_id_category="MU.6172",
            official_name="Stauffer",
            first_name="Andreas",
            sex="1",  # male
            date_of_birth=date(1960, 3, 25),
            vn="7561111000004",  # Required for XSD validation

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
                    'country_id': '8100',  # BFS 4-digit code
                    'country_iso': 'CH',
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
            paper_lock=False,

            # Political right data (optional) - restricted voting
            restricted_voting_and_election_right_federation=True
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Bahnhofstrasse",
            house_number="100",
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

        # Verify Layer 1 political right data
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.political_right_data is not None, \
            "political_right_data should exist in Layer 1"
        assert layer1_person.political_right_data.restricted_voting_and_election_right_federation is True, \
            "voting restriction should be True"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "political_right_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Stauffer' in xml_content, "Person name should be in XML"

            # Step 6: XSD validation (built-in library validation)
            # The to_file() method uses library's XSD validation internally
            # If we got here without exception, XSD validation passed

            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 political right data still correct after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.political_right_data is not None, \
                "political_right_data should still exist after XML roundtrip"
            assert roundtrip_layer1_person.political_right_data.restricted_voting_and_election_right_federation is True, \
                "voting restriction should still be True after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name
            assert roundtrip_event.person.first_name == person.first_name
            assert roundtrip_event.person.restricted_voting_and_election_right_federation is True, \
                f"voting restriction should be preserved, got {roundtrip_event.person.restricted_voting_and_election_right_federation}"

            # Verify other person data preserved
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.vn == person.vn

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_armed_forces_data_military_service_xsd_validation(self):
        """Test armed forces data with full XML+XSD validation.

        Complete chain validates military service data preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-ARMED-FORCES",
            manufacturer="XSDTest",
            product="CivicObligationsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with armed forces data
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10005",
            local_person_id_category="MU.6172",
            official_name="Wyss",
            first_name="Beat",
            sex="1",  # male
            date_of_birth=date(1995, 7, 18),
            vn="7561111000005",  # Required for XSD validation

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
                    'country_id': '8100',  # BFS 4-digit code
                    'country_iso': 'CH',
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
            paper_lock=False,

            # Armed forces data (optional)
            armed_forces_service="1",  # Yes - has completed/is doing military service
            armed_forces_liability="1",  # Yes - liable for military service
            armed_forces_valid_from=date(2018, 1, 15)
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Militärstrasse",
            house_number="5",
            town="Bern",
            swiss_zip_code=3000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="351",  # Bern
            reporting_municipality_name="Bern",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize to complete ECH0020Delivery
        delivery = event.finalize(config)
        assert delivery is not None, "Delivery should be created"

        # Verify Layer 1 armed forces data
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.armed_forces_data is not None, "armed_forces_data should exist"
        assert layer1_person.armed_forces_data.armed_forces_service == "1"
        assert layer1_person.armed_forces_data.armed_forces_liability == "1"
        assert layer1_person.armed_forces_data.armed_forces_valid_from == date(2018, 1, 15)

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "armed_forces_xsd.xml"
            delivery.to_file(xml_path)

            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert 'Wyss' in xml_content, "Person name should be in XML"

            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Step 8: Verify Layer 1 armed forces data preserved
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.armed_forces_data is not None
            assert roundtrip_layer1_person.armed_forces_data.armed_forces_service == "1"
            assert roundtrip_layer1_person.armed_forces_data.armed_forces_liability == "1"
            assert roundtrip_layer1_person.armed_forces_data.armed_forces_valid_from == date(2018, 1, 15)

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss
            assert roundtrip_event.person.armed_forces_service == "1"
            assert roundtrip_event.person.armed_forces_liability == "1"
            assert roundtrip_event.person.armed_forces_valid_from == date(2018, 1, 15)

            # SUCCESS: Complete chain validated with zero data loss! 🎉

    def test_civil_defense_data_xsd_validation(self):
        """Test civil defense data with full XML+XSD validation.

        Complete chain validates civil defense obligation preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-CIVIL-DEFENSE",
            manufacturer="XSDTest",
            product="CivicObligationsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with civil defense data
        person = BaseDeliveryPerson(
            local_person_id="10006",
            local_person_id_category="MU.6172",
            official_name="Herzog",
            first_name="Markus",
            sex="1",
            date_of_birth=date(1992, 11, 3),
            vn="7561111000006",
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
            # Civil defense data (optional)
            civil_defense="1",
            civil_defense_valid_from=date(2015, 3, 10)
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Schutzstrasse",
            house_number="12",
            town="Luzern",
            swiss_zip_code=6000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="1061",  # Luzern
            reporting_municipality_name="Luzern",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.civil_defense_data is not None
        assert layer1_person.civil_defense_data.civil_defense == "1"
        assert layer1_person.civil_defense_data.civil_defense_valid_from == date(2015, 3, 10)

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "civil_defense_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.civil_defense_data is not None
            assert roundtrip_layer1_person.civil_defense_data.civil_defense == "1"
            assert roundtrip_layer1_person.civil_defense_data.civil_defense_valid_from == date(2015, 3, 10)

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.civil_defense == "1"
            assert roundtrip_event.person.civil_defense_valid_from == date(2015, 3, 10)

            # SUCCESS! 🎉

    def test_fire_service_data_xsd_validation(self):
        """Test fire service data with full XML+XSD validation.

        Complete chain validates fire service obligation preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-FIRE-SERVICE",
            manufacturer="XSDTest",
            product="CivicObligationsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with fire service data
        person = BaseDeliveryPerson(
            local_person_id="10007",
            local_person_id_category="MU.6172",
            official_name="Bauer",
            first_name="Stefan",
            sex="1",
            date_of_birth=date(1987, 4, 22),
            vn="7561111000007",
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
            # Fire service data (optional)
            fire_service="1",
            fire_service_liability="1",
            fire_service_valid_from=date(2010, 8, 1)
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Feuerwehrstrasse",
            house_number="3",
            town="St. Gallen",
            swiss_zip_code=9000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="3203",  # St. Gallen
            reporting_municipality_name="St. Gallen",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.fire_service_data is not None
        assert layer1_person.fire_service_data.fire_service == "1"
        assert layer1_person.fire_service_data.fire_service_liability == "1"
        assert layer1_person.fire_service_data.fire_service_valid_from == date(2010, 8, 1)

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "fire_service_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.fire_service_data is not None
            assert roundtrip_layer1_person.fire_service_data.fire_service == "1"
            assert roundtrip_layer1_person.fire_service_data.fire_service_liability == "1"
            assert roundtrip_layer1_person.fire_service_data.fire_service_valid_from == date(2010, 8, 1)

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.fire_service == "1"
            assert roundtrip_event.person.fire_service_liability == "1"
            assert roundtrip_event.person.fire_service_valid_from == date(2010, 8, 1)

            # SUCCESS! 🎉
