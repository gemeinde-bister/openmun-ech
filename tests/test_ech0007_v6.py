"""Tests for eCH-0007 v6.0 municipality types.

Verifies namespace correctness, v6-specific constraints (historyMunicipalityId range),
and XML serialization roundtrip.
"""

import pytest
from xml.etree import ElementTree as ET

from openmun_ech.core import NS
from openmun_ech.ech0007.v5 import CantonAbbreviation, CantonFLAbbreviation
from openmun_ech.ech0007.v6 import (
    ECH0007v6SwissMunicipality,
    ECH0007v6SwissAndFLMunicipality,
)


class TestECH0007v6SwissMunicipality:
    """Test v6 Swiss municipality type."""

    def test_create_valid(self):
        m = ECH0007v6SwissMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
            canton_abbreviation=CantonAbbreviation.VS,
        )
        assert m.municipality_id == '6198'
        assert m.municipality_name == 'Bister'
        assert m.canton_abbreviation == CantonAbbreviation.VS

    def test_optional_fields(self):
        m = ECH0007v6SwissMunicipality(municipality_name='Bister')
        assert m.municipality_id is None
        assert m.canton_abbreviation is None
        assert m.history_municipality_id is None

    def test_history_id_v6_range(self):
        """v6 tightened range: 10001-99999."""
        m = ECH0007v6SwissMunicipality(
            municipality_name='Test',
            history_municipality_id='10001',
        )
        assert m.history_municipality_id == '10001'

        m = ECH0007v6SwissMunicipality(
            municipality_name='Test',
            history_municipality_id='99999',
        )
        assert m.history_municipality_id == '99999'

    def test_history_id_v6_range_too_low(self):
        with pytest.raises(ValueError, match='10001-99999'):
            ECH0007v6SwissMunicipality(
                municipality_name='Test',
                history_municipality_id='9999',
            )

    def test_history_id_v6_range_too_high(self):
        with pytest.raises(ValueError, match='10001-99999'):
            ECH0007v6SwissMunicipality(
                municipality_name='Test',
                history_municipality_id='100000',
            )

    def test_municipality_id_range(self):
        with pytest.raises(ValueError, match='1-9999'):
            ECH0007v6SwissMunicipality(
                municipality_id='0',
                municipality_name='Test',
            )

    def test_xml_namespace_is_v6(self):
        m = ECH0007v6SwissMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
        )
        xml = m.to_xml()
        assert xml.tag == f'{{{NS.ECH0007_V6}}}swissMunicipality'

    def test_xml_roundtrip(self):
        original = ECH0007v6SwissMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
            canton_abbreviation=CantonAbbreviation.VS,
            history_municipality_id='10001',
        )
        xml = original.to_xml()
        restored = ECH0007v6SwissMunicipality.from_xml(xml)
        assert restored.municipality_id == original.municipality_id
        assert restored.municipality_name == original.municipality_name
        assert restored.canton_abbreviation == original.canton_abbreviation
        assert restored.history_municipality_id == original.history_municipality_id


class TestECH0007v6SwissAndFLMunicipality:
    """Test v6 Swiss+FL municipality type."""

    def test_create_valid(self):
        m = ECH0007v6SwissAndFLMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
            canton_fl_abbreviation=CantonFLAbbreviation.VS,
        )
        assert m.municipality_id == '6198'
        assert m.canton_fl_abbreviation == CantonFLAbbreviation.VS

    def test_fl_abbreviation(self):
        m = ECH0007v6SwissAndFLMunicipality(
            municipality_id='7001',
            municipality_name='Vaduz',
            canton_fl_abbreviation=CantonFLAbbreviation.FL,
        )
        assert m.canton_fl_abbreviation == CantonFLAbbreviation.FL

    def test_required_fields(self):
        with pytest.raises(Exception):
            ECH0007v6SwissAndFLMunicipality(municipality_name='Test')

    def test_xml_namespace_is_v6(self):
        m = ECH0007v6SwissAndFLMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
            canton_fl_abbreviation=CantonFLAbbreviation.VS,
        )
        xml = m.to_xml()
        assert xml.tag == f'{{{NS.ECH0007_V6}}}swissAndFlMunicipality'

    def test_xml_roundtrip(self):
        original = ECH0007v6SwissAndFLMunicipality(
            municipality_id='6198',
            municipality_name='Bister',
            canton_fl_abbreviation=CantonFLAbbreviation.VS,
            history_municipality_id='10001',
        )
        xml = original.to_xml()
        restored = ECH0007v6SwissAndFLMunicipality.from_xml(xml)
        assert restored.municipality_id == original.municipality_id
        assert restored.municipality_name == original.municipality_name
        assert restored.canton_fl_abbreviation == original.canton_fl_abbreviation
        assert restored.history_municipality_id == original.history_municipality_id

    def test_history_id_v6_range(self):
        """v6 tightened range: 10001-99999."""
        with pytest.raises(ValueError, match='10001-99999'):
            ECH0007v6SwissAndFLMunicipality(
                municipality_id='6198',
                municipality_name='Test',
                canton_fl_abbreviation=CantonFLAbbreviation.VS,
                history_municipality_id='5000',
            )


class TestNamespaceDistinction:
    """Verify v5 and v6 produce different namespace URIs."""

    def test_v5_vs_v6_namespace(self):
        from openmun_ech.ech0007.v5 import ECH0007SwissMunicipality

        v5 = ECH0007SwissMunicipality(municipality_name='Test')
        v6 = ECH0007v6SwissMunicipality(municipality_name='Test')

        v5_xml = v5.to_xml()
        v6_xml = v6.to_xml()

        assert NS.ECH0007_V5 in v5_xml.tag
        assert NS.ECH0007_V6 in v6_xml.tag
        assert v5_xml.tag != v6_xml.tag
