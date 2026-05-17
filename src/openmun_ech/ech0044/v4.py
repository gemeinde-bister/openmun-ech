"""eCH-0044 Person Identification v4.1.

Standard: eCH-0044 v4.1 (Person Identification)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides person identification structures including:
- Person IDs (VN, local person ID, other IDs, EU person IDs)
- Basic person data (name, sex, date of birth)
- Support for partially known birth dates

ARCHITECTURE: Declarative ECHModel (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/person_mapper.py
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field


class Sex(str, Enum):
    """Sex codes per eCH-0044 sexType.

    XSD: sexType (lines 81-87)
    PDF: Section 3.2.4 sex - Geschlecht (page 7)
    """
    MALE = "1"      # männlich (male)
    FEMALE = "2"    # weiblich (female)
    UNKNOWN = "3"   # unbestimmt (undetermined/unknown)


class ECH0044DatePartiallyKnown(ECHModel):
    """eCH-0044 Partially known date.

    Represents a date that may be:
    - Fully known (year, month, day)
    - Partially known (year and month only)
    - Minimally known (year only)

    This is a choice type - exactly ONE of the three fields must be set.

    XML Schema: eCH-0044 datePartiallyKnownType
    """

    __xml_ns__ = NS.ECH0044_V4
    __xml_element__ = 'dateOfBirth'

    year_month_day: Optional[date] = xml_field('yearMonthDay', default=None)
    year_month: Optional[str] = xml_field(
        'yearMonth', default=None, pattern=r'^\d{4}-\d{2}$'
    )
    year: Optional[str] = xml_field(
        'year', default=None, pattern=r'^\d{4}$'
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce XSD choice: exactly one of the three fields must be set."""
        count = sum(v is not None for v in [
            self.year_month_day, self.year_month, self.year
        ])
        if count == 0:
            raise ValueError(
                "Must specify one of: year_month_day, year_month, or year"
            )
        if count > 1:
            raise ValueError(
                "Can only specify one of: year_month_day, year_month, or year"
            )
        return self

    @classmethod
    def from_date(cls, d: date) -> 'ECH0044DatePartiallyKnown':
        """Create from a full date (convenience factory)."""
        return cls(year_month_day=d)

    @classmethod
    def from_year_month(cls, year: int, month: int) -> 'ECH0044DatePartiallyKnown':
        """Create from year and month (convenience factory)."""
        return cls(year_month=f"{year:04d}-{month:02d}")

    @classmethod
    def from_year(cls, year: int) -> 'ECH0044DatePartiallyKnown':
        """Create from year only (convenience factory)."""
        return cls(year=f"{year:04d}")


class ECH0044NamedPersonId(ECHModel):
    """eCH-0044 Named person ID.

    Represents a person identifier with a category and value.
    Used for local person IDs, other person IDs, and EU person IDs.

    Common categories:
    - "veka.id" - Municipality-specific ID
    - "sedex.id" - Sedex participant ID
    - "eWID" - Dwelling ID
    - "EGID" - Building ID

    XML Schema: eCH-0044 namedPersonIdType
    """

    __xml_ns__ = NS.ECH0044_V4
    __xml_element__ = 'localPersonId'

    person_id_category: str = xml_field(
        'personIdCategory', min_length=1, max_length=20
    )
    person_id: str = xml_field(
        'personId', min_length=1, max_length=36
    )


class ECH0044PersonIdentification(ECHModel):
    """eCH-0044 Person identification (full version).

    Contains complete person identification information including:
    - VN (AHV-13 number) - optional
    - Local person ID - required
    - Other person IDs - optional (multiple)
    - EU person IDs - optional (multiple)
    - Official name - required
    - First name - required
    - Original name - optional
    - Sex - required (1=male, 2=female, 3=unknown)
    - Date of birth - required (may be partially known)

    XML Schema: eCH-0044 personIdentificationType
    """

    __xml_ns__ = NS.ECH0044_V4
    __xml_element__ = 'personIdentification'

    vn: Optional[str] = xml_field(
        'vn', default=None, pattern=r'^756\d{10}$'
    )
    local_person_id: ECH0044NamedPersonId = xml_field('localPersonId')
    other_person_id: List[ECH0044NamedPersonId] = xml_field(
        'otherPersonId', is_list=True, default_factory=list
    )
    eu_person_id: List[ECH0044NamedPersonId] = xml_field(
        'euPersonId', is_list=True, default_factory=list
    )
    official_name: str = xml_field('officialName', min_length=1, max_length=100)
    first_name: str = xml_field('firstName', min_length=1, max_length=100)
    original_name: Optional[str] = xml_field(
        'originalName', default=None, min_length=1, max_length=100
    )
    sex: Sex = xml_field('sex')
    date_of_birth: ECH0044DatePartiallyKnown = xml_field('dateOfBirth')

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number range."""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")
        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")
        return v


class ECH0044PersonIdentificationKeyOnly(ECHModel):
    """eCH-0044 Person identification (key only).

    Contains only identification keys without personal data (name, sex, birth).
    Used for privacy-sensitive contexts or ID-only references where personal
    data should not be transmitted.

    XML Schema: eCH-0044 personIdentificationKeyOnlyType
    XSD Lines: 41-48
    """

    __xml_ns__ = NS.ECH0044_V4
    __xml_element__ = 'personIdentificationKeyOnly'

    vn: Optional[str] = xml_field(
        'vn', default=None, pattern=r'^756\d{10}$'
    )
    local_person_id: ECH0044NamedPersonId = xml_field('localPersonId')
    other_person_id: List[ECH0044NamedPersonId] = xml_field(
        'otherPersonId', is_list=True, default_factory=list
    )
    eu_person_id: List[ECH0044NamedPersonId] = xml_field(
        'euPersonId', is_list=True, default_factory=list
    )

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number range."""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")
        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")
        return v


class ECH0044PersonIdentificationLight(ECHModel):
    """eCH-0044 Person identification (light version).

    Lighter version of person identification with fewer required fields.
    Used in relationships where full identification is not always available.

    Contains:
    - VN (AHV-13 number) - optional
    - Local person ID - optional
    - Other person IDs - optional (multiple)
    - Official name - required
    - First name - required
    - Original name - optional
    - Sex - optional
    - Date of birth - optional (may be partially known)

    XML Schema: eCH-0044 personIdentificationLightType
    """

    __xml_ns__ = NS.ECH0044_V4
    __xml_element__ = 'personIdentificationPartner'

    vn: Optional[str] = xml_field(
        'vn', default=None, pattern=r'^756\d{10}$'
    )
    local_person_id: Optional[ECH0044NamedPersonId] = xml_field(
        'localPersonId', default=None
    )
    other_person_id: List[ECH0044NamedPersonId] = xml_field(
        'otherPersonId', is_list=True, default_factory=list
    )
    official_name: str = xml_field('officialName', min_length=1, max_length=100)
    first_name: str = xml_field('firstName', min_length=1, max_length=100)
    original_name: Optional[str] = xml_field(
        'originalName', default=None, min_length=1, max_length=100
    )
    sex: Optional[Sex] = xml_field('sex', default=None)
    date_of_birth: Optional[ECH0044DatePartiallyKnown] = xml_field(
        'dateOfBirth', default=None
    )

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number range."""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")
        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")
        return v
