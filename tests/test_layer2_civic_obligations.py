"""Tests 12-15: Civic Obligations

Tests Layer 2 handling of Swiss civic obligation fields:
- Test 12: Political right data (restricted voting rights)
- Test 13: Armed forces data (military service)
- Test 14: Civil defense data
- Test 15: Fire service data

These are optional Swiss-specific fields that track civic duties and restrictions.

Tests verify:
1. Layer 2 construction with civic obligation fields
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, canton codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestCivicObligations:
    """Test Layer 2 civic obligation fields."""

    def test_political_right_data_restricted_voting(self):
        """Test 12: Political right data with restricted voting rights.

        Tests:
        - restricted_voting_and_election_right_federation field
        - Use case: Citizens with temporary voting restrictions (e.g., legal guardianship)
        - Stored in ECH0011PoliticalRightData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with restricted voting rights
        person_political_restricted = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10004",
            local_person_id_category="MU.6172",
            official_name="Stauffer",
            first_name="Andreas",
            sex="1",  # male
            date_of_birth=date(1960, 3, 25),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # BFS 4-digit code
                    'country_iso': 'CH',
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

            # Lock data (required)
            data_lock="0",
            paper_lock=False,

            # Political right data (optional) - restricted voting
            restricted_voting_and_election_right_federation=True
        )

        # Convert to Layer 1
        layer1_political = person_political_restricted.to_ech0020()

        # Verify political right data structure
        assert layer1_political.political_right_data is not None, "political_right_data should exist"
        assert layer1_political.political_right_data.restricted_voting_and_election_right_federation is True, \
            "voting restriction should be True"

        # Roundtrip: Layer 1 → Layer 2
        political_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_political)

        # Verify political right data preserved
        assert political_roundtrip.restricted_voting_and_election_right_federation is True, \
            "voting restriction not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_political_roundtrip = political_roundtrip.to_ech0020()
        assert layer1_political_roundtrip.political_right_data is not None
        assert layer1_political_roundtrip.political_right_data.restricted_voting_and_election_right_federation is True

    def test_armed_forces_data_military_service(self):
        """Test 13: Armed forces data with military service.

        Tests:
        - armed_forces_service field (yes/no)
        - armed_forces_liability field (yes/no)
        - armed_forces_valid_from date
        - Use case: Swiss male citizens with military service obligation
        - Stored in ECH0011ArmedForcesData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with armed forces data
        person_armed_forces = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="10005",
            local_person_id_category="MU.6172",
            official_name="Wyss",
            first_name="Beat",
            sex="1",  # male
            date_of_birth=date(1995, 7, 18),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",  # Zürich
            birth_municipality_name="Zürich",

            # Religion (required)
            religion="111",  # Roman Catholic

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # BFS 4-digit code
                    'country_iso': 'CH',
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

            # Lock data (required)
            data_lock="0",
            paper_lock=False,

            # Armed forces data (optional)
            armed_forces_service="1",  # Yes - has completed/is doing military service
            armed_forces_liability="1",  # Yes - liable for military service
            armed_forces_valid_from=date(2018, 1, 15)
        )

        # Convert to Layer 1
        layer1_armed = person_armed_forces.to_ech0020()

        # Verify armed forces data structure
        assert layer1_armed.armed_forces_data is not None, "armed_forces_data should exist"
        assert layer1_armed.armed_forces_data.armed_forces_service == "1", "armed_forces_service should be '1'"
        assert layer1_armed.armed_forces_data.armed_forces_liability == "1", "armed_forces_liability should be '1'"
        assert layer1_armed.armed_forces_data.armed_forces_valid_from == date(2018, 1, 15), \
            "armed_forces_valid_from should match"

        # Roundtrip: Layer 1 → Layer 2
        armed_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_armed)

        # Verify armed forces data preserved
        assert armed_roundtrip.armed_forces_service == "1", "armed_forces_service not preserved"
        assert armed_roundtrip.armed_forces_liability == "1", "armed_forces_liability not preserved"
        assert armed_roundtrip.armed_forces_valid_from == date(2018, 1, 15), "armed_forces_valid_from not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_armed_roundtrip = armed_roundtrip.to_ech0020()
        assert layer1_armed_roundtrip.armed_forces_data is not None
        assert layer1_armed_roundtrip.armed_forces_data.armed_forces_service == "1"
        assert layer1_armed_roundtrip.armed_forces_data.armed_forces_liability == "1"
        assert layer1_armed_roundtrip.armed_forces_data.armed_forces_valid_from == date(2018, 1, 15)

    def test_civil_defense_data(self):
        """Test 14: Civil defense data.

        Tests:
        - civil_defense field (yes/no)
        - civil_defense_valid_from date
        - Use case: Swiss citizens with civil defense obligation (alternative to military)
        - Stored in ECH0011CivilDefenseData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with civil defense data
        person_civil_defense = BaseDeliveryPerson(
            local_person_id="10006",
            local_person_id_category="MU.6172",
            official_name="Herzog",
            first_name="Markus",
            sex="1",
            date_of_birth=date(1992, 11, 3),
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
            # Civil defense data (optional)
            civil_defense="1",
            civil_defense_valid_from=date(2015, 3, 10)
        )

        # Convert to Layer 1
        layer1_civil = person_civil_defense.to_ech0020()
        assert layer1_civil.civil_defense_data is not None
        assert layer1_civil.civil_defense_data.civil_defense == "1"
        assert layer1_civil.civil_defense_data.civil_defense_valid_from == date(2015, 3, 10)

        # Roundtrip: Layer 1 → Layer 2
        civil_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_civil)
        assert civil_roundtrip.civil_defense == "1"
        assert civil_roundtrip.civil_defense_valid_from == date(2015, 3, 10)

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_civil_roundtrip = civil_roundtrip.to_ech0020()
        assert layer1_civil_roundtrip.civil_defense_data is not None
        assert layer1_civil_roundtrip.civil_defense_data.civil_defense == "1"
        assert layer1_civil_roundtrip.civil_defense_data.civil_defense_valid_from == date(2015, 3, 10)

    def test_fire_service_data(self):
        """Test 15: Fire service data.

        Tests:
        - fire_service field (yes/no)
        - fire_service_liability field (yes/no)
        - fire_service_valid_from date
        - Use case: Swiss citizens with fire service obligation (local fire department)
        - Stored in ECH0011FireServiceData
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with fire service data
        person_fire = BaseDeliveryPerson(
            local_person_id="10007",
            local_person_id_category="MU.6172",
            official_name="Bauer",
            first_name="Stefan",
            sex="1",
            date_of_birth=date(1987, 4, 22),
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
            # Fire service data (optional)
            fire_service="1",
            fire_service_liability="1",
            fire_service_valid_from=date(2010, 8, 1)
        )

        # Convert to Layer 1
        layer1_fire = person_fire.to_ech0020()
        assert layer1_fire.fire_service_data is not None
        assert layer1_fire.fire_service_data.fire_service == "1"
        assert layer1_fire.fire_service_data.fire_service_liability == "1"
        assert layer1_fire.fire_service_data.fire_service_valid_from == date(2010, 8, 1)

        # Roundtrip: Layer 1 → Layer 2
        fire_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_fire)
        assert fire_roundtrip.fire_service == "1"
        assert fire_roundtrip.fire_service_liability == "1"
        assert fire_roundtrip.fire_service_valid_from == date(2010, 8, 1)

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_fire_roundtrip = fire_roundtrip.to_ech0020()
        assert layer1_fire_roundtrip.fire_service_data is not None
        assert layer1_fire_roundtrip.fire_service_data.fire_service == "1"
        assert layer1_fire_roundtrip.fire_service_data.fire_service_liability == "1"
        assert layer1_fire_roundtrip.fire_service_data.fire_service_valid_from == date(2010, 8, 1)
