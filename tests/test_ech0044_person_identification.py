"""Tests for eCH-0044 Person Identification Pydantic models."""

import xml.etree.ElementTree as ET
import pytest
from datetime import date
from pydantic import ValidationError

from openmun_ech.ech0044 import (
    ECH0044DatePartiallyKnown,
    ECH0044NamedPersonId,
    ECH0044PersonIdentification,
)


class TestECH0044DatePartiallyKnown:
    """Test eCH-0044 partially known date model."""

    def test_create_full_date(self):
        """Test creating with full date."""
        d = ECH0044DatePartiallyKnown(year_month_day=date(1990, 5, 15))
        assert d.year_month_day == date(1990, 5, 15)
        assert d.year_month is None
        assert d.year is None

    def test_create_year_month(self):
        """Test creating with year and month."""
        d = ECH0044DatePartiallyKnown(year_month="1990-05")
        assert d.year_month_day is None
        assert d.year_month == "1990-05"
        assert d.year is None

    def test_create_year_only(self):
        """Test creating with year only."""
        d = ECH0044DatePartiallyKnown(year="1990")
        assert d.year_month_day is None
        assert d.year_month is None
        assert d.year == "1990"

    def test_factory_from_date(self):
        """Test factory method for full date."""
        d = ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        assert d.year_month_day == date(1990, 5, 15)
        assert d.year_month is None
        assert d.year is None

    def test_factory_from_year_month(self):
        """Test factory method for year-month."""
        d = ECH0044DatePartiallyKnown.from_year_month(1990, 5)
        assert d.year_month_day is None
        assert d.year_month == "1990-05"
        assert d.year is None

    def test_factory_from_year(self):
        """Test factory method for year only."""
        d = ECH0044DatePartiallyKnown.from_year(1990)
        assert d.year_month_day is None
        assert d.year_month is None
        assert d.year == "1990"

    def test_to_xml_full_date(self):
        """Test XML export for full date."""
        d = ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        xml = d.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0044/4}dateOfBirth'

        ymd_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}yearMonthDay')
        assert ymd_elem is not None
        assert ymd_elem.text == "1990-05-15"

    def test_to_xml_year_month(self):
        """Test XML export for year-month."""
        d = ECH0044DatePartiallyKnown.from_year_month(1990, 5)
        xml = d.to_xml()

        ym_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}yearMonth')
        assert ym_elem is not None
        assert ym_elem.text == "1990-05"

    def test_to_xml_year_only(self):
        """Test XML export for year only."""
        d = ECH0044DatePartiallyKnown.from_year(1990)
        xml = d.to_xml()

        y_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}year')
        assert y_elem is not None
        assert y_elem.text == "1990"

    def test_to_xml_fails_with_no_date(self):
        """Test XML export fails if no date set."""
        d = ECH0044DatePartiallyKnown()
        with pytest.raises(ValueError, match="Must specify one of"):
            d.to_xml()

    def test_to_xml_fails_with_multiple_dates(self):
        """Test XML export fails if multiple dates set."""
        d = ECH0044DatePartiallyKnown(
            year_month_day=date(1990, 5, 15),
            year_month="1990-05"
        )
        with pytest.raises(ValueError, match="Can only specify one of"):
            d.to_xml()

    def test_roundtrip_full_date(self):
        """Test XML roundtrip for full date."""
        original = ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        xml = original.to_xml()
        parsed = ECH0044DatePartiallyKnown.from_xml(xml)

        assert parsed.year_month_day == original.year_month_day
        assert parsed.year_month is None
        assert parsed.year is None

    def test_roundtrip_year_month(self):
        """Test XML roundtrip for year-month."""
        original = ECH0044DatePartiallyKnown.from_year_month(1990, 5)
        xml = original.to_xml()
        parsed = ECH0044DatePartiallyKnown.from_xml(xml)

        assert parsed.year_month_day is None
        assert parsed.year_month == original.year_month
        assert parsed.year is None

    def test_roundtrip_year_only(self):
        """Test XML roundtrip for year only."""
        original = ECH0044DatePartiallyKnown.from_year(1990)
        xml = original.to_xml()
        parsed = ECH0044DatePartiallyKnown.from_xml(xml)

        assert parsed.year_month_day is None
        assert parsed.year_month is None
        assert parsed.year == original.year


class TestECH0044NamedPersonId:
    """Test eCH-0044 named person ID model."""

    def test_create_minimal(self):
        """Test creating named person ID."""
        pid = ECH0044NamedPersonId(
            person_id_category="veka.id",
            person_id="12345"
        )
        assert pid.person_id_category == "veka.id"
        assert pid.person_id == "12345"

    def test_validation_category_max_length(self):
        """Test category max length validation."""
        with pytest.raises(ValidationError):
            ECH0044NamedPersonId(
                person_id_category="x" * 21,  # Max 20
                person_id="12345"
            )

    def test_validation_id_max_length(self):
        """Test ID max length validation."""
        with pytest.raises(ValidationError):
            ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="x" * 37  # Max 36
            )

    def test_to_xml_local_person_id(self):
        """Test XML export as localPersonId."""
        pid = ECH0044NamedPersonId(
            person_id_category="veka.id",
            person_id="MU.6172.123"
        )
        xml = pid.to_xml(element_name='localPersonId')

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0044/4}localPersonId'

        category_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}personIdCategory')
        assert category_elem is not None
        assert category_elem.text == "veka.id"

        id_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}personId')
        assert id_elem is not None
        assert id_elem.text == "MU.6172.123"

    def test_to_xml_other_person_id(self):
        """Test XML export as otherPersonId."""
        pid = ECH0044NamedPersonId(
            person_id_category="sedex.id",
            person_id="T4-1234"
        )
        xml = pid.to_xml(element_name='otherPersonId')

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0044/4}otherPersonId'

    def test_to_xml_eu_person_id(self):
        """Test XML export as euPersonId."""
        pid = ECH0044NamedPersonId(
            person_id_category="eu.passport",
            person_id="DE123456789"
        )
        xml = pid.to_xml(element_name='euPersonId')

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0044/4}euPersonId'

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0044NamedPersonId(
            person_id_category="veka.id",
            person_id="MU.6172.42"
        )
        xml = original.to_xml()
        parsed = ECH0044NamedPersonId.from_xml(xml)

        assert parsed.person_id_category == original.person_id_category
        assert parsed.person_id == original.person_id


class TestECH0044PersonIdentification:
    """Test eCH-0044 person identification model."""

    def test_create_minimal(self):
        """Test creating person identification with minimal required fields."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )

        assert person.vn is None
        assert person.local_person_id.person_id == "MU.6172.1"
        assert person.official_name == "Meier"
        assert person.first_name == "Anna"
        assert person.original_name is None
        assert person.sex == "2"
        assert person.date_of_birth.year_month_day == date(1990, 5, 15)
        assert len(person.other_person_id) == 0
        assert len(person.eu_person_id) == 0

    def test_create_full(self):
        """Test creating person identification with all fields."""
        person = ECH0044PersonIdentification(
            vn="7560123456789",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            other_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="sedex.id",
                    person_id="T4-1234"
                )
            ],
            eu_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="eu.passport",
                    person_id="DE123456789"
                )
            ],
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )

        assert person.vn == "7560123456789"
        assert len(person.other_person_id) == 1
        assert len(person.eu_person_id) == 1
        assert person.original_name == "Schmidt"

    def test_vn_validation_valid(self):
        """Test VN validation with valid number."""
        person = ECH0044PersonIdentification(
            vn="7560123456789",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        assert person.vn == "7560123456789"

    def test_vn_validation_invalid_length(self):
        """Test VN validation fails with wrong length."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ECH0044PersonIdentification(
                vn="756012345678",  # Only 12 digits
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            )

    def test_vn_validation_invalid_range(self):
        """Test VN validation fails outside valid range."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ECH0044PersonIdentification(
                vn="7550000000001",  # Starts with 755, not 756
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            )

    def test_to_xml_minimal(self):
        """Test XML export with minimal fields."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0044/4}personIdentification'

        # Check required fields
        local_id = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}localPersonId')
        assert local_id is not None

        official = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}officialName')
        assert official is not None
        assert official.text == "Meier"

        first = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}firstName')
        assert first is not None
        assert first.text == "Anna"

        sex = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}sex')
        assert sex is not None
        assert sex.text == "2"

        dob = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}dateOfBirth')
        assert dob is not None

        # VN should not be present
        vn = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}vn')
        assert vn is None

    def test_to_xml_full(self):
        """Test XML export with all fields."""
        person = ECH0044PersonIdentification(
            vn="7560123456789",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            other_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="sedex.id",
                    person_id="T4-1234"
                ),
                ECH0044NamedPersonId(
                    person_id_category="old.id",
                    person_id="OLD-999"
                )
            ],
            eu_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="eu.passport",
                    person_id="DE123456789"
                )
            ],
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()

        # Check VN
        vn = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}vn')
        assert vn is not None
        assert vn.text == "7560123456789"

        # Check other person IDs (should have 2)
        other_ids = xml.findall('{http://www.ech.ch/xmlns/eCH-0044/4}otherPersonId')
        assert len(other_ids) == 2

        # Check EU person IDs (should have 1)
        eu_ids = xml.findall('{http://www.ech.ch/xmlns/eCH-0044/4}euPersonId')
        assert len(eu_ids) == 1

        # Check original name
        original = xml.find('{http://www.ech.ch/xmlns/eCH-0044/4}originalName')
        assert original is not None
        assert original.text == "Schmidt"

    def test_roundtrip_minimal(self):
        """Test XML roundtrip with minimal fields."""
        original = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = original.to_xml()
        parsed = ECH0044PersonIdentification.from_xml(xml)

        assert parsed.vn is None
        assert parsed.local_person_id.person_id == original.local_person_id.person_id
        assert parsed.official_name == original.official_name
        assert parsed.first_name == original.first_name
        assert parsed.original_name is None
        assert parsed.sex == original.sex
        assert parsed.date_of_birth.year_month_day == original.date_of_birth.year_month_day

    def test_roundtrip_full(self):
        """Test XML roundtrip with all fields."""
        original = ECH0044PersonIdentification(
            vn="7560123456789",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            other_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="sedex.id",
                    person_id="T4-1234"
                )
            ],
            eu_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="eu.passport",
                    person_id="DE123456789"
                )
            ],
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = original.to_xml()
        parsed = ECH0044PersonIdentification.from_xml(xml)

        assert parsed.vn == original.vn
        assert parsed.local_person_id.person_id == original.local_person_id.person_id
        assert len(parsed.other_person_id) == 1
        assert parsed.other_person_id[0].person_id == "T4-1234"
        assert len(parsed.eu_person_id) == 1
        assert parsed.eu_person_id[0].person_id == "DE123456789"
        assert parsed.official_name == original.official_name
        assert parsed.first_name == original.first_name
        assert parsed.original_name == original.original_name
        assert parsed.sex == original.sex
        assert parsed.date_of_birth.year_month_day == original.date_of_birth.year_month_day

    def test_from_xml_missing_required_local_id(self):
        """Test parsing fails if localPersonId missing."""
        xml_str = """
        <personIdentification xmlns="http://www.ech.ch/xmlns/eCH-0044/4">
            <officialName>Meier</officialName>
            <firstName>Anna</firstName>
            <sex>2</sex>
            <dateOfBirth>
                <yearMonthDay>1990-05-15</yearMonthDay>
            </dateOfBirth>
        </personIdentification>
        """
        elem = ET.fromstring(xml_str)

        with pytest.raises(ValueError, match="Missing required field: localPersonId"):
            ECH0044PersonIdentification.from_xml(elem)

    def test_from_xml_missing_required_official_name(self):
        """Test parsing fails if officialName missing."""
        xml_str = """
        <personIdentification xmlns="http://www.ech.ch/xmlns/eCH-0044/4">
            <localPersonId>
                <personIdCategory>veka.id</personIdCategory>
                <personId>MU.6172.1</personId>
            </localPersonId>
            <firstName>Anna</firstName>
            <sex>2</sex>
            <dateOfBirth>
                <yearMonthDay>1990-05-15</yearMonthDay>
            </dateOfBirth>
        </personIdentification>
        """
        elem = ET.fromstring(xml_str)

        with pytest.raises(ValueError, match="Missing required field: officialName"):
            ECH0044PersonIdentification.from_xml(elem)
