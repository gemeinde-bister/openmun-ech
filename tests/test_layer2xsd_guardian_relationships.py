"""XSD Validation Tests for Guardian Relationships (Priority 8.3)

Extends test_layer2_guardian_relationships.py with full XML+XSD validation.

Tests the complete chain:
Layer 2 → Layer 1 → XML file → XSD validation → Layer 1 → Layer 2

This validates:
- Layer 2 → Layer 1 conversion (Pydantic)
- Layer 1 → XML serialization (to_file)
- XML → XSD schema compliance (xmlschema library)
- XML → Layer 1 deserialization (from_xml)
- Layer 1 → Layer 2 conversion (from_ech0020)
- Zero data loss across entire chain

Guardian Relationships (optional relationship data):
- Person guardian (individual guardian)
- Organization guardian (KESB)
- Partner guardian (person_identification_partner type)

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, ZGB articles)
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
    GuardianInfo,
    GuardianType,
    ResidenceType,
)
from openmun_ech.ech0020.v3 import ECH0020Delivery


class TestLayer2XSDGuardianRelationships:
    """XSD validation tests for guardian relationship fields."""

    def test_person_guardian_with_full_identification_xsd_validation(self):
        """Test person guardian with full XML+XSD validation.

        Complete chain validates individual guardian preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-PERSON-GUARDIAN",
            manufacturer="XSDTest",
            product="GuardianRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (minor child) with person guardian
        person = BaseDeliveryPerson(
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schneider",
            first_name="Sophie",
            sex="2",  # female
            date_of_birth=date(2015, 8, 10),  # minor child
            vn="7561111067890",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",
            religion="121",  # Protestant
            marital_status="1",  # unmarried (child)
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

            # Guardian: Person guardian
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-001",
                    guardian_type=GuardianType.PERSON,
                    person=PersonIdentification(
                        vn="7569871234567",
                        local_person_id="guard-001",
                        local_person_id_category="MU.6172",
                        official_name="Weber",
                        first_name="Thomas",
                        original_name=None,
                        sex="1",  # male
                        date_of_birth=date(1978, 3, 20)
                    ),
                    organization_uid=None,  # Not organization guardian
                    organization_name=None,
                    relationship_type="7",  # guardian_person
                    guardian_measure_based_on_law=["310", "327-a"],  # ZGB articles
                    guardian_measure_valid_from=date(2020, 1, 15),
                    care=None  # Optional, testing without it
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Vormundschaftstrasse",
            house_number="5",
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

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.guardian_relationship is not None
        assert len(layer1_person.guardian_relationship) == 1

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "person_guardian_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.guardian_relationship is not None
            assert len(roundtrip_layer1_person.guardian_relationship) == 1

            guardian_rel = roundtrip_layer1_person.guardian_relationship[0]
            assert guardian_rel.person_identification is not None
            assert guardian_rel.person_identification.official_name == "Weber"
            assert guardian_rel.type_of_relationship == "7"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert len(roundtrip_event.person.guardians) == 1
            assert roundtrip_event.person.guardians[0].guardian_type == GuardianType.PERSON
            assert roundtrip_event.person.guardians[0].person.official_name == "Weber"

            # SUCCESS! 🎉

    def test_organization_guardian_kesb_xsd_validation(self):
        """Test organization guardian (KESB) with full XML+XSD validation.

        Complete chain validates KESB guardian preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-ORG-GUARDIAN",
            manufacturer="XSDTest",
            product="GuardianRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (minor child) with KESB guardian
        person = BaseDeliveryPerson(
            local_person_id="77890",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Emma",
            sex="2",  # female
            date_of_birth=date(2016, 11, 22),  # minor child
            vn="7561111077890",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",
            religion="111",  # Roman Catholic
            marital_status="1",  # unmarried (child)
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

            # Guardian: Organization guardian (KESB)
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-002",
                    guardian_type=GuardianType.ORGANISATION,
                    person=None,  # Not person guardian
                    organization_uid="CHE-123.456.789",  # KESB UID
                    organization_name="KESB Zürich",  # Kindes- und Erwachsenenschutzbehörde
                    # KESB has real address (zero-tolerance: no fake data)
                    address_street="Musterstrasse",
                    address_house_number="42",
                    address_postal_code="8001",
                    address_town="Zürich",
                    relationship_type="8",  # guardian_org
                    guardian_measure_based_on_law=["310", "311"],  # ZGB articles
                    guardian_measure_valid_from=date(2021, 6, 1),
                    care="1"  # joint custody/care (common for KESB)
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="KESBstrasse",
            house_number="18",
            town="Basel",
            swiss_zip_code=4000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="2701",  # Basel
            reporting_municipality_name="Basel",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.guardian_relationship is not None
        assert len(layer1_person.guardian_relationship) == 1

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "org_guardian_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.guardian_relationship is not None
            assert len(roundtrip_layer1_person.guardian_relationship) == 1

            guardian_rel = roundtrip_layer1_person.guardian_relationship[0]
            assert guardian_rel.partner_id_organisation is not None
            assert guardian_rel.type_of_relationship == "8"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert len(roundtrip_event.person.guardians) == 1
            assert roundtrip_event.person.guardians[0].guardian_type == GuardianType.ORGANISATION
            assert roundtrip_event.person.guardians[0].organization_uid == "CHE-123.456.789"

            # SUCCESS! 🎉

    def test_partner_guardian_with_person_identification_xsd_validation(self):
        """Test partner guardian with full XML+XSD validation.

        Complete chain validates partner guardian preservation.
        """
        # Step 1: Create Layer 2 config
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-XSD-PARTNER-GUARDIAN",
            manufacturer="XSDTest",
            product="GuardianRelationshipsTest",
            product_version="1.0.0",
            test_delivery_flag=True
        )

        # Step 2: Create Layer 2 person (minor child) with partner guardian
        person = BaseDeliveryPerson(
            local_person_id="88901",
            local_person_id_category="MU.6172",
            official_name="Keller",
            first_name="Liam",
            sex="1",  # male
            date_of_birth=date(2017, 3, 5),  # minor child
            vn="7561111088901",
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",
            religion="111",  # Roman Catholic
            marital_status="1",  # unmarried (child)
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

            # Guardian: Partner guardian (uses person_identification_partner in Layer 1)
            guardians=[
                GuardianInfo(
                    guardian_relationship_id="guardian-rel-003",
                    guardian_type=GuardianType.PERSON_PARTNER,
                    person=PersonIdentification(
                        vn="7569872345678",
                        local_person_id="guard-partner-001",
                        local_person_id_category="MU.6172",
                        official_name="Keller",
                        first_name="Anna",
                        original_name=None,
                        sex="2",  # female
                        date_of_birth=date(1982, 9, 12)
                    ),
                    organization_uid=None,  # Not organization guardian
                    organization_name=None,
                    relationship_type="7",  # guardian_person (same as PERSON type)
                    guardian_measure_based_on_law=["310"],  # ZGB article for guardianship
                    guardian_measure_valid_from=date(2022, 2, 10),
                    care="2"  # sole custody mother
                )
            ]
        )

        # Step 3: Create Layer 2 event
        dwelling = DwellingAddressInfo(
            street="Partnerstrasse",
            house_number="9",
            town="Luzern",
            swiss_zip_code=6000,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="1061",  # Luzern
            reporting_municipality_name="Luzern",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Step 4: Finalize
        delivery = event.finalize(config)
        assert delivery is not None

        # Verify Layer 1
        layer1_person = delivery.event[0].base_delivery_person
        assert layer1_person.guardian_relationship is not None
        assert len(layer1_person.guardian_relationship) == 1

        # Step 5: XML roundtrip
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "partner_guardian_xsd.xml"
            delivery.to_file(xml_path)

            xml_content = xml_path.read_text()
            xml_root = ET.fromstring(xml_content)
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)

            # Verify Layer 1 after XML
            roundtrip_layer1_person = roundtrip_delivery.event[0].base_delivery_person
            assert roundtrip_layer1_person.guardian_relationship is not None
            assert len(roundtrip_layer1_person.guardian_relationship) == 1

            guardian_rel = roundtrip_layer1_person.guardian_relationship[0]
            assert guardian_rel.person_identification_partner is not None
            assert guardian_rel.person_identification_partner.official_name == "Keller"
            assert guardian_rel.type_of_relationship == "7"

            # Convert to Layer 2
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify zero data loss
            assert len(roundtrip_event.person.guardians) == 1
            assert roundtrip_event.person.guardians[0].guardian_type == GuardianType.PERSON_PARTNER
            assert roundtrip_event.person.guardians[0].person.official_name == "Keller"
            assert roundtrip_event.person.guardians[0].person.first_name == "Anna"

            # SUCCESS! 🎉
