"""eCH-0129 v6.0.0 — Estimation object types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 1633-1726)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.14, §4.24.5)
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import field_validator, model_validator
from typing_extensions import Self

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import TypeOfValue
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId


# ---------------------------------------------------------------------------
# valueType (§4.24.5 / §4.14.1.7.5)
# XSD lines 1633-1651
# ---------------------------------------------------------------------------

class ECH0129Value(ECHModel):
    """eCH-0129 value (Wert — CHF or percentage).

    XSD: valueType — xs:choice of 2 elements.
    PDF: §4.14.1.7.5 (page 80, "In CHF oder in %")

    Exactly one field must be set:
    - amount: xs:decimal, totalDigits=12, fractionDigits=2
    - percentage: xs:decimal, totalDigits=5, fractionDigits=2

    Note: structurally identical to insuranceSumType, but a separate XSD
    type used exclusively in estimationValueType.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'value'

    amount: Optional[str] = xml_field('amount', default=None)
    percentage: Optional[str] = xml_field('percentage', default=None)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:decimal, totalDigits=12, fractionDigits=2."""
        if v is None:
            return v
        try:
            Decimal(v)
        except InvalidOperation:
            raise ValueError(f"amount must be a valid decimal, got: '{v}'")
        return v

    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:decimal, totalDigits=5, fractionDigits=2."""
        if v is None:
            return v
        try:
            Decimal(v)
        except InvalidOperation:
            raise ValueError(f"percentage must be a valid decimal, got: '{v}'")
        return v

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one of amount or percentage."""
        count = sum(v is not None for v in [self.amount, self.percentage])
        if count == 0:
            raise ValueError(
                "valueType: must set one of amount or percentage"
            )
        if count > 1:
            raise ValueError(
                "valueType: only one of amount or percentage allowed"
            )
        return self


# ---------------------------------------------------------------------------
# estimationValueType (§4.14.1.7)
# XSD lines 1653-1676
# ---------------------------------------------------------------------------

class ECH0129EstimationValue(ECHModel):
    """eCH-0129 estimation value (Schaetzwert).

    XSD: estimationValueType — xs:sequence of 6 elements (3 required).
    PDF: §4.14.1.7 (page 79-81, Abb. 26)

    Fields (in XSD order):
    - localID: namedIdType (REQUIRED)
    - baseYear: xs:nonNegativeInteger, 1000–2999, minOccurs="0"
    - validFrom: validFromType (xs:date), minOccurs="0"
    - indexValue: xs:decimal, 0.00–999.99, minOccurs="0"
    - value: valueType (REQUIRED)
    - typeOfvalue: typeOfvalueType enum (REQUIRED)

    Note: XSD element name is 'typeOfvalue' with lowercase 'v' — not
    camelCase. This matches the XSD simpleType name 'typeOfvalueType'.

    indexValue stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'estimationValue'

    local_id: ECH0129NamedId = xml_field('localID')
    base_year: Optional[int] = xml_field(
        'baseYear', default=None, ge=1000, le=2999
    )
    valid_from: Optional[date] = xml_field('validFrom', default=None)
    index_value: Optional[str] = xml_field('indexValue', default=None)
    value: ECH0129Value = xml_field('value')
    type_of_value: TypeOfValue = xml_field('typeOfvalue')

    @field_validator('index_value')
    @classmethod
    def validate_index_value(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:decimal, 0.00–999.99."""
        if v is None:
            return v
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"indexValue must be a valid decimal, got: '{v}'")
        if d < Decimal('0.00') or d > Decimal('999.99'):
            raise ValueError(
                f"indexValue must be 0.00–999.99, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# estimationObjectType (§4.14)
# XSD lines 1701-1711
# ---------------------------------------------------------------------------

class ECH0129EstimationObject(ECHModel):
    """eCH-0129 estimation object (Schaetzobjekt).

    XSD: estimationObjectType — xs:sequence of 7 elements (1 required).
    PDF: §4.14 (page 77-78, Abb. 25)

    Fields (in XSD order):
    - localID: namedIdType (REQUIRED)
    - volume: estimationVolumeType (xs:nonNegativeInteger, 5–2000000), minOccurs="0"
    - yearOfConstruction: estimationYearOfConstructionType (xs:gYear, 1000–2099), minOccurs="0"
    - description: estimationDescriptionType (xs:token, 3–1000), minOccurs="0"
    - validFrom: xs:date, minOccurs="0"
    - estimationReason: estimationReasonTextType (xs:token, 1–30), minOccurs="0"
    - estimationValue: estimationValueType, minOccurs="0", maxOccurs="unbounded"

    yearOfConstruction stored as str to preserve xs:gYear format ("YYYY").
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'estimationObject'

    local_id: ECH0129NamedId = xml_field('localID')
    volume: Optional[int] = xml_field(
        'volume', default=None, ge=5, le=2000000
    )
    year_of_construction: Optional[str] = xml_field(
        'yearOfConstruction', default=None, pattern=r'^\d{4}$'
    )
    description: Optional[str] = xml_field(
        'description', default=None, min_length=3, max_length=1000
    )
    valid_from: Optional[date] = xml_field('validFrom', default=None)
    estimation_reason: Optional[str] = xml_field(
        'estimationReason', default=None, min_length=1, max_length=30
    )
    estimation_value: list[ECH0129EstimationValue] = xml_field(
        'estimationValue', default_factory=list, is_list=True
    )

    @field_validator('year_of_construction')
    @classmethod
    def validate_year_range(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:gYear, 1000–2099."""
        if v is None:
            return v
        year = int(v)
        if year < 1000 or year > 2099:
            raise ValueError(
                f"yearOfConstruction must be 1000–2099, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# estimationObjectOnlyType (§4.14, restriction)
# XSD lines 1712-1725
# ---------------------------------------------------------------------------

class ECH0129EstimationObjectOnly(ECHModel):
    """eCH-0129 estimation object (Only variant — no estimationValue).

    XSD: estimationObjectOnlyType — xs:restriction of estimationObjectType.
    PDF: §4.14 (restriction variant)

    Removes: estimationValue list
    Retains (in XSD order):
    - localID: namedIdType (REQUIRED)
    - volume: estimationVolumeType (xs:nonNegativeInteger, 5–2000000), minOccurs="0"
    - yearOfConstruction: estimationYearOfConstructionType (xs:gYear, 1000–2099), minOccurs="0"
    - description: estimationDescriptionType (xs:token, 3–1000), minOccurs="0"
    - validFrom: xs:date, minOccurs="0"
    - estimationReason: estimationReasonTextType (xs:token, 1–30), minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'estimationObject'

    local_id: ECH0129NamedId = xml_field('localID')
    volume: Optional[int] = xml_field(
        'volume', default=None, ge=5, le=2000000
    )
    year_of_construction: Optional[str] = xml_field(
        'yearOfConstruction', default=None, pattern=r'^\d{4}$'
    )
    description: Optional[str] = xml_field(
        'description', default=None, min_length=3, max_length=1000
    )
    valid_from: Optional[date] = xml_field('validFrom', default=None)
    estimation_reason: Optional[str] = xml_field(
        'estimationReason', default=None, min_length=1, max_length=30
    )

    @field_validator('year_of_construction')
    @classmethod
    def validate_year_range(cls, v: Optional[str]) -> Optional[str]:
        """XSD: xs:gYear, 1000–2099."""
        if v is None:
            return v
        year = int(v)
        if year < 1000 or year > 2099:
            raise ValueError(
                f"yearOfConstruction must be 1000–2099, got: {v}"
            )
        return v
