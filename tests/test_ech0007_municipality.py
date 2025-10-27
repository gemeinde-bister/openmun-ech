"""Tests for eCH-0007 Municipality Pydantic models (POC)."""

import xml.etree.ElementTree as ET
import pytest
from pydantic import ValidationError

from openmun_ech.ech0007 import (
    ECH0007Municipality,
    ECH0007SwissMunicipality,
    ECH0007SwissAndFLMunicipality,
    CantonAbbreviation,
    CantonFLAbbreviation,
)


class TestCantonAbbreviation:
    """Test Swiss canton enum."""

    def test_valid_cantons(self):
        """Test all valid canton abbreviations."""
        assert CantonAbbreviation.ZH.value == "ZH"
        assert CantonAbbreviation.BE.value == "BE"
        assert CantonAbbreviation.VS.value == "VS"

    def test_total_count(self):
        """Test we have all 26 cantons."""
        assert len(CantonAbbreviation) == 26


class TestECH0007SwissMunicipality:
    """Test Swiss municipality model."""

    def test_create_valid_municipality(self):
        """Test creating valid Swiss municipality."""
        mun = ECH0007SwissMunicipality(
            municipality_id="2310",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )
        assert mun.municipality_id == "2310"
        assert mun.municipality_name == "Bister"
        assert mun.canton_abbreviation == CantonAbbreviation.VS

    def test_validate_municipality_id_numeric(self):
        """Test municipality ID must be numeric."""
        with pytest.raises(ValidationError, match="Municipality ID must be numeric"):
            ECH0007SwissMunicipality(
                municipality_id="ABC",
                municipality_name="Test",
                canton_abbreviation=CantonAbbreviation.ZH
            )

    def test_validate_municipality_id_length(self):
        """Test municipality ID length limits."""
        # Too long (Pydantic catches this before custom validator)
        with pytest.raises(ValidationError, match="String should have at most 4 characters"):
            ECH0007SwissMunicipality(
                municipality_id="12345",
                municipality_name="Test",
                canton_abbreviation=CantonAbbreviation.ZH
            )

        # Valid 1-digit
        mun = ECH0007SwissMunicipality(
            municipality_id="1",
            municipality_name="Test",
            canton_abbreviation=CantonAbbreviation.ZH
        )
        assert mun.municipality_id == "1"

        # Valid 4-digit
        mun = ECH0007SwissMunicipality(
            municipality_id="2310",
            municipality_name="Test",
            canton_abbreviation=CantonAbbreviation.VS
        )
        assert mun.municipality_id == "2310"

    def test_validate_invalid_canton(self):
        """Test invalid canton abbreviation."""
        with pytest.raises(ValidationError):
            ECH0007SwissMunicipality(
                municipality_id="2310",
                municipality_name="Bister",
                canton_abbreviation="XX"  # Invalid
            )

    def test_to_xml(self):
        """Test export to XML."""
        mun = ECH0007SwissMunicipality(
            municipality_id="2310",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        elem = mun.to_xml()

        # Check element structure
        assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0007/5}swissMunicipality'

        # Check municipality ID
        mun_id = elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}municipalityId')
        assert mun_id is not None
        assert mun_id.text == "2310"

        # Check municipality name
        mun_name = elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}municipalityName')
        assert mun_name is not None
        assert mun_name.text == "Bister"

        # Check canton
        canton = elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}cantonAbbreviation')
        assert canton is not None
        assert canton.text == "VS"

    def test_from_xml(self):
        """Test import from XML."""
        xml_str = """
        <swissMunicipality xmlns="http://www.ech.ch/xmlns/eCH-0007/5">
            <municipalityId>2310</municipalityId>
            <municipalityName>Bister</municipalityName>
            <cantonAbbreviation>VS</cantonAbbreviation>
        </swissMunicipality>
        """
        elem = ET.fromstring(xml_str)
        mun = ECH0007SwissMunicipality.from_xml(elem)

        assert mun.municipality_id == "2310"
        assert mun.municipality_name == "Bister"
        assert mun.canton_abbreviation == CantonAbbreviation.VS

    def test_roundtrip_xml(self):
        """Test XML export -> import roundtrip."""
        original = ECH0007SwissMunicipality(
            municipality_id="2310",
            municipality_name="Bister",
            canton_abbreviation=CantonAbbreviation.VS
        )

        # Export to XML
        xml_elem = original.to_xml()

        # Import back
        restored = ECH0007SwissMunicipality.from_xml(xml_elem)

        # Verify match
        assert restored.municipality_id == original.municipality_id
        assert restored.municipality_name == original.municipality_name
        assert restored.canton_abbreviation == original.canton_abbreviation

    def test_from_xml_missing_fields(self):
        """Test import fails with missing required fields."""
        # Missing municipality name (the only required field per XSD)
        xml_str = """
        <swissMunicipality xmlns="http://www.ech.ch/xmlns/eCH-0007/5">
            <municipalityId>6172</municipalityId>
            <cantonAbbreviation>VS</cantonAbbreviation>
        </swissMunicipality>
        """
        elem = ET.fromstring(xml_str)
        with pytest.raises(ValueError, match="Missing required field: municipalityName"):
            ECH0007SwissMunicipality.from_xml(elem)


class TestECH0007Municipality:
    """Test Swiss municipality wrapper model."""

    def test_create_swiss_municipality(self):
        """Test creating Swiss municipality via factory method."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="2310",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS
        )

        assert mun.name == "Bister"
        assert mun.swiss_municipality is not None
        assert mun.swiss_municipality.municipality_id == "2310"
        assert mun.swiss_municipality.canton_abbreviation == CantonAbbreviation.VS

    def test_history_municipality_id(self):
        """Test history municipality ID for merged municipalities."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Goms",
            canton=CantonAbbreviation.VS,
            history_id="2310"  # Bister was merged into Goms
        )

        assert mun.history_municipality_id == "2310"

    def test_validate_history_id_format(self):
        """Test history ID validation."""
        # Invalid (non-numeric)
        with pytest.raises(ValidationError, match="History municipality ID must be numeric"):
            ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Goms",
                canton=CantonAbbreviation.VS,
                history_id="ABC"
            )

        # Invalid (too long - Pydantic catches this before custom validator)
        with pytest.raises(ValidationError, match="String should have at most 12 characters"):
            ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Goms",
                canton=CantonAbbreviation.VS,
                history_id="1234567890123"  # 13 digits
            )

    def test_to_xml_swiss(self):
        """Test export Swiss municipality to XML."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="2310",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS,
            history_id="2310"
        )

        elem = mun.to_xml(element_name='placeOfOrigin')

        # Check container
        assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0007/5}placeOfOrigin'

        # Check Swiss municipality present
        swiss_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}swissMunicipality')
        assert swiss_elem is not None

        # Check history ID is inside swissMunicipality per XSD
        hist_elem = swiss_elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}historyMunicipalityId')
        assert hist_elem is not None
        assert hist_elem.text == "2310"

    def test_from_xml_swiss(self):
        """Test import Swiss municipality from XML."""
        xml_str = """
        <placeOfOrigin xmlns="http://www.ech.ch/xmlns/eCH-0007/5">
            <swissMunicipality>
                <municipalityId>2310</municipalityId>
                <municipalityName>Bister</municipalityName>
                <cantonAbbreviation>VS</cantonAbbreviation>
                <historyMunicipalityId>2310</historyMunicipalityId>
            </swissMunicipality>
        </placeOfOrigin>
        """
        elem = ET.fromstring(xml_str)
        mun = ECH0007Municipality.from_xml(elem)

        assert mun.name == "Bister"
        assert mun.history_municipality_id == "2310"

    def test_roundtrip_xml_swiss(self):
        """Test XML roundtrip for Swiss municipality."""
        original = ECH0007Municipality.from_swiss(
            municipality_id="2310",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS,
            history_id="2310"
        )

        xml_elem = original.to_xml()
        restored = ECH0007Municipality.from_xml(xml_elem)

        assert restored.name == original.name
        assert restored.swiss_municipality.municipality_id == original.swiss_municipality.municipality_id
        assert restored.history_municipality_id == original.history_municipality_id


class TestRealWorldScenarios:
    """Test with real-world Swiss municipality scenarios."""

    def test_bister_municipality(self):
        """Test Bister municipality (historical, merged into Goms)."""
        # Historical Bister
        bister = ECH0007Municipality.from_swiss(
            municipality_id="2310",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS
        )

        assert bister.swiss_municipality.municipality_id == "2310"
        assert bister.swiss_municipality.canton_abbreviation == CantonAbbreviation.VS

        # Roundtrip
        xml_elem = bister.to_xml()
        restored = ECH0007Municipality.from_xml(xml_elem)
        assert restored.name == "Bister"

    def test_merged_municipality_with_history(self):
        """Test merged municipality (Goms) with historical reference."""
        goms = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Goms",
            canton=CantonAbbreviation.VS,
            history_id="2310"  # Former Bister
        )

        assert goms.history_municipality_id == "2310"

        # Roundtrip preserves history
        xml_elem = goms.to_xml()
        restored = ECH0007Municipality.from_xml(xml_elem)
        assert restored.history_municipality_id == "2310"

    def test_all_cantons_valid(self):
        """Test creating municipality for each canton."""
        test_cases = [
            ("261", "Zürich", CantonAbbreviation.ZH),
            ("351", "Bern", CantonAbbreviation.BE),
            ("1061", "Lausanne", CantonAbbreviation.VD),
            ("5586", "Sion", CantonAbbreviation.VS),
            ("6621", "Genève", CantonAbbreviation.GE),
        ]

        for mun_id, mun_name, canton in test_cases:
            mun = ECH0007Municipality.from_swiss(
                municipality_id=mun_id,
                municipality_name=mun_name,
                canton=canton
            )

            # Roundtrip test
            xml_elem = mun.to_xml()
            restored = ECH0007Municipality.from_xml(xml_elem)

            assert restored.swiss_municipality.municipality_id == mun_id
            assert restored.swiss_municipality.canton_abbreviation == canton
            assert restored.name == mun_name
