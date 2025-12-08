"""Tests for Contact CHOICE Constraint (Priority 1)

Tests the contact CHOICE constraint in eCH-0020 person data:
- Contact person: contact_person_partner with name fields
- Contact organization: contact_organization with organization name
- Contact address: Required when contact is present

Tests:
- Test 4: Contact person with address
- Test 5: Contact organization with address

CHOICE constraint verification:
- Person: contact_person_partner present, contact_organization None
- Organization: contact_organization present, contact_person/contact_person_partner None

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestContactChoice:
    """Test contact CHOICE constraint: Person XOR Organization."""

    def test_contact_person_with_address(self):
        """Test 4: Contact person with address.

        Tests:
        - contact_person_official_name and contact_person_first_name
        - contact_address fields (street, house_number, postal_code, town)
        - CHOICE constraint: contact_person present, contact_organization None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Family member or friend as contact person
        """
        # Create person with contact person
        person_with_contact = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="22222",
            local_person_id_category="MU.6172",
            official_name="Meier",
            first_name="Thomas",
            sex="1",  # male
            date_of_birth=date(1990, 3, 25),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="2",  # married

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
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Contact person (CHOICE: person XOR organization)
            contact_person_official_name="Schmidt",
            contact_person_first_name="Julia",
            # Include identifying data to trigger personIdentificationPartner (Light) creation
            contact_person_local_person_id="55555",
            contact_person_local_person_id_category="MU.6172",

            # Contact address (required when contact provided)
            contact_address_street="Bahnhofstrasse",
            contact_address_house_number="42",
            contact_address_postal_code="8001",
            contact_address_town="Zürich",

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_contact = person_with_contact.to_ech0020()

        # Verify contact CHOICE: has contact_person_partner, NOT contact_organization
        assert layer1_contact.contact_data is not None, "contact_data should exist"
        assert layer1_contact.contact_data.contact_person_partner is not None, \
            "contact_person_partner should exist"
        assert layer1_contact.contact_data.contact_person_partner.official_name == "Schmidt"
        assert layer1_contact.contact_data.contact_person_partner.first_name == "Julia"
        assert layer1_contact.contact_data.contact_organization is None, \
            "contact_organization should be None"

        # Verify contact address
        assert layer1_contact.contact_data.contact_address is not None, "contact_address should exist"
        assert layer1_contact.contact_data.contact_address.address_information.swiss_zip_code == 8001

        # Roundtrip: Layer 1 → Layer 2
        contact_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_contact)

        # Verify contact person preserved
        assert contact_roundtrip.contact_person_official_name == "Schmidt"
        assert contact_roundtrip.contact_person_first_name == "Julia"
        assert contact_roundtrip.contact_organization_name is None, \
            "contact_organization_name should be None"

        # Verify contact address preserved
        assert contact_roundtrip.contact_address_street == "Bahnhofstrasse"
        assert contact_roundtrip.contact_address_house_number == "42"
        assert contact_roundtrip.contact_address_postal_code == "8001"
        assert contact_roundtrip.contact_address_town == "Zürich"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_contact_roundtrip = contact_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_contact_roundtrip.contact_data.contact_person_partner is not None
        assert layer1_contact_roundtrip.contact_data.contact_organization is None
        assert layer1_contact_roundtrip.contact_data.contact_address.address_information.swiss_zip_code == 8001

    def test_contact_organization_with_address(self):
        """Test 5: Contact organization with address.

        Tests:
        - contact_organization_name field
        - contact_address fields (street, house_number, postal_code, town)
        - CHOICE constraint: contact_organization present, contact_person None
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Use case: Official organization (e.g., municipality office) as contact
        """
        # Create person with contact organization
        person_with_org_contact = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="33333",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Sarah",
            sex="2",  # female
            date_of_birth=date(1988, 7, 12),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="351",  # Bern
            birth_municipality_name="Bern",

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
                    'bfs_code': '351',
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Contact organization (CHOICE: organization XOR person)
            contact_organization_name="Einwohnerdienste Bern",

            # Contact address (required when contact provided)
            contact_address_street="Predigergasse",
            contact_address_house_number="5",
            contact_address_postal_code="3011",
            contact_address_town="Bern",

            # Lock data (required)
            data_lock="0",
            paper_lock="0"
        )

        # Convert to Layer 1
        layer1_org_contact = person_with_org_contact.to_ech0020()

        # Verify contact CHOICE: has contact_organization, NOT contact_person
        assert layer1_org_contact.contact_data is not None, "contact_data should exist"
        assert layer1_org_contact.contact_data.contact_organization is not None, \
            "contact_organization should exist"
        assert layer1_org_contact.contact_data.contact_organization.local_person_id.person_id == "33333"
        assert layer1_org_contact.contact_data.contact_person is None, \
            "contact_person should be None"
        assert layer1_org_contact.contact_data.contact_person_partner is None, \
            "contact_person_partner should be None"

        # Verify contact address has organization
        assert layer1_org_contact.contact_data.contact_address is not None, \
            "contact_address should exist"
        assert layer1_org_contact.contact_data.contact_address.organisation is not None, \
            "Mail address organization should exist"
        assert layer1_org_contact.contact_data.contact_address.person is None, \
            "Mail address person should be None"
        assert layer1_org_contact.contact_data.contact_address.address_information.swiss_zip_code == 3011

        # Roundtrip: Layer 1 → Layer 2
        org_contact_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_org_contact)

        # Verify contact organization preserved
        assert org_contact_roundtrip.contact_organization_name == "Einwohnerdienste Bern"
        assert org_contact_roundtrip.contact_person_official_name is None, \
            "contact_person_official_name should be None"
        assert org_contact_roundtrip.contact_person_first_name is None, \
            "contact_person_first_name should be None"

        # Verify contact address preserved
        assert org_contact_roundtrip.contact_address_street == "Predigergasse"
        assert org_contact_roundtrip.contact_address_house_number == "5"
        assert org_contact_roundtrip.contact_address_postal_code == "3011"
        assert org_contact_roundtrip.contact_address_town == "Bern"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_org_roundtrip = org_contact_roundtrip.to_ech0020()

        # Verify Layer 1 models equivalent
        assert layer1_org_roundtrip.contact_data.contact_organization is not None
        assert layer1_org_roundtrip.contact_data.contact_person is None
        assert layer1_org_roundtrip.contact_data.contact_person_partner is None
        assert layer1_org_roundtrip.contact_data.contact_address.address_information.swiss_zip_code == 3011
