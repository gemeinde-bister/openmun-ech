"""Tests for eCH-0129 v6 street, locality, and place name types.

Field-by-field verification against XSD lines 1161-1493, 1548-1564.
"""

import xml.etree.ElementTree as ET

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0129.enums import (
    PlaceNameType,
    StreetKind,
    StreetLanguage,
    StreetStatus,
)
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId
from openmun_ech.ech0129.v6.street_locality import (
    ECH0129Locality,
    ECH0129LocalityName,
    ECH0129PlaceName,
    ECH0129Street,
    ECH0129StreetDescription,
    ECH0129StreetDescriptionEntry,
    ECH0129StreetSection,
)

NS_URI = NS.ECH0129_V6


# ============================================================================
# ECH0129LocalityName
# ============================================================================


class TestLocalityName:

    def test_creation(self):
        ln = ECH0129LocalityName(name_long='Brig-Glis')
        assert ln.name_long == 'Brig-Glis'
        assert ln.name_short is None

    def test_all_fields(self):
        ln = ECH0129LocalityName(name_long='Brig-Glis', name_short='Brig-Glis')
        assert ln.name_long == 'Brig-Glis'
        assert ln.name_short == 'Brig-Glis'

    def test_name_long_required(self):
        with pytest.raises(Exception):
            ECH0129LocalityName()

    def test_name_long_min_length(self):
        with pytest.raises(Exception):
            ECH0129LocalityName(name_long='X')  # min 2

    def test_name_long_max_length(self):
        with pytest.raises(Exception):
            ECH0129LocalityName(name_long='A' * 41)  # max 40

    def test_name_short_min_length(self):
        with pytest.raises(Exception):
            ECH0129LocalityName(name_long='Valid', name_short='X')  # min 2

    def test_name_short_max_length(self):
        with pytest.raises(Exception):
            ECH0129LocalityName(name_long='Valid', name_short='A' * 19)  # max 18

    def test_roundtrip(self):
        original = ECH0129LocalityName(name_long='Brig-Glis', name_short='Brig')
        xml = original.to_xml()
        restored = ECH0129LocalityName.from_xml(xml)
        assert restored.name_long == 'Brig-Glis'
        assert restored.name_short == 'Brig'

    def test_roundtrip_minimal(self):
        original = ECH0129LocalityName(name_long='Visp')
        xml = original.to_xml()
        restored = ECH0129LocalityName.from_xml(xml)
        assert restored.name_long == 'Visp'
        assert restored.name_short is None

    def test_xml_element_order(self):
        ln = ECH0129LocalityName(name_long='Brig-Glis', name_short='Brig')
        xml = ln.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['nameLong', 'nameShort']

    def test_double_roundtrip_stability(self):
        original = ECH0129LocalityName(name_long='Brig-Glis', name_short='Brig')
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129LocalityName.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129Locality
# ============================================================================


class TestLocality:

    def test_creation_minimal(self):
        loc = ECH0129Locality(
            name=ECH0129LocalityName(name_long='Bister')
        )
        assert loc.swiss_zip_code is None
        assert loc.swiss_zip_code_add_on is None
        assert loc.name.name_long == 'Bister'

    def test_all_fields(self):
        loc = ECH0129Locality(
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            name=ECH0129LocalityName(name_long='Bister', name_short='Bister'),
        )
        assert loc.swiss_zip_code == 3983
        assert loc.swiss_zip_code_add_on == '00'

    def test_name_required(self):
        with pytest.raises(Exception):
            ECH0129Locality()

    def test_zip_code_min(self):
        with pytest.raises(Exception):
            ECH0129Locality(
                swiss_zip_code=999,
                name=ECH0129LocalityName(name_long='Test'),
            )

    def test_zip_code_max(self):
        with pytest.raises(Exception):
            ECH0129Locality(
                swiss_zip_code=10000,
                name=ECH0129LocalityName(name_long='Test'),
            )

    def test_zip_code_add_on_max_length(self):
        with pytest.raises(Exception):
            ECH0129Locality(
                swiss_zip_code_add_on='000',  # max 2
                name=ECH0129LocalityName(name_long='Test'),
            )

    def test_roundtrip_full(self):
        original = ECH0129Locality(
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            name=ECH0129LocalityName(name_long='Bister', name_short='Bister'),
        )
        xml = original.to_xml()
        restored = ECH0129Locality.from_xml(xml)
        assert restored.swiss_zip_code == 3983
        assert restored.swiss_zip_code_add_on == '00'
        assert restored.name.name_long == 'Bister'
        assert restored.name.name_short == 'Bister'

    def test_roundtrip_minimal(self):
        original = ECH0129Locality(
            name=ECH0129LocalityName(name_long='Bister')
        )
        xml = original.to_xml()
        restored = ECH0129Locality.from_xml(xml)
        assert restored.swiss_zip_code is None
        assert restored.name.name_long == 'Bister'

    def test_xml_element_order(self):
        loc = ECH0129Locality(
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            name=ECH0129LocalityName(name_long='Bister'),
        )
        xml = loc.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['swissZipCode', 'swissZipCodeAddOn', 'name']

    def test_double_roundtrip_stability(self):
        original = ECH0129Locality(
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
            name=ECH0129LocalityName(name_long='Bister'),
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129Locality.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129StreetDescriptionEntry
# ============================================================================


class TestStreetDescriptionEntry:

    def test_creation(self):
        entry = ECH0129StreetDescriptionEntry(
            language=StreetLanguage.GERMAN,
            description_long='Bahnhofstrasse',
        )
        assert entry.language == StreetLanguage.GERMAN
        assert entry.description_long == 'Bahnhofstrasse'
        assert entry.description_short is None
        assert entry.description_index is None

    def test_all_fields(self):
        entry = ECH0129StreetDescriptionEntry(
            language=StreetLanguage.FRENCH,
            description_long='Rue de la Gare',
            description_short='Rue de la Gare',
            description_index='Rue',
        )
        assert entry.description_short == 'Rue de la Gare'
        assert entry.description_index == 'Rue'

    def test_description_long_required(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(language=StreetLanguage.GERMAN)

    def test_description_long_min_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='',
            )

    def test_description_long_max_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='A' * 61,  # max 60
            )

    def test_description_short_min_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Valid',
                description_short='',
            )

    def test_description_short_max_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Valid',
                description_short='A' * 25,  # max 24
            )

    def test_description_index_min_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Valid',
                description_index='',
            )

    def test_description_index_max_length(self):
        with pytest.raises(Exception):
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Valid',
                description_index='ABCD',  # max 3
            )


# ============================================================================
# ECH0129StreetDescription
# ============================================================================


class TestStreetDescription:

    def _make_entry(self, lang=StreetLanguage.GERMAN, name='Bahnhofstrasse'):
        return ECH0129StreetDescriptionEntry(
            language=lang, description_long=name
        )

    def test_single_entry(self):
        desc = ECH0129StreetDescription(entries=[self._make_entry()])
        assert len(desc.entries) == 1

    def test_four_entries(self):
        entries = [
            self._make_entry(StreetLanguage.GERMAN, 'Bahnhofstrasse'),
            self._make_entry(StreetLanguage.FRENCH, 'Rue de la Gare'),
            self._make_entry(StreetLanguage.ITALIAN, 'Via della Stazione'),
            self._make_entry(StreetLanguage.ROMANSH, 'Via da la Staziun'),
        ]
        desc = ECH0129StreetDescription(entries=entries)
        assert len(desc.entries) == 4

    def test_empty_entries_rejected(self):
        with pytest.raises(Exception):
            ECH0129StreetDescription(entries=[])

    def test_five_entries_rejected(self):
        entries = [self._make_entry() for _ in range(5)]
        with pytest.raises(Exception):
            ECH0129StreetDescription(entries=entries)

    def test_roundtrip_single_entry(self):
        original = ECH0129StreetDescription(
            entries=[ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
                description_short='Bahnhofstr.',
                description_index='Ba',
            )]
        )
        xml = original.to_xml()
        restored = ECH0129StreetDescription.from_xml(xml)
        assert len(restored.entries) == 1
        e = restored.entries[0]
        assert e.language == StreetLanguage.GERMAN
        assert e.description_long == 'Bahnhofstrasse'
        assert e.description_short == 'Bahnhofstr.'
        assert e.description_index == 'Ba'

    def test_roundtrip_multiple_entries(self):
        original = ECH0129StreetDescription(entries=[
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
                description_short='Bahnhofstr.',
            ),
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.FRENCH,
                description_long='Rue de la Gare',
            ),
        ])
        xml = original.to_xml()
        restored = ECH0129StreetDescription.from_xml(xml)
        assert len(restored.entries) == 2
        assert restored.entries[0].language == StreetLanguage.GERMAN
        assert restored.entries[0].description_long == 'Bahnhofstrasse'
        assert restored.entries[0].description_short == 'Bahnhofstr.'
        assert restored.entries[1].language == StreetLanguage.FRENCH
        assert restored.entries[1].description_long == 'Rue de la Gare'
        assert restored.entries[1].description_short is None

    def test_xml_element_order_per_entry(self):
        desc = ECH0129StreetDescription(
            entries=[ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
                description_short='Bahnhofstr.',
                description_index='Ba',
            )]
        )
        xml = desc.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == [
            'language', 'descriptionLong', 'descriptionShort', 'descriptionIndex'
        ]

    def test_xml_flat_structure_multilingual(self):
        """Repeating groups are flat (not wrapped), per XSD maxOccurs on sequence."""
        desc = ECH0129StreetDescription(entries=[
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
            ),
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.FRENCH,
                description_long='Rue de la Gare',
            ),
        ])
        xml = desc.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        # Flat: no wrapper elements between entries
        assert children == [
            'language', 'descriptionLong',
            'language', 'descriptionLong',
        ]

    def test_double_roundtrip_stability(self):
        original = ECH0129StreetDescription(entries=[
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
                description_short='Bahnhofstr.',
            ),
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.FRENCH,
                description_long='Rue de la Gare',
            ),
        ])
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129StreetDescription.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129Street
# ============================================================================


class TestStreet:

    def _make_desc(self):
        return ECH0129StreetDescription(
            entries=[ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long='Bahnhofstrasse',
            )]
        )

    def test_minimal(self):
        s = ECH0129Street(description=self._make_desc())
        assert s.esid is None
        assert s.is_official_description is None
        assert s.official_street_number is None
        assert s.local_id is None
        assert s.street_kind is None
        assert s.street_status is None
        assert s.street_geometry_xml is None

    def test_all_fields(self):
        s = ECH0129Street(
            esid=12345678,
            is_official_description=True,
            official_street_number=42,
            local_id=ECH0129NamedId(id_category='canton', id_value='VS-123'),
            street_kind=StreetKind.STREET,
            description=self._make_desc(),
            street_status=StreetStatus.EXISTING,
        )
        assert s.esid == 12345678
        assert s.is_official_description is True
        assert s.official_street_number == 42
        assert s.street_kind == StreetKind.STREET
        assert s.street_status == StreetStatus.EXISTING

    def test_description_required(self):
        with pytest.raises(Exception):
            ECH0129Street()

    def test_esid_min(self):
        with pytest.raises(Exception):
            ECH0129Street(esid=9999999, description=self._make_desc())

    def test_esid_max(self):
        with pytest.raises(Exception):
            ECH0129Street(esid=90000001, description=self._make_desc())

    def test_official_street_number_min(self):
        with pytest.raises(Exception):
            ECH0129Street(official_street_number=0, description=self._make_desc())

    def test_official_street_number_max(self):
        with pytest.raises(Exception):
            ECH0129Street(official_street_number=1000000000000, description=self._make_desc())

    def test_roundtrip_minimal(self):
        original = ECH0129Street(description=self._make_desc())
        xml = original.to_xml()
        restored = ECH0129Street.from_xml(xml)
        assert restored.esid is None
        assert restored.description.entries[0].description_long == 'Bahnhofstrasse'

    def test_roundtrip_full(self):
        original = ECH0129Street(
            esid=12345678,
            is_official_description=True,
            official_street_number=42,
            local_id=ECH0129NamedId(id_category='canton', id_value='VS-123'),
            street_kind=StreetKind.STREET,
            description=ECH0129StreetDescription(entries=[
                ECH0129StreetDescriptionEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                    description_short='Bahnhofstr.',
                    description_index='Ba',
                ),
                ECH0129StreetDescriptionEntry(
                    language=StreetLanguage.FRENCH,
                    description_long='Rue de la Gare',
                ),
            ]),
            street_status=StreetStatus.EXISTING,
        )
        xml = original.to_xml()
        restored = ECH0129Street.from_xml(xml)
        assert restored.esid == 12345678
        assert restored.is_official_description is True
        assert restored.official_street_number == 42
        assert restored.local_id.id_category == 'canton'
        assert restored.street_kind == StreetKind.STREET
        assert len(restored.description.entries) == 2
        assert restored.street_status == StreetStatus.EXISTING

    def test_street_geometry_pass_through(self):
        """streetGeometry (xs:anyType) round-trips as raw XML."""
        geo_xml = (
            f'<ns0:streetGeometry xmlns:ns0="{NS_URI}">'
            '<gml>test</gml>'
            f'</ns0:streetGeometry>'
        )
        original = ECH0129Street(
            description=self._make_desc(),
            street_geometry_xml=geo_xml,
        )
        xml = original.to_xml()
        restored = ECH0129Street.from_xml(xml)
        assert restored.street_geometry_xml is not None
        # Parse both and verify content preserved
        rest_geo = ET.fromstring(restored.street_geometry_xml)
        assert rest_geo.tag == f'{{{NS_URI}}}streetGeometry'
        assert len(list(rest_geo)) == 1

    def test_xml_element_order(self):
        s = ECH0129Street(
            esid=12345678,
            is_official_description=True,
            official_street_number=42,
            street_kind=StreetKind.STREET,
            description=self._make_desc(),
            street_status=StreetStatus.EXISTING,
        )
        xml = s.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == [
            'ESID', 'isOfficialDescription', 'officialStreetNumber',
            'streetKind', 'description', 'streetStatus',
        ]

    def test_all_street_kinds(self):
        for kind in StreetKind:
            s = ECH0129Street(street_kind=kind, description=self._make_desc())
            xml = s.to_xml()
            restored = ECH0129Street.from_xml(xml)
            assert restored.street_kind == kind

    def test_all_street_statuses(self):
        for status in StreetStatus:
            s = ECH0129Street(street_status=status, description=self._make_desc())
            xml = s.to_xml()
            restored = ECH0129Street.from_xml(xml)
            assert restored.street_status == status

    def test_double_roundtrip_stability(self):
        original = ECH0129Street(
            esid=12345678,
            description=ECH0129StreetDescription(entries=[
                ECH0129StreetDescriptionEntry(
                    language=StreetLanguage.GERMAN,
                    description_long='Bahnhofstrasse',
                ),
            ]),
            street_status=StreetStatus.EXISTING,
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129Street.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129StreetSection
# ============================================================================


class TestStreetSection:

    def test_creation(self):
        ss = ECH0129StreetSection(
            esid=12345678,
            swiss_zip_code=3983,
            swiss_zip_code_add_on='00',
        )
        assert ss.esid == 12345678
        assert ss.swiss_zip_code == 3983
        assert ss.swiss_zip_code_add_on == '00'

    def test_all_required(self):
        with pytest.raises(Exception):
            ECH0129StreetSection()

        with pytest.raises(Exception):
            ECH0129StreetSection(esid=12345678)

        with pytest.raises(Exception):
            ECH0129StreetSection(esid=12345678, swiss_zip_code=3983)

    def test_esid_min(self):
        with pytest.raises(Exception):
            ECH0129StreetSection(
                esid=9999999, swiss_zip_code=3983, swiss_zip_code_add_on='00'
            )

    def test_esid_max(self):
        with pytest.raises(Exception):
            ECH0129StreetSection(
                esid=90000001, swiss_zip_code=3983, swiss_zip_code_add_on='00'
            )

    def test_zip_code_min(self):
        with pytest.raises(Exception):
            ECH0129StreetSection(
                esid=12345678, swiss_zip_code=999, swiss_zip_code_add_on='00'
            )

    def test_zip_code_max(self):
        with pytest.raises(Exception):
            ECH0129StreetSection(
                esid=12345678, swiss_zip_code=10000, swiss_zip_code_add_on='00'
            )

    def test_add_on_max_length(self):
        with pytest.raises(Exception):
            ECH0129StreetSection(
                esid=12345678, swiss_zip_code=3983, swiss_zip_code_add_on='000'
            )

    def test_roundtrip(self):
        original = ECH0129StreetSection(
            esid=12345678, swiss_zip_code=3983, swiss_zip_code_add_on='00'
        )
        xml = original.to_xml()
        restored = ECH0129StreetSection.from_xml(xml)
        assert restored.esid == 12345678
        assert restored.swiss_zip_code == 3983
        assert restored.swiss_zip_code_add_on == '00'

    def test_xml_element_order(self):
        ss = ECH0129StreetSection(
            esid=12345678, swiss_zip_code=3983, swiss_zip_code_add_on='00'
        )
        xml = ss.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['ESID', 'swissZipCode', 'swissZipCodeAddOn']

    def test_double_roundtrip_stability(self):
        original = ECH0129StreetSection(
            esid=12345678, swiss_zip_code=3983, swiss_zip_code_add_on='00'
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129StreetSection.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2


# ============================================================================
# ECH0129PlaceName
# ============================================================================


class TestPlaceName:

    def test_creation(self):
        pn = ECH0129PlaceName(
            place_name_type=PlaceNameType.FLURNAME,
            local_geographical_name='Oberbister',
        )
        assert pn.place_name_type == PlaceNameType.FLURNAME
        assert pn.local_geographical_name == 'Oberbister'

    def test_all_required(self):
        with pytest.raises(Exception):
            ECH0129PlaceName()

        with pytest.raises(Exception):
            ECH0129PlaceName(place_name_type=PlaceNameType.FLURNAME)

    def test_all_place_name_types(self):
        for pnt in PlaceNameType:
            pn = ECH0129PlaceName(
                place_name_type=pnt,
                local_geographical_name='Test',
            )
            xml = pn.to_xml()
            restored = ECH0129PlaceName.from_xml(xml)
            assert restored.place_name_type == pnt

    def test_roundtrip(self):
        original = ECH0129PlaceName(
            place_name_type=PlaceNameType.ORTSNAME,
            local_geographical_name='Bister',
        )
        xml = original.to_xml()
        restored = ECH0129PlaceName.from_xml(xml)
        assert restored.place_name_type == PlaceNameType.ORTSNAME
        assert restored.local_geographical_name == 'Bister'

    def test_xml_element_order(self):
        pn = ECH0129PlaceName(
            place_name_type=PlaceNameType.LOKALISATIONSNAME,
            local_geographical_name='Bister',
        )
        xml = pn.to_xml()
        children = [c.tag.split('}')[1] for c in xml]
        assert children == ['placeNameType', 'localGeographicalName']

    def test_double_roundtrip_stability(self):
        original = ECH0129PlaceName(
            place_name_type=PlaceNameType.FLURNAME,
            local_geographical_name='Oberbister',
        )
        xml1 = ET.tostring(original.to_xml(), encoding='unicode')
        restored = ECH0129PlaceName.from_xml(ET.fromstring(xml1))
        xml2 = ET.tostring(restored.to_xml(), encoding='unicode')
        assert xml1 == xml2
