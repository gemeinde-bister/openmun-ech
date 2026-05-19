"""Tests for eCH-0129 v6.0.0 insurance types (Session 5).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints, xs:choice enforcement
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. Enum handling — ChangeReason, UsageCode, LocationCode, BuildingVolumeNorm
5. "Only" variant — insuranceObjectOnlyType excludes insuranceValue
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import (
    BuildingVolumeNorm,
    ChangeReason,
    LocationCode,
    UsageCode,
)
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId
from openmun_ech.ech0129.v6.insurance import (
    ECH0129InsuranceObject,
    ECH0129InsuranceObjectOnly,
    ECH0129InsuranceSum,
    ECH0129InsuranceValue,
    ECH0129InsuranceVolume,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# ECH0129InsuranceSum
# ===========================================================================

class TestInsuranceSum:
    def test_amount(self):
        s = ECH0129InsuranceSum(amount='500000.00')
        assert s.amount == '500000.00'
        assert s.percentage is None

    def test_percentage(self):
        s = ECH0129InsuranceSum(percentage='85.50')
        assert s.percentage == '85.50'
        assert s.amount is None

    def test_choice_none_fails(self):
        """Must set at least one."""
        with pytest.raises(ValueError, match='must set one of'):
            ECH0129InsuranceSum()

    def test_choice_both_fails(self):
        """Cannot set both."""
        with pytest.raises(ValueError, match='only one of'):
            ECH0129InsuranceSum(amount='100.00', percentage='50.00')

    def test_amount_invalid_decimal(self):
        with pytest.raises(Exception):
            ECH0129InsuranceSum(amount='not_a_number')

    def test_percentage_invalid_decimal(self):
        with pytest.raises(Exception):
            ECH0129InsuranceSum(percentage='xyz')

    def test_roundtrip_amount(self):
        s = ECH0129InsuranceSum(amount='1234567890.12')
        xml = s.to_xml()
        parsed = ECH0129InsuranceSum.from_xml(xml)
        assert parsed.amount == '1234567890.12'
        assert parsed.percentage is None

    def test_roundtrip_percentage(self):
        s = ECH0129InsuranceSum(percentage='99.99')
        xml = s.to_xml()
        parsed = ECH0129InsuranceSum.from_xml(xml)
        assert parsed.percentage == '99.99'
        assert parsed.amount is None

    def test_xml_element_name_amount(self):
        s = ECH0129InsuranceSum(amount='100.00')
        xml = s.to_xml()
        assert xml.find(f'{{{NS_0129}}}amount') is not None
        assert xml.find(f'{{{NS_0129}}}percentage') is None

    def test_xml_element_name_percentage(self):
        s = ECH0129InsuranceSum(percentage='50.00')
        xml = s.to_xml()
        assert xml.find(f'{{{NS_0129}}}percentage') is not None
        assert xml.find(f'{{{NS_0129}}}amount') is None

    def test_double_roundtrip_amount(self):
        s = ECH0129InsuranceSum(amount='999999999999')
        xml1 = s.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129InsuranceSum.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2

    def test_double_roundtrip_percentage(self):
        s = ECH0129InsuranceSum(percentage='0.01')
        xml1 = s.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129InsuranceSum.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# ECH0129InsuranceValue
# ===========================================================================

class TestInsuranceValue:
    def _make_named_id(self):
        return ECH0129NamedId(id_category='GVB', id_value='12345')

    def test_creation(self):
        """All 4 fields are required."""
        iv = ECH0129InsuranceValue(
            local_id=self._make_named_id(),
            valid_from=date(2023, 1, 1),
            change_reason=ChangeReason.NEW_VALUE,
            insurance_sum=ECH0129InsuranceSum(amount='250000.00'),
        )
        assert iv.local_id.id_category == 'GVB'
        assert iv.valid_from == date(2023, 1, 1)
        assert iv.change_reason == ChangeReason.NEW_VALUE
        assert iv.insurance_sum.amount == '250000.00'

    def test_required_local_id(self):
        with pytest.raises(Exception):
            ECH0129InsuranceValue(
                valid_from=date(2023, 1, 1),
                change_reason=ChangeReason.NEW_VALUE,
                insurance_sum=ECH0129InsuranceSum(amount='100.00'),
            )

    def test_required_valid_from(self):
        with pytest.raises(Exception):
            ECH0129InsuranceValue(
                local_id=self._make_named_id(),
                change_reason=ChangeReason.NEW_VALUE,
                insurance_sum=ECH0129InsuranceSum(amount='100.00'),
            )

    def test_required_change_reason(self):
        with pytest.raises(Exception):
            ECH0129InsuranceValue(
                local_id=self._make_named_id(),
                valid_from=date(2023, 1, 1),
                insurance_sum=ECH0129InsuranceSum(amount='100.00'),
            )

    def test_required_insurance_sum(self):
        with pytest.raises(Exception):
            ECH0129InsuranceValue(
                local_id=self._make_named_id(),
                valid_from=date(2023, 1, 1),
                change_reason=ChangeReason.NEW_VALUE,
            )

    def test_all_change_reasons(self):
        for cr in ChangeReason:
            iv = ECH0129InsuranceValue(
                local_id=self._make_named_id(),
                valid_from=date(2023, 1, 1),
                change_reason=cr,
                insurance_sum=ECH0129InsuranceSum(amount='100.00'),
            )
            assert iv.change_reason == cr

    def test_roundtrip_with_amount(self):
        iv = ECH0129InsuranceValue(
            local_id=ECH0129NamedId(id_category='AVGBS', id_value='V-001'),
            valid_from=date(2022, 7, 15),
            change_reason=ChangeReason.TIME_VALUE,
            insurance_sum=ECH0129InsuranceSum(amount='780000.50'),
        )
        xml = iv.to_xml()
        parsed = ECH0129InsuranceValue.from_xml(xml)
        assert parsed.local_id.id_category == 'AVGBS'
        assert parsed.local_id.id_value == 'V-001'
        assert parsed.valid_from == date(2022, 7, 15)
        assert parsed.change_reason == ChangeReason.TIME_VALUE
        assert parsed.insurance_sum.amount == '780000.50'
        assert parsed.insurance_sum.percentage is None

    def test_roundtrip_with_percentage(self):
        iv = ECH0129InsuranceValue(
            local_id=self._make_named_id(),
            valid_from=date(2023, 3, 1),
            change_reason=ChangeReason.TECHNICAL_DEPRECIATION,
            insurance_sum=ECH0129InsuranceSum(percentage='92.50'),
        )
        xml = iv.to_xml()
        parsed = ECH0129InsuranceValue.from_xml(xml)
        assert parsed.change_reason == ChangeReason.TECHNICAL_DEPRECIATION
        assert parsed.insurance_sum.percentage == '92.50'

    def test_xml_element_order(self):
        iv = ECH0129InsuranceValue(
            local_id=self._make_named_id(),
            valid_from=date(2023, 1, 1),
            change_reason=ChangeReason.NEW_VALUE,
            insurance_sum=ECH0129InsuranceSum(amount='100.00'),
        )
        xml = iv.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'validFrom', 'changeReason', 'insuranceSum',
        ]


# ===========================================================================
# ECH0129InsuranceVolume
# ===========================================================================

class TestInsuranceVolume:
    def test_creation(self):
        vol = ECH0129InsuranceVolume(
            volume=1500,
            norm=BuildingVolumeNorm.SIA_416,
        )
        assert vol.volume == 1500
        assert vol.norm == BuildingVolumeNorm.SIA_416

    def test_required_volume(self):
        with pytest.raises(Exception):
            ECH0129InsuranceVolume(
                norm=BuildingVolumeNorm.SIA_416,
            )

    def test_required_norm(self):
        with pytest.raises(Exception):
            ECH0129InsuranceVolume(volume=100)

    def test_volume_min(self):
        """XSD: minInclusive=5."""
        vol = ECH0129InsuranceVolume(
            volume=5, norm=BuildingVolumeNorm.SIA_416,
        )
        assert vol.volume == 5

    def test_volume_max(self):
        """XSD: maxInclusive=9999999."""
        vol = ECH0129InsuranceVolume(
            volume=9999999, norm=BuildingVolumeNorm.SIA_416,
        )
        assert vol.volume == 9999999

    def test_volume_too_small(self):
        with pytest.raises(Exception):
            ECH0129InsuranceVolume(
                volume=4, norm=BuildingVolumeNorm.SIA_416,
            )

    def test_volume_too_large(self):
        with pytest.raises(Exception):
            ECH0129InsuranceVolume(
                volume=10000000, norm=BuildingVolumeNorm.SIA_416,
            )

    def test_all_norms(self):
        for n in BuildingVolumeNorm:
            vol = ECH0129InsuranceVolume(volume=100, norm=n)
            assert vol.norm == n

    def test_roundtrip(self):
        vol = ECH0129InsuranceVolume(
            volume=3200, norm=BuildingVolumeNorm.SIA_116,
        )
        xml = vol.to_xml()
        parsed = ECH0129InsuranceVolume.from_xml(xml)
        assert parsed.volume == 3200
        assert parsed.norm == BuildingVolumeNorm.SIA_116

    def test_xml_element_order(self):
        vol = ECH0129InsuranceVolume(
            volume=100, norm=BuildingVolumeNorm.SIA_416,
        )
        xml = vol.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == ['volume', 'norm']


# ===========================================================================
# ECH0129InsuranceObject
# ===========================================================================

class TestInsuranceObject:
    def _make_named_id(self, cat='GVB', val='OBJ-001'):
        return ECH0129NamedId(id_category=cat, id_value=val)

    def test_minimal(self):
        """Only required fields: localID + insuranceNumber."""
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(),
            insurance_number='VS-12345',
        )
        assert obj.local_id.id_category == 'GVB'
        assert obj.insurance_number == 'VS-12345'
        assert obj.start_date is None
        assert obj.end_date is None
        assert obj.usage_code is None
        assert obj.usage_description is None
        assert obj.location_code is None
        assert obj.insurance_value is None
        assert obj.volume is None

    def test_all_fields(self):
        insurance_sum = ECH0129InsuranceSum(amount='500000.00')
        iv = ECH0129InsuranceValue(
            local_id=ECH0129NamedId(id_category='GVB', id_value='V-001'),
            valid_from=date(2023, 1, 1),
            change_reason=ChangeReason.NEW_VALUE,
            insurance_sum=insurance_sum,
        )
        vol = ECH0129InsuranceVolume(
            volume=2500, norm=BuildingVolumeNorm.SIA_416,
        )
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(),
            start_date=date(2020, 6, 1),
            end_date=date(2030, 12, 31),
            insurance_number='VS-12345',
            usage_code=UsageCode.RESIDENTIAL,
            usage_description='Einfamilienhaus',
            location_code=LocationCode.DETACHED,
            insurance_value=iv,
            volume=vol,
        )
        assert obj.start_date == date(2020, 6, 1)
        assert obj.end_date == date(2030, 12, 31)
        assert obj.usage_code == UsageCode.RESIDENTIAL
        assert obj.usage_description == 'Einfamilienhaus'
        assert obj.location_code == LocationCode.DETACHED
        assert obj.insurance_value.insurance_sum.amount == '500000.00'
        assert obj.volume.volume == 2500

    def test_required_local_id(self):
        with pytest.raises(Exception):
            ECH0129InsuranceObject(insurance_number='VS-001')

    def test_required_insurance_number(self):
        with pytest.raises(Exception):
            ECH0129InsuranceObject(local_id=self._make_named_id())

    def test_all_usage_codes(self):
        for uc in UsageCode:
            obj = ECH0129InsuranceObject(
                local_id=self._make_named_id(),
                insurance_number='VS-001',
                usage_code=uc,
            )
            assert obj.usage_code == uc

    def test_all_location_codes(self):
        for lc in LocationCode:
            obj = ECH0129InsuranceObject(
                local_id=self._make_named_id(),
                insurance_number='VS-001',
                location_code=lc,
            )
            assert obj.location_code == lc

    def test_roundtrip_minimal(self):
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(),
            insurance_number='VS-99',
        )
        xml = obj.to_xml()
        parsed = ECH0129InsuranceObject.from_xml(xml)
        assert parsed.local_id.id_category == 'GVB'
        assert parsed.local_id.id_value == 'OBJ-001'
        assert parsed.insurance_number == 'VS-99'
        assert parsed.start_date is None
        assert parsed.end_date is None
        assert parsed.usage_code is None
        assert parsed.insurance_value is None
        assert parsed.volume is None

    def test_roundtrip_full(self):
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(val='OBJ-FULL'),
            start_date=date(2018, 3, 15),
            end_date=date(2028, 12, 31),
            insurance_number='VS-67890',
            usage_code=UsageCode.GASTRONOMY,
            usage_description='Restaurant',
            location_code=LocationCode.ATTACHED,
            insurance_value=ECH0129InsuranceValue(
                local_id=ECH0129NamedId(id_category='GVB', id_value='V-002'),
                valid_from=date(2022, 1, 1),
                change_reason=ChangeReason.INSURANCE_VALUE,
                insurance_sum=ECH0129InsuranceSum(amount='1200000.00'),
            ),
            volume=ECH0129InsuranceVolume(
                volume=8500, norm=BuildingVolumeNorm.SIA_416,
            ),
        )
        xml = obj.to_xml()
        parsed = ECH0129InsuranceObject.from_xml(xml)
        assert parsed.local_id.id_value == 'OBJ-FULL'
        assert parsed.start_date == date(2018, 3, 15)
        assert parsed.end_date == date(2028, 12, 31)
        assert parsed.insurance_number == 'VS-67890'
        assert parsed.usage_code == UsageCode.GASTRONOMY
        assert parsed.usage_description == 'Restaurant'
        assert parsed.location_code == LocationCode.ATTACHED
        assert parsed.insurance_value.change_reason == ChangeReason.INSURANCE_VALUE
        assert parsed.insurance_value.insurance_sum.amount == '1200000.00'
        assert parsed.volume.volume == 8500
        assert parsed.volume.norm == BuildingVolumeNorm.SIA_416

    def test_xml_element_order(self):
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(),
            start_date=date(2020, 1, 1),
            end_date=date(2030, 1, 1),
            insurance_number='VS-001',
            usage_code=UsageCode.RESIDENTIAL,
            usage_description='Test',
            location_code=LocationCode.UNKNOWN,
            insurance_value=ECH0129InsuranceValue(
                local_id=ECH0129NamedId(id_category='X', id_value='1'),
                valid_from=date(2023, 1, 1),
                change_reason=ChangeReason.NEW_VALUE,
                insurance_sum=ECH0129InsuranceSum(amount='100.00'),
            ),
            volume=ECH0129InsuranceVolume(
                volume=100, norm=BuildingVolumeNorm.SIA_416,
            ),
        )
        xml = obj.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'startDate', 'endDate', 'insuranceNumber',
            'usageCode', 'usageDescription', 'locationCode',
            'insuranceValue', 'volume',
        ]

    def test_double_roundtrip_stability(self):
        obj = ECH0129InsuranceObject(
            local_id=self._make_named_id(),
            insurance_number='VS-DRT',
            start_date=date(2020, 1, 1),
            usage_code=UsageCode.OFFICE,
            insurance_value=ECH0129InsuranceValue(
                local_id=ECH0129NamedId(id_category='X', id_value='1'),
                valid_from=date(2023, 1, 1),
                change_reason=ChangeReason.NEW_VALUE,
                insurance_sum=ECH0129InsuranceSum(percentage='75.00'),
            ),
        )
        xml1 = obj.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129InsuranceObject.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# ECH0129InsuranceObjectOnly
# ===========================================================================

class TestInsuranceObjectOnly:
    def _make_named_id(self):
        return ECH0129NamedId(id_category='GVB', id_value='OBJ-ONLY')

    def test_minimal(self):
        obj = ECH0129InsuranceObjectOnly(
            local_id=self._make_named_id(),
            insurance_number='VS-ONLY',
        )
        assert obj.local_id.id_value == 'OBJ-ONLY'
        assert obj.insurance_number == 'VS-ONLY'
        assert obj.start_date is None
        assert obj.end_date is None
        assert obj.usage_code is None
        assert obj.usage_description is None
        assert obj.location_code is None
        assert obj.volume is None

    def test_no_insurance_value_field(self):
        """insuranceObjectOnlyType has no insuranceValue field."""
        assert not hasattr(ECH0129InsuranceObjectOnly, 'insurance_value') or \
            'insurance_value' not in ECH0129InsuranceObjectOnly.model_fields

    def test_all_fields(self):
        vol = ECH0129InsuranceVolume(
            volume=1200, norm=BuildingVolumeNorm.SIA_116,
        )
        obj = ECH0129InsuranceObjectOnly(
            local_id=self._make_named_id(),
            start_date=date(2019, 5, 1),
            end_date=date(2029, 4, 30),
            insurance_number='VS-FULL-ONLY',
            usage_code=UsageCode.AGRICULTURE,
            usage_description='Scheune',
            location_code=LocationCode.ISOLATED_GT_25M,
            volume=vol,
        )
        assert obj.start_date == date(2019, 5, 1)
        assert obj.end_date == date(2029, 4, 30)
        assert obj.usage_code == UsageCode.AGRICULTURE
        assert obj.usage_description == 'Scheune'
        assert obj.location_code == LocationCode.ISOLATED_GT_25M
        assert obj.volume.volume == 1200

    def test_roundtrip(self):
        obj = ECH0129InsuranceObjectOnly(
            local_id=self._make_named_id(),
            start_date=date(2020, 1, 1),
            insurance_number='VS-RT',
            usage_code=UsageCode.SACRED,
            volume=ECH0129InsuranceVolume(
                volume=5000, norm=BuildingVolumeNorm.SIA_416,
            ),
        )
        xml = obj.to_xml()
        parsed = ECH0129InsuranceObjectOnly.from_xml(xml)
        assert parsed.local_id.id_value == 'OBJ-ONLY'
        assert parsed.start_date == date(2020, 1, 1)
        assert parsed.insurance_number == 'VS-RT'
        assert parsed.usage_code == UsageCode.SACRED
        assert parsed.volume.volume == 5000

    def test_xml_element_order(self):
        obj = ECH0129InsuranceObjectOnly(
            local_id=self._make_named_id(),
            start_date=date(2020, 1, 1),
            end_date=date(2030, 1, 1),
            insurance_number='VS-001',
            usage_code=UsageCode.RESIDENTIAL,
            usage_description='Test',
            location_code=LocationCode.UNKNOWN,
            volume=ECH0129InsuranceVolume(
                volume=100, norm=BuildingVolumeNorm.SIA_416,
            ),
        )
        xml = obj.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'startDate', 'endDate', 'insuranceNumber',
            'usageCode', 'usageDescription', 'locationCode', 'volume',
        ]

    def test_double_roundtrip_stability(self):
        obj = ECH0129InsuranceObjectOnly(
            local_id=self._make_named_id(),
            insurance_number='VS-DRT2',
            location_code=LocationCode.ATTACHED_WITH_FIREWALL,
        )
        xml1 = obj.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed = ECH0129InsuranceObjectOnly.from_xml(xml1)
        xml2 = parsed.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# Import from package
# ===========================================================================

class TestPackageExports:
    def test_import_from_v6(self):
        from openmun_ech.ech0129.v6 import (
            ECH0129InsuranceObject,
            ECH0129InsuranceObjectOnly,
            ECH0129InsuranceSum,
            ECH0129InsuranceValue,
            ECH0129InsuranceVolume,
        )
        assert ECH0129InsuranceObject is not None
        assert ECH0129InsuranceObjectOnly is not None
        assert ECH0129InsuranceSum is not None
        assert ECH0129InsuranceValue is not None
        assert ECH0129InsuranceVolume is not None
