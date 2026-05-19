"""Tests for eCH-0129 v6.0.0 base types (Session 2).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints, xs:choice enforcement
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. Nillable handling — xsi:nil="true" on buildingVolumeType
5. Cross-namespace references — personIdentificationType
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0044 import ECH0044PersonIdentificationLight, ECH0044NamedPersonId
from openmun_ech.ech0097 import (
    ECH0097OrganisationIdentification,
    ECH0097NamedOrganisationId,
)
from openmun_ech.ech0129.enums import (
    BuildingVolumeInformationSource,
    BuildingVolumeNorm,
    EnergySource,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    InformationSource,
    OriginOfCoordinates,
    PeriodOfConstruction,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129BuildingDate,
    ECH0129BuildingVolume,
    ECH0129Contact,
    ECH0129Coordinates,
    ECH0129DatePartiallyKnown,
    ECH0129DateRange,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129NamedId,
    ECH0129NamedMetaData,
    ECH0129PersonIdentification,
    XSI_NS,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# ECH0129DateRange
# ===========================================================================

class TestDateRange:
    def test_both_dates(self):
        dr = ECH0129DateRange(
            date_from=date(2020, 1, 1), date_to=date(2025, 12, 31)
        )
        assert dr.date_from == date(2020, 1, 1)
        assert dr.date_to == date(2025, 12, 31)

    def test_only_from(self):
        dr = ECH0129DateRange(date_from=date(2020, 1, 1))
        assert dr.date_from == date(2020, 1, 1)
        assert dr.date_to is None

    def test_only_to(self):
        dr = ECH0129DateRange(date_to=date(2025, 12, 31))
        assert dr.date_from is None
        assert dr.date_to == date(2025, 12, 31)

    def test_empty(self):
        """Both optional — empty is valid."""
        dr = ECH0129DateRange()
        assert dr.date_from is None
        assert dr.date_to is None

    def test_roundtrip(self):
        dr = ECH0129DateRange(
            date_from=date(2020, 1, 1), date_to=date(2025, 12, 31)
        )
        xml = dr.to_xml()
        parsed = ECH0129DateRange.from_xml(xml)
        assert parsed.date_from == dr.date_from
        assert parsed.date_to == dr.date_to

    def test_roundtrip_partial(self):
        dr = ECH0129DateRange(date_from=date(2020, 6, 15))
        xml = dr.to_xml()
        parsed = ECH0129DateRange.from_xml(xml)
        assert parsed.date_from == dr.date_from
        assert parsed.date_to is None

    def test_xml_element_names(self):
        dr = ECH0129DateRange(
            date_from=date(2020, 1, 1), date_to=date(2025, 12, 31)
        )
        xml = dr.to_xml()
        assert xml.find(f'{{{NS_0129}}}dateFrom') is not None
        assert xml.find(f'{{{NS_0129}}}dateTo') is not None


# ===========================================================================
# ECH0129NamedMetaData
# ===========================================================================

class TestNamedMetaData:
    def test_valid(self):
        md = ECH0129NamedMetaData(
            meta_data_name='canton', meta_data_value='VS'
        )
        assert md.meta_data_name == 'canton'
        assert md.meta_data_value == 'VS'

    def test_name_too_long(self):
        with pytest.raises(Exception):
            ECH0129NamedMetaData(
                meta_data_name='x' * 21, meta_data_value='val'
            )

    def test_name_empty(self):
        with pytest.raises(Exception):
            ECH0129NamedMetaData(meta_data_name='', meta_data_value='val')

    def test_value_empty(self):
        with pytest.raises(Exception):
            ECH0129NamedMetaData(meta_data_name='key', meta_data_value='')

    def test_roundtrip(self):
        md = ECH0129NamedMetaData(
            meta_data_name='buildingType', meta_data_value='Chalet'
        )
        xml = md.to_xml()
        parsed = ECH0129NamedMetaData.from_xml(xml)
        assert parsed.meta_data_name == md.meta_data_name
        assert parsed.meta_data_value == md.meta_data_value

    def test_xml_element_names(self):
        md = ECH0129NamedMetaData(
            meta_data_name='key', meta_data_value='val'
        )
        xml = md.to_xml()
        assert xml.find(f'{{{NS_0129}}}metaDataName') is not None
        assert xml.find(f'{{{NS_0129}}}metaDataValue') is not None


# ===========================================================================
# ECH0129NamedId
# ===========================================================================

class TestNamedId:
    def test_valid(self):
        nid = ECH0129NamedId(id_category='EGID', id_value='1234567')
        assert nid.id_category == 'EGID'
        assert nid.id_value == '1234567'

    def test_category_empty(self):
        with pytest.raises(Exception):
            ECH0129NamedId(id_category='', id_value='123')

    def test_category_too_long(self):
        with pytest.raises(Exception):
            ECH0129NamedId(id_category='x' * 21, id_value='123')

    def test_id_empty(self):
        with pytest.raises(Exception):
            ECH0129NamedId(id_category='EGID', id_value='')

    def test_id_too_long(self):
        with pytest.raises(Exception):
            ECH0129NamedId(id_category='EGID', id_value='x' * 51)

    def test_roundtrip(self):
        nid = ECH0129NamedId(id_category='EWID', id_value='42')
        xml = nid.to_xml()
        parsed = ECH0129NamedId.from_xml(xml)
        assert parsed.id_category == nid.id_category
        assert parsed.id_value == nid.id_value

    def test_xml_capital_i_element_names(self):
        """XSD uses capital 'I' for IdCategory and Id."""
        nid = ECH0129NamedId(id_category='EGID', id_value='123')
        xml = nid.to_xml()
        assert xml.find(f'{{{NS_0129}}}IdCategory') is not None
        assert xml.find(f'{{{NS_0129}}}Id') is not None


# ===========================================================================
# ECH0129Coordinates
# ===========================================================================

class TestCoordinates:
    def test_valid_bern(self):
        """Bern Bundesplatz approximate LV95 coordinates."""
        c = ECH0129Coordinates(
            east='2600000.000', north='1200000.000',
            origin_of_coordinates=OriginOfCoordinates.OFFICIAL_SURVEY,
        )
        assert c.east == '2600000.000'
        assert c.north == '1200000.000'
        assert c.origin_of_coordinates == OriginOfCoordinates.OFFICIAL_SURVEY

    def test_without_origin(self):
        c = ECH0129Coordinates(east='2600000.000', north='1200000.000')
        assert c.origin_of_coordinates is None

    def test_east_below_range(self):
        with pytest.raises(Exception, match='2480000'):
            ECH0129Coordinates(east='2400000.000', north='1200000.000')

    def test_east_above_range(self):
        with pytest.raises(Exception, match='2840000'):
            ECH0129Coordinates(east='2900000.000', north='1200000.000')

    def test_north_below_range(self):
        with pytest.raises(Exception, match='1070000'):
            ECH0129Coordinates(east='2600000.000', north='1000000.000')

    def test_north_above_range(self):
        with pytest.raises(Exception, match='1300000'):
            ECH0129Coordinates(east='2600000.000', north='1400000.000')

    def test_east_not_decimal(self):
        with pytest.raises(Exception, match='valid decimal'):
            ECH0129Coordinates(east='abc', north='1200000.000')

    def test_boundary_min_east(self):
        c = ECH0129Coordinates(east='2480000.000', north='1200000.000')
        assert c.east == '2480000.000'

    def test_boundary_max_east(self):
        c = ECH0129Coordinates(east='2840000.999', north='1200000.000')
        assert c.east == '2840000.999'

    def test_roundtrip(self):
        c = ECH0129Coordinates(
            east='2600123.456', north='1199876.543',
            origin_of_coordinates=OriginOfCoordinates.BFS,
        )
        xml = c.to_xml()
        parsed = ECH0129Coordinates.from_xml(xml)
        assert parsed.east == c.east
        assert parsed.north == c.north
        assert parsed.origin_of_coordinates == c.origin_of_coordinates

    def test_roundtrip_no_origin(self):
        c = ECH0129Coordinates(east='2600000.000', north='1200000.000')
        xml = c.to_xml()
        parsed = ECH0129Coordinates.from_xml(xml)
        assert parsed.origin_of_coordinates is None


# ===========================================================================
# ECH0129DatePartiallyKnown
# ===========================================================================

class TestDatePartiallyKnown:
    def test_full_date(self):
        d = ECH0129DatePartiallyKnown(year_month_day=date(2020, 6, 15))
        assert d.year_month_day == date(2020, 6, 15)
        assert d.year_month is None
        assert d.year is None

    def test_year_month(self):
        d = ECH0129DatePartiallyKnown(year_month='2020-06')
        assert d.year_month == '2020-06'

    def test_year_only(self):
        d = ECH0129DatePartiallyKnown(year='2020')
        assert d.year == '2020'

    def test_none_set_rejected(self):
        with pytest.raises(Exception, match='must set one'):
            ECH0129DatePartiallyKnown()

    def test_multiple_set_rejected(self):
        with pytest.raises(Exception, match='only one'):
            ECH0129DatePartiallyKnown(
                year_month_day=date(2020, 1, 1), year='2020'
            )

    def test_invalid_year_month_format(self):
        with pytest.raises(Exception):
            ECH0129DatePartiallyKnown(year_month='2020/06')

    def test_invalid_year_format(self):
        with pytest.raises(Exception):
            ECH0129DatePartiallyKnown(year='20')

    def test_roundtrip_full_date(self):
        d = ECH0129DatePartiallyKnown(year_month_day=date(2020, 6, 15))
        xml = d.to_xml()
        parsed = ECH0129DatePartiallyKnown.from_xml(xml)
        assert parsed.year_month_day == d.year_month_day

    def test_roundtrip_year_month(self):
        d = ECH0129DatePartiallyKnown(year_month='2020-06')
        xml = d.to_xml()
        parsed = ECH0129DatePartiallyKnown.from_xml(xml)
        assert parsed.year_month == d.year_month

    def test_roundtrip_year(self):
        d = ECH0129DatePartiallyKnown(year='2020')
        xml = d.to_xml()
        parsed = ECH0129DatePartiallyKnown.from_xml(xml)
        assert parsed.year == d.year

    def test_namespace_is_ech0129(self):
        """Must use eCH-0129 namespace, not eCH-0044."""
        d = ECH0129DatePartiallyKnown(year='2020')
        xml = d.to_xml()
        assert xml.tag == f'{{{NS_0129}}}datePartiallyKnown'
        assert xml.find(f'{{{NS_0129}}}year') is not None


# ===========================================================================
# ECH0129BuildingDate
# ===========================================================================

class TestBuildingDate:
    def test_full_date(self):
        bd = ECH0129BuildingDate(year_month_day=date(1985, 3, 15))
        assert bd.year_month_day == date(1985, 3, 15)

    def test_year_month(self):
        bd = ECH0129BuildingDate(year_month='1985-03')
        assert bd.year_month == '1985-03'

    def test_year(self):
        bd = ECH0129BuildingDate(year='1985')
        assert bd.year == '1985'

    def test_period(self):
        bd = ECH0129BuildingDate(
            period_of_construction=PeriodOfConstruction.P_1981_1985
        )
        assert bd.period_of_construction == PeriodOfConstruction.P_1981_1985

    def test_none_rejected(self):
        with pytest.raises(Exception, match='must set one'):
            ECH0129BuildingDate()

    def test_multiple_rejected(self):
        with pytest.raises(Exception, match='only one'):
            ECH0129BuildingDate(
                year='1985',
                period_of_construction=PeriodOfConstruction.P_1981_1985,
            )

    def test_year_too_low(self):
        with pytest.raises(Exception, match='1000'):
            ECH0129BuildingDate(year='0999')

    def test_year_too_high(self):
        with pytest.raises(Exception, match='2099'):
            ECH0129BuildingDate(year='2100')

    def test_year_month_too_low(self):
        with pytest.raises(Exception, match='1000'):
            ECH0129BuildingDate(year_month='0999-01')

    def test_year_month_too_high(self):
        with pytest.raises(Exception, match='2099'):
            ECH0129BuildingDate(year_month='2100-01')

    def test_full_date_too_high(self):
        with pytest.raises(Exception, match='2099'):
            ECH0129BuildingDate(year_month_day=date(2100, 1, 1))

    def test_boundary_min_year(self):
        bd = ECH0129BuildingDate(year='1000')
        assert bd.year == '1000'

    def test_boundary_max_year(self):
        bd = ECH0129BuildingDate(year='2099')
        assert bd.year == '2099'

    def test_roundtrip_date(self):
        bd = ECH0129BuildingDate(year_month_day=date(1985, 3, 15))
        xml = bd.to_xml()
        parsed = ECH0129BuildingDate.from_xml(xml)
        assert parsed.year_month_day == bd.year_month_day

    def test_roundtrip_year_month(self):
        bd = ECH0129BuildingDate(year_month='1985-03')
        xml = bd.to_xml()
        parsed = ECH0129BuildingDate.from_xml(xml)
        assert parsed.year_month == bd.year_month

    def test_roundtrip_year(self):
        bd = ECH0129BuildingDate(year='1985')
        xml = bd.to_xml()
        parsed = ECH0129BuildingDate.from_xml(xml)
        assert parsed.year == bd.year

    def test_roundtrip_period(self):
        bd = ECH0129BuildingDate(
            period_of_construction=PeriodOfConstruction.P_1986_1990
        )
        xml = bd.to_xml()
        parsed = ECH0129BuildingDate.from_xml(xml)
        assert parsed.period_of_construction == bd.period_of_construction


# ===========================================================================
# ECH0129BuildingVolume — nillable handling
# ===========================================================================

class TestBuildingVolume:
    def test_with_value(self):
        bv = ECH0129BuildingVolume(
            volume=12345,
            information_source=BuildingVolumeInformationSource.BUILDING_PERMIT,
            norm=BuildingVolumeNorm.SIA_416,
        )
        assert bv.volume == 12345
        assert bv.information_source == BuildingVolumeInformationSource.BUILDING_PERMIT
        assert bv.norm == BuildingVolumeNorm.SIA_416

    def test_empty(self):
        """All fields optional — empty is valid."""
        bv = ECH0129BuildingVolume()
        assert bv.volume is None
        assert bv.information_source is None
        assert bv.norm is None

    def test_volume_min(self):
        bv = ECH0129BuildingVolume(volume=1)
        assert bv.volume == 1

    def test_volume_max(self):
        bv = ECH0129BuildingVolume(volume=9999999)
        assert bv.volume == 9999999

    def test_volume_below_min(self):
        with pytest.raises(Exception):
            ECH0129BuildingVolume(volume=0)

    def test_volume_above_max(self):
        with pytest.raises(Exception):
            ECH0129BuildingVolume(volume=10000000)

    def test_value_and_nil_rejected(self):
        with pytest.raises(Exception, match='cannot have a value and be nil'):
            ECH0129BuildingVolume(volume=100, volume_nil=True)

    def test_nil_flags(self):
        bv = ECH0129BuildingVolume(
            volume_nil=True,
            information_source_nil=True,
            norm_nil=True,
        )
        assert bv.volume is None
        assert bv.volume_nil is True

    # --- Serialization ---

    def test_to_xml_with_values(self):
        bv = ECH0129BuildingVolume(
            volume=5000,
            information_source=BuildingVolumeInformationSource.OFFICIAL_SURVEY,
            norm=BuildingVolumeNorm.SIA_116,
        )
        xml = bv.to_xml()
        vol = xml.find(f'{{{NS_0129}}}volume')
        assert vol is not None
        assert vol.text == '5000'
        src = xml.find(f'{{{NS_0129}}}informationSource')
        assert src is not None
        assert src.text == '851'
        norm = xml.find(f'{{{NS_0129}}}norm')
        assert norm is not None
        assert norm.text == '961'

    def test_to_xml_empty_no_elements(self):
        bv = ECH0129BuildingVolume()
        xml = bv.to_xml()
        assert len(list(xml)) == 0

    def test_to_xml_nil_volume(self):
        bv = ECH0129BuildingVolume(volume_nil=True)
        xml = bv.to_xml()
        vol = xml.find(f'{{{NS_0129}}}volume')
        assert vol is not None
        assert vol.get(f'{{{XSI_NS}}}nil') == 'true'
        assert vol.text is None

    def test_to_xml_all_nil(self):
        bv = ECH0129BuildingVolume(
            volume_nil=True,
            information_source_nil=True,
            norm_nil=True,
        )
        xml = bv.to_xml()
        for name in ('volume', 'informationSource', 'norm'):
            elem = xml.find(f'{{{NS_0129}}}{name}')
            assert elem is not None, f'{name} element missing'
            assert elem.get(f'{{{XSI_NS}}}nil') == 'true'

    # --- Roundtrip ---

    def test_roundtrip_with_values(self):
        bv = ECH0129BuildingVolume(
            volume=5000,
            information_source=BuildingVolumeInformationSource.BUILDING_PERMIT,
            norm=BuildingVolumeNorm.SIA_416,
        )
        xml = bv.to_xml()
        parsed = ECH0129BuildingVolume.from_xml(xml)
        assert parsed.volume == bv.volume
        assert parsed.information_source == bv.information_source
        assert parsed.norm == bv.norm
        assert not parsed.volume_nil
        assert not parsed.information_source_nil
        assert not parsed.norm_nil

    def test_roundtrip_empty(self):
        bv = ECH0129BuildingVolume()
        xml = bv.to_xml()
        parsed = ECH0129BuildingVolume.from_xml(xml)
        assert parsed.volume is None
        assert parsed.information_source is None
        assert parsed.norm is None

    def test_roundtrip_nil(self):
        bv = ECH0129BuildingVolume(
            volume_nil=True,
            information_source_nil=True,
            norm_nil=True,
        )
        xml = bv.to_xml()
        parsed = ECH0129BuildingVolume.from_xml(xml)
        assert parsed.volume is None
        assert parsed.volume_nil is True
        assert parsed.information_source is None
        assert parsed.information_source_nil is True
        assert parsed.norm is None
        assert parsed.norm_nil is True

    def test_roundtrip_mixed(self):
        """Volume is nil, but info source has a value."""
        bv = ECH0129BuildingVolume(
            volume_nil=True,
            information_source=BuildingVolumeInformationSource.NOT_DETERMINABLE,
        )
        xml = bv.to_xml()
        parsed = ECH0129BuildingVolume.from_xml(xml)
        assert parsed.volume is None
        assert parsed.volume_nil is True
        assert parsed.information_source == BuildingVolumeInformationSource.NOT_DETERMINABLE
        assert not parsed.information_source_nil

    def test_from_xml_external_nil(self):
        """Parse xsi:nil from externally-generated XML."""
        xml_str = (
            f'<bv xmlns="{NS_0129}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<volume xsi:nil="true"/>'
            f'<informationSource>878</informationSource>'
            f'</bv>'
        )
        elem = ET.fromstring(xml_str)
        parsed = ECH0129BuildingVolume.from_xml(elem)
        assert parsed.volume is None
        assert parsed.volume_nil is True
        assert parsed.information_source == BuildingVolumeInformationSource.NOT_DETERMINABLE
        assert parsed.norm is None
        assert not parsed.norm_nil


# ===========================================================================
# ECH0129Heating
# ===========================================================================

class TestHeating:
    def test_full(self):
        h = ECH0129Heating(
            heat_generator_heating=HeatGeneratorHeating.HEAT_PUMP_SINGLE,
            energy_source_heating=EnergySource.GEOTHERMAL_PROBE,
            information_source_heating=InformationSource.OWNER,
            revision_date=date(2023, 6, 1),
        )
        assert h.heat_generator_heating == HeatGeneratorHeating.HEAT_PUMP_SINGLE
        assert h.energy_source_heating == EnergySource.GEOTHERMAL_PROBE
        assert h.information_source_heating == InformationSource.OWNER
        assert h.revision_date == date(2023, 6, 1)

    def test_empty(self):
        h = ECH0129Heating()
        assert h.heat_generator_heating is None

    def test_roundtrip(self):
        h = ECH0129Heating(
            heat_generator_heating=HeatGeneratorHeating.BOILER_CONDENSING_SINGLE,
            energy_source_heating=EnergySource.GAS,
            information_source_heating=InformationSource.CHIMNEY_INSPECTION,
            revision_date=date(2022, 11, 20),
        )
        xml = h.to_xml()
        parsed = ECH0129Heating.from_xml(xml)
        assert parsed.heat_generator_heating == h.heat_generator_heating
        assert parsed.energy_source_heating == h.energy_source_heating
        assert parsed.information_source_heating == h.information_source_heating
        assert parsed.revision_date == h.revision_date

    def test_xml_element_names(self):
        h = ECH0129Heating(
            heat_generator_heating=HeatGeneratorHeating.NONE,
            energy_source_heating=EnergySource.NONE,
        )
        xml = h.to_xml()
        assert xml.find(f'{{{NS_0129}}}heatGeneratorHeating') is not None
        assert xml.find(f'{{{NS_0129}}}energySourceHeating') is not None


# ===========================================================================
# ECH0129HotWater
# ===========================================================================

class TestHotWater:
    def test_full(self):
        hw = ECH0129HotWater(
            heat_generator_hot_water=HeatGeneratorHotWater.HEAT_PUMP,
            energy_source_heating=EnergySource.GEOTHERMAL_PROBE,
            information_source_heating=InformationSource.OWNER,
            revision_date=date(2023, 6, 1),
        )
        assert hw.heat_generator_hot_water == HeatGeneratorHotWater.HEAT_PUMP

    def test_empty(self):
        hw = ECH0129HotWater()
        assert hw.heat_generator_hot_water is None

    def test_roundtrip(self):
        hw = ECH0129HotWater(
            heat_generator_hot_water=HeatGeneratorHotWater.CENTRAL_BOILER,
            energy_source_heating=EnergySource.ELECTRICITY,
            revision_date=date(2021, 3, 10),
        )
        xml = hw.to_xml()
        parsed = ECH0129HotWater.from_xml(xml)
        assert parsed.heat_generator_hot_water == hw.heat_generator_hot_water
        assert parsed.energy_source_heating == hw.energy_source_heating
        assert parsed.revision_date == hw.revision_date

    def test_xml_element_names_reuse_heating_names(self):
        """XSD reuses 'energySourceHeating' name even for hot water."""
        hw = ECH0129HotWater(
            heat_generator_hot_water=HeatGeneratorHotWater.NONE,
            energy_source_heating=EnergySource.NONE,
            information_source_heating=InformationSource.OTHER,
        )
        xml = hw.to_xml()
        assert xml.find(f'{{{NS_0129}}}heatGeneratorHotWater') is not None
        assert xml.find(f'{{{NS_0129}}}energySourceHeating') is not None
        assert xml.find(f'{{{NS_0129}}}informationSourceHeating') is not None


# ===========================================================================
# ECH0129Contact
# ===========================================================================

class TestContact:
    def test_full(self):
        c = ECH0129Contact(
            email_address='info@example.ch',
            phone_number='0312345678901',
            fax_number='0312345678902',
        )
        assert c.email_address == 'info@example.ch'
        assert c.phone_number == '0312345678901'
        assert c.fax_number == '0312345678902'

    def test_empty(self):
        c = ECH0129Contact()
        assert c.email_address is None
        assert c.phone_number is None
        assert c.fax_number is None

    def test_email_too_long(self):
        with pytest.raises(Exception):
            ECH0129Contact(email_address='a' * 101)

    def test_phone_too_long(self):
        with pytest.raises(Exception):
            ECH0129Contact(phone_number='1' * 21)

    def test_roundtrip(self):
        c = ECH0129Contact(
            email_address='test@test.ch',
            phone_number='0312345678901',
        )
        xml = c.to_xml()
        parsed = ECH0129Contact.from_xml(xml)
        assert parsed.email_address == c.email_address
        assert parsed.phone_number == c.phone_number
        assert parsed.fax_number is None


# ===========================================================================
# ECH0129PersonIdentification — cross-namespace choice
# ===========================================================================

class TestPersonIdentification:
    @staticmethod
    def _make_individual():
        return ECH0044PersonIdentificationLight(
            local_person_id=ECH0044NamedPersonId(
                person_id_category='veka.id', person_id='12345'
            ),
            official_name='Mueller',
            first_name='Hans',
        )

    @staticmethod
    def _make_organisation():
        return ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category='CH.HR',
                organisation_id='CHE-123.456.789',
            ),
            organisation_name='Test AG',
        )

    def test_individual(self):
        pi = ECH0129PersonIdentification(
            individual=self._make_individual()
        )
        assert pi.individual is not None
        assert pi.organisation is None

    def test_organisation(self):
        pi = ECH0129PersonIdentification(
            organisation=self._make_organisation()
        )
        assert pi.organisation is not None
        assert pi.individual is None

    def test_none_rejected(self):
        with pytest.raises(Exception, match='must set one'):
            ECH0129PersonIdentification()

    def test_both_rejected(self):
        with pytest.raises(Exception, match='only one'):
            ECH0129PersonIdentification(
                individual=self._make_individual(),
                organisation=self._make_organisation(),
            )

    def test_roundtrip_individual(self):
        pi = ECH0129PersonIdentification(
            individual=self._make_individual()
        )
        xml = pi.to_xml()
        parsed = ECH0129PersonIdentification.from_xml(xml)
        assert parsed.individual is not None
        assert parsed.individual.official_name == 'Mueller'
        assert parsed.individual.first_name == 'Hans'
        assert parsed.organisation is None

    def test_roundtrip_organisation(self):
        pi = ECH0129PersonIdentification(
            organisation=self._make_organisation()
        )
        xml = pi.to_xml()
        parsed = ECH0129PersonIdentification.from_xml(xml)
        assert parsed.organisation is not None
        assert parsed.organisation.organisation_name == 'Test AG'
        assert parsed.individual is None

    def test_xml_structure_individual(self):
        """Wrapper element in eCH-0129 ns, children in eCH-0044 ns."""
        pi = ECH0129PersonIdentification(
            individual=self._make_individual()
        )
        xml = pi.to_xml()
        ind = xml.find(f'{{{NS_0129}}}individual')
        assert ind is not None
        # Children should be in eCH-0044 namespace
        official_name = ind.find(f'{{{NS.ECH0044_V4}}}officialName')
        assert official_name is not None
        assert official_name.text == 'Mueller'

    def test_xml_structure_organisation(self):
        """Wrapper element in eCH-0129 ns, children in eCH-0097 ns."""
        pi = ECH0129PersonIdentification(
            organisation=self._make_organisation()
        )
        xml = pi.to_xml()
        org = xml.find(f'{{{NS_0129}}}organisation')
        assert org is not None
        # Children should be in eCH-0097 namespace
        org_name = org.find(f'{{{NS.ECH0097_V2}}}organisationName')
        assert org_name is not None
        assert org_name.text == 'Test AG'


# ===========================================================================
# Double roundtrip stability
# ===========================================================================

class TestDoubleRoundtrip:
    """Serialize → parse → serialize → compare XML strings."""

    @staticmethod
    def _xml_to_str(elem):
        return ET.tostring(elem, encoding='unicode')

    def test_date_range(self):
        obj = ECH0129DateRange(
            date_from=date(2020, 1, 1), date_to=date(2025, 12, 31)
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129DateRange.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_named_meta_data(self):
        obj = ECH0129NamedMetaData(
            meta_data_name='key', meta_data_value='val'
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129NamedMetaData.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_named_id(self):
        obj = ECH0129NamedId(id_category='EGID', id_value='123')
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129NamedId.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_coordinates(self):
        obj = ECH0129Coordinates(
            east='2600000.000', north='1200000.000',
            origin_of_coordinates=OriginOfCoordinates.OFFICIAL_SURVEY,
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129Coordinates.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_building_date_period(self):
        obj = ECH0129BuildingDate(
            period_of_construction=PeriodOfConstruction.P_1981_1985
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129BuildingDate.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_building_volume_values(self):
        obj = ECH0129BuildingVolume(
            volume=5000,
            information_source=BuildingVolumeInformationSource.BUILDING_PERMIT,
            norm=BuildingVolumeNorm.SIA_416,
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129BuildingVolume.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_building_volume_nil(self):
        obj = ECH0129BuildingVolume(
            volume_nil=True,
            information_source_nil=True,
            norm_nil=True,
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129BuildingVolume.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_heating(self):
        obj = ECH0129Heating(
            heat_generator_heating=HeatGeneratorHeating.HEAT_PUMP_SINGLE,
            energy_source_heating=EnergySource.GEOTHERMAL_PROBE,
            information_source_heating=InformationSource.OWNER,
            revision_date=date(2023, 6, 1),
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129Heating.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_hot_water(self):
        obj = ECH0129HotWater(
            heat_generator_hot_water=HeatGeneratorHotWater.CENTRAL_BOILER,
            energy_source_heating=EnergySource.ELECTRICITY,
            revision_date=date(2021, 3, 10),
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129HotWater.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2

    def test_contact(self):
        obj = ECH0129Contact(
            email_address='info@example.ch',
            phone_number='0312345678901',
            fax_number='0312345678902',
        )
        xml1 = self._xml_to_str(obj.to_xml())
        xml2 = self._xml_to_str(ECH0129Contact.from_xml(ET.fromstring(xml1)).to_xml())
        assert xml1 == xml2
