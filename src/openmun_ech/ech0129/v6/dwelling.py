"""eCH-0129 v6.0.0 — Dwelling types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 957-963, 965-1000, 1002-1021)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.6, pages 48-55)

Types in this module depend on:
- eCH-0129 base_types (ECH0129NamedId, ECH0129DatePartiallyKnown)
- eCH-0129 enums (DwellingStatus, DwellingUsageCode, DwellingInformationSource,
  UsageLimitation)
"""

from datetime import date
from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import (
    DwellingInformationSource,
    DwellingStatus,
    DwellingUsageCode,
    UsageLimitation,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129DatePartiallyKnown,
    ECH0129NamedId,
)


# ---------------------------------------------------------------------------
# dwellingIdentificationType (§4.6.1, XSD lines 957-963)
# ---------------------------------------------------------------------------

class ECH0129DwellingIdentification(ECHModel):
    """eCH-0129 dwelling identification.

    XSD: dwellingIdentificationType — xs:sequence, all 4 fields required.
    PDF: §4.6 (page 48) — identifiers EGID+EWID (eidg. GWR).

    Fields (in XSD order):
    - EGID: EGIDType (nonNegativeInteger, 1–900000000)
    - EDID: EDIDType (nonNegativeInteger, 0–90)
    - EWID: EWIDType (nonNegativeInteger, 1–900)
    - localID: namedIdType
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'dwellingIdentification'

    egid: int = xml_field('EGID', ge=1, le=900000000)
    edid: int = xml_field('EDID', ge=0, le=90)
    ewid: int = xml_field('EWID', ge=1, le=900)
    local_id: ECH0129NamedId = xml_field('localID')


# ---------------------------------------------------------------------------
# dwellingUsageType (§4.6.1.15, XSD lines 965-1000)
# ---------------------------------------------------------------------------

_MIN_USAGE_DATE = date(2012, 12, 31)


class ECH0129DwellingUsage(ECHModel):
    """eCH-0129 dwelling usage information.

    XSD: dwellingUsageType — xs:sequence, all fields optional.
    PDF: §4.6.1.15 Wohnungsnutzung (pages 53-55, Abb. 12)

    Fields (in XSD order):
    - usageCode: dwellingUsageCodeType enum, minOccurs="0"
    - informationSource: dwellingInformationSourceType enum, minOccurs="0"
    - revisionDate: xs:date (minInclusive 2012-12-31), minOccurs="0"
    - remark: xs:token 1–2000, minOccurs="0"
    - personWithMainResidence: xs:boolean, minOccurs="0"
    - personWithSecondaryResidence: xs:boolean, minOccurs="0"
    - dateFirstOccupancy: xs:date (minInclusive 2012-12-31), minOccurs="0"
    - dateLastOccupancy: xs:date (minInclusive 2012-12-31), minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'dwellingUsage'

    usage_code: Optional[DwellingUsageCode] = xml_field(
        'usageCode', default=None
    )
    information_source: Optional[DwellingInformationSource] = xml_field(
        'informationSource', default=None
    )
    revision_date: Optional[date] = xml_field('revisionDate', default=None)
    remark: Optional[str] = xml_field(
        'remark', default=None, min_length=1, max_length=2000
    )
    person_with_main_residence: Optional[bool] = xml_field(
        'personWithMainResidence', default=None
    )
    person_with_secondary_residence: Optional[bool] = xml_field(
        'personWithSecondaryResidence', default=None
    )
    date_first_occupancy: Optional[date] = xml_field(
        'dateFirstOccupancy', default=None
    )
    date_last_occupancy: Optional[date] = xml_field(
        'dateLastOccupancy', default=None
    )

    @field_validator(
        'revision_date', 'date_first_occupancy', 'date_last_occupancy',
    )
    @classmethod
    def validate_usage_date(cls, v: Optional[date]) -> Optional[date]:
        """XSD: all date fields have minInclusive=2012-12-31."""
        if v is not None and v < _MIN_USAGE_DATE:
            raise ValueError(
                f"dwellingUsageType date must be >= 2012-12-31, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# dwellingType (§4.6, XSD lines 1002-1021)
# ---------------------------------------------------------------------------

class ECH0129Dwelling(ECHModel):
    """eCH-0129 dwelling entity.

    XSD: dwellingType — xs:sequence of 16 elements.
    PDF: §4.6 Wohnung (pages 48-55, Abb. 11)

    1 required field (localID list), 15 optional.

    Fields (in XSD order):
    - localID: namedIdType, maxOccurs="unbounded" (REQUIRED, min 1)
    - administrativeDwellingNo: administrativeDwellingNoType
      (xs:token 1–12), minOccurs="0"
    - EWID: EWIDType (nonNegativeInteger, 1–900), minOccurs="0"
    - physicalDwellingNo: physicalDwellingNoType
      (xs:token 1–12), minOccurs="0"
    - dateOfConstruction: datePartiallyKnownType, minOccurs="0"
    - dateOfDemolition: datePartiallyKnownType, minOccurs="0"
    - noOfHabitableRooms: noOfHabitableRoomsType
      (nonNegativeInteger, 1–99), minOccurs="0"
    - floor: floorType (nonNegativeInteger, 3100–3419), minOccurs="0"
    - locationOfDwellingOnFloor: locationOfDwellingOnFloorType
      (xs:token 3–40), minOccurs="0"
    - multipleFloor: multipleFloorType (xs:boolean), minOccurs="0"
    - usageLimitation: usageLimitationType enum, minOccurs="0"
    - kitchen: kitchenType (xs:boolean), minOccurs="0"
    - surfaceAreaOfDwelling: surfaceAreaOfDwellingType
      (nonNegativeInteger, 1–9999), minOccurs="0"
    - status: dwellingStatusType enum, minOccurs="0"
    - dwellingUsage: dwellingUsageType, minOccurs="0"
    - dwellingFreeText: freeTextType (xs:token 1–32),
      minOccurs="0", maxOccurs="2"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'dwelling'

    local_id: list[ECH0129NamedId] = xml_field(
        'localID', is_list=True, min_length=1
    )
    administrative_dwelling_no: Optional[str] = xml_field(
        'administrativeDwellingNo', default=None,
        min_length=1, max_length=12
    )
    ewid: Optional[int] = xml_field('EWID', default=None, ge=1, le=900)
    physical_dwelling_no: Optional[str] = xml_field(
        'physicalDwellingNo', default=None,
        min_length=1, max_length=12
    )
    date_of_construction: Optional[ECH0129DatePartiallyKnown] = xml_field(
        'dateOfConstruction', default=None
    )
    date_of_demolition: Optional[ECH0129DatePartiallyKnown] = xml_field(
        'dateOfDemolition', default=None
    )
    no_of_habitable_rooms: Optional[int] = xml_field(
        'noOfHabitableRooms', default=None, ge=1, le=99
    )
    floor: Optional[int] = xml_field(
        'floor', default=None, ge=3100, le=3419
    )
    location_of_dwelling_on_floor: Optional[str] = xml_field(
        'locationOfDwellingOnFloor', default=None,
        min_length=3, max_length=40
    )
    multiple_floor: Optional[bool] = xml_field(
        'multipleFloor', default=None
    )
    usage_limitation: Optional[UsageLimitation] = xml_field(
        'usageLimitation', default=None
    )
    kitchen: Optional[bool] = xml_field('kitchen', default=None)
    surface_area_of_dwelling: Optional[int] = xml_field(
        'surfaceAreaOfDwelling', default=None, ge=1, le=9999
    )
    status: Optional[DwellingStatus] = xml_field('status', default=None)
    dwelling_usage: Optional[ECH0129DwellingUsage] = xml_field(
        'dwellingUsage', default=None
    )
    dwelling_free_text: list[str] = xml_field(
        'dwellingFreeText', default_factory=list, is_list=True
    )

    @field_validator('dwelling_free_text')
    @classmethod
    def validate_free_text_list(cls, v: list[str]) -> list[str]:
        """XSD: dwellingFreeText maxOccurs="2", freeTextType 1–32 chars."""
        if len(v) > 2:
            raise ValueError(
                f"dwellingFreeText maxOccurs=2, got {len(v)} entries"
            )
        for i, text in enumerate(v):
            if len(text) < 1 or len(text) > 32:
                raise ValueError(
                    f"dwellingFreeText[{i}] must be 1-32 chars, "
                    f"got {len(text)} chars"
                )
        return v
