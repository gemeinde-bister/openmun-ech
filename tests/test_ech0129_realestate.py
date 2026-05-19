"""Tests for eCH-0129 v6.0.0 realestate types (Session 3).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints (length, decimal ranges)
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. Enum handling — RealestateType, RealestateStatus, AreaType, etc.
5. Nested types — coordinates, namedMetaData within realestate
"""

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import (
    AreaDescriptionCode,
    AreaType,
    FiscalRelationship,
    OriginOfCoordinates,
    RealestateStatus,
    RealestateType,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129Coordinates,
    ECH0129NamedMetaData,
)
from openmun_ech.ech0129.v6.realestate import (
    ECH0129Area,
    ECH0129FiscalOwnership,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
)

NS_0129 = NS.ECH0129_V6


# ===========================================================================
# ECH0129RealestateIdentification
# ===========================================================================

class TestRealestateIdentification:
    def test_minimal(self):
        """Only required field: number."""
        ri = ECH0129RealestateIdentification(number='1234')
        assert ri.number == '1234'
        assert ri.egrid is None
        assert ri.number_suffix is None
        assert ri.sub_district is None
        assert ri.lot is None

    def test_all_fields(self):
        ri = ECH0129RealestateIdentification(
            egrid='CH123456789012',
            number='567',
            number_suffix='A',
            sub_district='Kreis1',
            lot='Los42',
        )
        assert ri.egrid == 'CH123456789012'
        assert ri.number == '567'
        assert ri.number_suffix == 'A'
        assert ri.sub_district == 'Kreis1'
        assert ri.lot == 'Los42'

    def test_egrid_max_length(self):
        """EGRID: maxLength=14."""
        ri = ECH0129RealestateIdentification(
            egrid='CH123456789012', number='1'
        )
        assert ri.egrid == 'CH123456789012'
        assert len(ri.egrid) == 14

    def test_egrid_too_long(self):
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(
                egrid='CH1234567890123', number='1'  # 15 chars
            )

    def test_number_required(self):
        with pytest.raises(Exception):
            ECH0129RealestateIdentification()

    def test_number_min_length(self):
        """number: minLength=1 — empty string rejected."""
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(number='')

    def test_number_max_length(self):
        """number: maxLength=12."""
        ri = ECH0129RealestateIdentification(number='123456789012')
        assert len(ri.number) == 12

    def test_number_too_long(self):
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(number='1234567890123')  # 13

    def test_number_suffix_constraints(self):
        """numberSuffix: minLength=1, maxLength=12."""
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(number='1', number_suffix='')
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(
                number='1', number_suffix='1234567890123'
            )

    def test_sub_district_constraints(self):
        """subDistrict: minLength=1, maxLength=15."""
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(number='1', sub_district='')
        ri = ECH0129RealestateIdentification(
            number='1', sub_district='123456789012345'
        )
        assert len(ri.sub_district) == 15

    def test_lot_constraints(self):
        """lot: minLength=1, maxLength=15."""
        with pytest.raises(Exception):
            ECH0129RealestateIdentification(number='1', lot='')
        ri = ECH0129RealestateIdentification(
            number='1', lot='123456789012345'
        )
        assert len(ri.lot) == 15

    def test_roundtrip(self):
        ri = ECH0129RealestateIdentification(
            egrid='CH938302947384',
            number='1524',
            number_suffix='bis',
            sub_district='Morel',
            lot='Los1',
        )
        xml = ri.to_xml()
        parsed = ECH0129RealestateIdentification.from_xml(xml)
        assert parsed.egrid == ri.egrid
        assert parsed.number == ri.number
        assert parsed.number_suffix == ri.number_suffix
        assert parsed.sub_district == ri.sub_district
        assert parsed.lot == ri.lot

    def test_roundtrip_minimal(self):
        ri = ECH0129RealestateIdentification(number='42')
        xml = ri.to_xml()
        parsed = ECH0129RealestateIdentification.from_xml(xml)
        assert parsed.number == '42'
        assert parsed.egrid is None
        assert parsed.number_suffix is None
        assert parsed.sub_district is None
        assert parsed.lot is None

    def test_xml_element_names(self):
        """Verify correct camelCase element names in XML output."""
        ri = ECH0129RealestateIdentification(
            egrid='CH1234', number='99', number_suffix='A',
            sub_district='D1', lot='L1',
        )
        xml = ri.to_xml()
        ns = NS_0129
        assert xml.find(f'{{{ns}}}EGRID') is not None
        assert xml.find(f'{{{ns}}}number') is not None
        assert xml.find(f'{{{ns}}}numberSuffix') is not None
        assert xml.find(f'{{{ns}}}subDistrict') is not None
        assert xml.find(f'{{{ns}}}lot') is not None

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        ri = ECH0129RealestateIdentification(
            egrid='CH1234', number='99', number_suffix='A',
            sub_district='D1', lot='L1',
        )
        xml = ri.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == ['EGRID', 'number', 'numberSuffix', 'subDistrict', 'lot']


# ===========================================================================
# ECH0129Realestate
# ===========================================================================

class TestRealestate:
    def _make_identification(self, **kwargs):
        defaults = {'number': '1000'}
        defaults.update(kwargs)
        return ECH0129RealestateIdentification(**defaults)

    def test_minimal(self):
        """Only required fields: realestateIdentification + realestateType."""
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            realestate_type=RealestateType.LIEGENSCHAFT,
        )
        assert r.realestate_identification.number == '1000'
        assert r.realestate_type == RealestateType.LIEGENSCHAFT
        assert r.authority is None
        assert r.date_val is None
        assert r.cantonal_sub_kind is None
        assert r.status is None
        assert r.mutnumber is None
        assert r.ident_dn is None
        assert r.square_measure is None
        assert r.realestate_incomplete is None
        assert r.coordinates is None
        assert r.named_meta_data == []

    def test_all_fields(self):
        coords = ECH0129Coordinates(
            east='2600000.000', north='1200000.000',
            origin_of_coordinates=OriginOfCoordinates.OFFICIAL_SURVEY,
        )
        meta = ECH0129NamedMetaData(
            meta_data_name='source', meta_data_value='AVGBS'
        )
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(
                egrid='CH123456789012'
            ),
            authority='GrundbuchAmt',
            date_val=date(2023, 6, 15),
            realestate_type=RealestateType.STOCKWERKSEINHEIT,
            cantonal_sub_kind='Spezialform',
            status=RealestateStatus.VALID,
            mutnumber='MUT001',
            ident_dn='DN42',
            square_measure='1500.5',
            realestate_incomplete=False,
            coordinates=coords,
            named_meta_data=[meta],
        )
        assert r.authority == 'GrundbuchAmt'
        assert r.date_val == date(2023, 6, 15)
        assert r.realestate_type == RealestateType.STOCKWERKSEINHEIT
        assert r.cantonal_sub_kind == 'Spezialform'
        assert r.status == RealestateStatus.VALID
        assert r.mutnumber == 'MUT001'
        assert r.ident_dn == 'DN42'
        assert r.square_measure == '1500.5'
        assert r.realestate_incomplete is False
        assert r.coordinates == coords
        assert len(r.named_meta_data) == 1

    def test_required_identification(self):
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_type=RealestateType.LIEGENSCHAFT
            )

    def test_required_realestate_type(self):
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification()
            )

    def test_authority_constraints(self):
        """authority: minLength=1, maxLength=12."""
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                authority='',
            )
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                authority='1234567890123',  # 13 chars
            )

    def test_cantonal_sub_kind_constraints(self):
        """cantonalSubKind: minLength=1, maxLength=60."""
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.WEITERE,
                cantonal_sub_kind='',
            )

    def test_square_measure_valid(self):
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            realestate_type=RealestateType.LIEGENSCHAFT,
            square_measure='0.0',
        )
        assert r.square_measure == '0.0'

    def test_square_measure_max(self):
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            realestate_type=RealestateType.LIEGENSCHAFT,
            square_measure='1000000000.0',
        )
        assert r.square_measure == '1000000000.0'

    def test_square_measure_negative(self):
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                square_measure='-1.0',
            )

    def test_square_measure_too_large(self):
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                square_measure='1000000001.0',
            )

    def test_square_measure_invalid(self):
        with pytest.raises(Exception):
            ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                square_measure='not_a_number',
            )

    def test_all_realestate_types(self):
        """Every RealestateType enum value is accepted."""
        for rt in RealestateType:
            r = ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=rt,
            )
            assert r.realestate_type == rt

    def test_all_status_values(self):
        for s in RealestateStatus:
            r = ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                status=s,
            )
            assert r.status == s

    def test_roundtrip_minimal(self):
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            realestate_type=RealestateType.LIEGENSCHAFT,
        )
        xml = r.to_xml()
        parsed = ECH0129Realestate.from_xml(xml)
        assert parsed.realestate_identification.number == '1000'
        assert parsed.realestate_type == RealestateType.LIEGENSCHAFT
        assert parsed.authority is None
        assert parsed.named_meta_data == []

    def test_roundtrip_full(self):
        coords = ECH0129Coordinates(
            east='2600000.000', north='1200000.000',
            origin_of_coordinates=OriginOfCoordinates.OFFICIAL_SURVEY,
        )
        meta1 = ECH0129NamedMetaData(
            meta_data_name='source', meta_data_value='AVGBS'
        )
        meta2 = ECH0129NamedMetaData(
            meta_data_name='region', meta_data_value='Oberwallis'
        )
        r = ECH0129Realestate(
            realestate_identification=ECH0129RealestateIdentification(
                egrid='CH938302947384', number='1524',
                number_suffix='bis', sub_district='Morel',
            ),
            authority='GB-Brig',
            date_val=date(2023, 6, 15),
            realestate_type=RealestateType.STOCKWERKSEINHEIT,
            cantonal_sub_kind='Spezialform',
            status=RealestateStatus.VALID,
            mutnumber='MUT001',
            ident_dn='DN42',
            square_measure='1500.5',
            realestate_incomplete=True,
            coordinates=coords,
            named_meta_data=[meta1, meta2],
        )
        xml = r.to_xml()
        parsed = ECH0129Realestate.from_xml(xml)
        assert parsed.realestate_identification.egrid == 'CH938302947384'
        assert parsed.realestate_identification.number == '1524'
        assert parsed.realestate_identification.number_suffix == 'bis'
        assert parsed.realestate_identification.sub_district == 'Morel'
        assert parsed.authority == 'GB-Brig'
        assert parsed.date_val == date(2023, 6, 15)
        assert parsed.realestate_type == RealestateType.STOCKWERKSEINHEIT
        assert parsed.cantonal_sub_kind == 'Spezialform'
        assert parsed.status == RealestateStatus.VALID
        assert parsed.mutnumber == 'MUT001'
        assert parsed.ident_dn == 'DN42'
        assert parsed.square_measure == '1500.5'
        assert parsed.realestate_incomplete is True
        assert parsed.coordinates.east == '2600000.000'
        assert parsed.coordinates.north == '1200000.000'
        assert len(parsed.named_meta_data) == 2
        assert parsed.named_meta_data[0].meta_data_name == 'source'
        assert parsed.named_meta_data[1].meta_data_name == 'region'

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            authority='GB',
            date_val=date(2023, 1, 1),
            realestate_type=RealestateType.LIEGENSCHAFT,
            cantonal_sub_kind='Art',
            status=RealestateStatus.VALID,
            mutnumber='M1',
            ident_dn='D1',
            square_measure='100.0',
            realestate_incomplete=False,
            coordinates=ECH0129Coordinates(
                east='2600000.000', north='1200000.000'
            ),
            named_meta_data=[
                ECH0129NamedMetaData(
                    meta_data_name='k', meta_data_value='v'
                )
            ],
        )
        xml = r.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'realestateIdentification', 'authority', 'date',
            'realestateType', 'cantonalSubKind', 'status',
            'mutnumber', 'identDN', 'squareMeasure',
            'realestateIncomplete', 'coordinates', 'namedMetaData',
        ]

    def test_multiple_named_meta_data(self):
        """namedMetaData: maxOccurs="unbounded"."""
        metas = [
            ECH0129NamedMetaData(meta_data_name=f'k{i}', meta_data_value=f'v{i}')
            for i in range(5)
        ]
        r = ECH0129Realestate(
            realestate_identification=self._make_identification(),
            realestate_type=RealestateType.LIEGENSCHAFT,
            named_meta_data=metas,
        )
        xml = r.to_xml()
        parsed = ECH0129Realestate.from_xml(xml)
        assert len(parsed.named_meta_data) == 5
        for i in range(5):
            assert parsed.named_meta_data[i].meta_data_name == f'k{i}'
            assert parsed.named_meta_data[i].meta_data_value == f'v{i}'

    def test_realestate_incomplete_true_false(self):
        """xs:boolean roundtrip for true/false."""
        for val in [True, False]:
            r = ECH0129Realestate(
                realestate_identification=self._make_identification(),
                realestate_type=RealestateType.LIEGENSCHAFT,
                realestate_incomplete=val,
            )
            xml = r.to_xml()
            parsed = ECH0129Realestate.from_xml(xml)
            assert parsed.realestate_incomplete is val


# ===========================================================================
# ECH0129FiscalOwnership
# ===========================================================================

class TestFiscalOwnership:
    def test_minimal(self):
        """Only required fields: accessionDate + fiscalRelationship."""
        fo = ECH0129FiscalOwnership(
            accession_date=date(2023, 1, 15),
            fiscal_relationship=FiscalRelationship.OWNER,
        )
        assert fo.accession_date == date(2023, 1, 15)
        assert fo.fiscal_relationship == FiscalRelationship.OWNER
        assert fo.valid_from is None
        assert fo.valid_till is None
        assert fo.denominator is None
        assert fo.numerator is None

    def test_all_fields(self):
        fo = ECH0129FiscalOwnership(
            accession_date=date(2020, 7, 1),
            fiscal_relationship=FiscalRelationship.USUFRUCTUARY,
            valid_from=date(2020, 7, 1),
            valid_till=date(2025, 12, 31),
            denominator='2.000',
            numerator='1.000',
        )
        assert fo.accession_date == date(2020, 7, 1)
        assert fo.fiscal_relationship == FiscalRelationship.USUFRUCTUARY
        assert fo.valid_from == date(2020, 7, 1)
        assert fo.valid_till == date(2025, 12, 31)
        assert fo.denominator == '2.000'
        assert fo.numerator == '1.000'

    def test_required_accession_date(self):
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                fiscal_relationship=FiscalRelationship.OWNER
            )

    def test_required_fiscal_relationship(self):
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1)
            )

    def test_all_fiscal_relationships(self):
        for fr in FiscalRelationship:
            fo = ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=fr,
            )
            assert fo.fiscal_relationship == fr

    def test_denominator_min(self):
        fo = ECH0129FiscalOwnership(
            accession_date=date(2023, 1, 1),
            fiscal_relationship=FiscalRelationship.OWNER,
            denominator='0.001',
        )
        assert fo.denominator == '0.001'

    def test_denominator_max(self):
        fo = ECH0129FiscalOwnership(
            accession_date=date(2023, 1, 1),
            fiscal_relationship=FiscalRelationship.OWNER,
            denominator='1000000.000',
        )
        assert fo.denominator == '1000000.000'

    def test_denominator_too_small(self):
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=FiscalRelationship.OWNER,
                denominator='0.0001',
            )

    def test_denominator_too_large(self):
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=FiscalRelationship.OWNER,
                denominator='1000001.000',
            )

    def test_denominator_invalid(self):
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=FiscalRelationship.OWNER,
                denominator='abc',
            )

    def test_numerator_constraints(self):
        """Same range as denominator: 0.001–1000000.000."""
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=FiscalRelationship.OWNER,
                numerator='0.0001',
            )
        with pytest.raises(Exception):
            ECH0129FiscalOwnership(
                accession_date=date(2023, 1, 1),
                fiscal_relationship=FiscalRelationship.OWNER,
                numerator='1000001.000',
            )

    def test_roundtrip_minimal(self):
        fo = ECH0129FiscalOwnership(
            accession_date=date(2023, 1, 15),
            fiscal_relationship=FiscalRelationship.OWNER,
        )
        xml = fo.to_xml()
        parsed = ECH0129FiscalOwnership.from_xml(xml)
        assert parsed.accession_date == date(2023, 1, 15)
        assert parsed.fiscal_relationship == FiscalRelationship.OWNER
        assert parsed.valid_from is None
        assert parsed.valid_till is None
        assert parsed.denominator is None
        assert parsed.numerator is None

    def test_roundtrip_full(self):
        fo = ECH0129FiscalOwnership(
            accession_date=date(2020, 7, 1),
            fiscal_relationship=FiscalRelationship.RESIDENTIAL_RIGHT,
            valid_from=date(2020, 7, 1),
            valid_till=date(2030, 6, 30),
            denominator='3.000',
            numerator='1.000',
        )
        xml = fo.to_xml()
        parsed = ECH0129FiscalOwnership.from_xml(xml)
        assert parsed.accession_date == date(2020, 7, 1)
        assert parsed.fiscal_relationship == FiscalRelationship.RESIDENTIAL_RIGHT
        assert parsed.valid_from == date(2020, 7, 1)
        assert parsed.valid_till == date(2030, 6, 30)
        assert parsed.denominator == '3.000'
        assert parsed.numerator == '1.000'

    def test_xml_element_order(self):
        """Elements must appear in XSD sequence order."""
        fo = ECH0129FiscalOwnership(
            accession_date=date(2023, 1, 1),
            fiscal_relationship=FiscalRelationship.OWNER,
            valid_from=date(2023, 1, 1),
            valid_till=date(2024, 12, 31),
            denominator='2.000',
            numerator='1.000',
        )
        xml = fo.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'accessionDate', 'fiscalRelationship',
            'validFrom', 'validTill',
            'denominator', 'numerator',
        ]

    def test_double_roundtrip_stability(self):
        """Serialize → parse → serialize → parse — must be identical."""
        fo = ECH0129FiscalOwnership(
            accession_date=date(2020, 7, 1),
            fiscal_relationship=FiscalRelationship.USUFRUCTUARY,
            valid_from=date(2020, 7, 1),
            denominator='4.000',
            numerator='1.500',
        )
        xml1 = fo.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed1 = ECH0129FiscalOwnership.from_xml(xml1)
        xml2 = parsed1.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# ECH0129Area
# ===========================================================================

class TestArea:
    def test_creation(self):
        """All 4 fields are required."""
        a = ECH0129Area(
            area_type=AreaType.GROUND_COVER,
            area_description_code=AreaDescriptionCode.GEBAEUDE,
            area_description='Wohngebaeude',
            area_value='250.5',
        )
        assert a.area_type == AreaType.GROUND_COVER
        assert a.area_description_code == AreaDescriptionCode.GEBAEUDE
        assert a.area_description == 'Wohngebaeude'
        assert a.area_value == '250.5'

    def test_all_required(self):
        """Missing any field raises."""
        with pytest.raises(Exception):
            ECH0129Area(
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='X', area_value='1.0',
            )
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description='X', area_value='1.0',
            )
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_value='1.0',
            )
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='X',
            )

    def test_area_description_constraints(self):
        """areaDescription: minLength=1, maxLength=100."""
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='',
                area_value='1.0',
            )

    def test_area_value_valid_zero(self):
        a = ECH0129Area(
            area_type=AreaType.GROUND_COVER,
            area_description_code=AreaDescriptionCode.GEBAEUDE,
            area_description='X',
            area_value='0.0',
        )
        assert a.area_value == '0.0'

    def test_area_value_max(self):
        a = ECH0129Area(
            area_type=AreaType.GROUND_COVER,
            area_description_code=AreaDescriptionCode.GEBAEUDE,
            area_description='X',
            area_value='1000000000.0',
        )
        assert a.area_value == '1000000000.0'

    def test_area_value_negative(self):
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='X',
                area_value='-0.1',
            )

    def test_area_value_too_large(self):
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='X',
                area_value='1000000001.0',
            )

    def test_area_value_invalid(self):
        with pytest.raises(Exception):
            ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='X',
                area_value='abc',
            )

    def test_all_area_types(self):
        for at in AreaType:
            a = ECH0129Area(
                area_type=at,
                area_description_code=AreaDescriptionCode.GEBAEUDE,
                area_description='Test',
                area_value='1.0',
            )
            assert a.area_type == at

    def test_all_description_codes(self):
        for adc in AreaDescriptionCode:
            a = ECH0129Area(
                area_type=AreaType.GROUND_COVER,
                area_description_code=adc,
                area_description='Test',
                area_value='1.0',
            )
            assert a.area_description_code == adc

    def test_roundtrip(self):
        a = ECH0129Area(
            area_type=AreaType.USAGE_ZONES,
            area_description_code=AreaDescriptionCode.ACKER_WIESE_WEIDE,
            area_description='Weideland Alpgebiet',
            area_value='35000.75',
        )
        xml = a.to_xml()
        parsed = ECH0129Area.from_xml(xml)
        assert parsed.area_type == AreaType.USAGE_ZONES
        assert parsed.area_description_code == AreaDescriptionCode.ACKER_WIESE_WEIDE
        assert parsed.area_description == 'Weideland Alpgebiet'
        assert parsed.area_value == '35000.75'

    def test_xml_element_order(self):
        """All 4 elements in XSD sequence order."""
        a = ECH0129Area(
            area_type=AreaType.GROUND_COVER,
            area_description_code=AreaDescriptionCode.FELS,
            area_description='Felswand',
            area_value='500.0',
        )
        xml = a.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'areaType', 'areaDescriptionCode',
            'areaDescription', 'areaValue',
        ]

    def test_double_roundtrip_stability(self):
        a = ECH0129Area(
            area_type=AreaType.OTHER,
            area_description_code=AreaDescriptionCode.GLETSCHER_FIRN,
            area_description='Aletschgletscher',
            area_value='100000.0',
        )
        xml1 = a.to_xml()
        s1 = ET.tostring(xml1, encoding='unicode')
        parsed1 = ECH0129Area.from_xml(xml1)
        xml2 = parsed1.to_xml()
        s2 = ET.tostring(xml2, encoding='unicode')
        assert s1 == s2


# ===========================================================================
# Import from package
# ===========================================================================

class TestPackageExports:
    def test_import_from_v6(self):
        """All types importable from ech0129.v6."""
        from openmun_ech.ech0129.v6 import (
            ECH0129Area,
            ECH0129FiscalOwnership,
            ECH0129Realestate,
            ECH0129RealestateIdentification,
        )
        assert ECH0129Area is not None
        assert ECH0129FiscalOwnership is not None
        assert ECH0129Realestate is not None
        assert ECH0129RealestateIdentification is not None
