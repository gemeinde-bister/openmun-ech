"""Phase 2 Prototype Gate: ECHModel structural XML comparison.

Tests that ECHModel-based classes produce structurally identical XML to the
existing handwritten implementations. This is the pass/fail gate for the
declarative framework approach.

Pass criteria:
    1. ECH0008CountryProto produces identical XML to ECH0008Country
    2. ECH0020NameInfoProto produces identical XML to ECH0020NameInfo
    3. from_xml() roundtrip works for both
    4. Pydantic validation (Field constraints) still works
"""

import xml.etree.ElementTree as ET
from datetime import date
from typing import Optional

import pytest

from openmun_ech.core import NS, ECHModel, xml_field
from openmun_ech.ech0008.v3 import ECH0008Country, ECH0008CountryShort
from openmun_ech.ech0011.v8 import ECH0011NameData
from openmun_ech.ech0020.v3 import ECH0020NameInfo


# ---------------------------------------------------------------------------
# Prototype models (ECHModel-based reimplementations)
# ---------------------------------------------------------------------------

class ECH0008CountryProto(ECHModel):
    """ECHModel-based eCH-0008 Country (prototype)."""

    __xml_ns__ = NS.ECH0008_V3
    __xml_element__ = 'country'

    country_id: Optional[str] = xml_field('countryId', default=None, min_length=4, max_length=4)
    country_id_iso2: Optional[str] = xml_field('countryIdISO2', default=None, min_length=2, max_length=2)
    country_name_short: str = xml_field('countryNameShort', min_length=1, max_length=50)


class ECH0008CountryShortProto(ECHModel):
    """ECHModel-based eCH-0008 CountryShort (prototype)."""

    __xml_ns__ = NS.ECH0008_V3
    __xml_element__ = 'country'  # Original uses 'country' as default element name

    country_name_short: str = xml_field('countryNameShort', min_length=1, max_length=50)


class ECH0020NameInfoProto(ECHModel):
    """ECHModel-based ECH0020NameInfo (prototype).

    Wraps ECH0011NameData (old-style class, not migrated).
    Tests cross-namespace wrapper pattern.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'nameInfo'

    name_data: ECH0011NameData = xml_field(
        'nameData', wrapper=True, child_ns=NS.ECH0011_V8
    )
    name_valid_from: Optional[date] = xml_field('nameValidFrom', default=None)


# ---------------------------------------------------------------------------
# Structural XML comparison utility
# ---------------------------------------------------------------------------

def xml_structurally_equal(a: ET.Element, b: ET.Element, path: str = '') -> tuple[bool, str]:
    """Compare two XML elements by expanded names, text, attributes, and children.

    Uses Clark notation ({namespace}localname) — immune to prefix differences.

    Returns:
        (True, '') if equal, (False, 'path: description of difference') otherwise.
    """
    current_path = f"{path}/{a.tag}" if path else a.tag

    # Tag (expanded name)
    if a.tag != b.tag:
        return False, f"{current_path}: tag mismatch: {a.tag!r} != {b.tag!r}"

    # Text content
    a_text = (a.text or '').strip()
    b_text = (b.text or '').strip()
    if a_text != b_text:
        return False, f"{current_path}: text mismatch: {a_text!r} != {b_text!r}"

    # Tail text
    a_tail = (a.tail or '').strip()
    b_tail = (b.tail or '').strip()
    if a_tail != b_tail:
        return False, f"{current_path}: tail mismatch: {a_tail!r} != {b_tail!r}"

    # Attributes
    if dict(a.attrib) != dict(b.attrib):
        return False, f"{current_path}: attrib mismatch: {dict(a.attrib)} != {dict(b.attrib)}"

    # Children count
    a_children = list(a)
    b_children = list(b)
    if len(a_children) != len(b_children):
        return False, (
            f"{current_path}: child count mismatch: {len(a_children)} != {len(b_children)}. "
            f"a_tags={[c.tag for c in a_children]}, b_tags={[c.tag for c in b_children]}"
        )

    # Recurse into children
    for ac, bc in zip(a_children, b_children):
        equal, msg = xml_structurally_equal(ac, bc, current_path)
        if not equal:
            return False, msg

    return True, ''


def assert_xml_equal(a: ET.Element, b: ET.Element) -> None:
    """Assert two XML elements are structurally identical."""
    equal, msg = xml_structurally_equal(a, b)
    if not equal:
        # Provide debug output
        a_str = ET.tostring(a, encoding='unicode', short_empty_elements=False)
        b_str = ET.tostring(b, encoding='unicode', short_empty_elements=False)
        pytest.fail(f"XML structural mismatch:\n  {msg}\n\nExpected:\n{a_str}\n\nGot:\n{b_str}")


# ---------------------------------------------------------------------------
# Test Case 1: eCH-0008 Country (all fields populated)
# ---------------------------------------------------------------------------

class TestECH0008Prototype:
    """Verify ECH0008CountryProto produces identical XML to ECH0008Country."""

    def test_country_all_fields(self):
        """All three fields populated."""
        old = ECH0008Country(
            country_id='8100',
            country_id_iso2='CH',
            country_name_short='Schweiz'
        )
        new = ECH0008CountryProto(
            country_id='8100',
            country_id_iso2='CH',
            country_name_short='Schweiz'
        )

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_country_required_only(self):
        """Only required field (country_name_short) set."""
        old = ECH0008Country(country_name_short='Deutschland')
        new = ECH0008CountryProto(country_name_short='Deutschland')

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_country_partial_optional(self):
        """One optional field set, one None."""
        old = ECH0008Country(
            country_id='8207',
            country_name_short='Frankreich'
        )
        new = ECH0008CountryProto(
            country_id='8207',
            country_name_short='Frankreich'
        )

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_country_custom_element_name(self):
        """Custom element_name parameter."""
        old = ECH0008Country(
            country_id='8100',
            country_id_iso2='CH',
            country_name_short='Schweiz'
        )
        new = ECH0008CountryProto(
            country_id='8100',
            country_id_iso2='CH',
            country_name_short='Schweiz'
        )

        old_xml = old.to_xml(element_name='placeOfBirthCountry')
        new_xml = new.to_xml(element_name='placeOfBirthCountry')
        assert_xml_equal(old_xml, new_xml)

    def test_country_short(self):
        """ECH0008CountryShort — single field."""
        old = ECH0008CountryShort(country_name_short='Schweiz')
        new = ECH0008CountryShortProto(country_name_short='Schweiz')

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_country_roundtrip(self):
        """from_xml(to_xml(data)) produces same model data."""
        original = ECH0008CountryProto(
            country_id='8100',
            country_id_iso2='CH',
            country_name_short='Schweiz'
        )

        xml = original.to_xml()
        restored = ECH0008CountryProto.from_xml(xml)

        assert restored.country_id == original.country_id
        assert restored.country_id_iso2 == original.country_id_iso2
        assert restored.country_name_short == original.country_name_short

    def test_country_roundtrip_optional_none(self):
        """Roundtrip with optional fields as None."""
        original = ECH0008CountryProto(country_name_short='Italien')

        xml = original.to_xml()
        restored = ECH0008CountryProto.from_xml(xml)

        assert restored.country_id is None
        assert restored.country_id_iso2 is None
        assert restored.country_name_short == 'Italien'

    def test_pydantic_validation_min_length(self):
        """Pydantic Field constraints still enforced."""
        with pytest.raises(Exception):  # ValidationError
            ECH0008CountryProto(country_name_short='')

    def test_pydantic_validation_max_length(self):
        """Pydantic max_length constraint."""
        with pytest.raises(Exception):  # ValidationError
            ECH0008CountryProto(country_id='12345')  # max 4 chars


# ---------------------------------------------------------------------------
# Test Case 2: ECH0020NameInfo (cross-namespace wrapper)
# ---------------------------------------------------------------------------

class TestECH0020NameInfoPrototype:
    """Verify ECH0020NameInfoProto produces identical XML to ECH0020NameInfo."""

    def _make_name_data_minimal(self) -> ECH0011NameData:
        """Minimal NameData: only required fields."""
        return ECH0011NameData(
            official_name='Muster',
            first_name='Hans'
        )

    def _make_name_data_full(self) -> ECH0011NameData:
        """NameData with all optional fields populated."""
        return ECH0011NameData(
            official_name='von Ballmoos',
            first_name='David',
            original_name='Ballmoos',
            alliance_name='Meier',
            alias_name='Dav',
            other_name='Friedrich',
            call_name='Dave'
        )

    def test_name_info_minimal(self):
        """Wrapper with minimal NameData (officialName + firstName only)."""
        name_data = self._make_name_data_minimal()

        old = ECH0020NameInfo(name_data=name_data)
        new = ECH0020NameInfoProto(name_data=name_data)

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_name_info_full_names(self):
        """Wrapper with all name fields populated."""
        name_data = self._make_name_data_full()

        old = ECH0020NameInfo(name_data=name_data)
        new = ECH0020NameInfoProto(name_data=name_data)

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_name_info_with_valid_from(self):
        """Wrapper with nameValidFrom date set."""
        name_data = self._make_name_data_minimal()

        old = ECH0020NameInfo(name_data=name_data, name_valid_from=date(2020, 3, 15))
        new = ECH0020NameInfoProto(name_data=name_data, name_valid_from=date(2020, 3, 15))

        old_xml = old.to_xml()
        new_xml = new.to_xml()
        assert_xml_equal(old_xml, new_xml)

    def test_name_info_with_parent(self):
        """Serialization into a parent element."""
        name_data = self._make_name_data_minimal()

        parent_old = ET.Element(f'{{{NS.ECH0020_V3}}}person')
        parent_new = ET.Element(f'{{{NS.ECH0020_V3}}}person')

        old = ECH0020NameInfo(name_data=name_data, name_valid_from=date(2021, 6, 1))
        new = ECH0020NameInfoProto(name_data=name_data, name_valid_from=date(2021, 6, 1))

        old.to_xml(parent=parent_old)
        new.to_xml(parent=parent_new)

        assert_xml_equal(parent_old, parent_new)

    def test_name_info_roundtrip(self):
        """from_xml(to_xml(data)) roundtrip for wrapper pattern."""
        name_data = self._make_name_data_full()
        original = ECH0020NameInfoProto(
            name_data=name_data,
            name_valid_from=date(2023, 1, 1)
        )

        xml = original.to_xml()
        restored = ECH0020NameInfoProto.from_xml(xml)

        assert restored.name_data.official_name == 'von Ballmoos'
        assert restored.name_data.first_name == 'David'
        assert restored.name_data.original_name == 'Ballmoos'
        assert restored.name_data.alliance_name == 'Meier'
        assert restored.name_data.alias_name == 'Dav'
        assert restored.name_data.other_name == 'Friedrich'
        assert restored.name_data.call_name == 'Dave'
        assert restored.name_valid_from == date(2023, 1, 1)

    def test_name_info_roundtrip_no_date(self):
        """Roundtrip without optional nameValidFrom."""
        name_data = self._make_name_data_minimal()
        original = ECH0020NameInfoProto(name_data=name_data)

        xml = original.to_xml()
        restored = ECH0020NameInfoProto.from_xml(xml)

        assert restored.name_data.official_name == 'Muster'
        assert restored.name_data.first_name == 'Hans'
        assert restored.name_valid_from is None

    def test_namespace_structure(self):
        """Verify the wrapper has correct namespace structure.

        The wrapper element (nameData) must be in eCH-0020 namespace,
        while its children (officialName, firstName...) are in eCH-0011.
        """
        name_data = ECH0011NameData(official_name='Test', first_name='Person')
        model = ECH0020NameInfoProto(name_data=name_data)
        xml = model.to_xml()

        # Root: {eCH-0020}nameInfo
        assert xml.tag == f'{{{NS.ECH0020_V3}}}nameInfo'

        # First child: {eCH-0020}nameData (wrapper in parent namespace)
        name_data_elem = xml[0]
        assert name_data_elem.tag == f'{{{NS.ECH0020_V3}}}nameData'

        # Wrapper's children: {eCH-0011}officialName, {eCH-0011}firstName
        children = list(name_data_elem)
        assert len(children) >= 2
        assert children[0].tag == f'{{{NS.ECH0011_V8}}}officialName'
        assert children[1].tag == f'{{{NS.ECH0011_V8}}}firstName'
