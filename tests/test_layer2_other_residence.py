"""Test Layer 2 OTHER residence type with finalize() pattern.

This test extends the basic template (test_layer2_finalize_basic.py) to validate
OTHER residence type - the simplest residence type.

Pattern Source: tests/test_layer2_finalize_basic.py (TEMPLATE)

What This File Tests
====================
1. OTHER residence type (diplomatic, asylum, institutional, etc.)
2. Required fields for OTHER: comes_from (REQUIRED)
3. Forbidden fields for OTHER: main_residence_*, secondary_residence_list
4. Complete roundtrip with zero data loss

Key Differences from MAIN and SECONDARY Residence
==================================================
- residence_type: ResidenceType.OTHER
- comes_from: REQUIRED (person came from somewhere)
- main_residence_*: FORBIDDEN (not applicable for OTHER)
- secondary_residence_list: FORBIDDEN (not applicable for OTHER)
- Simplest residence type - no extensions

Use Cases for OTHER Residence
==============================
- Diplomatic personnel
- Asylum seekers
- Institutional residences (nursing homes, prisons)
- Temporary special cases

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures
  - Residence: Basel (BFS 2701, canton BS)
  - Comes from: Geneva (BFS 6621, canton GE)

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
    DestinationInfo,
    PlaceType,
    ResidenceType,
)


class TestLayer2OtherResidence:
    """Test OTHER residence type - the simplest residence type."""

    def test_other_residence_complete_roundtrip(self):
        """Test OTHER residence with complete roundtrip validation.

        Scenario: Diplomatic personnel registered in Basel, previously in Geneva.

        Validates:
        - OTHER residence type
        - comes_from required and present (from Geneva)
        - main_residence_* forbidden (should be None)
        - secondary_residence_list forbidden (should be None)
        - Complete roundtrip: Layer 2 → XML → Layer 2 (zero data loss)
        """
        # Step 1: Create config (same pattern as basic test)
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER",
            manufacturer="OtherTest",
            product="TestProduct",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create person (fictive personal data + real BFS fixtures)
        person = BaseDeliveryPerson(
            official_name="Diplomat",
            first_name="John",
            sex="1",  # Male
            date_of_birth=date(1970, 4, 25),
            vn="7566666777788",
            local_person_id="DIPLOMAT-001",
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

        # Step 3: Create comes_from (person came from Geneva)
        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="6621",
            municipality_name="Genève",
            canton_abbreviation="GE"
        )

        # Step 4: Create dwelling address (institutional residence in Basel)
        dwelling = DwellingAddressInfo(
            street="Ambassade Street",
            house_number="10",
            town="Basel",
            swiss_zip_code=4001,
            type_of_household="1"  # Single household
        )

        # Step 5: Create OTHER residence event
        # KEY: comes_from REQUIRED, main_residence_* FORBIDDEN, secondary_residence_list FORBIDDEN
        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,  # OTHER!
            # Reporting municipality: Basel (current residence)
            reporting_municipality_bfs="2701",
            reporting_municipality_name="Basel",
            arrival_date=date(2023, 9, 1),
            dwelling_address=dwelling,
            # REQUIRED for OTHER
            comes_from=comes_from,
            # FORBIDDEN for OTHER (should not be set)
            # main_residence_bfs: None (implicitly)
            # main_residence_name: None (implicitly)
            # secondary_residence_list: None (implicitly)
        )

        # Step 6: Finalize to complete delivery
        delivery = original_event.finalize(config)

        # Step 7: Verify delivery structure
        assert delivery is not None
        assert delivery.version == "3.0"
        assert len(delivery.event) == 1

        # Step 8: Verify event type (should be OTHER, not MAIN or SECONDARY)
        event_layer1 = delivery.event[0]
        assert event_layer1.has_main_residence is None  # NOT main
        assert event_layer1.has_secondary_residence is None  # NOT secondary
        assert event_layer1.has_other_residence is not None  # IS other

        # Step 9: Verify OTHER residence fields
        other_res = event_layer1.has_other_residence
        assert other_res is not None

        # Verify reporting municipality (Basel)
        assert other_res.reporting_municipality is not None
        assert other_res.reporting_municipality.municipality_id == "2701"
        assert other_res.reporting_municipality.municipality_name == "Basel"

        # Verify comes_from (Geneva)
        assert other_res.comes_from is not None
        assert other_res.comes_from.swiss_municipality is not None
        assert other_res.comes_from.swiss_municipality.swiss_municipality.municipality_id == "6621"
        assert other_res.comes_from.swiss_municipality.swiss_municipality.municipality_name == "Genève"

        # Verify NO main_residence extension (OTHER type has no main_residence field)
        # This is structural - ECH0020ReportingMunicipalityRestrictedBaseSecondary doesn't have main_residence

        # Step 10: Export to XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "other_residence.xml"
            delivery.to_file(xml_path)

            assert xml_path.exists()
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000
            assert 'Diplomat' in xml_content
            assert 'Basel' in xml_content
            assert 'hasOtherResidence' in xml_content  # Verify element name

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
            assert roundtrip_event_layer2.residence_type == ResidenceType.OTHER

            # Reporting municipality (Basel)
            assert roundtrip_event_layer2.reporting_municipality_bfs == original_event.reporting_municipality_bfs
            assert roundtrip_event_layer2.reporting_municipality_name == original_event.reporting_municipality_name

            # comes_from (Geneva)
            assert roundtrip_event_layer2.comes_from is not None
            assert roundtrip_event_layer2.comes_from.place_type == PlaceType.SWISS
            assert roundtrip_event_layer2.comes_from.municipality_bfs == "6621"
            assert roundtrip_event_layer2.comes_from.municipality_name == "Genève"

            # Verify extensions are None (OTHER type has no extensions)
            assert roundtrip_event_layer2.main_residence_bfs is None
            assert roundtrip_event_layer2.main_residence_name is None
            assert roundtrip_event_layer2.secondary_residence_list is None

            # Dwelling address (Basel institutional residence)
            assert roundtrip_event_layer2.dwelling_address.street == "Ambassade Street"
            assert roundtrip_event_layer2.dwelling_address.house_number == "10"
            assert roundtrip_event_layer2.dwelling_address.town == "Basel"
            assert roundtrip_event_layer2.dwelling_address.swiss_zip_code == 4001

            # SUCCESS: Complete OTHER residence roundtrip with zero data loss! 🎉

    def test_other_residence_comes_from_foreign(self):
        """Test OTHER residence with comes_from FOREIGN country.

        Scenario: Asylum seeker from foreign country registered in Basel.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER-FOREIGN",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Asylum",
            first_name="Seeker",
            sex="2",
            date_of_birth=date(1985, 7, 20),
            vn="7567777888800",
            local_person_id="ASYLUM-001",
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

        # comes_from FOREIGN (from Syria)
        comes_from = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="SY",
            country_name_short="Syrien",
            town="Damascus"
        )

        dwelling = DwellingAddressInfo(
            street="Asylum Center",
            house_number="5",
            town="Basel",
            swiss_zip_code=4002,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="2701",
            reporting_municipality_name="Basel",
            arrival_date=date(2023, 10, 15),
            dwelling_address=dwelling,
            comes_from=comes_from  # From Syria
        )

        # Finalize and verify
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify FOREIGN comes_from in Layer 1
        event_layer1 = delivery.event[0]
        assert event_layer1.has_other_residence is not None
        other_res = event_layer1.has_other_residence
        assert other_res.comes_from is not None
        assert other_res.comes_from.foreign_country is not None
        assert other_res.comes_from.foreign_country.country_id_iso2 == "SY"
        assert other_res.comes_from.foreign_town == "Damascus"

    def test_other_residence_comes_from_unknown(self):
        """Test OTHER residence with comes_from UNKNOWN.

        Scenario: Person with unknown previous location.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER-UNKNOWN",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Unknown",
            first_name="Origin",
            sex="1",
            date_of_birth=date(1992, 12, 5),
            vn="7568888999911",
            local_person_id="UNKNOWN-001",
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
            town="Basel",
            swiss_zip_code=4003,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="2701",
            reporting_municipality_name="Basel",
            arrival_date=date(2024, 1, 10),
            dwelling_address=dwelling,
            comes_from=comes_from  # UNKNOWN
        )

        # Finalize and verify
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify UNKNOWN comes_from in Layer 1
        event_layer1 = delivery.event[0]
        assert event_layer1.has_other_residence is not None
        other_res = event_layer1.has_other_residence
        assert other_res.comes_from is not None
        assert other_res.comes_from.unknown is not None
        assert other_res.comes_from.swiss_municipality is None
        assert other_res.comes_from.foreign_country is None

    def test_other_residence_with_optional_fields(self):
        """Test OTHER residence with optional fields: departure_date, goes_to.

        Scenario: Temporary diplomatic assignment with known end date.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-OTHER-OPTIONAL",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="Temporary",
            first_name="Diplomat",
            sex="2",
            date_of_birth=date(1978, 3, 12),
            vn="7569999000022",
            local_person_id="TEMP-DIPL-001",
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

        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="351",
            municipality_name="Bern",
            canton_abbreviation="BE"
        )

        goes_to = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="FR",
            country_name_short="Frankreich",
            town="Paris"
        )

        dwelling = DwellingAddressInfo(
            street="Embassy Row",
            house_number="25",
            town="Basel",
            swiss_zip_code=4001,
            type_of_household="2"  # Multi-person household
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="2701",
            reporting_municipality_name="Basel",
            arrival_date=date(2023, 1, 1),
            dwelling_address=dwelling,
            comes_from=comes_from,
            # OPTIONAL fields
            departure_date=date(2025, 12, 31),  # End of assignment
            goes_to=goes_to  # Next assignment in Paris
        )

        # Finalize
        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify optional fields in Layer 1
        event_layer1 = delivery.event[0]
        other_res = event_layer1.has_other_residence
        assert other_res.departure_date == date(2025, 12, 31)
        assert other_res.goes_to is not None
        assert other_res.goes_to.foreign_country is not None
        assert other_res.goes_to.foreign_country.country_id_iso2 == "FR"
        assert other_res.goes_to.foreign_town == "Paris"

        # Roundtrip to verify optional fields preserved
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "other_optional.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify optional fields roundtrip
            assert roundtrip_event_layer2.departure_date == date(2025, 12, 31)
            assert roundtrip_event_layer2.goes_to is not None
            assert roundtrip_event_layer2.goes_to.place_type == PlaceType.FOREIGN
            assert roundtrip_event_layer2.goes_to.country_iso == "FR"
            assert roundtrip_event_layer2.goes_to.country_name_short == "Frankreich"
            assert roundtrip_event_layer2.goes_to.town == "Paris"

            # SUCCESS: Optional fields preserved! 🎉
