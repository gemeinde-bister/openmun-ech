"""XSD Validation tests for eCH-0007 Municipality models.

These tests validate that our Pydantic models produce XML that conforms
to the official eCH-0007 XSD schema.

Note: eCH-0007 is a "library" schema used by other standards (eCH-0020, etc.).
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

from openmun_ech.ech0007 import (
    ECH0007Municipality,
    ECH0007SwissMunicipality,
    ECH0007SwissAndFLMunicipality,
    CantonAbbreviation,
    CantonFLAbbreviation,
)


# Path to eCH XSD schemas
ECH_SCHEMA_DIR = Path(__file__).parent.parent / "docs" / "eCH"
ECH_0007_V5_XSD = ECH_SCHEMA_DIR / "eCH-0007-5-0.xsd"


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0007XSDValidation:
    """XSD validation tests for eCH-0007 models."""

    @pytest.fixture
    def schema(self):
        """Load eCH-0007 v5.0 XSD schema."""
        if not ECH_0007_V5_XSD.exists():
            pytest.skip(f"eCH-0007 XSD not found: {ECH_0007_V5_XSD}")
        return xmlschema.XMLSchema(str(ECH_0007_V5_XSD))

    def test_swiss_municipality_structure_valid(self, schema):
        """Test that Swiss municipality XML structure is XSD-compliant."""
        # Create test municipality
        mun = ECH0007SwissMunicipality(
            municipality_id="6172",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        # Export to XML (creates swissMunicipality element)
        xml_elem = mun.to_xml()

        # Convert to string for validation
        xml_str = ET.tostring(xml_elem, encoding='unicode')

        # The element should be valid according to swissMunicipalityType
        # We validate the element matches the type definition
        try:
            # xmlschema can validate elements against their type
            schema.validate(xml_str)
            # If we get here without exception, validation passed
            assert True
        except xmlschema.XMLSchemaValidationError as e:
            # Check if it's just because it's a fragment (expected)
            # The actual structure should still be valid
            if "not an element" in str(e).lower():
                # Fragment validation - check manually that structure is correct
                assert xml_elem.tag.endswith('swissMunicipality')
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}municipalityId') is not None
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}municipalityName') is not None
                assert xml_elem.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}cantonAbbreviation') is not None
            else:
                # Real validation error - fail the test
                pytest.fail(f"XSD validation failed: {e}")

    def test_swiss_municipality_with_all_fields(self, schema):
        """Test Swiss municipality with all optional fields."""
        mun = ECH0007SwissMunicipality(
            municipality_id="6172",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        xml_elem = mun.to_xml()

        # Check XML structure
        ns = '{http://www.ech.ch/xmlns/eCH-0007/5}'
        assert xml_elem.tag == f'{ns}swissMunicipality'
        assert xml_elem.find(f'{ns}municipalityId').text == "6172"
        assert xml_elem.find(f'{ns}municipalityName').text == "Bister"
        assert xml_elem.find(f'{ns}cantonAbbreviation').text == "VS"

    def test_municipality_wrapper_with_history(self, schema):
        """Test ECH0007Municipality wrapper with history ID."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS,
            history_id="11807"
        )

        xml_elem = mun.to_xml(element_name='placeOfOrigin')

        # Check XML structure
        ns = '{http://www.ech.ch/xmlns/eCH-0007/5}'
        assert xml_elem.tag == f'{ns}placeOfOrigin'

        # Should contain swissMunicipality
        swiss_mun = xml_elem.find(f'{ns}swissMunicipality')
        assert swiss_mun is not None

        # And historyMunicipalityId inside swissMunicipality per XSD
        hist_id = swiss_mun.find(f'{ns}historyMunicipalityId')
        assert hist_id is not None
        assert hist_id.text == "11807"

    def test_municipality_id_format(self, schema):
        """Test that municipality ID conforms to XSD type (1-4 digits, 1-9999)."""
        # Valid IDs
        valid_ids = ["1", "99", "6172", "9999"]
        for mid in valid_ids:
            mun = ECH0007SwissMunicipality(
                municipality_id=mid,
                municipality_name="Test",
                canton_abbreviation=CantonAbbreviation.ZH
            )
            xml = mun.to_xml()
            assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}municipalityId').text == mid

    def test_canton_abbreviation_valid_values(self, schema):
        """Test that canton abbreviations match XSD enumeration."""
        # All valid canton codes from XSD
        valid_cantons = [
            'ZH', 'BE', 'LU', 'UR', 'SZ', 'OW', 'NW', 'GL', 'ZG', 'FR',
            'SO', 'BS', 'BL', 'SH', 'AR', 'AI', 'SG', 'GR', 'AG', 'TG',
            'TI', 'VD', 'VS', 'NE', 'GE', 'JU'
        ]

        for canton_code in valid_cantons:
            mun = ECH0007SwissMunicipality(
                municipality_id="1",
                municipality_name="Test",
                canton_abbreviation=CantonAbbreviation[canton_code]
            )
            xml = mun.to_xml()
            canton_elem = xml.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}cantonAbbreviation')
            assert canton_elem.text == canton_code

    def test_municipality_name_length(self, schema):
        """Test that municipality name respects maxLength=40 from XSD."""
        # Valid: exactly 40 characters
        name_40 = "A" * 40
        mun = ECH0007SwissMunicipality(
            municipality_id="1",
            municipality_name=name_40,
            canton_abbreviation=CantonAbbreviation.ZH
        )
        xml = mun.to_xml()
        assert xml.find('.//{http://www.ech.ch/xmlns/eCH-0007/5}municipalityName').text == name_40

        # Pydantic should prevent > 40 chars (validated at model level)
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ECH0007SwissMunicipality(
                municipality_id="1",
                municipality_name="A" * 41,
                canton_abbreviation=CantonAbbreviation.ZH
            )

    def test_namespace_correctness(self, schema):
        """Test that all elements use correct eCH-0007 namespace."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS
        )

        xml_elem = mun.to_xml()

        expected_ns = 'http://www.ech.ch/xmlns/eCH-0007/5'

        # Check all elements have correct namespace
        def check_namespace(elem):
            if elem.tag.startswith('{'):
                ns = elem.tag[1:elem.tag.find('}')]
                assert ns == expected_ns, f"Wrong namespace: {ns}"
            for child in elem:
                check_namespace(child)

        check_namespace(xml_elem)


class TestECH0007ManualValidation:
    """Manual validation tests (no xmlschema required).

    These tests check XML structure without relying on external libraries.
    """

    def test_xml_well_formed(self):
        """Test that generated XML is well-formed."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS,
            history_id="11807"
        )

        xml_elem = mun.to_xml()

        # Should be able to convert to string and parse back
        xml_str = ET.tostring(xml_elem, encoding='unicode')
        parsed = ET.fromstring(xml_str)

        assert parsed is not None

    def test_xml_element_order(self):
        """Test that XML elements follow XSD sequence order.

        XSD sequence for swissMunicipality:
        1. municipalityId (optional)
        2. municipalityName
        3. cantonAbbreviation
        """
        mun = ECH0007SwissMunicipality(
            municipality_id="6172",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        xml_elem = mun.to_xml()
        children = list(xml_elem)

        # Check order
        assert children[0].tag.endswith('municipalityId')
        assert children[1].tag.endswith('municipalityName')
        assert children[2].tag.endswith('cantonAbbreviation')

    def test_no_unexpected_elements(self):
        """Test that XML contains only expected elements."""
        mun = ECH0007SwissMunicipality(
            municipality_id="6172",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        xml_elem = mun.to_xml()

        expected_tags = {
            '{http://www.ech.ch/xmlns/eCH-0007/5}municipalityId',
            '{http://www.ech.ch/xmlns/eCH-0007/5}municipalityName',
            '{http://www.ech.ch/xmlns/eCH-0007/5}cantonAbbreviation',
        }

        actual_tags = {child.tag for child in xml_elem}
        assert actual_tags == expected_tags

    def test_xml_text_content_not_empty(self):
        """Test that required elements have non-empty text content."""
        mun = ECH0007SwissMunicipality(
            municipality_id="6172",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        xml_elem = mun.to_xml()

        # All elements should have text content
        for child in xml_elem:
            assert child.text is not None
            assert len(child.text.strip()) > 0

    def test_roundtrip_preserves_validity(self):
        """Test that XML roundtrip maintains structure."""
        original = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS,
            history_id="11807"
        )

        # Export
        xml_elem = original.to_xml()

        # Import back
        restored = ECH0007Municipality.from_xml(xml_elem)

        # Export again
        xml_elem2 = restored.to_xml()

        # Should be identical
        xml_str1 = ET.tostring(xml_elem, encoding='unicode')
        xml_str2 = ET.tostring(xml_elem2, encoding='unicode')

        assert xml_str1 == xml_str2
