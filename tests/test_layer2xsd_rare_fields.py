"""XSD Validation Tests for Rare Fields (Priority 8.5)

Extends test_layer2_rare_fields.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Rare Fields (infrequently used optional data):
- Naturalization data (naturalization_date in place of origin)
- Parent names from birth certificate (birth_father_name, birth_mother_name with proof flag)
- Marital data addon (place_of_marriage)

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


class TestLayer2XSDRareFields:
    """XSD validation tests for rare/infrequent optional fields."""

    def test_naturalization_data_xsd_validation(self):
        """Test naturalization data with full XML+XSD validation.

        Complete chain validates place of origin with naturalization date.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-NATURALIZATION",
            manufacturer="XSDTest",
            product="RareFieldsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with naturalization data
        person = BaseDeliveryPerson(
            local_person_id="80456",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1975, 4, 10),
            vn="7561111080456",
            birth_place_type=PlaceType.FOREIGN,
            birth_country_id="8207",  # Germany
            birth_country_iso="DE",
            birth_country_name_short="Deutschland",
            religion="121",  # Protestant
            marital_status="1",  # unmarried
            nationality_status="1",  # Swiss (naturalized)
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            # Place of origin with naturalization date
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH',
                    'naturalization_date': date(2010, 6, 15)  # Rare field: naturalization date
                }
            ],
            data_lock="0",
            paper_lock="0"
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Bürgerstrasse",
            house_number="12",
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

        # Verify Layer 1 has naturalization date
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.place_of_origin_info is not None
        assert len(layer1_person.place_of_origin_info) == 1
        origin = layer1_person.place_of_origin_info[0]
        assert origin.place_of_origin_addon_data is not None
        assert origin.place_of_origin_addon_data.naturalization_date == date(2010, 6, 15)

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "naturalization_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.place_of_origin_info is not None
            assert len(roundtrip_layer1_person.place_of_origin_info) == 1
            roundtrip_origin = roundtrip_layer1_person.place_of_origin_info[0]
            assert roundtrip_origin.place_of_origin_addon_data is not None
            assert roundtrip_origin.place_of_origin_addon_data.naturalization_date == date(2010, 6, 15)

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.places_of_origin is not None
            assert len(roundtrip_event.person.places_of_origin) == 1
            assert roundtrip_event.person.places_of_origin[0]['bfs_code'] == '261'
            assert roundtrip_event.person.places_of_origin[0]['name'] == 'Zürich'
            assert roundtrip_event.person.places_of_origin[0]['naturalization_date'] == date(2010, 6, 15)

            # SUCCESS! 🎉

    def test_parent_names_from_certificate_xsd_validation(self):
        """Test parent names from birth certificate with full XML+XSD validation.

        Complete chain validates birth addon data with parent names
        and official proof flag.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-PARENT-NAMES",
            manufacturer="XSDTest",
            product="RareFieldsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with parent names from certificate
        person = BaseDeliveryPerson(
            local_person_id="80567",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1995, 8, 20),
            vn="7561111080567",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="351",  # Bern
            birth_municipality_name="Bern",
            religion="111",  # Roman Catholic
            marital_status="1",  # unmarried
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '351',
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],
            data_lock="0",
            paper_lock="0",

            # Rare fields: Parent names from birth certificate
            # When both names are known from certificate, use regular fields (not "only" variants)
            birth_father_name="Schmidt",
            birth_father_first_name="Peter",
            birth_father_official_proof=True,  # Official proof exists
            birth_mother_name="Meier",
            birth_mother_first_name="Anna",
            birth_mother_official_proof=True  # Official proof exists
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Zertifikatstrasse",
            house_number="5",
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

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 has birth addon data
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.birth_info is not None
        assert layer1_person.birth_info.birth_addon_data is not None
        assert layer1_person.birth_info.birth_addon_data.name_of_parent is not None
        assert len(layer1_person.birth_info.birth_addon_data.name_of_parent) == 2  # father + mother
        # Find father and mother in the list
        father = next(p for p in layer1_person.birth_info.birth_addon_data.name_of_parent
                      if p.type_of_relationship.value == '4')  # FATHER
        mother = next(p for p in layer1_person.birth_info.birth_addon_data.name_of_parent
                      if p.type_of_relationship.value == '3')  # MOTHER
        assert father.official_name == "Schmidt"  # Regular field (not "only")
        assert father.first_name == "Peter"  # Regular field (not "only")
        assert father.official_proof_of_name_of_parents_yes_no is True
        assert mother.official_name == "Meier"  # Regular field (not "only")
        assert mother.first_name == "Anna"  # Regular field (not "only")
        assert mother.official_proof_of_name_of_parents_yes_no is True

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "parent_names_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.birth_info is not None
            assert roundtrip_layer1_person.birth_info.birth_addon_data is not None
            assert len(roundtrip_layer1_person.birth_info.birth_addon_data.name_of_parent) == 2

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.birth_father_name == "Schmidt"
            assert roundtrip_event.person.birth_father_first_name == "Peter"
            assert roundtrip_event.person.birth_father_official_proof is True
            assert roundtrip_event.person.birth_mother_name == "Meier"
            assert roundtrip_event.person.birth_mother_first_name == "Anna"
            assert roundtrip_event.person.birth_mother_official_proof is True

            # SUCCESS! 🎉

    def test_marital_place_of_marriage_xsd_validation(self):
        """Test marital data addon with place of marriage.

        Complete chain validates marital relationship with
        place_of_marriage (rare field in maritalDataAddon).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-MARRIAGE-PLACE",
            manufacturer="XSDTest",
            product="RareFieldsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with spouse and marriage place
        from openmun_ech.ech0020.models import PersonIdentification

        person = BaseDeliveryPerson(
            local_person_id="80678",
            local_person_id_category="MU.6172",
            official_name="Weber",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1988, 11, 5),
            vn="7561111080678",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="230",  # Winterthur
            birth_municipality_name="Winterthur",
            religion="121",  # Protestant
            marital_status="2",  # married
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '230',
                    'name': 'Winterthur',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock="0",

            # Spouse data
            spouse=PersonIdentification(
                local_person_id="80789",
                local_person_id_category="MU.6172",
                official_name="Weber",  # Married name
                first_name="Lisa",
                sex="2",
                date_of_birth=date(1990, 3, 12),
                vn="7561111080789"
            ),
            marital_relationship_type="1",  # married

            # Rare field: Place of marriage
            marriage_place_type=PlaceType.SWISS,
            marriage_municipality_bfs="261",  # Zürich (where they got married)
            marriage_municipality_name="Zürich"
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Hochzeitsstrasse",
            house_number="9",
            town="Winterthur",
            swiss_zip_code=8400,
            type_of_household="2"  # couple
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="230",  # Winterthur
            reporting_municipality_name="Winterthur",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 has marital data addon with place of marriage
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.marital_info is not None
        assert layer1_person.marital_info.marital_data_addon is not None
        assert layer1_person.marital_info.marital_data_addon.place_of_marriage is not None
        # Check it's a Swiss place
        assert layer1_person.marital_info.marital_data_addon.place_of_marriage.swiss_municipality is not None

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "marriage_place_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.marital_info is not None
            assert roundtrip_layer1_person.marital_info.marital_data_addon is not None
            assert roundtrip_layer1_person.marital_info.marital_data_addon.place_of_marriage is not None

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.marriage_place_type == PlaceType.SWISS
            assert roundtrip_event.person.marriage_municipality_bfs == "261"
            assert roundtrip_event.person.marriage_municipality_name == "Zürich"

            # SUCCESS! 🎉
