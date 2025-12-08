"""Test Layer 2 finalize() pattern with minimal required fields.

TEMPLATE FILE FOR FUTURE TESTS
===============================
This file serves as the REFERENCE IMPLEMENTATION for all future Layer 2 tests.
When implementing new tests (secondary residence, foreign persons, optional fields,
etc.), use this file as a template and follow the same patterns.

What This File Tests
====================
1. Complete delivery construction via config-driven finalize() pattern
2. Config values properly used (no hardcoded data)
3. Message ID auto-generation and custom override
4. Complete roundtrip with zero data loss: Layer 2 → XML → Layer 2
5. Minimum required fields for Swiss person with main residence

Test Pattern Template
=====================
For future tests, follow this structure:

1. Create DeliveryConfig (fictive deployment data)
   - sender_id, manufacturer, product, product_version, test_delivery_flag

2. Create BaseDeliveryPerson (fictive personal + real BFS fixtures)
   - Required: official_name, first_name, sex, date_of_birth, vn, local_person_id
   - Required: religion, marital_status, nationality_status, data_lock
   - Required: places_of_origin OR residence_permit (CHOICE constraint)
   - Required: birth_place_type + birth place fields

3. Create DwellingAddressInfo (fictive address in real municipality)
   - Required: street, house_number, town, swiss_zip_code, type_of_household

4. Create BaseDeliveryEvent (combine person + residence)
   - Required: person, residence_type, arrival_date, dwelling_address
   - Required: reporting_municipality OR federal_register (CHOICE constraint)

5. Test: delivery = event.finalize(config)
   - Verify delivery structure
   - Verify header from config
   - Verify event converted to Layer 1
   - Export to XML and verify file

6. Roundtrip Test (zero data loss validation)
   - Layer 2 → Layer 1 → XML → Layer 1 → Layer 2
   - Assert all fields match original

Data Policy
===========
- Personal data: ALWAYS fictive/anonymized (names, dates, IDs, VNs)
- BFS data: ALWAYS real opendata fixtures (municipalities, cantons, BFS codes)
- Config data: ALWAYS fictive (sender IDs, product names, versions)

Minimum Required Fields (Discovered through Testing)
====================================================
These fields are REQUIRED (validation will fail without them):

BaseDeliveryPerson:
- official_name: str
- first_name: str
- sex: str ("1" or "2")
- date_of_birth: date
- vn: str (13 digits, starts with 756)
- local_person_id: str
- religion: str (BFS code, e.g., "111")
- marital_status: str (BFS code, e.g., "1")
- nationality_status: str ("1" for Swiss)
- data_lock: str ("0" for no lock)
- places_of_origin: List[dict] with {bfs_code, name, canton}
- birth_place_type: PlaceType (SWISS/FOREIGN/UNKNOWN)
- birth_municipality_bfs: str (if SWISS)
- birth_municipality_name: str (if SWISS)

BaseDeliveryEvent:
- person: BaseDeliveryPerson
- residence_type: ResidenceType (MAIN/SECONDARY/OTHER)
- reporting_municipality_bfs: str
- reporting_municipality_name: str
- arrival_date: date
- dwelling_address: DwellingAddressInfo

DwellingAddressInfo:
- street: str
- house_number: str
- town: str
- swiss_zip_code: int
- type_of_household: str

Test Results (2025-11-05)
==========================
- 5/5 tests passing
- Complete roundtrip validated (zero data loss)
- Phase 2.1-2.3 implementation chain proven functional

Related Documentation
======================
- docs/PHASE_2_IMPLEMENTATION_TRACKER.md: Implementation progress
- docs/PHASE_2_3_DELIVERY_CONSTRUCTION_DECISION.md: Design rationale
- docs/TWO_LAYER_ARCHITECTURE_ROADMAP.md: Overall roadmap
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from openmun_ech.ech0020.models import (
    BaseDeliveryPerson,
    BaseDeliveryEvent,
    DeliveryConfig,
    DwellingAddressInfo,
    PlaceType,
    ResidenceType,
)


class TestLayer2FinalizeBasic:
    """Test basic finalize() pattern with minimum required fields."""

    def test_minimal_swiss_person_base_delivery(self):
        """Test complete delivery construction with minimal Swiss person data.

        Validates:
        - Layer 2 event construction (minimum fields)
        - Config-driven finalize()
        - Complete ECH0020Delivery returned
        - XML export succeeds
        """
        # Step 1: Create minimal config (fictive deployment data)
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-001",
            manufacturer="TestManufacturer",
            product="TestProduct",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create minimal Swiss person (fictive personal data + real BFS fixtures)
        person = BaseDeliveryPerson(
            # Personal identification (fictive)
            official_name="Muster",
            first_name="Hans",
            sex="1",  # Male
            date_of_birth=date(1980, 1, 15),
            vn="7561234567897",  # Fictive VN (13 digits string, starts with 756)
            local_person_id="TEST-12345",
            local_person_id_category="MU.6172",

            # Required status fields (fictive)
            religion="111",  # Roman Catholic (real BFS code)
            marital_status="1",  # Single (real BFS code)
            nationality_status="1",  # Swiss citizen
            data_lock="0",  # No data lock

            # Swiss citizenship (real BFS fixture: Zürich)
            places_of_origin=[{
                "bfs_code": "261",
                "name": "Zürich",
                "canton": "ZH"
            }],

            # Birth place (real BFS fixture: Zürich)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        # Step 3: Create minimal dwelling address (fictive address in real municipality)
        dwelling = DwellingAddressInfo(
            street="Teststrasse",
            house_number="42",
            town="Zürich",
            swiss_zip_code=8000,
            type_of_household="1"  # Single person household
        )

        # Step 4: Create minimal event (person + residence)
        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            # Real BFS fixture: Reporting municipality Zürich
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 5: Finalize to complete delivery (THIS IS THE KEY TEST!)
        delivery = event.finalize(config)

        # Step 6: Verify delivery structure
        assert delivery is not None
        assert delivery.version == "3.0"
        assert delivery.delivery_header is not None
        assert delivery.delivery_header.header is not None
        assert delivery.event is not None
        assert len(delivery.event) == 1  # baseDelivery is a list

        # Step 7: Verify header was built from config
        header = delivery.delivery_header.header
        assert header.sender_id == "sedex://T1-TEST-001"
        assert header.test_delivery_flag is True
        assert header.sending_application.manufacturer == "TestManufacturer"
        assert header.sending_application.product == "TestProduct"
        assert header.sending_application.product_version == "1.0.0"
        assert header.message_id is not None  # Auto-generated UUID
        assert header.message_date is not None  # Auto-generated timestamp
        assert header.message_type == "http://www.ech.ch/xmlns/eCH-0020/3"

        # Step 8: Verify event was converted to Layer 1
        event_layer1 = delivery.event[0]
        assert event_layer1.base_delivery_person is not None
        assert event_layer1.has_main_residence is not None
        assert event_layer1.has_secondary_residence is None
        assert event_layer1.has_other_residence is None

        # Step 9: Verify person data preserved
        person_layer1 = event_layer1.base_delivery_person
        assert person_layer1.person_identification.official_name == "Muster"
        assert person_layer1.person_identification.first_name == "Hans"
        assert person_layer1.person_identification.vn == "7561234567897"

        # Step 10: Export to XML (final validation that everything works)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_delivery.xml"
            delivery.to_file(output_path)

            # Verify file was created and has content
            assert output_path.exists()
            xml_content = output_path.read_text()
            assert len(xml_content) > 1000  # Should be substantial XML
            assert '<?xml version' in xml_content
            assert 'eCH-0020' in xml_content
            assert 'Muster' in xml_content
            assert 'Hans' in xml_content

    def test_config_values_respected(self):
        """Test that config values are used, not hardcoded defaults."""
        # Custom config values
        config = DeliveryConfig(
            sender_id="sedex://CUSTOM-SENDER",
            manufacturer="CustomManufacturer",
            product="CustomProduct",
            product_version="2.5.3",
            test_delivery_flag=False  # Production flag
        )

        # Minimal person + event
        person = BaseDeliveryPerson(
            official_name="Test",
            first_name="Person",
            sex="2",
            date_of_birth=date(1990, 6, 1),
            vn="7569999888877",
            local_person_id="TEST-99999",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 6, 1),
            dwelling_address=DwellingAddressInfo(
                street="Street",
                house_number="1",
                town="Zürich",
                swiss_zip_code=8000,
                type_of_household="1"
            )
        )

        # Finalize with custom config
        delivery = event.finalize(config)
        header = delivery.delivery_header.header

        # Verify custom config values were used
        assert header.sender_id == "sedex://CUSTOM-SENDER"
        assert header.test_delivery_flag is False
        assert header.sending_application.manufacturer == "CustomManufacturer"
        assert header.sending_application.product == "CustomProduct"
        assert header.sending_application.product_version == "2.5.3"

    def test_message_id_auto_generated(self):
        """Test that message_id is auto-generated if not provided."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-001",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Test",
            first_name="Person",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7561111222233",
            local_person_id="TEST-1",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 1, 1),
            dwelling_address=DwellingAddressInfo(
                street="Test", house_number="1", town="Zürich",
                swiss_zip_code=8000, type_of_household="1"
            )
        )

        # Finalize WITHOUT providing message_id
        delivery = event.finalize(config)

        # Verify message_id was auto-generated (should be UUID format)
        message_id = delivery.delivery_header.header.message_id
        assert message_id is not None
        assert len(message_id) > 0
        # UUID format: 8-4-4-4-12 characters with hyphens
        assert message_id.count('-') == 4

    def test_custom_message_id(self):
        """Test that custom message_id can be provided."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-001",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Test",
            first_name="Person",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7561111222233",
            local_person_id="TEST-1",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 1, 1),
            dwelling_address=DwellingAddressInfo(
                street="Test", house_number="1", town="Zürich",
                swiss_zip_code=8000, type_of_household="1"
            )
        )

        # Finalize WITH custom message_id
        custom_id = "CUSTOM-MSG-12345"
        delivery = event.finalize(config, message_id=custom_id)

        # Verify custom message_id was used
        assert delivery.delivery_header.header.message_id == custom_id

    def test_complete_roundtrip_layer2_xml_layer2(self):
        """Test complete roundtrip: Layer 2 → XML → Layer 2 with zero data loss.

        Validates:
        - Layer 2 → Layer 1 (to_ech0020_event)
        - Layer 1 → XML (to_file)
        - XML → Layer 1 (from_xml)
        - Layer 1 → Layer 2 (from_ech0020_event)
        - Original Layer 2 == Roundtrip Layer 2 (zero data loss)
        """
        # Step 1: Create config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-ROUNDTRIP",
            manufacturer="RoundtripTest",
            product="TestProduct",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create ORIGINAL Layer 2 event (minimal data)
        original_person = BaseDeliveryPerson(
            official_name="Roundtrip",
            first_name="Test",
            sex="1",
            date_of_birth=date(1985, 3, 20),
            vn="7565555666677",
            local_person_id="ROUNDTRIP-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        original_event = BaseDeliveryEvent(
            person=original_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 3, 15),
            dwelling_address=DwellingAddressInfo(
                street="Roundtrip Street",
                house_number="99",
                town="Zürich",
                swiss_zip_code=8001,
                type_of_household="1"
            )
        )

        # Step 3: Finalize to complete delivery
        delivery = original_event.finalize(config)

        # Step 4: Export to XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "roundtrip.xml"
            delivery.to_file(xml_path)

            # Verify XML was created
            assert xml_path.exists()
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000
            assert 'Roundtrip' in xml_content
            assert 'Test' in xml_content

            # Step 5: Read back XML to Layer 1
            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Step 6: Verify Layer 1 structure is intact
            assert roundtrip_delivery is not None
            assert roundtrip_delivery.version == "3.0"
            assert len(roundtrip_delivery.event) == 1

            # Step 7: Convert Layer 1 back to Layer 2
            roundtrip_event_layer1 = roundtrip_delivery.event[0]
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_event_layer1)

            # Step 8: Verify roundtrip Layer 2 matches original Layer 2
            # Person data
            assert roundtrip_event_layer2.person.official_name == original_event.person.official_name
            assert roundtrip_event_layer2.person.first_name == original_event.person.first_name
            assert roundtrip_event_layer2.person.sex == original_event.person.sex
            assert roundtrip_event_layer2.person.date_of_birth == original_event.person.date_of_birth
            assert roundtrip_event_layer2.person.vn == original_event.person.vn
            assert roundtrip_event_layer2.person.local_person_id == original_event.person.local_person_id
            assert roundtrip_event_layer2.person.religion == original_event.person.religion
            assert roundtrip_event_layer2.person.marital_status == original_event.person.marital_status
            assert roundtrip_event_layer2.person.nationality_status == original_event.person.nationality_status
            assert roundtrip_event_layer2.person.data_lock == original_event.person.data_lock

            # Birth place
            assert roundtrip_event_layer2.person.birth_place_type == original_event.person.birth_place_type
            assert roundtrip_event_layer2.person.birth_municipality_bfs == original_event.person.birth_municipality_bfs
            assert roundtrip_event_layer2.person.birth_municipality_name == original_event.person.birth_municipality_name

            # Places of origin
            assert len(roundtrip_event_layer2.person.places_of_origin) == len(original_event.person.places_of_origin)
            roundtrip_origin = roundtrip_event_layer2.person.places_of_origin[0]
            original_origin = original_event.person.places_of_origin[0]
            assert roundtrip_origin['bfs_code'] == original_origin['bfs_code']
            assert roundtrip_origin['name'] == original_origin['name']
            assert roundtrip_origin['canton'] == original_origin['canton']

            # Event residence data
            assert roundtrip_event_layer2.residence_type == original_event.residence_type
            assert roundtrip_event_layer2.reporting_municipality_bfs == original_event.reporting_municipality_bfs
            assert roundtrip_event_layer2.reporting_municipality_name == original_event.reporting_municipality_name
            assert roundtrip_event_layer2.arrival_date == original_event.arrival_date

            # Dwelling address
            assert roundtrip_event_layer2.dwelling_address.street == original_event.dwelling_address.street
            assert roundtrip_event_layer2.dwelling_address.house_number == original_event.dwelling_address.house_number
            assert roundtrip_event_layer2.dwelling_address.town == original_event.dwelling_address.town
            assert roundtrip_event_layer2.dwelling_address.swiss_zip_code == original_event.dwelling_address.swiss_zip_code
            assert roundtrip_event_layer2.dwelling_address.type_of_household == original_event.dwelling_address.type_of_household

            # SUCCESS: Complete roundtrip with zero data loss! 🎉
