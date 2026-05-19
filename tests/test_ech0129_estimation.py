"""Tests for eCH-0129 v6.0.0 estimation types (Session 5).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints, xs:choice enforcement
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. Enum handling — TypeOfValue
5. "Only" variant — estimationObjectOnlyType excludes estimationValue list
6. yearOfConstruction — xs:gYear format + range validation
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import TypeOfValue
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId
from openmun_ech.ech0129.v6.estimation import (
    ECH0129EstimationObject,
    ECH0129EstimationObjectOnly,
    ECH0129EstimationValue,
    ECH0129Value,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# ECH0129Value
# ===========================================================================

class TestValue:
    def test_amount(self):
        v = ECH0129Value(amount='350000.00')
        assert v.amount == '350000.00'
        assert v.percentage is None

    def test_percentage(self):
        v = ECH0129Value(percentage='72.50')
        assert v.percentage == '72.50'
        assert v.amount is None

    def test_choice_none_fails(self):
        with pytest.raises(ValueError, match='must set one of'):
            ECH0129Value()

    def test_choice_both_fails(self):
        with pytest.raises(ValueError, match='only one of'):
            ECH0129Value(amount='100.00', percentage='50.00')

    def test_amount_invalid_decimal(self):
        with pytest.raises(Exception):
            ECH0129Value(amount='not_a_number')

    def test_percentage_invalid_decimal(self):
        with pytest.raises(Exception):
            ECH0129Value(percentage='abc')

    def test_roundtrip_amount(self):
        v = ECH0129Value(amount='9876543210.99')
        xml = v.to_xml()
        parsed = ECH0129Value.from_xml(xml)
        assert parsed.amount == '9876543210.99'
        assert parsed.percentage is None

    def test_roundtrip_percentage(self):
        v = ECH0129Value(percentage='100.00')
        xml = v.to_xml()
        parsed = ECH0129Value.from_xml(xml)
        assert parsed.percentage == '100.00'
        assert parsed.amount is None

    def test_xml_element_name_amount(self):
        v = ECH0129Value(amount='100.00')
        xml = v.to_xml()
        assert xml.find(f'{{{NS_0129}}}amount') is not None
        assert xml.find(f'{{{NS_0129}}}percentage') is None

    def test_xml_element_name_percentage(self):
        v = ECH0129Value(percentage='50.00')
        xml = v.to_xml()
        assert xml.find(f'{{{NS_0129}}}percentage') is not None
        assert xml.find(f'{{{NS_0129}}}amount') is None

    def test_double_roundtrip_amount(self):
        v = ECH0129Value(amount='123456789012')
        xml1 = v.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129Value.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# ECH0129EstimationValue
# ===========================================================================

class TestEstimationValue:
    def _make_named_id(self):
        return ECH0129NamedId(id_category='SCHAETZ', id_value='EV-001')

    def test_minimal(self):
        """Required fields: localID, value, typeOfvalue."""
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            value=ECH0129Value(amount='250000.00'),
            type_of_value=TypeOfValue.TAX_VALUE,
        )
        assert ev.local_id.id_category == 'SCHAETZ'
        assert ev.value.amount == '250000.00'
        assert ev.type_of_value == TypeOfValue.TAX_VALUE
        assert ev.base_year is None
        assert ev.valid_from is None
        assert ev.index_value is None

    def test_all_fields(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            base_year=2020,
            valid_from=date(2023, 1, 1),
            index_value='105.50',
            value=ECH0129Value(percentage='88.00'),
            type_of_value=TypeOfValue.IMPUTED_RENTAL,
        )
        assert ev.base_year == 2020
        assert ev.valid_from == date(2023, 1, 1)
        assert ev.index_value == '105.50'
        assert ev.value.percentage == '88.00'
        assert ev.type_of_value == TypeOfValue.IMPUTED_RENTAL

    def test_required_local_id(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.TAX_VALUE,
            )

    def test_required_value(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                type_of_value=TypeOfValue.TAX_VALUE,
            )

    def test_required_type_of_value(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                value=ECH0129Value(amount='100.00'),
            )

    def test_base_year_min(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            base_year=1000,
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.BASIS_VALUE,
        )
        assert ev.base_year == 1000

    def test_base_year_max(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            base_year=2999,
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.BASIS_VALUE,
        )
        assert ev.base_year == 2999

    def test_base_year_too_small(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                base_year=999,
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.BASIS_VALUE,
            )

    def test_base_year_too_large(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                base_year=3000,
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.BASIS_VALUE,
            )

    def test_index_value_min(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            index_value='0.00',
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.BASIS_VALUE,
        )
        assert ev.index_value == '0.00'

    def test_index_value_max(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            index_value='999.99',
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.BASIS_VALUE,
        )
        assert ev.index_value == '999.99'

    def test_index_value_too_small(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                index_value='-0.01',
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.BASIS_VALUE,
            )

    def test_index_value_too_large(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                index_value='1000.00',
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.BASIS_VALUE,
            )

    def test_index_value_invalid(self):
        with pytest.raises(Exception):
            ECH0129EstimationValue(
                local_id=self._make_named_id(),
                index_value='abc',
                value=ECH0129Value(amount='100.00'),
                type_of_value=TypeOfValue.BASIS_VALUE,
            )

    def test_all_type_of_value(self):
        for tov in TypeOfValue:
            ev = ECH0129EstimationValue(
                local_id=self._make_named_id(),
                value=ECH0129Value(amount='100.00'),
                type_of_value=tov,
            )
            assert ev.type_of_value == tov

    def test_roundtrip_minimal(self):
        ev = ECH0129EstimationValue(
            local_id=ECH0129NamedId(id_category='KT', id_value='SW-001'),
            value=ECH0129Value(amount='780000.00'),
            type_of_value=TypeOfValue.TAX_VALUE,
        )
        xml = ev.to_xml()
        parsed = ECH0129EstimationValue.from_xml(xml)
        assert parsed.local_id.id_category == 'KT'
        assert parsed.local_id.id_value == 'SW-001'
        assert parsed.value.amount == '780000.00'
        assert parsed.type_of_value == TypeOfValue.TAX_VALUE
        assert parsed.base_year is None
        assert parsed.valid_from is None
        assert parsed.index_value is None

    def test_roundtrip_full(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            base_year=2015,
            valid_from=date(2022, 7, 1),
            index_value='112.30',
            value=ECH0129Value(percentage='95.00'),
            type_of_value=TypeOfValue.TIME_VALUE,
        )
        xml = ev.to_xml()
        parsed = ECH0129EstimationValue.from_xml(xml)
        assert parsed.base_year == 2015
        assert parsed.valid_from == date(2022, 7, 1)
        assert parsed.index_value == '112.30'
        assert parsed.value.percentage == '95.00'
        assert parsed.type_of_value == TypeOfValue.TIME_VALUE

    def test_xml_element_order(self):
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            base_year=2020,
            valid_from=date(2023, 1, 1),
            index_value='100.00',
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.TAX_VALUE,
        )
        xml = ev.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'baseYear', 'validFrom', 'indexValue',
            'value', 'typeOfvalue',
        ]

    def test_xml_type_of_value_lowercase_v(self):
        """XSD element is 'typeOfvalue' (lowercase v), not 'typeOfValue'."""
        ev = ECH0129EstimationValue(
            local_id=self._make_named_id(),
            value=ECH0129Value(amount='100.00'),
            type_of_value=TypeOfValue.TAX_VALUE,
        )
        xml = ev.to_xml()
        # Must be lowercase 'v' in 'typeOfvalue'
        assert xml.find(f'{{{NS_0129}}}typeOfvalue') is not None
        assert xml.find(f'{{{NS_0129}}}typeOfValue') is None


# ===========================================================================
# ECH0129EstimationObject
# ===========================================================================

class TestEstimationObject:
    def _make_named_id(self, val='EO-001'):
        return ECH0129NamedId(id_category='SCHAETZ', id_value=val)

    def _make_estimation_value(self, amount='100000.00',
                                tov=TypeOfValue.TAX_VALUE):
        return ECH0129EstimationValue(
            local_id=ECH0129NamedId(id_category='KT', id_value='EV-1'),
            value=ECH0129Value(amount=amount),
            type_of_value=tov,
        )

    def test_minimal(self):
        """Only required field: localID."""
        eo = ECH0129EstimationObject(local_id=self._make_named_id())
        assert eo.local_id.id_category == 'SCHAETZ'
        assert eo.volume is None
        assert eo.year_of_construction is None
        assert eo.description is None
        assert eo.valid_from is None
        assert eo.estimation_reason is None
        assert eo.estimation_value == []

    def test_all_fields(self):
        ev1 = self._make_estimation_value('500000.00', TypeOfValue.TAX_VALUE)
        ev2 = self._make_estimation_value('450000.00', TypeOfValue.MARKET_VALUE)
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            volume=3500,
            year_of_construction='1985',
            description='Wohngebäude mit Garage',
            valid_from=date(2023, 1, 1),
            estimation_reason='Neubewertung',
            estimation_value=[ev1, ev2],
        )
        assert eo.volume == 3500
        assert eo.year_of_construction == '1985'
        assert eo.description == 'Wohngebäude mit Garage'
        assert eo.valid_from == date(2023, 1, 1)
        assert eo.estimation_reason == 'Neubewertung'
        assert len(eo.estimation_value) == 2

    def test_required_local_id(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject()

    def test_volume_min(self):
        """XSD: estimationVolumeType, min=5."""
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(), volume=5,
        )
        assert eo.volume == 5

    def test_volume_max(self):
        """XSD: estimationVolumeType, max=2000000."""
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(), volume=2000000,
        )
        assert eo.volume == 2000000

    def test_volume_too_small(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(), volume=4,
            )

    def test_volume_too_large(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(), volume=2000001,
            )

    def test_year_of_construction_valid(self):
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            year_of_construction='2023',
        )
        assert eo.year_of_construction == '2023'

    def test_year_of_construction_min(self):
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            year_of_construction='1000',
        )
        assert eo.year_of_construction == '1000'

    def test_year_of_construction_max(self):
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            year_of_construction='2099',
        )
        assert eo.year_of_construction == '2099'

    def test_year_of_construction_too_small(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                year_of_construction='0999',
            )

    def test_year_of_construction_too_large(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                year_of_construction='2100',
            )

    def test_year_of_construction_invalid_format(self):
        """Must be exactly 4 digits."""
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                year_of_construction='85',
            )

    def test_description_min_length(self):
        """XSD: estimationDescriptionType, minLength=3."""
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                description='AB',
            )

    def test_description_max_length(self):
        """XSD: estimationDescriptionType, maxLength=1000."""
        desc = 'A' * 1000
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(), description=desc,
        )
        assert len(eo.description) == 1000

    def test_description_too_long(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                description='A' * 1001,
            )

    def test_estimation_reason_min_length(self):
        """XSD: estimationReasonTextType, minLength=1."""
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                estimation_reason='',
            )

    def test_estimation_reason_max_length(self):
        """XSD: estimationReasonTextType, maxLength=30."""
        reason = 'A' * 30
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(), estimation_reason=reason,
        )
        assert len(eo.estimation_reason) == 30

    def test_estimation_reason_too_long(self):
        with pytest.raises(Exception):
            ECH0129EstimationObject(
                local_id=self._make_named_id(),
                estimation_reason='A' * 31,
            )

    def test_multiple_estimation_values(self):
        """estimationValue: maxOccurs="unbounded"."""
        values = [
            self._make_estimation_value(f'{i * 100000}.00', TypeOfValue.TAX_VALUE)
            for i in range(1, 6)
        ]
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            estimation_value=values,
        )
        assert len(eo.estimation_value) == 5

    def test_roundtrip_minimal(self):
        eo = ECH0129EstimationObject(local_id=self._make_named_id())
        xml = eo.to_xml()
        parsed = ECH0129EstimationObject.from_xml(xml)
        assert parsed.local_id.id_category == 'SCHAETZ'
        assert parsed.local_id.id_value == 'EO-001'
        assert parsed.volume is None
        assert parsed.year_of_construction is None
        assert parsed.description is None
        assert parsed.valid_from is None
        assert parsed.estimation_reason is None
        assert parsed.estimation_value == []

    def test_roundtrip_full(self):
        ev = ECH0129EstimationValue(
            local_id=ECH0129NamedId(id_category='KT', id_value='EV-RT'),
            base_year=2018,
            valid_from=date(2023, 6, 1),
            index_value='108.50',
            value=ECH0129Value(amount='680000.00'),
            type_of_value=TypeOfValue.MARKET_VALUE,
        )
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(val='EO-FULL'),
            volume=4200,
            year_of_construction='1972',
            description='Mehrfamilienhaus',
            valid_from=date(2023, 1, 1),
            estimation_reason='Periodische Revision',
            estimation_value=[ev],
        )
        xml = eo.to_xml()
        parsed = ECH0129EstimationObject.from_xml(xml)
        assert parsed.local_id.id_value == 'EO-FULL'
        assert parsed.volume == 4200
        assert parsed.year_of_construction == '1972'
        assert parsed.description == 'Mehrfamilienhaus'
        assert parsed.valid_from == date(2023, 1, 1)
        assert parsed.estimation_reason == 'Periodische Revision'
        assert len(parsed.estimation_value) == 1
        ev_parsed = parsed.estimation_value[0]
        assert ev_parsed.base_year == 2018
        assert ev_parsed.valid_from == date(2023, 6, 1)
        assert ev_parsed.index_value == '108.50'
        assert ev_parsed.value.amount == '680000.00'
        assert ev_parsed.type_of_value == TypeOfValue.MARKET_VALUE

    def test_roundtrip_multiple_values(self):
        """Round-trip with multiple estimationValue entries."""
        ev1 = ECH0129EstimationValue(
            local_id=ECH0129NamedId(id_category='KT', id_value='EV-1'),
            value=ECH0129Value(amount='500000.00'),
            type_of_value=TypeOfValue.TAX_VALUE,
        )
        ev2 = ECH0129EstimationValue(
            local_id=ECH0129NamedId(id_category='KT', id_value='EV-2'),
            value=ECH0129Value(amount='600000.00'),
            type_of_value=TypeOfValue.MARKET_VALUE,
        )
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            estimation_value=[ev1, ev2],
        )
        xml = eo.to_xml()
        parsed = ECH0129EstimationObject.from_xml(xml)
        assert len(parsed.estimation_value) == 2
        assert parsed.estimation_value[0].type_of_value == TypeOfValue.TAX_VALUE
        assert parsed.estimation_value[1].type_of_value == TypeOfValue.MARKET_VALUE

    def test_xml_element_order(self):
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            volume=1000,
            year_of_construction='2000',
            description='Test building',
            valid_from=date(2023, 1, 1),
            estimation_reason='Test',
            estimation_value=[self._make_estimation_value()],
        )
        xml = eo.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'volume', 'yearOfConstruction', 'description',
            'validFrom', 'estimationReason', 'estimationValue',
        ]

    def test_double_roundtrip_stability(self):
        eo = ECH0129EstimationObject(
            local_id=self._make_named_id(),
            volume=800,
            year_of_construction='1990',
            description='Chalet',
            estimation_value=[self._make_estimation_value()],
        )
        xml1 = eo.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129EstimationObject.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# ECH0129EstimationObjectOnly
# ===========================================================================

class TestEstimationObjectOnly:
    def _make_named_id(self):
        return ECH0129NamedId(id_category='SCHAETZ', id_value='EOO-001')

    def test_minimal(self):
        eo = ECH0129EstimationObjectOnly(local_id=self._make_named_id())
        assert eo.local_id.id_value == 'EOO-001'
        assert eo.volume is None
        assert eo.year_of_construction is None
        assert eo.description is None
        assert eo.valid_from is None
        assert eo.estimation_reason is None

    def test_no_estimation_value_field(self):
        """estimationObjectOnlyType has no estimationValue field."""
        assert 'estimation_value' not in ECH0129EstimationObjectOnly.model_fields

    def test_all_fields(self):
        eo = ECH0129EstimationObjectOnly(
            local_id=self._make_named_id(),
            volume=2200,
            year_of_construction='1965',
            description='Landwirtschaftliches Gebäude',
            valid_from=date(2022, 1, 1),
            estimation_reason='Handänderung',
        )
        assert eo.volume == 2200
        assert eo.year_of_construction == '1965'
        assert eo.description == 'Landwirtschaftliches Gebäude'
        assert eo.valid_from == date(2022, 1, 1)
        assert eo.estimation_reason == 'Handänderung'

    def test_volume_constraints(self):
        """Same constraints as estimationObjectType: 5–2000000."""
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(), volume=4,
            )
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(), volume=2000001,
            )

    def test_year_of_construction_constraints(self):
        """Same constraints: 1000–2099, 4-digit format."""
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(),
                year_of_construction='0999',
            )
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(),
                year_of_construction='2100',
            )

    def test_description_constraints(self):
        """Same constraints: minLength=3, maxLength=1000."""
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(),
                description='AB',
            )

    def test_estimation_reason_constraints(self):
        """Same constraints: minLength=1, maxLength=30."""
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(),
                estimation_reason='',
            )
        with pytest.raises(Exception):
            ECH0129EstimationObjectOnly(
                local_id=self._make_named_id(),
                estimation_reason='A' * 31,
            )

    def test_roundtrip(self):
        eo = ECH0129EstimationObjectOnly(
            local_id=self._make_named_id(),
            volume=1500,
            year_of_construction='2010',
            description='Einfamilienhaus',
            valid_from=date(2023, 7, 1),
            estimation_reason='Umbau',
        )
        xml = eo.to_xml()
        parsed = ECH0129EstimationObjectOnly.from_xml(xml)
        assert parsed.local_id.id_value == 'EOO-001'
        assert parsed.volume == 1500
        assert parsed.year_of_construction == '2010'
        assert parsed.description == 'Einfamilienhaus'
        assert parsed.valid_from == date(2023, 7, 1)
        assert parsed.estimation_reason == 'Umbau'

    def test_xml_element_order(self):
        eo = ECH0129EstimationObjectOnly(
            local_id=self._make_named_id(),
            volume=100,
            year_of_construction='2000',
            description='Test',
            valid_from=date(2023, 1, 1),
            estimation_reason='Test',
        )
        xml = eo.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'volume', 'yearOfConstruction', 'description',
            'validFrom', 'estimationReason',
        ]

    def test_double_roundtrip_stability(self):
        eo = ECH0129EstimationObjectOnly(
            local_id=self._make_named_id(),
            year_of_construction='1880',
            estimation_reason='Revision',
        )
        xml1 = eo.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129EstimationObjectOnly.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# Import from package
# ===========================================================================

class TestPackageExports:
    def test_import_from_v6(self):
        from openmun_ech.ech0129.v6 import (
            ECH0129EstimationObject,
            ECH0129EstimationObjectOnly,
            ECH0129EstimationValue,
            ECH0129Value,
        )
        assert ECH0129EstimationObject is not None
        assert ECH0129EstimationObjectOnly is not None
        assert ECH0129EstimationValue is not None
        assert ECH0129Value is not None
