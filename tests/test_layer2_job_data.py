"""Priority 4: Job Data Tests - Single and Multiple Employers

Tests Layer 2 occupation_data field handling:
- Test 26: Single employer (occupation_data with 1 entry)
- Test 27: Multiple employers (occupation_data with 2+ entries, overlapping dates)

Tests verify:
1. Layer 2 construction with job data
2. to_ech0020() conversion (Layer 2 → Layer 1)
3. from_ech0020() conversion (Layer 1 → Layer 2)
4. Full roundtrip with zero data loss
5. List preservation (Rule #5: Preserve lists even for "typical" cases)

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes, canton codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestLayer2JobData:
    """Test Layer 2 job data (occupation_data) handling."""

    def test_single_employer_with_occupation_data(self):
        """Test 26: Single employer with occupation_data.

        Tests:
        - occupation_data list with 1 entry
        - kind_of_employment, job_title fields
        - employer, employer_uid, place_of_work, place_of_employer
        - occupation_valid_from, occupation_valid_till dates
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person with single employer
        person_single_employer = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",  # male
            date_of_birth=date(1980, 5, 15),

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
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',   # ISO 2-letter code
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required)
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Job data - Single employer
            kind_of_employment="1",  # Employed
            job_title="Software Engineer",
            occupation_data=[
                {
                    'employer': 'Tech AG',
                    'employer_uid': 'CHE-123.456.789',
                    'place_of_work': {
                        'town': 'Zürich',
                        'swiss_zip_code': 8000,
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'town': 'Zürich',
                        'swiss_zip_code': 8000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2015, 1, 1),
                    'occupation_valid_till': None  # Current employment, no end date
                }
            ]
        )

        # Convert to Layer 1
        layer1_single = person_single_employer.to_ech0020()

        # Verify job_data structure in Layer 1
        assert layer1_single.job_data is not None, "job_data missing in Layer 1"
        assert layer1_single.job_data.kind_of_employment == "1", "kind_of_employment not preserved"
        assert layer1_single.job_data.job_title == "Software Engineer", "job_title not preserved"
        assert layer1_single.job_data.occupation_data is not None, "occupation_data missing"
        assert len(layer1_single.job_data.occupation_data) == 1, "occupation_data count wrong"

        # Verify single occupation entry
        occ = layer1_single.job_data.occupation_data[0]
        assert occ.employer == 'Tech AG', "employer name not preserved"
        # Verify UID structure
        assert occ.uid is not None, "employer_uid missing"
        assert occ.uid.uid_organisation_id_categorie.value == "CHE", "employer_uid category wrong"
        assert occ.uid.uid_organisation_id == 123456789, "employer_uid number wrong"
        # Verify place_of_work address
        assert occ.place_of_work is not None, "place_of_work missing"
        assert occ.place_of_work.town == 'Zürich', "place_of_work town wrong"
        # Verify place_of_employer address
        assert occ.place_of_employer is not None, "place_of_employer missing"
        assert occ.place_of_employer.town == 'Zürich', "place_of_employer town wrong"
        # Verify dates
        assert occ.occupation_valid_from == date(2015, 1, 1), "occupation_valid_from not preserved"
        assert occ.occupation_valid_till is None, "occupation_valid_till should be None"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_single = BaseDeliveryPerson.from_ech0020(layer1_single)

        # Verify all job fields preserved
        assert roundtrip_single.kind_of_employment == person_single_employer.kind_of_employment, \
            "kind_of_employment not preserved in roundtrip"
        assert roundtrip_single.job_title == person_single_employer.job_title, \
            "job_title not preserved in roundtrip"
        assert roundtrip_single.occupation_data is not None, "occupation_data lost in roundtrip"
        assert len(roundtrip_single.occupation_data) == 1, "occupation_data count changed in roundtrip"

        # Verify single occupation entry preserved
        occ_rt = roundtrip_single.occupation_data[0]
        occ_orig = person_single_employer.occupation_data[0]
        assert occ_rt['employer'] == occ_orig['employer'], "employer not preserved in roundtrip"
        assert occ_rt['employer_uid'] == occ_orig['employer_uid'], "employer_uid not preserved in roundtrip"

        # Compare place_of_work dicts (roundtrip has all fields, original may have subset)
        assert occ_rt['place_of_work'] is not None, "place_of_work lost in roundtrip"
        assert occ_rt['place_of_work']['town'] == occ_orig['place_of_work']['town'], "place_of_work town not preserved"
        assert occ_rt['place_of_work']['swiss_zip_code'] == occ_orig['place_of_work']['swiss_zip_code'], "place_of_work zip not preserved"
        assert occ_rt['place_of_work']['country'] == occ_orig['place_of_work']['country'], "place_of_work country not preserved"

        # Compare place_of_employer dicts
        assert occ_rt['place_of_employer'] is not None, "place_of_employer lost in roundtrip"
        assert occ_rt['place_of_employer']['town'] == occ_orig['place_of_employer']['town'], "place_of_employer town not preserved"
        assert occ_rt['place_of_employer']['swiss_zip_code'] == occ_orig['place_of_employer']['swiss_zip_code'], "place_of_employer zip not preserved"
        assert occ_rt['place_of_employer']['country'] == occ_orig['place_of_employer']['country'], "place_of_employer country not preserved"
        assert occ_rt['occupation_valid_from'] == occ_orig['occupation_valid_from'], "occupation_valid_from not preserved in roundtrip"
        assert occ_rt['occupation_valid_till'] == occ_orig['occupation_valid_till'], "occupation_valid_till not preserved in roundtrip"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_single = roundtrip_single.to_ech0020()

        # Verify Layer 1 models are equivalent
        assert layer1_roundtrip_single.job_data.kind_of_employment == layer1_single.job_data.kind_of_employment
        assert layer1_roundtrip_single.job_data.job_title == layer1_single.job_data.job_title
        assert len(layer1_roundtrip_single.job_data.occupation_data) == len(layer1_single.job_data.occupation_data)
        assert layer1_roundtrip_single.job_data.occupation_data[0].employer == layer1_single.job_data.occupation_data[0].employer

    def test_multiple_employers_with_overlapping_dates(self):
        """Test 27: Multiple employers with overlapping dates.

        Tests:
        - occupation_data list with 3 entries (2 concurrent, 1 past)
        - Part-time work scenario with overlapping employment
        - Different employer UIDs and locations
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        - Validates Rule #5: Preserve lists even for "typical" cases
        """
        # Create Layer 2 person with multiple employers
        person_multiple_employers = BaseDeliveryPerson(
            # Person identification (required)
            local_person_id="67890",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Maria",
            sex="2",  # female
            date_of_birth=date(1985, 8, 20),

            # Birth info (required)
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="230",  # Bern
            birth_municipality_name="Bern",

            # Religion (required)
            religion="121",  # Protestant

            # Marital status (required)
            marital_status="1",  # unmarried

            # Nationality (required)
            nationality_status="1",  # Swiss
            nationalities=[
                {
                    'country_id': '8100',  # Switzerland (BFS 4-digit code)
                    'country_iso': 'CH',   # ISO 2-letter code
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required)
            places_of_origin=[
                {
                    'bfs_code': '230',
                    'name': 'Bern',
                    'canton': 'BE'
                }
            ],

            # Lock data (required)
            data_lock="0",
            paper_lock="0",

            # Job data - Multiple employers (part-time work, overlapping dates)
            kind_of_employment="1",  # Employed
            job_title="Data Analyst",
            occupation_data=[
                {
                    'employer': 'Research Institute Alpha',
                    'employer_uid': 'CHE-111.222.333',
                    'place_of_work': {
                        'town': 'Bern',
                        'swiss_zip_code': 3000,
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'town': 'Bern',
                        'swiss_zip_code': 3000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2020, 1, 1),
                    'occupation_valid_till': None  # Ongoing
                },
                {
                    'employer': 'Consulting Beta GmbH',
                    'employer_uid': 'CHE-444.555.666',
                    'place_of_work': {
                        'town': 'Zürich',
                        'swiss_zip_code': 8000,
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'town': 'Zürich',
                        'swiss_zip_code': 8000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2021, 6, 1),  # Started while still at first job
                    'occupation_valid_till': None  # Ongoing
                },
                {
                    'employer': 'Previous Employer Corp',
                    'employer_uid': 'CHE-777.888.999',
                    'place_of_work': {
                        'town': 'Basel',
                        'swiss_zip_code': 4000,
                        'country': 'CH'
                    },
                    'place_of_employer': {
                        'town': 'Basel',
                        'swiss_zip_code': 4000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2018, 3, 1),
                    'occupation_valid_till': date(2019, 12, 31)  # Ended before current jobs
                }
            ]
        )

        # Convert to Layer 1
        layer1_multiple = person_multiple_employers.to_ech0020()

        # Verify job_data structure with multiple occupations
        assert layer1_multiple.job_data is not None, "job_data missing"
        assert layer1_multiple.job_data.occupation_data is not None, "occupation_data missing"
        assert len(layer1_multiple.job_data.occupation_data) == 3, \
            f"Expected 3 occupations, got {len(layer1_multiple.job_data.occupation_data)}"

        # Verify first occupation (current, Research Institute)
        occ1 = layer1_multiple.job_data.occupation_data[0]
        assert occ1.employer == 'Research Institute Alpha', "First employer name wrong"
        assert occ1.uid.uid_organisation_id == 111222333, "First employer UID number wrong"
        assert occ1.uid.uid_organisation_id_categorie.value == "CHE", "First employer UID category wrong"
        assert occ1.occupation_valid_from == date(2020, 1, 1), "First employer start date wrong"
        assert occ1.occupation_valid_till is None, "First employer should have no end date"

        # Verify second occupation (current, Consulting)
        occ2 = layer1_multiple.job_data.occupation_data[1]
        assert occ2.employer == 'Consulting Beta GmbH', "Second employer name wrong"
        assert occ2.uid.uid_organisation_id == 444555666, "Second employer UID number wrong"
        assert occ2.uid.uid_organisation_id_categorie.value == "CHE", "Second employer UID category wrong"
        assert occ2.occupation_valid_from == date(2021, 6, 1), "Second employer start date wrong"
        assert occ2.occupation_valid_till is None, "Second employer should have no end date"

        # Verify third occupation (past employment)
        occ3 = layer1_multiple.job_data.occupation_data[2]
        assert occ3.employer == 'Previous Employer Corp', "Third employer name wrong"
        assert occ3.uid.uid_organisation_id == 777888999, "Third employer UID number wrong"
        assert occ3.uid.uid_organisation_id_categorie.value == "CHE", "Third employer UID category wrong"
        assert occ3.occupation_valid_from == date(2018, 3, 1), "Third employer start date wrong"
        assert occ3.occupation_valid_till == date(2019, 12, 31), "Third employer end date wrong"

        # Roundtrip: Layer 1 → Layer 2
        roundtrip_multiple = BaseDeliveryPerson.from_ech0020(layer1_multiple)

        # Verify occupation_data list fully preserved
        assert roundtrip_multiple.occupation_data is not None, "occupation_data lost"
        assert len(roundtrip_multiple.occupation_data) == 3, \
            f"Expected 3 occupations in roundtrip, got {len(roundtrip_multiple.occupation_data)}"

        # Verify each occupation preserved (iterate to avoid repetition)
        for i, (occ_rt, occ_orig) in enumerate(zip(
            roundtrip_multiple.occupation_data,
            person_multiple_employers.occupation_data
        )):
            assert occ_rt['employer'] == occ_orig['employer'], \
                f"Occupation {i}: employer not preserved"
            assert occ_rt['employer_uid'] == occ_orig['employer_uid'], \
                f"Occupation {i}: employer_uid not preserved"

            # Compare place_of_work dicts
            assert occ_rt['place_of_work'] is not None, f"Occupation {i}: place_of_work lost"
            assert occ_rt['place_of_work']['town'] == occ_orig['place_of_work']['town'], \
                f"Occupation {i}: place_of_work town not preserved"
            assert occ_rt['place_of_work']['swiss_zip_code'] == occ_orig['place_of_work']['swiss_zip_code'], \
                f"Occupation {i}: place_of_work zip not preserved"
            assert occ_rt['place_of_work']['country'] == occ_orig['place_of_work']['country'], \
                f"Occupation {i}: place_of_work country not preserved"

            # Compare place_of_employer dicts
            assert occ_rt['place_of_employer'] is not None, f"Occupation {i}: place_of_employer lost"
            assert occ_rt['place_of_employer']['town'] == occ_orig['place_of_employer']['town'], \
                f"Occupation {i}: place_of_employer town not preserved"
            assert occ_rt['place_of_employer']['swiss_zip_code'] == occ_orig['place_of_employer']['swiss_zip_code'], \
                f"Occupation {i}: place_of_employer zip not preserved"
            assert occ_rt['place_of_employer']['country'] == occ_orig['place_of_employer']['country'], \
                f"Occupation {i}: place_of_employer country not preserved"

            assert occ_rt['occupation_valid_from'] == occ_orig['occupation_valid_from'], \
                f"Occupation {i}: occupation_valid_from not preserved"
            assert occ_rt['occupation_valid_till'] == occ_orig['occupation_valid_till'], \
                f"Occupation {i}: occupation_valid_till not preserved"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip_multiple = roundtrip_multiple.to_ech0020()

        # Verify Layer 1 models equivalent
        assert len(layer1_roundtrip_multiple.job_data.occupation_data) == \
               len(layer1_multiple.job_data.occupation_data), \
               "Occupation count changed in full roundtrip"

        for i, (occ_rt, occ_orig) in enumerate(zip(
            layer1_roundtrip_multiple.job_data.occupation_data,
            layer1_multiple.job_data.occupation_data
        )):
            assert occ_rt.employer == occ_orig.employer, \
                f"Occupation {i}: employer changed in full roundtrip"
            assert occ_rt.uid == occ_orig.uid, \
                f"Occupation {i}: UID changed in full roundtrip"
