"""XSD validation tests for eCH-0044 Person Identification models.

These tests validate that our Pydantic models generate XML that conforms
to the official eCH-0044 v4.1 XSD schema.
"""

import xml.etree.ElementTree as ET
import pytest
from datetime import date
from pathlib import Path

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

from openmun_ech.ech0044 import (
    ECH0044DatePartiallyKnown,
    ECH0044NamedPersonId,
    ECH0044PersonIdentification,
)

# Path to eCH-0044 XSD schema
XSD_PATH = Path(__file__).parent.parent / 'docs' / 'eCH' / 'eCH-0044-4-1.xsd'

# Skip all tests if xmlschema not installed
pytestmark = pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")


@pytest.fixture(scope='module')
def schema():
    """Load eCH-0044 XSD schema."""
    if not XSD_PATH.exists():
        pytest.skip(f"XSD schema not found at {XSD_PATH}")
    return xmlschema.XMLSchema(str(XSD_PATH))


class TestECH0044PersonIdentificationXSD:
    """XSD validation tests for PersonIdentification."""

    def test_minimal_person_validates(self, schema):
        """Test that minimal person identification validates against XSD."""
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
        xml_string = ET.tostring(xml, encoding='unicode')

        # Wrap in personIdentificationRoot for XSD validation
        wrapped = f"""
        <personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">
            {xml_string}
        </personIdentificationRoot>
        """
        schema.validate(wrapped)

    def test_full_person_with_vn_validates(self, schema):
        """Test that person identification with VN validates against XSD."""
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
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_original_name_validates(self, schema):
        """Test that person identification with original name validates against XSD."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_other_ids_validates(self, schema):
        """Test that person identification with other IDs validates against XSD."""
        person = ECH0044PersonIdentification(
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
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_eu_ids_validates(self, schema):
        """Test that person identification with EU IDs validates against XSD."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            eu_person_id=[
                ECH0044NamedPersonId(
                    person_id_category="eu.passport",
                    person_id="DE123456789"
                )
            ],
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_all_fields_validates(self, schema):
        """Test that person identification with all fields validates against XSD."""
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
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_partially_known_birth_year_month_validates(self, schema):
        """Test that person with year-month birth date validates against XSD."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_year_month(1990, 5)
        )
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_partially_known_birth_year_validates(self, schema):
        """Test that person with year-only birth date validates against XSD."""
        person = ECH0044PersonIdentification(
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Anna",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_year(1990)
        )
        xml = person.to_xml()
        xml_string = ET.tostring(xml, encoding='unicode')

        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)

    def test_person_with_all_sex_values_validates(self, schema):
        """Test that person identification with all sex values validates against XSD."""
        for sex_value in ["1", "2", "3"]:
            person = ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex=sex_value,
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            )
            xml = person.to_xml()
            xml_string = ET.tostring(xml, encoding='unicode')

            wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
            schema.validate(wrapped)

    def test_element_order_is_correct(self, schema):
        """Test that XML element order matches XSD sequence requirements."""
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
            official_name="Meier",
            first_name="Anna",
            original_name="Schmidt",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
        )
        xml = person.to_xml()

        # XSD requires specific order:
        # vn?, localPersonId, otherPersonId*, euPersonId*,
        # officialName, firstName, originalName?, sex, dateOfBirth

        children = list(xml)
        tags = [child.tag.split('}')[-1] for child in children]

        # Check order
        expected_order = [
            'vn',
            'localPersonId',
            'otherPersonId',
            'euPersonId',
            'officialName',
            'firstName',
            'originalName',
            'sex',
            'dateOfBirth'
        ]

        # Filter to only tags that are present
        present_tags = [tag for tag in expected_order if tag in tags]
        actual_order = [tag for tag in tags if tag in expected_order]

        assert actual_order == present_tags, f"Element order mismatch: {actual_order} != {present_tags}"

        # Validate against XSD (final check)
        xml_string = ET.tostring(xml, encoding='unicode')
        wrapped = f'<personIdentificationRoot xmlns="http://www.ech.ch/xmlns/eCH-0044/4">{xml_string}</personIdentificationRoot>'
        schema.validate(wrapped)
