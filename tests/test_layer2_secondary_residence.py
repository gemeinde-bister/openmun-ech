"""Test Layer 2 SECONDARY residence type with finalize() pattern.

This test extends the basic template (test_layer2_finalize_basic.py) to validate
SECONDARY residence type with its additional required fields.

Pattern Source: tests/test_layer2_finalize_basic.py (TEMPLATE)

What This File Tests
====================
1. SECONDARY residence type (vacation home scenario)
2. Required fields for SECONDARY: comes_from, main_residence_bfs, main_residence_name
3. DestinationInfo with Swiss municipality (comes_from)
4. Complete roundtrip with zero data loss

Key Differences from MAIN Residence
====================================
- residence_type: ResidenceType.SECONDARY (not MAIN)
- comes_from: REQUIRED (person came from somewhere)
- main_residence_bfs: REQUIRED (person's primary residence BFS code)
- main_residence_name: REQUIRED (person's primary residence name)
- secondary_residence_list: FORBIDDEN (cannot have secondary when you ARE secondary)

Data Policy
===========
- Personal data: Fictive/anonymized (vacation home owner)
- BFS data: Real opendata fixtures
  - Secondary residence: Davos (BFS 3851, canton GR)
  - Main residence: Zürich (BFS 261, canton ZH)
  - Comes from: Bern (BFS 351, canton BE)
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
    DestinationInfo,
    PlaceType,
    ResidenceType,
)


class TestLayer2SecondaryResidence:
    """Test SECONDARY residence type with additional required fields."""

    def test_secondary_residence_complete_roundtrip(self):
        """Test SECONDARY residence with complete roundtrip validation.

        Scenario: Swiss person owns vacation home in Davos (secondary residence).
        Primary residence is in Zürich, previously lived in Bern.

        Validates:
        - SECONDARY residence type
        - comes_from required and present (from Bern)
        - main_residence required and present (Zürich)
        - Complete roundtrip: Layer 2 → XML → Layer 2 (zero data loss)
        """
        # Step 1: Create config (same pattern as basic test)
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-SECONDARY",
            manufacturer="SecondaryTest",
            product="TestProduct",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create person (fictive personal data + real BFS fixtures)
        person = BaseDeliveryPerson(
            official_name="Vacation",
            first_name="Owner",
            sex="2",  # Female
            date_of_birth=date(1975, 8, 10),
            vn="7567777888899",
            local_person_id="VACATION-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="2",  # Married
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        # Step 3: Create comes_from (person came from Bern)
        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="351",
            municipality_name="Bern",
            canton_abbreviation="BE"
        )

        # Step 4: Create dwelling address (vacation home in Davos)
        dwelling = DwellingAddressInfo(
            street="Promenade",
            house_number="15",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"  # Single household
        )

        # Step 5: Create SECONDARY residence event
        # KEY: comes_from REQUIRED, main_residence_* REQUIRED
        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.SECONDARY,  # SECONDARY!
            # Reporting municipality: Davos (vacation home location)
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            arrival_date=date(2023, 6, 1),  # Summer vacation home
            dwelling_address=dwelling,
            # REQUIRED for SECONDARY
            comes_from=comes_from,
            main_residence_bfs="261",  # Main residence in Zürich
            main_residence_name="Zürich"
        )

        # Step 6: Finalize to complete delivery
        delivery = original_event.finalize(config)

        # Step 7: Verify delivery structure
        assert delivery is not None
        assert delivery.version == "3.0"
        assert len(delivery.event) == 1

        # Step 8: Verify event type (should be SECONDARY, not MAIN)
        event_layer1 = delivery.event[0]
        assert event_layer1.has_main_residence is None  # NOT main
        assert event_layer1.has_secondary_residence is not None  # IS secondary
        assert event_layer1.has_other_residence is None  # NOT other

        # Step 9: Verify secondary residence fields
        secondary_res = event_layer1.has_secondary_residence
        assert secondary_res is not None

        # Verify reporting municipality (Davos)
        assert secondary_res.reporting_municipality is not None
        assert secondary_res.reporting_municipality.municipality_id == "3851"
        assert secondary_res.reporting_municipality.municipality_name == "Davos"

        # Verify comes_from (Bern)
        assert secondary_res.comes_from is not None
        assert secondary_res.comes_from.swiss_municipality is not None
        assert secondary_res.comes_from.swiss_municipality.swiss_municipality.municipality_id == "351"
        assert secondary_res.comes_from.swiss_municipality.swiss_municipality.municipality_name == "Bern"

        # Verify main_residence (Zürich)
        assert secondary_res.main_residence is not None
        assert secondary_res.main_residence.municipality_id == "261"
        assert secondary_res.main_residence.municipality_name == "Zürich"

        # Step 10: Export to XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "secondary_residence.xml"
            delivery.to_file(xml_path)

            assert xml_path.exists()
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000
            assert 'Vacation' in xml_content
            assert 'Davos' in xml_content
            assert 'hasSecondaryResidence' in xml_content  # Verify element name

            # Step 11: Read back XML to Layer 1
            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None
            assert len(roundtrip_delivery.event) == 1

            # Step 12: Convert Layer 1 back to Layer 2
            roundtrip_event_layer1 = roundtrip_delivery.event[0]
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_event_layer1)

            # Step 13: Verify roundtrip (ZERO DATA LOSS)
            # Person data
            assert roundtrip_event_layer2.person.official_name == original_event.person.official_name
            assert roundtrip_event_layer2.person.first_name == original_event.person.first_name
            assert roundtrip_event_layer2.person.vn == original_event.person.vn

            # Residence type
            assert roundtrip_event_layer2.residence_type == ResidenceType.SECONDARY

            # Reporting municipality (Davos)
            assert roundtrip_event_layer2.reporting_municipality_bfs == original_event.reporting_municipality_bfs
            assert roundtrip_event_layer2.reporting_municipality_name == original_event.reporting_municipality_name

            # comes_from (Bern)
            assert roundtrip_event_layer2.comes_from is not None
            assert roundtrip_event_layer2.comes_from.place_type == PlaceType.SWISS
            assert roundtrip_event_layer2.comes_from.municipality_bfs == "351"
            assert roundtrip_event_layer2.comes_from.municipality_name == "Bern"

            # main_residence (Zürich)
            assert roundtrip_event_layer2.main_residence_bfs == "261"
            assert roundtrip_event_layer2.main_residence_name == "Zürich"

            # Dwelling address (Davos vacation home)
            assert roundtrip_event_layer2.dwelling_address.street == "Promenade"
            assert roundtrip_event_layer2.dwelling_address.house_number == "15"
            assert roundtrip_event_layer2.dwelling_address.town == "Davos"
            assert roundtrip_event_layer2.dwelling_address.swiss_zip_code == 7270

            # SUCCESS: Complete SECONDARY residence roundtrip with zero data loss! 🎉

    def test_secondary_residence_comes_from_foreign(self):
        """Test SECONDARY residence with comes_from FOREIGN country.

        Scenario: Swiss person owns vacation home in Davos, previously abroad.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-SEC-FOREIGN",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="International",
            first_name="Traveler",
            sex="1",
            date_of_birth=date(1980, 5, 15),
            vn="7568888999900",
            local_person_id="INTL-001",
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

        # comes_from FOREIGN (from Austria)
        comes_from = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="AT",
            country_name_short="Österreich",
            town="Innsbruck"
        )

        dwelling = DwellingAddressInfo(
            street="Promenade",
            house_number="20",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            arrival_date=date(2023, 7, 1),
            dwelling_address=dwelling,
            comes_from=comes_from,  # From Austria
            main_residence_bfs="261",
            main_residence_name="Zürich"
        )

        # Finalize and verify
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify FOREIGN comes_from in Layer 1
        event_layer1 = delivery.event[0]
        assert event_layer1.has_secondary_residence is not None
        secondary_res = event_layer1.has_secondary_residence
        assert secondary_res.comes_from is not None
        assert secondary_res.comes_from.foreign_country is not None
        assert secondary_res.comes_from.foreign_country.country_id_iso2 == "AT"
        assert secondary_res.comes_from.foreign_town == "Innsbruck"

    def test_secondary_residence_comes_from_unknown(self):
        """Test SECONDARY residence with comes_from UNKNOWN.

        Scenario: Person's previous location unknown.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-SEC-UNKNOWN",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Mystery",
            first_name="Person",
            sex="2",
            date_of_birth=date(1990, 1, 1),
            vn="7569999000011",
            local_person_id="MYSTERY-001",
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

        # comes_from UNKNOWN
        comes_from = DestinationInfo(place_type=PlaceType.UNKNOWN)

        dwelling = DwellingAddressInfo(
            street="Street",
            house_number="1",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs="3851",
            reporting_municipality_name="Davos",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling,
            comes_from=comes_from,  # UNKNOWN
            main_residence_bfs="261",
            main_residence_name="Zürich"
        )

        # Finalize and verify
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify UNKNOWN comes_from in Layer 1
        event_layer1 = delivery.event[0]
        assert event_layer1.has_secondary_residence is not None
        secondary_res = event_layer1.has_secondary_residence
        assert secondary_res.comes_from is not None
        assert secondary_res.comes_from.unknown is not None
        assert secondary_res.comes_from.swiss_municipality is None
        assert secondary_res.comes_from.foreign_country is None
