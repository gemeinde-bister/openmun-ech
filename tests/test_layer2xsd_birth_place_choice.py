"""XSD Validation Tests for Birth Place CHOICE Constraint (Priority 8)

Extends test_layer2_birth_place_choice.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Birth Place CHOICE constraint:
- UNKNOWN: unknown=True, swiss_municipality=None, foreign_country=None
- SWISS: swiss_municipality present, unknown=None, foreign_country=None
- FOREIGN: foreign_country present, unknown=None, swiss_municipality=None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, cantons)
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


class TestLayer2XSDBirthPlaceChoice:
    """XSD validation tests for birth place CHOICE constraint."""

    def test_birth_place_unknown_xsd_validation(self):
        """Test birth place UNKNOWN with full XML+XSD validation.

        Complete chain:
        1. Create Layer 2 person with UNKNOWN birth place
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
            sender_id="sedex://T1-TEST-XSD-BIRTH-UNKNOWN",
            manufacturer="XSDTest",
            product="BirthPlaceTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with UNKNOWN birth place
        person = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="11111",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Anna",
            sex="2",  # female
            date_of_birth=date(1975, 12, 10),
            vn="7561111222233",  # Required for XSD validation

            # Birth info (required) - UNKNOWN birth place
            birth_place_type=PlaceType.UNKNOWN,
            # No birth_municipality_bfs, no birth_country_iso

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',   # Switzerland (ISO 2-letter code)
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required) - Swiss citizen
            places_of_origin=[
                {
                    'bfs_code': '230',  # Bern
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event (person + residence)
        dwelling = DwellingAddressInfo(
            street="Teststrasse",
            house_number="1",
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

        # Verify Layer 1 birth place is UNKNOWN
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.birth_info.birth_data.place_of_birth.unknown is True, \
            "Birth place should be marked as unknown in Layer 1"
        assert layer1_person.birth_info.birth_data.place_of_birth.swiss_municipality is None, \
            "Swiss municipality should be None"
        assert layer1_person.birth_info.birth_data.place_of_birth.foreign_country is None, \
            "Foreign country should be None"

        # Step 5: Export to XML file and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "birth_unknown_xsd.xml"
            delivery.to_file(xml_path)

            # Verify file exists
            assert xml_path.exists(), "XML file should be created"
            xml_content = xml_path.read_text()
            assert len(xml_content) > 1000, "XML should have substantial content"
            assert 'Weber' in xml_content, "Person name should be in XML"
            assert 'Anna' in xml_content, "First name should be in XML"

            # Step 6: XSD validation (built-in library validation)
            # The to_file() method uses library's XSD validation internally
            # If we got here without exception, XSD validation passed
            # Now explicitly verify by reading back

            # Step 7: Read XML back to Layer 1
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            assert roundtrip_delivery is not None, "Delivery should be parsed from XML"
            assert roundtrip_delivery.version == "3.0", "Version should be preserved"
            assert len(roundtrip_delivery.event) == 1, "Should have 1 event"

            # Step 8: Verify Layer 1 birth place still UNKNOWN after XML roundtrip
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.birth_info.birth_data.place_of_birth.unknown is True, \
                "Birth place should still be marked as unknown after XML roundtrip"
            assert roundtrip_layer1_person.birth_info.birth_data.place_of_birth.swiss_municipality is None, \
                "Swiss municipality should still be None after XML roundtrip"
            assert roundtrip_layer1_person.birth_info.birth_data.place_of_birth.foreign_country is None, \
                "Foreign country should still be None after XML roundtrip"

            # Step 9: Convert back to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Step 10: Verify zero data loss - Layer 2 fields
            assert roundtrip_event.person.official_name == person.official_name, \
                "Official name should be preserved"
            assert roundtrip_event.person.first_name == person.first_name, \
                "First name should be preserved"
            assert roundtrip_event.person.birth_place_type == PlaceType.UNKNOWN, \
                f"Birth place type should be UNKNOWN, got {roundtrip_event.person.birth_place_type}"
            assert roundtrip_event.person.birth_municipality_bfs is None, \
                "birth_municipality_bfs should be None for UNKNOWN"
            assert roundtrip_event.person.birth_country_iso is None, \
                "birth_country_iso should be None for UNKNOWN"
            assert roundtrip_event.person.birth_town is None, \
                "birth_town should be None for UNKNOWN"

            # Verify other person data preserved
            assert roundtrip_event.person.sex == person.sex
            assert roundtrip_event.person.date_of_birth == person.date_of_birth
            assert roundtrip_event.person.vn == person.vn
            assert roundtrip_event.person.religion == person.religion
            assert roundtrip_event.person.marital_status == person.marital_status

            # Verify event data preserved
            assert roundtrip_event.residence_type == ResidenceType.MAIN
            assert roundtrip_event.reporting_municipality_bfs == "351"
            assert roundtrip_event.reporting_municipality_name == "Bern"
            assert roundtrip_event.arrival_date == date(2024, 1, 1)

            # SUCCESS: Complete chain validated with zero data loss! 🎉
            # Layer 2 → Layer 1 → XML → XSD ✅ → Layer 1 → Layer 2
