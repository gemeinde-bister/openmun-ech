"""Tests for eCH-0129 v6 cadastral types (right, map, remark, SDR, partial area).

Field-by-field verification against XSD lines 1500-1577.
"""

import xml.etree.ElementTree as ET

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import RemarkType
from openmun_ech.ech0129.v6.cadastral import (
    ECH0129CadastralMap,
    ECH0129CadastralSurveyorRemark,
    ECH0129CoveringAreaOfSDR,
    ECH0129PartialAreaOfBuilding,
    ECH0129Right,
)
from openmun_ech.ech0129.v6.realestate import ECH0129RealestateIdentification

NS_URI = NS.ECH0129_V6


# ============================================================================
# ECH0129Right
# ============================================================================


class TestRight:

    def test_creation_minimal(self):
        r = ECH0129Right(ereid='CH123456')
        assert r.ereid == 'CH123456'
        assert r.protected is None

    def test_all_fields(self):
        r = ECH0129Right(ereid='CH123456', protected=True)
        assert r.ereid == 'CH123456'
        assert r.protected is True

    def test_ereid_required(self):
        with pytest.raises(Exception):
            ECH0129Right()

    def test_protected_values(self):
        for val in (True, False):
            r = ECH0129Right(ereid='X', protected=val)
            xml = r.to_xml()
            restored = ECH0129Right.from_xml(xml)
            assert restored.protected == val

    def test_roundtrip_minimal(self):
        original = ECH0129Right(ereid='CH-VS-123')
        xml = original.to_xml()
        restored = ECH0129Right.from_xml(xml)
        assert restored.ereid == 'CH-VS-123'
        assert restored.protected is None

    def test_roundtrip_full(self):
        original = ECH0129Right(ereid='CH-VS-123', protected=False)
        xml = original.to_xml()
        restored = ECH0129Right.from_xml(xml)
        assert restored.ereid == 'CH-VS-123'
        assert restored.protected is False

    def test_xml_element_order(self):
        r = ECH0129Right(ereid='X', protected=True)
        xml = r.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['EREID', 'protected']

    def test_double_roundtrip_stability(self):
        original = ECH0129Right(ereid='CH-VS-123', protected=True)
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129Right.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129CadastralMap
# ============================================================================


class TestCadastralMap:

    def test_creation(self):
        cm = ECH0129CadastralMap(map_number='Plan-42', ident_dn='VS-DN-1')
        assert cm.map_number == 'Plan-42'
        assert cm.ident_dn == 'VS-DN-1'

    def test_all_required(self):
        with pytest.raises(Exception):
            ECH0129CadastralMap()

        with pytest.raises(Exception):
            ECH0129CadastralMap(map_number='Plan-42')

    def test_map_number_min_length(self):
        with pytest.raises(Exception):
            ECH0129CadastralMap(map_number='', ident_dn='VS-1')

    def test_map_number_max_length(self):
        with pytest.raises(Exception):
            ECH0129CadastralMap(map_number='A' * 13, ident_dn='VS-1')

    def test_ident_dn_min_length(self):
        with pytest.raises(Exception):
            ECH0129CadastralMap(map_number='Plan-1', ident_dn='')

    def test_ident_dn_max_length(self):
        with pytest.raises(Exception):
            ECH0129CadastralMap(map_number='Plan-1', ident_dn='A' * 13)

    def test_roundtrip(self):
        original = ECH0129CadastralMap(map_number='Plan-42', ident_dn='VS-DN-1')
        xml = original.to_xml()
        restored = ECH0129CadastralMap.from_xml(xml)
        assert restored.map_number == 'Plan-42'
        assert restored.ident_dn == 'VS-DN-1'

    def test_xml_element_order(self):
        cm = ECH0129CadastralMap(map_number='P1', ident_dn='D1')
        xml = cm.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['mapNumber', 'identDN']

    def test_double_roundtrip_stability(self):
        original = ECH0129CadastralMap(map_number='Plan-42', ident_dn='VS-DN-1')
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129CadastralMap.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129CadastralSurveyorRemark
# ============================================================================


class TestCadastralSurveyorRemark:

    def test_creation_minimal(self):
        r = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.DISPUTED_BOUNDARY,
            remark_text='Grenze umstritten',
            object_id='OBJ-42',
        )
        assert r.remark_type == RemarkType.DISPUTED_BOUNDARY
        assert r.remark_other_type is None
        assert r.remark_text == 'Grenze umstritten'
        assert r.object_id == 'OBJ-42'

    def test_all_fields(self):
        r = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.OTHER,
            remark_other_type='Sonderfall',
            remark_text='Spezielle Vermerkung',
            object_id='OBJ-99',
        )
        assert r.remark_type == RemarkType.OTHER
        assert r.remark_other_type == 'Sonderfall'

    def test_required_fields(self):
        with pytest.raises(Exception):
            ECH0129CadastralSurveyorRemark()

        with pytest.raises(Exception):
            ECH0129CadastralSurveyorRemark(
                remark_type=RemarkType.DISPUTED_BOUNDARY,
            )

    def test_all_remark_types(self):
        for rt in RemarkType:
            r = ECH0129CadastralSurveyorRemark(
                remark_type=rt,
                remark_text='text',
                object_id='obj',
            )
            xml = r.to_xml()
            restored = ECH0129CadastralSurveyorRemark.from_xml(xml)
            assert restored.remark_type == rt

    def test_roundtrip_minimal(self):
        original = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.SURVEY_POINT,
            remark_text='LFP-12 kontrolliert',
            object_id='LFP-12',
        )
        xml = original.to_xml()
        restored = ECH0129CadastralSurveyorRemark.from_xml(xml)
        assert restored.remark_type == RemarkType.SURVEY_POINT
        assert restored.remark_other_type is None
        assert restored.remark_text == 'LFP-12 kontrolliert'
        assert restored.object_id == 'LFP-12'

    def test_roundtrip_full(self):
        original = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.OTHER,
            remark_other_type='Sonderfall',
            remark_text='Besondere Situation',
            object_id='SPEC-1',
        )
        xml = original.to_xml()
        restored = ECH0129CadastralSurveyorRemark.from_xml(xml)
        assert restored.remark_type == RemarkType.OTHER
        assert restored.remark_other_type == 'Sonderfall'
        assert restored.remark_text == 'Besondere Situation'
        assert restored.object_id == 'SPEC-1'

    def test_xml_element_order(self):
        r = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.OTHER,
            remark_other_type='X',
            remark_text='Y',
            object_id='Z',
        )
        xml = r.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['remarkType', 'remarkOtherType', 'remarkText', 'objectID']

    def test_double_roundtrip_stability(self):
        original = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.CULVERTED_WATER,
            remark_text='Eingedolter Bach',
            object_id='BACH-3',
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129CadastralSurveyorRemark.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129CoveringAreaOfSDR
# ============================================================================


class TestCoveringAreaOfSDR:

    def _make_realestate_id(self):
        return ECH0129RealestateIdentification(number='1234')

    def test_creation(self):
        ca = ECH0129CoveringAreaOfSDR(
            square_measure='500.0',
            realestate_identification=self._make_realestate_id(),
        )
        assert ca.square_measure == '500.0'

    def test_all_required(self):
        with pytest.raises(Exception):
            ECH0129CoveringAreaOfSDR()

        with pytest.raises(Exception):
            ECH0129CoveringAreaOfSDR(square_measure='100.0')

    def test_square_measure_valid_zero(self):
        ca = ECH0129CoveringAreaOfSDR(
            square_measure='0.0',
            realestate_identification=self._make_realestate_id(),
        )
        assert ca.square_measure == '0.0'

    def test_square_measure_max(self):
        ca = ECH0129CoveringAreaOfSDR(
            square_measure='1000000000.0',
            realestate_identification=self._make_realestate_id(),
        )
        assert ca.square_measure == '1000000000.0'

    def test_square_measure_negative(self):
        with pytest.raises(Exception):
            ECH0129CoveringAreaOfSDR(
                square_measure='-1.0',
                realestate_identification=self._make_realestate_id(),
            )

    def test_square_measure_too_large(self):
        with pytest.raises(Exception):
            ECH0129CoveringAreaOfSDR(
                square_measure='1000000001.0',
                realestate_identification=self._make_realestate_id(),
            )

    def test_square_measure_invalid(self):
        with pytest.raises(Exception):
            ECH0129CoveringAreaOfSDR(
                square_measure='abc',
                realestate_identification=self._make_realestate_id(),
            )

    def test_roundtrip(self):
        original = ECH0129CoveringAreaOfSDR(
            square_measure='12345.67',
            realestate_identification=ECH0129RealestateIdentification(
                egrid='CH123456789012',
                number='567',
            ),
        )
        xml = original.to_xml()
        restored = ECH0129CoveringAreaOfSDR.from_xml(xml)
        assert restored.square_measure == '12345.67'
        assert restored.realestate_identification.egrid == 'CH123456789012'
        assert restored.realestate_identification.number == '567'

    def test_xml_element_order(self):
        ca = ECH0129CoveringAreaOfSDR(
            square_measure='100.0',
            realestate_identification=self._make_realestate_id(),
        )
        xml = ca.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['squareMeasure', 'realestateIdentification']

    def test_double_roundtrip_stability(self):
        original = ECH0129CoveringAreaOfSDR(
            square_measure='999.99',
            realestate_identification=ECH0129RealestateIdentification(
                number='42',
            ),
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129CoveringAreaOfSDR.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129PartialAreaOfBuilding
# ============================================================================


class TestPartialAreaOfBuilding:

    def test_creation_empty(self):
        pa = ECH0129PartialAreaOfBuilding()
        assert pa.square_measure is None

    def test_creation_with_value(self):
        pa = ECH0129PartialAreaOfBuilding(square_measure='250.5')
        assert pa.square_measure == '250.5'

    def test_square_measure_valid_zero(self):
        pa = ECH0129PartialAreaOfBuilding(square_measure='0.0')
        assert pa.square_measure == '0.0'

    def test_square_measure_max(self):
        pa = ECH0129PartialAreaOfBuilding(square_measure='1000000000.0')
        assert pa.square_measure == '1000000000.0'

    def test_square_measure_negative(self):
        with pytest.raises(Exception):
            ECH0129PartialAreaOfBuilding(square_measure='-0.1')

    def test_square_measure_too_large(self):
        with pytest.raises(Exception):
            ECH0129PartialAreaOfBuilding(square_measure='1000000001.0')

    def test_square_measure_invalid(self):
        with pytest.raises(Exception):
            ECH0129PartialAreaOfBuilding(square_measure='not-a-number')

    def test_roundtrip_empty(self):
        original = ECH0129PartialAreaOfBuilding()
        xml = original.to_xml()
        restored = ECH0129PartialAreaOfBuilding.from_xml(xml)
        assert restored.square_measure is None

    def test_roundtrip_with_value(self):
        original = ECH0129PartialAreaOfBuilding(square_measure='42.123')
        xml = original.to_xml()
        restored = ECH0129PartialAreaOfBuilding.from_xml(xml)
        assert restored.square_measure == '42.123'

    def test_xml_element_present(self):
        pa = ECH0129PartialAreaOfBuilding(square_measure='100.0')
        xml = pa.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['squareMeasure']

    def test_xml_element_absent(self):
        pa = ECH0129PartialAreaOfBuilding()
        xml = pa.to_xml()
        assert len(list(xml)) == 0

    def test_double_roundtrip_stability(self):
        original = ECH0129PartialAreaOfBuilding(square_measure='77.77')
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129PartialAreaOfBuilding.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2
