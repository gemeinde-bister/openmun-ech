"""Tests for eCH-0008 Country Pydantic models."""

import xml.etree.ElementTree as ET
import pytest
from pydantic import ValidationError

from openmun_ech.ech0008 import ECH0008Country, ECH0008CountryShort


class TestECH0008Country:
    """Test eCH-0008 country model."""

    def test_create_valid_country(self):
        """Test creating valid country."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        assert country.country_id == "8100"
        assert country.country_id_iso2 == "CH"
        assert country.country_name_short == "Schweiz"

    def test_create_country_without_iso2(self):
        """Test creating country without ISO2 code (optional)."""
        country = ECH0008Country(
            country_id="8100",
            country_name_short="Schweiz"
        )
        assert country.country_id == "8100"
        assert country.country_id_iso2 is None
        assert country.country_name_short == "Schweiz"

    def test_validate_country_id_numeric(self):
        """Test country ID must be numeric."""
        with pytest.raises(ValidationError, match="Country ID must be numeric"):
            ECH0008Country(
                country_id="ABCD",
                country_name_short="Test"
            )

    def test_validate_country_id_length(self):
        """Test country ID must be exactly 4 digits."""
        # Too short
        with pytest.raises(ValidationError, match="String should have at least 4 characters"):
            ECH0008Country(
                country_id="810",
                country_name_short="Test"
            )

        # Too long
        with pytest.raises(ValidationError, match="String should have at most 4 characters"):
            ECH0008Country(
                country_id="81000",
                country_name_short="Test"
            )

    def test_validate_iso2_length(self):
        """Test ISO2 code must be 2 characters."""
        with pytest.raises(ValidationError, match="String should have at most 2 characters"):
            ECH0008Country(
                country_id="8100",
                country_id_iso2="CHE",
                country_name_short="Schweiz"
            )

    def test_iso2_uppercase_conversion(self):
        """Test ISO2 code is converted to uppercase."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="ch",
            country_name_short="Schweiz"
        )
        assert country.country_id_iso2 == "CH"

    def test_from_bfs_code_switzerland(self):
        """Test creating country from BFS code."""
        country = ECH0008Country.from_bfs_code("8100", language="de")
        assert country.country_id == "8100"
        assert country.country_id_iso2 == "CH"
        assert country.country_name_short == "Schweiz"

    def test_from_bfs_code_different_languages(self):
        """Test creating country with different languages."""
        # German
        country_de = ECH0008Country.from_bfs_code("8100", language="de")
        assert country_de.country_name_short == "Schweiz"

        # French
        country_fr = ECH0008Country.from_bfs_code("8100", language="fr")
        assert country_fr.country_name_short == "Suisse"

        # Italian
        country_it = ECH0008Country.from_bfs_code("8100", language="it")
        assert country_it.country_name_short == "Svizzera"

        # English
        country_en = ECH0008Country.from_bfs_code("8100", language="en")
        assert country_en.country_name_short == "Switzerland"

    def test_from_bfs_code_invalid(self):
        """Test creating country from invalid BFS code."""
        with pytest.raises(ValueError, match="Unknown BFS country code"):
            ECH0008Country.from_bfs_code("9999")

    def test_from_iso2_switzerland(self):
        """Test creating country from ISO2 code."""
        country = ECH0008Country.from_iso2("CH", language="de")
        assert country.country_id == "8100"
        assert country.country_id_iso2 == "CH"
        assert country.country_name_short == "Schweiz"

    def test_from_iso2_case_insensitive(self):
        """Test ISO2 lookup is case-insensitive."""
        country = ECH0008Country.from_iso2("ch", language="de")
        assert country.country_id_iso2 == "CH"

    def test_from_iso2_invalid(self):
        """Test creating country from invalid ISO2 code."""
        with pytest.raises(ValueError, match="Unknown ISO2 country code"):
            ECH0008Country.from_iso2("XX")


    def test_to_xml(self):
        """Test XML export."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml = country.to_xml()

        # Check structure
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0008/3}country'

        # Check country ID
        country_id = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryId')
        assert country_id is not None
        assert country_id.text == "8100"

        # Check ISO2
        iso2 = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2')
        assert iso2 is not None
        assert iso2.text == "CH"

        # Check name
        name = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort')
        assert name is not None
        assert name.text == "Schweiz"

    def test_to_xml_without_iso2(self):
        """Test XML export without ISO2 code."""
        country = ECH0008Country(
            country_id="8100",
            country_name_short="Schweiz"
        )

        xml = country.to_xml()

        # ISO2 should not be present
        iso2 = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2')
        assert iso2 is None

        # But other fields should be present
        country_id = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryId')
        assert country_id is not None

    def test_to_xml_with_parent(self):
        """Test XML export with parent element."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        parent = ET.Element('test')
        country.to_xml(parent)

        # Check child was added
        country_elem = parent.find('{http://www.ech.ch/xmlns/eCH-0008/3}country')
        assert country_elem is not None

    def test_to_xml_custom_element_name(self):
        """Test XML export with custom element name."""
        country = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        xml = country.to_xml(element_name='placeOfBirthCountry')
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0008/3}placeOfBirthCountry'

    def test_from_xml(self):
        """Test XML import."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
            <countryId>8100</countryId>
            <countryIdISO2>CH</countryIdISO2>
            <countryNameShort>Schweiz</countryNameShort>
        </country>
        """
        elem = ET.fromstring(xml_str)
        country = ECH0008Country.from_xml(elem)

        assert country.country_id == "8100"
        assert country.country_id_iso2 == "CH"
        assert country.country_name_short == "Schweiz"

    def test_from_xml_without_iso2(self):
        """Test XML import without ISO2 code."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
            <countryId>8100</countryId>
            <countryNameShort>Schweiz</countryNameShort>
        </country>
        """
        elem = ET.fromstring(xml_str)
        country = ECH0008Country.from_xml(elem)

        assert country.country_id == "8100"
        assert country.country_id_iso2 is None
        assert country.country_name_short == "Schweiz"

    def test_from_xml_missing_country_id(self):
        """Test XML import succeeds with missing country ID (optional per XSD)."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
            <countryNameShort>Schweiz</countryNameShort>
        </country>
        """
        elem = ET.fromstring(xml_str)

        # Should succeed - country_id is optional per XSD
        country = ECH0008Country.from_xml(elem)
        assert country.country_id is None
        assert country.country_name_short == "Schweiz"

    def test_from_xml_missing_name(self):
        """Test XML import fails with missing name."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
            <countryId>8100</countryId>
        </country>
        """
        elem = ET.fromstring(xml_str)

        with pytest.raises(ValueError, match="Missing required field: countryNameShort"):
            ECH0008Country.from_xml(elem)

    def test_roundtrip_xml(self):
        """Test XML export and import roundtrip."""
        original = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        # Export to XML
        xml = original.to_xml()

        # Import from XML
        restored = ECH0008Country.from_xml(xml)

        # Should be identical
        assert restored.country_id == original.country_id
        assert restored.country_id_iso2 == original.country_id_iso2
        assert restored.country_name_short == original.country_name_short

    def test_roundtrip_xml_without_iso2(self):
        """Test XML roundtrip without ISO2 code."""
        original = ECH0008Country(
            country_id="8100",
            country_name_short="Schweiz"
        )

        xml = original.to_xml()
        restored = ECH0008Country.from_xml(xml)

        assert restored.country_id == original.country_id
        assert restored.country_id_iso2 is None
        assert restored.country_name_short == original.country_name_short


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_nationality_switzerland(self):
        """Test Swiss nationality scenario."""
        # Person with Swiss nationality
        country = ECH0008Country.from_iso2("CH", language="de")

        # Should export correctly
        xml = country.to_xml()
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryId').text == "8100"

    def test_multiple_nationalities(self):
        """Test person with multiple nationalities."""
        countries = [
            ECH0008Country.from_iso2("CH", language="de"),
            ECH0008Country.from_iso2("IT", language="de"),
        ]

        assert len(countries) == 2
        assert countries[0].country_id == "8100"
        assert countries[1].country_id == "8218"  # Italy BFS code

    def test_foreign_birth_place(self):
        """Test foreign birth place scenario."""
        # Person born in Germany
        birth_country = ECH0008Country.from_iso2("DE", language="de")

        # Export as part of birth info
        parent = ET.Element('birthInfo')
        birth_country.to_xml(parent, element_name='placeOfBirth')

        birth_elem = parent.find('{http://www.ech.ch/xmlns/eCH-0008/3}placeOfBirth')
        assert birth_elem is not None

    def test_all_languages_for_same_country(self):
        """Test same country in different languages."""
        languages = ['de', 'fr', 'it', 'en']
        expected_names = ['Schweiz', 'Suisse', 'Svizzera', 'Switzerland']

        for lang, expected_name in zip(languages, expected_names):
            country = ECH0008Country.from_bfs_code("8100", language=lang)
            assert country.country_name_short == expected_name
            assert country.country_id == "8100"  # Same BFS code


class TestECH0008CountryShort:
    """Test eCH-0008 country short form model (countryShortType)."""

    def test_create_valid_country_short(self):
        """Test creating valid country short form."""
        country = ECH0008CountryShort(country_name_short="Schweiz")
        assert country.country_name_short == "Schweiz"

    def test_from_country_name(self):
        """Test creating country short from name."""
        country = ECH0008CountryShort.from_country_name("Schweiz")
        assert country.country_name_short == "Schweiz"

    def test_from_country_name_strips_whitespace(self):
        """Test that country name is stripped of whitespace."""
        country = ECH0008CountryShort.from_country_name("  Schweiz  ")
        assert country.country_name_short == "Schweiz"

    def test_from_country_name_empty(self):
        """Test that empty country name raises error."""
        with pytest.raises(ValueError, match="Country name cannot be empty"):
            ECH0008CountryShort.from_country_name("")

    def test_from_country_name_whitespace_only(self):
        """Test that whitespace-only country name raises error."""
        with pytest.raises(ValueError, match="Country name cannot be empty"):
            ECH0008CountryShort.from_country_name("   ")

    def test_from_country_name_too_long(self):
        """Test that country name longer than 50 chars raises error."""
        long_name = "A" * 51
        with pytest.raises(ValueError, match="Country name too long"):
            ECH0008CountryShort.from_country_name(long_name)

    def test_validate_name_length(self):
        """Test country name length validation (1-50 chars per XSD)."""
        # Valid: exactly 50 characters
        name_50 = "A" * 50
        country = ECH0008CountryShort(country_name_short=name_50)
        assert country.country_name_short == name_50

        # Invalid: 51 characters
        with pytest.raises(ValidationError):
            ECH0008CountryShort(country_name_short="A" * 51)

        # Invalid: empty string
        with pytest.raises(ValidationError):
            ECH0008CountryShort(country_name_short="")

    def test_to_xml(self):
        """Test XML export of country short form."""
        country = ECH0008CountryShort(country_name_short="Schweiz")
        xml = country.to_xml()

        # Check structure
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0008/3}country'

        # Check name (only field for countryShortType)
        name = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort')
        assert name is not None
        assert name.text == "Schweiz"

        # Check that countryId and countryIdISO2 are NOT present
        country_id = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryId')
        assert country_id is None

        iso2 = xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryIdISO2')
        assert iso2 is None

    def test_to_xml_with_parent(self):
        """Test XML export with parent element."""
        country = ECH0008CountryShort(country_name_short="Schweiz")
        parent = ET.Element('test')
        country.to_xml(parent)

        # Check child was added
        country_elem = parent.find('{http://www.ech.ch/xmlns/eCH-0008/3}country')
        assert country_elem is not None

    def test_to_xml_custom_element_name(self):
        """Test XML export with custom element name."""
        country = ECH0008CountryShort(country_name_short="Schweiz")
        xml = country.to_xml(element_name='nationality')
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0008/3}nationality'

    def test_from_xml(self):
        """Test XML import of country short form."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
            <countryNameShort>Schweiz</countryNameShort>
        </country>
        """
        elem = ET.fromstring(xml_str)
        country = ECH0008CountryShort.from_xml(elem)

        assert country.country_name_short == "Schweiz"

    def test_from_xml_missing_name(self):
        """Test XML import fails with missing name."""
        xml_str = """
        <country xmlns="http://www.ech.ch/xmlns/eCH-0008/3">
        </country>
        """
        elem = ET.fromstring(xml_str)

        with pytest.raises(ValueError, match="Missing required field: countryNameShort"):
            ECH0008CountryShort.from_xml(elem)

    def test_roundtrip_xml(self):
        """Test XML export and import roundtrip."""
        original = ECH0008CountryShort(country_name_short="Schweiz")

        # Export to XML
        xml = original.to_xml()

        # Import from XML
        restored = ECH0008CountryShort.from_xml(xml)

        # Should be identical
        assert restored.country_name_short == original.country_name_short


class TestCountryShortVsFullComparison:
    """Test comparison between countryShortType and countryType.

    These tests verify the architectural difference between the two types:
    - countryShortType: Only country name (simpler)
    - countryType: BFS code + ISO code + name (full identification)
    """

    def test_short_form_has_only_name(self):
        """Test that short form only contains name field."""
        short = ECH0008CountryShort(country_name_short="Schweiz")

        # Should have exactly one field
        assert hasattr(short, 'country_name_short')
        assert not hasattr(short, 'country_id')
        assert not hasattr(short, 'country_id_iso2')

    def test_full_form_has_all_fields(self):
        """Test that full form has all three fields."""
        full = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        assert hasattr(full, 'country_name_short')
        assert hasattr(full, 'country_id')
        assert hasattr(full, 'country_id_iso2')

    def test_xml_structure_difference(self):
        """Test that XML output differs between short and full types."""
        short = ECH0008CountryShort(country_name_short="Schweiz")
        full = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )

        short_xml = short.to_xml()
        full_xml = full.to_xml()

        # Short form should have only countryNameShort
        assert len(list(short_xml)) == 1

        # Full form should have 3 children
        assert len(list(full_xml)) == 3

    def test_use_case_simple_name_only(self):
        """Test use case: When only country name is needed.

        From PDF: 'Je nach Aufgabenstellung können Schnittstellenstandards
        welche den eCH-0008 importieren, den countryType oder den
        countryShortType verwenden.'
        """
        # Scenario: Display nationality in UI, no need for codes
        nationality = ECH0008CountryShort(country_name_short="Schweiz")

        # Simple XML for display purposes
        xml = nationality.to_xml()
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0008/3}countryNameShort').text == "Schweiz"

