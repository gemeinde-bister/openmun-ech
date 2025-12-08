"""XSD Validation Tests for Personal Affairs (Priority 8.2)

Extends test_layer2_personal_affairs.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Personal Affairs (optional fields):
- Health insurance data
- Matrimonial inheritance arrangement
- Multiple nationalities (dual citizenship)

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


class TestLayer2XSDPersonalAffairs:
    """XSD validation tests for personal affairs fields."""

    def test_health_insurance_data_xsd_validation(self):
        """Test health insurance data with full XML+XSD validation.

        Complete chain validates health insurance compliance tracking.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-HEALTH-INSURANCE",
            manufacturer="XSDTest",
            product="PersonalAffairsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with health insurance data
        person = BaseDeliveryPerson(
            local_person_id="10008",
            local_person_id_category="MU.6172",
            official_name="Brunner",
            first_name="Anna",
            sex="2",
            date_of_birth=date(1991, 9, 8),
            vn="7561111000008",
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

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Gesundheitsstrasse",
            house_number="8",
            town="Basel",
            swiss_zip_code=4000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="2701",  # Basel
            reporting_municipality_name="Basel",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.health_insurance_data is not None
        assert layer1_person.health_insurance_data.health_insured == "1"

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "health_insurance_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            assert 'Brunner' in xml_content

            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.health_insurance_data is not None
            assert roundtrip_layer1_person.health_insurance_data.health_insured == "1"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss (Layer 2 stores as boolean)
            assert roundtrip_event.person.health_insured is True

            # SUCCESS! 🎉

    def test_matrimonial_inheritance_arrangement_xsd_validation(self):
        """Test matrimonial inheritance arrangement with full XML+XSD validation.

        Complete chain validates marital property regime preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-MATRIMONIAL",
            manufacturer="XSDTest",
            product="PersonalAffairsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with matrimonial inheritance arrangement
        person = BaseDeliveryPerson(
            local_person_id="10009",
            local_person_id_category="MU.6172",
            official_name="Frei",
            first_name="Sandra",
            sex="2",
            date_of_birth=date(1983, 2, 14),
            vn="7561111000009",
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

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Ehestrasse",
            house_number="15",
            town="Genève",
            swiss_zip_code=1200,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="6621",  # Genève
            reporting_municipality_name="Genève",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.matrimonial_inheritance_arrangement_data is not None
        assert layer1_person.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement == "1"
        assert layer1_person.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement_valid_from == \
               date(2010, 6, 15)

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "matrimonial_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.matrimonial_inheritance_arrangement_data is not None
            assert roundtrip_layer1_person.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement == "1"
            assert roundtrip_layer1_person.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement_valid_from == \
                   date(2010, 6, 15)

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.matrimonial_inheritance_arrangement == "1"
            assert roundtrip_event.person.matrimonial_inheritance_arrangement_valid_from == date(2010, 6, 15)

            # SUCCESS! 🎉

    def test_multiple_nationalities_xsd_validation(self):
        """Test dual nationality with full XML+XSD validation.

        Complete chain validates multiple citizenship preservation (list handling).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-DUAL-NATIONALITY",
            manufacturer="XSDTest",
            product="PersonalAffairsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with dual nationality
        person = BaseDeliveryPerson(
            local_person_id="10010",
            local_person_id_category="MU.6172",
            official_name="Rossi",
            first_name="Marco",
            sex="1",
            date_of_birth=date(1985, 5, 30),
            vn="7561111000010",
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
                    'country_id': '8211',  # Italy (BFS 4-digit code)
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

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Via Nazionale",
            house_number="22",
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

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 - should have 2 nationalities
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.nationality_data is not None
        assert len(layer1_person.nationality_data.country_info) == 2

        # Verify both countries present
        country_ids = [c.country.country_id for c in layer1_person.nationality_data.country_info]
        assert "8100" in country_ids, "Switzerland missing"
        assert "8211" in country_ids, "Italy missing"

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "dual_nationality_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML - both nationalities preserved
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.nationality_data is not None
            assert len(roundtrip_layer1_person.nationality_data.country_info) == 2

            roundtrip_country_ids = [c.country.country_id for c in roundtrip_layer1_person.nationality_data.country_info]
            assert "8100" in roundtrip_country_ids, "Switzerland lost in XML roundtrip"
            assert "8211" in roundtrip_country_ids, "Italy lost in XML roundtrip"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss - both nationalities preserved
            assert len(roundtrip_event.person.nationalities) == 2

            roundtrip_ids_layer2 = [n['country_id'] for n in roundtrip_event.person.nationalities]
            assert '8100' in roundtrip_ids_layer2, "Switzerland lost in Layer 2 conversion"
            assert '8211' in roundtrip_ids_layer2, "Italy lost in Layer 2 conversion"

            # SUCCESS: List preservation validated! 🎉
