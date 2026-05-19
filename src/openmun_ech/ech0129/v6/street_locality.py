"""eCH-0129 v6.0.0 — Street, locality, and place name types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 1161-1493, 1548-1564)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.10, §4.15, §4.16, §4.19)
"""

import xml.etree.ElementTree as ET
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import (
    PlaceNameType,
    StreetKind,
    StreetLanguage,
    StreetStatus,
)
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId


# ---------------------------------------------------------------------------
# localityNameType (§4.10.1.3)
# XSD lines 1161-1179
# ---------------------------------------------------------------------------

class ECH0129LocalityName(ECHModel):
    """eCH-0129 locality name (long + optional short).

    XSD: localityNameType — xs:sequence of 2 elements.
    PDF: §4.10.1.3 (page 68)

    Fields (in XSD order):
    - nameLong: anonymous xs:token, minLength=2, maxLength=40 (REQUIRED)
    - nameShort: anonymous xs:token, minLength=2, maxLength=18, minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'name'

    name_long: str = xml_field('nameLong', min_length=2, max_length=40)
    name_short: Optional[str] = xml_field(
        'nameShort', default=None, min_length=2, max_length=18
    )


# ---------------------------------------------------------------------------
# localityType (§4.10)
# XSD lines 1181-1187
# ---------------------------------------------------------------------------

class ECH0129Locality(ECHModel):
    """eCH-0129 locality (PLZ + name).

    XSD: localityType — xs:sequence of 3 elements.
    PDF: §4.10 (page 67-68)

    Fields (in XSD order):
    - swissZipCode: eCH-0010:swissZipCodeType (unsignedInt, 1000-9999), minOccurs="0"
    - swissZipCodeAddOn: eCH-0010:swissZipCodeAddOnType (string, maxLength=2), minOccurs="0"
    - name: localityNameType (REQUIRED)

    Note: element names are in eCH-0129 namespace; types reference eCH-0010
    simpleTypes for validation constraints only.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'locality'

    swiss_zip_code: Optional[int] = xml_field(
        'swissZipCode', default=None, ge=1000, le=9999
    )
    swiss_zip_code_add_on: Optional[str] = xml_field(
        'swissZipCodeAddOn', default=None, max_length=2
    )
    name: ECH0129LocalityName = xml_field('name')


# ---------------------------------------------------------------------------
# streetDescriptionType (§4.15) — repeating group helper
# XSD lines 1486-1492
# ---------------------------------------------------------------------------

class ECH0129StreetDescriptionEntry(BaseModel):
    """Single language entry in a street description.

    Not an ECHModel — this is a helper for the repeating group in
    streetDescriptionType (xs:sequence maxOccurs="4"). Each entry
    represents one language variant of a street name.

    Fields match the inner sequence elements:
    - language: streetLanguageType enum (REQUIRED)
    - descriptionLong: streetDescriptionLongType, xs:token 1-60 (REQUIRED)
    - descriptionShort: streetDescriptionShortType, xs:token 1-24, minOccurs="0"
    - descriptionIndex: streetIndexNameType, xs:token 1-3, minOccurs="0"
    """

    language: StreetLanguage
    description_long: str = Field(min_length=1, max_length=60)
    description_short: Optional[str] = Field(
        default=None, min_length=1, max_length=24
    )
    description_index: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )


class ECH0129StreetDescription(ECHModel):
    """eCH-0129 street description (multilingual, up to 4 languages).

    XSD: streetDescriptionType — xs:sequence with maxOccurs="4".
    PDF: §4.15 (page 82-83)

    The XSD uses a repeating sequence (not a repeating element), meaning
    the child elements (language, descriptionLong, descriptionShort,
    descriptionIndex) appear flat within the parent, grouped by language.

    Custom to_xml()/from_xml() handles the repeating group serialization.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'description'

    # Not an xml_field — custom serialization handles this
    entries: list[ECH0129StreetDescriptionEntry] = Field(
        min_length=1, max_length=4
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
    ) -> ET.Element:
        ns = namespace or self.__xml_ns__
        el_name = element_name or self.__xml_element__
        root_ns = wrapper_namespace or ns

        tag = f'{{{root_ns}}}{el_name}'
        elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

        for entry in self.entries:
            sub = ET.SubElement(elem, f'{{{ns}}}language')
            sub.text = str(entry.language.value)

            sub = ET.SubElement(elem, f'{{{ns}}}descriptionLong')
            sub.text = entry.description_long

            if entry.description_short is not None:
                sub = ET.SubElement(elem, f'{{{ns}}}descriptionShort')
                sub.text = entry.description_short

            if entry.description_index is not None:
                sub = ET.SubElement(elem, f'{{{ns}}}descriptionIndex')
                sub.text = entry.description_index

        return elem

    @classmethod
    def from_xml(
        cls, elem: ET.Element, namespace: str | None = None,
    ) -> 'ECH0129StreetDescription':
        ns = namespace or cls.__xml_ns__
        entries: list[dict] = []
        current: dict | None = None

        for child in elem:
            local = child.tag.split('}')[1] if '}' in child.tag else child.tag
            text = child.text.strip() if child.text else ''

            if local == 'language':
                if current is not None:
                    entries.append(current)
                current = {'language': StreetLanguage(text)}
            elif local == 'descriptionLong' and current is not None:
                current['description_long'] = text
            elif local == 'descriptionShort' and current is not None:
                current['description_short'] = text
            elif local == 'descriptionIndex' and current is not None:
                current['description_index'] = text

        if current is not None:
            entries.append(current)

        return cls(
            entries=[ECH0129StreetDescriptionEntry(**e) for e in entries]
        )


# ---------------------------------------------------------------------------
# streetType (§4.15)
# XSD lines 1458-1468
# ---------------------------------------------------------------------------

class ECH0129Street(ECHModel):
    """eCH-0129 street.

    XSD: streetType — xs:sequence of 8 elements.
    PDF: §4.15 (page 82-84)

    Fields (in XSD order):
    - ESID: ESIDType (nonNegativeInteger, 10000000-90000000), minOccurs="0"
    - isOfficialDescription: isOfficialDescriptionType (boolean), minOccurs="0"
    - officialStreetNumber: officialStreetNumberType (nonNegativeInteger, 1-999999999999), minOccurs="0"
    - localID: namedIdType, minOccurs="0"
    - streetKind: streetKindType enum, minOccurs="0"
    - description: streetDescriptionType (REQUIRED)
    - streetStatus: streetStatusType enum, minOccurs="0"
    - streetGeometry: xs:anyType, minOccurs="0" — raw XML pass-through
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'street'

    esid: Optional[int] = xml_field(
        'ESID', default=None, ge=10000000, le=90000000
    )
    is_official_description: Optional[bool] = xml_field(
        'isOfficialDescription', default=None
    )
    official_street_number: Optional[int] = xml_field(
        'officialStreetNumber', default=None, ge=1, le=999999999999
    )
    local_id: Optional[ECH0129NamedId] = xml_field('localID', default=None)
    street_kind: Optional[StreetKind] = xml_field('streetKind', default=None)
    description: ECH0129StreetDescription = xml_field('description')
    street_status: Optional[StreetStatus] = xml_field('streetStatus', default=None)

    # xs:anyType — not an xml_field, handled by custom to_xml/from_xml
    street_geometry_xml: Optional[str] = None

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
    ) -> ET.Element:
        # Generic serialization handles fields 1-7
        elem = super().to_xml(parent, namespace, element_name, wrapper_namespace)

        # Append streetGeometry (field 8) if present
        if self.street_geometry_xml is not None:
            geo_elem = ET.fromstring(self.street_geometry_xml)
            elem.append(geo_elem)

        return elem

    @classmethod
    def from_xml(
        cls, elem: ET.Element, namespace: str | None = None,
    ) -> 'ECH0129Street':
        ns = namespace or cls.__xml_ns__
        # Generic deserialization handles fields 1-7
        # (streetGeometry is not an xml_field, so it's ignored)
        instance = super().from_xml(elem, namespace)

        # Extract streetGeometry if present
        geo_elem = elem.find(f'{{{ns}}}streetGeometry')
        if geo_elem is not None:
            instance.street_geometry_xml = ET.tostring(
                geo_elem, encoding='unicode'
            )

        return instance


# ---------------------------------------------------------------------------
# streetSectionType (§4.16)
# XSD lines 1470-1476
# ---------------------------------------------------------------------------

class ECH0129StreetSection(ECHModel):
    """eCH-0129 street section (ESID + PLZ).

    XSD: streetSectionType — xs:sequence of 3 required elements.
    PDF: §4.16 (page 84-85)

    Fields (in XSD order, ALL required):
    - ESID: ESIDType (nonNegativeInteger, 10000000-90000000)
    - swissZipCode: eCH-0010:swissZipCodeType (unsignedInt, 1000-9999)
    - swissZipCodeAddOn: eCH-0010:swissZipCodeAddOnType (string, maxLength=2)

    Note: element names are in eCH-0129 namespace; eCH-0010 types provide
    validation constraints only.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'streetSection'

    esid: int = xml_field('ESID', ge=10000000, le=90000000)
    swiss_zip_code: int = xml_field('swissZipCode', ge=1000, le=9999)
    swiss_zip_code_add_on: str = xml_field('swissZipCodeAddOn', max_length=2)


# ---------------------------------------------------------------------------
# placeNameType (§4.19)
# XSD lines 1559-1563
# ---------------------------------------------------------------------------

class ECH0129PlaceName(ECHModel):
    """eCH-0129 place name (Lagebezeichnung).

    XSD: placeNameType — xs:sequence of 2 required elements.
    PDF: §4.19 (page 88)

    Fields (in XSD order, ALL required):
    - placeNameType: placeNameTypeType enum (0-3)
    - localGeographicalName: localGeographicalNameType (xs:token, no length constraints)

    Note: element name 'placeNameType' matches the complexType name — same
    pattern as realestateType in realestate.py.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'placeName'

    place_name_type: PlaceNameType = xml_field('placeNameType')
    local_geographical_name: str = xml_field('localGeographicalName')
