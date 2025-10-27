"""Tests for eCH-0010 Address Pydantic models."""

import xml.etree.ElementTree as ET
import pytest
from pydantic import ValidationError

from openmun_ech.ech0010 import (
    ECH0010PersonMailAddressInfo,
    ECH0010OrganisationMailAddressInfo,
    ECH0010AddressInformation,
    ECH0010MailAddress,
)


class TestECH0010PersonMailAddressInfo:
    """Test eCH-0010 person mail address info model."""

    def test_create_minimal_person(self):
        """Test creating person with only last name (minimum required)."""
        person = ECH0010PersonMailAddressInfo(
            last_name="Müller"
        )
        assert person.last_name == "Müller"
        assert person.first_name is None
        assert person.title is None
        assert person.mr_mrs is None

    def test_create_full_person(self):
        """Test creating person with all fields."""
        person = ECH0010PersonMailAddressInfo(
            mr_mrs="1",
            title="Dr.",
            first_name="Hans",
            last_name="Müller"
        )
        assert person.mr_mrs == "1"
        assert person.title == "Dr."
        assert person.first_name == "Hans"
        assert person.last_name == "Müller"

    def test_validate_last_name_required(self):
        """Test that last_name is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0010PersonMailAddressInfo()

    def test_validate_last_name_max_length(self):
        """Test last_name max length (30 chars)."""
        with pytest.raises(ValidationError, match="String should have at most 30 characters"):
            ECH0010PersonMailAddressInfo(
                last_name="A" * 31
            )

    def test_validate_first_name_max_length(self):
        """Test first_name max length (30 chars)."""
        with pytest.raises(ValidationError, match="String should have at most 30 characters"):
            ECH0010PersonMailAddressInfo(
                first_name="A" * 31,
                last_name="Müller"
            )

    def test_validate_title_max_length(self):
        """Test title max length (50 chars)."""
        with pytest.raises(ValidationError, match="String should have at most 50 characters"):
            ECH0010PersonMailAddressInfo(
                title="A" * 51,
                last_name="Müller"
            )

    def test_validate_mr_mrs_values(self):
        """Test mr_mrs accepts only 1, 2, or 3."""
        # Valid values
        for value in ["1", "2", "3"]:
            person = ECH0010PersonMailAddressInfo(mr_mrs=value, last_name="Test")
            assert person.mr_mrs == value

        # Invalid value
        with pytest.raises(ValidationError, match="Input should be '1', '2' or '3'"):
            ECH0010PersonMailAddressInfo(mr_mrs="4", last_name="Test")

    def test_to_xml_minimal(self):
        """Test XML export with minimal data."""
        person = ECH0010PersonMailAddressInfo(last_name="Müller")
        xml = person.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0010/5}person'

        # Only last name should be present
        last_name = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}lastName')
        assert last_name is not None
        assert last_name.text == "Müller"

        # Optional fields should not be present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}firstName') is None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}title') is None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}mrMrs') is None

    def test_to_xml_full(self):
        """Test XML export with all fields."""
        person = ECH0010PersonMailAddressInfo(
            mr_mrs="1",
            title="Dr.",
            first_name="Hans",
            last_name="Müller"
        )
        xml = person.to_xml()

        # Check all fields present
        mr_mrs = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}mrMrs')
        assert mr_mrs is not None
        assert mr_mrs.text == "1"

        title = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}title')
        assert title is not None
        assert title.text == "Dr."

        first_name = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}firstName')
        assert first_name is not None
        assert first_name.text == "Hans"

        last_name = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}lastName')
        assert last_name is not None
        assert last_name.text == "Müller"

    def test_from_xml(self):
        """Test parsing from XML."""
        xml_str = """
        <person xmlns="http://www.ech.ch/xmlns/eCH-0010/5">
            <mrMrs>2</mrMrs>
            <title>Prof.</title>
            <firstName>Maria</firstName>
            <lastName>Schmidt</lastName>
        </person>
        """
        elem = ET.fromstring(xml_str)
        person = ECH0010PersonMailAddressInfo.from_xml(elem)

        assert person.mr_mrs == "2"
        assert person.title == "Prof."
        assert person.first_name == "Maria"
        assert person.last_name == "Schmidt"

    def test_roundtrip_xml(self):
        """Test XML roundtrip (export -> import -> export)."""
        original = ECH0010PersonMailAddressInfo(
            mr_mrs="1",
            title="Dr.",
            first_name="Hans",
            last_name="Müller"
        )

        # Export to XML
        xml = original.to_xml()

        # Import from XML
        parsed = ECH0010PersonMailAddressInfo.from_xml(xml)

        # Should be identical
        assert parsed.mr_mrs == original.mr_mrs
        assert parsed.title == original.title
        assert parsed.first_name == original.first_name
        assert parsed.last_name == original.last_name


class TestECH0010OrganisationMailAddressInfo:
    """Test eCH-0010 organisation mail address info model."""

    def test_create_minimal_organisation(self):
        """Test creating organisation with only name (minimum required)."""
        org = ECH0010OrganisationMailAddressInfo(
            organisation_name="Gemeinde Bister"
        )
        assert org.organisation_name == "Gemeinde Bister"
        assert org.organisation_name_add_on1 is None
        assert org.organisation_name_add_on2 is None
        assert org.mr_mrs is None
        assert org.title is None
        assert org.first_name is None
        assert org.last_name is None

    def test_create_full_organisation(self):
        """Test creating organisation with all fields."""
        org = ECH0010OrganisationMailAddressInfo(
            organisation_name="Gemeinde Bister",
            organisation_name_add_on1="Einwohnerkontrolle",
            organisation_name_add_on2="Abteilung Register",
            mr_mrs="2",
            title="lic. iur.",
            first_name="Anna",
            last_name="Meier"
        )
        assert org.organisation_name == "Gemeinde Bister"
        assert org.organisation_name_add_on1 == "Einwohnerkontrolle"
        assert org.organisation_name_add_on2 == "Abteilung Register"
        assert org.mr_mrs == "2"
        assert org.title == "lic. iur."
        assert org.first_name == "Anna"
        assert org.last_name == "Meier"

    def test_validate_organisation_name_required(self):
        """Test that organisation_name is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0010OrganisationMailAddressInfo()

    def test_validate_organisation_name_max_length(self):
        """Test organisation_name max length (60 chars)."""
        with pytest.raises(ValidationError, match="String should have at most 60 characters"):
            ECH0010OrganisationMailAddressInfo(
                organisation_name="A" * 61
            )

    def test_to_xml_minimal(self):
        """Test XML export with minimal data."""
        org = ECH0010OrganisationMailAddressInfo(
            organisation_name="Gemeinde Bister"
        )
        xml = org.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0010/5}organisation'

        # Only organisation name should be present
        org_name = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}organisationName')
        assert org_name is not None
        assert org_name.text == "Gemeinde Bister"

        # Optional fields should not be present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}organisationNameAddOn1') is None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}lastName') is None

    def test_roundtrip_xml(self):
        """Test XML roundtrip."""
        original = ECH0010OrganisationMailAddressInfo(
            organisation_name="Gemeinde Bister",
            organisation_name_add_on1="Einwohnerkontrolle",
            mr_mrs="1",
            first_name="Hans",
            last_name="Müller"
        )

        xml = original.to_xml()
        parsed = ECH0010OrganisationMailAddressInfo.from_xml(xml)

        assert parsed.organisation_name == original.organisation_name
        assert parsed.organisation_name_add_on1 == original.organisation_name_add_on1
        assert parsed.mr_mrs == original.mr_mrs
        assert parsed.first_name == original.first_name
        assert parsed.last_name == original.last_name


class TestECH0010AddressInformation:
    """Test eCH-0010 address information model."""

    def test_create_swiss_address_minimal(self):
        """Test creating minimal Swiss address."""
        addr = ECH0010AddressInformation(
            town="Bister",
            swiss_zip_code=3983,
            country="CH"
        )
        assert addr.town == "Bister"
        assert addr.swiss_zip_code == 3983
        assert addr.country == "CH"

    def test_create_swiss_address_full(self):
        """Test creating full Swiss address with all fields."""
        addr = ECH0010AddressInformation(
            address_line1="c/o Maria Meier",
            street="Hauptstrasse",
            house_number="42",
            dwelling_number="3",
            locality="Dorfkern",
            town="Bister",
            swiss_zip_code=3983,
            swiss_zip_code_add_on="01",
            swiss_zip_code_id=12345,
            country="CH"
        )
        assert addr.street == "Hauptstrasse"
        assert addr.house_number == "42"
        assert addr.dwelling_number == "3"
        assert addr.locality == "Dorfkern"
        assert addr.swiss_zip_code == 3983
        assert addr.swiss_zip_code_add_on == "01"
        assert addr.swiss_zip_code_id == 12345

    def test_create_foreign_address(self):
        """Test creating foreign address."""
        addr = ECH0010AddressInformation(
            street="Main Street",
            house_number="100",
            town="Paris",
            foreign_zip_code="75001",
            country="FR"
        )
        assert addr.street == "Main Street"
        assert addr.town == "Paris"
        assert addr.foreign_zip_code == "75001"
        assert addr.country == "FR"

    def test_validate_town_required(self):
        """Test that town is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0010AddressInformation(
                swiss_zip_code=3983,
                country="CH"
            )

    def test_validate_country_required(self):
        """Test that country is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983
            )

    def test_validate_zip_code_exclusivity(self):
        """Test that swiss_zip_code and foreign_zip_code are mutually exclusive."""
        # Both present - should fail
        with pytest.raises(ValidationError, match="Cannot have both swiss_zip_code and foreign_zip_code"):
            ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                foreign_zip_code="12345",
                country="CH"
            )

        # Neither present - should fail
        with pytest.raises(ValidationError, match="Must have either swiss_zip_code or foreign_zip_code"):
            ECH0010AddressInformation(
                town="Bister",
                country="CH"
            )

    def test_validate_swiss_zip_code_range(self):
        """Test Swiss ZIP code range (1000-9999)."""
        # Too low
        with pytest.raises(ValidationError, match="greater than or equal to 1000"):
            ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=999,
                country="CH"
            )

        # Too high
        with pytest.raises(ValidationError, match="less than or equal to 9999"):
            ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=10000,
                country="CH"
            )

        # Valid range
        addr = ECH0010AddressInformation(
            town="Bister",
            swiss_zip_code=1000,
            country="CH"
        )
        assert addr.swiss_zip_code == 1000

        addr = ECH0010AddressInformation(
            town="Zürich",
            swiss_zip_code=9999,
            country="CH"
        )
        assert addr.swiss_zip_code == 9999

    def test_validate_po_box_sequence(self):
        """Test PO Box validation: if number present, text must be present."""
        # Number without text - should fail
        with pytest.raises(ValidationError, match="post_office_box_text is required"):
            ECH0010AddressInformation(
                town="Bister",
                post_office_box_number=123,
                swiss_zip_code=3983,
                country="CH"
            )

        # Number with text - should succeed
        addr = ECH0010AddressInformation(
            town="Bister",
            post_office_box_number=123,
            post_office_box_text="Postfach",
            swiss_zip_code=3983,
            country="CH"
        )
        assert addr.post_office_box_number == 123
        assert addr.post_office_box_text == "Postfach"

    def test_country_uppercase_conversion(self):
        """Test country code is converted to uppercase."""
        addr = ECH0010AddressInformation(
            town="Bister",
            swiss_zip_code=3983,
            country="ch"  # lowercase
        )
        assert addr.country == "CH"  # Should be uppercase

    def test_to_xml_swiss_address(self):
        """Test XML export of Swiss address."""
        addr = ECH0010AddressInformation(
            street="Hauptstrasse",
            house_number="42",
            town="Bister",
            swiss_zip_code=3983,
            country="CH"
        )
        xml = addr.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0010/5}addressInformation'

        street = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}street')
        assert street is not None
        assert street.text == "Hauptstrasse"

        town = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}town')
        assert town is not None
        assert town.text == "Bister"

        zip_code = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}swissZipCode')
        assert zip_code is not None
        assert zip_code.text == "3983"

        country = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}country')
        assert country is not None
        assert country.text == "CH"

    def test_roundtrip_xml(self):
        """Test XML roundtrip."""
        original = ECH0010AddressInformation(
            address_line1="c/o Test",
            street="Hauptstrasse",
            house_number="42",
            dwelling_number="3",
            locality="Dorf",
            town="Bister",
            swiss_zip_code=3983,
            swiss_zip_code_add_on="01",
            country="CH"
        )

        xml = original.to_xml()
        parsed = ECH0010AddressInformation.from_xml(xml)

        assert parsed.address_line1 == original.address_line1
        assert parsed.street == original.street
        assert parsed.house_number == original.house_number
        assert parsed.dwelling_number == original.dwelling_number
        assert parsed.locality == original.locality
        assert parsed.town == original.town
        assert parsed.swiss_zip_code == original.swiss_zip_code
        assert parsed.swiss_zip_code_add_on == original.swiss_zip_code_add_on
        assert parsed.country == original.country


class TestECH0010MailAddress:
    """Test eCH-0010 mail address (top-level) model."""

    def test_create_person_mail_address(self):
        """Test creating mail address with person recipient."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                first_name="Hans",
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                street="Hauptstrasse",
                house_number="42",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        assert mail_addr.person is not None
        assert mail_addr.person.last_name == "Müller"
        assert mail_addr.organisation is None
        assert mail_addr.address_information.town == "Bister"

    def test_create_organisation_mail_address(self):
        """Test creating mail address with organisation recipient."""
        mail_addr = ECH0010MailAddress(
            organisation=ECH0010OrganisationMailAddressInfo(
                organisation_name="Gemeinde Bister"
            ),
            address_information=ECH0010AddressInformation(
                street="Rathausplatz",
                house_number="1",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        assert mail_addr.organisation is not None
        assert mail_addr.organisation.organisation_name == "Gemeinde Bister"
        assert mail_addr.person is None
        assert mail_addr.address_information.town == "Bister"

    def test_validate_person_or_organisation_required(self):
        """Test that either person or organisation must be present."""
        # Neither present - should fail
        with pytest.raises(ValidationError, match="Must have either person or organisation"):
            ECH0010MailAddress(
                address_information=ECH0010AddressInformation(
                    town="Bister",
                    swiss_zip_code=3983,
                    country="CH"
                )
            )

    def test_validate_person_and_organisation_exclusive(self):
        """Test that person and organisation are mutually exclusive."""
        # Both present - should fail
        with pytest.raises(ValidationError, match="Cannot have both person and organisation"):
            ECH0010MailAddress(
                person=ECH0010PersonMailAddressInfo(last_name="Müller"),
                organisation=ECH0010OrganisationMailAddressInfo(organisation_name="Test AG"),
                address_information=ECH0010AddressInformation(
                    town="Bister",
                    swiss_zip_code=3983,
                    country="CH"
                )
            )

    def test_to_xml_person_address(self):
        """Test XML export of person mail address."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                first_name="Hans",
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0010/5}mailAddress'

        # Person should be present
        person = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}person')
        assert person is not None

        # Organisation should not be present
        org = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}organisation')
        assert org is None

        # Address information should be present
        addr_info = xml.find('{http://www.ech.ch/xmlns/eCH-0010/5}addressInformation')
        assert addr_info is not None

    def test_roundtrip_xml(self):
        """Test XML roundtrip."""
        original = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                mr_mrs="1",
                title="Dr.",
                first_name="Hans",
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                street="Hauptstrasse",
                house_number="42",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        xml = original.to_xml()
        parsed = ECH0010MailAddress.from_xml(xml)

        assert parsed.person is not None
        assert parsed.person.mr_mrs == original.person.mr_mrs
        assert parsed.person.title == original.person.title
        assert parsed.person.first_name == original.person.first_name
        assert parsed.person.last_name == original.person.last_name
        assert parsed.organisation is None
        assert parsed.address_information.street == original.address_information.street
        assert parsed.address_information.town == original.address_information.town


class TestRealWorldScenarios:
    """Test real-world address scenarios."""

    def test_swiss_residential_address(self):
        """Test typical Swiss residential address."""
        addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                mr_mrs="2",
                first_name="Maria",
                last_name="Meier"
            ),
            address_information=ECH0010AddressInformation(
                street="Dorfstrasse",
                house_number="15",
                dwelling_number="2",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        # Should create successfully
        assert addr.person.last_name == "Meier"
        assert addr.address_information.swiss_zip_code == 3983

        # Should roundtrip through XML
        xml = addr.to_xml()
        parsed = ECH0010MailAddress.from_xml(xml)
        assert parsed.person.last_name == "Meier"
        assert parsed.address_information.dwelling_number == "2"

    def test_municipality_address_with_po_box(self):
        """Test municipality address with PO box."""
        addr = ECH0010MailAddress(
            organisation=ECH0010OrganisationMailAddressInfo(
                organisation_name="Gemeinde Bister",
                organisation_name_add_on1="Einwohnerkontrolle"
            ),
            address_information=ECH0010AddressInformation(
                post_office_box_number=12,
                post_office_box_text="Postfach",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        assert addr.organisation.organisation_name == "Gemeinde Bister"
        assert addr.address_information.post_office_box_number == 12

        # Should roundtrip
        xml = addr.to_xml()
        parsed = ECH0010MailAddress.from_xml(xml)
        assert parsed.address_information.post_office_box_number == 12
        assert parsed.address_information.post_office_box_text == "Postfach"

    def test_foreign_address(self):
        """Test foreign address (non-Swiss)."""
        addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                last_name="Schmidt"
            ),
            address_information=ECH0010AddressInformation(
                address_line1="123 Main Street",
                address_line2="Apartment 4B",
                town="Berlin",
                foreign_zip_code="10115",
                country="DE"
            )
        )

        assert addr.address_information.foreign_zip_code == "10115"
        assert addr.address_information.country == "DE"
        assert addr.address_information.swiss_zip_code is None

        # Should roundtrip
        xml = addr.to_xml()
        parsed = ECH0010MailAddress.from_xml(xml)
        assert parsed.address_information.foreign_zip_code == "10115"
        assert parsed.address_information.country == "DE"
