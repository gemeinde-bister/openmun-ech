"""Tests for eCH-0129 v6.0.0 dwelling types (Session 7).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints, date ranges, list cardinality
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. XML element names and ordering (xs:sequence)
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import (
    DwellingInformationSource,
    DwellingStatus,
    DwellingUsageCode,
    UsageLimitation,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129DatePartiallyKnown,
    ECH0129NamedId,
)
from openmun_ech.ech0129.v6.dwelling import (
    ECH0129Dwelling,
    ECH0129DwellingIdentification,
    ECH0129DwellingUsage,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# Helpers
# ===========================================================================

def _make_named_id(category='IDBBP', value='12345'):
    return ECH0129NamedId(id_category=category, id_value=value)


def _make_dwelling_usage(**kwargs):
    """Create a DwellingUsage with defaults for optional fields."""
    return ECH0129DwellingUsage(**kwargs)


def _make_dwelling(**kwargs):
    """Create a Dwelling with required fields + overrides."""
    defaults = {
        'local_id': [_make_named_id()],
    }
    defaults.update(kwargs)
    return ECH0129Dwelling(**defaults)


def _roundtrip(obj):
    """Serialize to XML and back, return the new object."""
    xml = obj.to_xml()
    return type(obj).from_xml(xml)


# ===========================================================================
# ECH0129DwellingIdentification
# ===========================================================================

class TestDwellingIdentification:
    """Tests for dwellingIdentificationType (XSD lines 957-963)."""

    def test_create_minimal(self):
        """All 4 fields are required."""
        di = ECH0129DwellingIdentification(
            egid=1234567,
            edid=0,
            ewid=1,
            local_id=_make_named_id(),
        )
        assert di.egid == 1234567
        assert di.edid == 0
        assert di.ewid == 1

    def test_egid_range(self):
        """EGIDType: 1–900000000."""
        ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=1, local_id=_make_named_id()
        )
        ECH0129DwellingIdentification(
            egid=900000000, edid=0, ewid=1, local_id=_make_named_id()
        )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=0, edid=0, ewid=1, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=900000001, edid=0, ewid=1, local_id=_make_named_id()
            )

    def test_edid_range(self):
        """EDIDType: 0–90."""
        ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=1, local_id=_make_named_id()
        )
        ECH0129DwellingIdentification(
            egid=1, edid=90, ewid=1, local_id=_make_named_id()
        )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=-1, ewid=1, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=91, ewid=1, local_id=_make_named_id()
            )

    def test_ewid_range(self):
        """EWIDType: 1–900."""
        ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=1, local_id=_make_named_id()
        )
        ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=900, local_id=_make_named_id()
        )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=0, ewid=0, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=0, ewid=901, local_id=_make_named_id()
            )

    def test_missing_required_fields(self):
        """All 4 fields are required — omitting any must fail."""
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                edid=0, ewid=1, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, ewid=1, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=0, local_id=_make_named_id()
            )
        with pytest.raises(ValueError):
            ECH0129DwellingIdentification(
                egid=1, edid=0, ewid=1
            )

    def test_xml_roundtrip(self):
        di = ECH0129DwellingIdentification(
            egid=190334,
            edid=1,
            ewid=42,
            local_id=_make_named_id('IDGWR', '99'),
        )
        di2 = _roundtrip(di)
        assert di2.egid == 190334
        assert di2.edid == 1
        assert di2.ewid == 42
        assert di2.local_id.id_category == 'IDGWR'
        assert di2.local_id.id_value == '99'

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        di = ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=1, local_id=_make_named_id()
        )
        xml = di.to_xml()
        children = [child.tag for child in xml]
        expected = [
            f'{{{NS_0129}}}EGID',
            f'{{{NS_0129}}}EDID',
            f'{{{NS_0129}}}EWID',
            f'{{{NS_0129}}}localID',
        ]
        assert children == expected

    def test_xml_element_name(self):
        di = ECH0129DwellingIdentification(
            egid=1, edid=0, ewid=1, local_id=_make_named_id()
        )
        xml = di.to_xml()
        assert xml.tag == f'{{{NS_0129}}}dwellingIdentification'


# ===========================================================================
# ECH0129DwellingUsage
# ===========================================================================

class TestDwellingUsage:
    """Tests for dwellingUsageType (XSD lines 965-1000)."""

    def test_create_empty(self):
        """All fields are optional — empty is valid."""
        du = ECH0129DwellingUsage()
        assert du.usage_code is None
        assert du.information_source is None
        assert du.revision_date is None
        assert du.remark is None
        assert du.person_with_main_residence is None
        assert du.person_with_secondary_residence is None
        assert du.date_first_occupancy is None
        assert du.date_last_occupancy is None

    def test_create_full(self):
        """All fields populated."""
        du = ECH0129DwellingUsage(
            usage_code=DwellingUsageCode.MAIN_RESIDENCE,
            information_source=DwellingInformationSource.EWK,
            revision_date=date(2024, 6, 15),
            remark='Hauptwohnsitz Familie Müller',
            person_with_main_residence=True,
            person_with_secondary_residence=False,
            date_first_occupancy=date(2020, 1, 1),
            date_last_occupancy=date(2024, 12, 31),
        )
        assert du.usage_code == DwellingUsageCode.MAIN_RESIDENCE
        assert du.information_source == DwellingInformationSource.EWK
        assert du.revision_date == date(2024, 6, 15)
        assert du.remark == 'Hauptwohnsitz Familie Müller'
        assert du.person_with_main_residence is True
        assert du.person_with_secondary_residence is False
        assert du.date_first_occupancy == date(2020, 1, 1)
        assert du.date_last_occupancy == date(2024, 12, 31)

    def test_revision_date_min(self):
        """XSD: minInclusive=2012-12-31."""
        ECH0129DwellingUsage(revision_date=date(2012, 12, 31))
        with pytest.raises(ValueError, match='2012-12-31'):
            ECH0129DwellingUsage(revision_date=date(2012, 12, 30))

    def test_date_first_occupancy_min(self):
        """XSD: minInclusive=2012-12-31."""
        ECH0129DwellingUsage(date_first_occupancy=date(2012, 12, 31))
        with pytest.raises(ValueError, match='2012-12-31'):
            ECH0129DwellingUsage(date_first_occupancy=date(2010, 1, 1))

    def test_date_last_occupancy_min(self):
        """XSD: minInclusive=2012-12-31."""
        ECH0129DwellingUsage(date_last_occupancy=date(2012, 12, 31))
        with pytest.raises(ValueError, match='2012-12-31'):
            ECH0129DwellingUsage(date_last_occupancy=date(2000, 6, 15))

    def test_remark_length(self):
        """xs:token 1–2000 chars."""
        ECH0129DwellingUsage(remark='A')
        ECH0129DwellingUsage(remark='X' * 2000)
        with pytest.raises(ValueError):
            ECH0129DwellingUsage(remark='')
        with pytest.raises(ValueError):
            ECH0129DwellingUsage(remark='X' * 2001)

    def test_xml_roundtrip_empty(self):
        du = ECH0129DwellingUsage()
        du2 = _roundtrip(du)
        assert du2.usage_code is None
        assert du2.information_source is None

    def test_xml_roundtrip_full(self):
        du = ECH0129DwellingUsage(
            usage_code=DwellingUsageCode.SECONDARY_RESIDENCE,
            information_source=DwellingInformationSource.OWNER,
            revision_date=date(2023, 3, 15),
            remark='Ferienwohnung',
            person_with_main_residence=False,
            person_with_secondary_residence=True,
            date_first_occupancy=date(2018, 7, 1),
            date_last_occupancy=date(2023, 9, 30),
        )
        du2 = _roundtrip(du)
        assert du2.usage_code == DwellingUsageCode.SECONDARY_RESIDENCE
        assert du2.information_source == DwellingInformationSource.OWNER
        assert du2.revision_date == date(2023, 3, 15)
        assert du2.remark == 'Ferienwohnung'
        assert du2.person_with_main_residence is False
        assert du2.person_with_secondary_residence is True
        assert du2.date_first_occupancy == date(2018, 7, 1)
        assert du2.date_last_occupancy == date(2023, 9, 30)

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        du = ECH0129DwellingUsage(
            usage_code=DwellingUsageCode.MAIN_RESIDENCE,
            information_source=DwellingInformationSource.AUTOMATIC,
            revision_date=date(2024, 1, 1),
            remark='test',
            person_with_main_residence=True,
            person_with_secondary_residence=False,
            date_first_occupancy=date(2020, 1, 1),
            date_last_occupancy=date(2024, 1, 1),
        )
        xml = du.to_xml()
        children = [child.tag for child in xml]
        expected = [
            f'{{{NS_0129}}}usageCode',
            f'{{{NS_0129}}}informationSource',
            f'{{{NS_0129}}}revisionDate',
            f'{{{NS_0129}}}remark',
            f'{{{NS_0129}}}personWithMainResidence',
            f'{{{NS_0129}}}personWithSecondaryResidence',
            f'{{{NS_0129}}}dateFirstOccupancy',
            f'{{{NS_0129}}}dateLastOccupancy',
        ]
        assert children == expected

    def test_xml_element_name(self):
        du = ECH0129DwellingUsage()
        xml = du.to_xml()
        assert xml.tag == f'{{{NS_0129}}}dwellingUsage'

    def test_usage_code_enum_values(self):
        """Verify enum string coercion works for all values."""
        for code in DwellingUsageCode:
            du = ECH0129DwellingUsage(usage_code=code)
            du2 = _roundtrip(du)
            assert du2.usage_code == code

    def test_information_source_enum_values(self):
        for src in DwellingInformationSource:
            du = ECH0129DwellingUsage(information_source=src)
            du2 = _roundtrip(du)
            assert du2.information_source == src


# ===========================================================================
# ECH0129Dwelling
# ===========================================================================

class TestDwelling:
    """Tests for dwellingType (XSD lines 1002-1021)."""

    def test_create_minimal(self):
        """Only localID is required."""
        d = _make_dwelling()
        assert len(d.local_id) == 1
        assert d.administrative_dwelling_no is None
        assert d.ewid is None
        assert d.physical_dwelling_no is None
        assert d.date_of_construction is None
        assert d.date_of_demolition is None
        assert d.no_of_habitable_rooms is None
        assert d.floor is None
        assert d.location_of_dwelling_on_floor is None
        assert d.multiple_floor is None
        assert d.usage_limitation is None
        assert d.kitchen is None
        assert d.surface_area_of_dwelling is None
        assert d.status is None
        assert d.dwelling_usage is None
        assert d.dwelling_free_text == []

    def test_create_full(self):
        """All fields populated."""
        d = _make_dwelling(
            administrative_dwelling_no='W01',
            ewid=42,
            physical_dwelling_no='3.OG links',
            date_of_construction=ECH0129DatePartiallyKnown(year='2015'),
            date_of_demolition=ECH0129DatePartiallyKnown(year='2025'),
            no_of_habitable_rooms=4,
            floor=3103,
            location_of_dwelling_on_floor='links',
            multiple_floor=False,
            usage_limitation=UsageLimitation.NONE,
            kitchen=True,
            surface_area_of_dwelling=85,
            status=DwellingStatus.EXISTING,
            dwelling_usage=ECH0129DwellingUsage(
                usage_code=DwellingUsageCode.MAIN_RESIDENCE,
            ),
            dwelling_free_text=['Minergie', 'Neubau'],
        )
        assert d.administrative_dwelling_no == 'W01'
        assert d.ewid == 42
        assert d.no_of_habitable_rooms == 4
        assert d.floor == 3103
        assert d.kitchen is True
        assert d.surface_area_of_dwelling == 85
        assert d.status == DwellingStatus.EXISTING
        assert d.dwelling_usage.usage_code == DwellingUsageCode.MAIN_RESIDENCE
        assert len(d.dwelling_free_text) == 2

    def test_local_id_required(self):
        """localID is required with min 1 entry."""
        with pytest.raises(ValueError):
            ECH0129Dwelling(local_id=[])

    def test_local_id_multiple(self):
        """maxOccurs="unbounded" — multiple local IDs allowed."""
        d = ECH0129Dwelling(local_id=[
            _make_named_id('IDBBP', '1'),
            _make_named_id('IDGWR', '2'),
        ])
        assert len(d.local_id) == 2

    def test_ewid_range(self):
        """EWIDType: 1–900."""
        _make_dwelling(ewid=1)
        _make_dwelling(ewid=900)
        with pytest.raises(ValueError):
            _make_dwelling(ewid=0)
        with pytest.raises(ValueError):
            _make_dwelling(ewid=901)

    def test_administrative_dwelling_no_length(self):
        """xs:token 1–12."""
        _make_dwelling(administrative_dwelling_no='A')
        _make_dwelling(administrative_dwelling_no='A' * 12)
        with pytest.raises(ValueError):
            _make_dwelling(administrative_dwelling_no='')
        with pytest.raises(ValueError):
            _make_dwelling(administrative_dwelling_no='A' * 13)

    def test_physical_dwelling_no_length(self):
        """xs:token 1–12."""
        _make_dwelling(physical_dwelling_no='1')
        _make_dwelling(physical_dwelling_no='X' * 12)
        with pytest.raises(ValueError):
            _make_dwelling(physical_dwelling_no='')
        with pytest.raises(ValueError):
            _make_dwelling(physical_dwelling_no='X' * 13)

    def test_no_of_habitable_rooms_range(self):
        """noOfHabitableRoomsType: 1–99."""
        _make_dwelling(no_of_habitable_rooms=1)
        _make_dwelling(no_of_habitable_rooms=99)
        with pytest.raises(ValueError):
            _make_dwelling(no_of_habitable_rooms=0)
        with pytest.raises(ValueError):
            _make_dwelling(no_of_habitable_rooms=100)

    def test_floor_range(self):
        """floorType: 3100–3419."""
        _make_dwelling(floor=3100)  # Parterre
        _make_dwelling(floor=3199)  # 99. Stock
        _make_dwelling(floor=3401)  # 1. Untergeschoss
        _make_dwelling(floor=3419)  # 19. Untergeschoss
        with pytest.raises(ValueError):
            _make_dwelling(floor=3099)
        with pytest.raises(ValueError):
            _make_dwelling(floor=3420)

    def test_location_of_dwelling_on_floor_length(self):
        """xs:token 3–40."""
        _make_dwelling(location_of_dwelling_on_floor='ABC')
        _make_dwelling(location_of_dwelling_on_floor='X' * 40)
        with pytest.raises(ValueError):
            _make_dwelling(location_of_dwelling_on_floor='AB')
        with pytest.raises(ValueError):
            _make_dwelling(location_of_dwelling_on_floor='X' * 41)

    def test_surface_area_range(self):
        """surfaceAreaOfDwellingType: 1–9999."""
        _make_dwelling(surface_area_of_dwelling=1)
        _make_dwelling(surface_area_of_dwelling=9999)
        with pytest.raises(ValueError):
            _make_dwelling(surface_area_of_dwelling=0)
        with pytest.raises(ValueError):
            _make_dwelling(surface_area_of_dwelling=10000)

    def test_dwelling_free_text_max_2(self):
        """maxOccurs="2"."""
        _make_dwelling(dwelling_free_text=['A', 'B'])
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_dwelling(dwelling_free_text=['A', 'B', 'C'])

    def test_dwelling_free_text_length(self):
        """freeTextType: 1–32 chars per entry."""
        _make_dwelling(dwelling_free_text=['X'])
        _make_dwelling(dwelling_free_text=['X' * 32])
        with pytest.raises(ValueError, match='1-32 chars'):
            _make_dwelling(dwelling_free_text=[''])
        with pytest.raises(ValueError, match='1-32 chars'):
            _make_dwelling(dwelling_free_text=['X' * 33])

    def test_usage_limitation_enum(self):
        """All UsageLimitation values must be accepted."""
        for ul in UsageLimitation:
            d = _make_dwelling(usage_limitation=ul)
            assert d.usage_limitation == ul

    def test_status_enum(self):
        """All DwellingStatus values must be accepted."""
        for st in DwellingStatus:
            d = _make_dwelling(status=st)
            assert d.status == st

    def test_xml_roundtrip_minimal(self):
        d = _make_dwelling()
        d2 = _roundtrip(d)
        assert len(d2.local_id) == 1
        assert d2.local_id[0].id_category == 'IDBBP'
        assert d2.ewid is None
        assert d2.status is None
        assert d2.dwelling_free_text == []

    def test_xml_roundtrip_full(self):
        d = _make_dwelling(
            administrative_dwelling_no='W01',
            ewid=42,
            physical_dwelling_no='3OG-L',
            date_of_construction=ECH0129DatePartiallyKnown(year='2015'),
            no_of_habitable_rooms=4,
            floor=3103,
            location_of_dwelling_on_floor='links vorne',
            multiple_floor=True,
            usage_limitation=UsageLimitation.PRIMARY_RESIDENCE,
            kitchen=True,
            surface_area_of_dwelling=120,
            status=DwellingStatus.EXISTING,
            dwelling_usage=ECH0129DwellingUsage(
                usage_code=DwellingUsageCode.MAIN_RESIDENCE,
                information_source=DwellingInformationSource.EWK,
                person_with_main_residence=True,
            ),
            dwelling_free_text=['Minergie'],
        )
        d2 = _roundtrip(d)
        assert d2.administrative_dwelling_no == 'W01'
        assert d2.ewid == 42
        assert d2.physical_dwelling_no == '3OG-L'
        assert d2.date_of_construction.year == '2015'
        assert d2.no_of_habitable_rooms == 4
        assert d2.floor == 3103
        assert d2.location_of_dwelling_on_floor == 'links vorne'
        assert d2.multiple_floor is True
        assert d2.usage_limitation == UsageLimitation.PRIMARY_RESIDENCE
        assert d2.kitchen is True
        assert d2.surface_area_of_dwelling == 120
        assert d2.status == DwellingStatus.EXISTING
        assert d2.dwelling_usage.usage_code == DwellingUsageCode.MAIN_RESIDENCE
        assert d2.dwelling_usage.information_source == DwellingInformationSource.EWK
        assert d2.dwelling_usage.person_with_main_residence is True
        assert d2.dwelling_free_text == ['Minergie']

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        d = _make_dwelling(
            administrative_dwelling_no='W01',
            ewid=1,
            physical_dwelling_no='1',
            date_of_construction=ECH0129DatePartiallyKnown(year='2020'),
            date_of_demolition=ECH0129DatePartiallyKnown(year='2025'),
            no_of_habitable_rooms=3,
            floor=3100,
            location_of_dwelling_on_floor='mitte',
            multiple_floor=False,
            usage_limitation=UsageLimitation.NONE,
            kitchen=True,
            surface_area_of_dwelling=50,
            status=DwellingStatus.EXISTING,
            dwelling_usage=ECH0129DwellingUsage(
                usage_code=DwellingUsageCode.MAIN_RESIDENCE,
            ),
            dwelling_free_text=['A', 'B'],
        )
        xml = d.to_xml()
        children = [child.tag for child in xml]
        expected = [
            f'{{{NS_0129}}}localID',
            f'{{{NS_0129}}}administrativeDwellingNo',
            f'{{{NS_0129}}}EWID',
            f'{{{NS_0129}}}physicalDwellingNo',
            f'{{{NS_0129}}}dateOfConstruction',
            f'{{{NS_0129}}}dateOfDemolition',
            f'{{{NS_0129}}}noOfHabitableRooms',
            f'{{{NS_0129}}}floor',
            f'{{{NS_0129}}}locationOfDwellingOnFloor',
            f'{{{NS_0129}}}multipleFloor',
            f'{{{NS_0129}}}usageLimitation',
            f'{{{NS_0129}}}kitchen',
            f'{{{NS_0129}}}surfaceAreaOfDwelling',
            f'{{{NS_0129}}}status',
            f'{{{NS_0129}}}dwellingUsage',
            f'{{{NS_0129}}}dwellingFreeText',
            f'{{{NS_0129}}}dwellingFreeText',
        ]
        assert children == expected

    def test_xml_element_name(self):
        d = _make_dwelling()
        xml = d.to_xml()
        assert xml.tag == f'{{{NS_0129}}}dwelling'

    def test_date_of_construction_roundtrip(self):
        """datePartiallyKnownType with date branch."""
        d = _make_dwelling(
            date_of_construction=ECH0129DatePartiallyKnown(
                year_month_day=date(2015, 6, 15)
            ),
        )
        d2 = _roundtrip(d)
        assert d2.date_of_construction.year_month_day == date(2015, 6, 15)

    def test_date_of_demolition_roundtrip(self):
        """datePartiallyKnownType with yearMonth branch."""
        d = _make_dwelling(
            date_of_demolition=ECH0129DatePartiallyKnown(
                year_month='2025-03'
            ),
        )
        d2 = _roundtrip(d)
        assert d2.date_of_demolition.year_month == '2025-03'

    def test_dwelling_usage_nested_roundtrip(self):
        """dwellingUsage is a nested complex type."""
        d = _make_dwelling(
            dwelling_usage=ECH0129DwellingUsage(
                usage_code=DwellingUsageCode.VACANT_SHORT,
                date_first_occupancy=date(2020, 1, 15),
                date_last_occupancy=date(2022, 6, 30),
                remark='Leerstehend seit Auszug',
            ),
        )
        d2 = _roundtrip(d)
        assert d2.dwelling_usage.usage_code == DwellingUsageCode.VACANT_SHORT
        assert d2.dwelling_usage.date_first_occupancy == date(2020, 1, 15)
        assert d2.dwelling_usage.date_last_occupancy == date(2022, 6, 30)
        assert d2.dwelling_usage.remark == 'Leerstehend seit Auszug'

    def test_multiple_free_text_roundtrip(self):
        """dwellingFreeText maxOccurs=2, both entries preserved."""
        d = _make_dwelling(dwelling_free_text=['Minergie', 'Neubau 2020'])
        d2 = _roundtrip(d)
        assert d2.dwelling_free_text == ['Minergie', 'Neubau 2020']

    def test_floor_codes_parterre(self):
        """3100 = Parterre (inkl. Hochparterre)."""
        d = _make_dwelling(floor=3100)
        d2 = _roundtrip(d)
        assert d2.floor == 3100

    def test_floor_codes_upper(self):
        """3101-3199 = 1.–99. Stock."""
        d = _make_dwelling(floor=3101)
        d2 = _roundtrip(d)
        assert d2.floor == 3101

    def test_floor_codes_basement(self):
        """3401-3419 = 1.–19. Untergeschoss."""
        d = _make_dwelling(floor=3419)
        d2 = _roundtrip(d)
        assert d2.floor == 3419
