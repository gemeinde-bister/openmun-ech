"""eCH-0129 v6.0.0 — Insurance object types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 1308-1399)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.13)
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import field_validator, model_validator
from typing_extensions import Self

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import (
    BuildingVolumeNorm,
    ChangeReason,
    LocationCode,
    UsageCode,
)
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId


# ---------------------------------------------------------------------------
# insuranceSumType (§4.13.1.9.4)
# XSD lines 1308-1327
# ---------------------------------------------------------------------------

class ECH0129InsuranceSum(ECHModel):
    """eCH-0129 insurance sum (Versicherungssumme).

    XSD: insuranceSumType — xs:choice of 2 elements.
    PDF: §4.13.1.9.4 (page 76)

    Exactly one field must be set:
    - amount: xs:decimal, totalDigits=12, fractionDigits=2
    - percentage: xs:decimal, totalDigits=5, fractionDigits=2
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'insuranceSum'

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
                "insuranceSumType: must set one of amount or percentage"
            )
        if count > 1:
            raise ValueError(
                "insuranceSumType: only one of amount or percentage allowed"
            )
        return self


# ---------------------------------------------------------------------------
# insuranceValueType (§4.13.1.9)
# XSD lines 1349-1356
# ---------------------------------------------------------------------------

class ECH0129InsuranceValue(ECHModel):
    """eCH-0129 insurance value (Versicherungswert).

    XSD: insuranceValueType — xs:sequence of 4 required elements.
    PDF: §4.13.1.9 (page 75-76, Abb. 23)

    Fields (in XSD order, ALL required):
    - localID: namedIdType
    - validFrom: xs:date
    - changeReason: changeReasonType enum
    - insuranceSum: insuranceSumType
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'insuranceValue'

    local_id: ECH0129NamedId = xml_field('localID')
    valid_from: date = xml_field('validFrom')
    change_reason: ChangeReason = xml_field('changeReason')
    insurance_sum: ECH0129InsuranceSum = xml_field('insuranceSum')


# ---------------------------------------------------------------------------
# insuranceVolumeType (§4.13.1.10–11)
# XSD lines 1357-1369
# ---------------------------------------------------------------------------

class ECH0129InsuranceVolume(ECHModel):
    """eCH-0129 insurance volume (Versicherungsvolumen).

    XSD: insuranceVolumeType — xs:sequence of 2 required elements.
    PDF: §4.13.1.10 (page 76, Abb. 24)

    Fields (in XSD order, ALL required):
    - volume: xs:nonNegativeInteger, min=5, max=9999999
    - norm: buildingVolumeNormType enum

    Note: volume constraints match the anonymous inline simpleType in XSD,
    same range as used in insuranceVolumeType (not buildingVolumeType which
    uses nillable fields).
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'volume'

    volume: int = xml_field('volume', ge=5, le=9999999)
    norm: BuildingVolumeNorm = xml_field('norm')


# ---------------------------------------------------------------------------
# insuranceObjectType (§4.13)
# XSD lines 1370-1382
# ---------------------------------------------------------------------------

class ECH0129InsuranceObject(ECHModel):
    """eCH-0129 insurance object (Versicherungsobjekt).

    XSD: insuranceObjectType — xs:sequence of 9 elements.
    PDF: §4.13 (page 72-76, Abb. 22)

    Fields (in XSD order):
    - localID: namedIdType (REQUIRED)
    - startDate: xs:date, minOccurs="0"
    - endDate: xs:date, minOccurs="0"
    - insuranceNumber: buildingInsuranceNumberType (xs:token) (REQUIRED)
    - usageCode: usageCodeType enum, minOccurs="0"
    - usageDescription: usageDescriptionType (xs:token), minOccurs="0"
    - locationCode: locationCodeType enum, minOccurs="0"
    - insuranceValue: insuranceValueType, minOccurs="0"
    - volume: insuranceVolumeType, minOccurs="0"

    Note: PDF §4.13.1.7 describes usageDescription as xs:nonNegativeInteger,
    but XSD line 1305-1307 defines usageDescriptionType as xs:token with no
    constraints. XSD is authoritative — implemented as str.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'insuranceObject'

    local_id: ECH0129NamedId = xml_field('localID')
    start_date: Optional[date] = xml_field('startDate', default=None)
    end_date: Optional[date] = xml_field('endDate', default=None)
    insurance_number: str = xml_field('insuranceNumber')
    usage_code: Optional[UsageCode] = xml_field('usageCode', default=None)
    usage_description: Optional[str] = xml_field(
        'usageDescription', default=None
    )
    location_code: Optional[LocationCode] = xml_field(
        'locationCode', default=None
    )
    insurance_value: Optional[ECH0129InsuranceValue] = xml_field(
        'insuranceValue', default=None
    )
    volume: Optional[ECH0129InsuranceVolume] = xml_field(
        'volume', default=None
    )


# ---------------------------------------------------------------------------
# insuranceObjectOnlyType (§4.13, restriction)
# XSD lines 1383-1398
# ---------------------------------------------------------------------------

class ECH0129InsuranceObjectOnly(ECHModel):
    """eCH-0129 insurance object (Only variant — no insuranceValue).

    XSD: insuranceObjectOnlyType — xs:restriction of insuranceObjectType.
    PDF: §4.13 (restriction variant)

    Removes: insuranceValue
    Retains (in XSD order):
    - localID: namedIdType (REQUIRED)
    - startDate: xs:date, minOccurs="0"
    - endDate: xs:date, minOccurs="0"
    - insuranceNumber: buildingInsuranceNumberType (xs:token) (REQUIRED)
    - usageCode: usageCodeType enum, minOccurs="0"
    - usageDescription: usageDescriptionType (xs:token), minOccurs="0"
    - locationCode: locationCodeType enum, minOccurs="0"
    - volume: insuranceVolumeType, minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'insuranceObject'

    local_id: ECH0129NamedId = xml_field('localID')
    start_date: Optional[date] = xml_field('startDate', default=None)
    end_date: Optional[date] = xml_field('endDate', default=None)
    insurance_number: str = xml_field('insuranceNumber')
    usage_code: Optional[UsageCode] = xml_field('usageCode', default=None)
    usage_description: Optional[str] = xml_field(
        'usageDescription', default=None
    )
    location_code: Optional[LocationCode] = xml_field(
        'locationCode', default=None
    )
    volume: Optional[ECH0129InsuranceVolume] = xml_field(
        'volume', default=None
    )
