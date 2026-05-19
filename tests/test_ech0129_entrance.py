"""Tests for eCH-0129 v6.0.0 entrance and address types.

Covers:
- ECH0129BuildingEntranceIdentification (buildingEntranceIdentificationType)
- ECH0129BuildingEntrance (buildingEntranceType)
- ECH0129BuildingEntranceOnly (buildingEntranceOnlyType)
- ECH0129AddressStreetEntry + ECH0129AddressStreetDescription (anonymous inline)
- ECH0129BuildingAddress (buildingAddressType)
- ECH0129BuildingAddressLight (buildingAddressLightType)
"""

import xml.etree.ElementTree as ET

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import BuildingStatus, StreetLanguage
from openmun_ech.ech0129.v6.base_types import ECH0129Coordinates, ECH0129NamedId
from openmun_ech.ech0129.v6.entrance import (
    ECH0129AddressStreetDescription,
    ECH0129AddressStreetEntry,
    ECH0129BuildingAddress,
    ECH0129BuildingAddressLight,
    ECH0129BuildingEntrance,
    ECH0129BuildingEntranceIdentification,
    ECH0129BuildingEntranceOnly,
)
from openmun_ech.ech0129.v6.street_locality import ECH0129StreetSection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _named_id(category: str = 'GWR', id_val: str = '1') -> ECH0129NamedId:
    return ECH0129NamedId(id_category=category, id_value=id_val)


def _street_section() -> ECH0129StreetSection:
    return ECH0129StreetSection(
        esid=10000001, swiss_zip_code=3983, swiss_zip_code_add_on='00'
    )


def _coordinates() -> ECH0129Coordinates:
    return ECH0129Coordinates(east='2640000.000', north='1130000.000')


def _street_desc() -> ECH0129AddressStreetDescription:
    return ECH0129AddressStreetDescription(
        entries=[
            ECH0129AddressStreetEntry(
                language=StreetLanguage.GERMAN,
                description_long='Hauptstrasse',
            )
        ]
    )


def _roundtrip(obj):
    """Serialize to XML and deserialize back."""
    elem = obj.to_xml()
    return obj.__class__.from_xml(elem)


# ===========================================================================
# ECH0129AddressStreetEntry
# ===========================================================================

class TestAddressStreetEntry:
    def test_minimal(self):
        entry = ECH0129AddressStreetEntry(
            language=StreetLanguage.GERMAN,
            description_long='Bahnhofstrasse',
        )
        assert entry.language == StreetLanguage.GERMAN
        assert entry.description_long == 'Bahnhofstrasse'

    def test_description_long_too_short(self):
        with pytest.raises(Exception):
            ECH0129AddressStreetEntry(
                language=StreetLanguage.GERMAN, description_long=''
            )

    def test_description_long_too_long(self):
        with pytest.raises(Exception):
            ECH0129AddressStreetEntry(
                language=StreetLanguage.GERMAN, description_long='x' * 61
            )

    def test_description_long_max(self):
        entry = ECH0129AddressStreetEntry(
            language=StreetLanguage.FRENCH, description_long='x' * 60
        )
        assert len(entry.description_long) == 60


# ===========================================================================
# ECH0129AddressStreetDescription
# ===========================================================================

class TestAddressStreetDescription:
    def test_single_language(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                )
            ]
        )
        assert len(desc.entries) == 1

    def test_multiple_languages(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Rue de la gare',
                ),
            ]
        )
        assert len(desc.entries) == 2

    def test_max_four_languages(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN, description_long='Strasse'
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH, description_long='Rue'
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.ITALIAN, description_long='Via'
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.ROMANSH, description_long='Via'
                ),
            ]
        )
        assert len(desc.entries) == 4

    def test_reject_five_languages(self):
        with pytest.raises(Exception):
            ECH0129AddressStreetDescription(
                entries=[
                    ECH0129AddressStreetEntry(
                        language=StreetLanguage.GERMAN, description_long='A'
                    )
                ] * 5
            )

    def test_reject_empty(self):
        with pytest.raises(Exception):
            ECH0129AddressStreetDescription(entries=[])

    def test_to_xml_single(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                )
            ]
        )
        elem = desc.to_xml()
        ns = NS.ECH0129_V6
        assert elem.tag == f'{{{ns}}}streetDescription'
        children = list(elem)
        assert len(children) == 2
        assert children[0].tag == f'{{{ns}}}language'
        assert children[0].text == '9901'
        assert children[1].tag == f'{{{ns}}}descriptionLong'
        assert children[1].text == 'Bahnhofstrasse'

    def test_to_xml_multi(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Rue de la gare',
                ),
            ]
        )
        elem = desc.to_xml()
        children = list(elem)
        assert len(children) == 4  # 2 entries x 2 elements
        assert children[2].text == '9903'  # FR
        assert children[3].text == 'Rue de la gare'

    def test_roundtrip_single(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Hauptstrasse',
                )
            ]
        )
        rt = _roundtrip(desc)
        assert len(rt.entries) == 1
        assert rt.entries[0].language == StreetLanguage.GERMAN
        assert rt.entries[0].description_long == 'Hauptstrasse'

    def test_roundtrip_multi(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Rue de la gare',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.ITALIAN,
                    description_long='Via della stazione',
                ),
            ]
        )
        rt = _roundtrip(desc)
        assert len(rt.entries) == 3
        assert rt.entries[0].description_long == 'Bahnhofstrasse'
        assert rt.entries[1].language == StreetLanguage.FRENCH
        assert rt.entries[2].description_long == 'Via della stazione'


# ===========================================================================
# ECH0129BuildingEntranceIdentification
# ===========================================================================

class TestBuildingEntranceIdentification:
    def test_minimal_required(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=123456, local_id=_named_id()
        )
        assert obj.egid == 123456
        assert obj.egaid is None
        assert obj.edid is None

    def test_all_fields(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=123456,
            egaid=100000001,
            edid=1,
            local_id=_named_id(),
        )
        assert obj.egaid == 100000001
        assert obj.edid == 1

    def test_egid_range_min(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, local_id=_named_id()
        )
        assert obj.egid == 1

    def test_egid_range_max(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=900000000, local_id=_named_id()
        )
        assert obj.egid == 900000000

    def test_egid_too_low(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntranceIdentification(
                egid=0, local_id=_named_id()
            )

    def test_egid_too_high(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntranceIdentification(
                egid=900000001, local_id=_named_id()
            )

    def test_egaid_range(self):
        # Min
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, egaid=100000000, local_id=_named_id()
        )
        assert obj.egaid == 100000000
        # Max
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, egaid=900000000, local_id=_named_id()
        )
        assert obj.egaid == 900000000

    def test_egaid_too_low(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntranceIdentification(
                egid=1, egaid=99999999, local_id=_named_id()
            )

    def test_edid_range(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, edid=0, local_id=_named_id()
        )
        assert obj.edid == 0
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, edid=90, local_id=_named_id()
        )
        assert obj.edid == 90

    def test_edid_too_high(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntranceIdentification(
                egid=1, edid=91, local_id=_named_id()
            )

    def test_roundtrip_minimal(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=123456, local_id=_named_id()
        )
        rt = _roundtrip(obj)
        assert rt.egid == 123456
        assert rt.egaid is None
        assert rt.edid is None
        assert rt.local_id.id_category == 'GWR'

    def test_roundtrip_full(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=123456, egaid=100000001, edid=3,
            local_id=_named_id('MADD', '999'),
        )
        rt = _roundtrip(obj)
        assert rt.egid == 123456
        assert rt.egaid == 100000001
        assert rt.edid == 3
        assert rt.local_id.id_value == '999'

    def test_xml_element_order(self):
        obj = ECH0129BuildingEntranceIdentification(
            egid=1, egaid=100000000, edid=0,
            local_id=_named_id(),
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == ['EGID', 'EGAID', 'EDID', 'localID']


# ===========================================================================
# ECH0129BuildingEntrance
# ===========================================================================

class TestBuildingEntrance:
    def test_minimal(self):
        obj = ECH0129BuildingEntrance(
            local_id=_named_id(),
            street_section=_street_section(),
        )
        assert obj.egaid is None
        assert obj.edid is None
        assert obj.building_entrance_no is None
        assert obj.coordinates is None
        assert obj.is_official_address is None

    def test_all_fields(self):
        obj = ECH0129BuildingEntrance(
            egaid=100000001,
            edid=1,
            building_entrance_no='12a',
            coordinates=_coordinates(),
            local_id=_named_id(),
            is_official_address=True,
            street_section=_street_section(),
        )
        assert obj.egaid == 100000001
        assert obj.building_entrance_no == '12a'
        assert obj.is_official_address is True

    def test_building_entrance_no_too_long(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntrance(
                local_id=_named_id(),
                street_section=_street_section(),
                building_entrance_no='x' * 13,
            )

    def test_building_entrance_no_empty_rejected(self):
        with pytest.raises(Exception):
            ECH0129BuildingEntrance(
                local_id=_named_id(),
                street_section=_street_section(),
                building_entrance_no='',
            )

    def test_roundtrip_minimal(self):
        obj = ECH0129BuildingEntrance(
            local_id=_named_id(),
            street_section=_street_section(),
        )
        rt = _roundtrip(obj)
        assert rt.egaid is None
        assert rt.local_id.id_category == 'GWR'
        assert rt.street_section.esid == 10000001

    def test_roundtrip_full(self):
        obj = ECH0129BuildingEntrance(
            egaid=200000000,
            edid=5,
            building_entrance_no='42',
            coordinates=_coordinates(),
            local_id=_named_id('TEST', 'abc'),
            is_official_address=False,
            street_section=_street_section(),
        )
        rt = _roundtrip(obj)
        assert rt.egaid == 200000000
        assert rt.edid == 5
        assert rt.building_entrance_no == '42'
        assert rt.coordinates.east == '2640000.000'
        assert rt.is_official_address is False
        assert rt.street_section.swiss_zip_code == 3983

    def test_xml_element_order(self):
        obj = ECH0129BuildingEntrance(
            egaid=100000000,
            edid=0,
            building_entrance_no='1',
            coordinates=_coordinates(),
            local_id=_named_id(),
            is_official_address=True,
            street_section=_street_section(),
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == [
            'EGAID', 'EDID', 'buildingEntranceNo', 'coordinates',
            'localID', 'isOfficialAddress', 'streetSection',
        ]


# ===========================================================================
# ECH0129BuildingEntranceOnly
# ===========================================================================

class TestBuildingEntranceOnly:
    def test_minimal(self):
        obj = ECH0129BuildingEntranceOnly(local_id=_named_id())
        assert obj.egaid is None
        assert obj.is_official_address is None

    def test_all_fields(self):
        obj = ECH0129BuildingEntranceOnly(
            egaid=100000001,
            edid=2,
            building_entrance_no='7b',
            coordinates=_coordinates(),
            local_id=_named_id(),
            is_official_address=True,
        )
        assert obj.egaid == 100000001
        assert obj.building_entrance_no == '7b'

    def test_no_street_section(self):
        """buildingEntranceOnlyType has no streetSection field."""
        assert not hasattr(ECH0129BuildingEntranceOnly, 'street_section') or \
            'street_section' not in ECH0129BuildingEntranceOnly.model_fields

    def test_roundtrip(self):
        obj = ECH0129BuildingEntranceOnly(
            egaid=300000000,
            edid=10,
            building_entrance_no='A',
            coordinates=_coordinates(),
            local_id=_named_id(),
            is_official_address=False,
        )
        rt = _roundtrip(obj)
        assert rt.egaid == 300000000
        assert rt.edid == 10
        assert rt.building_entrance_no == 'A'
        assert rt.is_official_address is False

    def test_xml_element_order(self):
        obj = ECH0129BuildingEntranceOnly(
            egaid=100000000,
            edid=0,
            building_entrance_no='1',
            coordinates=_coordinates(),
            local_id=_named_id(),
            is_official_address=True,
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == [
            'EGAID', 'EDID', 'buildingEntranceNo', 'coordinates',
            'localID', 'isOfficialAddress',
        ]


# ===========================================================================
# ECH0129BuildingAddress
# ===========================================================================

class TestBuildingAddress:
    def test_minimal_required(self):
        obj = ECH0129BuildingAddress(
            egaid=100000001,
            egid=123456,
            edid=1,
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Mörel-Filet',
            municipality_id=6198,
            municipality_name='Mörel-Filet',
            status=BuildingStatus.EXISTING,
        )
        assert obj.egaid == 100000001
        assert obj.building_name is None
        assert obj.street_description is None
        assert obj.coordinates is None
        assert obj.is_official_address is None

    def test_all_fields(self):
        obj = ECH0129BuildingAddress(
            egaid=100000001,
            egid=123456,
            edid=1,
            building_name='Gemeindehaus',
            building_entrance_no='12',
            esid=10000001,
            street_description=_street_desc(),
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Mörel-Filet',
            municipality_id=6198,
            municipality_name='Mörel-Filet',
            coordinates=_coordinates(),
            status=BuildingStatus.EXISTING,
            is_official_address=True,
        )
        assert obj.building_name == 'Gemeindehaus'
        assert obj.esid == 10000001
        assert obj.is_official_address is True

    def test_building_name_constraints(self):
        # min 3 chars
        with pytest.raises(Exception):
            ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                building_name='AB',
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='Bister', municipality_id=6198,
                municipality_name='Bister',
                status=BuildingStatus.EXISTING,
            )
        # max 40 chars
        with pytest.raises(Exception):
            ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                building_name='x' * 41,
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='Bister', municipality_id=6198,
                municipality_name='Bister',
                status=BuildingStatus.EXISTING,
            )

    def test_locality_constraints(self):
        # min 2 chars
        with pytest.raises(Exception):
            ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='A',
                municipality_id=6198,
                municipality_name='Bister',
                status=BuildingStatus.EXISTING,
            )
        # max 40 chars
        with pytest.raises(Exception):
            ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='x' * 41,
                municipality_id=6198,
                municipality_name='Bister',
                status=BuildingStatus.EXISTING,
            )

    def test_municipality_id_range(self):
        # Valid range
        obj = ECH0129BuildingAddress(
            egaid=100000001, egid=1, edid=0,
            swiss_zip_code=3983, swiss_zip_code_add_on='00',
            locality='Bister', municipality_id=1,
            municipality_name='Test', status=BuildingStatus.EXISTING,
        )
        assert obj.municipality_id == 1
        # Too high
        with pytest.raises(Exception):
            ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='Bister', municipality_id=10000,
                municipality_name='Test', status=BuildingStatus.EXISTING,
            )

    def test_roundtrip_minimal(self):
        obj = ECH0129BuildingAddress(
            egaid=100000001, egid=123456, edid=1,
            swiss_zip_code=3983, swiss_zip_code_add_on='00',
            locality='Mörel-Filet',
            municipality_id=6198, municipality_name='Mörel-Filet',
            status=BuildingStatus.EXISTING,
        )
        rt = _roundtrip(obj)
        assert rt.egaid == 100000001
        assert rt.egid == 123456
        assert rt.edid == 1
        assert rt.swiss_zip_code == 3983
        assert rt.locality == 'Mörel-Filet'
        assert rt.municipality_id == 6198
        assert rt.status == BuildingStatus.EXISTING
        assert rt.building_name is None
        assert rt.street_description is None

    def test_roundtrip_full(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Hauptstrasse',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Route principale',
                ),
            ]
        )
        obj = ECH0129BuildingAddress(
            egaid=200000000, egid=999, edid=5,
            building_name='Gemeindehaus',
            building_entrance_no='1a',
            esid=20000000,
            street_description=desc,
            swiss_zip_code=3983, swiss_zip_code_add_on='00',
            locality='Bister',
            municipality_id=6198, municipality_name='Bister',
            coordinates=_coordinates(),
            status=BuildingStatus.PROJECTED,
            is_official_address=True,
        )
        rt = _roundtrip(obj)
        assert rt.building_name == 'Gemeindehaus'
        assert rt.building_entrance_no == '1a'
        assert rt.esid == 20000000
        assert len(rt.street_description.entries) == 2
        assert rt.street_description.entries[0].description_long == 'Hauptstrasse'
        assert rt.street_description.entries[1].language == StreetLanguage.FRENCH
        assert rt.coordinates.east == '2640000.000'
        assert rt.status == BuildingStatus.PROJECTED
        assert rt.is_official_address is True

    def test_xml_element_order(self):
        obj = ECH0129BuildingAddress(
            egaid=100000001, egid=1, edid=0,
            building_name='Test Building',
            building_entrance_no='1',
            esid=10000001,
            street_description=_street_desc(),
            swiss_zip_code=3983, swiss_zip_code_add_on='00',
            locality='Bister',
            municipality_id=6198, municipality_name='Bister',
            coordinates=_coordinates(),
            status=BuildingStatus.EXISTING,
            is_official_address=True,
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == [
            'EGAID', 'EGID', 'EDID', 'buildingName',
            'buildingEntranceNo', 'ESID', 'streetDescription',
            'swissZipCode', 'swissZipCodeAddOn', 'locality',
            'municipalityId', 'municipalityName', 'coordinates',
            'status', 'isOfficialAddress',
        ]

    def test_all_status_values(self):
        """All BuildingStatus enum values should be accepted."""
        for status in BuildingStatus:
            obj = ECH0129BuildingAddress(
                egaid=100000001, egid=1, edid=0,
                swiss_zip_code=3983, swiss_zip_code_add_on='00',
                locality='Bister', municipality_id=6198,
                municipality_name='Bister', status=status,
            )
            assert obj.status == status


# ===========================================================================
# ECH0129BuildingAddressLight
# ===========================================================================

class TestBuildingAddressLight:
    def test_branch_egaid(self):
        obj = ECH0129BuildingAddressLight(
            egaid=100000001,
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        assert obj.egaid == 100000001
        assert obj.egid is None
        assert obj.edid is None

    def test_branch_egid_edid(self):
        obj = ECH0129BuildingAddressLight(
            egid=123456,
            edid=1,
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        assert obj.egaid is None
        assert obj.egid == 123456
        assert obj.edid == 1

    def test_reject_both_branches(self):
        """EGAID and EGID/EDID are mutually exclusive."""
        with pytest.raises(ValueError, match='mutually exclusive'):
            ECH0129BuildingAddressLight(
                egaid=100000001,
                egid=123456,
                edid=1,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_reject_egaid_with_egid_only(self):
        with pytest.raises(ValueError, match='mutually exclusive'):
            ECH0129BuildingAddressLight(
                egaid=100000001,
                egid=123456,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_reject_egaid_with_edid_only(self):
        with pytest.raises(ValueError, match='mutually exclusive'):
            ECH0129BuildingAddressLight(
                egaid=100000001,
                edid=1,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_reject_no_id(self):
        """Must set either EGAID or (EGID + EDID)."""
        with pytest.raises(ValueError, match='must set either'):
            ECH0129BuildingAddressLight(
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_reject_egid_without_edid(self):
        with pytest.raises(ValueError, match='EGID requires EDID'):
            ECH0129BuildingAddressLight(
                egid=123456,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_reject_edid_without_egid(self):
        with pytest.raises(ValueError, match='EDID requires EGID'):
            ECH0129BuildingAddressLight(
                edid=1,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )

    def test_all_optional_fields(self):
        obj = ECH0129BuildingAddressLight(
            egaid=100000001,
            building_entrance_no='5',
            esid=10000001,
            street_description=_street_desc(),
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        assert obj.building_entrance_no == '5'
        assert obj.esid == 10000001
        assert len(obj.street_description.entries) == 1

    def test_roundtrip_egaid_branch(self):
        obj = ECH0129BuildingAddressLight(
            egaid=100000001,
            building_entrance_no='12',
            esid=20000000,
            street_description=_street_desc(),
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        rt = _roundtrip(obj)
        assert rt.egaid == 100000001
        assert rt.egid is None
        assert rt.edid is None
        assert rt.building_entrance_no == '12'
        assert rt.esid == 20000000
        assert len(rt.street_description.entries) == 1
        assert rt.swiss_zip_code == 3983
        assert rt.locality == 'Bister'

    def test_roundtrip_egid_edid_branch(self):
        obj = ECH0129BuildingAddressLight(
            egid=999999,
            edid=42,
            swiss_zip_code=8000,
            swiss_zip_code_add_on='01',
            locality='Zürich',
        )
        rt = _roundtrip(obj)
        assert rt.egaid is None
        assert rt.egid == 999999
        assert rt.edid == 42
        assert rt.swiss_zip_code == 8000
        assert rt.locality == 'Zürich'

    def test_roundtrip_full_with_street(self):
        desc = ECH0129AddressStreetDescription(
            entries=[
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                ),
                ECH0129AddressStreetEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Rue de la gare',
                ),
            ]
        )
        obj = ECH0129BuildingAddressLight(
            egaid=200000000,
            building_entrance_no='3a',
            esid=30000000,
            street_description=desc,
            swiss_zip_code=3000,
            swiss_zip_code_add_on='25',
            locality='Bern',
        )
        rt = _roundtrip(obj)
        assert rt.egaid == 200000000
        assert rt.building_entrance_no == '3a'
        assert len(rt.street_description.entries) == 2
        assert rt.street_description.entries[1].language == StreetLanguage.FRENCH

    def test_xml_element_order_egaid(self):
        obj = ECH0129BuildingAddressLight(
            egaid=100000001,
            building_entrance_no='1',
            esid=10000001,
            street_description=_street_desc(),
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == [
            'EGAID', 'buildingEntranceNo', 'ESID',
            'streetDescription', 'swissZipCode',
            'swissZipCodeAddOn', 'locality',
        ]

    def test_xml_element_order_egid_edid(self):
        obj = ECH0129BuildingAddressLight(
            egid=123456, edid=1,
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            locality='Bister',
        )
        elem = obj.to_xml()
        children = [c.tag.split('}')[1] for c in elem]
        assert children == [
            'EGID', 'EDID', 'swissZipCode',
            'swissZipCodeAddOn', 'locality',
        ]

    def test_locality_constraints(self):
        with pytest.raises(Exception):
            ECH0129BuildingAddressLight(
                egaid=100000001,
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='A',  # too short
            )

    def test_egaid_range(self):
        with pytest.raises(Exception):
            ECH0129BuildingAddressLight(
                egaid=99999999,  # below 100000000
                swiss_zip_code=3983,
                swiss_zip_code_add_on='00',
                locality='Bister',
            )
