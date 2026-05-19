"""eCH-0129 v6.0.0 — Real estate, area, and fiscal ownership types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 1034-1285)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.8, §4.9, §4.12)
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import (
    AreaDescriptionCode,
    AreaType,
    FiscalRelationship,
    RealestateStatus,
    RealestateType,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129Coordinates,
    ECH0129NamedMetaData,
)


# ---------------------------------------------------------------------------
# realestateIdentificationType (§4.8.1)
# XSD lines 1034-1074
# ---------------------------------------------------------------------------

class ECH0129RealestateIdentification(ECHModel):
    """eCH-0129 realestate identification.

    XSD: realestateIdentificationType — xs:sequence of 5 elements.
    PDF: §4.8.1 (page 60-61, Abb. 16)

    Fields (in XSD order):
    - EGRID: EGRIDType (xs:token, maxLength=14), minOccurs="0"
    - number: xs:token, minLength=1, maxLength=12 (REQUIRED)
    - numberSuffix: xs:token, minLength=1, maxLength=12, minOccurs="0"
    - subDistrict: xs:token, minLength=1, maxLength=15, minOccurs="0"
    - lot: xs:token, minLength=1, maxLength=15, minOccurs="0"

    Note: XSD makes `number` required (no minOccurs="0"), even though
    PDF §4.8.1.10 says it's mandatory only "falls EGRID nicht geliefert wird".
    We follow XSD — `number` is always required.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'realestateIdentification'

    egrid: Optional[str] = xml_field('EGRID', default=None, max_length=14)
    number: str = xml_field('number', min_length=1, max_length=12)
    number_suffix: Optional[str] = xml_field(
        'numberSuffix', default=None, min_length=1, max_length=12
    )
    sub_district: Optional[str] = xml_field(
        'subDistrict', default=None, min_length=1, max_length=15
    )
    lot: Optional[str] = xml_field(
        'lot', default=None, min_length=1, max_length=15
    )


# ---------------------------------------------------------------------------
# realestateType (§4.8)
# XSD lines 1132-1147
# ---------------------------------------------------------------------------

class ECH0129Realestate(ECHModel):
    """eCH-0129 realestate (Grundstueck).

    XSD: realestateType — xs:sequence of 12 elements.
    PDF: §4.8 (page 60-65, Abb. 17)

    Fields (in XSD order):
    - realestateIdentification: realestateIdentificationType (REQUIRED)
    - authority: authorityType (xs:token, minLength=1, maxLength=12), minOccurs="0"
    - date: realestateDateType (xs:date), minOccurs="0"
    - realestateType: realestateTypeType enum (REQUIRED)
    - cantonalSubKind: cantonalSubKindType (xs:token, minLength=1, maxLength=60), minOccurs="0"
    - status: realestateStatusType enum, minOccurs="0"
    - mutnumber: realestateMutnumberType (xs:token, minLength=1, maxLength=12), minOccurs="0"
    - identDN: identDNType (xs:token, minLength=1, maxLength=12), minOccurs="0"
    - squareMeasure: squareMeasureType (xs:decimal, 0.0–1000000000.0), minOccurs="0"
    - realestateIncomplete: realestateIncompleteType (xs:boolean), minOccurs="0"
    - coordinates: coordinatesType, minOccurs="0"
    - namedMetaData: namedMetaDataType, minOccurs="0", maxOccurs="unbounded"

    squareMeasure stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'realestate'

    realestate_identification: ECH0129RealestateIdentification = xml_field(
        'realestateIdentification'
    )
    authority: Optional[str] = xml_field(
        'authority', default=None, min_length=1, max_length=12
    )
    date_val: Optional[date] = xml_field('date', default=None)
    realestate_type: RealestateType = xml_field('realestateType')
    cantonal_sub_kind: Optional[str] = xml_field(
        'cantonalSubKind', default=None, min_length=1, max_length=60
    )
    status: Optional[RealestateStatus] = xml_field('status', default=None)
    mutnumber: Optional[str] = xml_field(
        'mutnumber', default=None, min_length=1, max_length=12
    )
    ident_dn: Optional[str] = xml_field(
        'identDN', default=None, min_length=1, max_length=12
    )
    square_measure: Optional[str] = xml_field('squareMeasure', default=None)
    realestate_incomplete: Optional[bool] = xml_field(
        'realestateIncomplete', default=None
    )
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    named_meta_data: list[ECH0129NamedMetaData] = xml_field(
        'namedMetaData', default_factory=list, is_list=True
    )

    @field_validator('square_measure')
    @classmethod
    def validate_square_measure(cls, v: Optional[str]) -> Optional[str]:
        """XSD: squareMeasureType — xs:decimal, 0.0–1000000000.0."""
        if v is None:
            return v
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"squareMeasure must be a valid decimal, got: '{v}'")
        if d < Decimal('0.0') or d > Decimal('1000000000.0'):
            raise ValueError(
                f"squareMeasure must be 0.0–1000000000.0, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# fiscalOwnershipType (§4.12)
# XSD lines 1189-1224
# ---------------------------------------------------------------------------

class ECH0129FiscalOwnership(ECHModel):
    """eCH-0129 fiscal ownership (Steuerrechtliches Eigentum).

    XSD: fiscalOwnershipType — xs:sequence of 6 elements.
    PDF: §4.12 (page 70-71, Abb. 21)

    Fields (in XSD order):
    - accessionDate: xs:date (REQUIRED) — Nutzen-/Schadendatum
    - fiscalRelationship: anonymous inline enum 1-3 (REQUIRED)
    - validFrom: xs:date, minOccurs="0"
    - validTill: xs:date, minOccurs="0"
    - denominator: xs:decimal (totalDigits=10, fractionDigits=3,
      0.001–1000000.000), minOccurs="0"
    - numerator: xs:decimal (totalDigits=10, fractionDigits=3,
      0.001–1000000.000), minOccurs="0"

    denominator/numerator stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'fiscalOwnership'

    accession_date: date = xml_field('accessionDate')
    fiscal_relationship: FiscalRelationship = xml_field('fiscalRelationship')
    valid_from: Optional[date] = xml_field('validFrom', default=None)
    valid_till: Optional[date] = xml_field('validTill', default=None)
    denominator: Optional[str] = xml_field('denominator', default=None)
    numerator: Optional[str] = xml_field('numerator', default=None)

    @field_validator('denominator', 'numerator')
    @classmethod
    def validate_fraction(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:decimal, totalDigits=10, fractionDigits=3, 0.001–1000000.000."""
        if v is None:
            return v
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"Must be a valid decimal, got: '{v}'")
        if d < Decimal('0.001') or d > Decimal('1000000.000'):
            raise ValueError(
                f"Must be 0.001–1000000.000, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# areaType (§4.9)
# XSD lines 1277-1284
# ---------------------------------------------------------------------------

class ECH0129Area(ECHModel):
    """eCH-0129 area (Flaeche).

    XSD: areaType — xs:sequence of 4 required elements.
    PDF: §4.9 (page 65-67, Abb. 18)

    Fields (in XSD order, ALL required):
    - areaType: areaTypeType enum
    - areaDescriptionCode: areaDescriptionCodeType enum
    - areaDescription: areaDescriptionType (xs:token, minLength=1, maxLength=100)
    - areaValue: areaValueType (xs:decimal, 0.0–1000000000.0)

    areaValue stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'area'

    area_type: AreaType = xml_field('areaType')
    area_description_code: AreaDescriptionCode = xml_field('areaDescriptionCode')
    area_description: str = xml_field(
        'areaDescription', min_length=1, max_length=100
    )
    area_value: str = xml_field('areaValue')

    @field_validator('area_value')
    @classmethod
    def validate_area_value(cls, v: str) -> str:
        """XSD: areaValueType — xs:decimal, 0.0–1000000000.0."""
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"areaValue must be a valid decimal, got: '{v}'")
        if d < Decimal('0.0') or d > Decimal('1000000000.0'):
            raise ValueError(
                f"areaValue must be 0.0–1000000000.0, got: {v}"
            )
        return v
