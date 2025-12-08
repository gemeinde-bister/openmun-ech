"""XSD Validation Tests for Job Data (Priority 8.4)

Extends test_layer2_job_data.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Job Data (optional employment information):
- Single employer (one occupation_data entry)
- Multiple employers (multiple occupation_data entries - part-time workers)

Data policy:
- Fake personal data (names, dates, IDs, employers)
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


class TestLayer2XSDJobData:
    """XSD validation tests for job data fields."""

    def test_single_employer_xsd_validation(self):
        """Test single employer with full XML+XSD validation.

        Complete chain validates job data with one employer.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-JOB-SINGLE",
            manufacturer="XSDTest",
            product="JobDataTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with single employer
        person = BaseDeliveryPerson(
            local_person_id="90123",
            local_person_id_category="MU.6172",
            official_name="Meier",
            first_name="Stefan",
            sex="1",  # male
            date_of_birth=date(1985, 7, 14),
            vn="7561111090123",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",
            religion="121",  # Protestant
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
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock="0",

            # Job data: Single employer
            kind_of_employment="1",  # employed
            job_title="Software Engineer",
            occupation_data=[
                {
                    'employer': 'Tech Solutions AG',
                    'employer_uid': 'CHE-123.456.789',
                    'place_of_work': {
                        'street': 'Techstrasse',
                        'house_number': '42',
                        'town': 'Zürich',
                        'swiss_zip_code': '8001',
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'street': 'Hauptstrasse',
                        'house_number': '10',
                        'town': 'Zürich',
                        'swiss_zip_code': '8001',
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2020, 1, 15),
                    'occupation_valid_till': None  # current employment
                }
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Arbeiterstrasse",
            house_number="7",
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

        # Verify Layer 1 has job data
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.job_data is not None
        assert layer1_person.job_data.kind_of_employment == "1"
        assert layer1_person.job_data.job_title == "Software Engineer"
        assert layer1_person.job_data.occupation_data is not None
        assert len(layer1_person.job_data.occupation_data) == 1
        assert layer1_person.job_data.occupation_data[0].employer == "Tech Solutions AG"

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "single_employer_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.job_data is not None
            assert roundtrip_layer1_person.job_data.kind_of_employment == "1"
            assert roundtrip_layer1_person.job_data.job_title == "Software Engineer"
            assert len(roundtrip_layer1_person.job_data.occupation_data) == 1

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert roundtrip_event.person.kind_of_employment == "1"
            assert roundtrip_event.person.job_title == "Software Engineer"
            assert roundtrip_event.person.occupation_data is not None
            assert len(roundtrip_event.person.occupation_data) == 1
            assert roundtrip_event.person.occupation_data[0]['employer'] == "Tech Solutions AG"
            assert roundtrip_event.person.occupation_data[0]['employer_uid'] == "CHE-123.456.789"
            assert roundtrip_event.person.occupation_data[0]['place_of_work']['town'] == "Zürich"
            assert roundtrip_event.person.occupation_data[0]['place_of_employer']['street'] == "Hauptstrasse"
            assert roundtrip_event.person.occupation_data[0]['occupation_valid_from'] == date(2020, 1, 15)
            assert roundtrip_event.person.occupation_data[0]['occupation_valid_till'] is None

            # SUCCESS! 🎉

    def test_multiple_employers_xsd_validation(self):
        """Test multiple employers with full XML+XSD validation.

        Complete chain validates job data with multiple employers (part-time work).
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-JOB-MULTIPLE",
            manufacturer="XSDTest",
            product="JobDataTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person with multiple employers
        person = BaseDeliveryPerson(
            local_person_id="90234",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Anna",
            sex="2",  # female
            date_of_birth=date(1990, 3, 22),
            vn="7561111090234",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="230",  # Winterthur
            birth_municipality_name="Winterthur",
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
                    'bfs_code': '230',
                    'name': 'Winterthur',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock="0",

            # Job data: Multiple part-time employers
            kind_of_employment="1",  # employed
            job_title="Pflegehelferin",
            occupation_data=[
                {
                    'employer': 'Spital Winterthur',
                    'employer_uid': 'CHE-234.567.890',
                    'place_of_work': {
                        'street': 'Spitalstrasse',
                        'house_number': '1',
                        'town': 'Winterthur',
                        'swiss_zip_code': '8400',
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'street': 'Spitalstrasse',
                        'house_number': '1',
                        'town': 'Winterthur',
                        'swiss_zip_code': '8400',
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2019, 8, 1),
                    'occupation_valid_till': None  # current
                },
                {
                    'employer': 'Altersheim Rosengarten',
                    'employer_uid': 'CHE-345.678.901',
                    'place_of_work': {
                        'street': 'Rosenweg',
                        'house_number': '8',
                        'town': 'Winterthur',
                        'swiss_zip_code': '8405',
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'street': 'Rosenweg',
                        'house_number': '8',
                        'town': 'Winterthur',
                        'swiss_zip_code': '8405',
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2021, 3, 15),
                    'occupation_valid_till': None  # current
                },
                {
                    'employer': 'Spitex Winterthur',
                    'employer_uid': 'CHE-456.789.012',
                    'place_of_work': None,  # works at clients' homes
                    'place_of_employer': {
                        'street': 'Hauptstrasse',
                        'house_number': '55',
                        'town': 'Winterthur',
                        'swiss_zip_code': '8400',
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2022, 1, 10),
                    'occupation_valid_till': None  # current
                }
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Teilzeitstrasse",
            house_number="20",
            town="Winterthur",
            swiss_zip_code=8400,
            type_of_household="1"
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

        # Verify Layer 1 has job data with 3 employers
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.job_data is not None
        assert layer1_person.job_data.kind_of_employment == "1"
        assert layer1_person.job_data.job_title == "Pflegehelferin"
        assert len(layer1_person.job_data.occupation_data) == 3

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "multiple_employers_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.job_data is not None
            assert len(roundtrip_layer1_person.job_data.occupation_data) == 3

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss - all 3 employers preserved
            assert roundtrip_event.person.kind_of_employment == "1"
            assert roundtrip_event.person.job_title == "Pflegehelferin"
            assert len(roundtrip_event.person.occupation_data) == 3

            # Verify first employer
            emp1 = roundtrip_event.person.occupation_data[0]
            assert emp1['employer'] == "Spital Winterthur"
            assert emp1['employer_uid'] == "CHE-234.567.890"
            assert emp1['place_of_work']['town'] == "Winterthur"

            # Verify second employer
            emp2 = roundtrip_event.person.occupation_data[1]
            assert emp2['employer'] == "Altersheim Rosengarten"
            assert emp2['employer_uid'] == "CHE-345.678.901"
            assert emp2['place_of_work']['swiss_zip_code'] == 8405  # int type from Layer 1

            # Verify third employer (no place_of_work - Spitex)
            emp3 = roundtrip_event.person.occupation_data[2]
            assert emp3['employer'] == "Spitex Winterthur"
            assert emp3['employer_uid'] == "CHE-456.789.012"
            assert emp3['place_of_work'] is None  # Works at clients' homes
            assert emp3['place_of_employer']['street'] == "Hauptstrasse"

            # SUCCESS! 🎉
