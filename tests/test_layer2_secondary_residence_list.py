"""Test Layer 2 secondary_residence_list (0-n vacation homes for MAIN residence).

This test validates the secondary_residence_list field, which allows a person
with MAIN residence to register 0 or more vacation homes.

Pattern Source: tests/test_layer2_finalize_basic.py (TEMPLATE)

What This File Tests
====================
1. secondary_residence_list with 0 items (None)
2. secondary_residence_list with 1 vacation home
3. secondary_residence_list with multiple vacation homes (2-3 items)
4. Complete roundtrip preserves all vacation homes
5. Validation: Only allowed for MAIN residence (forbidden for SECONDARY, OTHER)

Feature Constraints
===================
- MAIN residence: secondary_residence_list ALLOWED (0-n vacation homes)
- SECONDARY residence: secondary_residence_list FORBIDDEN
- OTHER residence: secondary_residence_list FORBIDDEN

SecondaryResidenceInfo Structure
=================================
- bfs: str (BFS number, e.g., "3851" for Davos)
- name: str (municipality name, e.g., "Davos")
- canton: str (canton abbreviation, e.g., "GR")

Use Cases
==========
- Wealthy individuals with multiple vacation properties
- Business owners with secondary residences in different cantons
- Seasonal workers with temporary housing in mountain resorts

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures (Swiss municipalities)
  - Davos: BFS 3851, canton GR
  - St. Moritz: BFS 3787, canton GR
  - Verbier: BFS 6031, canton VS

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
    SecondaryResidenceInfo,
    PlaceType,
    ResidenceType,
)


class TestLayer2SecondaryResidenceList:
    """Test secondary_residence_list for MAIN residence (0-n vacation homes)."""

    def test_no_vacation_homes_none(self):
        """Test MAIN residence with no vacation homes (secondary_residence_list=None).

        This is the most common case - person has only main residence.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-NO-VAC",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="NoVacation",
            first_name="Person",
            sex="1",
            date_of_birth=date(1985, 5, 10),
            vn="7561111222255",
            local_person_id="NO-VAC-001",
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
            street="Main Street",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 1, 1),
            dwelling_address=dwelling
            # secondary_residence_list: None (implicitly, not provided)
        )

        delivery = event.finalize(config)
        assert delivery is not None

        # Verify no secondary residences in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.secondary_residence is None  # Layer 1 field name

    def test_one_vacation_home(self):
        """Test MAIN residence with 1 vacation home (Davos).

        Scenario: Person with main residence in Zürich, vacation home in Davos.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-ONE-VAC",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="OneVacation",
            first_name="Owner",
            sex="2",
            date_of_birth=date(1978, 8, 15),
            vn="7562222333355",
            local_person_id="ONE-VAC-001",
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
            street="Luxury Street",
            house_number="5",
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="2"
        )

        # 1 vacation home in Davos (real BFS: 3851)
        vacation_homes = [
            SecondaryResidenceInfo(
                bfs="3851",
                name="Davos",
                canton="GR"
            )
        ]

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 2, 1),
            dwelling_address=dwelling,
            secondary_residence_list=vacation_homes  # 1 vacation home
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify 1 secondary residence in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.secondary_residence is not None
        assert len(main_res.secondary_residence) == 1
        assert main_res.secondary_residence[0].municipality_id == "3851"
        assert main_res.secondary_residence[0].municipality_name == "Davos"

        # Roundtrip to verify preservation
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "one_vacation.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify vacation home preserved
            assert roundtrip_event_layer2.secondary_residence_list is not None
            assert len(roundtrip_event_layer2.secondary_residence_list) == 1
            assert roundtrip_event_layer2.secondary_residence_list[0].bfs == "3851"
            assert roundtrip_event_layer2.secondary_residence_list[0].name == "Davos"
            assert roundtrip_event_layer2.secondary_residence_list[0].canton == "GR"

            # SUCCESS: 1 vacation home preserved! 🎉

    def test_multiple_vacation_homes(self):
        """Test MAIN residence with multiple vacation homes (Davos + St. Moritz + Verbier).

        Scenario: Wealthy person with main residence in Zürich, 3 vacation homes.
        """
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-MULTI-VAC",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="MultiVacation",
            first_name="Wealthy",
            sex="1",
            date_of_birth=date(1965, 12, 5),
            vn="7563333444466",
            local_person_id="MULTI-VAC-001",
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
            street="Millionaire Row",
            house_number="10",
            town="Zürich",
            swiss_zip_code=8002,
            type_of_household="2"
        )

        # 3 vacation homes (real BFS codes)
        vacation_homes = [
            SecondaryResidenceInfo(
                bfs="3851",  # Davos
                name="Davos",
                canton="GR"
            ),
            SecondaryResidenceInfo(
                bfs="3787",  # St. Moritz
                name="St. Moritz",
                canton="GR"
            ),
            SecondaryResidenceInfo(
                bfs="6031",  # Bagnes (Verbier)
                name="Bagnes",
                canton="VS"
            )
        ]

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2023, 3, 1),
            dwelling_address=dwelling,
            secondary_residence_list=vacation_homes  # 3 vacation homes
        )

        delivery = original_event.finalize(config)
        assert delivery is not None

        # Verify 3 secondary residences in Layer 1
        main_res = delivery.event[0].has_main_residence
        assert main_res.secondary_residence is not None
        assert len(main_res.secondary_residence) == 3

        # Verify all 3 vacation homes
        davos = main_res.secondary_residence[0]
        assert davos.municipality_id == "3851"
        assert davos.municipality_name == "Davos"

        st_moritz = main_res.secondary_residence[1]
        assert st_moritz.municipality_id == "3787"
        assert st_moritz.municipality_name == "St. Moritz"

        bagnes = main_res.secondary_residence[2]
        assert bagnes.municipality_id == "6031"
        assert bagnes.municipality_name == "Bagnes"

        # Roundtrip to verify all preserved
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "multiple_vacation.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event_layer2 = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify all 3 vacation homes preserved
            assert roundtrip_event_layer2.secondary_residence_list is not None
            assert len(roundtrip_event_layer2.secondary_residence_list) == 3

            davos_rt = roundtrip_event_layer2.secondary_residence_list[0]
            assert davos_rt.bfs == "3851"
            assert davos_rt.name == "Davos"
            assert davos_rt.canton == "GR"

            st_moritz_rt = roundtrip_event_layer2.secondary_residence_list[1]
            assert st_moritz_rt.bfs == "3787"
            assert st_moritz_rt.name == "St. Moritz"
            assert st_moritz_rt.canton == "GR"

            bagnes_rt = roundtrip_event_layer2.secondary_residence_list[2]
            assert bagnes_rt.bfs == "6031"
            assert bagnes_rt.name == "Bagnes"
            assert bagnes_rt.canton == "VS"

            # SUCCESS: All 3 vacation homes preserved! 🎉

    def test_secondary_residence_list_forbidden_for_secondary_type(self):
        """Test that secondary_residence_list is forbidden for SECONDARY residence type.

        Validation: You can't have vacation homes when you ARE a vacation home.
        """
        person = BaseDeliveryPerson(
            official_name="Invalid",
            first_name="Secondary",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7564444555577",
            local_person_id="INVALID-SEC-001",
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
            street="Street",
            house_number="1",
            town="Davos",
            swiss_zip_code=7270,
            type_of_household="1"
        )

        # Try to add vacation homes to SECONDARY residence (should fail)
        vacation_homes = [
            SecondaryResidenceInfo(bfs="3851", name="Davos", canton="GR")
        ]

        with pytest.raises(ValueError) as exc_info:
            BaseDeliveryEvent(
                person=person,
                residence_type=ResidenceType.SECONDARY,
                reporting_municipality_bfs="3851",
                reporting_municipality_name="Davos",
                arrival_date=date(2023, 1, 1),
                dwelling_address=dwelling,
                comes_from=comes_from,
                main_residence_bfs="261",
                main_residence_name="Zürich",
                secondary_residence_list=vacation_homes  # FORBIDDEN for SECONDARY
            )

        # Verify error mentions forbidden or SECONDARY
        assert "secondary_residence_list" in str(exc_info.value).lower()

    def test_secondary_residence_list_forbidden_for_other_type(self):
        """Test that secondary_residence_list is forbidden for OTHER residence type.

        Validation: Diplomatic/asylum residences don't have vacation homes.
        """
        person = BaseDeliveryPerson(
            official_name="Invalid",
            first_name="Other",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            vn="7565555666688",
            local_person_id="INVALID-OTHER-001",
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
            street="Street",
            house_number="1",
            town="Basel",
            swiss_zip_code=4001,
            type_of_household="1"
        )

        # Try to add vacation homes to OTHER residence (should fail)
        vacation_homes = [
            SecondaryResidenceInfo(bfs="3851", name="Davos", canton="GR")
        ]

        with pytest.raises(ValueError) as exc_info:
            BaseDeliveryEvent(
                person=person,
                residence_type=ResidenceType.OTHER,
                reporting_municipality_bfs="2701",
                reporting_municipality_name="Basel",
                arrival_date=date(2023, 1, 1),
                dwelling_address=dwelling,
                comes_from=comes_from,
                secondary_residence_list=vacation_homes  # FORBIDDEN for OTHER
            )

        # Verify error mentions forbidden or secondary_residence_list
        assert "secondary_residence_list" in str(exc_info.value).lower()
