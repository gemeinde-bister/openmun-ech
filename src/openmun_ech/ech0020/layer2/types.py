"""eCH-0020 Layer 2: Enums and Reusable Type Models."""

from datetime import date
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from openmun_ech.ech0044 import Sex


# ============================================================================
# ENUMS FOR CHOICE CONSTRAINTS (Phase 0.2: CHOICE Constraint Analysis)
# ============================================================================

class ReportingType(str, Enum):
    """Reporting type nested CHOICE (reportingMunicipality XOR federalRegister)."""
    MUNICIPALITY = "municipality"
    FEDERAL_REGISTER = "federal_register"


class PlaceType(str, Enum):
    """Place type CHOICE (unknown XOR swiss_municipality XOR foreign_country)."""
    UNKNOWN = "unknown"
    SWISS = "swiss"
    FOREIGN = "foreign"


class GuardianType(str, Enum):
    """Guardian type CHOICE (person XOR person_partner XOR organisation)."""
    PERSON = "person"
    PERSON_PARTNER = "partner"
    ORGANISATION = "organisation"


class DatePrecision(str, Enum):
    """Date precision CHOICE (year_month_day XOR year_month XOR year)."""
    FULL = "full"  # YYYY-MM-DD
    YEAR_MONTH = "year_month"  # YYYY-MM
    YEAR_ONLY = "year"  # YYYY


# ============================================================================
# REUSABLE PERSON IDENTIFICATION (Phase 0.3: Relationship Data Analysis)
# ============================================================================

class PersonIdentification(BaseModel):
    """Reusable person identification for main person and related persons.

    Used for:
    - Spouse identification
    - Parent identification
    - Guardian identification (if person type)

    Design: Covers both ECH0044PersonIdentification and ECH0044PersonIdentificationLight.
    Validation: All required fields must be provided (zero tolerance).
    """

    # Identity
    vn: Optional[str] = Field(
        None,
        description="AHV-13 number (Swiss: starts with 756, total 13 digits)",
        pattern=r"^756\d{10}$"
    )
    local_person_id: Optional[str] = Field(
        None,
        description="Local person ID from municipality system"
    )
    local_person_id_category: Optional[str] = Field(
        None,
        description="Category of local person ID (e.g., 'veka.id')"
    )

    # Name (required)
    official_name: str = Field(
        ...,
        description="Family name / last name (required)"
    )
    first_name: str = Field(
        ...,
        description="First name / given name (required)"
    )
    original_name: Optional[str] = Field(
        None,
        description="Birth name / maiden name"
    )

    # Demographics (optional in Light version, required in Full version)
    sex: Optional[Sex] = Field(
        None,
        description="Sex: '1'=male, '2'=female, '3'=unknown (optional for relationships)"
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Date of birth (optional for relationships, may be partially known in Layer 1)"
    )
    date_of_birth_precision: Optional[DatePrecision] = Field(
        None,
        description="Precision of date_of_birth for lossless roundtrips. "
                    "None means FULL precision (YYYY-MM-DD)."
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v: Optional[Sex]) -> Optional[Sex]:
        """Validate sex value (Enum coerced by Pydantic; None allowed)."""
        return v


# ============================================================================
# RELATIONSHIP MODELS (Phase 0.3: Flat reference structure)
# ============================================================================

class ParentInfo(BaseModel):
    """Parent information for parental_relationship list.

    Contains:
    - Person identification (full PersonIdentification model)
    - Relationship type (biological/foster mother/father)
    - Care arrangement (parental authority)
    - Validity dates
    - Optional address with mr_mrs
    """

    person: PersonIdentification = Field(
        ...,
        description="Parent's identification data (required)"
    )
    relationship_type: str = Field(
        ...,
        description="Type: '3'=mother, '4'=father, '5'=foster_father, '6'=foster_mother",
        pattern=r"^[3-6]$"
    )
    care: str = Field(
        ...,
        description="Parental authority: '0'=unknown, '1'=legacy (old law), '2'=joint, '3'=sole, '4'=none (required)",
        pattern=r"^[0-4]$"
    )
    relationship_valid_from: Optional[date] = Field(
        None,
        description="Date from which relationship is valid"
    )

    # Address fields (from ECH0010MailAddress)
    mr_mrs: Optional[str] = Field(
        None,
        description="Parent salutation in mail address: '1'=Frau, '2'=Herr, '3'=deprecated"
    )
    address_street: Optional[str] = Field(
        None,
        description="Parent's street address"
    )
    address_house_number: Optional[str] = Field(
        None,
        description="Parent's house number"
    )
    address_postal_code: Optional[str] = Field(
        None,
        description="Parent's postal code"
    )
    address_postal_code_addon: Optional[str] = Field(
        None,
        description="Parent's postal code add-on (optional)"
    )
    address_town: Optional[str] = Field(
        None,
        description="Parent's town/city"
    )
    address_country: Optional[str] = Field(
        None,
        description="Parent's address country (ISO 3166-1 alpha-2, e.g., 'CH', 'DE')",
        pattern=r"^[A-Z]{2}$"
    )

    model_config = ConfigDict(populate_by_name=True)


class GuardianInfo(BaseModel):
    """Guardian information for guardian_relationship list.

    Supports three types (CHOICE):
    - Person guardian (full person identification)
    - Organization guardian (UID + name)

    Contains:
    - Guardian identification (person OR organization)
    - Guardian type
    - Legal basis (ZGB articles)
    - Care arrangement
    """

    guardian_relationship_id: str = Field(
        ...,
        max_length=36,
        description="Unique guardian relationship identifier (required)"
    )

    # CHOICE: Person guardian OR organization guardian
    guardian_type: GuardianType = Field(
        ...,
        description="Guardian type: PERSON, PERSON_PARTNER, or ORGANISATION"
    )

    # Person guardian fields (if guardian_type == PERSON or PERSON_PARTNER)
    person: Optional[PersonIdentification] = Field(
        None,
        description="Guardian person identification (if type=PERSON)"
    )

    # Organization guardian fields (if guardian_type == ORGANISATION)
    organization_uid: Optional[str] = Field(
        None,
        pattern=r"^CHE-\d{3}\.\d{3}\.\d{3}$",
        description="Organization UID (if type=ORGANISATION)"
    )
    organization_name: Optional[str] = Field(
        None,
        description="Organization name (if type=ORGANISATION)"
    )

    # Address fields (from ECH0010MailAddress in partner_address)
    mr_mrs: Optional[str] = Field(
        None,
        description="Guardian salutation in mail address: '1'=Frau, '2'=Herr, '3'=deprecated"
    )
    address_street: Optional[str] = Field(
        None,
        description="Guardian's street address"
    )
    address_house_number: Optional[str] = Field(
        None,
        description="Guardian's house number"
    )
    address_postal_code: Optional[str] = Field(
        None,
        description="Guardian's postal code"
    )
    address_postal_code_addon: Optional[str] = Field(
        None,
        description="Guardian's postal code add-on (optional)"
    )
    address_town: Optional[str] = Field(
        None,
        description="Guardian's town/city"
    )
    address_country: Optional[str] = Field(
        None,
        description="Guardian's address country (ISO 3166-1 alpha-2, e.g., 'CH', 'DE')",
        pattern=r"^[A-Z]{2}$"
    )

    # Common fields
    relationship_type: str = Field(
        ...,
        description="Type: '7'=guardian_person, '8'=guardian_org, '9'=representative, '10'=curator",
        pattern=r"^(7|8|9|10)$"
    )
    guardian_measure_based_on_law: List[str] = Field(
        default_factory=list,
        description="ZGB article numbers (e.g., ['310', '327'])"
    )
    guardian_measure_valid_from: date = Field(
        ...,
        description="Date from which guardian measure is valid (required)"
    )
    care: Optional[str] = Field(
        None,
        description="Care arrangement type (CareType enum value)"
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_guardian_choice(self) -> 'GuardianInfo':
        """Validate CHOICE: person XOR organization based on guardian_type."""
        if self.guardian_type == GuardianType.PERSON or self.guardian_type == GuardianType.PERSON_PARTNER:
            if not self.person:
                raise ValueError(f"Guardian type {self.guardian_type} requires person field")
            if self.organization_uid or self.organization_name:
                raise ValueError(f"Guardian type {self.guardian_type} cannot have organization fields")
        elif self.guardian_type == GuardianType.ORGANISATION:
            # Per eCH-0011: UID is required (true identifier), name is optional (stored in address)
            # Per zero-tolerance policy: organization_name can be lost if no address data provided
            if not self.organization_uid:
                raise ValueError("Guardian type ORGANISATION requires organization_uid")
            if self.person:
                raise ValueError("Guardian type ORGANISATION cannot have person field")

        return self
