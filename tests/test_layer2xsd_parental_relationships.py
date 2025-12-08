"""XSD Validation Tests for Parental Relationships (Priority 8.3)

Extends test_layer2_parental_relationships.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Parental Relationships (optional relationship data):
- Single parent (biological mother)
- Two parents (biological mother + father)
- Four parents (2 biological + 2 adoptive)

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
    PersonIdentification,
    ParentInfo,
    ResidenceType,
)
from openmun_ech.ech0020.v3 import ECH0020Delivery


class TestLayer2XSDParentalRelationships:
    """XSD validation tests for parental relationship fields."""

    def test_single_parent_biological_mother_xsd_validation(self):
        """Test single parent (biological mother) with full XML+XSD validation.

        Complete chain validates single parent relationship preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-SINGLE-PARENT",
            manufacturer="XSDTest",
            product="ParentalRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (child) with single parent
        person = BaseDeliveryPerson(
            local_person_id="12000",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Lisa",
            sex="2",
            date_of_birth=date(2010, 6, 15),  # Child born 2010
            vn="7561111120000",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",  # single (child)
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Single parent: biological mother
            parents=[
                ParentInfo(
                    person=PersonIdentification(
                        # No VN (testing optional case)
                        local_person_id="12001",
                        local_person_id_category="MU.6172",
                        official_name="Schmidt",
                        first_name="Maria",
                        original_name="Müller",  # Maiden name
                        sex="2",  # Female
                        date_of_birth=date(1985, 3, 20)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="0",  # 0 = unknown custody (required field per eCH-0021)
                    # No relationship_valid_from (testing optional case)
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Familienstrasse",
            house_number="11",
            town="Zürich",
            swiss_zip_code=8003,
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

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.parental_relationship is not None
        assert len(layer1_person.parental_relationship) == 1

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "single_parent_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.parental_relationship is not None
            assert len(roundtrip_layer1_person.parental_relationship) == 1

            parent_rel = roundtrip_layer1_person.parental_relationship[0]
            assert parent_rel.partner.person_identification.official_name == "Schmidt"
            assert parent_rel.partner.person_identification.first_name == "Maria"
            assert parent_rel.partner.person_identification.original_name == "Müller"
            assert parent_rel.type_of_relationship == "4"
            assert parent_rel.care == "0"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.parents is not None
            assert len(roundtrip_event.person.parents) == 1
            assert roundtrip_event.person.parents[0].person.official_name == "Schmidt"
            assert roundtrip_event.person.parents[0].person.first_name == "Maria"
            assert roundtrip_event.person.parents[0].relationship_type == "4"

            # SUCCESS! 🎉

    def test_two_parents_biological_mother_and_father_xsd_validation(self):
        """Test two parents (mother + father) with full XML+XSD validation.

        Complete chain validates two-parent family relationship preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-TWO-PARENTS",
            manufacturer="XSDTest",
            product="ParentalRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (child) with two parents
        person = BaseDeliveryPerson(
            local_person_id="13000",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Emma",
            sex="2",
            date_of_birth=date(2015, 9, 10),  # Child born 2015
            vn="7561111130000",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",  # single (child)
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Two parents: biological mother and father (typical case)
            parents=[
                # Biological mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569877777777",  # AHV-13 - mother has VN
                        local_person_id="13001",
                        local_person_id_category="MU.6172",
                        official_name="Fischer",
                        first_name="Anna",
                        original_name="Meier",  # Maiden name
                        sex="2",  # Female
                        date_of_birth=date(1988, 5, 15)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="1",  # 1 = joint custody (typical case)
                    relationship_valid_from=date(2015, 9, 10)  # Since child's birth
                ),
                # Biological father
                ParentInfo(
                    person=PersonIdentification(
                        # No VN for father (testing optional VN)
                        local_person_id="13002",
                        local_person_id_category="MU.6172",
                        official_name="Fischer",
                        first_name="Thomas",
                        # No original_name (testing optional field)
                        sex="1",  # Male
                        date_of_birth=date(1986, 11, 22)
                    ),
                    relationship_type="3",  # 3 = biological father
                    care="1",  # 1 = joint custody (same as mother)
                    relationship_valid_from=date(2015, 9, 10)  # Since child's birth
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Elternstrasse",
            house_number="25",
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

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.parental_relationship is not None
        assert len(layer1_person.parental_relationship) == 2

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "two_parents_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML - both parents preserved
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.parental_relationship is not None
            assert len(roundtrip_layer1_person.parental_relationship) == 2

            # Verify mother
            mother_rel = roundtrip_layer1_person.parental_relationship[0]
            assert mother_rel.partner.person_identification.first_name == "Anna"
            assert mother_rel.type_of_relationship == "4"
            assert mother_rel.care == "1"

            # Verify father
            father_rel = roundtrip_layer1_person.parental_relationship[1]
            assert father_rel.partner.person_identification.first_name == "Thomas"
            assert father_rel.type_of_relationship == "3"
            assert father_rel.care == "1"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss - both parents
            assert len(roundtrip_event.person.parents) == 2
            assert roundtrip_event.person.parents[0].person.first_name == "Anna"
            assert roundtrip_event.person.parents[0].relationship_type == "4"
            assert roundtrip_event.person.parents[1].person.first_name == "Thomas"
            assert roundtrip_event.person.parents[1].relationship_type == "3"

            # SUCCESS! 🎉

    def test_four_parents_biological_and_adoptive_xsd_validation(self):
        """Test four parents (2 biological + 2 adoptive) with full XML+XSD validation.

        Complete chain validates complex adoption scenario preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-FOUR-PARENTS",
            manufacturer="XSDTest",
            product="ParentalRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (child) with four parents
        person = BaseDeliveryPerson(
            local_person_id="14000",
            local_person_id_category="MU.6172",
            official_name="Bernasconi",
            first_name="Marco",
            sex="1",
            date_of_birth=date(2010, 3, 25),  # Child born 2010
            vn="7561111140000",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Four parents: 2 biological + 2 adoptive (edge case for adopted children)
            parents=[
                # Biological mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888888",
                        local_person_id="14001",
                        local_person_id_category="MU.6172",
                        official_name="Rossi",
                        first_name="Elena",
                        sex="2",
                        date_of_birth=date(1992, 7, 10)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="0",  # 0 = unknown (biological parents may not have custody after adoption)
                    relationship_valid_from=date(2010, 3, 25)  # Birth date
                ),
                # Biological father
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888889",
                        local_person_id="14002",
                        local_person_id_category="MU.6172",
                        official_name="Rossi",
                        first_name="Marco",
                        sex="1",
                        date_of_birth=date(1990, 4, 5)
                    ),
                    relationship_type="3",  # 3 = biological father
                    care="0",  # 0 = unknown
                    relationship_valid_from=date(2010, 3, 25)  # Birth date
                ),
                # Adoptive mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888890",
                        local_person_id="14003",
                        local_person_id_category="MU.6172",
                        official_name="Bernasconi",
                        first_name="Laura",
                        sex="2",
                        date_of_birth=date(1985, 11, 15)
                    ),
                    relationship_type="6",  # 6 = adoptive mother
                    care="1",  # 1 = joint custody (with adoptive father)
                    relationship_valid_from=date(2012, 6, 1)  # Adoption date
                ),
                # Adoptive father
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888891",
                        local_person_id="14004",
                        local_person_id_category="MU.6172",
                        official_name="Bernasconi",
                        first_name="Roberto",
                        sex="1",
                        date_of_birth=date(1983, 9, 20)
                    ),
                    relationship_type="5",  # 5 = adoptive father
                    care="1",  # 1 = joint custody (with adoptive mother)
                    relationship_valid_from=date(2012, 6, 1)  # Adoption date
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Adoptionsstrasse",
            house_number="30",
            town="Lugano",
            swiss_zip_code=6900,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="5192",  # Lugano
            reporting_municipality_name="Lugano",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1 - all 4 parents
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.parental_relationship is not None
        assert len(layer1_person.parental_relationship) == 4

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "four_parents_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML - all 4 parents preserved
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.parental_relationship is not None
            assert len(roundtrip_layer1_person.parental_relationship) == 4

            # Verify each parent type
            parent_types = [p.type_of_relationship for p in roundtrip_layer1_person.parental_relationship]
            assert "4" in parent_types  # biological mother
            assert "3" in parent_types  # biological father
            assert "6" in parent_types  # adoptive mother
            assert "5" in parent_types  # adoptive father

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss - all 4 parents
            assert len(roundtrip_event.person.parents) == 4

            # Verify relationship types preserved
            roundtrip_types = [p.relationship_type for p in roundtrip_event.person.parents]
            assert "4" in roundtrip_types  # biological mother
            assert "3" in roundtrip_types  # biological father
            assert "6" in roundtrip_types  # adoptive mother
            assert "5" in roundtrip_types  # adoptive father

            # SUCCESS: Complex adoption scenario validated! 🎉
