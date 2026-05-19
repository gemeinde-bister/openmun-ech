"""Tests for eCH-0129 v6.0.0 building types (Session 9).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — choice constraints, field ranges, list cardinality
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. XML element names and ordering (xs:sequence)
"""

import xml.etree.ElementTree as ET

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import (
    BuildingCategory,
    BuildingStatus,
    EnergySource,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    RealestateType,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129BuildingDate,
    ECH0129BuildingVolume,
    ECH0129Coordinates,
    ECH0129DatePartiallyKnown,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129NamedId,
    ECH0129NamedMetaData,
)
from openmun_ech.ech0129.v6.building import (
    ECH0129Building,
    ECH0129BuildingIdentification,
    ECH0129BuildingOnly,
)
from openmun_ech.ech0129.v6.entrance import ECH0129BuildingEntrance
from openmun_ech.ech0129.v6.street_locality import (
    ECH0129StreetSection,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# Helpers
# ===========================================================================

def _make_named_id(category='IDBBP', value='12345'):
    return ECH0129NamedId(id_category=category, id_value=value)


def _make_building_id_egid(**kwargs):
    """Create a BuildingIdentification with branch 1 (EGID)."""
    defaults = {
        'egid': 123456789,
        'local_id': [_make_named_id()],
        'municipality': 6002,
    }
    defaults.update(kwargs)
    return ECH0129BuildingIdentification(**defaults)


def _make_building_id_address(**kwargs):
    """Create a BuildingIdentification with branch 2 (address)."""
    defaults = {
        'street': 'Bahnhofstrasse',
        'house_number': '42',
        'zip_code': 3983,
        'local_id': [_make_named_id()],
        'municipality': 6002,
    }
    defaults.update(kwargs)
    return ECH0129BuildingIdentification(**defaults)


def _make_building_id_egrid(**kwargs):
    """Create a BuildingIdentification with branch 3a (EGRID)."""
    defaults = {
        'egrid': 'CH123456789012',
        'official_building_no': 'B001',
        'local_id': [_make_named_id()],
        'municipality': 6002,
    }
    defaults.update(kwargs)
    return ECH0129BuildingIdentification(**defaults)


def _make_building_id_cadaster(**kwargs):
    """Create a BuildingIdentification with branch 3b (cadaster)."""
    defaults = {
        'cadaster_area_number': 'CA-1234',
        'number': '567',
        'official_building_no': 'B002',
        'local_id': [_make_named_id()],
        'municipality': 6002,
    }
    defaults.update(kwargs)
    return ECH0129BuildingIdentification(**defaults)


def _make_building(**kwargs):
    """Create a Building with required fields + overrides."""
    defaults = {
        'building_category': BuildingCategory.RESIDENTIAL_ONLY,
    }
    defaults.update(kwargs)
    return ECH0129Building(**defaults)


def _make_building_only(**kwargs):
    """Create a BuildingOnly with required fields + overrides."""
    defaults = {
        'building_category': BuildingCategory.RESIDENTIAL_ONLY,
    }
    defaults.update(kwargs)
    return ECH0129BuildingOnly(**defaults)


def _make_street_section():
    """Create a minimal StreetSection for entrance tests."""
    return ECH0129StreetSection(
        esid=12345678,
        local_id=_make_named_id('ESID', '99'),
        swiss_zip_code=3983,
        swiss_zip_code_add_on='00',
    )


def _make_entrance():
    """Create a minimal BuildingEntrance."""
    return ECH0129BuildingEntrance(
        local_id=_make_named_id('EDID', '1'),
        street_section=_make_street_section(),
    )


def _roundtrip(obj):
    """Serialize to XML and back, return the new object."""
    xml = obj.to_xml()
    return type(obj).from_xml(xml)


def _child_names(elem):
    """Get local element names of direct children."""
    return [
        c.tag.split('}')[1] if '}' in c.tag else c.tag
        for c in elem
    ]


# ===========================================================================
# ECH0129BuildingIdentification
# ===========================================================================

class TestBuildingIdentification:
    """Tests for buildingIdentificationType (XSD lines 442-474)."""

    # --- Branch 1: EGID ---

    def test_branch1_egid(self):
        """EGID branch with required after-choice fields."""
        bi = _make_building_id_egid()
        assert bi.egid == 123456789
        assert bi.municipality == 6002
        assert len(bi.local_id) == 1

    def test_branch1_egid_roundtrip(self):
        bi = _make_building_id_egid()
        bi2 = _roundtrip(bi)
        assert bi2.egid == bi.egid
        assert bi2.municipality == bi.municipality
        assert bi2.local_id[0].id_category == bi.local_id[0].id_category

    def test_branch1_xml_element_order(self):
        bi = _make_building_id_egid()
        xml = bi.to_xml()
        names = _child_names(xml)
        assert names == ['EGID', 'localID', 'municipality']

    def test_branch1_egid_range(self):
        with pytest.raises(ValueError):
            _make_building_id_egid(egid=0)
        with pytest.raises(ValueError):
            _make_building_id_egid(egid=900000001)

    # --- Branch 2: Address ---

    def test_branch2_address_minimal(self):
        bi = _make_building_id_address()
        assert bi.street == 'Bahnhofstrasse'
        assert bi.house_number == '42'
        assert bi.zip_code == 3983
        assert bi.name_of_building is None

    def test_branch2_address_with_name(self):
        bi = _make_building_id_address(name_of_building='Gemeindehaus')
        assert bi.name_of_building == 'Gemeindehaus'

    def test_branch2_address_roundtrip(self):
        bi = _make_building_id_address(name_of_building='Altes Schulhaus')
        bi2 = _roundtrip(bi)
        assert bi2.street == bi.street
        assert bi2.house_number == bi.house_number
        assert bi2.zip_code == bi.zip_code
        assert bi2.name_of_building == bi.name_of_building
        assert bi2.municipality == bi.municipality

    def test_branch2_xml_element_order(self):
        bi = _make_building_id_address(name_of_building='Villa Blau')
        xml = bi.to_xml()
        names = _child_names(xml)
        assert names == [
            'street', 'houseNumber', 'zipCode', 'nameOfBuilding',
            'localID', 'municipality',
        ]

    def test_branch2_missing_street_rejected(self):
        with pytest.raises(ValueError, match='street'):
            ECH0129BuildingIdentification(
                house_number='1', zip_code=3983,
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch2_missing_house_number_rejected(self):
        with pytest.raises(ValueError, match='houseNumber'):
            ECH0129BuildingIdentification(
                street='Hauptstrasse', zip_code=3983,
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch2_missing_zip_code_rejected(self):
        with pytest.raises(ValueError, match='zipCode'):
            ECH0129BuildingIdentification(
                street='Hauptstrasse', house_number='1',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch2_name_constraints(self):
        """nameOfBuildingType: min 3, max 40."""
        with pytest.raises(ValueError):
            _make_building_id_address(name_of_building='AB')
        with pytest.raises(ValueError):
            _make_building_id_address(name_of_building='A' * 41)

    # --- Branch 3a: EGRID ---

    def test_branch3a_egrid(self):
        bi = _make_building_id_egrid()
        assert bi.egrid == 'CH123456789012'
        assert bi.official_building_no == 'B001'

    def test_branch3a_egrid_roundtrip(self):
        bi = _make_building_id_egrid()
        bi2 = _roundtrip(bi)
        assert bi2.egrid == bi.egrid
        assert bi2.official_building_no == bi.official_building_no
        assert bi2.municipality == bi.municipality

    def test_branch3a_xml_element_order(self):
        bi = _make_building_id_egrid()
        xml = bi.to_xml()
        names = _child_names(xml)
        assert names == [
            'EGRID', 'officialBuildingNo', 'localID', 'municipality',
        ]

    def test_branch3a_egrid_max_length(self):
        """EGRIDType: maxLength 14."""
        with pytest.raises(ValueError):
            _make_building_id_egrid(egrid='CH12345678901234')

    # --- Branch 3b: Cadaster ---

    def test_branch3b_cadaster(self):
        bi = _make_building_id_cadaster()
        assert bi.cadaster_area_number == 'CA-1234'
        assert bi.number == '567'
        assert bi.official_building_no == 'B002'
        assert bi.realestate_type is None

    def test_branch3b_cadaster_with_type(self):
        bi = _make_building_id_cadaster(
            realestate_type=RealestateType.LIEGENSCHAFT,
        )
        assert bi.realestate_type == RealestateType.LIEGENSCHAFT

    def test_branch3b_cadaster_roundtrip(self):
        bi = _make_building_id_cadaster(
            realestate_type=RealestateType.STOCKWERKSEINHEIT,
        )
        bi2 = _roundtrip(bi)
        assert bi2.cadaster_area_number == bi.cadaster_area_number
        assert bi2.number == bi.number
        assert bi2.realestate_type == bi.realestate_type
        assert bi2.official_building_no == bi.official_building_no

    def test_branch3b_xml_element_order(self):
        bi = _make_building_id_cadaster(
            realestate_type=RealestateType.KONZESSION,
        )
        xml = bi.to_xml()
        names = _child_names(xml)
        assert names == [
            'cadasterAreaNumber', 'number', 'realestateType',
            'officialBuildingNo', 'localID', 'municipality',
        ]

    def test_branch3b_cadaster_missing_number_rejected(self):
        with pytest.raises(ValueError, match='number'):
            ECH0129BuildingIdentification(
                cadaster_area_number='CA', official_building_no='B1',
                local_id=[_make_named_id()], municipality=6002,
            )

    # --- Cross-branch validation ---

    def test_no_branch_rejected(self):
        """Must set at least one branch."""
        with pytest.raises(ValueError, match='must set one of'):
            ECH0129BuildingIdentification(
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch1_and_branch2_rejected(self):
        """EGID and address are mutually exclusive."""
        with pytest.raises(ValueError, match='mutually exclusive'):
            ECH0129BuildingIdentification(
                egid=1, street='Hauptstr', house_number='1', zip_code=3000,
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch1_and_branch3_rejected(self):
        """EGID and EGRID are mutually exclusive."""
        with pytest.raises(ValueError, match='mutually exclusive'):
            ECH0129BuildingIdentification(
                egid=1, egrid='CH1234', official_building_no='B1',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch3_egrid_and_cadaster_rejected(self):
        """EGRID and cadasterAreaNumber are mutually exclusive."""
        with pytest.raises(ValueError, match='EGRID and cadasterAreaNumber'):
            ECH0129BuildingIdentification(
                egrid='CH1234', cadaster_area_number='CA',
                number='1', official_building_no='B1',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch3_egrid_with_number_rejected(self):
        """number only valid with cadasterAreaNumber, not EGRID."""
        with pytest.raises(ValueError, match='number only valid'):
            ECH0129BuildingIdentification(
                egrid='CH1234', number='99', official_building_no='B1',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch3_egrid_with_realestate_type_rejected(self):
        """realestateType only valid with cadasterAreaNumber."""
        with pytest.raises(ValueError, match='realestateType only valid'):
            ECH0129BuildingIdentification(
                egrid='CH1234', official_building_no='B1',
                realestate_type=RealestateType.LIEGENSCHAFT,
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_branch3_missing_official_building_no_rejected(self):
        with pytest.raises(ValueError, match='officialBuildingNo'):
            ECH0129BuildingIdentification(
                egrid='CH1234',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_name_of_building_only_in_branch2(self):
        """nameOfBuilding outside branch 2 is rejected."""
        with pytest.raises(ValueError, match='nameOfBuilding only valid'):
            ECH0129BuildingIdentification(
                egid=1, name_of_building='Villa',
                local_id=[_make_named_id()], municipality=6002,
            )

    def test_realestate_type_only_in_branch3(self):
        """realestateType outside branch 3 is rejected."""
        with pytest.raises(ValueError, match='realestateType only valid'):
            ECH0129BuildingIdentification(
                egid=1, realestate_type=RealestateType.LIEGENSCHAFT,
                local_id=[_make_named_id()], municipality=6002,
            )

    # --- Required after-choice fields ---

    def test_empty_local_id_rejected(self):
        with pytest.raises(ValueError):
            ECH0129BuildingIdentification(
                egid=1, local_id=[], municipality=6002,
            )

    def test_multiple_local_ids(self):
        bi = _make_building_id_egid(
            local_id=[_make_named_id('A', '1'), _make_named_id('B', '2')],
        )
        assert len(bi.local_id) == 2

    def test_multiple_local_ids_roundtrip(self):
        bi = _make_building_id_egid(
            local_id=[_make_named_id('A', '1'), _make_named_id('B', '2')],
        )
        bi2 = _roundtrip(bi)
        assert len(bi2.local_id) == 2
        assert bi2.local_id[0].id_category == 'A'
        assert bi2.local_id[1].id_category == 'B'

    def test_municipality_range(self):
        with pytest.raises(ValueError):
            _make_building_id_egid(municipality=0)
        with pytest.raises(ValueError):
            _make_building_id_egid(municipality=10000)


# ===========================================================================
# ECH0129Building
# ===========================================================================

class TestBuilding:
    """Tests for buildingType (XSD lines 749-779)."""

    def test_create_minimal(self):
        """Only buildingCategory is required."""
        b = _make_building()
        assert b.building_category == BuildingCategory.RESIDENTIAL_ONLY
        assert b.egid is None
        assert b.building_identification is None
        assert b.other_id == []
        assert b.heating == []
        assert b.building_entrance == []
        assert b.building_free_text == []

    def test_create_with_all_scalar_fields(self):
        b = _make_building(
            egid=100000001,
            official_building_no='GEB-001',
            name='Gemeindehaus Bister',
            number_of_floors=3,
            number_of_separate_habitable_rooms=12,
            surface_area_of_building=500,
            sub_surface_area_of_building=200,
            surface_area_of_building_signale_object=80,
            building_class=1210,
            status=BuildingStatus.EXISTING,
            civil_defense_shelter=True,
            neighbourhood=6002,
            energy_relevant_surface=450,
        )
        assert b.egid == 100000001
        assert b.number_of_floors == 3
        assert b.building_class == 1210
        assert b.civil_defense_shelter is True
        assert b.neighbourhood == 6002

    def test_create_with_complex_subobjects(self):
        b = _make_building(
            building_identification=_make_building_id_egid(),
            date_of_construction=ECH0129BuildingDate(year='1985'),
            date_of_renovation=ECH0129BuildingDate(year='2020'),
            date_of_demolition=ECH0129DatePartiallyKnown(year='2099'),
            coordinates=ECH0129Coordinates(
                east='2640000.000', north='1130000.000',
            ),
            volume=ECH0129BuildingVolume(volume=5000),
        )
        assert b.building_identification.egid == 123456789
        assert b.date_of_construction.year == '1985'
        assert b.volume.volume == 5000

    def test_create_with_list_fields(self):
        b = _make_building(
            other_id=[_make_named_id('GIS', 'A1')],
            local_code=['AB12', 'CD34'],
            heating=[ECH0129Heating(
                heat_generator_heating=HeatGeneratorHeating.HEAT_PUMP_SINGLE,
                energy_source_heating=EnergySource.AIR,
            )],
            hot_water=[ECH0129HotWater(
                heat_generator_hot_water=HeatGeneratorHotWater.HEAT_PUMP,
            )],
            building_entrance=[_make_entrance()],
            named_meta_data=[ECH0129NamedMetaData(
                meta_data_name='source', meta_data_value='GWR',
            )],
            building_free_text=['Historic building'],
        )
        assert len(b.other_id) == 1
        assert len(b.local_code) == 2
        assert len(b.heating) == 1
        assert len(b.building_entrance) == 1
        assert len(b.building_free_text) == 1

    def test_missing_building_category_rejected(self):
        with pytest.raises(ValueError):
            ECH0129Building()

    def test_xml_element_order_minimal(self):
        b = _make_building()
        xml = b.to_xml()
        names = _child_names(xml)
        assert names == ['buildingCategory']

    def test_xml_element_order_full(self):
        """Verify element ordering matches XSD sequence."""
        b = _make_building(
            building_identification=_make_building_id_egid(),
            egid=999,
            official_building_no='B1',
            name='Testgebäude',
            date_of_construction=ECH0129BuildingDate(year='1990'),
            number_of_floors=2,
            building_class=1150,
            status=BuildingStatus.EXISTING,
            other_id=[_make_named_id()],
            civil_defense_shelter=False,
            neighbourhood=6002,
            local_code=['A1'],
            heating=[ECH0129Heating()],
            named_meta_data=[ECH0129NamedMetaData(
                meta_data_name='k', meta_data_value='v',
            )],
            building_free_text=['note'],
        )
        xml = b.to_xml()
        names = _child_names(xml)
        expected = [
            'buildingIdentification', 'EGID', 'officialBuildingNo',
            'name', 'dateOfConstruction',
            'numberOfFloors',
            'buildingCategory', 'buildingClass', 'status',
            'otherID', 'civilDefenseShelter', 'neighbourhood',
            'localCode', 'heating',
            'namedMetaData', 'buildingFreeText',
        ]
        assert names == expected

    def test_roundtrip_minimal(self):
        b = _make_building()
        b2 = _roundtrip(b)
        assert b2.building_category == b.building_category

    def test_roundtrip_full(self):
        b = _make_building(
            egid=100000001,
            official_building_no='GEB-001',
            name='Gemeindehaus Bister',
            number_of_floors=3,
            number_of_separate_habitable_rooms=12,
            surface_area_of_building=500,
            sub_surface_area_of_building=200,
            surface_area_of_building_signale_object=80,
            building_class=1210,
            status=BuildingStatus.EXISTING,
            civil_defense_shelter=True,
            neighbourhood=6002,
            energy_relevant_surface=450,
            other_id=[_make_named_id('GIS', 'A1')],
            local_code=['AB12'],
            building_free_text=['historic'],
        )
        b2 = _roundtrip(b)
        assert b2.egid == 100000001
        assert b2.official_building_no == 'GEB-001'
        assert b2.name == 'Gemeindehaus Bister'
        assert b2.number_of_floors == 3
        assert b2.number_of_separate_habitable_rooms == 12
        assert b2.surface_area_of_building == 500
        assert b2.sub_surface_area_of_building == 200
        assert b2.surface_area_of_building_signale_object == 80
        assert b2.building_class == 1210
        assert b2.status == BuildingStatus.EXISTING
        assert b2.civil_defense_shelter is True
        assert b2.neighbourhood == 6002
        assert b2.energy_relevant_surface == 450
        assert len(b2.other_id) == 1
        assert b2.other_id[0].id_category == 'GIS'
        assert b2.local_code == ['AB12']
        assert b2.building_free_text == ['historic']

    def test_roundtrip_with_subobjects(self):
        b = _make_building(
            building_identification=_make_building_id_address(
                name_of_building='Schulhaus',
            ),
            date_of_construction=ECH0129BuildingDate(year='1985'),
            volume=ECH0129BuildingVolume(volume=5000),
            heating=[ECH0129Heating(
                heat_generator_heating=HeatGeneratorHeating.HEAT_PUMP_SINGLE,
            )],
            hot_water=[ECH0129HotWater(
                heat_generator_hot_water=HeatGeneratorHotWater.BOILER_GENERIC,
            )],
            building_entrance=[_make_entrance()],
            named_meta_data=[ECH0129NamedMetaData(
                meta_data_name='src', meta_data_value='GWR',
            )],
        )
        b2 = _roundtrip(b)
        assert b2.building_identification.street == 'Bahnhofstrasse'
        assert b2.building_identification.name_of_building == 'Schulhaus'
        assert b2.date_of_construction.year == '1985'
        assert b2.volume.volume == 5000
        assert len(b2.heating) == 1
        assert b2.heating[0].heat_generator_heating == (
            HeatGeneratorHeating.HEAT_PUMP_SINGLE
        )
        assert len(b2.hot_water) == 1
        assert len(b2.building_entrance) == 1
        assert len(b2.named_meta_data) == 1

    def test_signale_object_xml_name(self):
        """XSD has typo 'Signale' in element name — verify preserved."""
        b = _make_building(surface_area_of_building_signale_object=100)
        xml = b.to_xml()
        names = _child_names(xml)
        assert 'surfaceAreaOfBuildingSignaleObject' in names

    # --- Field constraint validation ---

    def test_building_class_range(self):
        with pytest.raises(ValueError):
            _make_building(building_class=1109)
        with pytest.raises(ValueError):
            _make_building(building_class=1279)
        # Valid boundaries
        assert _make_building(building_class=1110).building_class == 1110
        assert _make_building(building_class=1278).building_class == 1278

    def test_number_of_floors_range(self):
        with pytest.raises(ValueError):
            _make_building(number_of_floors=0)
        with pytest.raises(ValueError):
            _make_building(number_of_floors=100)

    def test_neighbourhood_range(self):
        with pytest.raises(ValueError):
            _make_building(neighbourhood=999)
        with pytest.raises(ValueError):
            _make_building(neighbourhood=10000000)

    def test_energy_relevant_surface_range(self):
        with pytest.raises(ValueError):
            _make_building(energy_relevant_surface=4)
        with pytest.raises(ValueError):
            _make_building(energy_relevant_surface=900001)

    # --- List cardinality validation ---

    def test_local_code_max_4(self):
        with pytest.raises(ValueError, match='maxOccurs=4'):
            _make_building(local_code=['A', 'B', 'C', 'D', 'E'])

    def test_local_code_item_length(self):
        with pytest.raises(ValueError, match='1-8 chars'):
            _make_building(local_code=[''])
        with pytest.raises(ValueError, match='1-8 chars'):
            _make_building(local_code=['123456789'])

    def test_heating_max_2(self):
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_building(heating=[
                ECH0129Heating(), ECH0129Heating(), ECH0129Heating(),
            ])

    def test_hot_water_max_2(self):
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_building(hot_water=[
                ECH0129HotWater(), ECH0129HotWater(), ECH0129HotWater(),
            ])

    def test_building_free_text_max_2(self):
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_building(building_free_text=['a', 'b', 'c'])

    def test_building_free_text_item_length(self):
        with pytest.raises(ValueError, match='1-32 chars'):
            _make_building(building_free_text=[''])
        with pytest.raises(ValueError, match='1-32 chars'):
            _make_building(building_free_text=['A' * 33])


# ===========================================================================
# ECH0129BuildingOnly
# ===========================================================================

class TestBuildingOnly:
    """Tests for buildingOnlyType (XSD lines 781-815)."""

    def test_create_minimal(self):
        b = _make_building_only()
        assert b.building_category == BuildingCategory.RESIDENTIAL_ONLY

    def test_no_building_entrance_field(self):
        """buildingOnlyType has no buildingEntrance field."""
        assert not hasattr(ECH0129BuildingOnly, 'building_entrance') or \
            'building_entrance' not in ECH0129BuildingOnly.model_fields

    def test_create_with_fields(self):
        b = _make_building_only(
            egid=100000001,
            name='Gemeindehaus',
            building_class=1210,
            status=BuildingStatus.EXISTING,
            heating=[ECH0129Heating()],
            named_meta_data=[ECH0129NamedMetaData(
                meta_data_name='k', meta_data_value='v',
            )],
        )
        assert b.egid == 100000001
        assert b.name == 'Gemeindehaus'
        assert len(b.heating) == 1
        assert len(b.named_meta_data) == 1

    def test_roundtrip(self):
        b = _make_building_only(
            egid=100000001,
            name='Kapelle',
            building_category=BuildingCategory.SPECIAL,
            building_class=1278,
            status=BuildingStatus.EXISTING,
            civil_defense_shelter=False,
            local_code=['A1', 'B2'],
            building_free_text=['chapel'],
        )
        b2 = _roundtrip(b)
        assert b2.egid == 100000001
        assert b2.name == 'Kapelle'
        assert b2.building_category == BuildingCategory.SPECIAL
        assert b2.building_class == 1278
        assert b2.status == BuildingStatus.EXISTING
        assert b2.civil_defense_shelter is False
        assert b2.local_code == ['A1', 'B2']
        assert b2.building_free_text == ['chapel']

    def test_xml_element_name(self):
        """buildingOnlyType uses 'buildingOnly' as element name."""
        b = _make_building_only()
        xml = b.to_xml()
        local = xml.tag.split('}')[1] if '}' in xml.tag else xml.tag
        assert local == 'buildingOnly'

    def test_xml_element_order(self):
        b = _make_building_only(
            egid=1,
            status=BuildingStatus.EXISTING,
            named_meta_data=[ECH0129NamedMetaData(
                meta_data_name='k', meta_data_value='v',
            )],
            building_free_text=['note'],
        )
        xml = b.to_xml()
        names = _child_names(xml)
        expected = [
            'EGID', 'buildingCategory', 'status',
            'namedMetaData', 'buildingFreeText',
        ]
        assert names == expected

    # --- Same list validators as buildingType ---

    def test_local_code_max_4(self):
        with pytest.raises(ValueError, match='maxOccurs=4'):
            _make_building_only(local_code=['A', 'B', 'C', 'D', 'E'])

    def test_heating_max_2(self):
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_building_only(heating=[
                ECH0129Heating(), ECH0129Heating(), ECH0129Heating(),
            ])

    def test_building_free_text_max_2(self):
        with pytest.raises(ValueError, match='maxOccurs=2'):
            _make_building_only(building_free_text=['a', 'b', 'c'])
