"""Test Layer 2 federal_register variant (CHOICE #10 alternative).

This test validates the federal_register field as an alternative to
reporting_municipality, testing CHOICE constraint #10.

Pattern Source: tests/test_layer2_finalize_basic.py (TEMPLATE)

What This File Tests
====================
1. federal_register as alternative to reporting_municipality (CHOICE #10)
2. All 3 federal register values (INFOSTAR, ORDIPRO, ZEMIS)
3. Complete roundtrip with federal_register
4. CHOICE validation (cannot have both)

CHOICE #10 Constraint
======================
Exactly ONE of:
- reporting_municipality_bfs + reporting_municipality_name
- federal_register

Federal Register Values (eCH-0011)
===================================
- "1" = INFOSTAR (civil status registry)
- "2" = ORDIPRO (criminal records registry)
- "3" = ZEMIS (immigration/asylum registry)

Use Cases
==========
- INFOSTAR: Civil status events (births, marriages, deaths)
- ORDIPRO: Criminal records system
- ZEMIS: Immigration and asylum system

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures where applicable
- federal_register: Valid values "1", "2", "3"

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


class TestLayer2FederalRegister:
    """Test federal_register as alternative to reporting_municipality."""

    def test_federal_register_infostar_complete_roundtrip(self):
        """Test MAIN residence with federal_register=INFOSTAR (1).

        Scenario: Civil status event registered in INFOSTAR.

        Validates:
        - federal_register field accepted
        - reporting_municipality fields NOT provided (CHOICE constraint)
        - INFOSTAR value (1) preserved in roundtrip
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-INFOSTAR",
            manufacturer="InfostarTest",
            product="TestProduct",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Infostar",
            first_name="Person",
            sex="1",
            date_of_birth=date(1982, 6, 15),
            vn="7561111222244",
            local_person_id="INFOSTAR-001",
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
            street="Civil Registry Street",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8000,
            type_of_household="1"
        )

        # KEY: Use federal_register instead of reporting_municipality
        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            # NO reporting_municipality_* fields (CHOICE constraint)
            federal_register="1",  # INFOSTAR
            arrival_date=date(2023, 6, 15),
            dwelling_address=dwelling
        )

        # Finalize
        delivery = original_event.finalize(config)
        assert delivery is not None
        assert len(delivery.event) == 1

        # Verify Layer 1 has federal_register
        event_layer1 = delivery.event[0]
        assert event_layer1.has_main_residence is not None
        main_res = event_layer1.has_main_residence
        assert main_res.federal_register is not None
        assert main_res.federal_register.value == "1"  # INFOSTAR enum value
        assert main_res.reporting_municipality is None  # NOT set (CHOICE)

        # Roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "infostar.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify federal_register preserved
            assert roundtrip_event_layer2.federal_register == "1"
            assert roundtrip_event_layer2.reporting_municipality_bfs is None
            assert roundtrip_event_layer2.reporting_municipality_name is None

            # SUCCESS: federal_register roundtrip works! 🎉

    def test_federal_register_ordipro(self):
        """Test federal_register=ORDIPRO (2) for criminal records."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-ORDIPRO",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Ordipro",
            first_name="Person",
            sex="2",
            date_of_birth=date(1975, 3, 20),
            vn="7562222333344",
            local_person_id="ORDIPRO-001",
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
            street="Records Street",
            house_number="2",
            town="Bern",
            swiss_zip_code=3000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            federal_register="2",  # ORDIPRO
            arrival_date=date(2023, 7, 1),
            dwelling_address=dwelling
        )

        delivery = event.finalize(config)
        assert delivery is not None

        # Verify ORDIPRO in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.federal_register is not None
        assert main_res.federal_register.value == "2"  # ORDIPRO
        assert main_res.reporting_municipality is None

    def test_federal_register_zemis(self):
        """Test federal_register=ZEMIS (3) for immigration/asylum."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-ZEMIS",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Zemis",
            first_name="Person",
            sex="1",
            date_of_birth=date(1988, 9, 10),
            vn="7563333444455",
            local_person_id="ZEMIS-001",
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
            street="Immigration Street",
            house_number="3",
            town="Geneva",
            swiss_zip_code=1200,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            federal_register="3",  # ZEMIS
            arrival_date=date(2023, 8, 1),
            dwelling_address=dwelling
        )

        delivery = event.finalize(config)
        assert delivery is not None

        # Verify ZEMIS in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.federal_register is not None
        assert main_res.federal_register.value == "3"  # ZEMIS
        assert main_res.reporting_municipality is None

    def test_federal_register_secondary_residence(self):
        """Test federal_register works for SECONDARY residence type too."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-SEC-FED",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Secondary",
            first_name="Federal",
            sex="2",
            date_of_birth=date(1980, 4, 5),
            vn="7564444555566",
            local_person_id="SEC-FED-001",
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
            municipality_bfs="351",
            municipality_name="Bern",
            canton_abbreviation="BE"
        )

        dwelling = DwellingAddressInfo(
            street="Vacation Street",
            house_number="10",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            federal_register="1",  # INFOSTAR
            arrival_date=date(2023, 9, 1),
            dwelling_address=dwelling,
            comes_from=comes_from,
            main_residence_bfs="261",
            main_residence_name="Zürich"
        )

        delivery = event.finalize(config)
        assert delivery is not None

        # Verify federal_register works for SECONDARY
        secondary_res = delivery.event[0].has_secondary_residence
        assert secondary_res is not None
        assert secondary_res.federal_register is not None
        assert secondary_res.federal_register.value == "1"
        assert secondary_res.reporting_municipality is None

    def test_federal_register_other_residence(self):
        """Test federal_register works for OTHER residence type too."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER-FED",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Other",
            first_name="Federal",
            sex="1",
            date_of_birth=date(1990, 11, 25),
            vn="7565555666677",
            local_person_id="OTHER-FED-001",
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
            municipality_bfs="6621",
            municipality_name="Genève",
            canton_abbreviation="GE"
        )

        dwelling = DwellingAddressInfo(
            street="Diplomatic Street",
            house_number="5",
            town="Basel",
            swiss_zip_code=4001,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            federal_register="3",  # ZEMIS
            arrival_date=date(2023, 10, 1),
            dwelling_address=dwelling,
            comes_from=comes_from
        )

        delivery = event.finalize(config)
        assert delivery is not None

        # Verify federal_register works for OTHER
        other_res = delivery.event[0].has_other_residence
        assert other_res is not None
        assert other_res.federal_register is not None
        assert other_res.federal_register.value == "3"
        assert other_res.reporting_municipality is None

    def test_choice_validation_both_provided_fails(self):
        """Test that providing BOTH reporting_municipality AND federal_register fails.

        CHOICE constraint #10 validation.
        """
        person = BaseDeliveryPerson(
            official_name="Invalid",
            first_name="Choice",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7566666777788",
            local_person_id="INVALID-001",
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
            street="Street",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8000,
            type_of_household="1"
        )

        # Try to provide BOTH (should fail validation)
        with pytest.raises(ValueError) as exc_info:
            BaseDeliveryEvent(
                person=person,
                residence_type=ResidenceType.MAIN,
                # BOTH provided (violates CHOICE)
                reporting_municipality_bfs="261",
                reporting_municipality_name="Zürich",
                federal_register="1",
                arrival_date=date(2023, 1, 1),
                dwelling_address=dwelling
            )

        # Verify error message mentions CHOICE constraint
        assert "CHOICE" in str(exc_info.value) or "both" in str(exc_info.value).lower()

    def test_choice_validation_neither_provided_fails(self):
        """Test that providing NEITHER reporting_municipality NOR federal_register fails.

        CHOICE constraint #10 validation.
        """
        person = BaseDeliveryPerson(
            official_name="Invalid",
            first_name="Missing",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7567777888899",
            local_person_id="INVALID-002",
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
            street="Street",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8000,
            type_of_household="1"
        )

        # Try to provide NEITHER (should fail validation)
        with pytest.raises(ValueError) as exc_info:
            BaseDeliveryEvent(
                person=person,
                residence_type=ResidenceType.MAIN,
                # NEITHER provided (violates CHOICE)
                arrival_date=date(2023, 1, 1),
                dwelling_address=dwelling
            )

        # Verify error message mentions CHOICE constraint
        assert "CHOICE" in str(exc_info.value) or "either" in str(exc_info.value).lower()
