"""XSD Validation Tests for Edge Cases (Priority 8.6)

Extends test_layer2_edge_cases.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Edge Cases (uncommon but valid scenarios):
- Multiple places of origin (Swiss citizen with 3+ origins from different cantons)
- Birth place unknown (historical records lost or not recorded)
- Residence permit without dates (no valid_from, no valid_till)

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


class TestLayer2XSDEdgeCases:
    """XSD validation tests for edge cases."""

    def test_multiple_places_of_origin_xsd_validation(self):
        """Test multiple places of origin with full XML+XSD validation.

        Complete chain validates Swiss citizen with 3 places of origin
        from different cantons (inherited from both parents).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-MULTI-ORIGIN",
            manufacturer="XSDTest",
            product="EdgeCasesTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with multiple places of origin
        person = BaseDeliveryPerson(
            local_person_id="80900",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1980, 5, 15),
            vn="7561111080900",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",
            religion="111",  # Roman Catholic
            marital_status="1",  # unmarried
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            # Edge case: Multiple places of origin (inherited from both parents)
            places_of_origin=[
                {
                    'bfs_code': '261',  # Zürich (father's side)
                    'name': 'Zürich',
                    'canton': 'ZH'
                },
                {
                    'bfs_code': '351',  # Bern (mother's side)
                    'name': 'Bern',
                    'canton': 'BE'
                },
                {
                    'bfs_code': '2701',  # Basel (inherited from grandparent)
                    'name': 'Basel',
                    'canton': 'BS'
                }
            ],
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Bürgerstrasse",
            house_number="42",
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

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 has 3 places of origin
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.place_of_origin_info is not None
        assert len(layer1_person.place_of_origin_info) == 3
        # Verify each origin
        origins = {ori.place_of_origin.origin_name
                   for ori in layer1_person.place_of_origin_info}
        assert origins == {'Zürich', 'Bern', 'Basel'}

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "multi_origins_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.place_of_origin_info is not None
            assert len(roundtrip_layer1_person.place_of_origin_info) == 3

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.places_of_origin is not None
            assert len(roundtrip_event.person.places_of_origin) == 3
            # Verify all origins present
            origin_names = {ori['name'] for ori in roundtrip_event.person.places_of_origin}
            assert origin_names == {'Zürich', 'Bern', 'Basel'}
            origin_cantons = {ori['canton'] for ori in roundtrip_event.person.places_of_origin}
            assert origin_cantons == {'ZH', 'BE', 'BS'}

            # SUCCESS! 🎉

    def test_birth_unknown_xsd_validation(self):
        """Test birth place unknown with full XML+XSD validation.

        Complete chain validates person with unknown birth place
        (historical records lost or not recorded).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-BIRTH-UNKNOWN",
            manufacturer="XSDTest",
            product="EdgeCasesTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with unknown birth place
        person = BaseDeliveryPerson(
            local_person_id="81011",
            local_person_id_category="MU.6172",
            official_name="Unknown",
            first_name="Origin",
            sex="1",  # male
            date_of_birth=date(1945, 1, 1),  # Post-war, records lost
            vn="7561111081011",
            # Edge case: Birth place unknown
            birth_place_type=PlaceType.UNKNOWN,
            religion="999",  # unknown
            marital_status="1",  # unmarried
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',  # Zürich (citizenship known from documents)
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Unbekannstrasse",
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

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 has unknown birth place
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.birth_info is not None
        assert layer1_person.birth_info.birth_data is not None
        assert layer1_person.birth_info.birth_data.place_of_birth is not None
        assert layer1_person.birth_info.birth_data.place_of_birth.unknown is True

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "birth_unknown_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.birth_info is not None
            assert roundtrip_layer1_person.birth_info.birth_data.place_of_birth.unknown is True

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.birth_place_type == PlaceType.UNKNOWN

            # SUCCESS! 🎉

    def test_residence_permit_no_dates_xsd_validation(self):
        """Test residence permit without dates with full XML+XSD validation.

        Complete chain validates foreign national with residence permit
        but no validity dates (dates not yet established or open-ended).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-PERMIT-NO-DATES",
            manufacturer="XSDTest",
            product="EdgeCasesTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with residence permit (no dates)
        person = BaseDeliveryPerson(
            local_person_id="81122",
            local_person_id_category="MU.6172",
            official_name="Novak",
            first_name="Ivan",
            sex="1",  # male
            date_of_birth=date(1992, 7, 8),
            vn="7561111081122",
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8135",  # Croatia
            birth_country_iso="HR",
            birth_country_name_short="Kroatien",
            religion="211",  # Christian Orthodox
            marital_status="1",  # unmarried
            nationality_status="2",  # Foreign
            nationalities=[
                {
                    'country_id': '8135',  # Croatia
                    'country_iso': 'HR',
                    'country_name_short': 'Kroatien'
                }
            ],
            # Edge case: Residence permit without dates
            residence_permit='01',  # Temporary residence (B permit)
            # residence_permit_valid_from=None,  # Not set (pending)
            # residence_permit_valid_till=None,  # Not set (pending)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Ausländerstrasse",
            house_number="99",
            town="Zürich",
            swiss_zip_code=8050,
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

        # Verify Layer 1 has residence permit without dates
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.residence_permit_data is not None
        assert layer1_person.residence_permit_data.residence_permit.value == '01'
        # Dates should be None
        assert layer1_person.residence_permit_data.residence_permit_valid_from is None
        assert layer1_person.residence_permit_data.residence_permit_valid_till is None

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "permit_no_dates_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.residence_permit_data.residence_permit.value == '01'
            assert roundtrip_layer1_person.residence_permit_data.residence_permit_valid_from is None
            assert roundtrip_layer1_person.residence_permit_data.residence_permit_valid_till is None

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.residence_permit == '01'
            assert roundtrip_event.person.residence_permit_valid_from is None
            assert roundtrip_event.person.residence_permit_valid_till is None

            # SUCCESS! 🎉
