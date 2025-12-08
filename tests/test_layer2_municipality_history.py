"""Test Layer 2 municipality history_id support.

This test validates the history_municipality_id field, which is used for
merged municipalities in Switzerland.

What This File Tests
====================
1. SecondaryResidenceInfo.history_id field
2. reporting_municipality_history_id field on residence events
3. Roundtrip preservation of history IDs

Background: Municipality Mergers in Switzerland
===============================================
Swiss municipalities occasionally merge. When this happens:
- The new municipality gets a new BFS number
- The old BFS number becomes a "history municipality ID"
- Both IDs must be tracked for historical records

Example: If municipalities A (BFS 1234) and B (BFS 5678) merge into C (BFS 9999):
- municipality_id = "9999" (current BFS)
- history_municipality_id = "1234" or "5678" (original BFS for historical tracking)

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures (Davos, St. Moritz)
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
    SecondaryResidenceInfo,
    PlaceType,
    ResidenceType,
)


class TestSecondaryResidenceInfoHistoryId:
    """Test SecondaryResidenceInfo.history_id field."""

    def test_history_id_optional(self):
        """Test that history_id is optional."""
        sec = SecondaryResidenceInfo(
            bfs="3851",
            name="Davos",
            canton="GR"
        )
        assert sec.history_id is None

    def test_history_id_set(self):
        """Test setting history_id for merged municipality."""
        sec = SecondaryResidenceInfo(
            bfs="3851",
            name="Davos",
            canton="GR",
            history_id="3850"  # Hypothetical old BFS
        )
        assert sec.history_id == "3850"


class TestSecondaryResidenceListHistoryIdRoundtrip:
    """Test history_id roundtrip in secondary_residence_list."""

    def test_secondary_residence_with_history_id_roundtrip(self):
        """Test that history_id in vacation homes is preserved through roundtrip."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-HISTORY",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="HistoryTest",
            first_name="Person",
            sex="1",
            date_of_birth=date(1975, 3, 10),
            vn="7561111222233",
            local_person_id="HIST-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="2",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        dwelling = DwellingAddressInfo(
            street="Main Street",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="1"
        )

        # Vacation homes with history_id
        vacation_homes = [
            SecondaryResidenceInfo(
                bfs="3851",
                name="Davos",
                canton="GR",
                history_id="3850"  # Historical BFS before merger
            ),
            SecondaryResidenceInfo(
                bfs="3787",
                name="St. Moritz",
                canton="GR"
                # No history_id - municipality never merged
            )
        ]

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 1, 1),
            dwelling_address=dwelling,
            secondary_residence_list=vacation_homes
        )

        delivery = original_event.finalize(config)

        # Verify Layer 1 has history_municipality_id
        main_res = delivery.event[0].has_main_residence
        assert main_res.secondary_residence is not None
        assert len(main_res.secondary_residence) == 2
        assert main_res.secondary_residence[0].history_municipality_id == "3850"
        assert main_res.secondary_residence[1].history_municipality_id is None

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "history_vacation.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify history_id preserved
            rt_list = roundtrip_event.secondary_residence_list
            assert rt_list is not None
            assert len(rt_list) == 2
            assert rt_list[0].bfs == "3851"
            assert rt_list[0].history_id == "3850"  # Preserved!
            assert rt_list[1].bfs == "3787"
            assert rt_list[1].history_id is None


class TestReportingMunicipalityHistoryIdRoundtrip:
    """Test reporting_municipality_history_id roundtrip."""

    def test_main_residence_with_history_id_roundtrip(self):
        """Test reporting_municipality_history_id for MAIN residence."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-REP-HIST",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="ReportingHistory",
            first_name="Test",
            sex="2",
            date_of_birth=date(1990, 6, 25),
            vn="7562222333344",
            local_person_id="REP-HIST-001",
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

        dwelling = DwellingAddressInfo(
            street="History Street",
            house_number="99",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            reporting_municipality_canton="GR",
            reporting_municipality_history_id="3850",  # Historical BFS
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        delivery = original_event.finalize(config)

        # Verify Layer 1 has history_municipality_id
        main_res = delivery.event[0].has_main_residence
        assert main_res.reporting_municipality.history_municipality_id == "3850"

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "rep_history_main.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify reporting_municipality_history_id preserved
            assert roundtrip_event.reporting_municipality_bfs == "3851"
            assert roundtrip_event.reporting_municipality_name == "Davos"
            assert roundtrip_event.reporting_municipality_history_id == "3850"

    def test_secondary_residence_with_history_id_roundtrip(self):
        """Test reporting_municipality_history_id for SECONDARY residence."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-SEC-HIST",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="SecondaryHistory",
            first_name="Test",
            sex="1",
            date_of_birth=date(1988, 11, 12),
            vn="7563333444455",
            local_person_id="SEC-HIST-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="2",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        from openmun_ech.ech0020.models import DestinationInfo
        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH"
        )

        dwelling = DwellingAddressInfo(
            street="Vacation Street",
            house_number="5",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            reporting_municipality_canton="GR",
            reporting_municipality_history_id="3850",  # Historical BFS
            arrival_date=date(2024, 3, 1),
            dwelling_address=dwelling,
            comes_from=comes_from,
            main_residence_bfs="261",
            main_residence_name="Zürich"
        )

        delivery = original_event.finalize(config)

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "rep_history_sec.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify reporting_municipality_history_id preserved
            assert roundtrip_event.reporting_municipality_history_id == "3850"

    def test_other_residence_with_history_id_roundtrip(self):
        """Test reporting_municipality_history_id for OTHER residence."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER-HIST",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="OtherHistory",
            first_name="Test",
            sex="2",
            date_of_birth=date(1995, 4, 8),
            vn="7564444555566",
            local_person_id="OTH-HIST-001",
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

        from openmun_ech.ech0020.models import DestinationInfo
        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH"
        )

        dwelling = DwellingAddressInfo(
            street="Other Street",
            house_number="10",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            reporting_municipality_canton="GR",
            reporting_municipality_history_id="3850",  # Historical BFS
            arrival_date=date(2024, 5, 1),
            dwelling_address=dwelling,
            comes_from=comes_from
        )

        delivery = original_event.finalize(config)

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "rep_history_other.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify reporting_municipality_history_id preserved
            assert roundtrip_event.reporting_municipality_history_id == "3850"
