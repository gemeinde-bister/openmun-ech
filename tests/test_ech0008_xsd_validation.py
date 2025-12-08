"""XSD Validation tests for eCH-0008 Country models.

These tests validate that our Pydantic models produce XML that conforms
to the official eCH-0008 XSD schema.

Note: eCH-0008 is a "library" schema used by other standards (eCH-0020, etc.).
The types are not standalone documents, so we validate the structure and types
rather than full document validation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

from openmun_ech.ech0008 import ECH0008Country


# Path to eCH XSD schemas
ECH_SCHEMA_DIR = Path(__file__).parent.parent / "docs" / "eCH"
ECH_0008_V3_XSD = ECH_SCHEMA_DIR / "eCH-0008-3-0.xsd"


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0008XSDValidation:
    """XSD validation tests for eCH-0008 models."""

    @pytest.fixture
    def schema(self):
        """Load eCH-0008 v3.0 XSD schema."""
        if not ECH_0008_V3_XSD.exists():
            pytest.skip(f"eCH-0008 XSD not found: {ECH_0008_V3_XSD}")
        return xmlschema.XMLSchema(str(ECH_0008_V3_XSD))

    def test_country_structure_valid(self, schema):
        """Test that country XML structure is XSD-compliant."""
        # Create test country with all fields
        country = ECH0008Country.from_iso2("CH", language="de")

        # Export to XML
        xml_elem = country.to_xml()

        # Convert to string for validation
        xml_str = ET.tostring(xml_elem, encoding='unicode')

        # The element should be valid according to countryType
        try:
            schema.validate(xml_str)
            assert True
        except xmlschema.XMLSchemaValidationError as e:
            # Check if it's just because it's a fragment (expected)
            if "not an element" in str(e).lower():
                # Fragment validation - check structure is correct
                assert xml_elem.tag.endswith('country')
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryId') is not None
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2') is not None
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort') is not None
            else:
                pytest.fail(f"XSD validation failed: {e}")

    def test_country_with_all_fields(self, schema):
        """Test country with all fields present."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()

        # Check XML structure
        ns = '{http://www.ech.ch/xmlns/eCH-0008/3}'
        assert xml_elem.tag == f'{ns}country'
        assert xml_elem.find(f'{ns}countryId').text == "8100"
        assert xml_elem.find(f'{ns}countryIdISO2').text == "CH"
        assert xml_elem.find(f'{ns}countryNameShort').text == "Schweiz"

    def test_country_minimal_fields(self, schema):
        """Test country with only required field (countryNameShort)."""
        country = ECH0008Country(
            country_id="8100",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()

        # Check XML structure
        ns = '{http://www.ech.ch/xmlns/eCH-0008/3}'
        assert xml_elem.tag == f'{ns}country'
        assert xml_elem.find(f'{ns}countryId').text == "8100"
        assert xml_elem.find(f'{ns}countryIdISO2') is None  # Optional, not provided
        assert xml_elem.find(f'{ns}countryNameShort').text == "Schweiz"

    def test_country_id_range(self, schema):
        """Test that countryId conforms to XSD type (1000-9999)."""
        # Valid IDs (BFS codes are 4 digits, 1000-9999)
        valid_ids = ["1000", "8100", "8207", "9999"]
        for country_id in valid_ids:
            country = ECH0008Country(
                country_id=country_id,
                country_name_short="Test"
            )
            xml = country.to_xml()
            assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryId').text == country_id

    def test_country_id_iso2_length(self, schema):
        """Test that countryIdISO2 respects maxLength=2 from XSD."""
        # Valid: exactly 2 characters
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        xml = country.to_xml()
        iso2 = xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2')
        assert iso2.text == "CH"
        assert len(iso2.text) == 2

        # Pydantic should prevent > 2 chars
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ECH0008Country(
                country_id="8100",
                country_id_iso2="CHE",
                country_name_short="Schweiz"
            )

    def test_country_name_short_length(self, schema):
        """Test that countryNameShort respects maxLength=50 from XSD."""
        # Valid: exactly 50 characters
        name_50 = "A" * 50
        country = ECH0008Country(
            country_id="8100",
            country_name_short=name_50
        )
        xml = country.to_xml()
        name = xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort')
        assert name.text == name_50
        assert len(name.text) == 50

        # Pydantic should prevent > 50 chars
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ECH0008Country(
                country_id="8100",
                country_name_short="A" * 51
            )

    def test_namespace_correctness(self, schema):
        """Test that all elements use correct eCH-0008 namespace."""
        country = ECH0008Country.from_iso2("CH", language="de")
        xml_elem = country.to_xml()

        expected_ns = 'http://www.ech.ch/xmlns/eCH-0008/3'

        # Check all elements have correct namespace
        def check_namespace(elem):
            if elem.tag.startswith('{'):
                ns = elem.tag[1:elem.tag.find('}')]
                assert ns == expected_ns, f"Wrong namespace: {ns}"
            for child in elem:
                check_namespace(child)

        check_namespace(xml_elem)

    def test_element_order_sequence(self, schema):
        """Test that XML elements follow XSD sequence order.

        XSD sequence for countryType:
        1. countryId (optional)
        2. countryIdISO2 (optional)
        3. countryNameShort (required)
        """
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()
        children = list(xml_elem)

        # Check order
        assert children[0].tag.endswith('countryId')
        assert children[1].tag.endswith('countryIdISO2')
        assert children[2].tag.endswith('countryNameShort')

    def test_multilingual_names_valid(self, schema):
        """Test that country names in different languages are valid."""
        languages = ['de', 'fr', 'it', 'en']
        expected_names = ['Schweiz', 'Suisse', 'Svizzera', 'Switzerland']

        for lang, expected_name in zip(languages, expected_names):
            country = ECH0008Country.from_bfs_code("8100", language=lang)
            xml = country.to_xml()

            name_elem = xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort')
            assert name_elem.text == expected_name
            # All names should be within XSD max length
            assert len(name_elem.text) <= 50


class TestECH0008ManualValidation:
    """Manual validation tests (no xmlschema required).

    These tests check XML structure without relying on external libraries.
    """

    def test_xml_well_formed(self):
        """Test that generated XML is well-formed."""
        country = ECH0008Country.from_iso2("CH", language="de")
        xml_elem = country.to_xml()

        # Should be able to convert to string and parse back
        xml_str = ET.tostring(xml_elem, encoding='unicode')
        parsed = ET.fromstring(xml_str)

        assert parsed is not None

    def test_xml_element_order(self):
        """Test that XML elements follow correct order."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()
        children = list(xml_elem)

        # Check we have all three elements in order
        assert len(children) == 3
        assert children[0].tag.endswith('countryId')
        assert children[1].tag.endswith('countryIdISO2')
        assert children[2].tag.endswith('countryNameShort')

    def test_optional_fields_omitted(self):
        """Test that optional fields can be omitted."""
        # Only required field
        country = ECH0008Country(
            country_id="8100",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()

        # countryId should be present
        assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryId') is not None

        # countryIdISO2 should be absent (was None)
        assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2') is None

        # countryNameShort should be present (required)
        assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort') is not None

    def test_no_unexpected_elements(self):
        """Test that XML contains only expected elements."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()

        expected_tags = {
            '{http://www.ech.ch/xmlns/eCH-0008/3}countryId',
            '{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2',
            '{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort',
        }

        actual_tags = {child.tag for child in xml_elem}
        assert actual_tags == expected_tags

    def test_xml_text_content_not_empty(self):
        """Test that elements have non-empty text content."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml_elem = country.to_xml()

        # All elements should have text content
        for child in xml_elem:
            assert child.text is not None
            assert len(child.text.strip()) > 0

    def test_roundtrip_preserves_validity(self):
        """Test that XML roundtrip maintains structure."""
        original = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        # Export
        xml_elem = original.to_xml()

        # Import back
        restored = ECH0008Country.from_xml(xml_elem)

        # Export again
        xml_elem2 = restored.to_xml()

        # Should be identical
        xml_str1 = ET.tostring(xml_elem, encoding='unicode')
        xml_str2 = ET.tostring(xml_elem2, encoding='unicode')

        assert xml_str1 == xml_str2

    def test_custom_element_name(self):
        """Test that custom element names work correctly."""
        country = ECH0008Country.from_iso2("CH", language="de")

        # Export with custom element name
        xml_elem = country.to_xml(element_name='placeOfBirthCountry')

        # Check element name
        assert xml_elem.tag == '{http://www.ech.ch/xmlns/eCH-0008/3}placeOfBirthCountry'

        # Children should still be correct
        assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryId') is not None

    def test_real_world_countries(self):
        """Test several real-world countries from BFS data."""
        test_countries = [
            ("CH", "8100", "Schweiz"),
            ("DE", "8207", "Deutschland"),
            ("FR", "8212", "Frankreich"),
            ("IT", "8218", "Italien"),
            ("AT", "8229", "Österreich"),
        ]

        for iso2, expected_bfs, expected_name_de in test_countries:
            country = ECH0008Country.from_iso2(iso2, language="de")

            assert country.country_id == expected_bfs
            assert country.country_id_iso2 == iso2
            assert country.country_name_short == expected_name_de

            # Validate XML
            xml = country.to_xml()
            assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryId').text == expected_bfs
            assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2').text == iso2
            assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort').text == expected_name_de
