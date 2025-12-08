"""Test Layer 2 DwellingAddressInfo optional fields comprehensively.

This test validates ALL optional fields in DwellingAddressInfo to ensure
complete roundtrip and zero data loss for address information.

Pattern Source: tests/test_layer2_finalize_basic.py (TEMPLATE)

What This File Tests
====================
1. Building IDs (egid, ewid, household_id)
2. Free-form address lines (address_line1, address_line2)
3. Structured address fields (street, house_number, dwelling_number, locality)
4. Postal code extensions (swiss_zip_code_add_on, swiss_zip_code_id)
5. Moving date
6. Complete roundtrip with all fields populated
7. Minimal vs. maximal address configurations

DwellingAddressInfo Field Summary
==================================
REQUIRED fields:
- town: str (REQUIRED)
- swiss_zip_code: int (REQUIRED, 1000-9999)
- type_of_household: str (REQUIRED, "0"-"3")

OPTIONAL fields (tested here):
- egid: int (building ID, 1-999999999)
- ewid: int (dwelling ID, 1-999)
- household_id: str
- address_line1: str (max 60 chars)
- address_line2: str (max 60 chars)
- street: str (max 60 chars)
- house_number: str (max 12 chars)
- dwelling_number: str (max 10 chars)
- locality: str (max 40 chars)
- swiss_zip_code_add_on: str (max 2 chars, e.g., "01")
- swiss_zip_code_id: int (official postal code ID)
- moving_date: date

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures (municipalities, postal codes)
- Building IDs: Fictive (EGID/EWID not real)

Test Results
============
- Pending initial implementation
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


class TestLayer2DwellingAddressFields:
    """Test all DwellingAddressInfo optional fields with comprehensive coverage."""

    def test_building_ids_egid_ewid_household(self):
        """Test building identifiers: EGID, EWID, household_id.

        These are federal building/dwelling IDs used for official registration.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-BUILDING-IDS",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="BuildingTest",
            first_name="Person",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7561111222266",
            local_person_id="BUILD-001",
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

        # Test with building IDs
        dwelling = DwellingAddressInfo(
            egid=123456789,  # Federal building ID
            ewid=42,  # Federal dwelling ID
            household_id="HH-ZH-2023-001",  # Household ID
            street="Teststrasse",
            house_number="10",
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="2"  # Family household
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 1, 1),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify building IDs in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.dwelling_address.egid == 123456789
        assert main_res.dwelling_address.ewid == 42
        assert main_res.dwelling_address.household_id == "HH-ZH-2023-001"

        # Roundtrip to verify preservation
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "building_ids.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify building IDs preserved
            assert roundtrip_event_layer2.dwelling_address.egid == 123456789
            assert roundtrip_event_layer2.dwelling_address.ewid == 42
            assert roundtrip_event_layer2.dwelling_address.household_id == "HH-ZH-2023-001"

            # SUCCESS: Building IDs preserved! 🎉

    def test_free_form_address_lines(self):
        """Test free-form address lines (address_line1, address_line2).

        Used when structured address is not available or for special cases.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-FREEFORM",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="FreeformTest",
            first_name="Person",
            sex="2",
            date_of_birth=date(1985, 5, 10),
            vn="7562222333377",
            local_person_id="FREEFORM-001",
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

        # Test with free-form address lines (no structured address)
        dwelling = DwellingAddressInfo(
            address_line1="c/o Musterfirma AG",
            address_line2="Hinterhaus, 2. Stock rechts",
            town="Zürich",
            swiss_zip_code=8002,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 2, 1),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify address lines in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.dwelling_address.address.address_line1 == "c/o Musterfirma AG"
        assert main_res.dwelling_address.address.address_line2 == "Hinterhaus, 2. Stock rechts"

        # Roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "freeform.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify address lines preserved
            assert roundtrip_event_layer2.dwelling_address.address_line1 == "c/o Musterfirma AG"
            assert roundtrip_event_layer2.dwelling_address.address_line2 == "Hinterhaus, 2. Stock rechts"

            # SUCCESS: Free-form address lines preserved! 🎉

    def test_structured_address_with_dwelling_number_and_locality(self):
        """Test complete structured address: street, house_number, dwelling_number, locality.

        Structured address is preferred over free-form for data quality.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-STRUCTURED",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="StructuredTest",
            first_name="Person",
            sex="1",
            date_of_birth=date(1990, 8, 15),
            vn="7563333444488",
            local_person_id="STRUCT-001",
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

        # Test with complete structured address
        dwelling = DwellingAddressInfo(
            street="Musterstrasse",
            house_number="42a",
            dwelling_number="3B",  # Apartment number
            locality="Seefeld",  # District/locality
            town="Zürich",
            swiss_zip_code=8008,
            type_of_household="2"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 3, 1),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify structured address in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.dwelling_address.address.street == "Musterstrasse"
        assert main_res.dwelling_address.address.house_number == "42a"
        assert main_res.dwelling_address.address.dwelling_number == "3B"
        assert main_res.dwelling_address.address.locality == "Seefeld"

        # Roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "structured.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify structured address preserved
            assert roundtrip_event_layer2.dwelling_address.street == "Musterstrasse"
            assert roundtrip_event_layer2.dwelling_address.house_number == "42a"
            assert roundtrip_event_layer2.dwelling_address.dwelling_number == "3B"
            assert roundtrip_event_layer2.dwelling_address.locality == "Seefeld"

            # SUCCESS: Structured address preserved! 🎉

    def test_postal_code_extensions(self):
        """Test postal code extensions: swiss_zip_code_add_on, swiss_zip_code_id.

        These provide additional precision for Swiss postal codes.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-POSTAL",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="PostalTest",
            first_name="Person",
            sex="2",
            date_of_birth=date(1975, 12, 25),
            vn="7564444555599",
            local_person_id="POSTAL-001",
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

        # Test with postal code extensions
        dwelling = DwellingAddressInfo(
            street="Bahnhofstrasse",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8001,
            swiss_zip_code_add_on="01",  # Postal code extension
            swiss_zip_code_id=123456,  # Official postal code ID
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 4, 1),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify postal extensions in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.dwelling_address.address.swiss_zip_code_add_on == "01"
        assert main_res.dwelling_address.address.swiss_zip_code_id == 123456

        # Roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "postal.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify postal extensions preserved
            assert roundtrip_event_layer2.dwelling_address.swiss_zip_code_add_on == "01"
            assert roundtrip_event_layer2.dwelling_address.swiss_zip_code_id == 123456

            # SUCCESS: Postal code extensions preserved! 🎉

    def test_moving_date(self):
        """Test moving_date field.

        Records when the person moved into this dwelling.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-MOVING",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="MovingTest",
            first_name="Person",
            sex="1",
            date_of_birth=date(1982, 6, 10),
            vn="7565555666600",
            local_person_id="MOVING-001",
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

        # Test with moving date
        moving_date = date(2023, 5, 15)
        dwelling = DwellingAddressInfo(
            street="Moving Street",
            house_number="20",
            town="Zürich",
            swiss_zip_code=8003,
            type_of_household="2",
            moving_date=moving_date  # Date person moved in
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 5, 1),  # Municipality arrival
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify moving date in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.dwelling_address.moving_date == moving_date

        # Roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "moving.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify moving date preserved
            assert roundtrip_event_layer2.dwelling_address.moving_date == moving_date

            # SUCCESS: Moving date preserved! 🎉

    def test_complete_address_all_fields(self):
        """Test dwelling address with ALL optional fields populated.

        This is the maximum configuration test - every field has a value.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-MAXIMAL",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="MaximalTest",
            first_name="Person",
            sex="2",
            date_of_birth=date(1988, 11, 20),
            vn="7566666777711",
            local_person_id="MAXIMAL-001",
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

        # Test with ALL fields populated
        dwelling = DwellingAddressInfo(
            # Building IDs
            egid=987654321,
            ewid=999,
            household_id="HH-MAXIMAL-2023",
            # Free-form lines
            address_line1="Additional info line 1",
            address_line2="Additional info line 2",
            # Structured address
            street="Vollständigestrasse",
            house_number="99z",
            dwelling_number="10C",
            locality="Maximalquartier",
            # Required
            town="Zürich",
            swiss_zip_code=8050,
            # Postal extensions
            swiss_zip_code_add_on="99",
            swiss_zip_code_id=999999,
            # Country (default CH)
            country="CH",
            # Required
            type_of_household="3",  # Collective household
            # Moving date
            moving_date=date(2023, 6, 30)
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 6, 30),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Roundtrip with ALL fields
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "maximal.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify ALL fields preserved
            rt_addr = roundtrip_event_layer2.dwelling_address

            # Building IDs
            assert rt_addr.egid == 987654321
            assert rt_addr.ewid == 999
            assert rt_addr.household_id == "HH-MAXIMAL-2023"

            # Free-form lines
            assert rt_addr.address_line1 == "Additional info line 1"
            assert rt_addr.address_line2 == "Additional info line 2"

            # Structured address
            assert rt_addr.street == "Vollständigestrasse"
            assert rt_addr.house_number == "99z"
            assert rt_addr.dwelling_number == "10C"
            assert rt_addr.locality == "Maximalquartier"

            # Required fields
            assert rt_addr.town == "Zürich"
            assert rt_addr.swiss_zip_code == 8050

            # Postal extensions
            assert rt_addr.swiss_zip_code_add_on == "99"
            assert rt_addr.swiss_zip_code_id == 999999

            # Country
            assert rt_addr.country == "CH"

            # Household type
            assert rt_addr.type_of_household == "3"

            # Moving date
            assert rt_addr.moving_date == date(2023, 6, 30)

            # SUCCESS: ALL dwelling address fields preserved! 🎉
