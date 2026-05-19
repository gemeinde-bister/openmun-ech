"""eCH-0129 v6.0.0 — Building entrance and address types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 834-862, 1790-1853)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.7, pages 55-60)

Types in this module depend on:
- eCH-0129 base_types (ECH0129NamedId, ECH0129Coordinates)
- eCH-0129 street_locality (ECH0129StreetSection)
- eCH-0129 enums (BuildingStatus, StreetLanguage)

Anonymous inline streetDescription:
  Both buildingAddressType and buildingAddressLightType contain an anonymous
  inline complexType for streetDescription that differs from the named
  streetDescriptionType (§4.15). The anonymous type has only 2 fields per
  language entry (language + descriptionLong), vs 4 in the named type
  (+ descriptionShort + descriptionIndex). A separate helper class
  ECH0129AddressStreetEntry handles the simpler structure.
"""

import xml.etree.ElementTree as ET
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import BuildingStatus, StreetLanguage
from openmun_ech.ech0129.v6.base_types import ECH0129Coordinates, ECH0129NamedId
from openmun_ech.ech0129.v6.street_locality import ECH0129StreetSection


# ---------------------------------------------------------------------------
# Anonymous inline streetDescription helper
# Used by buildingAddressType (XSD 1798-1804) and
# buildingAddressLightType (XSD 1834-1840)
# ---------------------------------------------------------------------------

class ECH0129AddressStreetEntry(BaseModel):
    """Single language entry in building address street description.

    Not an ECHModel — helper for the anonymous inline complexType in
    buildingAddressType and buildingAddressLightType. Each entry represents
    one language variant.

    Fields match the inner sequence elements:
    - language: streetLanguageType enum (REQUIRED)
    - descriptionLong: streetDescriptionLongType, xs:token 1-60 (REQUIRED)

    Note: this is simpler than ECH0129StreetDescriptionEntry (§4.15) which
    also has descriptionShort and descriptionIndex.
    """

    language: StreetLanguage
    description_long: str = Field(min_length=1, max_length=60)


class ECH0129AddressStreetDescription(ECHModel):
    """Anonymous inline streetDescription for building address types.

    XSD: anonymous complexType inside buildingAddressType and
    buildingAddressLightType — xs:sequence with maxOccurs="4".

    The inner sequence (language + descriptionLong) repeats up to 4 times,
    serialized flat (no wrapper per entry). Each 'language' element starts
    a new group.

    Custom to_xml()/from_xml() handles the repeating group serialization.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'streetDescription'

    # Not an xml_field — custom serialization handles this
    entries: list[ECH0129AddressStreetEntry] = Field(
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
        elem = (
            ET.SubElement(parent, tag)
            if parent is not None
            else ET.Element(tag)
        )

        for entry in self.entries:
            sub = ET.SubElement(elem, f'{{{ns}}}language')
            sub.text = str(entry.language.value)

            sub = ET.SubElement(elem, f'{{{ns}}}descriptionLong')
            sub.text = entry.description_long

        return elem

    @classmethod
    def from_xml(
        cls, elem: ET.Element, namespace: str | None = None,
    ) -> 'ECH0129AddressStreetDescription':
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

        if current is not None:
            entries.append(current)

        return cls(
            entries=[ECH0129AddressStreetEntry(**e) for e in entries]
        )


# ---------------------------------------------------------------------------
# buildingEntranceIdentificationType (§4.7.1, XSD lines 834-841)
# ---------------------------------------------------------------------------

class ECH0129BuildingEntranceIdentification(ECHModel):
    """eCH-0129 building entrance identification.

    XSD: buildingEntranceIdentificationType — xs:sequence, 2 required + 2 optional.
    PDF: §4.7.1 (page 55-57)

    Fields (in XSD order):
    - EGID: EGIDType (nonNegativeInteger, 1-900000000)
    - EGAID: EGAIDType (nonNegativeInteger, 100000000-900000000), minOccurs="0"
    - EDID: EDIDType (nonNegativeInteger, 0-90), minOccurs="0"
    - localID: namedIdType
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingEntranceIdentification'

    egid: int = xml_field('EGID', ge=1, le=900000000)
    egaid: Optional[int] = xml_field(
        'EGAID', default=None, ge=100000000, le=900000000
    )
    edid: Optional[int] = xml_field('EDID', default=None, ge=0, le=90)
    local_id: ECH0129NamedId = xml_field('localID')


# ---------------------------------------------------------------------------
# buildingEntranceType (§4.7, XSD lines 842-852)
# ---------------------------------------------------------------------------

class ECH0129BuildingEntrance(ECHModel):
    """eCH-0129 building entrance (full, with street section).

    XSD: buildingEntranceType — xs:sequence of 7 elements.
    PDF: §4.7 (page 55-57, Abb. 13)

    Fields (in XSD order):
    - EGAID: EGAIDType (nonNegativeInteger, 100000000-900000000), minOccurs="0"
    - EDID: EDIDType (nonNegativeInteger, 0-90), minOccurs="0"
    - buildingEntranceNo: buildingEntranceNoType (xs:token 1-12), minOccurs="0"
    - coordinates: coordinatesType, minOccurs="0"
    - localID: namedIdType (REQUIRED)
    - isOfficialAddress: xs:boolean, minOccurs="0"
    - streetSection: streetSectionType (REQUIRED)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingEntrance'

    egaid: Optional[int] = xml_field(
        'EGAID', default=None, ge=100000000, le=900000000
    )
    edid: Optional[int] = xml_field('EDID', default=None, ge=0, le=90)
    building_entrance_no: Optional[str] = xml_field(
        'buildingEntranceNo', default=None, min_length=1, max_length=12
    )
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    local_id: ECH0129NamedId = xml_field('localID')
    is_official_address: Optional[bool] = xml_field(
        'isOfficialAddress', default=None
    )
    street_section: ECH0129StreetSection = xml_field('streetSection')


# ---------------------------------------------------------------------------
# buildingEntranceOnlyType (§4.7, XSD lines 853-862)
# ---------------------------------------------------------------------------

class ECH0129BuildingEntranceOnly(ECHModel):
    """eCH-0129 building entrance (without street section).

    XSD: buildingEntranceOnlyType — xs:sequence of 6 elements.
    PDF: §4.7 (page 55-57, Abb. 13)

    Identical to buildingEntranceType but without the streetSection element.

    Fields (in XSD order):
    - EGAID: EGAIDType (nonNegativeInteger, 100000000-900000000), minOccurs="0"
    - EDID: EDIDType (nonNegativeInteger, 0-90), minOccurs="0"
    - buildingEntranceNo: buildingEntranceNoType (xs:token 1-12), minOccurs="0"
    - coordinates: coordinatesType, minOccurs="0"
    - localID: namedIdType (REQUIRED)
    - isOfficialAddress: xs:boolean, minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingEntranceOnly'

    egaid: Optional[int] = xml_field(
        'EGAID', default=None, ge=100000000, le=900000000
    )
    edid: Optional[int] = xml_field('EDID', default=None, ge=0, le=90)
    building_entrance_no: Optional[str] = xml_field(
        'buildingEntranceNo', default=None, min_length=1, max_length=12
    )
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    local_id: ECH0129NamedId = xml_field('localID')
    is_official_address: Optional[bool] = xml_field(
        'isOfficialAddress', default=None
    )


# ---------------------------------------------------------------------------
# buildingAddressType (§4.7.2, XSD lines 1790-1822)
# ---------------------------------------------------------------------------

class ECH0129BuildingAddress(ECHModel):
    """eCH-0129 building address (full).

    XSD: buildingAddressType — xs:sequence of 15 elements.
    PDF: §4.7.2 (page 57-59, Abb. 14)

    9 required + 6 optional fields.

    Fields (in XSD order):
    - EGAID: EGAIDType (nonNegativeInteger, 100000000-900000000)
    - EGID: EGIDType (nonNegativeInteger, 1-900000000)
    - EDID: EDIDType (nonNegativeInteger, 0-90)
    - buildingName: nameOfBuildingType (xs:token 3-40), minOccurs="0"
    - buildingEntranceNo: buildingEntranceNoType (xs:token 1-12), minOccurs="0"
    - ESID: ESIDType (nonNegativeInteger, 10000000-90000000), minOccurs="0"
    - streetDescription: anonymous inline complexType (maxOccurs="4"
      sequence of language + descriptionLong), minOccurs="0"
    - swissZipCode: eCH-0010:swissZipCodeType (unsignedInt, 1000-9999)
    - swissZipCodeAddOn: eCH-0010:swissZipCodeAddOnType (string, maxLength=2)
    - locality: anonymous inline simpleType (xs:token 2-40)
    - municipalityId: eCH-0007:municipalityIdType (int, 1-9999)
    - municipalityName: eCH-0007:municipalityNameType (xs:token, maxLength=40)
    - coordinates: coordinatesType, minOccurs="0"
    - status: buildingStatusType enum
    - isOfficialAddress: xs:boolean, minOccurs="0"

    Note: element names are in eCH-0129 namespace; eCH-0010 and eCH-0007
    simpleTypes provide validation constraints only.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingAddress'

    egaid: int = xml_field('EGAID', ge=100000000, le=900000000)
    egid: int = xml_field('EGID', ge=1, le=900000000)
    edid: int = xml_field('EDID', ge=0, le=90)
    building_name: Optional[str] = xml_field(
        'buildingName', default=None, min_length=3, max_length=40
    )
    building_entrance_no: Optional[str] = xml_field(
        'buildingEntranceNo', default=None, min_length=1, max_length=12
    )
    esid: Optional[int] = xml_field(
        'ESID', default=None, ge=10000000, le=90000000
    )
    street_description: Optional[ECH0129AddressStreetDescription] = xml_field(
        'streetDescription', default=None
    )
    swiss_zip_code: int = xml_field('swissZipCode', ge=1000, le=9999)
    swiss_zip_code_add_on: str = xml_field('swissZipCodeAddOn', max_length=2)
    locality: str = xml_field('locality', min_length=2, max_length=40)
    municipality_id: int = xml_field('municipalityId', ge=1, le=9999)
    municipality_name: str = xml_field('municipalityName', max_length=40)
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    status: BuildingStatus = xml_field('status')
    is_official_address: Optional[bool] = xml_field(
        'isOfficialAddress', default=None
    )


# ---------------------------------------------------------------------------
# buildingAddressLightType (§4.7.2, XSD lines 1823-1853)
# ---------------------------------------------------------------------------

class ECH0129BuildingAddressLight(ECHModel):
    """eCH-0129 building address (light variant).

    XSD: buildingAddressLightType — xs:sequence with xs:choice.
    PDF: §4.7.2 (page 59-60, Abb. 15)

    xs:choice: either EGAID alone, or (EGID + EDID) together.
    3 required fields (after choice) + 3 optional.

    Fields (in XSD order):
    - xs:choice:
      - branch 1: EGAID: EGAIDType (nonNegativeInteger, 100000000-900000000)
      - branch 2: EGID: EGIDType (nonNegativeInteger, 1-900000000)
                 + EDID: EDIDType (nonNegativeInteger, 0-90)
    - buildingEntranceNo: buildingEntranceNoType (xs:token 1-12), minOccurs="0"
    - ESID: ESIDType (nonNegativeInteger, 10000000-90000000), minOccurs="0"
    - streetDescription: anonymous inline complexType (same as in
      buildingAddressType), minOccurs="0"
    - swissZipCode: eCH-0010:swissZipCodeType (unsignedInt, 1000-9999)
    - swissZipCodeAddOn: eCH-0010:swissZipCodeAddOnType (string, maxLength=2)
    - locality: anonymous inline simpleType (xs:token 2-40)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingAddressLight'

    # xs:choice branch 1
    egaid: Optional[int] = xml_field(
        'EGAID', default=None, ge=100000000, le=900000000
    )
    # xs:choice branch 2
    egid: Optional[int] = xml_field(
        'EGID', default=None, ge=1, le=900000000
    )
    edid: Optional[int] = xml_field('EDID', default=None, ge=0, le=90)

    building_entrance_no: Optional[str] = xml_field(
        'buildingEntranceNo', default=None, min_length=1, max_length=12
    )
    esid: Optional[int] = xml_field(
        'ESID', default=None, ge=10000000, le=90000000
    )
    street_description: Optional[ECH0129AddressStreetDescription] = xml_field(
        'streetDescription', default=None
    )
    swiss_zip_code: int = xml_field('swissZipCode', ge=1000, le=9999)
    swiss_zip_code_add_on: str = xml_field('swissZipCodeAddOn', max_length=2)
    locality: str = xml_field('locality', min_length=2, max_length=40)

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: EGAID alone OR (EGID + EDID) together."""
        has_egaid = self.egaid is not None
        has_egid = self.egid is not None
        has_edid = self.edid is not None

        if has_egaid and (has_egid or has_edid):
            raise ValueError(
                "buildingAddressLightType: EGAID and EGID/EDID are "
                "mutually exclusive (xs:choice)"
            )
        if has_egaid:
            return self
        if has_egid and has_edid:
            return self
        if has_egid and not has_edid:
            raise ValueError(
                "buildingAddressLightType: EGID requires EDID "
                "(xs:sequence in choice branch 2)"
            )
        if has_edid and not has_egid:
            raise ValueError(
                "buildingAddressLightType: EDID requires EGID "
                "(xs:sequence in choice branch 2)"
            )
        raise ValueError(
            "buildingAddressLightType: must set either EGAID or "
            "(EGID + EDID)"
        )
