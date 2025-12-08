"""XSD validation tests for eCH-0010 Address models.

These tests validate that our Pydantic models generate XML that conforms
to the official eCH-0010 XSD schema.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import xmlschema
import pytest

from openmun_ech.ech0010 import (
    ECH0010PersonMailAddressInfo,
    ECH0010OrganisationMailAddressInfo,
    ECH0010AddressInformation,
    ECH0010MailAddress,
)


# XSD schema path
ECH0010_XSD_PATH = Path(__file__).parent.parent / 'docs' / 'eCH' / 'eCH-0010-5-1.xsd'


class TestECH0010XSDValidation:
    """Test eCH-0010 models against official XSD schema."""

    @pytest.fixture(scope='class')
    def schema(self):
        """Load eCH-0010 XSD schema once for all tests."""
        assert ECH0010_XSD_PATH.exists(), f"XSD not found at {ECH0010_XSD_PATH}"
        return xmlschema.XMLSchema(str(ECH0010_XSD_PATH))

    def test_minimal_person_address_valid(self, schema):
        """Test minimal person address validates against XSD."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        # Should validate successfully
        assert schema.is_valid(xml_str)

    def test_full_person_address_valid(self, schema):
        """Test full person address with all fields validates against XSD."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                mr_mrs="1",
                title="Dr.",
                first_name="Hans",
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                address_line1="c/o Maria Meier",
                address_line2="Zusatz",
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
        )

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        assert schema.is_valid(xml_str)

    def test_organisation_address_valid(self, schema):
        """Test organisation address validates against XSD."""
        mail_addr = ECH0010MailAddress(
            organisation=ECH0010OrganisationMailAddressInfo(
                organisation_name="Gemeinde Bister",
                organisation_name_add_on1="Einwohnerkontrolle",
                organisation_name_add_on2="Abteilung Register",
                mr_mrs="2",
                title="lic. iur.",
                first_name="Anna",
                last_name="Meier"
            ),
            address_information=ECH0010AddressInformation(
                street="Rathausplatz",
                house_number="1",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        assert schema.is_valid(xml_str)

    def test_po_box_address_valid(self, schema):
        """Test address with PO box validates against XSD."""
        mail_addr = ECH0010MailAddress(
            organisation=ECH0010OrganisationMailAddressInfo(
                organisation_name="Gemeinde Bister"
            ),
            address_information=ECH0010AddressInformation(
                post_office_box_number=12,
                post_office_box_text="Postfach",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        assert schema.is_valid(xml_str)

    def test_foreign_address_valid(self, schema):
        """Test foreign address validates against XSD."""
        mail_addr = ECH0010MailAddress(
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

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        assert schema.is_valid(xml_str)

    def test_swiss_zip_code_range_enforcement(self, schema):
        """Test XSD enforces Swiss ZIP code range (1000-9999)."""
        # Minimum valid value
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Test"),
            address_information=ECH0010AddressInformation(
                town="Aigle",
                swiss_zip_code=1000,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert schema.is_valid(xml_str)

        # Maximum valid value
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Test"),
            address_information=ECH0010AddressInformation(
                town="Zürich",
                swiss_zip_code=9999,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert schema.is_valid(xml_str)

    def test_po_box_number_max_value(self, schema):
        """Test XSD enforces PO box number max value (99999999)."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Test"),
            address_information=ECH0010AddressInformation(
                post_office_box_number=99999999,
                post_office_box_text="Postfach",
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert schema.is_valid(xml_str)

    def test_field_length_constraints(self, schema):
        """Test XSD enforces field length constraints."""
        # All fields at max length
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                title="A" * 50,  # max 50
                first_name="B" * 30,  # max 30
                last_name="C" * 30  # max 30
            ),
            address_information=ECH0010AddressInformation(
                address_line1="D" * 60,  # max 60
                address_line2="E" * 60,  # max 60
                street="F" * 60,  # max 60
                house_number="G" * 12,  # max 12
                dwelling_number="H" * 10,  # max 10
                locality="I" * 40,  # max 40
                town="J" * 40,  # max 40
                foreign_zip_code="K" * 15,  # max 15
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert schema.is_valid(xml_str)

    def test_namespace_correctness(self, schema):
        """Test XML uses correct eCH-0010 namespace."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Test"),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()

        # Check root element has correct namespace
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0010/5}mailAddress'

        # Validate
        xml_str = ET.tostring(xml, encoding='unicode')
        assert schema.is_valid(xml_str)

    def test_element_order_correct(self, schema):
        """Test elements appear in correct XSD-defined order."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(
                mr_mrs="1",
                title="Dr.",
                first_name="Hans",
                last_name="Müller"
            ),
            address_information=ECH0010AddressInformation(
                address_line1="Line 1",
                address_line2="Line 2",
                street="Street",
                house_number="42",
                dwelling_number="3",
                post_office_box_number=123,
                post_office_box_text="PO Box",
                locality="Locality",
                town="Town",
                swiss_zip_code=3983,
                swiss_zip_code_add_on="01",
                swiss_zip_code_id=12345,
                country="CH"
            )
        )

        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        # XSD validation will fail if element order is wrong
        assert schema.is_valid(xml_str)


class TestECH0010ManualValidation:
    """Manual validation tests (not using XSD validator)."""

    def test_xml_well_formed(self):
        """Test XML is well-formed."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Müller"),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        # Should be able to parse it back
        reparsed = ET.fromstring(xml_str)
        assert reparsed is not None

    def test_xml_element_order_person_info(self):
        """Test person info elements appear in correct order: mrMrs, title, firstName, lastName."""
        person = ECH0010PersonMailAddressInfo(
            mr_mrs="1",
            title="Dr.",
            first_name="Hans",
            last_name="Müller"
        )
        xml = person.to_xml()

        # Get all child elements
        children = list(xml)
        child_tags = [child.tag for child in children]

        # Expected order (with namespace)
        ns = 'http://www.ech.ch/xmlns/eCH-0010/5'
        expected_order = [
            f'{{{ns}}}mrMrs',
            f'{{{ns}}}title',
            f'{{{ns}}}firstName',
            f'{{{ns}}}lastName'
        ]

        assert child_tags == expected_order

    def test_optional_fields_omitted_when_none(self):
        """Test optional fields are not included in XML when None."""
        person = ECH0010PersonMailAddressInfo(last_name="Müller")
        xml = person.to_xml()

        # Check only lastName is present
        children = list(xml)
        assert len(children) == 1
        assert children[0].tag == '{http://www.ech.ch/xmlns/eCH-0010/5}lastName'

    def test_no_unexpected_elements(self):
        """Test XML contains only expected elements."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Müller"),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()

        # mailAddress should have exactly 2 children: person, addressInformation
        children = list(xml)
        assert len(children) == 2

        ns = 'http://www.ech.ch/xmlns/eCH-0010/5'
        assert children[0].tag == f'{{{ns}}}person'
        assert children[1].tag == f'{{{ns}}}addressInformation'

    def test_xml_text_content_not_empty(self):
        """Test XML text content is not empty for required fields."""
        mail_addr = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Müller"),
            address_information=ECH0010AddressInformation(
                town="Bister",
                swiss_zip_code=3983,
                country="CH"
            )
        )
        xml = mail_addr.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')

        root = ET.fromstring(xml_str)
        ns = {'eCH-0010': 'http://www.ech.ch/xmlns/eCH-0010/5'}

        # Check required fields have text content
        last_name = root.find('.//eCH-0010:lastName', ns)
        assert last_name is not None
        assert last_name.text
        assert last_name.text.strip() == "Müller"

        town = root.find('.//eCH-0010:town', ns)
        assert town is not None
        assert town.text
        assert town.text.strip() == "Bister"

        country = root.find('.//eCH-0010:country', ns)
        assert country is not None
        assert country.text
        assert country.text.strip() == "CH"

    def test_roundtrip_preserves_validity(self, schema=None):
        """Test roundtrip (export -> import -> export) preserves validity."""
        if schema is None:
            schema = xmlschema.XMLSchema(str(ECH0010_XSD_PATH))

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

        # Export to XML
        xml1 = original.to_xml()
        xml_str1 = ET.tostring(xml1, encoding='unicode')
        assert schema.is_valid(xml_str1)

        # Import from XML
        parsed = ECH0010MailAddress.from_xml(xml1)

        # Export again
        xml2 = parsed.to_xml()
        xml_str2 = ET.tostring(xml2, encoding='unicode')
        assert schema.is_valid(xml_str2)

    def test_real_world_swiss_addresses(self, schema=None):
        """Test real-world Swiss address scenarios."""
        if schema is None:
            schema = xmlschema.XMLSchema(str(ECH0010_XSD_PATH))

        # Scenario 1: Rural address with dwelling number
        addr1 = ECH0010MailAddress(
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
        xml_str = ET.tostring(addr1.to_xml(), encoding='unicode')
        assert schema.is_valid(xml_str)

        # Scenario 2: Urban address with locality
        addr2 = ECH0010MailAddress(
            person=ECH0010PersonMailAddressInfo(last_name="Schmidt"),
            address_information=ECH0010AddressInformation(
                street="Bahnhofstrasse",
                house_number="100",
                locality="Zürich-Oerlikon",
                town="Zürich",
                swiss_zip_code=8050,
                country="CH"
            )
        )
        xml_str = ET.tostring(addr2.to_xml(), encoding='unicode')
        assert schema.is_valid(xml_str)

        # Scenario 3: Municipality with PO box
        addr3 = ECH0010MailAddress(
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
        xml_str = ET.tostring(addr3.to_xml(), encoding='unicode')
        assert schema.is_valid(xml_str)
