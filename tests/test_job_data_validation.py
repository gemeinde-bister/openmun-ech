"""Job Data Validation Tests - eCH-0021 Compliance

Tests the fix for the bug where jobData was created with None kind_of_employment.

According to eCH-0021 standard (section 3.1.8):
- jobData.kindOfEmployment is MANDATORY ("zwingend")
- If kind_of_employment is None/unknown, the entire jobData element MUST be omitted
- Even if job_title or occupation_data are present, jobData cannot exist without kind_of_employment

These tests verify that the to_ech0020() conversion correctly handles edge cases.

Bug fix location: src/openmun_ech/ech0020/models.py:1960
Changed from: if any([self.kind_of_employment, self.job_title, self.occupation_data])
Changed to: if self.kind_of_employment is not None
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestJobDataValidation:
    """Test eCH-0021 jobData validation rules."""

    def _create_minimal_person(self, **kwargs) -> BaseDeliveryPerson:
        """Create a minimal valid person with required fields.

        Args:
            **kwargs: Override or add any fields

        Returns:
            BaseDeliveryPerson with valid minimal data
        """
        defaults = {
            # Person identification (required)
            "local_person_id": "12345",
            "local_person_id_category": "veka.id",
            "official_name": "TestPerson",
            "first_name": "Test",
            "sex": "1",  # male
            "date_of_birth": date(1980, 1, 1),

            # Birth info (required)
            "birth_place_type": PlaceType.SWISS,
            "birth_municipality_bfs": "261",  # Zürich
            "birth_municipality_name": "Zürich",

            # Religion (required)
            "religion": "111",  # Roman Catholic

            # Marital status (required)
            "marital_status": "1",  # unmarried

            # Nationality (required)
            "nationality_status": "1",  # Swiss
            "nationalities": [
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],

            # Citizenship CHOICE (required)
            "places_of_origin": [
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],

            # Lock data (required)
            "data_lock": "0",
            "paper_lock": "0",
        }

        # Merge kwargs into defaults
        defaults.update(kwargs)
        return BaseDeliveryPerson(**defaults)

    def test_job_title_without_kind_of_employment_should_not_create_jobdata(self):
        """Test that job_title alone does NOT create jobData.

        Scenario: Person has job_title but kind_of_employment is None.
        Expected: jobData should be None (per eCH-0021 standard).

        This tests the bug fix where the old code would incorrectly create
        jobData with None kind_of_employment, violating the standard.
        """
        person = self._create_minimal_person(
            kind_of_employment=None,  # Missing mandatory field
            job_title="Software Engineer"  # Present, but should be ignored
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData is NOT created (standard compliance)
        assert layer1.job_data is None, \
            "jobData should be None when kind_of_employment is None (eCH-0021 violation)"

    def test_occupation_data_without_kind_of_employment_should_not_create_jobdata(self):
        """Test that occupation_data alone does NOT create jobData.

        Scenario: Person has occupation_data but kind_of_employment is None.
        Expected: jobData should be None (per eCH-0021 standard).
        """
        person = self._create_minimal_person(
            kind_of_employment=None,  # Missing mandatory field
            occupation_data=[
                {
                    'employer': 'Tech AG',
                    'employer_uid': 'CHE-123.456.789',
                    'place_of_work': {
                        'town': 'Zürich',
                        'swiss_zip_code': 8000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2020, 1, 1)
                }
            ]  # Present, but should be ignored
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData is NOT created
        assert layer1.job_data is None, \
            "jobData should be None when kind_of_employment is None, even with occupation_data"

    def test_job_title_and_occupation_data_without_kind_of_employment(self):
        """Test that job_title + occupation_data without kind_of_employment does NOT create jobData.

        Scenario: Person has both job_title AND occupation_data but kind_of_employment is None.
        Expected: jobData should still be None (kindOfEmployment is mandatory).
        """
        person = self._create_minimal_person(
            kind_of_employment=None,  # Missing mandatory field
            job_title="Senior Data Analyst",
            occupation_data=[
                {
                    'employer': 'Research Institute',
                    'employer_uid': 'CHE-111.222.333',
                    'occupation_valid_from': date(2019, 1, 1)
                }
            ]
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData is NOT created
        assert layer1.job_data is None, \
            "jobData should be None when kind_of_employment is None, regardless of other fields"

    def test_kind_of_employment_alone_should_create_jobdata(self):
        """Test that kind_of_employment alone DOES create jobData.

        Scenario: Person has kind_of_employment but no job_title or occupation_data.
        Expected: jobData should be created (kindOfEmployment is present).
        """
        person = self._create_minimal_person(
            kind_of_employment="1",  # Employed - MANDATORY field present
            job_title=None,
            occupation_data=None
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData IS created
        assert layer1.job_data is not None, \
            "jobData should be created when kind_of_employment is present"
        assert layer1.job_data.kind_of_employment == "1", \
            "kind_of_employment should be preserved"
        assert layer1.job_data.job_title is None, \
            "job_title should be None"
        assert layer1.job_data.occupation_data == [], \
            "occupation_data should be empty list"

    def test_kind_of_employment_with_job_title_creates_jobdata(self):
        """Test that kind_of_employment + job_title creates jobData.

        Scenario: Person has both kind_of_employment and job_title.
        Expected: jobData should be created with both fields.
        """
        person = self._create_minimal_person(
            kind_of_employment="2",  # Self-employed
            job_title="Freelance Consultant"
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData is created correctly
        assert layer1.job_data is not None, "jobData should be created"
        assert layer1.job_data.kind_of_employment == "2"
        assert layer1.job_data.job_title == "Freelance Consultant"
        assert layer1.job_data.occupation_data == []

    def test_kind_of_employment_with_occupation_data_creates_jobdata(self):
        """Test that kind_of_employment + occupation_data creates jobData.

        Scenario: Person has kind_of_employment and occupation_data.
        Expected: jobData should be created with occupation list.
        """
        person = self._create_minimal_person(
            kind_of_employment="1",  # Employed
            occupation_data=[
                {
                    'employer': 'Company XYZ',
                    'employer_uid': 'CHE-999.888.777',
                    'place_of_work': {
                        'town': 'Bern',
                        'swiss_zip_code': 3000,
                        'country': 'CH'
                    }
                }
            ]
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify jobData is created correctly
        assert layer1.job_data is not None, "jobData should be created"
        assert layer1.job_data.kind_of_employment == "1"
        assert layer1.job_data.occupation_data is not None
        assert len(layer1.job_data.occupation_data) == 1
        assert layer1.job_data.occupation_data[0].employer == 'Company XYZ'

    def test_all_job_fields_present_creates_complete_jobdata(self):
        """Test that all job fields present creates complete jobData.

        Scenario: Person has kind_of_employment, job_title, AND occupation_data.
        Expected: jobData should be created with all fields.
        """
        person = self._create_minimal_person(
            kind_of_employment="1",  # Employed
            job_title="Project Manager",
            occupation_data=[
                {
                    'employer': 'Consulting AG',
                    'employer_uid': 'CHE-555.666.777',
                    'place_of_work': {
                        'town': 'Basel',
                        'swiss_zip_code': 4000,
                        'country': 'CH'
                    },
                    'occupation_valid_from': date(2021, 3, 1)
                }
            ]
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify complete jobData structure
        assert layer1.job_data is not None, "jobData should be created"
        assert layer1.job_data.kind_of_employment == "1"
        assert layer1.job_data.job_title == "Project Manager"
        assert len(layer1.job_data.occupation_data) == 1
        assert layer1.job_data.occupation_data[0].employer == 'Consulting AG'
        assert layer1.job_data.occupation_data[0].occupation_valid_from == date(2021, 3, 1)

    def test_no_job_fields_creates_no_jobdata(self):
        """Test that no job fields at all does NOT create jobData.

        Scenario: Person has no job-related fields set.
        Expected: jobData should be None.
        """
        person = self._create_minimal_person()

        # Convert to Layer 1
        layer1 = person.to_ech0020()

        # Verify no jobData
        assert layer1.job_data is None, \
            "jobData should be None when no job fields are present"

    def test_roundtrip_with_none_kind_of_employment_and_job_title(self):
        """Test roundtrip behavior when job_title exists but kind_of_employment is None.

        Scenario: Person has job_title but no kind_of_employment.
        Expected:
        - Layer 2 → Layer 1: jobData is None (job_title is lost)
        - Layer 1 → Layer 2: job_title remains None (no data loss from Layer 1)

        Note: This is expected data loss from Layer 2 to Layer 1, because the
        eCH-0021 standard forbids jobData without kindOfEmployment.
        """
        person = self._create_minimal_person(
            kind_of_employment=None,
            job_title="Engineer"  # This will be lost in conversion
        )

        # Convert to Layer 1
        layer1 = person.to_ech0020()
        assert layer1.job_data is None, "jobData should be None"

        # Convert back to Layer 2
        roundtrip = BaseDeliveryPerson.from_ech0020(layer1)

        # Verify job fields are None (expected data loss from Layer 2 → Layer 1)
        assert roundtrip.kind_of_employment is None
        assert roundtrip.job_title is None
        assert roundtrip.occupation_data is None

        # This is acceptable because the Layer 2 data was invalid per eCH-0021 standard
