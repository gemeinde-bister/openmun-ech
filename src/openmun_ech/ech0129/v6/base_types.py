"""eCH-0129 v6.0.0 — Foundation complex types (Level 0-1).

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf

Types in this module have no cross-dependencies within eCH-0129 —
they only reference external standards (eCH-0044, eCH-0097) or enums.
"""

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0044 import ECH0044PersonIdentificationLight
from openmun_ech.ech0097 import ECH0097OrganisationIdentification
from openmun_ech.ech0129.enums import (
    BuildingVolumeInformationSource,
    BuildingVolumeNorm,
    EnergySource,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    InformationSource,
    OriginOfCoordinates,
    PeriodOfConstruction,
)

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


# ---------------------------------------------------------------------------
# dateRangeType (§4.23.1.3.3 / Abb. 39)
# XSD lines 89-94
# ---------------------------------------------------------------------------

class ECH0129DateRange(ECHModel):
    """eCH-0129 date range (validity period).

    XSD: dateRangeType — xs:sequence of 2 optional dates.
    PDF: §4.23.1.3.3 (page 95, Abb. 39)

    Both fields are optional per XSD (minOccurs="0").
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'validity'

    date_from: Optional[date] = xml_field('dateFrom', default=None)
    date_to: Optional[date] = xml_field('dateTo', default=None)


# ---------------------------------------------------------------------------
# namedMetaDataType (§4.5.1.26)
# XSD lines 95-113
# ---------------------------------------------------------------------------

class ECH0129NamedMetaData(ECHModel):
    """eCH-0129 named metadata key-value pair.

    XSD: namedMetaDataType — xs:sequence of 2 required strings.
    PDF: §4.5.1.26 (page 47)

    Both fields are required (no minOccurs="0").
    - metaDataName: xs:token, minLength=1, maxLength=20
    - metaDataValue: xs:token, minLength=1 (no maxLength in XSD)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'namedMetaData'

    meta_data_name: str = xml_field('metaDataName', min_length=1, max_length=20)
    meta_data_value: str = xml_field('metaDataValue', min_length=1)


# ---------------------------------------------------------------------------
# namedIdType (§4.24.1)
# XSD lines 126-138
# ---------------------------------------------------------------------------

class ECH0129NamedId(ECHModel):
    """eCH-0129 named identifier (category + value).

    XSD: namedIdType — xs:sequence of 2 required strings.
    PDF: §4.24.1 (page 97-98)

    Both fields are required (no minOccurs="0").
    - IdCategory: iDCategoryType (xs:token, minLength=1, maxLength=20)
    - Id: xs:token, minLength=1, maxLength=50

    Note: XSD uses capital 'I' for both element names ('IdCategory', 'Id').
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'namedId'

    id_category: str = xml_field('IdCategory', min_length=1, max_length=20)
    id_value: str = xml_field('Id', min_length=1, max_length=50)


# ---------------------------------------------------------------------------
# coordinatesType (§4.24.4)
# XSD lines 178-184
# ---------------------------------------------------------------------------

class ECH0129Coordinates(ECHModel):
    """eCH-0129 Swiss LV95 coordinates.

    XSD: coordinatesType — xs:sequence.
    PDF: §4.24.4 (page 100-101)

    - east: coordinatesEastType — xs:decimal, totalDigits=10, fractionDigits=3,
      min=2480000.000, max=2840000.999
    - north: coordinatesNorthType — xs:decimal, totalDigits=10, fractionDigits=3,
      min=1070000.000, max=1300000.999
    - originOfCoordinates: originOfCoordinatesType enum, minOccurs="0"

    Stored as str for lossless XML round-trip (xs:decimal validated via
    Python Decimal, serialized as str).
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'coordinates'

    east: str = xml_field('east')
    north: str = xml_field('north')
    origin_of_coordinates: Optional[OriginOfCoordinates] = xml_field(
        'originOfCoordinates', default=None
    )

    @field_validator('east')
    @classmethod
    def validate_east(cls, v: str) -> str:
        """XSD: coordinatesEastType — decimal 2480000.000–2840000.999."""
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"east must be a valid decimal, got: '{v}'")
        if d < Decimal('2480000.000') or d > Decimal('2840000.999'):
            raise ValueError(
                f"east must be 2480000.000–2840000.999 (LV95), got: {v}"
            )
        return v

    @field_validator('north')
    @classmethod
    def validate_north(cls, v: str) -> str:
        """XSD: coordinatesNorthType — decimal 1070000.000–1300000.999."""
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"north must be a valid decimal, got: '{v}'")
        if d < Decimal('1070000.000') or d > Decimal('1300000.999'):
            raise ValueError(
                f"north must be 1070000.000–1300000.999 (LV95), got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# datePartiallyKnownType (§4.24.2)
# XSD lines 139-145
# ---------------------------------------------------------------------------

class ECH0129DatePartiallyKnown(ECHModel):
    """eCH-0129 partially known date.

    XSD: datePartiallyKnownType — xs:choice of 3 branches.
    PDF: §4.24.2 (page 98)

    Exactly one field must be set:
    - yearMonthDay: xs:date
    - yearMonth: xs:gYearMonth
    - year: xs:gYear

    This is the eCH-0129 version, separate from eCH-0044
    datePartiallyKnownType. Same structure, different namespace.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'datePartiallyKnown'

    year_month_day: Optional[date] = xml_field('yearMonthDay', default=None)
    year_month: Optional[str] = xml_field(
        'yearMonth', default=None, pattern=r'^\d{4}-\d{2}$'
    )
    year: Optional[str] = xml_field(
        'year', default=None, pattern=r'^\d{4}$'
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one branch must be set."""
        count = sum(v is not None for v in [
            self.year_month_day, self.year_month, self.year
        ])
        if count == 0:
            raise ValueError(
                "datePartiallyKnownType: must set one of "
                "year_month_day, year_month, or year"
            )
        if count > 1:
            raise ValueError(
                "datePartiallyKnownType: only one of "
                "year_month_day, year_month, or year allowed"
            )
        return self


# ---------------------------------------------------------------------------
# buildingDateType (§4.24.3)
# XSD lines 493-521
# ---------------------------------------------------------------------------

class ECH0129BuildingDate(ECHModel):
    """eCH-0129 building date (extends datePartiallyKnown with period).

    XSD: buildingDateType — xs:choice of 4 branches.
    PDF: §4.24.3 (page 99-100)

    Exactly one field must be set:
    - yearMonthDay: xs:date (min=1000-01-01, max=2099-12-31)
    - yearMonth: xs:gYearMonth (min=1000-01, max=2099-12)
    - year: xs:gYear (min=1000, max=2099)
    - periodOfConstruction: periodOfConstructionType enum
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingDate'

    year_month_day: Optional[date] = xml_field('yearMonthDay', default=None)
    year_month: Optional[str] = xml_field(
        'yearMonth', default=None, pattern=r'^\d{4}-\d{2}$'
    )
    year: Optional[str] = xml_field(
        'year', default=None, pattern=r'^\d{4}$'
    )
    period_of_construction: Optional[PeriodOfConstruction] = xml_field(
        'periodOfConstruction', default=None
    )

    @field_validator('year_month_day')
    @classmethod
    def validate_year_month_day(cls, v: Optional[date]) -> Optional[date]:
        """XSD: min=1000-01-01, max=2099-12-31."""
        if v is not None:
            if v.year < 1000 or v > date(2099, 12, 31):
                raise ValueError(
                    f"yearMonthDay must be 1000-01-01..2099-12-31, got: {v}"
                )
        return v

    @field_validator('year_month')
    @classmethod
    def validate_year_month_range(cls, v: Optional[str]) -> Optional[str]:
        """XSD: min=1000-01, max=2099-12."""
        if v is not None:
            year = int(v[:4])
            if year < 1000 or year > 2099:
                raise ValueError(f"yearMonth year must be 1000–2099, got: {v}")
        return v

    @field_validator('year')
    @classmethod
    def validate_year_range(cls, v: Optional[str]) -> Optional[str]:
        """XSD: min=1000, max=2099."""
        if v is not None:
            year_int = int(v)
            if year_int < 1000 or year_int > 2099:
                raise ValueError(f"year must be 1000–2099, got: {v}")
        return v

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one branch must be set."""
        count = sum(v is not None for v in [
            self.year_month_day, self.year_month,
            self.year, self.period_of_construction
        ])
        if count == 0:
            raise ValueError(
                "buildingDateType: must set one of year_month_day, "
                "year_month, year, or period_of_construction"
            )
        if count > 1:
            raise ValueError(
                "buildingDateType: only one of year_month_day, "
                "year_month, year, or period_of_construction allowed"
            )
        return self


# ---------------------------------------------------------------------------
# buildingVolumeType (§4.5.1.23)
# XSD lines 633-646 — nillable="true" on all 3 fields
# ---------------------------------------------------------------------------

def _emit_nillable(
    parent: ET.Element, ns: str, xml_name: str,
    value: object, is_nil: bool, value_type: str,
) -> None:
    """Emit an element that may carry xsi:nil="true"."""
    if is_nil:
        sub = ET.SubElement(parent, f'{{{ns}}}{xml_name}')
        sub.set(f'{{{XSI_NS}}}nil', 'true')
    elif value is not None:
        sub = ET.SubElement(parent, f'{{{ns}}}{xml_name}')
        if value_type == 'enum':
            sub.text = str(value.value)
        else:
            sub.text = str(value)


class ECH0129BuildingVolume(ECHModel):
    """eCH-0129 building volume with nillable fields.

    XSD: buildingVolumeType — xs:sequence, 3 optional nillable elements.
    PDF: §4.5.1.23 (page 43)

    All 3 elements have nillable="true" + minOccurs="0", meaning each can be:
    - Absent (element omitted): field is None, *_nil is False
    - Explicitly null (xsi:nil="true"): field is None, *_nil is True
    - Present with value: field has value, *_nil is False

    Fields:
    - volume: nonNegativeInteger, min=1, max=9999999 (cubic meters)
    - informationSource: buildingVolumeInformationSourceType enum
    - norm: buildingVolumeNormType enum

    Custom to_xml()/from_xml() handles xsi:nil serialization.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingVolume'

    volume: Optional[int] = xml_field('volume', default=None, ge=1, le=9999999)
    information_source: Optional[BuildingVolumeInformationSource] = xml_field(
        'informationSource', default=None
    )
    norm: Optional[BuildingVolumeNorm] = xml_field('norm', default=None)

    # Nillable control flags — not xml_fields, used by custom to_xml/from_xml.
    # Default False = element is absent when value is None.
    volume_nil: bool = False
    information_source_nil: bool = False
    norm_nil: bool = False

    @model_validator(mode='after')
    def validate_nil_consistency(self) -> Self:
        """A field cannot have both a value and be nil."""
        if self.volume is not None and self.volume_nil:
            raise ValueError(
                "volume cannot have a value and be nil simultaneously"
            )
        if self.information_source is not None and self.information_source_nil:
            raise ValueError(
                "information_source cannot have a value and be nil simultaneously"
            )
        if self.norm is not None and self.norm_nil:
            raise ValueError(
                "norm cannot have a value and be nil simultaneously"
            )
        return self

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

        _emit_nillable(elem, ns, 'volume', self.volume, self.volume_nil, 'int')
        _emit_nillable(
            elem, ns, 'informationSource',
            self.information_source, self.information_source_nil, 'enum',
        )
        _emit_nillable(elem, ns, 'norm', self.norm, self.norm_nil, 'enum')

        return elem

    @classmethod
    def from_xml(
        cls, elem: ET.Element, namespace: str | None = None,
    ) -> 'ECH0129BuildingVolume':
        ns = namespace or cls.__xml_ns__
        kwargs: dict = {}

        vol_elem = elem.find(f'{{{ns}}}volume')
        if vol_elem is not None:
            if vol_elem.get(f'{{{XSI_NS}}}nil') == 'true':
                kwargs['volume_nil'] = True
            elif vol_elem.text:
                kwargs['volume'] = int(vol_elem.text.strip())

        src_elem = elem.find(f'{{{ns}}}informationSource')
        if src_elem is not None:
            if src_elem.get(f'{{{XSI_NS}}}nil') == 'true':
                kwargs['information_source_nil'] = True
            elif src_elem.text:
                kwargs['information_source'] = BuildingVolumeInformationSource(
                    src_elem.text.strip()
                )

        norm_elem = elem.find(f'{{{ns}}}norm')
        if norm_elem is not None:
            if norm_elem.get(f'{{{XSI_NS}}}nil') == 'true':
                kwargs['norm_nil'] = True
            elif norm_elem.text:
                kwargs['norm'] = BuildingVolumeNorm(norm_elem.text.strip())

        return cls(**kwargs)


# ---------------------------------------------------------------------------
# heatingType (§4.5.1.24)
# XSD lines 733-740
# ---------------------------------------------------------------------------

class ECH0129Heating(ECHModel):
    """eCH-0129 heating installation data.

    XSD: heatingType — xs:sequence, 4 optional elements.
    PDF: §4.5.1.24 (page 44-46)

    Max 2 instances per building (PDF: "Es koennen maximal 2 solche
    Angaben uebergeben werden.").

    - heatGeneratorHeating: heatGeneratorHeatingType enum
    - energySourceHeating: energySourceType enum
    - informationSourceHeating: informationSourceType enum
    - revisionDate: xs:date (min=2000-12-31, PDF §4.5.1.24.4)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'heating'

    heat_generator_heating: Optional[HeatGeneratorHeating] = xml_field(
        'heatGeneratorHeating', default=None
    )
    energy_source_heating: Optional[EnergySource] = xml_field(
        'energySourceHeating', default=None
    )
    information_source_heating: Optional[InformationSource] = xml_field(
        'informationSourceHeating', default=None
    )
    revision_date: Optional[date] = xml_field('revisionDate', default=None)


# ---------------------------------------------------------------------------
# hotWaterType (§4.5.1.25)
# XSD lines 741-748
# ---------------------------------------------------------------------------

class ECH0129HotWater(ECHModel):
    """eCH-0129 hot water installation data.

    XSD: hotWaterType — xs:sequence, 4 optional elements.
    PDF: §4.5.1.25 (page 46-47)

    Max 2 instances per building (PDF: "Es koennen maximal 2 solche
    Angaben uebergeben werden.").

    Note: XSD reuses 'energySourceHeating' and 'informationSourceHeating'
    element names (same as heatingType), despite being for hot water.

    - heatGeneratorHotWater: heatGeneratorHotWaterType enum
    - energySourceHeating: energySourceType enum
    - informationSourceHeating: informationSourceType enum
    - revisionDate: xs:date
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'hotWater'

    heat_generator_hot_water: Optional[HeatGeneratorHotWater] = xml_field(
        'heatGeneratorHotWater', default=None
    )
    energy_source_heating: Optional[EnergySource] = xml_field(
        'energySourceHeating', default=None
    )
    information_source_heating: Optional[InformationSource] = xml_field(
        'informationSourceHeating', default=None
    )
    revision_date: Optional[date] = xml_field('revisionDate', default=None)


# ---------------------------------------------------------------------------
# contactType (§4.22.1.5)
# XSD lines 1755-1761
# ---------------------------------------------------------------------------

class ECH0129Contact(ECHModel):
    """eCH-0129 simple contact information.

    XSD: contactType — xs:sequence, 3 optional string elements.
    PDF: §4.22.1.5 (referenced from buildingAuthorityType)

    Simple flat contact — different from the richer phoneType/emailType
    which have categories and validity periods.

    - emailAddress: emailAddressType (xs:string, max=100, email regex)
    - phoneNumber: phoneNumberType (xs:string, max=20, pattern \\d{10,20})
    - faxNumber: phoneNumberType (same constraints as phoneNumber)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'contact'

    email_address: Optional[str] = xml_field(
        'emailAddress', default=None, max_length=100
    )
    phone_number: Optional[str] = xml_field(
        'phoneNumber', default=None, max_length=20
    )
    fax_number: Optional[str] = xml_field(
        'faxNumber', default=None, max_length=20
    )


# ---------------------------------------------------------------------------
# personIdentificationType (§4.23.1.1)
# XSD lines 120-125
# ---------------------------------------------------------------------------

class ECH0129PersonIdentification(ECHModel):
    """eCH-0129 person/organisation identification (choice).

    XSD: personIdentificationType — xs:choice.
    PDF: §4.23.1.1 (page 94)

    Exactly one must be set:
    - individual: eCH-0044:personIdentificationLightType (natural person)
    - organisation: eCH-0097:organisationIdentificationType (legal entity)

    Uses wrapper pattern for cross-namespace serialization:
    the choice branch element is in eCH-0129 namespace, its children
    are in the external standard's namespace.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'personIdentification'

    individual: Optional[ECH0044PersonIdentificationLight] = xml_field(
        'individual', wrapper=True, child_ns=NS.ECH0044_V4, default=None
    )
    organisation: Optional[ECH0097OrganisationIdentification] = xml_field(
        'organisation', wrapper=True, child_ns=NS.ECH0097_V2, default=None
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one branch must be set."""
        count = sum(v is not None for v in [self.individual, self.organisation])
        if count == 0:
            raise ValueError(
                "personIdentificationType: must set one of "
                "individual or organisation"
            )
        if count > 1:
            raise ValueError(
                "personIdentificationType: only one of "
                "individual or organisation allowed"
            )
        return self
