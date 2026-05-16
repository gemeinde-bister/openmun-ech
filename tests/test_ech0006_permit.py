"""Tests for eCH-0006 v2 permit models.

Covers:
- PermitRoot model creation and validation
- XML serialization (to_xml)
- XML deserialization (from_xml)
- Roundtrip integrity
- Optional field handling (None = not serialized)
- Enum value correctness in XML text
"""

import xml.etree.ElementTree as ET

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0006 import (
    InhabitantControlType,
    PermitRoot,
    ResidencePermitBorderType,
    ResidencePermitCategoryType,
    ResidencePermitDetailedType,
    ResidencePermitRulingType,
    ResidencePermitShortType,
    ResidencePermitToBeRegisteredType,
    ResidencePermitType,
    get_permit_description,
)


class TestPermitRootModel:
    """Test PermitRoot model creation and validation."""

    def test_create_empty(self):
        """All fields are optional — empty PermitRoot is valid."""
        root = PermitRoot()
        assert root.residence_permit_category is None
        assert root.residence_permit_ruling is None
        assert root.residence_permit_border is None
        assert root.residence_permit_short_type is None
        assert root.residence_permit is None
        assert root.inhabitant_control is None
        assert root.residence_permit_detailed_type is None
        assert root.residence_permit_to_be_registered_type is None

    def test_create_with_single_field(self):
        root = PermitRoot(residence_permit=ResidencePermitType.B_EU_EFTA)
        assert root.residence_permit == ResidencePermitType.B_EU_EFTA
        assert root.residence_permit.value == "0201"

    def test_create_with_multiple_fields(self):
        root = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.B_RESIDENCE,
            residence_permit_ruling=ResidencePermitRulingType.EU_EFTA_REGULATION,
            residence_permit=ResidencePermitType.B_EU_EFTA,
            inhabitant_control=InhabitantControlType.B_RESIDENCE_EU_EFTA,
        )
        assert root.residence_permit_category == ResidencePermitCategoryType.B_RESIDENCE
        assert root.residence_permit_ruling == ResidencePermitRulingType.EU_EFTA_REGULATION
        assert root.residence_permit == ResidencePermitType.B_EU_EFTA
        assert root.inhabitant_control == InhabitantControlType.B_RESIDENCE_EU_EFTA

    def test_create_with_all_fields(self):
        root = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.L_SHORT_TERM,
            residence_permit_ruling=ResidencePermitRulingType.EU_EFTA_REGULATION,
            residence_permit_border=ResidencePermitBorderType.STAY_LESS_12_MONTHS,
            residence_permit_short_type=ResidencePermitShortType.SHORT_TERM_4_TO_12_MONTHS,
            residence_permit=ResidencePermitType.L_EU_EFTA_4_TO_12M,
            inhabitant_control=InhabitantControlType.L_SHORT_TERM_EU_EFTA,
            residence_permit_detailed_type=ResidencePermitDetailedType.L_SHORT_EU_4_TO_12M,
            residence_permit_to_be_registered_type=ResidencePermitToBeRegisteredType.EMPLOYEE_SWISS_EMPLOYER,
        )
        assert root.residence_permit_category == ResidencePermitCategoryType.L_SHORT_TERM
        assert root.residence_permit_to_be_registered_type == ResidencePermitToBeRegisteredType.EMPLOYEE_SWISS_EMPLOYER


class TestPermitRootToXml:
    """Test XML serialization."""

    def test_empty_permit_root(self):
        """Empty PermitRoot serializes to element with no children."""
        root = PermitRoot()
        elem = root.to_xml()
        assert elem.tag == f'{{{NS.ECH0006_V2}}}permitRoot'
        assert len(list(elem)) == 0

    def test_single_field(self):
        root = PermitRoot(residence_permit=ResidencePermitType.C_EU_EFTA)
        elem = root.to_xml()

        child = elem.find(f'{{{NS.ECH0006_V2}}}residencePermit')
        assert child is not None
        assert child.text == '0301'

    def test_multiple_fields_order(self):
        """Fields appear in declaration order (XSD sequence)."""
        root = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.G_CROSS_BORDER_COMMUTER,
            residence_permit=ResidencePermitType.G_EU_EFTA,
            inhabitant_control=InhabitantControlType.G_BORDER_EU_EFTA,
        )
        elem = root.to_xml()
        children = list(elem)
        assert len(children) == 3

        # Declaration order: category, ruling, border, short, permit, control, detailed, register
        assert children[0].tag == f'{{{NS.ECH0006_V2}}}residencePermitCategory'
        assert children[0].text == '06'
        assert children[1].tag == f'{{{NS.ECH0006_V2}}}residencePermit'
        assert children[1].text == '0601'
        assert children[2].tag == f'{{{NS.ECH0006_V2}}}inhabitantControl'
        assert children[2].text == '0601'

    def test_namespace_correct(self):
        """All elements use eCH-0006 v2 namespace."""
        root = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.B_RESIDENCE,
            residence_permit_ruling=ResidencePermitRulingType.EU_EFTA_REGULATION,
        )
        elem = root.to_xml()
        for child in elem:
            assert child.tag.startswith(f'{{{NS.ECH0006_V2}}}')

    def test_all_fields_serialized(self):
        """All 8 fields serialize when populated."""
        root = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.B_RESIDENCE,
            residence_permit_ruling=ResidencePermitRulingType.EU_EFTA_REGULATION,
            residence_permit_border=ResidencePermitBorderType.STAY_12_MONTHS_OR_MORE,
            residence_permit_short_type=ResidencePermitShortType.SHORT_TERM_12_MONTHS_OR_MORE,
            residence_permit=ResidencePermitType.B_EU_EFTA,
            inhabitant_control=InhabitantControlType.B_RESIDENCE_EU_EFTA,
            residence_permit_detailed_type=ResidencePermitDetailedType.B_RESIDENCE_EU_EFTA,
            residence_permit_to_be_registered_type=ResidencePermitToBeRegisteredType.EMPLOYEE_SWISS_EMPLOYER,
        )
        elem = root.to_xml()
        assert len(list(elem)) == 8


class TestPermitRootFromXml:
    """Test XML deserialization."""

    def test_empty_element(self):
        """Empty permitRoot element deserializes to all-None fields."""
        elem = ET.Element(f'{{{NS.ECH0006_V2}}}permitRoot')
        root = PermitRoot.from_xml(elem)
        assert root.residence_permit is None
        assert root.residence_permit_category is None

    def test_single_field(self):
        elem = ET.Element(f'{{{NS.ECH0006_V2}}}permitRoot')
        child = ET.SubElement(elem, f'{{{NS.ECH0006_V2}}}residencePermit')
        child.text = '0201'

        root = PermitRoot.from_xml(elem)
        assert root.residence_permit == ResidencePermitType.B_EU_EFTA

    def test_multiple_fields(self):
        elem = ET.Element(f'{{{NS.ECH0006_V2}}}permitRoot')

        cat = ET.SubElement(elem, f'{{{NS.ECH0006_V2}}}residencePermitCategory')
        cat.text = '02'
        ruling = ET.SubElement(elem, f'{{{NS.ECH0006_V2}}}residencePermitRuling')
        ruling.text = '01'
        permit = ET.SubElement(elem, f'{{{NS.ECH0006_V2}}}residencePermit')
        permit.text = '0201'

        root = PermitRoot.from_xml(elem)
        assert root.residence_permit_category == ResidencePermitCategoryType.B_RESIDENCE
        assert root.residence_permit_ruling == ResidencePermitRulingType.EU_EFTA_REGULATION
        assert root.residence_permit == ResidencePermitType.B_EU_EFTA

    def test_all_fields(self):
        elem = ET.Element(f'{{{NS.ECH0006_V2}}}permitRoot')

        fields = [
            ('residencePermitCategory', '07'),
            ('residencePermitRuling', '01'),
            ('residencePermitBorder', '01'),
            ('residencePermitShortType', '02'),
            ('residencePermit', '0701'),
            ('inhabitantControl', '0701'),
            ('residencePermitDetailedType', '0701'),
            ('residencePermitToBeRegisteredType', '01'),
        ]
        for name, value in fields:
            child = ET.SubElement(elem, f'{{{NS.ECH0006_V2}}}{name}')
            child.text = value

        root = PermitRoot.from_xml(elem)
        assert root.residence_permit_category == ResidencePermitCategoryType.L_SHORT_TERM
        assert root.residence_permit_ruling == ResidencePermitRulingType.EU_EFTA_REGULATION
        assert root.residence_permit_border == ResidencePermitBorderType.STAY_LESS_12_MONTHS
        assert root.residence_permit_short_type == ResidencePermitShortType.SHORT_TERM_4_TO_12_MONTHS
        assert root.residence_permit == ResidencePermitType.L_EU_EFTA
        assert root.inhabitant_control == InhabitantControlType.L_SHORT_TERM_EU_EFTA
        assert root.residence_permit_detailed_type == ResidencePermitDetailedType.L_SHORT_TERM_EU_EFTA
        assert root.residence_permit_to_be_registered_type == ResidencePermitToBeRegisteredType.EMPLOYEE_SWISS_EMPLOYER


class TestPermitRootRoundtrip:
    """Test serialization roundtrip integrity."""

    @pytest.mark.parametrize("permit_type", [
        ResidencePermitType.B_EU_EFTA,
        ResidencePermitType.C_NON_EU_EFTA,
        ResidencePermitType.F_PROVISIONALLY_ADMITTED,
        ResidencePermitType.G_EU_EFTA_LESS_12M,
        ResidencePermitType.L_TRAINEE_18M_OR_LESS,
        ResidencePermitType.N_ASYLUM_SEEKER,
        ResidencePermitType.MANDATORY_REG_POSTED_WORKER,
    ])
    def test_roundtrip_single_permit(self, permit_type):
        """Roundtrip for various permit types."""
        original = PermitRoot(residence_permit=permit_type)
        elem = original.to_xml()
        restored = PermitRoot.from_xml(elem)
        assert restored.residence_permit == original.residence_permit

    def test_roundtrip_empty(self):
        """Empty PermitRoot survives roundtrip."""
        original = PermitRoot()
        elem = original.to_xml()
        restored = PermitRoot.from_xml(elem)
        assert restored == original

    def test_roundtrip_all_fields(self):
        """Full PermitRoot survives roundtrip."""
        original = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.G_CROSS_BORDER_COMMUTER,
            residence_permit_ruling=ResidencePermitRulingType.EU_EFTA_REGULATION,
            residence_permit_border=ResidencePermitBorderType.STAY_12_MONTHS_OR_MORE,
            residence_permit_short_type=ResidencePermitShortType.SHORT_TERM_12_MONTHS_OR_MORE,
            residence_permit=ResidencePermitType.G_EU_EFTA_12M_OR_MORE,
            inhabitant_control=InhabitantControlType.G_BORDER_EU_EFTA,
            residence_permit_detailed_type=ResidencePermitDetailedType.G_BORDER_EU_EFTA_12M_OR_MORE,
            residence_permit_to_be_registered_type=ResidencePermitToBeRegisteredType.SELF_EMPLOYED_SERVICE_PROVIDER,
        )
        elem = original.to_xml()
        restored = PermitRoot.from_xml(elem)
        assert restored == original

    def test_roundtrip_partial_fields(self):
        """Partial PermitRoot (some None) survives roundtrip."""
        original = PermitRoot(
            residence_permit_category=ResidencePermitCategoryType.N_ASYLUM_SEEKER,
            residence_permit=ResidencePermitType.N_ASYLUM_SEEKER,
        )
        elem = original.to_xml()
        restored = PermitRoot.from_xml(elem)
        assert restored == original
        assert restored.residence_permit_ruling is None
        assert restored.residence_permit_border is None


class TestGetPermitDescription:
    """Test helper function."""

    def test_known_permit(self):
        desc = get_permit_description("02")
        assert desc == 'B'

    def test_known_permit_detailed(self):
        desc = get_permit_description("0201")
        assert desc == 'B Eu Efta'

    def test_unknown_permit(self):
        desc = get_permit_description("9999")
        assert desc == 'Unknown permit: 9999'
