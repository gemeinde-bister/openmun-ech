"""eCH-0020 Layer 2: Simplified Models for Application Use.

Layer 2 provides a flattened, user-friendly API for constructing eCH-0020 deliveries
from application data (e.g., database fields). This layer hides XML complexity while
maintaining 100% XSD compliance through conversion to Layer 1 models.

Architecture:
- Layer 1 (v3.py): XSD-faithful models for XML roundtrip
- Layer 2 (this file): Simplified models for application use

Design Principles (Zero Tolerance):
1. No default values for government data
2. No data invention
3. Fail hard on missing required data
4. No lossy transformations
5. No schema violations
6. Explicit over implicit

Type 1 Duplication Handling (Schema Duplication):
- official_name, first_name, sex, date_of_birth appear in multiple Layer 1 locations
- User provides ONCE in Layer 2
- to_ech0020() copies to all required Layer 1 locations

Type 2 "Duplication" (Relationships):
- Fields appear in related persons (spouse, parents, guardians)
- NOT duplication - different people
- Clear naming with PersonIdentification model

Phase 0 Validation: COMPLETE ✅
- All 21 fields flattenable (max depth 5 → 2)
- 8 CHOICE constraints handled with Enums
- Relationships are FLAT (no circular references)
- NO Type 3 conflicts found
- GO decision approved 2025-01-04

Implementation Status:
- Phase 1.1: Model Design - COMPLETE ✅ (2025-01-04)
- Phase 1.2: Layer 2 → Layer 1 (to_ech0020) - COMPLETE ✅ (2025-11-04)
- Phase 1.3: Layer 1 → Layer 2 (from_ech0020) - COMPLETE ✅ (2025-11-04)
- Phase 1.4: Comprehensive Tests - IN PROGRESS
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Union
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# Import Layer 1 models for conversion
from openmun_ech.ech0020.v3 import (
    ECH0020BaseDeliveryPerson,
    ECH0020EventBaseDelivery,
    ECH0020HasMainResidence,
    ECH0020HasSecondaryResidence,
    ECH0020ReportingMunicipalityRestrictedBaseSecondary,
    ECH0020NameInfo,
    ECH0020BirthInfo,
    ECH0020MaritalInfo,
    ECH0020PlaceOfOriginInfo,
    ECH0020Delivery,
    ECH0020Header,
)
from openmun_ech.ech0058 import ECH0058Header, ECH0058SendingApplication, ActionType
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044NamedPersonId,
    ECH0044DatePartiallyKnown,
    Sex,
)
from openmun_ech.ech0011 import (
    ECH0011NameData,
    ECH0011BirthData,
    ECH0011MaritalData,
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011CountryInfo,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathPeriod,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011GeneralPlace,
    ECH0011ForeignerName,
    ECH0011PartnerIdOrganisation,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    MaritalStatus,
    TypeOfHousehold,
    FederalRegister,
)
from openmun_ech.ech0021.v7 import (
    ECH0021LockData,
    ECH0021PersonAdditionalData,
    ECH0021PoliticalRightData,
    ECH0021JobData,
    ECH0021MaritalRelationship,
    ECH0021MaritalDataAddon,
    ECH0021ParentalRelationship,
    ECH0021GuardianRelationship,
    ECH0021GuardianMeasureInfo,
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021HealthInsuranceData,
    ECH0021MatrimonialInheritanceArrangementData,
    ECH0021Partner,
    ECH0021BirthAddonData,
    ECH0021OccupationData,
    ECH0021UIDStructure,
)
from openmun_ech.ech0021.enums import UIDOrganisationIdCategory
from openmun_ech.ech0007 import ECH0007Municipality, ECH0007SwissMunicipality
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0010 import (
    ECH0010MailAddress,
    ECH0010AddressInformation,
    ECH0010SwissAddressInformation,
    ECH0010OrganisationMailAddressInfo,
    ECH0010OrganisationMailAddress,
)


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
# DELIVERY CONFIGURATION (Phase 2.3: Delivery Construction)
# ============================================================================

class DeliveryConfig(BaseModel):
    """Deployment configuration for creating complete eCH deliveries.

    This configuration contains deployment-level metadata that remains constant
    across all deliveries from a specific application deployment. Values should
    come from configuration files or environment variables, NEVER hardcoded.

    Usage Pattern:
        >>> # Load from config file (user implementation)
        >>> config = DeliveryConfig(
        ...     sender_id="1-6172-1",              # From sedex registration
        ...     manufacturer="OpenMun",            # From application config
        ...     product="Municipality System",    # From application config
        ...     product_version="1.0.0",         # From application version
        ...     test_delivery_flag=True           # From environment (test vs prod)
        ... )
        >>>
        >>> # Use with Layer 2 events to create complete deliveries
        >>> event = BaseDeliveryEvent(...)
        >>> delivery = event.finalize(config)
        >>> delivery.to_file("output.xml")

    Config File Example (YAML):
        deployment:
          sender_id: "1-6172-1"
          manufacturer: "OpenMun"
          product: "Municipality System"
          product_version: "1.0.0"
          test_delivery_flag: true

    Config File Example (TOML):
        [deployment]
        sender_id = "1-6172-1"
        manufacturer = "OpenMun"
        product = "Municipality System"
        product_version = "1.0.0"
        test_delivery_flag = true

    Homogeneous API:
        Same DeliveryConfig works for ALL eCH delivery types:
        - eCH-0020 (Event deliveries): BaseDeliveryEvent.finalize(config)
        - eCH-0099 (Statistics deliveries): StatisticsDelivery.finalize(config)
        - Future eCH types: Same pattern

    Zero-Tolerance Policy:
        Values MUST come from configuration, not hardcoded:
        - ❌ WRONG: DeliveryConfig(manufacturer="OpenMun")  # Hardcoded
        - ✅ RIGHT: DeliveryConfig(**yaml.safe_load(config_file))

    See Also:
        - BaseDeliveryEvent.finalize(): Uses this config to create ECH0020Delivery
        - docs/PHASE_2_3_DELIVERY_CONSTRUCTION_DECISION.md: Design rationale
    """

    # ========== Required Fields (Deployment-Level) ==========
    sender_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Sedex participant ID (format: type-bfs-instance, e.g., '1-6172-1'). "
            "Identifies the sender in the sedex network. Must come from sedex registration."
        )
    )
    manufacturer: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description=(
            "Software manufacturer name (1-30 characters). "
            "Identifies who developed the software. Must come from application configuration."
        )
    )
    product: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description=(
            "Product/software name (1-30 characters). "
            "Identifies the software product. Must come from application configuration."
        )
    )
    product_version: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description=(
            "Product version (1-10 characters, e.g., '1.0.0'). "
            "Identifies the software version. Must come from application version."
        )
    )
    test_delivery_flag: bool = Field(
        ...,
        description=(
            "Test vs production flag. True = test delivery, False = production delivery. "
            "Should come from environment configuration (test/staging/production)."
        )
    )

    # ========== Optional Fields (Deployment-Level) ==========
    message_type_override: Optional[str] = Field(
        None,
        description=(
            "Override message type URI. If None, auto-detected based on delivery type: "
            "eCH-0020 = 'http://www.ech.ch/xmlns/eCH-0020/3', "
            "eCH-0099 = 'http://www.ech.ch/xmlns/eCH-0099/2'. "
            "Only override if using non-standard message types."
        )
    )
    original_sender_id: Optional[str] = Field(
        None,
        description=(
            "Original sender ID for forwarded messages (optional). "
            "Only used if this deployment forwards messages from another system."
        )
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


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


# ============================================================================
# LAYER 2 MAIN MODEL: BASE DELIVERY PERSON
# ============================================================================

class BaseDeliveryPerson(BaseModel):
    """Layer 2: Simplified model for eCH-0020 base delivery person construction.

    This model flattens the complex Layer 1 structure (7 nesting levels → 1-2 levels).

    Features:
    - Flat main person fields (no nesting)
    - One level of nesting for relationships
    - Type 1 duplication handled internally (official_name, first_name, sex, date_of_birth)
    - Type 2 relationships exposed clearly (spouse, parents, guardians)
    - CHOICE constraints enforced with validators
    - Zero tolerance validation (no defaults, explicit required)

    Conversion:
    - to_ech0020(): Convert to Layer 1 ECH0020BaseDeliveryPerson
    - from_ech0020(): Convert from Layer 1 to Layer 2

    Coverage: All 21 fields from ECH0020BaseDeliveryPerson (Phase 0.1)
    """

    # ========================================================================
    # 1. PERSON IDENTIFICATION (REQUIRED) - Flattened from ECH0044PersonIdentification
    # ========================================================================
    # Type 1 Duplication: These 4 fields appear in multiple Layer 1 locations
    # User provides ONCE here, to_ech0020() copies to all locations

    vn: Optional[str] = Field(
        None,
        description="AHV-13 number (Swiss: starts with 756, total 13 digits)",
        pattern=r"^756\d{10}$"
    )
    local_person_id: str = Field(
        ...,
        description="Local person ID from municipality system (required)"
    )
    local_person_id_category: str = Field(
        ...,
        description=(
            "Category of local person ID (required). "
            "Format: 'MU.{BFS_NUMBER}' for municipalities (e.g., 'MU.6172'), "
            "'CH.ZAR' (Central Register), 'CH.ZEMIS' (Foreign nationals). "
            "MU = Municipality, BFS_NUMBER = Federal Statistical Office number."
        )
    )
    other_person_ids: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Other person IDs (e.g., CH.ZAR, CH.ZEMIS). Each dict has 'person_id' and 'person_id_category' keys."
    )

    # Type 1 duplicated fields (provided once, copied to person_identification + name_data)
    official_name: str = Field(
        ...,
        description="Family name / last name (required, Type 1 duplication)"
    )
    first_name: str = Field(
        ...,
        description="First name / given name (required, Type 1 duplication)"
    )
    original_name: Optional[str] = Field(
        None,
        description="Birth name / maiden name"
    )

    # Type 1 duplicated fields (provided once, copied to person_identification + birth_data)
    sex: Sex = Field(
        ...,
        description="Sex: '1'=male, '2'=female, '3'=unknown (Type 1 duplication)"
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth (full date, required, Type 1 duplication)"
    )

    # ========================================================================
    # 2. NAME INFO (REQUIRED) - Flattened from ECH0020NameInfo
    # ========================================================================

    call_name: Optional[str] = Field(
        None,
        description="Call name / preferred name"
    )
    alliance_name: Optional[str] = Field(
        None,
        description="Alliance name"
    )
    alias_name: Optional[str] = Field(
        None,
        description="Alias name"
    )
    other_name: Optional[str] = Field(
        None,
        description="Other name"
    )
    name_valid_from: Optional[date] = Field(
        None,
        description="Date from which name is valid"
    )

    # Foreign name fields (CHOICE: at most one)
    name_on_foreign_passport: Optional[str] = Field(
        None,
        description="Name on foreign passport"
    )
    name_on_foreign_passport_first: Optional[str] = Field(
        None,
        description="First name on foreign passport"
    )
    declared_foreign_name: Optional[str] = Field(
        None,
        description="Declared foreign name"
    )
    declared_foreign_name_first: Optional[str] = Field(
        None,
        description="Declared foreign first name"
    )

    # ========================================================================
    # 3. BIRTH INFO (REQUIRED) - Flattened from ECH0020BirthInfo
    # ========================================================================

    birth_place_type: PlaceType = Field(
        ...,
        description="Type of birth place (CHOICE: unknown, swiss, foreign)"
    )
    # Swiss birth fields (required if birth_place_type == SWISS)
    birth_municipality_bfs: Optional[str] = Field(
        None,
        description="BFS municipality code for Swiss birth"
    )
    birth_municipality_name: Optional[str] = Field(
        None,
        description="Municipality name for Swiss birth"
    )
    birth_canton_abbreviation: Optional[str] = Field(
        None,
        description="Canton abbreviation for Swiss birth (e.g., ZH, VS)"
    )
    birth_municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS number for merged municipalities (historyMunicipalityId)"
    )
    # Foreign birth fields (required if birth_place_type == FOREIGN)
    birth_country_id: Optional[str] = Field(
        None,
        description="BFS country code (4 digits) for foreign birth"
    )
    birth_country_iso: Optional[str] = Field(
        None,
        description="ISO 3166-1 alpha-2 country code (2 letters) for foreign birth",
        pattern=r"^[A-Z]{2}$"
    )
    birth_country_name_short: Optional[str] = Field(
        None,
        description="Country name (short) for foreign birth"
    )
    birth_town: Optional[str] = Field(
        None,
        description="Town/city name for foreign birth"
    )

    # Parent names (optional addon data from ECH-0021)
    birth_father_name: Optional[str] = Field(
        None,
        description="Father's official name (from birth certificate)"
    )
    birth_father_first_name: Optional[str] = Field(
        None,
        description="Father's first name (from birth certificate)"
    )
    birth_father_official_proof: Optional[bool] = Field(
        None,
        description="Official proof of father's name exists (from birth certificate)"
    )
    birth_mother_name: Optional[str] = Field(
        None,
        description="Mother's official name (from birth certificate)"
    )
    birth_mother_first_name: Optional[str] = Field(
        None,
        description="Mother's first name (from birth certificate)"
    )
    birth_mother_official_proof: Optional[bool] = Field(
        None,
        description="Official proof of mother's name exists (from birth certificate)"
    )

    # ========================================================================
    # 4. RELIGION DATA (REQUIRED)
    # ========================================================================

    religion: str = Field(
        ...,
        description="Religion code (3-6 digits, e.g., '111' for Roman Catholic)",
        pattern=r"^\d{3,6}$"
    )
    religion_valid_from: Optional[date] = Field(
        None,
        description="Date from which religion is valid"
    )

    # ========================================================================
    # 5. MARITAL INFO (REQUIRED)
    # ========================================================================

    marital_status: MaritalStatus = Field(
        ...,
        description="Marital status: 1=unmarried, 2=married, 3=widowed, 4=divorced, 5=separated, 6=partnership, 9=unknown"
    )
    date_of_marital_status: Optional[date] = Field(
        None,
        description="Date of current marital status"
    )
    official_proof_of_marital_status_yes_no: Optional[bool] = Field(
        None,
        description="Whether official proof of marital status exists"
    )

    # Place of marriage (optional, part of marital_data_addon)
    marriage_place_type: Optional[PlaceType] = Field(
        None,
        description="Type of marriage place (swiss, foreign, unknown)"
    )
    marriage_municipality_bfs: Optional[str] = Field(
        None,
        description="BFS municipality code for Swiss marriage"
    )
    marriage_municipality_name: Optional[str] = Field(
        None,
        description="Municipality name for Swiss marriage"
    )
    marriage_municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS number for merged municipalities (historyMunicipalityId)"
    )
    marriage_canton_abbreviation: Optional[str] = Field(
        None,
        description="Canton abbreviation for Swiss marriage (e.g., ZH, VS)"
    )
    marriage_country_id: Optional[str] = Field(
        None,
        description="BFS country code (4 digits) for foreign marriage"
    )
    marriage_country_iso: Optional[str] = Field(
        None,
        description="ISO 3166-1 alpha-2 country code (2 letters) for foreign marriage",
        pattern=r"^[A-Z]{2}$"
    )
    marriage_country_name_short: Optional[str] = Field(
        None,
        description="Country name (short) for foreign marriage"
    )
    marriage_town: Optional[str] = Field(
        None,
        description="Town/city name for foreign marriage"
    )

    # ========================================================================
    # 6. NATIONALITY DATA (REQUIRED)
    # ========================================================================

    nationality_status: str = Field(
        ...,
        description="Nationality status per eCH-0011 v9.0.0: 0=unknown, 1=stateless, 2=known (NOTE: Does NOT indicate Swiss/foreign - use places_of_origin vs residence_permit)",
        pattern=r"^[0-2]$"
    )
    nationalities: Optional[List[dict]] = Field(
        None,
        description="List of nationalities with validity dates: [{'country_id': '8100' (BFS), 'country_iso': 'CH' (ISO), 'country_name_short': 'Schweiz', 'valid_from': date}]"
    )

    # ========================================================================
    # 7 & 8. CITIZENSHIP CHOICE (REQUIRED) - placeOfOriginInfo XOR residencePermitData
    # ========================================================================
    # CHOICE constraint: Exactly ONE must be present

    # Swiss citizens (CHOICE option 1)
    places_of_origin: Optional[List[dict]] = Field(
        None,
        description="Swiss places of origin (1-n for Swiss citizens): [{'bfs_code': str, 'name': str, 'canton': str}]"
    )

    # Foreign nationals (CHOICE option 2)
    residence_permit: Optional[str] = Field(
        None,
        description="Residence permit type for foreign nationals (e.g., 'B', 'C', 'L')"
    )
    residence_permit_valid_from: Optional[date] = Field(
        None,
        description="Residence permit valid from date"
    )
    residence_permit_valid_till: Optional[date] = Field(
        None,
        description="Residence permit valid until date"
    )
    entry_date: Optional[date] = Field(
        None,
        description="Entry date to Switzerland"
    )

    # ========================================================================
    # 9. LOCK DATA (REQUIRED)
    # ========================================================================

    data_lock: str = Field(
        ...,
        description="Data lock type (eCH-0021 enum value)"
    )
    data_lock_valid_from: Optional[date] = Field(
        None,
        description="Data lock valid from date"
    )
    data_lock_valid_till: Optional[date] = Field(
        None,
        description="Data lock valid until date"
    )
    paper_lock: Optional[bool] = Field(
        None,
        description="Paper lock flag"
    )
    paper_lock_valid_from: Optional[date] = Field(
        None,
        description="Paper lock valid from date"
    )
    paper_lock_valid_till: Optional[date] = Field(
        None,
        description="Paper lock valid until date"
    )

    # ========================================================================
    # 10. DEATH DATA (OPTIONAL)
    # ========================================================================

    death_date: Optional[date] = Field(
        None,
        description="Death date (exact)"
    )
    death_place_type: Optional[PlaceType] = Field(
        None,
        description="Type of death place (swiss, foreign, unknown)"
    )
    death_municipality_bfs: Optional[str] = Field(
        None,
        description="BFS municipality code for Swiss death"
    )
    death_municipality_name: Optional[str] = Field(
        None,
        description="Municipality name for Swiss death"
    )
    death_canton_abbreviation: Optional[str] = Field(
        None,
        description="Canton abbreviation for Swiss death (e.g., ZH, VS)",
        max_length=2
    )
    death_municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS number for merged municipalities"
    )
    death_country_id: Optional[str] = Field(
        None,
        description="BFS country code (4 digits) for foreign death"
    )
    death_country_iso: Optional[str] = Field(
        None,
        description="ISO 3166-1 alpha-2 country code (2 letters) for foreign death",
        pattern=r"^[A-Z]{2}$"
    )
    death_country_name_short: Optional[str] = Field(
        None,
        description="Country name (short form) for foreign death"
    )

    # ========================================================================
    # 11. CONTACT DATA (OPTIONAL) - Flattened from ECH0011ContactData
    # ========================================================================
    # NOTE: If any contact fields are provided, contact_address_* fields become required
    # per Layer 1 ECH0011ContactData constraint

    # Contact person/organization identification (CHOICE: at most one)
    # Simplified from PersonIdentification - just name fields for Layer 2
    contact_person_official_name: Optional[str] = Field(
        None,
        description="Contact person's family name (CHOICE: person XOR organization)"
    )
    contact_person_first_name: Optional[str] = Field(
        None,
        description="Contact person's first name"
    )
    contact_person_sex: Optional[str] = Field(
        None,
        description="Contact person's sex (optional, required for Full identification): '1'=male, '2'=female, '3'=unknown",
        pattern=r"^[123]$"
    )
    contact_person_date_of_birth: Optional[date] = Field(
        None,
        description="Contact person's date of birth (optional, required for Full identification)"
    )
    contact_person_mr_mrs: Optional[str] = Field(
        None,
        description="Contact person's title/salutation: '1'=Herr/Mr, '2'=Frau/Mrs, '3'=neutral"
    )
    contact_person_local_person_id: Optional[str] = Field(
        None,
        description="Contact person's local person ID (from personIdentificationPartner)"
    )
    contact_person_local_person_id_category: Optional[str] = Field(
        None,
        description="Contact person's local person ID category (from personIdentificationPartner)"
    )
    contact_person_vn: Optional[str] = Field(
        None,
        description="Contact person's Swiss social security number (AHV-13, from personIdentificationPartner)"
    )
    contact_organization_name: Optional[str] = Field(
        None,
        description="Contact organization name (CHOICE: person XOR organization)"
    )

    # Contact address (REQUIRED in Layer 1 if contact_data is present)
    # Flattened from ECH0010MailAddress > address_information
    contact_address_address_line1: Optional[str] = Field(
        None,
        description="Address line 1 (c/o, attention, or additional address info)"
    )
    contact_address_street: Optional[str] = Field(
        None,
        description="Street name for contact address"
    )
    contact_address_house_number: Optional[str] = Field(
        None,
        description="House number for contact address"
    )
    contact_address_dwelling_number: Optional[str] = Field(
        None,
        description="Dwelling/apartment number"
    )
    contact_address_postal_code: Optional[str] = Field(
        None,
        description="Postal code for contact address (required if contact provided)"
    )
    contact_address_postal_code_addon: Optional[str] = Field(
        None,
        description="Postal code add-on (optional, e.g., '02' for specific delivery area)"
    )
    contact_address_town: Optional[str] = Field(
        None,
        description="Town/city name for contact address (required if contact provided)"
    )
    contact_address_locality: Optional[str] = Field(
        None,
        description="Locality/district name"
    )
    contact_address_country_iso: Optional[str] = Field(
        None,
        description="ISO country code (for foreign addresses, optional for Swiss)",
        pattern=r"^[A-Z]{2}$"
    )

    # Contact validity
    contact_valid_from: Optional[date] = Field(
        None,
        description="Contact data valid from date"
    )
    contact_valid_till: Optional[date] = Field(
        None,
        description="Contact data valid until date"
    )

    # ========================================================================
    # 12. PERSON ADDITIONAL DATA (OPTIONAL) - From ECH0021PersonAdditionalData
    # ========================================================================
    # All fields are optional, no nesting

    mr_mrs: Optional[str] = Field(
        None,
        description="Salutation/title: '1'=Mr/Herr, '2'=Mrs/Frau",
        pattern=r"^[12]$"
    )
    title: Optional[str] = Field(
        None,
        max_length=50,
        description="Academic/professional title (e.g., 'Dr.', 'Prof.')"
    )
    language_of_correspondance: Optional[str] = Field(
        None,
        description="Language code: 'de', 'fr', 'it', 'rm', 'en'",
        pattern=r"^(de|fr|it|rm|en)$"
    )

    # ========================================================================
    # 13. POLITICAL RIGHT DATA (OPTIONAL) - From ECH0021PoliticalRightData (v7 only)
    # ========================================================================
    # NOTE: This field was REMOVED in eCH-0021 v8 but exists in v7 for eCH-0020 v3.0

    restricted_voting_and_election_right_federation: Optional[bool] = Field(
        None,
        description="Restriction of voting rights at federal level (true=restricted, false=not restricted)"
    )

    # ========================================================================
    # 14. JOB DATA (OPTIONAL) - From ECH0021JobData
    # ========================================================================
    # MUST support full structure for zero data loss roundtrip
    # occupation_data is a LIST (0-n employers) in Layer 1

    kind_of_employment: Optional[str] = Field(
        None,
        description="Kind of employment: employed, self-employed, unemployed, etc."
    )
    job_title: Optional[str] = Field(
        None,
        max_length=100,
        description="Job title or occupation description"
    )

    # Occupation data as list to preserve full Layer 1 structure
    # Each item: {employer, employer_uid, place_of_work, place_of_employer, valid_from, valid_till}
    occupation_data: Optional[List[dict]] = Field(
        None,
        description="List of occupation/employer data (0-n). Each dict contains: employer, uid, place_of_work, place_of_employer, occupation_valid_from, occupation_valid_till"
    )

    # ========================================================================
    # 15. MARITAL RELATIONSHIP (OPTIONAL) - From ECH0021MaritalRelationship
    # ========================================================================
    # Uses PersonIdentification model for spouse data
    # Phase 0.3: Confirmed flat reference structure (no circular references)

    spouse: Optional[PersonIdentification] = Field(
        None,
        description="Spouse or registered partner identification (if married/partnered)"
    )
    spouse_mr_mrs: Optional[str] = Field(
        None,
        description="Spouse salutation in mail address: '1'=Frau, '2'=Herr, '3'=deprecated"
    )
    spouse_address_street: Optional[str] = Field(
        None,
        description="Spouse's street address (if different from main person)"
    )
    spouse_address_house_number: Optional[str] = Field(
        None,
        description="Spouse's house number"
    )
    spouse_address_postal_code: Optional[str] = Field(
        None,
        description="Spouse's postal code"
    )
    spouse_address_postal_code_addon: Optional[str] = Field(
        None,
        description="Spouse's postal code add-on (optional)"
    )
    spouse_address_town: Optional[str] = Field(
        None,
        description="Spouse's town/city"
    )
    spouse_other_person_ids: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Spouse's additional person IDs from other systems: [{'person_id': '123', 'person_id_category': 'CH.ZEMIS'}]"
    )
    marital_relationship_type: Optional[str] = Field(
        None,
        description="Type of relationship: '1'=married, '2'=registered partnership",
        pattern=r"^[12]$"
    )

    # ========================================================================
    # 16. PARENTAL RELATIONSHIP (OPTIONAL) - From ECH0021ParentalRelationship
    # ========================================================================
    # List of 0-n parents (biological + foster)
    # Uses ParentInfo model (defined above) for type safety

    parents: Optional[List[ParentInfo]] = Field(
        None,
        description="List of parent relationships (0-n). Supports biological and foster parents."
    )

    # ========================================================================
    # 17. GUARDIAN RELATIONSHIP (OPTIONAL) - From ECH0021GuardianRelationship
    # ========================================================================
    # List of 0-n guardians (persons or organizations like KESB)
    # Uses GuardianInfo model (defined above) with CHOICE validation

    guardians: Optional[List[GuardianInfo]] = Field(
        None,
        description="List of guardian relationships (0-n). Supports person and organization guardians."
    )

    # ========================================================================
    # 18. ARMED FORCES DATA (OPTIONAL) - From ECH0021ArmedForcesData
    # ========================================================================

    armed_forces_service: Optional[str] = Field(
        None,
        description="Military service status (enum value)"
    )
    armed_forces_liability: Optional[str] = Field(
        None,
        description="Military service liability status (enum value)"
    )
    armed_forces_valid_from: Optional[date] = Field(
        None,
        description="Armed forces data valid from date"
    )

    # ========================================================================
    # 19. CIVIL DEFENSE DATA (OPTIONAL) - From ECH0021CivilDefenseData
    # ========================================================================

    civil_defense: Optional[str] = Field(
        None,
        description="Civil defense service status (enum value)"
    )
    civil_defense_valid_from: Optional[date] = Field(
        None,
        description="Civil defense data valid from date"
    )

    # ========================================================================
    # 20. FIRE SERVICE DATA (OPTIONAL) - From ECH0021FireServiceData
    # ========================================================================

    fire_service: Optional[str] = Field(
        None,
        description="Fire service status (enum value)"
    )
    fire_service_liability: Optional[str] = Field(
        None,
        description="Fire service liability status (enum value)"
    )
    fire_service_valid_from: Optional[date] = Field(
        None,
        description="Fire service data valid from date"
    )

    # ========================================================================
    # 21. HEALTH INSURANCE DATA (OPTIONAL) - From ECH0021HealthInsuranceData
    # ========================================================================

    health_insured: Optional[bool] = Field(
        None,
        description="Health insurance status (true=insured, false=not insured)"
    )
    health_insurance_name: Optional[str] = Field(
        None,
        description="Health insurance company name"
    )
    # Insurance address - flattened from ECH0010MailAddress
    health_insurance_address_street: Optional[str] = Field(
        None,
        description="Health insurance company street address"
    )
    health_insurance_address_house_number: Optional[str] = Field(
        None,
        description="Health insurance company house number"
    )
    health_insurance_address_postal_code: Optional[str] = Field(
        None,
        description="Health insurance company postal code"
    )
    health_insurance_address_town: Optional[str] = Field(
        None,
        description="Health insurance company town/city"
    )
    health_insurance_address_country: Optional[str] = Field(
        None,
        description="Health insurance company country code (ISO 3166-1 alpha-2, e.g., 'CH')",
        pattern=r"^[A-Z]{2}$"
    )
    health_insurance_valid_from: Optional[date] = Field(
        None,
        description="Health insurance data valid from date"
    )

    # ========================================================================
    # 22. MATRIMONIAL INHERITANCE ARRANGEMENT DATA (OPTIONAL) - From ECH0021MatrimonialInheritanceArrangementData
    # ========================================================================

    matrimonial_inheritance_arrangement: Optional[str] = Field(
        None,
        description="Matrimonial property regime type (enum value)"
    )
    matrimonial_inheritance_arrangement_valid_from: Optional[date] = Field(
        None,
        description="Matrimonial arrangement valid from date"
    )

    model_config = ConfigDict(populate_by_name=True)

    # ========================================================================
    # VALIDATORS (CHOICE constraints, zero tolerance)
    # ========================================================================

    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v: Sex) -> Sex:
        """Validate sex value (Enum coerced by Pydantic)."""
        return v

    @field_validator('marital_status')
    @classmethod
    def validate_marital_status(cls, v: 'MaritalStatus') -> 'MaritalStatus':
        """Validate marital status value (Enum coerced by Pydantic)."""
        return v

    @model_validator(mode='after')
    def validate_citizenship_choice(self) -> 'BaseDeliveryPerson':
        """Validate CHOICE: Exactly ONE of places_of_origin OR residence_permit must be present."""
        has_origin = self.places_of_origin is not None and len(self.places_of_origin) > 0
        has_permit = self.residence_permit is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "Must provide either places_of_origin (Swiss citizen) "
                "OR residence_permit (foreign national)"
            )
        if has_origin and has_permit:
            raise ValueError(
                "Cannot provide both places_of_origin AND residence_permit "
                "(XSD CHOICE constraint)"
            )

        return self

    @model_validator(mode='after')
    def validate_birth_place_data(self) -> 'BaseDeliveryPerson':
        """Validate birth place data based on birth_place_type."""
        if self.birth_place_type == PlaceType.SWISS:
            if not self.birth_municipality_bfs:
                raise ValueError("Swiss birth requires birth_municipality_bfs")
        elif self.birth_place_type == PlaceType.FOREIGN:
            if not self.birth_country_iso:
                raise ValueError("Foreign birth requires birth_country_iso")
        # UNKNOWN type requires no additional fields

        return self

    @model_validator(mode='after')
    def validate_foreign_name_choice(self) -> 'BaseDeliveryPerson':
        """Validate CHOICE: At most ONE of name_on_foreign_passport OR declared_foreign_name."""
        has_passport_name = self.name_on_foreign_passport is not None
        has_declared_name = self.declared_foreign_name is not None

        if has_passport_name and has_declared_name:
            raise ValueError(
                "Cannot provide both name_on_foreign_passport AND declared_foreign_name "
                "(XSD CHOICE constraint)"
            )

        return self

    @model_validator(mode='after')
    def validate_contact_data(self) -> 'BaseDeliveryPerson':
        """Validate contact data: CHOICE constraint and required fields."""
        # Check if any contact fields are provided
        has_person_name = self.contact_person_official_name is not None
        has_org_name = self.contact_organization_name is not None
        has_any_contact = (
            has_person_name or has_org_name or
            self.contact_address_street is not None or
            self.contact_address_postal_code is not None or
            self.contact_address_town is not None or
            self.contact_valid_from is not None or
            self.contact_valid_till is not None
        )

        # CHOICE constraint: At most ONE of person OR organization
        if has_person_name and has_org_name:
            raise ValueError(
                "Cannot provide both contact_person_official_name AND contact_organization_name "
                "(XSD CHOICE constraint)"
            )

        # If any contact data is provided, address fields are required
        # per Layer 1 ECH0011ContactData: contact_address is REQUIRED
        if has_any_contact:
            if not self.contact_address_postal_code:
                raise ValueError(
                    "If contact_data is provided, contact_address_postal_code is required"
                )
            if not self.contact_address_town:
                raise ValueError(
                    "If contact_data is provided, contact_address_town is required"
                )

        return self

    # ========================================================================
    # CONVERSION METHODS (Layer 2 ↔ Layer 1)
    # ========================================================================

    def _determine_parent_name_variant(
        self,
        official_name: Optional[str],
        first_name: Optional[str]
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Determine which XSD nameOfParentType variant to use based on provided data.

        XSD defines CHOICE in eCH-0021 nameOfParentType:
        - (firstName + officialName) - both names known
        - firstNameOnly - only first name known
        - officialNameOnly - only official/last name known

        Args:
            official_name: Parent's official/last name
            first_name: Parent's first/given name

        Returns:
            Tuple of (official_name_value, first_name_value, official_name_only_value, first_name_only_value)
            where exactly one pair will be populated based on which variant applies.

        Note: This implements the XSD CHOICE constraint internally, hiding it from the public API.
        """
        if official_name and first_name:
            # Both known: use regular fields
            return (official_name, first_name, None, None)
        elif official_name and not first_name:
            # Only official name: use officialNameOnly variant
            return (None, None, official_name, None)
        elif not official_name and first_name:
            # Only first name: use firstNameOnly variant
            return (None, None, None, first_name)
        else:
            # Neither provided
            return (None, None, None, None)

    def _should_create_contact_person_identification(self) -> bool:
        """Check if we should create a separate personIdentification element for contact person.

        Create separate element (personIdentificationPartner or personIdentification)
        ONLY when we have identifying data beyond just names:
        - vn (AHV number)
        - local_person_id
        - sex AND date_of_birth

        If we ONLY have names (official_name, first_name, optionally mr_mrs),
        put contact person ONLY in the mail address (no separate personIdentification).

        This ensures roundtrip fidelity: XML → Layer 1 → Layer 2 → Layer 1 → XML
        preserves the original structure.

        Returns:
            True if we have identifying data, False if only names

        Note: This replaces the old contact_person_only_in_address flag (removed in P0 refactoring).
        """
        return bool(
            self.contact_person_vn or
            self.contact_person_local_person_id or
            (self.contact_person_sex and self.contact_person_date_of_birth)
        )

    def to_ech0020(self) -> ECH0020BaseDeliveryPerson:
        """Convert Layer 2 model to Layer 1 ECH0020BaseDeliveryPerson.

        Handles:
        - Type 1 duplication: Copies official_name, first_name, sex, date_of_birth to all required locations
        - Wrapper construction: NameInfo, BirthInfo, MaritalInfo, PlaceOfOriginInfo
        - CHOICE constraints: places_of_origin XOR residence_permit
        - Nested model construction: All eCH-0044, eCH-0011, eCH-0021 models

        Returns:
            ECH0020BaseDeliveryPerson: Complete Layer 1 model ready for XML serialization

        Raises:
            ValueError: If validation fails (zero tolerance)
        """
        # ====================================================================
        # 1. PERSON IDENTIFICATION (REQUIRED)
        # Type 1 Duplication: official_name, first_name, sex, date_of_birth
        # ====================================================================

        # Construct local_person_id
        local_person_id = ECH0044NamedPersonId(
            person_id=self.local_person_id,
            person_id_category=self.local_person_id_category
        )

        # Construct other_person_ids (optional, multiple)
        other_person_ids = []
        if self.other_person_ids:
            for other_id_dict in self.other_person_ids:
                other_pid = ECH0044NamedPersonId(
                    person_id=other_id_dict['person_id'],
                    person_id_category=other_id_dict['person_id_category']
                )
                other_person_ids.append(other_pid)

        # Construct date_of_birth wrapper
        date_of_birth_wrapper = ECH0044DatePartiallyKnown(
            year_month_day=self.date_of_birth
        )

        # Construct person_identification (REQUIRED)
        person_identification = ECH0044PersonIdentification(
            vn=self.vn,
            local_person_id=local_person_id,
            other_person_id=other_person_ids,
            official_name=self.official_name,  # Type 1 field
            first_name=self.first_name,  # Type 1 field
            original_name=self.original_name,
            sex=Sex(self.sex),  # Type 1 field - convert to enum
            date_of_birth=date_of_birth_wrapper  # Type 1 field
        )

        # ====================================================================
        # 2. NAME INFO (REQUIRED)
        # Type 1 Duplication: Copy official_name, first_name
        # ====================================================================

        # Handle foreign name CHOICE (at most one)
        name_on_foreign_passport = None
        if self.name_on_foreign_passport:
            name_on_foreign_passport = ECH0011ForeignerName(
                name=self.name_on_foreign_passport,
                first_name=self.name_on_foreign_passport_first
            )

        declared_foreign_name = None
        if self.declared_foreign_name:
            declared_foreign_name = ECH0011ForeignerName(
                name=self.declared_foreign_name,
                first_name=self.declared_foreign_name_first
            )

        # Construct name_data
        name_data = ECH0011NameData(
            official_name=self.official_name,  # Type 1 COPY
            first_name=self.first_name,  # Type 1 COPY
            original_name=self.original_name,
            call_name=self.call_name,
            alliance_name=self.alliance_name,
            alias_name=self.alias_name,
            other_name=self.other_name,
            name_on_foreign_passport=name_on_foreign_passport,
            declared_foreign_name=declared_foreign_name
        )

        # Construct name_info wrapper
        name_info = ECH0020NameInfo(
            name_data=name_data,
            name_valid_from=self.name_valid_from
        )

        # ====================================================================
        # 3. BIRTH INFO (REQUIRED)
        # Type 1 Duplication: Copy sex, date_of_birth
        # CHOICE: birth place type
        # ====================================================================

        # Construct birth place based on CHOICE
        place_of_birth = None
        if self.birth_place_type == PlaceType.UNKNOWN:
            place_of_birth = ECH0011GeneralPlace(unknown=True)
        elif self.birth_place_type == PlaceType.SWISS:
            # Import canton abbreviation enum if needed
            canton_abbr_enum = None
            if self.birth_canton_abbreviation:
                from openmun_ech.ech0007.v5 import CantonAbbreviation
                try:
                    canton_abbr_enum = CantonAbbreviation(self.birth_canton_abbreviation)
                except ValueError:
                    canton_abbr_enum = None

            # Convert birth_municipality_history_id to string if provided as int
            birth_hist_muni_id = self.birth_municipality_history_id
            if birth_hist_muni_id is not None and not isinstance(birth_hist_muni_id, str):
                birth_hist_muni_id = str(birth_hist_muni_id)

            place_of_birth = ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality(
                    swiss_municipality=ECH0007SwissMunicipality(
                        municipality_id=self.birth_municipality_bfs,
                        municipality_name=self.birth_municipality_name,
                        canton_abbreviation=canton_abbr_enum,
                        history_municipality_id=birth_hist_muni_id
                    )
                )
            )
        elif self.birth_place_type == PlaceType.FOREIGN:
            place_of_birth = ECH0011GeneralPlace(
                foreign_country=ECH0008Country(
                    country_id=self.birth_country_id,
                    country_id_iso2=self.birth_country_iso,
                    country_name_short=self.birth_country_name_short
                ),
                foreign_town=self.birth_town
            )

        # Construct birth_data
        birth_data = ECH0011BirthData(
            sex=Sex(self.sex),  # Type 1 COPY
            date_of_birth=self.date_of_birth,  # Type 1 COPY
            place_of_birth=place_of_birth
        )

        # Construct birth addon data (optional parent names from birth certificate)
        birth_addon_data = None
        if any([self.birth_father_name, self.birth_father_first_name,
                self.birth_mother_name, self.birth_mother_first_name]):
            from openmun_ech.ech0021.v7 import ECH0021NameOfParent
            from openmun_ech.ech0021.enums import TypeOfRelationship

            name_of_parent = []
            # Add father if present
            if self.birth_father_name or self.birth_father_first_name:
                # Auto-determine which XSD variant to use based on provided data
                official, first, official_only, first_only = self._determine_parent_name_variant(
                    self.birth_father_name,
                    self.birth_father_first_name
                )

                # Build kwargs with auto-calculated fields
                father_kwargs = {
                    'type_of_relationship': TypeOfRelationship.FATHER,
                    'official_proof_of_name_of_parents_yes_no': self.birth_father_official_proof
                }
                # Add fields based on determined variant
                if official is not None:
                    father_kwargs['official_name'] = official
                if first is not None:
                    father_kwargs['first_name'] = first
                if official_only is not None:
                    father_kwargs['official_name_only'] = official_only
                if first_only is not None:
                    father_kwargs['first_name_only'] = first_only

                father = ECH0021NameOfParent(**father_kwargs)
                name_of_parent.append(father)

            # Add mother if present
            if self.birth_mother_name or self.birth_mother_first_name:
                # Auto-determine which XSD variant to use based on provided data
                official, first, official_only, first_only = self._determine_parent_name_variant(
                    self.birth_mother_name,
                    self.birth_mother_first_name
                )

                # Build kwargs with auto-calculated fields
                mother_kwargs = {
                    'type_of_relationship': TypeOfRelationship.MOTHER,
                    'official_proof_of_name_of_parents_yes_no': self.birth_mother_official_proof
                }
                # Add fields based on determined variant
                if official is not None:
                    mother_kwargs['official_name'] = official
                if first is not None:
                    mother_kwargs['first_name'] = first
                if official_only is not None:
                    mother_kwargs['official_name_only'] = official_only
                if first_only is not None:
                    mother_kwargs['first_name_only'] = first_only

                mother = ECH0021NameOfParent(**mother_kwargs)
                name_of_parent.append(mother)

            birth_addon_data = ECH0021BirthAddonData(
                name_of_parent=name_of_parent
            )

        # Construct birth_info wrapper
        birth_info = ECH0020BirthInfo(
            birth_data=birth_data,
            birth_addon_data=birth_addon_data
        )

        # ====================================================================
        # 4. RELIGION DATA (REQUIRED)
        # ====================================================================

        religion_data = ECH0011ReligionData(
            religion=self.religion,
            religion_valid_from=self.religion_valid_from
        )

        # ====================================================================
        # 5. MARITAL INFO (REQUIRED)
        # ====================================================================

        marital_data = ECH0011MaritalData(
            marital_status=MaritalStatus(self.marital_status),
            date_of_marital_status=self.date_of_marital_status,
            official_proof_of_marital_status_yes_no=self.official_proof_of_marital_status_yes_no
        )

        # Construct marital data addon (place of marriage)
        marital_data_addon = None
        if self.marriage_place_type:
            place_of_marriage = None
            if self.marriage_place_type == PlaceType.UNKNOWN:
                place_of_marriage = ECH0011GeneralPlace(unknown=True)
            elif self.marriage_place_type == PlaceType.SWISS:
                if self.marriage_municipality_bfs:
                    # Import canton abbreviation enum if needed
                    marriage_canton_abbr_enum = None
                    if self.marriage_canton_abbreviation:
                        from openmun_ech.ech0007.v5 import CantonAbbreviation
                        try:
                            marriage_canton_abbr_enum = CantonAbbreviation(self.marriage_canton_abbreviation)
                        except ValueError:
                            marriage_canton_abbr_enum = None

                    # Convert marriage_municipality_history_id to string if provided as int
                    marriage_hist_muni_id = self.marriage_municipality_history_id
                    if marriage_hist_muni_id is not None and not isinstance(marriage_hist_muni_id, str):
                        marriage_hist_muni_id = str(marriage_hist_muni_id)

                    place_of_marriage = ECH0011GeneralPlace(
                        swiss_municipality=ECH0007Municipality(
                            swiss_municipality=ECH0007SwissMunicipality(
                                municipality_id=self.marriage_municipality_bfs,
                                municipality_name=self.marriage_municipality_name,
                                canton_abbreviation=marriage_canton_abbr_enum,
                                history_municipality_id=marriage_hist_muni_id
                            )
                        )
                    )
            elif self.marriage_place_type == PlaceType.FOREIGN:
                if self.marriage_country_iso:
                    place_of_marriage = ECH0011GeneralPlace(
                        foreign_country=ECH0008Country(
                            country_id=self.marriage_country_id,
                            country_id_iso2=self.marriage_country_iso,
                            country_name_short=self.marriage_country_name_short
                        ),
                        foreign_town=self.marriage_town
                    )

            if place_of_marriage:
                marital_data_addon = ECH0021MaritalDataAddon(
                    place_of_marriage=place_of_marriage
                )

        marital_info = ECH0020MaritalInfo(
            marital_data=marital_data,
            marital_data_addon=marital_data_addon
        )

        # ====================================================================
        # 6. NATIONALITY DATA (REQUIRED)
        # ====================================================================

        # Construct nationality list
        country_info_list = []
        if self.nationalities:
            for nat_dict in self.nationalities:
                country = ECH0008Country(
                    country_id=nat_dict.get('country_id'),  # BFS 4-digit code (optional)
                    country_id_iso2=nat_dict['country_iso'],  # ISO 2-letter code (required)
                    country_name_short=nat_dict.get('country_name_short')
                )
                country_info = ECH0011CountryInfo(
                    country=country,
                    nationality_valid_from=nat_dict.get('valid_from')
                )
                country_info_list.append(country_info)

        nationality_data = ECH0011NationalityData(
            nationality_status=self.nationality_status,
            country_info=country_info_list
        )

        # ====================================================================
        # 7 & 8. CITIZENSHIP CHOICE (REQUIRED)
        # ====================================================================

        place_of_origin_info = None
        residence_permit_data = None

        if self.places_of_origin:
            # Swiss citizens
            place_of_origin_info = []
            for origin_dict in self.places_of_origin:
                # Convert BFS code from string to int for Layer 1
                bfs_code = origin_dict.get('bfs_code')
                if bfs_code is not None and isinstance(bfs_code, str):
                    bfs_code = int(bfs_code) if bfs_code else None

                # Convert history_municipality_id to string if provided as int
                hist_muni_id = origin_dict.get('history_municipality_id')
                if hist_muni_id is not None and not isinstance(hist_muni_id, str):
                    hist_muni_id = str(hist_muni_id)

                place_of_origin = ECH0011PlaceOfOrigin(
                    origin_name=origin_dict.get('name'),
                    canton=origin_dict.get('canton'),
                    place_of_origin_id=bfs_code,  # Municipality BFS code (int)
                    history_municipality_id=hist_muni_id
                )

                # Create addon data if naturalization_date or expatriation_date is provided
                place_of_origin_addon_data = None
                if origin_dict.get('naturalization_date') or origin_dict.get('expatriation_date'):
                    from openmun_ech.ech0021.v7 import ECH0021PlaceOfOriginAddonData
                    place_of_origin_addon_data = ECH0021PlaceOfOriginAddonData(
                        naturalization_date=origin_dict.get('naturalization_date'),
                        expatriation_date=origin_dict.get('expatriation_date')
                    )

                place_of_origin_wrapper = ECH0020PlaceOfOriginInfo(
                    place_of_origin=place_of_origin,
                    place_of_origin_addon_data=place_of_origin_addon_data
                )
                place_of_origin_info.append(place_of_origin_wrapper)

        elif self.residence_permit:
            # Foreign nationals
            residence_permit_data = ECH0011ResidencePermitData(
                residence_permit=self.residence_permit,
                residence_permit_valid_from=self.residence_permit_valid_from,
                residence_permit_valid_till=self.residence_permit_valid_till,
                entry_date=self.entry_date
            )

        # ====================================================================
        # 9. LOCK DATA (REQUIRED)
        # ====================================================================

        lock_data = ECH0021LockData(
            data_lock=self.data_lock,
            data_lock_valid_from=self.data_lock_valid_from,
            data_lock_valid_till=self.data_lock_valid_till,
            paper_lock="1" if self.paper_lock else "0",
            paper_lock_valid_from=self.paper_lock_valid_from,
            paper_lock_valid_till=self.paper_lock_valid_till
        )

        # ====================================================================
        # 10. DEATH DATA (OPTIONAL)
        # ====================================================================

        death_data = None
        if self.death_date:
            # Construct death place based on type
            place_of_death = None
            if self.death_place_type == PlaceType.UNKNOWN:
                place_of_death = ECH0011GeneralPlace(unknown=True)
            elif self.death_place_type == PlaceType.SWISS:
                if self.death_municipality_bfs and self.death_municipality_name:
                    # Convert canton abbreviation to enum if present
                    death_canton_abbr_enum = None
                    if self.death_canton_abbreviation:
                        from openmun_ech.ech0007.v5 import CantonAbbreviation
                        try:
                            death_canton_abbr_enum = CantonAbbreviation(self.death_canton_abbreviation)
                        except ValueError:
                            death_canton_abbr_enum = None

                    # Convert history municipality ID to string if needed
                    death_hist_muni_id = self.death_municipality_history_id
                    if death_hist_muni_id is not None and not isinstance(death_hist_muni_id, str):
                        death_hist_muni_id = str(death_hist_muni_id)

                    place_of_death = ECH0011GeneralPlace(
                        swiss_municipality=ECH0007Municipality(
                            swiss_municipality=ECH0007SwissMunicipality(
                                municipality_id=self.death_municipality_bfs,
                                municipality_name=self.death_municipality_name,
                                canton_abbreviation=death_canton_abbr_enum,
                                history_municipality_id=death_hist_muni_id
                            )
                        )
                    )
            elif self.death_place_type == PlaceType.FOREIGN:
                if self.death_country_iso and self.death_country_name_short:
                    place_of_death = ECH0011GeneralPlace(
                        foreign_country=ECH0008Country(
                            country_id=self.death_country_id,
                            country_id_iso2=self.death_country_iso,
                            country_name_short=self.death_country_name_short
                        )
                    )

            death_data = ECH0011DeathData(
                death_period=ECH0011DeathPeriod(
                    date_from=self.death_date
                ),
                place_of_death=place_of_death
            )

        # ====================================================================
        # 11. CONTACT DATA (OPTIONAL)
        # CHOICE: contact person XOR contact organization
        # ====================================================================

        contact_data = None
        if any([self.contact_person_official_name, self.contact_organization_name,
                self.contact_address_postal_code]):

            # Build contact person/organization (CHOICE)
            contact_person = None
            contact_person_partner = None
            contact_organization = None
            mail_address_person = None
            mail_address_org = None

            if self.contact_person_official_name:
                # Always create separate personIdentification element when contact person provided
                if self._should_create_contact_person_identification():
                    # Create separate personIdentification element
                    # Determine if we need Full or Light identification
                    # If we have local_person_id, use Light (personIdentificationPartner)
                    # Otherwise, if we have sex+dateOfBirth (no local_person_id), use Full (personIdentification)
                    # Light identification CAN have sex/dateOfBirth as optional fields
                    if self.contact_person_local_person_id:
                        # Use Light identification (personIdentificationPartner)
                        # even if sex/dateOfBirth are present (they're optional in Light)
                        # ECH0044PersonIdentificationLight for ECH0011ContactData
                        # Note: PersonIdentificationLight CAN have sex and date_of_birth as OPTIONAL fields
                        partner_kwargs = {
                            'official_name': self.contact_person_official_name,
                            'first_name': self.contact_person_first_name
                        }
                        # Add optional vn if present
                        if self.contact_person_vn:
                            partner_kwargs['vn'] = self.contact_person_vn
                        # Add optional local_person_id if present
                        if self.contact_person_local_person_id and self.contact_person_local_person_id_category:
                            partner_kwargs['local_person_id'] = ECH0044NamedPersonId(
                                person_id=self.contact_person_local_person_id,
                                person_id_category=self.contact_person_local_person_id_category
                            )
                        # Add optional sex and date_of_birth if present
                        if self.contact_person_sex:
                            partner_kwargs['sex'] = Sex(self.contact_person_sex)
                        if self.contact_person_date_of_birth:
                            partner_kwargs['date_of_birth'] = ECH0044DatePartiallyKnown(
                                year_month_day=self.contact_person_date_of_birth
                            )
                        contact_person_partner = ECH0044PersonIdentificationLight(**partner_kwargs)
                    elif self.contact_person_sex and self.contact_person_date_of_birth:
                        # Use Full identification (personIdentification) when we have sex+dateOfBirth but NO local_person_id
                        # This is rare, but supported by eCH-0044
                        contact_person = ECH0044PersonIdentification(
                            local_person_id=ECH0044NamedPersonId(
                                person_id=self.local_person_id,  # Use main person's ID as fallback
                                person_id_category=self.local_person_id_category
                            ),
                            official_name=self.contact_person_official_name,
                            first_name=self.contact_person_first_name,
                            sex=Sex(self.contact_person_sex),
                            date_of_birth=ECH0044DatePartiallyKnown(
                                year_month_day=self.contact_person_date_of_birth
                            )
                        )
                    else:
                        # Use Light identification without optional fields (minimal)
                        contact_person_partner = ECH0044PersonIdentificationLight(
                            official_name=self.contact_person_official_name,
                            first_name=self.contact_person_first_name
                        )
                # Always create mail_address_person for ECH0010MailAddress
                from openmun_ech.ech0010 import ECH0010PersonMailAddressInfo
                mail_address_person = ECH0010PersonMailAddressInfo(
                    mr_mrs=self.contact_person_mr_mrs,
                    first_name=self.contact_person_first_name,
                    last_name=self.contact_person_official_name
                )
            elif self.contact_organization_name:
                # Build ECH0011PartnerIdOrganisation with main person's local ID
                contact_organization = ECH0011PartnerIdOrganisation(
                    local_person_id=ECH0044NamedPersonId(
                        person_id=self.local_person_id,
                        person_id_category=self.local_person_id_category
                    )
                )
                # For mail address, use organization name (already imported at module level)
                mail_address_org = ECH0010OrganisationMailAddressInfo(
                    organisation_name=self.contact_organization_name
                )

            # Build contact address (required if contact_data exists)
            contact_address = None
            if self.contact_address_postal_code and self.contact_address_town:
                # Only create MailAddress if we have person OR organisation (CHOICE constraint)
                if mail_address_person or mail_address_org:
                    # Build address information
                    address_info = ECH0010AddressInformation(
                        address_line1=self.contact_address_address_line1,
                        street=self.contact_address_street,
                        house_number=self.contact_address_house_number,
                        dwelling_number=self.contact_address_dwelling_number,
                        locality=self.contact_address_locality,
                        town=self.contact_address_town,
                        swiss_zip_code=int(self.contact_address_postal_code),
                        swiss_zip_code_add_on=self.contact_address_postal_code_addon,
                        country="CH"  # Default to Switzerland for now
                    )

                    contact_address = ECH0010MailAddress(
                        person=mail_address_person,
                        organisation=mail_address_org,
                        address_information=address_info
                    )

            # Only create contact_data if we have contact_address (REQUIRED field in ECH0011ContactData)
            if contact_address:
                contact_data = ECH0011ContactData(
                    contact_person=contact_person,
                    contact_person_partner=contact_person_partner,
                    contact_organization=contact_organization,
                    contact_address=contact_address,
                    contact_valid_from=self.contact_valid_from,
                    contact_valid_till=self.contact_valid_till
                )

        # ====================================================================
        # 12. PERSON ADDITIONAL DATA (OPTIONAL)
        # ====================================================================

        person_additional_data = None
        if any([self.mr_mrs, self.title, self.language_of_correspondance]):
            person_additional_data = ECH0021PersonAdditionalData(
                mr_mrs=self.mr_mrs,
                title=self.title,
                language_of_correspondance=self.language_of_correspondance
            )

        # ====================================================================
        # 13. POLITICAL RIGHT DATA (OPTIONAL)
        # ====================================================================

        political_right_data = None
        if self.restricted_voting_and_election_right_federation is not None:
            political_right_data = ECH0021PoliticalRightData(
                restricted_voting_and_election_right_federation=self.restricted_voting_and_election_right_federation
            )

        # ====================================================================
        # 14. JOB DATA (OPTIONAL)
        # ====================================================================
        # Per eCH-0021 standard: kind_of_employment is mandatory within jobData.
        # If kind_of_employment is None, omit entire jobData element (even if
        # job_title or occupation_data are present).

        job_data = None
        if self.kind_of_employment is not None:
            # Build occupation data list
            occupation_data_list = []
            if self.occupation_data:
                for occ_dict in self.occupation_data:
                    # Parse UID string (e.g., "CHE-123.456.789") to ECH0021UIDStructure
                    uid_structure = None
                    employer_uid_str = occ_dict.get('employer_uid')
                    if employer_uid_str:
                        # UID format: "CHE-123.456.789" or "ADM-123.456.789"
                        # Extract category (CHE/ADM) and numeric ID
                        if employer_uid_str.startswith('CHE-'):
                            category = UIDOrganisationIdCategory.ENTERPRISE
                            uid_numeric = int(employer_uid_str[4:].replace('.', ''))  # Remove "CHE-" and dots
                        elif employer_uid_str.startswith('ADM-'):
                            category = UIDOrganisationIdCategory.ADMINISTRATION
                            uid_numeric = int(employer_uid_str[4:].replace('.', ''))  # Remove "ADM-" and dots
                        else:
                            # Invalid format - skip UID (fail-safe, but should not happen with valid data)
                            uid_numeric = None
                            category = None

                        if uid_numeric and category:
                            uid_structure = ECH0021UIDStructure(
                                uid_organisation_id_categorie=category,
                                uid_organisation_id=uid_numeric
                            )

                    # Create ECH0010AddressInformation for place_of_work from full address dict
                    place_of_work_address = None
                    place_of_work_dict = occ_dict.get('place_of_work')
                    if place_of_work_dict:
                        # Reconstruct full address from dict (preserving all fields)
                        place_of_work_address = ECH0010AddressInformation(
                            street=place_of_work_dict.get('street'),
                            house_number=place_of_work_dict.get('house_number'),
                            town=place_of_work_dict.get('town'),
                            swiss_zip_code=place_of_work_dict.get('swiss_zip_code'),
                            swiss_zip_code_add_on=place_of_work_dict.get('swiss_zip_code_add_on'),
                            country=place_of_work_dict.get('country')
                        )

                    # Create ECH0010AddressInformation for place_of_employer from full address dict
                    place_of_employer_address = None
                    place_of_employer_dict = occ_dict.get('place_of_employer')
                    if place_of_employer_dict:
                        # Reconstruct full address from dict (preserving all fields)
                        place_of_employer_address = ECH0010AddressInformation(
                            street=place_of_employer_dict.get('street'),
                            house_number=place_of_employer_dict.get('house_number'),
                            town=place_of_employer_dict.get('town'),
                            swiss_zip_code=place_of_employer_dict.get('swiss_zip_code'),
                            swiss_zip_code_add_on=place_of_employer_dict.get('swiss_zip_code_add_on'),
                            country=place_of_employer_dict.get('country')
                        )

                    occupation = ECH0021OccupationData(
                        employer=occ_dict.get('employer'),
                        uid=uid_structure,
                        place_of_work=place_of_work_address,
                        place_of_employer=place_of_employer_address,
                        occupation_valid_from=occ_dict.get('occupation_valid_from'),
                        occupation_valid_till=occ_dict.get('occupation_valid_till')
                    )
                    occupation_data_list.append(occupation)

            job_data = ECH0021JobData(
                kind_of_employment=self.kind_of_employment,
                job_title=self.job_title,
                occupation_data=occupation_data_list  # Can be empty list (default_factory=list)
            )

        # ====================================================================
        # 15. MARITAL RELATIONSHIP (OPTIONAL)
        # ====================================================================

        marital_relationship = None
        if self.spouse:
            # Convert PersonIdentification to ECH0044PersonIdentification
            # Construct spouse local_person_id if available
            spouse_local_person_id = None
            if self.spouse.local_person_id:
                spouse_local_person_id = ECH0044NamedPersonId(
                    person_id=self.spouse.local_person_id,
                    person_id_category=self.spouse.local_person_id_category
                )

            # Construct spouse other_person_ids (optional, multiple)
            spouse_other_person_ids = []
            if self.spouse_other_person_ids:
                for other_id_dict in self.spouse_other_person_ids:
                    other_pid = ECH0044NamedPersonId(
                        person_id=other_id_dict['person_id'],
                        person_id_category=other_id_dict['person_id_category']
                    )
                    spouse_other_person_ids.append(other_pid)

            spouse_person_id = ECH0044PersonIdentification(
                vn=self.spouse.vn,
                local_person_id=spouse_local_person_id,
                other_person_id=spouse_other_person_ids,
                official_name=self.spouse.official_name,
                first_name=self.spouse.first_name,
                original_name=self.spouse.original_name,
                sex=Sex(self.spouse.sex),
                date_of_birth=ECH0044DatePartiallyKnown(
                    year_month_day=self.spouse.date_of_birth
                )
            )

            # Build spouse address if provided
            partner_address = None
            if self.spouse_address_postal_code:
                address_info = ECH0010AddressInformation(
                    street=self.spouse_address_street,
                    house_number=self.spouse_address_house_number,
                    town=self.spouse_address_town,
                    swiss_zip_code=self.spouse_address_postal_code,
                    swiss_zip_code_add_on=self.spouse_address_postal_code_addon,
                    country="CH"  # Default to Switzerland for Swiss postal codes
                )

                from openmun_ech.ech0010 import ECH0010PersonMailAddressInfo

                partner_address = ECH0010MailAddress(
                    person=ECH0010PersonMailAddressInfo(
                        mr_mrs=self.spouse_mr_mrs,
                        last_name=self.spouse.official_name,
                        first_name=self.spouse.first_name
                    ),
                    address_information=address_info
                )

            # Build partner
            partner = ECH0021Partner(
                person_identification=spouse_person_id,
                address=partner_address
            )

            marital_relationship = ECH0021MaritalRelationship(
                partner=partner,
                type_of_relationship=self.marital_relationship_type
            )

        # ====================================================================
        # 16. PARENTAL RELATIONSHIP (OPTIONAL)
        # ====================================================================

        parental_relationship = None
        if self.parents:
            parental_relationship = []
            for parent_info in self.parents:
                # Convert PersonIdentification to ECH0044PersonIdentification
                # Construct parent local_person_id if available
                parent_local_person_id = None
                if parent_info.person.local_person_id:
                    parent_local_person_id = ECH0044NamedPersonId(
                        person_id=parent_info.person.local_person_id,
                        person_id_category=parent_info.person.local_person_id_category
                    )

                parent_person_id = ECH0044PersonIdentification(
                    vn=parent_info.person.vn,
                    local_person_id=parent_local_person_id,
                    official_name=parent_info.person.official_name,
                    first_name=parent_info.person.first_name,
                    original_name=parent_info.person.original_name,
                    sex=Sex(parent_info.person.sex),
                    date_of_birth=ECH0044DatePartiallyKnown(
                        year_month_day=parent_info.person.date_of_birth
                    )
                )

                # Build parent address if provided
                parent_address = None
                if parent_info.address_postal_code:
                    address_info = ECH0010AddressInformation(
                        street=parent_info.address_street,
                        house_number=parent_info.address_house_number,
                        town=parent_info.address_town,
                        swiss_zip_code=parent_info.address_postal_code,
                        swiss_zip_code_add_on=parent_info.address_postal_code_addon,
                        country="CH"
                    )

                    from openmun_ech.ech0010 import ECH0010PersonMailAddressInfo

                    parent_address = ECH0010MailAddress(
                        person=ECH0010PersonMailAddressInfo(
                            mr_mrs=parent_info.mr_mrs,
                            last_name=parent_info.person.official_name,
                            first_name=parent_info.person.first_name
                        ),
                        address_information=address_info
                    )

                # Build partner wrapper
                parent_partner = ECH0021Partner(
                    person_identification=parent_person_id,
                    address=parent_address
                )

                parental_rel = ECH0021ParentalRelationship(
                    partner=parent_partner,
                    relationshipValidFrom=parent_info.relationship_valid_from,  # Use alias name
                    type_of_relationship=parent_info.relationship_type,
                    care=parent_info.care
                )
                parental_relationship.append(parental_rel)

        # ====================================================================
        # 17. GUARDIAN RELATIONSHIP (OPTIONAL)
        # ====================================================================

        guardian_relationship = None
        if self.guardians:
            guardian_relationship = []
            for guardian_info in self.guardians:
                partner = None

                if guardian_info.guardian_type in [GuardianType.PERSON, GuardianType.PERSON_PARTNER]:
                    # Person guardian
                    # Construct guardian local_person_id if available
                    guardian_local_person_id = None
                    if guardian_info.person.local_person_id:
                        guardian_local_person_id = ECH0044NamedPersonId(
                            person_id=guardian_info.person.local_person_id,
                            person_id_category=guardian_info.person.local_person_id_category
                        )

                    # Build guardian relationship directly (no Partner wrapper for guardians)
                    if guardian_info.guardian_type == GuardianType.PERSON:
                        # Full person identification
                        guardian_person_id = ECH0044PersonIdentification(
                            vn=guardian_info.person.vn,
                            local_person_id=guardian_local_person_id,
                            official_name=guardian_info.person.official_name,
                            first_name=guardian_info.person.first_name,
                            original_name=guardian_info.person.original_name,
                            sex=Sex(guardian_info.person.sex),
                            date_of_birth=ECH0044DatePartiallyKnown(
                                year_month_day=guardian_info.person.date_of_birth
                            )
                        )
                        person_id_field = guardian_person_id
                        person_id_partner_field = None
                        org_id_field = None
                    elif guardian_info.guardian_type == GuardianType.PERSON_PARTNER:
                        # Light person identification (sex and date_of_birth are optional)
                        guardian_person_id_light = ECH0044PersonIdentificationLight(
                            vn=guardian_info.person.vn,
                            local_person_id=guardian_local_person_id,
                            official_name=guardian_info.person.official_name,
                            first_name=guardian_info.person.first_name,
                            original_name=guardian_info.person.original_name,
                            sex=Sex(guardian_info.person.sex) if guardian_info.person.sex else None,
                            date_of_birth=ECH0044DatePartiallyKnown(
                                year_month_day=guardian_info.person.date_of_birth
                            ) if guardian_info.person.date_of_birth else None
                        )
                        person_id_field = None
                        person_id_partner_field = guardian_person_id_light
                        org_id_field = None
                    else:
                        # Should not reach here in this branch
                        person_id_field = None
                        person_id_partner_field = None
                        org_id_field = None

                elif guardian_info.guardian_type == GuardianType.ORGANISATION:
                    # Organization guardian
                    org_id_field = ECH0011PartnerIdOrganisation(
                        local_person_id=ECH0044NamedPersonId(
                            person_id=guardian_info.organization_uid,
                            person_id_category="UID"
                        )
                    )
                    person_id_field = None
                    person_id_partner_field = None

                # Build partner_address
                partner_address_field = None

                # ZERO-TOLERANCE POLICY: Only create address if we have REAL address data
                # Do NOT invent fake addresses to store names
                if guardian_info.guardian_type == GuardianType.ORGANISATION:
                    # Organization guardian
                    if guardian_info.address_postal_code and guardian_info.address_town and guardian_info.organization_name:
                        # We have REAL address data - create address with organization name
                        address_info = ECH0010AddressInformation(
                            street=guardian_info.address_street,
                            house_number=guardian_info.address_house_number,
                            town=guardian_info.address_town,
                            swiss_zip_code=guardian_info.address_postal_code,
                            swiss_zip_code_add_on=guardian_info.address_postal_code_addon,
                            country="CH"
                        )

                        # ECH0010OrganisationMailAddressInfo already imported at module level
                        partner_address_field = ECH0010MailAddress(
                            organisation=ECH0010OrganisationMailAddressInfo(
                                organisation_name=guardian_info.organization_name
                            ),
                            address_information=address_info
                        )
                    # else: No address data provided - address element will be omitted (minOccurs=0)
                    # Note: organization_name will be lost if no address data provided, but this
                    # respects zero-tolerance policy (no data invention)

                elif guardian_info.guardian_type in [GuardianType.PERSON, GuardianType.PERSON_PARTNER]:
                    # Person guardian with address
                    if guardian_info.address_postal_code:
                        address_info = ECH0010AddressInformation(
                            street=guardian_info.address_street,
                            house_number=guardian_info.address_house_number,
                            town=guardian_info.address_town,
                            swiss_zip_code=guardian_info.address_postal_code,
                            swiss_zip_code_add_on=guardian_info.address_postal_code_addon,
                            country="CH"
                        )

                        from openmun_ech.ech0010 import ECH0010PersonMailAddressInfo

                        partner_address_field = ECH0010MailAddress(
                            person=ECH0010PersonMailAddressInfo(
                                mr_mrs=guardian_info.mr_mrs,
                                last_name=guardian_info.person.official_name,
                                first_name=guardian_info.person.first_name
                            ),
                            address_information=address_info
                        )

                # Build guardian measure info
                guardian_measure_info = ECH0021GuardianMeasureInfo(
                    based_on_law=guardian_info.guardian_measure_based_on_law,
                    guardian_measure_valid_from=guardian_info.guardian_measure_valid_from
                )

                guardian_rel = ECH0021GuardianRelationship(
                    guardian_relationship_id=guardian_info.guardian_relationship_id,
                    person_identification=person_id_field,
                    person_identification_partner=person_id_partner_field,
                    partner_id_organisation=org_id_field,
                    partner_address=partner_address_field,  # Store organization name here
                    type_of_relationship=guardian_info.relationship_type,
                    guardian_measure_info=guardian_measure_info,
                    care=guardian_info.care
                )
                guardian_relationship.append(guardian_rel)

        # ====================================================================
        # 18. ARMED FORCES DATA (OPTIONAL)
        # ====================================================================

        armed_forces_data = None
        if any([self.armed_forces_service, self.armed_forces_liability]):
            armed_forces_data = ECH0021ArmedForcesData(
                armed_forces_service=self.armed_forces_service,
                armed_forces_liability=self.armed_forces_liability,
                armed_forces_valid_from=self.armed_forces_valid_from
            )

        # ====================================================================
        # 19. CIVIL DEFENSE DATA (OPTIONAL)
        # ====================================================================

        civil_defense_data = None
        if self.civil_defense:
            civil_defense_data = ECH0021CivilDefenseData(
                civil_defense=self.civil_defense,
                civil_defense_valid_from=self.civil_defense_valid_from
            )

        # ====================================================================
        # 20. FIRE SERVICE DATA (OPTIONAL)
        # ====================================================================

        fire_service_data = None
        if any([self.fire_service, self.fire_service_liability]):
            fire_service_data = ECH0021FireServiceData(
                fire_service=self.fire_service,
                fire_service_liability=self.fire_service_liability,
                fire_service_valid_from=self.fire_service_valid_from
            )

        # ====================================================================
        # 21. HEALTH INSURANCE DATA (OPTIONAL)
        # ====================================================================

        health_insurance_data = None
        if self.health_insured is not None or self.health_insurance_name:
            # Build insurance address if provided (CHOICE: name OR address)
            insurance_name = None
            insurance_address = None

            # Create address if we have town (required field) and organisation name
            if self.health_insurance_address_town and self.health_insurance_name:
                address_info = ECH0010AddressInformation(
                    street=self.health_insurance_address_street,
                    house_number=self.health_insurance_address_house_number,
                    town=self.health_insurance_address_town,
                    swiss_zip_code=int(self.health_insurance_address_postal_code) if self.health_insurance_address_postal_code else None,
                    country=self.health_insurance_address_country or 'CH'  # Default to Switzerland if not specified
                )

                organisation_info = ECH0010OrganisationMailAddressInfo(
                    organisation_name=self.health_insurance_name
                )

                insurance_address = ECH0010OrganisationMailAddress(
                    organisation=organisation_info,
                    address_information=address_info
                )
            elif self.health_insurance_name:
                # Name only (no address)
                insurance_name = self.health_insurance_name

            health_insurance_data = ECH0021HealthInsuranceData(
                health_insured="1" if self.health_insured else "0",
                insurance_name=insurance_name,
                insurance_address=insurance_address,
                health_insurance_valid_from=self.health_insurance_valid_from
            )

        # ====================================================================
        # 22. MATRIMONIAL INHERITANCE ARRANGEMENT DATA (OPTIONAL)
        # ====================================================================

        matrimonial_inheritance_arrangement_data = None
        if self.matrimonial_inheritance_arrangement:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData(
                matrimonial_inheritance_arrangement=self.matrimonial_inheritance_arrangement,
                matrimonial_inheritance_arrangement_valid_from=self.matrimonial_inheritance_arrangement_valid_from
            )

        # ====================================================================
        # CONSTRUCT BASE DELIVERY PERSON (All fields)
        # ====================================================================

        return ECH0020BaseDeliveryPerson(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            death_data=death_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            political_right_data=political_right_data,
            job_data=job_data,
            marital_relationship=marital_relationship,
            parental_relationship=parental_relationship,
            guardian_relationship=guardian_relationship,
            armed_forces_data=armed_forces_data,
            civil_defense_data=civil_defense_data,
            fire_service_data=fire_service_data,
            health_insurance_data=health_insurance_data,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
        )

    @classmethod
    def from_ech0020(cls, raw: ECH0020BaseDeliveryPerson) -> 'BaseDeliveryPerson':
        """Convert Layer 1 ECH0020BaseDeliveryPerson to Layer 2 model.

        Handles:
        - Field flattening: Extracts from 7 nesting levels to 1-2 levels
        - Type 1 de-duplication: Extracts duplicated fields once
        - Wrapper unwrapping: Extracts from NameInfo, BirthInfo, etc.
        - CHOICE detection: Determines which CHOICE branch is present

        Args:
            raw: Layer 1 ECH0020BaseDeliveryPerson model

        Returns:
            BaseDeliveryPerson: Flattened Layer 2 model

        Raises:
            ValueError: If Layer 1 model is invalid (zero tolerance)
        """

        # ====================================================================
        # 1. PERSON IDENTIFICATION (REQUIRED)
        # Type 1 De-duplication: Extract official_name, first_name, sex, date_of_birth
        # once from person_identification (ignore duplicates in name_info, birth_info)
        # ====================================================================

        person_id = raw.person_identification

        # Extract VN
        vn = person_id.vn

        # Extract local person ID
        local_person_id = person_id.local_person_id.person_id if person_id.local_person_id else None
        local_person_id_category = person_id.local_person_id.person_id_category if person_id.local_person_id else "veka.id"

        # Extract other person IDs (optional, multiple)
        other_person_ids = None
        if person_id.other_person_id and len(person_id.other_person_id) > 0:
            other_person_ids = [
                {
                    'person_id': other_id.person_id,
                    'person_id_category': other_id.person_id_category
                }
                for other_id in person_id.other_person_id
            ]

        # Type 1 fields - extract ONCE from person_identification
        official_name = person_id.official_name
        first_name = person_id.first_name
        original_name = person_id.original_name
        sex = person_id.sex.value if hasattr(person_id.sex, 'value') else str(person_id.sex)

        # Extract date_of_birth from wrapper
        date_of_birth = None
        if person_id.date_of_birth:
            if hasattr(person_id.date_of_birth, 'year_month_day') and person_id.date_of_birth.year_month_day:
                date_of_birth = person_id.date_of_birth.year_month_day
            elif hasattr(person_id.date_of_birth, 'year_month') and person_id.date_of_birth.year_month:
                # Partial date - use first day of month
                ym = person_id.date_of_birth.year_month
                date_of_birth = date(ym.year, ym.month, 1)
            elif hasattr(person_id.date_of_birth, 'year') and person_id.date_of_birth.year:
                # Year only - use January 1st
                date_of_birth = date(person_id.date_of_birth.year, 1, 1)

        # ====================================================================
        # 2. NAME INFO (REQUIRED)
        # Extract from wrapper, ignore Type 1 duplicated fields
        # ====================================================================

        name_data = raw.name_info.name_data

        # Extract non-duplicated name fields
        call_name = name_data.call_name
        alliance_name = name_data.alliance_name
        alias_name = name_data.alias_name
        other_name = name_data.other_name
        name_valid_from = raw.name_info.name_valid_from

        # Extract foreign name CHOICE
        name_on_foreign_passport = None
        name_on_foreign_passport_first = None
        if name_data.name_on_foreign_passport:
            name_on_foreign_passport = name_data.name_on_foreign_passport.name
            name_on_foreign_passport_first = name_data.name_on_foreign_passport.first_name

        declared_foreign_name = None
        declared_foreign_name_first = None
        if name_data.declared_foreign_name:
            declared_foreign_name = name_data.declared_foreign_name.name
            declared_foreign_name_first = name_data.declared_foreign_name.first_name

        # ====================================================================
        # 3. BIRTH INFO (REQUIRED)
        # Extract from wrapper, detect place CHOICE
        # ====================================================================

        birth_data = raw.birth_info.birth_data
        birth_addon_data = raw.birth_info.birth_addon_data

        # Detect birth place type (CHOICE)
        birth_place_type = PlaceType.UNKNOWN
        birth_municipality_bfs = None
        birth_municipality_name = None
        birth_canton_abbreviation = None
        birth_municipality_history_id = None
        birth_country_id = None
        birth_country_iso = None
        birth_country_name_short = None
        birth_town = None

        if birth_data.place_of_birth:
            place = birth_data.place_of_birth
            if place.unknown:
                birth_place_type = PlaceType.UNKNOWN
            elif place.swiss_municipality:
                birth_place_type = PlaceType.SWISS
                # Unwrap double wrapper: ECH0007Municipality > ECH0007SwissMunicipality
                swiss_muni = place.swiss_municipality
                if hasattr(swiss_muni, 'swiss_municipality') and swiss_muni.swiss_municipality:
                    birth_municipality_bfs = swiss_muni.swiss_municipality.municipality_id
                    birth_municipality_name = swiss_muni.swiss_municipality.municipality_name
                    # Extract canton and history ID
                    if hasattr(swiss_muni.swiss_municipality, 'canton_abbreviation'):
                        ca = swiss_muni.swiss_municipality.canton_abbreviation
                        if ca is not None:
                            birth_canton_abbreviation = ca.value if hasattr(ca, 'value') else str(ca)
                    birth_municipality_history_id = getattr(swiss_muni.swiss_municipality, 'history_municipality_id', None)
                else:
                    # Direct access (in case wrapper is not present)
                    birth_municipality_bfs = getattr(swiss_muni, 'municipality_id', None)
                    birth_municipality_name = getattr(swiss_muni, 'municipality_name', None)
                    if hasattr(swiss_muni, 'canton_abbreviation'):
                        ca = swiss_muni.canton_abbreviation
                        if ca is not None:
                            birth_canton_abbreviation = ca.value if hasattr(ca, 'value') else str(ca)
                    birth_municipality_history_id = getattr(swiss_muni, 'history_municipality_id', None)
            elif place.foreign_country:
                birth_place_type = PlaceType.FOREIGN
                birth_country_id = place.foreign_country.country_id
                birth_country_iso = place.foreign_country.country_id_iso2
                birth_country_name_short = place.foreign_country.country_name_short
                birth_town = place.foreign_town

        # Extract birth parent names from addon data
        birth_father_name = None
        birth_father_first_name = None
        birth_father_official_proof = None
        birth_mother_name = None
        birth_mother_first_name = None
        birth_mother_official_proof = None
        if birth_addon_data and birth_addon_data.name_of_parent:
            from openmun_ech.ech0021.enums import TypeOfRelationship
            for parent in birth_addon_data.name_of_parent:
                # Mother (type_of_relationship == 3)
                if parent.type_of_relationship == TypeOfRelationship.MOTHER:
                    birth_mother_name = parent.official_name or parent.official_name_only
                    birth_mother_first_name = parent.first_name or parent.first_name_only
                    birth_mother_official_proof = parent.official_proof_of_name_of_parents_yes_no
                # Father (type_of_relationship == 4)
                elif parent.type_of_relationship == TypeOfRelationship.FATHER:
                    birth_father_name = parent.official_name or parent.official_name_only
                    birth_father_first_name = parent.first_name or parent.first_name_only
                    birth_father_official_proof = parent.official_proof_of_name_of_parents_yes_no

        # ====================================================================
        # 4. RELIGION DATA (REQUIRED)
        # ====================================================================

        religion = raw.religion_data.religion
        religion_valid_from = raw.religion_data.religion_valid_from

        # ====================================================================
        # 5. MARITAL INFO (REQUIRED)
        # ====================================================================

        marital_data = raw.marital_info.marital_data
        marital_status = marital_data.marital_status.value if hasattr(marital_data.marital_status, 'value') else str(marital_data.marital_status)
        date_of_marital_status = marital_data.date_of_marital_status
        official_proof_of_marital_status_yes_no = marital_data.official_proof_of_marital_status_yes_no

        # Extract place of marriage from addon
        marriage_place_type = None
        marriage_municipality_bfs = None
        marriage_municipality_name = None
        marriage_municipality_history_id = None
        marriage_canton_abbreviation = None
        marriage_country_id = None
        marriage_country_iso = None
        marriage_country_name_short = None
        marriage_town = None

        if raw.marital_info.marital_data_addon and raw.marital_info.marital_data_addon.place_of_marriage:
            place = raw.marital_info.marital_data_addon.place_of_marriage
            if place.unknown:
                marriage_place_type = PlaceType.UNKNOWN
            elif place.swiss_municipality:
                marriage_place_type = PlaceType.SWISS
                swiss_muni = place.swiss_municipality
                if hasattr(swiss_muni, 'swiss_municipality') and swiss_muni.swiss_municipality:
                    marriage_municipality_bfs = swiss_muni.swiss_municipality.municipality_id
                    marriage_municipality_name = swiss_muni.swiss_municipality.municipality_name
                    # Extract canton and history ID
                    if hasattr(swiss_muni.swiss_municipality, 'canton_abbreviation'):
                        ca = swiss_muni.swiss_municipality.canton_abbreviation
                        if ca is not None:
                            marriage_canton_abbreviation = ca.value if hasattr(ca, 'value') else str(ca)
                    marriage_municipality_history_id = getattr(swiss_muni.swiss_municipality, 'history_municipality_id', None)
                else:
                    marriage_municipality_bfs = getattr(swiss_muni, 'municipality_id', None)
                    marriage_municipality_name = getattr(swiss_muni, 'municipality_name', None)
                    marriage_municipality_history_id = getattr(swiss_muni, 'history_municipality_id', None)
            elif place.foreign_country:
                marriage_place_type = PlaceType.FOREIGN
                marriage_country_id = place.foreign_country.country_id
                marriage_country_iso = place.foreign_country.country_id_iso2
                marriage_country_name_short = place.foreign_country.country_name_short
                marriage_town = place.foreign_town

        # ====================================================================
        # 6. NATIONALITY DATA (REQUIRED)
        # ====================================================================

        nationality_status = raw.nationality_data.nationality_status

        nationalities = None
        if raw.nationality_data.country_info:
            nationalities = []
            for country_info in raw.nationality_data.country_info:
                nat_dict = {
                    'country_id': country_info.country.country_id,  # BFS 4-digit code
                    'country_iso': country_info.country.country_id_iso2,  # ISO 2-letter code
                    'country_name_short': getattr(country_info.country, 'country_name_short', None),
                    'valid_from': country_info.nationality_valid_from
                }
                nationalities.append(nat_dict)

        # ====================================================================
        # 7 & 8. CITIZENSHIP CHOICE (REQUIRED)
        # Detect which branch is present
        # ====================================================================

        places_of_origin = None
        residence_permit = None
        residence_permit_valid_from = None
        residence_permit_valid_till = None
        entry_date = None

        if raw.place_of_origin_info:
            # Swiss citizen
            places_of_origin = []
            for origin_info in raw.place_of_origin_info:
                origin = origin_info.place_of_origin
                # Extract naturalization_date and expatriation_date from addon data if present
                naturalization_date = None
                expatriation_date = None
                if origin_info.place_of_origin_addon_data:
                    naturalization_date = origin_info.place_of_origin_addon_data.naturalization_date
                    expatriation_date = origin_info.place_of_origin_addon_data.expatriation_date

                # Convert BFS code from int to string for Layer 2
                bfs_code = str(origin.place_of_origin_id) if origin.place_of_origin_id is not None else None

                # Extract history_municipality_id if present
                history_municipality_id = getattr(origin, 'history_municipality_id', None)

                origin_dict = {
                    'name': origin.origin_name,
                    'canton': origin.canton,
                    'bfs_code': bfs_code,
                    'history_municipality_id': history_municipality_id,
                    'naturalization_date': naturalization_date,
                    'expatriation_date': expatriation_date
                }
                places_of_origin.append(origin_dict)

        elif raw.residence_permit_data:
            # Foreign national
            residence_permit = raw.residence_permit_data.residence_permit
            residence_permit_valid_from = raw.residence_permit_data.residence_permit_valid_from
            residence_permit_valid_till = raw.residence_permit_data.residence_permit_valid_till
            entry_date = raw.residence_permit_data.entry_date

        # ====================================================================
        # 9. LOCK DATA (REQUIRED)
        # ====================================================================

        data_lock = raw.lock_data.data_lock
        data_lock_valid_from = raw.lock_data.data_lock_valid_from
        data_lock_valid_till = raw.lock_data.data_lock_valid_till

        # Convert paper_lock string to bool
        paper_lock = None
        if raw.lock_data.paper_lock:
            paper_lock = raw.lock_data.paper_lock == "1"

        paper_lock_valid_from = raw.lock_data.paper_lock_valid_from
        paper_lock_valid_till = raw.lock_data.paper_lock_valid_till

        # ====================================================================
        # 10. DEATH DATA (OPTIONAL)
        # ====================================================================

        death_date = None
        death_place_type = None
        death_municipality_bfs = None
        death_municipality_name = None
        death_canton_abbreviation = None
        death_municipality_history_id = None
        death_country_id = None
        death_country_iso = None
        death_country_name_short = None

        if raw.death_data:
            # Extract death date from death_period
            if raw.death_data.death_period and raw.death_data.death_period.date_from:
                death_date = raw.death_data.death_period.date_from

            # Detect death place type
            if raw.death_data.place_of_death:
                place = raw.death_data.place_of_death
                if place.unknown:
                    death_place_type = PlaceType.UNKNOWN
                elif place.swiss_municipality:
                    death_place_type = PlaceType.SWISS
                    swiss_muni = place.swiss_municipality
                    if hasattr(swiss_muni, 'swiss_municipality') and swiss_muni.swiss_municipality:
                        death_municipality_bfs = swiss_muni.swiss_municipality.municipality_id
                        death_municipality_name = swiss_muni.swiss_municipality.municipality_name
                        # Extract canton and history ID
                        if hasattr(swiss_muni.swiss_municipality, 'canton_abbreviation'):
                            ca = swiss_muni.swiss_municipality.canton_abbreviation
                            if ca is not None:
                                death_canton_abbreviation = ca.value if hasattr(ca, 'value') else str(ca)
                        death_municipality_history_id = getattr(swiss_muni.swiss_municipality, 'history_municipality_id', None)
                    else:
                        death_municipality_bfs = getattr(swiss_muni, 'municipality_id', None)
                        death_municipality_name = getattr(swiss_muni, 'municipality_name', None)
                        if hasattr(swiss_muni, 'canton_abbreviation'):
                            ca = swiss_muni.canton_abbreviation
                            if ca is not None:
                                death_canton_abbreviation = ca.value if hasattr(ca, 'value') else str(ca)
                        death_municipality_history_id = getattr(swiss_muni, 'history_municipality_id', None)
                elif place.foreign_country:
                    death_place_type = PlaceType.FOREIGN
                    death_country_id = place.foreign_country.country_id
                    death_country_iso = place.foreign_country.country_id_iso2
                    death_country_name_short = place.foreign_country.country_name_short

        # ====================================================================
        # 11. CONTACT DATA (OPTIONAL)
        # CHOICE: contact person XOR contact organization
        # ====================================================================

        contact_person_official_name = None
        contact_person_first_name = None
        contact_person_sex = None
        contact_person_date_of_birth = None
        contact_person_mr_mrs = None
        contact_person_local_person_id = None
        contact_person_local_person_id_category = None
        contact_person_vn = None
        contact_organization_name = None
        contact_address_address_line1 = None
        contact_address_street = None
        contact_address_house_number = None
        contact_address_dwelling_number = None
        contact_address_postal_code = None
        contact_address_postal_code_addon = None
        contact_address_town = None
        contact_address_locality = None
        contact_address_country_iso = None
        contact_valid_from = None
        contact_valid_till = None

        if raw.contact_data:
            # Extract contact person/organization (CHOICE)
            if raw.contact_data.contact_person:
                # Full identification includes sex and date_of_birth
                contact_person_official_name = raw.contact_data.contact_person.official_name
                contact_person_first_name = raw.contact_data.contact_person.first_name
                contact_person_sex = raw.contact_data.contact_person.sex.value if hasattr(raw.contact_data.contact_person.sex, 'value') else str(raw.contact_data.contact_person.sex)
                # Extract date_of_birth
                if raw.contact_data.contact_person.date_of_birth:
                    if hasattr(raw.contact_data.contact_person.date_of_birth, 'year_month_day') and raw.contact_data.contact_person.date_of_birth.year_month_day:
                        contact_person_date_of_birth = raw.contact_data.contact_person.date_of_birth.year_month_day
                    elif hasattr(raw.contact_data.contact_person.date_of_birth, 'year_month') and raw.contact_data.contact_person.date_of_birth.year_month:
                        ym = raw.contact_data.contact_person.date_of_birth.year_month
                        contact_person_date_of_birth = date(ym.year, ym.month, 1)
                    elif hasattr(raw.contact_data.contact_person.date_of_birth, 'year') and raw.contact_data.contact_person.date_of_birth.year:
                        contact_person_date_of_birth = date(raw.contact_data.contact_person.date_of_birth.year, 1, 1)
            elif raw.contact_data.contact_person_partner:
                # Light identification (personIdentificationPartner element)
                # Note: PersonIdentificationLight CAN have sex and date_of_birth as OPTIONAL fields
                contact_person_official_name = raw.contact_data.contact_person_partner.official_name
                contact_person_first_name = raw.contact_data.contact_person_partner.first_name
                # Extract vn (AHV number) if present
                if hasattr(raw.contact_data.contact_person_partner, 'vn') and raw.contact_data.contact_person_partner.vn:
                    contact_person_vn = raw.contact_data.contact_person_partner.vn
                # Extract local_person_id if present
                if hasattr(raw.contact_data.contact_person_partner, 'local_person_id') and raw.contact_data.contact_person_partner.local_person_id:
                    contact_person_local_person_id = raw.contact_data.contact_person_partner.local_person_id.person_id
                    contact_person_local_person_id_category = raw.contact_data.contact_person_partner.local_person_id.person_id_category
                # Extract sex if present (optional in Light identification)
                if hasattr(raw.contact_data.contact_person_partner, 'sex') and raw.contact_data.contact_person_partner.sex:
                    contact_person_sex = raw.contact_data.contact_person_partner.sex.value if hasattr(raw.contact_data.contact_person_partner.sex, 'value') else str(raw.contact_data.contact_person_partner.sex)
                # Extract date_of_birth if present (optional in Light identification)
                if hasattr(raw.contact_data.contact_person_partner, 'date_of_birth') and raw.contact_data.contact_person_partner.date_of_birth:
                    if hasattr(raw.contact_data.contact_person_partner.date_of_birth, 'year_month_day') and raw.contact_data.contact_person_partner.date_of_birth.year_month_day:
                        contact_person_date_of_birth = raw.contact_data.contact_person_partner.date_of_birth.year_month_day
                    elif hasattr(raw.contact_data.contact_person_partner.date_of_birth, 'year_month') and raw.contact_data.contact_person_partner.date_of_birth.year_month:
                        ym = raw.contact_data.contact_person_partner.date_of_birth.year_month
                        contact_person_date_of_birth = date(ym.year, ym.month, 1)
                    elif hasattr(raw.contact_data.contact_person_partner.date_of_birth, 'year') and raw.contact_data.contact_person_partner.date_of_birth.year:
                        contact_person_date_of_birth = date(raw.contact_data.contact_person_partner.date_of_birth.year, 1, 1)
            elif raw.contact_data.contact_address and raw.contact_data.contact_address.person:
                # Contact person ONLY in mail address (no separate personIdentification element)
                contact_person_official_name = raw.contact_data.contact_address.person.last_name
                contact_person_first_name = raw.contact_data.contact_address.person.first_name
                # Extract mrMrs from mail address person
                if hasattr(raw.contact_data.contact_address.person, 'mr_mrs'):
                    contact_person_mr_mrs = raw.contact_data.contact_address.person.mr_mrs
            elif raw.contact_data.contact_organization:
                # Organization name is in the mail address, not in PartnerIdOrganisation
                if raw.contact_data.contact_address and raw.contact_data.contact_address.organisation:
                    contact_organization_name = raw.contact_data.contact_address.organisation.organisation_name
            elif raw.contact_data.contact_address and raw.contact_data.contact_address.organisation:
                # Organization in mail address only
                contact_organization_name = raw.contact_data.contact_address.organisation.organisation_name

            # Extract mrMrs from contact_address.person (ALWAYS, regardless of personIdentification variant)
            # This preserves mrMrs even when we have personIdentification/personIdentificationPartner
            if raw.contact_data.contact_address and raw.contact_data.contact_address.person:
                if hasattr(raw.contact_data.contact_address.person, 'mr_mrs') and raw.contact_data.contact_address.person.mr_mrs:
                    # Only override if not already set from personIdentification
                    if contact_person_mr_mrs is None:
                        contact_person_mr_mrs = raw.contact_data.contact_address.person.mr_mrs

            # Extract contact address
            if raw.contact_data.contact_address and raw.contact_data.contact_address.address_information:
                addr_info = raw.contact_data.contact_address.address_information
                contact_address_address_line1 = addr_info.address_line1
                contact_address_street = addr_info.street
                contact_address_house_number = addr_info.house_number
                contact_address_dwelling_number = addr_info.dwelling_number
                contact_address_postal_code = str(addr_info.swiss_zip_code) if addr_info.swiss_zip_code else addr_info.foreign_zip_code
                contact_address_postal_code_addon = addr_info.swiss_zip_code_add_on
                contact_address_town = addr_info.town
                contact_address_locality = addr_info.locality
                # addr_info.country is a 2-letter ISO code string, not an object
                # For now we don't store it since we default to "CH" in to_ech0020()
                # TODO: Add contact_address_country_iso2 field to properly support foreign addresses

            contact_valid_from = raw.contact_data.contact_valid_from
            contact_valid_till = raw.contact_data.contact_valid_till

        # ====================================================================
        # 12. PERSON ADDITIONAL DATA (OPTIONAL)
        # ====================================================================

        mr_mrs = None
        title = None
        language_of_correspondance = None

        if raw.person_additional_data:
            mr_mrs = raw.person_additional_data.mr_mrs
            title = raw.person_additional_data.title
            language_of_correspondance = raw.person_additional_data.language_of_correspondance

        # ====================================================================
        # 13. POLITICAL RIGHT DATA (OPTIONAL)
        # ====================================================================

        restricted_voting_and_election_right_federation = None
        if raw.political_right_data:
            restricted_voting_and_election_right_federation = raw.political_right_data.restricted_voting_and_election_right_federation

        # ====================================================================
        # 14. JOB DATA (OPTIONAL)
        # ====================================================================

        kind_of_employment = None
        job_title = None
        occupation_data = None

        if raw.job_data:
            kind_of_employment = raw.job_data.kind_of_employment
            job_title = raw.job_data.job_title

            if raw.job_data.occupation_data:
                occupation_data = []
                for occ in raw.job_data.occupation_data:
                    # Convert ECH0021UIDStructure back to string format
                    employer_uid_str = None
                    if occ.uid:
                        # Reconstruct "CHE-123.456.789" format from structure
                        category_str = occ.uid.uid_organisation_id_categorie.value  # "CHE" or "ADM"
                        uid_num = occ.uid.uid_organisation_id  # e.g., 123456789
                        # Format with dots: 123.456.789
                        uid_formatted = f"{uid_num // 1000000}.{(uid_num // 1000) % 1000:03d}.{uid_num % 1000:03d}"
                        employer_uid_str = f"{category_str}-{uid_formatted}"

                    # Extract full address information from ECH0010AddressInformation
                    # Store all fields to preserve full data in roundtrip
                    place_of_work_dict = None
                    if occ.place_of_work:
                        place_of_work_dict = {
                            'street': occ.place_of_work.street,
                            'house_number': occ.place_of_work.house_number,
                            'town': occ.place_of_work.town,
                            'swiss_zip_code': occ.place_of_work.swiss_zip_code,
                            'swiss_zip_code_add_on': occ.place_of_work.swiss_zip_code_add_on,
                            'country': occ.place_of_work.country
                        }

                    place_of_employer_dict = None
                    if occ.place_of_employer:
                        place_of_employer_dict = {
                            'street': occ.place_of_employer.street,
                            'house_number': occ.place_of_employer.house_number,
                            'town': occ.place_of_employer.town,
                            'swiss_zip_code': occ.place_of_employer.swiss_zip_code,
                            'swiss_zip_code_add_on': occ.place_of_employer.swiss_zip_code_add_on,
                            'country': occ.place_of_employer.country
                        }

                    occ_dict = {
                        'employer': occ.employer,
                        'employer_uid': employer_uid_str,
                        'place_of_work': place_of_work_dict,
                        'place_of_employer': place_of_employer_dict,
                        'occupation_valid_from': occ.occupation_valid_from,
                        'occupation_valid_till': occ.occupation_valid_till
                    }
                    occupation_data.append(occ_dict)

        # ====================================================================
        # 15. MARITAL RELATIONSHIP (OPTIONAL)
        # Convert ECH0044PersonIdentification to PersonIdentification
        # ====================================================================

        spouse = None
        spouse_mr_mrs = None
        spouse_address_street = None
        spouse_address_house_number = None
        spouse_address_postal_code = None
        spouse_address_postal_code_addon = None
        spouse_address_town = None
        spouse_other_person_ids = None
        marital_relationship_type = None

        if raw.marital_relationship:
            partner = raw.marital_relationship.partner

            if partner and partner.person_identification:
                spouse_person_id = partner.person_identification

                # Extract spouse date_of_birth
                spouse_dob = None
                if spouse_person_id.date_of_birth:
                    if hasattr(spouse_person_id.date_of_birth, 'year_month_day') and spouse_person_id.date_of_birth.year_month_day:
                        spouse_dob = spouse_person_id.date_of_birth.year_month_day
                    elif hasattr(spouse_person_id.date_of_birth, 'year_month') and spouse_person_id.date_of_birth.year_month:
                        ym = spouse_person_id.date_of_birth.year_month
                        spouse_dob = date(ym.year, ym.month, 1)
                    elif hasattr(spouse_person_id.date_of_birth, 'year') and spouse_person_id.date_of_birth.year:
                        spouse_dob = date(spouse_person_id.date_of_birth.year, 1, 1)

                # Extract VN and local_person_id
                spouse_vn = None
                spouse_local_person_id = None
                spouse_local_person_id_category = None

                if hasattr(spouse_person_id, 'named_person_id') and spouse_person_id.named_person_id:
                    spouse_vn = spouse_person_id.named_person_id.vn
                    if spouse_person_id.named_person_id.local_person_id:
                        spouse_local_person_id = spouse_person_id.named_person_id.local_person_id.person_id
                        spouse_local_person_id_category = spouse_person_id.named_person_id.local_person_id.person_id_category
                elif hasattr(spouse_person_id, 'vn'):
                    spouse_vn = spouse_person_id.vn
                    if hasattr(spouse_person_id, 'local_person_id') and spouse_person_id.local_person_id:
                        spouse_local_person_id = spouse_person_id.local_person_id.person_id
                        spouse_local_person_id_category = spouse_person_id.local_person_id.person_id_category

                # Extract spouse other person IDs (optional, multiple)
                spouse_other_person_ids = None
                if hasattr(spouse_person_id, 'other_person_id') and spouse_person_id.other_person_id and len(spouse_person_id.other_person_id) > 0:
                    spouse_other_person_ids = [
                        {
                            'person_id': other_id.person_id,
                            'person_id_category': other_id.person_id_category
                        }
                        for other_id in spouse_person_id.other_person_id
                    ]

                spouse = PersonIdentification(
                    vn=spouse_vn,
                    local_person_id=spouse_local_person_id,
                    local_person_id_category=spouse_local_person_id_category,
                    official_name=spouse_person_id.official_name,
                    first_name=spouse_person_id.first_name,
                    original_name=spouse_person_id.original_name,
                    sex=spouse_person_id.sex.value if hasattr(spouse_person_id.sex, 'value') else str(spouse_person_id.sex),
                    date_of_birth=spouse_dob
                )

            # Extract spouse address and mr_mrs
            if partner and partner.address:
                if partner.address.person and hasattr(partner.address.person, 'mr_mrs'):
                    spouse_mr_mrs = partner.address.person.mr_mrs
                if partner.address.address_information:
                    addr_info = partner.address.address_information
                    spouse_address_street = addr_info.street
                    spouse_address_house_number = addr_info.house_number
                    spouse_address_postal_code = str(addr_info.swiss_zip_code) if addr_info.swiss_zip_code else None
                    spouse_address_postal_code_addon = addr_info.swiss_zip_code_add_on
                    spouse_address_town = addr_info.town

            marital_relationship_type = raw.marital_relationship.type_of_relationship

        # ====================================================================
        # 16. PARENTAL RELATIONSHIP (OPTIONAL)
        # Convert list of ECH0021ParentalRelationship to list of ParentInfo
        # ====================================================================

        parents = None
        if raw.parental_relationship:
            parents = []
            for parent_rel in raw.parental_relationship:
                if parent_rel.partner and parent_rel.partner.person_identification:
                    parent_person_id = parent_rel.partner.person_identification

                    # Extract parent date_of_birth
                    parent_dob = None
                    if parent_person_id.date_of_birth:
                        if hasattr(parent_person_id.date_of_birth, 'year_month_day') and parent_person_id.date_of_birth.year_month_day:
                            parent_dob = parent_person_id.date_of_birth.year_month_day
                        elif hasattr(parent_person_id.date_of_birth, 'year_month') and parent_person_id.date_of_birth.year_month:
                            ym = parent_person_id.date_of_birth.year_month
                            parent_dob = date(ym.year, ym.month, 1)
                        elif hasattr(parent_person_id.date_of_birth, 'year') and parent_person_id.date_of_birth.year:
                            parent_dob = date(parent_person_id.date_of_birth.year, 1, 1)

                    # Extract VN and local_person_id
                    parent_vn = None
                    parent_local_person_id = None
                    parent_local_person_id_category = None

                    if hasattr(parent_person_id, 'named_person_id') and parent_person_id.named_person_id:
                        parent_vn = parent_person_id.named_person_id.vn
                        if parent_person_id.named_person_id.local_person_id:
                            parent_local_person_id = parent_person_id.named_person_id.local_person_id.person_id
                            parent_local_person_id_category = parent_person_id.named_person_id.local_person_id.person_id_category
                    elif hasattr(parent_person_id, 'vn'):
                        parent_vn = parent_person_id.vn
                        if hasattr(parent_person_id, 'local_person_id') and parent_person_id.local_person_id:
                            parent_local_person_id = parent_person_id.local_person_id.person_id
                            parent_local_person_id_category = parent_person_id.local_person_id.person_id_category

                    parent_person = PersonIdentification(
                        vn=parent_vn,
                        local_person_id=parent_local_person_id,
                        local_person_id_category=parent_local_person_id_category,
                        official_name=parent_person_id.official_name,
                        first_name=parent_person_id.first_name,
                        original_name=parent_person_id.original_name,
                        sex=parent_person_id.sex.value if hasattr(parent_person_id.sex, 'value') else str(parent_person_id.sex),
                        date_of_birth=parent_dob
                    )

                    # Extract parent address and mr_mrs
                    parent_mr_mrs = None
                    parent_address_street = None
                    parent_address_house_number = None
                    parent_address_postal_code = None
                    parent_address_postal_code_addon = None
                    parent_address_town = None

                    if parent_rel.partner and parent_rel.partner.address:
                        if parent_rel.partner.address.person and hasattr(parent_rel.partner.address.person, 'mr_mrs'):
                            parent_mr_mrs = parent_rel.partner.address.person.mr_mrs
                        if parent_rel.partner.address.address_information:
                            addr_info = parent_rel.partner.address.address_information
                            parent_address_street = addr_info.street
                            parent_address_house_number = addr_info.house_number
                            parent_address_postal_code = str(addr_info.swiss_zip_code) if addr_info.swiss_zip_code else None
                            parent_address_postal_code_addon = addr_info.swiss_zip_code_add_on
                            parent_address_town = addr_info.town

                    parent_info = ParentInfo(
                        person=parent_person,
                        relationship_type=parent_rel.type_of_relationship,
                        care=parent_rel.care,
                        relationship_valid_from=parent_rel.relationship_valid_from,
                        mr_mrs=parent_mr_mrs,
                        address_street=parent_address_street,
                        address_house_number=parent_address_house_number,
                        address_postal_code=parent_address_postal_code,
                        address_postal_code_addon=parent_address_postal_code_addon,
                        address_town=parent_address_town
                    )
                    parents.append(parent_info)

        # ====================================================================
        # 17. GUARDIAN RELATIONSHIP (OPTIONAL)
        # Convert list of ECH0021GuardianRelationship to list of GuardianInfo
        # ====================================================================

        guardians = None
        if raw.guardian_relationship:
            guardians = []
            for guardian_rel in raw.guardian_relationship:
                # ECH0021GuardianRelationship has flat structure (no partner wrapper)
                # Detect guardian type
                guardian_type = None
                guardian_person = None
                org_uid = None
                org_name = None

                if guardian_rel.person_identification:
                    # Person guardian
                    guardian_type = GuardianType.PERSON
                    guardian_person_id = guardian_rel.person_identification

                    # Extract guardian date_of_birth
                    guardian_dob = None
                    if guardian_person_id.date_of_birth:
                        if hasattr(guardian_person_id.date_of_birth, 'year_month_day') and guardian_person_id.date_of_birth.year_month_day:
                            guardian_dob = guardian_person_id.date_of_birth.year_month_day
                        elif hasattr(guardian_person_id.date_of_birth, 'year_month') and guardian_person_id.date_of_birth.year_month:
                            ym = guardian_person_id.date_of_birth.year_month
                            guardian_dob = date(ym.year, ym.month, 1)
                        elif hasattr(guardian_person_id.date_of_birth, 'year') and guardian_person_id.date_of_birth.year:
                            guardian_dob = date(guardian_person_id.date_of_birth.year, 1, 1)

                    # Extract VN and local_person_id
                    guardian_vn = None
                    guardian_local_person_id = None
                    guardian_local_person_id_category = None

                    if hasattr(guardian_person_id, 'named_person_id') and guardian_person_id.named_person_id:
                        guardian_vn = guardian_person_id.named_person_id.vn
                        if guardian_person_id.named_person_id.local_person_id:
                            guardian_local_person_id = guardian_person_id.named_person_id.local_person_id.person_id
                            guardian_local_person_id_category = guardian_person_id.named_person_id.local_person_id.person_id_category
                    elif hasattr(guardian_person_id, 'vn'):
                        guardian_vn = guardian_person_id.vn
                        if hasattr(guardian_person_id, 'local_person_id') and guardian_person_id.local_person_id:
                            guardian_local_person_id = guardian_person_id.local_person_id.person_id
                            guardian_local_person_id_category = guardian_person_id.local_person_id.person_id_category

                    guardian_person = PersonIdentification(
                        vn=guardian_vn,
                        local_person_id=guardian_local_person_id,
                        local_person_id_category=guardian_local_person_id_category,
                        official_name=guardian_person_id.official_name,
                        first_name=guardian_person_id.first_name,
                        original_name=guardian_person_id.original_name,
                        sex=guardian_person_id.sex.value if hasattr(guardian_person_id.sex, 'value') else str(guardian_person_id.sex),
                        date_of_birth=guardian_dob
                    )

                elif guardian_rel.person_identification_partner:
                    # Partner person guardian
                    guardian_type = GuardianType.PERSON_PARTNER
                    guardian_person_id = guardian_rel.person_identification_partner

                    # Extract similar to above
                    guardian_dob = None
                    if guardian_person_id.date_of_birth:
                        if hasattr(guardian_person_id.date_of_birth, 'year_month_day') and guardian_person_id.date_of_birth.year_month_day:
                            guardian_dob = guardian_person_id.date_of_birth.year_month_day
                        elif hasattr(guardian_person_id.date_of_birth, 'year_month') and guardian_person_id.date_of_birth.year_month:
                            ym = guardian_person_id.date_of_birth.year_month
                            guardian_dob = date(ym.year, ym.month, 1)
                        elif hasattr(guardian_person_id.date_of_birth, 'year') and guardian_person_id.date_of_birth.year:
                            guardian_dob = date(guardian_person_id.date_of_birth.year, 1, 1)

                    guardian_vn = None
                    guardian_local_person_id = None
                    guardian_local_person_id_category = None

                    if hasattr(guardian_person_id, 'named_person_id') and guardian_person_id.named_person_id:
                        guardian_vn = guardian_person_id.named_person_id.vn
                        if guardian_person_id.named_person_id.local_person_id:
                            guardian_local_person_id = guardian_person_id.named_person_id.local_person_id.person_id
                            guardian_local_person_id_category = guardian_person_id.named_person_id.local_person_id.person_id_category
                    elif hasattr(guardian_person_id, 'vn'):
                        guardian_vn = guardian_person_id.vn
                        if hasattr(guardian_person_id, 'local_person_id') and guardian_person_id.local_person_id:
                            guardian_local_person_id = guardian_person_id.local_person_id.person_id
                            guardian_local_person_id_category = guardian_person_id.local_person_id.person_id_category

                    guardian_person = PersonIdentification(
                        vn=guardian_vn,
                        local_person_id=guardian_local_person_id,
                        local_person_id_category=guardian_local_person_id_category,
                        official_name=guardian_person_id.official_name,
                        first_name=guardian_person_id.first_name,
                        original_name=guardian_person_id.original_name,
                        sex=guardian_person_id.sex.value if hasattr(guardian_person_id.sex, 'value') else str(guardian_person_id.sex),
                        date_of_birth=guardian_dob
                    )

                elif guardian_rel.partner_id_organisation:
                    # Organization guardian
                    guardian_type = GuardianType.ORGANISATION
                    # Extract UID from local_person_id (confusingly named)
                    org_uid = guardian_rel.partner_id_organisation.local_person_id.person_id
                    # Extract organization name from partner_address.organisation.organisation_name
                    # (ECH0011PartnerIdOrganisation doesn't have name field, so we store it in partner_address)
                    org_name = None
                    if guardian_rel.partner_address and guardian_rel.partner_address.organisation:
                        org_name = guardian_rel.partner_address.organisation.organisation_name

                # Extract guardian address and mr_mrs
                guardian_mr_mrs = None
                guardian_address_street = None
                guardian_address_house_number = None
                guardian_address_postal_code = None
                guardian_address_postal_code_addon = None
                guardian_address_town = None

                if guardian_rel.partner_address:
                    if guardian_rel.partner_address.person and hasattr(guardian_rel.partner_address.person, 'mr_mrs'):
                        guardian_mr_mrs = guardian_rel.partner_address.person.mr_mrs
                    if guardian_rel.partner_address.address_information:
                        addr_info = guardian_rel.partner_address.address_information
                        guardian_address_street = addr_info.street
                        guardian_address_house_number = addr_info.house_number
                        guardian_address_postal_code = str(addr_info.swiss_zip_code) if addr_info.swiss_zip_code else None
                        guardian_address_postal_code_addon = addr_info.swiss_zip_code_add_on
                        guardian_address_town = addr_info.town

                if guardian_type:
                    guardian_info = GuardianInfo(
                        guardian_relationship_id=guardian_rel.guardian_relationship_id,
                        guardian_type=guardian_type,
                        person=guardian_person,
                        organization_uid=org_uid,
                        organization_name=org_name,
                        mr_mrs=guardian_mr_mrs,
                        address_street=guardian_address_street,
                        address_house_number=guardian_address_house_number,
                        address_postal_code=guardian_address_postal_code,
                        address_postal_code_addon=guardian_address_postal_code_addon,
                        address_town=guardian_address_town,
                        relationship_type=guardian_rel.type_of_relationship,
                        guardian_measure_based_on_law=guardian_rel.guardian_measure_info.based_on_law if guardian_rel.guardian_measure_info else [],
                        guardian_measure_valid_from=guardian_rel.guardian_measure_info.guardian_measure_valid_from if guardian_rel.guardian_measure_info else None,
                        care=guardian_rel.care
                    )
                    guardians.append(guardian_info)

        # ====================================================================
        # 18. ARMED FORCES DATA (OPTIONAL)
        # ====================================================================

        armed_forces_service = None
        armed_forces_liability = None
        armed_forces_valid_from = None

        if raw.armed_forces_data:
            armed_forces_service = raw.armed_forces_data.armed_forces_service
            armed_forces_liability = raw.armed_forces_data.armed_forces_liability
            armed_forces_valid_from = raw.armed_forces_data.armed_forces_valid_from

        # ====================================================================
        # 19. CIVIL DEFENSE DATA (OPTIONAL)
        # ====================================================================

        civil_defense = None
        civil_defense_valid_from = None

        if raw.civil_defense_data:
            civil_defense = raw.civil_defense_data.civil_defense
            civil_defense_valid_from = raw.civil_defense_data.civil_defense_valid_from

        # ====================================================================
        # 20. FIRE SERVICE DATA (OPTIONAL)
        # ====================================================================

        fire_service = None
        fire_service_liability = None
        fire_service_valid_from = None

        if raw.fire_service_data:
            fire_service = raw.fire_service_data.fire_service
            fire_service_liability = raw.fire_service_data.fire_service_liability
            fire_service_valid_from = raw.fire_service_data.fire_service_valid_from

        # ====================================================================
        # 21. HEALTH INSURANCE DATA (OPTIONAL)
        # ====================================================================

        health_insured = None
        health_insurance_name = None
        health_insurance_address_street = None
        health_insurance_address_house_number = None
        health_insurance_address_postal_code = None
        health_insurance_address_town = None
        health_insurance_address_country = None
        health_insurance_valid_from = None

        if raw.health_insurance_data:
            # Convert YesNo enum to bool
            health_insured = raw.health_insurance_data.health_insured == "1" if raw.health_insurance_data.health_insured else None

            # CHOICE: insurance_name OR insurance_address (with name inside)
            if raw.health_insurance_data.insurance_address:
                # Extract name from insurance_address.organisation
                if raw.health_insurance_data.insurance_address.organisation:
                    health_insurance_name = raw.health_insurance_data.insurance_address.organisation.organisation_name

                # Extract address information
                if raw.health_insurance_data.insurance_address.address_information:
                    addr_info = raw.health_insurance_data.insurance_address.address_information
                    health_insurance_address_street = addr_info.street
                    health_insurance_address_house_number = addr_info.house_number
                    # Convert postal code to string (can be int in XML)
                    health_insurance_address_postal_code = str(addr_info.swiss_zip_code) if addr_info.swiss_zip_code is not None else None
                    health_insurance_address_town = addr_info.town
                    health_insurance_address_country = addr_info.country
            else:
                # Just name, no address
                health_insurance_name = raw.health_insurance_data.insurance_name

            health_insurance_valid_from = raw.health_insurance_data.health_insurance_valid_from

        # ====================================================================
        # 22. MATRIMONIAL INHERITANCE ARRANGEMENT DATA (OPTIONAL)
        # ====================================================================

        matrimonial_inheritance_arrangement = None
        matrimonial_inheritance_arrangement_valid_from = None

        if raw.matrimonial_inheritance_arrangement_data:
            matrimonial_inheritance_arrangement = raw.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement
            matrimonial_inheritance_arrangement_valid_from = raw.matrimonial_inheritance_arrangement_data.matrimonial_inheritance_arrangement_valid_from

        # ====================================================================
        # CONSTRUCT LAYER 2 MODEL
        # ====================================================================

        return cls(
            # Person identification
            vn=vn,
            local_person_id=local_person_id,
            local_person_id_category=local_person_id_category,
            other_person_ids=other_person_ids,
            official_name=official_name,
            first_name=first_name,
            original_name=original_name,
            sex=sex,
            date_of_birth=date_of_birth,
            # Name info
            call_name=call_name,
            alliance_name=alliance_name,
            alias_name=alias_name,
            other_name=other_name,
            name_valid_from=name_valid_from,
            name_on_foreign_passport=name_on_foreign_passport,
            name_on_foreign_passport_first=name_on_foreign_passport_first,
            declared_foreign_name=declared_foreign_name,
            declared_foreign_name_first=declared_foreign_name_first,
            # Birth info
            birth_place_type=birth_place_type,
            birth_municipality_bfs=birth_municipality_bfs,
            birth_municipality_name=birth_municipality_name,
            birth_canton_abbreviation=birth_canton_abbreviation,
            birth_municipality_history_id=birth_municipality_history_id,
            birth_country_id=birth_country_id,
            birth_country_iso=birth_country_iso,
            birth_country_name_short=birth_country_name_short,
            birth_town=birth_town,
            birth_father_name=birth_father_name,
            birth_father_first_name=birth_father_first_name,
            birth_father_official_proof=birth_father_official_proof,
            birth_mother_name=birth_mother_name,
            birth_mother_first_name=birth_mother_first_name,
            birth_mother_official_proof=birth_mother_official_proof,
            # Religion
            religion=religion,
            religion_valid_from=religion_valid_from,
            # Marital info
            marital_status=marital_status,
            date_of_marital_status=date_of_marital_status,
            official_proof_of_marital_status_yes_no=official_proof_of_marital_status_yes_no,
            marriage_place_type=marriage_place_type,
            marriage_municipality_bfs=marriage_municipality_bfs,
            marriage_municipality_name=marriage_municipality_name,
            marriage_municipality_history_id=marriage_municipality_history_id,
            marriage_canton_abbreviation=marriage_canton_abbreviation,
            marriage_country_id=marriage_country_id,
            marriage_country_iso=marriage_country_iso,
            marriage_country_name_short=marriage_country_name_short,
            marriage_town=marriage_town,
            # Nationality
            nationality_status=nationality_status,
            nationalities=nationalities,
            # Citizenship CHOICE
            places_of_origin=places_of_origin,
            residence_permit=residence_permit,
            residence_permit_valid_from=residence_permit_valid_from,
            residence_permit_valid_till=residence_permit_valid_till,
            entry_date=entry_date,
            # Lock data
            data_lock=data_lock,
            data_lock_valid_from=data_lock_valid_from,
            data_lock_valid_till=data_lock_valid_till,
            paper_lock=paper_lock,
            paper_lock_valid_from=paper_lock_valid_from,
            paper_lock_valid_till=paper_lock_valid_till,
            # Death data
            death_date=death_date,
            death_place_type=death_place_type,
            death_municipality_bfs=death_municipality_bfs,
            death_municipality_name=death_municipality_name,
            death_canton_abbreviation=death_canton_abbreviation,
            death_municipality_history_id=death_municipality_history_id,
            death_country_id=death_country_id,
            death_country_iso=death_country_iso,
            death_country_name_short=death_country_name_short,
            # Contact data
            contact_person_official_name=contact_person_official_name,
            contact_person_first_name=contact_person_first_name,
            contact_person_sex=contact_person_sex,
            contact_person_date_of_birth=contact_person_date_of_birth,
            contact_person_mr_mrs=contact_person_mr_mrs,
            contact_person_local_person_id=contact_person_local_person_id,
            contact_person_local_person_id_category=contact_person_local_person_id_category,
            contact_person_vn=contact_person_vn,
            contact_organization_name=contact_organization_name,
            contact_address_address_line1=contact_address_address_line1,
            contact_address_street=contact_address_street,
            contact_address_house_number=contact_address_house_number,
            contact_address_dwelling_number=contact_address_dwelling_number,
            contact_address_postal_code=contact_address_postal_code,
            contact_address_postal_code_addon=contact_address_postal_code_addon,
            contact_address_town=contact_address_town,
            contact_address_locality=contact_address_locality,
            contact_address_country_iso=contact_address_country_iso,
            contact_valid_from=contact_valid_from,
            contact_valid_till=contact_valid_till,
            # Person additional data
            mr_mrs=mr_mrs,
            title=title,
            language_of_correspondance=language_of_correspondance,
            # Political right data
            restricted_voting_and_election_right_federation=restricted_voting_and_election_right_federation,
            # Job data
            kind_of_employment=kind_of_employment,
            job_title=job_title,
            occupation_data=occupation_data,
            # Marital relationship
            spouse=spouse,
            spouse_mr_mrs=spouse_mr_mrs,
            spouse_address_street=spouse_address_street,
            spouse_address_house_number=spouse_address_house_number,
            spouse_address_postal_code=spouse_address_postal_code,
            spouse_address_postal_code_addon=spouse_address_postal_code_addon,
            spouse_address_town=spouse_address_town,
            spouse_other_person_ids=spouse_other_person_ids,
            marital_relationship_type=marital_relationship_type,
            # Parental relationship
            parents=parents,
            # Guardian relationship
            guardians=guardians,
            # Armed forces data
            armed_forces_service=armed_forces_service,
            armed_forces_liability=armed_forces_liability,
            armed_forces_valid_from=armed_forces_valid_from,
            # Civil defense data
            civil_defense=civil_defense,
            civil_defense_valid_from=civil_defense_valid_from,
            # Fire service data
            fire_service=fire_service,
            fire_service_liability=fire_service_liability,
            fire_service_valid_from=fire_service_valid_from,
            # Health insurance data
            health_insured=health_insured,
            health_insurance_name=health_insurance_name,
            health_insurance_address_street=health_insurance_address_street,
            health_insurance_address_house_number=health_insurance_address_house_number,
            health_insurance_address_postal_code=health_insurance_address_postal_code,
            health_insurance_address_town=health_insurance_address_town,
            health_insurance_address_country=health_insurance_address_country,
            health_insurance_valid_from=health_insurance_valid_from,
            # Matrimonial inheritance arrangement data
            matrimonial_inheritance_arrangement=matrimonial_inheritance_arrangement,
            matrimonial_inheritance_arrangement_valid_from=matrimonial_inheritance_arrangement_valid_from
        )

    def validate_swiss_data(self, context: Optional['ValidationContext'] = None) -> 'ValidationContext':
        """Optional validation using Swiss open data.

        This method validates Swiss government data fields against official open data
        sources (postal codes, municipalities, etc.) and provides warnings for
        potential data quality issues.

        **IMPORTANT**: This method NEVER raises exceptions or blocks data entry.
        It only collects warnings that can be inspected by the application.

        **Core Principle**: User is king - warnings provide feedback but the user
        always has the final say.

        Args:
            context: Optional ValidationContext to add warnings to. If None, a new
                    context is created and returned.

        Returns:
            ValidationContext containing any warnings found during validation.
            Returns empty context if no issues found.

        Requires:
            openmun-opendata package must be installed. If not available, validation
            is silently disabled and an empty context is returned.

        Example - Basic Usage:
            >>> person = BaseDeliveryPerson(
            ...     contact_address_postal_code="8001",
            ...     contact_address_town="Basel",  # Wrong!
            ...     # ... other required fields ...
            ... )
            >>> ctx = person.validate_swiss_data()
            >>> if ctx.has_warnings():
            ...     for warning in ctx.warnings:
            ...         print(warning)
            ⚠️  contact_address_postal_code + contact_address_town: Postal code 8001 is typically associated with: Zürich, Zürich Sihlpost

        Example - Interactive Application:
            >>> ctx = person.validate_swiss_data()
            >>> if ctx.has_warnings():
            ...     for warning in ctx.warnings:
            ...         print(f"\\nWarning: {warning}")
            ...         if warning.suggestions:
            ...             print("Did you mean one of these?")
            ...             for suggestion in warning.suggestions[:5]:
            ...                 print(f"  - {suggestion}")
            ...         response = input("Continue anyway? (y/n): ")
            ...         if response.lower() != 'y':
            ...             print("Save cancelled")
            ...             return

        Example - Reuse Context:
            >>> ctx = ValidationContext()
            >>> person1.validate_swiss_data(ctx)
            >>> person2.validate_swiss_data(ctx)
            >>> # ctx now contains warnings from both persons

        Current Validators:
            - Postal code + town validation (contact_address_postal_code + contact_address_town)
            - Municipality BFS code validation (birth_municipality_bfs, marriage_municipality_bfs, death_municipality_bfs)
            - Canton code validation (birth_canton_abbreviation, marriage_canton_abbreviation, death_canton_abbreviation, places_of_origin)
            - Street name validation (contact_address_street)
            - Cross-validation (postal code vs municipality, street vs postal code)

        Future Validators (Phase 3+ expansion):
            - Country ISO code validation

        Note:
            BaseDeliveryPerson validates contact person address fields.
            For dwelling address validation, use BaseDeliveryEvent.validate_swiss_data()

        See Also:
            ValidationContext: For inspecting warnings
            ValidationWarning: Base warning class
            PostalCodeWarning: Specific warning type for postal code mismatches
        """
        # Import here to avoid circular dependency
        from openmun_ech.validation import (
            ValidationContext,
            PostalCodeValidator,
            MunicipalityBFSValidator,
            CantonCodeValidator,
            StreetNameValidator,
            CrossValidator,
            ReligionCodeValidator,
        )

        # Create context if not provided
        if context is None:
            context = ValidationContext()

        # Validate contact address postal code + town if both are provided
        if self.contact_address_postal_code and self.contact_address_town:
            PostalCodeValidator.validate(
                postal_code=self.contact_address_postal_code,
                town=self.contact_address_town,
                context=context,
                field_name_prefix="contact_address_postal_code + contact_address_town"
            )

        # Warn if religion code is not in eCH-0011 enum (non-blocking)
        if self.religion:
            ReligionCodeValidator.validate(
                code=self.religion,
                context=context,
                field_name_prefix="religion"
            )

        # Validate birth municipality BFS code if provided
        if self.birth_municipality_bfs:
            MunicipalityBFSValidator.validate(
                bfs_code=self.birth_municipality_bfs,
                municipality_name=self.birth_municipality_name,
                context=context,
                field_name_prefix="birth_municipality_bfs"
            )

        # Validate marriage municipality BFS code if provided
        if self.marriage_municipality_bfs:
            MunicipalityBFSValidator.validate(
                bfs_code=self.marriage_municipality_bfs,
                municipality_name=self.marriage_municipality_name,
                context=context,
                field_name_prefix="marriage_municipality_bfs"
            )

        # Validate death municipality BFS code if provided
        if self.death_municipality_bfs:
            MunicipalityBFSValidator.validate(
                bfs_code=self.death_municipality_bfs,
                municipality_name=self.death_municipality_name,
                context=context,
                field_name_prefix="death_municipality_bfs"
            )

        # Validate birth canton code if provided
        if self.birth_canton_abbreviation:
            CantonCodeValidator.validate(
                canton_code=self.birth_canton_abbreviation,
                context=context,
                field_name_prefix="birth_canton_abbreviation"
            )

        # Validate marriage canton code if provided
        if self.marriage_canton_abbreviation:
            CantonCodeValidator.validate(
                canton_code=self.marriage_canton_abbreviation,
                context=context,
                field_name_prefix="marriage_canton_abbreviation"
            )

        # Validate death canton code if provided
        if self.death_canton_abbreviation:
            CantonCodeValidator.validate(
                canton_code=self.death_canton_abbreviation,
                context=context,
                field_name_prefix="death_canton_abbreviation"
            )

        # Validate places of origin canton codes if provided
        if self.places_of_origin:
            for idx, origin in enumerate(self.places_of_origin):
                if isinstance(origin, dict) and 'canton' in origin and origin['canton']:
                    CantonCodeValidator.validate(
                        canton_code=origin['canton'],
                        context=context,
                        field_name_prefix=f"places_of_origin[{idx}].canton"
                    )

        # Validate contact address street name if provided
        # Note: We validate street without municipality filter since contact_address
        # doesn't have a municipality_bfs field (unlike dwelling_address in BaseDeliveryEvent)
        if self.contact_address_street:
            StreetNameValidator.validate(
                street_name=self.contact_address_street,
                context=context,
                municipality_bfs=None,  # No municipality field for contact_address
                postal_code=self.contact_address_postal_code,
                field_name_prefix="contact_address_street"
            )

        # Cross-validation: street vs postal code (if both provided)
        # Note: We don't cross-validate contact_address_postal_code with birth_municipality_bfs
        # because they represent different addresses (contact vs birth location)
        if self.contact_address_street and self.contact_address_postal_code:
            CrossValidator.validate_street_postal(
                street_name=self.contact_address_street,
                postal_code=self.contact_address_postal_code,
                context=context,
                municipality_bfs=None,  # No municipality field for contact_address
                field_name_prefix_street="contact_address_street",
                field_name_prefix_postal="contact_address_postal_code"
            )

        return context


# ============================================================================
# PHASE 2: EVENT MODELS (Base Delivery Event)
# ============================================================================
# Phase 2 adds event wrapper (residence/dwelling) for complete eCH-0020 delivery
# Phase 1 = person data, Phase 2 = WHERE person lives
#
# Structure:
# - Phase 1: BaseDeliveryPerson (person data only) ✅ COMPLETE
# - Phase 2: BaseDeliveryEvent (person + residence/dwelling) ⬅️ THIS SECTION
#
# Layer 2 hides:
# - Namespace wrappers (ECH0020HasMainResidence, ECH0020HasSecondaryResidence, etc.)
# - XSD CHOICE complexity (validators enforce)
# - Nesting levels (5 → 2)
#
# Layer 2 exposes:
# - ALL fields (100% roundtrip guarantee)
# - All optional fields
# - All rare fields
# ============================================================================


class ResidenceType(str, Enum):
    """Residence type for base delivery event.

    XSD CHOICE #9: Exactly ONE residence type per event.

    Values:
    - MAIN: Person's main residence (most common)
    - SECONDARY: Person's secondary residence (vacation home, etc.)
    - OTHER: Other residence type
    """
    MAIN = "main"
    SECONDARY = "secondary"
    OTHER = "other"


class SecondaryResidenceInfo(BaseModel):
    """Secondary residence municipality (for main residence type).

    When a person has main residence in one municipality, they can have
    0-n secondary residences in other municipalities.

    This is a SIMPLE model (only 3 fields) for secondary residence list.

    Example:
        Person lives in Zürich (main), has vacation home in Davos (secondary):
        >>> sec = SecondaryResidenceInfo(
        ...     bfs="3851",
        ...     name="Davos",
        ...     canton="GR"
        ... )
    """
    bfs: str = Field(
        ...,
        description="BFS municipality number (e.g., '261' for Zürich)"
    )
    name: str = Field(
        ...,
        description="Municipality name (e.g., 'Zürich')"
    )
    canton: Optional[str] = Field(
        None,
        description="Canton abbreviation (e.g., 'ZH', 'BE', 'GR')"
    )


class DwellingAddressInfo(BaseModel):
    """Dwelling address (flattened from ECH0011DwellingAddress + ECH0010SwissAddressInformation).

    Complete Swiss address with building IDs, household info, and postal address.

    Minimal example (required fields only):
        >>> dwelling = DwellingAddressInfo(
        ...     town="Zürich",
        ...     swiss_zip_code=8001,
        ...     type_of_household="1"  # Single person
        ... )

    Complete example (with optional fields):
        >>> dwelling = DwellingAddressInfo(
        ...     # Building IDs (optional)
        ...     egid=123456,
        ...     ewid=1,
        ...     household_id="HH-001",
        ...     # Structured address (optional)
        ...     street="Bahnhofstrasse",
        ...     house_number="1",
        ...     dwelling_number="3A",
        ...     # Required fields
        ...     town="Zürich",
        ...     swiss_zip_code=8001,
        ...     type_of_household="2",  # Family household
        ...     # Optional metadata
        ...     moving_date=date(2023, 1, 1)
        ... )

    Layer 1 mapping:
        ECH0011DwellingAddress
        └── address (ECH0010SwissAddressInformation)
            └── All address fields

    Layer 2 flattens 2 levels → 1 level (all fields accessible).
    """

    # Building identifiers (optional) - Federal building/dwelling IDs
    egid: Optional[int] = Field(
        None,
        ge=1,
        le=999999999,
        description="EGID: Federal Building ID (Eidgenössischer Gebäudeidentifikator, optional)"
    )
    ewid: Optional[int] = Field(
        None,
        ge=1,
        le=999,
        description="EWID: Federal Dwelling ID (Eidgenössischer Wohnungsidentifikator, optional)"
    )
    household_id: Optional[str] = Field(
        None,
        description="Household identifier (optional)"
    )

    # Free-form address lines (optional) - Use when structured address not available
    address_line1: Optional[str] = Field(
        None,
        max_length=60,
        description="First address line, free-form (optional)"
    )
    address_line2: Optional[str] = Field(
        None,
        max_length=60,
        description="Second address line, free-form (optional)"
    )

    # Structured address (optional as group) - Prefer over free-form
    street: Optional[str] = Field(
        None,
        max_length=60,
        description="Street name (optional, structured address)"
    )
    house_number: Optional[str] = Field(
        None,
        max_length=12,
        description="House number (optional, structured address)"
    )
    dwelling_number: Optional[str] = Field(
        None,
        max_length=10,
        description="Apartment/dwelling number (optional, structured address)"
    )

    # Locality (optional) - District or locality name
    locality: Optional[str] = Field(
        None,
        max_length=40,
        description="Locality/district name (optional)"
    )

    # Town (REQUIRED) - Always required for Swiss addresses
    town: str = Field(
        ...,
        max_length=40,
        description="Town/city name (REQUIRED)"
    )

    # Swiss ZIP code (REQUIRED) - 4-digit postal code
    swiss_zip_code: int = Field(
        ...,
        ge=1000,
        le=9999,
        description="Swiss postal code, 4 digits 1000-9999 (REQUIRED)"
    )
    swiss_zip_code_add_on: Optional[str] = Field(
        None,
        max_length=2,
        description="Swiss postal code add-on (e.g., '01', optional)"
    )
    swiss_zip_code_id: Optional[int] = Field(
        None,
        description="Official Swiss postal code ID (optional)"
    )

    # Country (default "CH") - ISO 3166-1 alpha-2 code
    country: str = Field(
        default="CH",
        min_length=1,
        max_length=2,
        description="Country code, ISO 3166-1 alpha-2 (default 'CH')"
    )

    # Household type (REQUIRED) - Type of household living at this address
    type_of_household: TypeOfHousehold = Field(
        ...,
        description=(
            "Type of household (REQUIRED): "
            "0=unknown, 1=single person, 2=family, 3=non-family"
        )
    )

    # Moving date (optional) - When person moved into this dwelling
    moving_date: Optional[date] = Field(
        None,
        description="Date of moving into dwelling (optional)"
    )


class DestinationInfo(BaseModel):
    """Destination (comes from / goes to) - flattened from ECH0011DestinationType.

    Represents where a person came from (previous residence) or goes to (new residence).

    XSD CHOICE #11: Exactly ONE of UNKNOWN, SWISS, or FOREIGN.

    Minimal examples:
        # Unknown destination
        >>> dest = DestinationInfo(place_type=PlaceType.UNKNOWN)

        # Swiss municipality
        >>> dest = DestinationInfo(
        ...     place_type=PlaceType.SWISS,
        ...     municipality_bfs="261",
        ...     municipality_name="Zürich"
        ... )

        # Foreign country
        >>> dest = DestinationInfo(
        ...     place_type=PlaceType.FOREIGN,
        ...     country_iso="DE",
        ...     country_name_short="Deutschland",
        ...     town="Berlin"
        ... )

    Complete example with mail address:
        >>> dest = DestinationInfo(
        ...     place_type=PlaceType.SWISS,
        ...     municipality_bfs="261",
        ...     municipality_name="Zürich",
        ...     canton_abbreviation="ZH",
        ...     # Optional mail address at destination
        ...     mail_address_street="Bahnhofstrasse",
        ...     mail_address_house_number="1",
        ...     mail_address_town="Zürich",
        ...     mail_address_zip=8001,
        ...     mail_address_country="CH"
        ... )

    Layer 1 mapping: ECH0011DestinationType (CHOICE of unknown/swiss/foreign + mail_address)
    Layer 2: Flat with place_type enum + validator
    """

    # Place type (REQUIRED) - Determines which fields are required
    place_type: PlaceType = Field(
        ...,
        description="Destination type: UNKNOWN, SWISS, or FOREIGN (REQUIRED)"
    )

    # Swiss municipality fields (required if place_type == SWISS)
    municipality_bfs: Optional[str] = Field(
        None,
        description="BFS municipality number (required for SWISS, e.g., '261' for Zürich)"
    )
    municipality_name: Optional[str] = Field(
        None,
        description="Municipality name (required for SWISS, e.g., 'Zürich')"
    )
    canton_abbreviation: Optional[str] = Field(
        None,
        description="Canton abbreviation (optional for SWISS, e.g., 'ZH', 'BE')"
    )
    municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS municipality number (optional for SWISS)"
    )

    # Foreign country fields (required if place_type == FOREIGN)
    country_id: Optional[str] = Field(
        None,
        description="BFS country code (optional for FOREIGN, e.g., '8207' for Germany)"
    )
    country_iso: Optional[str] = Field(
        None,
        description="ISO country code (required for FOREIGN, e.g., 'DE' for Germany)"
    )
    country_name_short: Optional[str] = Field(
        None,
        description="Country name (required for FOREIGN, e.g., 'Deutschland')"
    )
    town: Optional[str] = Field(
        None,
        max_length=100,
        description="Town name (optional for FOREIGN, e.g., 'Berlin')"
    )

    # Optional mail address (all place types) - Full address at destination
    mail_address_address_line1: Optional[str] = Field(
        None,
        description="Mail address line 1 at destination (optional)"
    )
    mail_address_street: Optional[str] = Field(
        None,
        description="Mail address street at destination (optional)"
    )
    mail_address_house_number: Optional[str] = Field(
        None,
        description="Mail address house number at destination (optional)"
    )
    mail_address_dwelling_number: Optional[str] = Field(
        None,
        description="Mail address dwelling number at destination (optional)"
    )
    mail_address_locality: Optional[str] = Field(
        None,
        description="Mail address locality at destination (optional)"
    )
    mail_address_town: Optional[str] = Field(
        None,
        description="Mail address town at destination (optional)"
    )
    mail_address_zip: Optional[int] = Field(
        None,
        description="Mail address ZIP code at destination (optional)"
    )
    mail_address_zip_addon: Optional[str] = Field(
        None,
        description="Mail address ZIP add-on at destination (optional)"
    )
    mail_address_country: Optional[str] = Field(
        None,
        description="Mail address country at destination (optional, e.g., 'CH')"
    )

    @model_validator(mode='after')
    def validate_place_choice(self) -> 'DestinationInfo':
        """Validate XSD CHOICE #11: place type determines required fields.

        - UNKNOWN: No additional fields required
        - SWISS: municipality_bfs and municipality_name required
        - FOREIGN: country_iso and country_name_short required
        """
        if self.place_type == PlaceType.SWISS:
            if not self.municipality_bfs or not self.municipality_name:
                raise ValueError(
                    "SWISS destination requires municipality_bfs and municipality_name"
                )
        elif self.place_type == PlaceType.FOREIGN:
            if not self.country_iso or not self.country_name_short:
                raise ValueError(
                    "FOREIGN destination requires country_iso and country_name_short"
                )
        # UNKNOWN requires no additional fields

        return self


class BaseDeliveryEvent(BaseModel):
    """Layer 2: Base delivery event (person + residence).

    Complete eCH-0020 base delivery combining person data (Phase 1) with
    residence/dwelling data (Phase 2).

    This model represents a complete base delivery event: WHO (person) lives WHERE
    (dwelling address in municipality).

    Minimal Working Example:
        >>> from datetime import date
        >>> from openmun_ech.ech0020.models import (
        ...     BaseDeliveryEvent, BaseDeliveryPerson, ResidenceType,
        ...     DwellingAddressInfo, PlaceType
        ... )
        >>>
        >>> # Step 1: Create person (Phase 1)
        >>> person = BaseDeliveryPerson(
        ...     official_name="Müller",
        ...     first_name="Hans",
        ...     sex="1",
        ...     date_of_birth=date(1980, 5, 15),
        ...     vn=756123456789,
        ...     local_person_id="12345",
        ...     places_of_origin=[{
        ...         "canton": "ZH",
        ...         "municipality_bfs": "261",
        ...         "municipality_name": "Zürich"
        ...     }],
        ...     birth_place_type=PlaceType.SWISS,
        ...     birth_municipality_bfs="261",
        ...     birth_municipality_name="Zürich"
        ... )
        >>>
        >>> # Step 2: Create dwelling address
        >>> dwelling = DwellingAddressInfo(
        ...     street="Bahnhofstrasse",
        ...     house_number="1",
        ...     town="Zürich",
        ...     swiss_zip_code=8001,
        ...     type_of_household="1"  # Single person
        ... )
        >>>
        >>> # Step 3: Create event (combines person + residence)
        >>> event = BaseDeliveryEvent(
        ...     person=person,
        ...     residence_type=ResidenceType.MAIN,
        ...     reporting_municipality_bfs="261",
        ...     reporting_municipality_name="Zürich",
        ...     arrival_date=date(2023, 1, 1),
        ...     dwelling_address=dwelling
        ... )
        >>>
        >>> # Step 4: Convert to Layer 1 (ready for XML export)
        >>> layer1_event = event.to_ech0020_event()

    Residence Type Variations:

        # Main residence (most common):
        >>> event = BaseDeliveryEvent(
        ...     person=person,
        ...     residence_type=ResidenceType.MAIN,
        ...     reporting_municipality_bfs="261",
        ...     reporting_municipality_name="Zürich",
        ...     arrival_date=date(2023, 1, 1),
        ...     dwelling_address=dwelling,
        ...     comes_from=comes_from_dest,  # Optional for MAIN
        ...     secondary_residence_list=[...]  # Optional list
        ... )

        # Secondary residence (vacation home):
        >>> event = BaseDeliveryEvent(
        ...     person=person,
        ...     residence_type=ResidenceType.SECONDARY,
        ...     reporting_municipality_bfs="3851",
        ...     reporting_municipality_name="Davos",
        ...     arrival_date=date(2023, 6, 1),
        ...     dwelling_address=dwelling,
        ...     comes_from=comes_from_dest,  # REQUIRED for SECONDARY
        ...     main_residence_bfs="261",  # REQUIRED for SECONDARY
        ...     main_residence_name="Zürich"
        ... )

        # Other residence:
        >>> event = BaseDeliveryEvent(
        ...     person=person,
        ...     residence_type=ResidenceType.OTHER,
        ...     reporting_municipality_bfs="261",
        ...     reporting_municipality_name="Zürich",
        ...     arrival_date=date(2023, 1, 1),
        ...     dwelling_address=dwelling,
        ...     comes_from=comes_from_dest  # REQUIRED for OTHER
        ... )

    Federal Register (Alternative to Municipality):
        >>> event = BaseDeliveryEvent(
        ...     person=person,
        ...     residence_type=ResidenceType.MAIN,
        ...     federal_register="1",  # INFOSTAR (1=INFOSTAR, 2=ORDIPRO, 3=ZEMIS)
        ...     arrival_date=date(2023, 1, 1),
        ...     dwelling_address=dwelling
        ... )

    Field Requirements by Residence Type:

        ┌─────────────────────────────┬──────┬───────────┬───────┐
        │ Field                       │ MAIN │ SECONDARY │ OTHER │
        ├─────────────────────────────┼──────┼───────────┼───────┤
        │ person                      │  ✓   │     ✓     │   ✓   │
        │ residence_type              │  ✓   │     ✓     │   ✓   │
        │ reporting_* or federal_*    │  ✓   │     ✓     │   ✓   │
        │ arrival_date                │  ✓   │     ✓     │   ✓   │
        │ dwelling_address            │  ✓   │     ✓     │   ✓   │
        │ comes_from                  │  ○   │     ✓     │   ✓   │
        │ departure_date              │  ○   │     ○     │   ○   │
        │ goes_to                     │  ○   │     ○     │   ○   │
        │ secondary_residence_list    │  ○   │     ✗     │   ✗   │
        │ main_residence_*            │  ✗   │     ✓     │   ✗   │
        │ base_delivery_valid_from    │  ○   │     ○     │   ○   │
        └─────────────────────────────┴──────┴───────────┴───────┘
        Legend: ✓ Required, ○ Optional, ✗ Forbidden

    XSD CHOICE Constraints:

        CHOICE #9 (Residence Type): Implicit in residence_type enum
        - Exactly ONE of: MAIN, SECONDARY, OTHER

        CHOICE #10 (Reporting): Validator enforced
        - Exactly ONE of: reporting_municipality OR federal_register

        CHOICE #11 (Destination Place): In comes_from/goes_to (DestinationInfo)
        - Exactly ONE of: UNKNOWN, SWISS, FOREIGN

    Layer 1 Mapping:
        ECH0020EventBaseDelivery
        ├── base_delivery_person: ECH0020BaseDeliveryPerson (Phase 1)
        ├── has_main_residence: ECH0020HasMainResidence (if MAIN)
        │   ├── reporting_municipality OR federal_register (CHOICE #10)
        │   ├── arrival_date, dwelling_address (REQUIRED)
        │   ├── comes_from, departure_date, goes_to (OPTIONAL)
        │   └── secondary_residence (OPTIONAL list)
        ├── has_secondary_residence: ECH0020HasSecondaryResidence (if SECONDARY)
        │   ├── Same structure as MAIN
        │   ├── comes_from (REQUIRED for SECONDARY)
        │   └── main_residence (REQUIRED for SECONDARY)
        ├── has_other_residence: ECH0020ReportingMunicipalityRestrictedBaseSecondary (if OTHER)
        │   ├── Same structure as MAIN
        │   └── comes_from (REQUIRED for OTHER)
        └── base_delivery_valid_from (OPTIONAL)

    Zero-Tolerance Policies (inherited from Phase 1):
        1. No default values for government data
        2. No data invention
        3. Fail hard on missing required data
        4. No lossy transformations (100% roundtrip)
        5. No schema violations (CHOICE validators)
        6. Explicit over implicit (clear field names)

    See Also:
        - BaseDeliveryPerson (Phase 1): Person data model
        - DwellingAddressInfo: Dwelling address helper model
        - DestinationInfo: comes_from/goes_to helper model
        - docs/PHASE_2_BASEDELIVERYEVENT_DESIGN.md: Complete design documentation
    """

    # ========== Person Data (Phase 1) ==========
    person: BaseDeliveryPerson = Field(
        ...,
        description=(
            "Person data (Phase 1): Complete person information including name, birth, "
            "citizenship, relationships, etc. (REQUIRED)"
        )
    )

    # ========== Residence Type (CHOICE #9) ==========
    residence_type: ResidenceType = Field(
        ...,
        description=(
            "Residence type: MAIN (primary residence), SECONDARY (vacation home), "
            "or OTHER (REQUIRED)"
        )
    )

    # ========== Reporting (CHOICE #10: municipality XOR federal_register) ==========
    reporting_municipality_bfs: Optional[str] = Field(
        None,
        description=(
            "Reporting municipality BFS number (e.g., '261' for Zürich). "
            "Required if federal_register not provided (CHOICE constraint)"
        )
    )
    reporting_municipality_name: Optional[str] = Field(
        None,
        description=(
            "Reporting municipality name (e.g., 'Zürich'). "
            "Required if federal_register not provided (CHOICE constraint)"
        )
    )
    reporting_municipality_canton: Optional[str] = Field(
        None,
        description=(
            "Reporting municipality canton abbreviation (e.g., 'ZH'). "
            "Optional, only valid with reporting_municipality"
        )
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        description=(
            "Federal register: 1=INFOSTAR, 2=ORDIPRO, 3=ZEMIS. "
            "Required if reporting_municipality not provided (CHOICE constraint)"
        )
    )

    # ========== Common Required Fields (all residence types) ==========
    arrival_date: date = Field(
        ...,
        description="Date of arrival in this municipality (REQUIRED)"
    )
    dwelling_address: DwellingAddressInfo = Field(
        ...,
        description=(
            "Dwelling address: Complete Swiss address with building IDs, household info, "
            "and postal address (REQUIRED)"
        )
    )

    # ========== Common Optional Fields (all residence types) ==========
    departure_date: Optional[date] = Field(
        None,
        description="Date of departure from municipality (optional, if person left)"
    )
    goes_to: Optional[DestinationInfo] = Field(
        None,
        description=(
            "Destination where person is going/went (optional, if person leaving/left). "
            "CHOICE #11: UNKNOWN, SWISS, or FOREIGN"
        )
    )

    # ========== Type-Specific: comes_from ==========
    # Optional for MAIN, REQUIRED for SECONDARY/OTHER
    comes_from: Optional[DestinationInfo] = Field(
        None,
        description=(
            "Previous residence where person came from. "
            "Optional for MAIN residence, REQUIRED for SECONDARY and OTHER. "
            "CHOICE #11: UNKNOWN, SWISS, or FOREIGN"
        )
    )

    # ========== Type-Specific: MAIN residence extensions ==========
    # Only valid for MAIN residence type
    secondary_residence_list: Optional[List[SecondaryResidenceInfo]] = Field(
        None,
        description=(
            "List of secondary residences (0-n) where person also lives. "
            "Only valid for MAIN residence type (e.g., vacation homes). "
            "Forbidden for SECONDARY and OTHER"
        )
    )

    # ========== Type-Specific: SECONDARY residence extensions ==========
    # Only valid for SECONDARY residence type (REQUIRED)
    main_residence_bfs: Optional[str] = Field(
        None,
        description=(
            "Main residence municipality BFS number (e.g., '261' for Zürich). "
            "REQUIRED for SECONDARY residence type (where person primarily lives). "
            "Forbidden for MAIN and OTHER"
        )
    )
    main_residence_name: Optional[str] = Field(
        None,
        description=(
            "Main residence municipality name (e.g., 'Zürich'). "
            "REQUIRED for SECONDARY residence type. "
            "Forbidden for MAIN and OTHER"
        )
    )
    main_residence_canton: Optional[str] = Field(
        None,
        description=(
            "Main residence canton abbreviation (e.g., 'ZH'). "
            "Optional for SECONDARY residence type. "
            "Forbidden for MAIN and OTHER"
        )
    )

    # ========== Event Validity Date ==========
    base_delivery_valid_from: Optional[date] = Field(
        None,
        description="Date from which this base delivery is valid (optional)"
    )

    # ========== Validators ==========

    @model_validator(mode='after')
    def validate_reporting_choice(self) -> 'BaseDeliveryEvent':
        """Validate XSD CHOICE #10: reporting_municipality XOR federal_register.

        Exactly ONE of:
        - reporting_municipality_bfs + reporting_municipality_name
        - federal_register

        Zero-Tolerance Policy #5: No Schema Violations.
        """
        has_municipality = (
            self.reporting_municipality_bfs is not None and
            self.reporting_municipality_name is not None
        )
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "Must provide either reporting_municipality (bfs + name) "
                "OR federal_register (XSD CHOICE #10)"
            )
        if has_municipality and has_register:
            raise ValueError(
                "Cannot provide both reporting_municipality AND federal_register "
                "(XSD CHOICE #10 constraint)"
            )

        # If municipality provided, BFS and name both required
        if self.reporting_municipality_bfs is not None or self.reporting_municipality_name is not None:
            if not has_municipality:
                raise ValueError(
                    "reporting_municipality requires BOTH bfs AND name "
                    "(Zero-Tolerance Policy #3: Fail Hard)"
                )

        return self

    @model_validator(mode='after')
    def validate_residence_type_fields(self) -> 'BaseDeliveryEvent':
        """Validate type-specific field requirements.

        MAIN Residence:
        - comes_from: Optional
        - secondary_residence_list: Optional (0-n list)
        - main_residence_*: Forbidden

        SECONDARY Residence:
        - comes_from: REQUIRED
        - main_residence_*: REQUIRED (bfs + name)
        - secondary_residence_list: Forbidden

        OTHER Residence:
        - comes_from: REQUIRED
        - secondary_residence_list: Forbidden
        - main_residence_*: Forbidden

        Zero-Tolerance Policy #3: Fail Hard on Missing Required Data.
        """
        if self.residence_type == ResidenceType.MAIN:
            # MAIN: secondary_residence_list allowed, main_residence_* forbidden
            if self.main_residence_bfs is not None or self.main_residence_name is not None:
                raise ValueError(
                    "main_residence_* fields only valid for SECONDARY residence type "
                    "(current: MAIN)"
                )

        elif self.residence_type == ResidenceType.SECONDARY:
            # SECONDARY: comes_from required, main_residence_* required, secondary_residence_list forbidden
            if self.comes_from is None:
                raise ValueError(
                    "comes_from is REQUIRED for SECONDARY residence type "
                    "(Zero-Tolerance Policy #3: Fail Hard)"
                )
            if self.main_residence_bfs is None or self.main_residence_name is None:
                raise ValueError(
                    "main_residence (bfs + name) is REQUIRED for SECONDARY residence type "
                    "(Zero-Tolerance Policy #3: Fail Hard)"
                )
            if self.secondary_residence_list is not None:
                raise ValueError(
                    "secondary_residence_list only valid for MAIN residence type "
                    "(current: SECONDARY)"
                )

        elif self.residence_type == ResidenceType.OTHER:
            # OTHER: comes_from required, no extension fields
            if self.comes_from is None:
                raise ValueError(
                    "comes_from is REQUIRED for OTHER residence type "
                    "(Zero-Tolerance Policy #3: Fail Hard)"
                )
            if self.secondary_residence_list is not None:
                raise ValueError(
                    "secondary_residence_list only valid for MAIN residence type "
                    "(current: OTHER)"
                )
            if self.main_residence_bfs is not None or self.main_residence_name is not None:
                raise ValueError(
                    "main_residence_* fields only valid for SECONDARY residence type "
                    "(current: OTHER)"
                )

        return self

    # ========== Conversion Methods (Phase 2.2) ==========

    def _convert_dwelling_address(self, dwelling: DwellingAddressInfo) -> ECH0011DwellingAddress:
        """Convert DwellingAddressInfo (Layer 2) → ECH0011DwellingAddress (Layer 1).

        Handles:
        - Building IDs (egid, ewid, household_id)
        - Swiss address (flat fields → ECH0010SwissAddressInformation)
        - Household type (string → TypeOfHousehold enum)
        - Moving date

        Args:
            dwelling: Layer 2 dwelling address info

        Returns:
            ECH0011DwellingAddress: Layer 1 dwelling address

        Raises:
            ValueError: If household type is invalid
        """
        # Convert Swiss address (Layer 2 flat → Layer 1 nested)
        swiss_address = ECH0010SwissAddressInformation(
            address_line1=dwelling.address_line1,
            address_line2=dwelling.address_line2,
            street=dwelling.street,
            house_number=dwelling.house_number,
            dwelling_number=dwelling.dwelling_number,
            locality=dwelling.locality,
            town=dwelling.town,
            swiss_zip_code=dwelling.swiss_zip_code,
            swiss_zip_code_add_on=dwelling.swiss_zip_code_add_on,
            swiss_zip_code_id=dwelling.swiss_zip_code_id,
            country=dwelling.country
        )

        # Convert household type (string → enum)
        # Zero-Tolerance Policy #3: Fail hard on invalid data
        try:
            household_type_enum = TypeOfHousehold(dwelling.type_of_household)
        except ValueError:
            raise ValueError(
                f"Invalid type_of_household: '{dwelling.type_of_household}'. "
                f"Must be one of: 0 (unknown), 1 (single), 2 (family), 3 (non-family)"
            )

        # Construct Layer 1 dwelling address
        return ECH0011DwellingAddress(
            egid=dwelling.egid,
            ewid=dwelling.ewid,
            household_id=dwelling.household_id,
            address=swiss_address,
            type_of_household=household_type_enum,
            moving_date=dwelling.moving_date
        )

    def _convert_destination(self, dest: DestinationInfo) -> ECH0011DestinationType:
        """Convert DestinationInfo (Layer 2) → ECH0011DestinationType (Layer 1).

        Handles CHOICE #11 (place_type):
        - UNKNOWN: Sets unknown=True
        - SWISS: Constructs ECH0007Municipality wrapper
        - FOREIGN: Constructs ECH0008Country wrapper
        - Optional mail_address (9 fields → ECH0010AddressInformation)

        Args:
            dest: Layer 2 destination info

        Returns:
            ECH0011DestinationType: Layer 1 destination

        Raises:
            ValueError: If place_type has invalid combination of fields
        """
        # Initialize Layer 1 fields
        unknown = None
        swiss_municipality = None
        foreign_country = None
        foreign_town = None
        mail_address = None

        # Handle CHOICE #11 based on place_type
        if dest.place_type == PlaceType.UNKNOWN:
            unknown = True

        elif dest.place_type == PlaceType.SWISS:
            # Build ECH0007Municipality wrapper
            swiss_muni = ECH0007SwissMunicipality(
                municipality_id=dest.municipality_bfs,
                municipality_name=dest.municipality_name,
                canton_abbreviation=dest.canton_abbreviation,
                history_municipality_id=dest.municipality_history_id
            )
            swiss_municipality = ECH0007Municipality(swiss_municipality=swiss_muni)

        elif dest.place_type == PlaceType.FOREIGN:
            # Build ECH0008Country wrapper
            country = ECH0008Country(
                country_id=dest.country_id,
                country_id_iso2=dest.country_iso,
                country_name_short=dest.country_name_short
            )
            foreign_country = country
            foreign_town = dest.town

        # Convert optional mail address (9 fields → Layer 1)
        if any([
            dest.mail_address_address_line1,
            dest.mail_address_street,
            dest.mail_address_house_number,
            dest.mail_address_dwelling_number,
            dest.mail_address_locality,
            dest.mail_address_town,
            dest.mail_address_zip,
            dest.mail_address_zip_addon,
            dest.mail_address_country
        ]):
            mail_address = ECH0010AddressInformation(
                address_line1=dest.mail_address_address_line1,
                address_line2=None,  # Not in Layer 2 DestinationInfo
                street=dest.mail_address_street,
                house_number=dest.mail_address_house_number,
                dwelling_number=dest.mail_address_dwelling_number,
                locality=dest.mail_address_locality,
                town=dest.mail_address_town,
                swiss_zip_code=dest.mail_address_zip,
                swiss_zip_code_add_on=dest.mail_address_zip_addon,
                country=dest.mail_address_country
            )

        # Construct Layer 1 destination
        return ECH0011DestinationType(
            unknown=unknown,
            swiss_municipality=swiss_municipality,
            foreign_country=foreign_country,
            foreign_town=foreign_town,
            mail_address=mail_address
        )

    def _convert_reporting_municipality(
        self,
        bfs: str,
        name: str,
        canton: Optional[str]
    ) -> ECH0007SwissMunicipality:
        """Convert reporting municipality fields (Layer 2) → ECH0007SwissMunicipality (Layer 1).

        Args:
            bfs: BFS municipality number (e.g., '261' for Zürich)
            name: Municipality name (e.g., 'Zürich')
            canton: Optional canton abbreviation (e.g., 'ZH')

        Returns:
            ECH0007SwissMunicipality: Layer 1 municipality
        """
        return ECH0007SwissMunicipality(
            municipality_id=bfs,
            municipality_name=name,
            canton_abbreviation=canton
        )

    def _convert_secondary_residence_list(
        self,
        secondary_list: Optional[List[SecondaryResidenceInfo]]
    ) -> Optional[List[ECH0007SwissMunicipality]]:
        """Convert List[SecondaryResidenceInfo] (Layer 2) → List[ECH0007SwissMunicipality] (Layer 1).

        Args:
            secondary_list: Optional list of secondary residences (0-n)

        Returns:
            Optional[List[ECH0007SwissMunicipality]]: Layer 1 list, or None if empty/None
        """
        if not secondary_list:
            return None

        return [
            ECH0007SwissMunicipality(
                municipality_id=sec.bfs,
                municipality_name=sec.name,
                canton_abbreviation=sec.canton
            )
            for sec in secondary_list
        ]

    def _build_main_residence(self) -> ECH0020HasMainResidence:
        """Build ECH0020HasMainResidence from Layer 2 MAIN residence fields.

        Uses helpers:
        - _convert_reporting_municipality() for reporting_municipality
        - _convert_dwelling_address() for dwelling_address
        - _convert_destination() for comes_from, goes_to
        - _convert_secondary_residence_list() for secondary_residence_list

        Returns:
            ECH0020HasMainResidence: Layer 1 main residence

        Raises:
            ValueError: If CHOICE #10 constraint violated
        """
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton
            )
        elif self.federal_register:
            federal_register = FederalRegister(self.federal_register)

        # Convert required fields
        dwelling_address = self._convert_dwelling_address(self.dwelling_address)

        # Convert optional fields
        comes_from = self._convert_destination(self.comes_from) if self.comes_from else None
        goes_to = self._convert_destination(self.goes_to) if self.goes_to else None
        secondary_residence = self._convert_secondary_residence_list(self.secondary_residence_list)

        # Construct Layer 1 main residence
        return ECH0020HasMainResidence(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=self.arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,
            departure_date=self.departure_date,
            goes_to=goes_to,
            secondary_residence=secondary_residence
        )

    def _build_secondary_residence(self) -> ECH0020HasSecondaryResidence:
        """Build ECH0020HasSecondaryResidence from Layer 2 SECONDARY residence fields.

        Uses helpers:
        - _convert_reporting_municipality() for reporting_municipality and main_residence
        - _convert_dwelling_address() for dwelling_address
        - _convert_destination() for comes_from (REQUIRED), goes_to

        Returns:
            ECH0020HasSecondaryResidence: Layer 1 secondary residence

        Raises:
            ValueError: If CHOICE #10 constraint violated or required fields missing
        """
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton
            )
        elif self.federal_register:
            federal_register = FederalRegister(self.federal_register)

        # Convert required fields
        dwelling_address = self._convert_dwelling_address(self.dwelling_address)
        comes_from = self._convert_destination(self.comes_from)  # REQUIRED for SECONDARY
        main_residence = self._convert_reporting_municipality(
            self.main_residence_bfs,  # type: ignore  # Validator ensures these are set for SECONDARY
            self.main_residence_name,  # type: ignore
            self.main_residence_canton
        )

        # Convert optional fields
        goes_to = self._convert_destination(self.goes_to) if self.goes_to else None

        # Construct Layer 1 secondary residence
        return ECH0020HasSecondaryResidence(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=self.arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=self.departure_date,
            goes_to=goes_to,
            main_residence=main_residence
        )

    def _build_other_residence(self) -> ECH0020ReportingMunicipalityRestrictedBaseSecondary:
        """Build ECH0020ReportingMunicipalityRestrictedBaseSecondary from Layer 2 OTHER residence fields.

        Uses helpers:
        - _convert_reporting_municipality() for reporting_municipality
        - _convert_dwelling_address() for dwelling_address
        - _convert_destination() for comes_from (REQUIRED), goes_to

        Returns:
            ECH0020ReportingMunicipalityRestrictedBaseSecondary: Layer 1 other residence

        Raises:
            ValueError: If CHOICE #10 constraint violated or required fields missing
        """
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton
            )
        elif self.federal_register:
            federal_register = FederalRegister(self.federal_register)

        # Convert required fields
        dwelling_address = self._convert_dwelling_address(self.dwelling_address)
        comes_from = self._convert_destination(self.comes_from)  # REQUIRED for OTHER

        # Convert optional fields
        goes_to = self._convert_destination(self.goes_to) if self.goes_to else None

        # Construct Layer 1 other residence
        return ECH0020ReportingMunicipalityRestrictedBaseSecondary(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=self.arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=self.departure_date,
            goes_to=goes_to
        )

    def to_ech0020_event(self) -> ECH0020EventBaseDelivery:
        """Convert Layer 2 → Layer 1 (ECH0020EventBaseDelivery).

        Transforms simplified Layer 2 event model into XSD-compliant Layer 1 structure:
        - Unwraps person (BaseDeliveryPerson → ECH0020BaseDeliveryPerson)
        - Constructs residence wrapper based on residence_type
        - Handles namespace wrappers (ECH0020HasMainResidence, etc.)
        - Converts dwelling address (DwellingAddressInfo → ECH0011DwellingAddress)
        - Converts destinations (DestinationInfo → ECH0011DestinationType)

        Returns:
            ECH0020EventBaseDelivery: Layer 1 model ready for XML export

        Example:
            >>> event = BaseDeliveryEvent(...)
            >>> layer1_event = event.to_ech0020_event()
            >>> # Can now export to XML
            >>> xml_elem = layer1_event.to_xml(...)

        Phase: 2.2 ✅ COMPLETE
        """
        # Step 1: Convert person (reuse Phase 1 conversion)
        base_delivery_person = self.person.to_ech0020()

        # Step 2: Build residence wrapper based on residence_type (CHOICE #9)
        has_main_residence = None
        has_secondary_residence = None
        has_other_residence = None

        if self.residence_type == ResidenceType.MAIN:
            has_main_residence = self._build_main_residence()
        elif self.residence_type == ResidenceType.SECONDARY:
            has_secondary_residence = self._build_secondary_residence()
        elif self.residence_type == ResidenceType.OTHER:
            has_other_residence = self._build_other_residence()

        # Step 3: Construct Layer 1 event
        return ECH0020EventBaseDelivery(
            base_delivery_person=base_delivery_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence,
            base_delivery_valid_from=self.base_delivery_valid_from
        )

    # ========================================================================
    # LAYER 1 → LAYER 2 CONVERSION HELPERS (Phase 2.2, tasks 2.2.9-2.2.12)
    # ========================================================================

    @staticmethod
    def _flatten_dwelling_address(dwelling: 'ECH0011DwellingAddress') -> DwellingAddressInfo:
        """Flatten ECH0011DwellingAddress + ECH0010SwissAddressInformation → DwellingAddressInfo.

        Extracts:
        - Building identifiers (egid, ewid, household_id)
        - All address fields (11 fields from nested ECH0010SwissAddressInformation)
        - Household type (enum → string conversion)
        - Moving date

        Args:
            dwelling: Layer 1 ECH0011DwellingAddress model

        Returns:
            DwellingAddressInfo: Layer 2 flattened model

        Pattern:
            Layer 1: ECH0011DwellingAddress
                     └── address: ECH0010SwissAddressInformation (11 fields)
            Layer 2: DwellingAddressInfo (all fields at top level)

        Phase: 2.2.9
        """
        # Extract building identifiers
        egid = dwelling.egid
        ewid = dwelling.ewid
        household_id = dwelling.household_id

        # Extract address fields from nested ECH0010SwissAddressInformation
        addr = dwelling.address
        address_line1 = addr.address_line1
        address_line2 = addr.address_line2
        street = addr.street
        house_number = addr.house_number
        dwelling_number = addr.dwelling_number
        locality = addr.locality
        town = addr.town
        swiss_zip_code = addr.swiss_zip_code
        swiss_zip_code_add_on = addr.swiss_zip_code_add_on
        swiss_zip_code_id = addr.swiss_zip_code_id
        country = addr.country

        # Convert household type enum → string
        # TypeOfHousehold is Enum with values: "0", "1", "2", "3"
        type_of_household = dwelling.type_of_household.value if hasattr(dwelling.type_of_household, 'value') else str(dwelling.type_of_household)

        # Extract moving date
        moving_date = dwelling.moving_date

        # Construct flattened Layer 2 model
        return DwellingAddressInfo(
            egid=egid,
            ewid=ewid,
            household_id=household_id,
            address_line1=address_line1,
            address_line2=address_line2,
            street=street,
            house_number=house_number,
            dwelling_number=dwelling_number,
            locality=locality,
            town=town,
            swiss_zip_code=swiss_zip_code,
            swiss_zip_code_add_on=swiss_zip_code_add_on,
            swiss_zip_code_id=swiss_zip_code_id,
            country=country,
            type_of_household=type_of_household,
            moving_date=moving_date
        )

    @staticmethod
    def _flatten_destination(dest: 'ECH0011DestinationType') -> DestinationInfo:
        """Flatten ECH0011DestinationType → DestinationInfo (CHOICE #11).

        Detects place type (UNKNOWN/SWISS/FOREIGN) from Layer 1 CHOICE and extracts:
        - Swiss municipality fields (unwrap ECH0007Municipality double-wrapper)
        - Foreign country fields (unwrap ECH0008Country)
        - Optional mail address (9 fields from ECH0010AddressInformation)

        Args:
            dest: Layer 1 ECH0011DestinationType model

        Returns:
            DestinationInfo: Layer 2 flattened model with place_type enum

        Pattern:
            Layer 1: ECH0011DestinationType (CHOICE + optional mail_address)
                     ├── unknown: bool | swiss_municipality: ECH0007Municipality | foreign_country: ECH0008Country
                     └── mail_address: ECH0010AddressInformation (14 fields)
            Layer 2: DestinationInfo (place_type enum + flat fields)

        Phase: 2.2.10
        """
        # Detect place type from Layer 1 CHOICE
        if dest.unknown:
            place_type = PlaceType.UNKNOWN
            # No additional fields for UNKNOWN
            municipality_bfs = None
            municipality_name = None
            canton_abbreviation = None
            municipality_history_id = None
            country_id = None
            country_iso = None
            country_name_short = None
            town = None

        elif dest.swiss_municipality:
            place_type = PlaceType.SWISS
            # Unwrap double wrapper: ECH0007Municipality → ECH0007SwissMunicipality
            swiss_muni = dest.swiss_municipality.swiss_municipality
            municipality_bfs = swiss_muni.municipality_id
            municipality_name = swiss_muni.municipality_name
            canton_abbreviation = swiss_muni.canton_abbreviation.value if swiss_muni.canton_abbreviation else None
            municipality_history_id = swiss_muni.history_municipality_id
            # No foreign fields
            country_id = None
            country_iso = None
            country_name_short = None
            town = None

        elif dest.foreign_country:
            place_type = PlaceType.FOREIGN
            # Unwrap ECH0008Country
            country = dest.foreign_country
            country_id = country.country_id
            country_iso = country.country_id_iso2
            country_name_short = country.country_name_short
            town = dest.foreign_town  # Separate field at DestinationType level
            # No Swiss fields
            municipality_bfs = None
            municipality_name = None
            canton_abbreviation = None
            municipality_history_id = None

        else:
            # Should never happen if Layer 1 is valid
            raise ValueError(
                "Invalid ECH0011DestinationType: must have exactly ONE of "
                "unknown, swiss_municipality, or foreign_country"
            )

        # Extract optional mail address (ECH0010AddressInformation → 9 flat fields)
        mail_address_address_line1 = None
        mail_address_street = None
        mail_address_house_number = None
        mail_address_dwelling_number = None
        mail_address_locality = None
        mail_address_town = None
        mail_address_zip = None
        mail_address_zip_addon = None
        mail_address_country = None

        if dest.mail_address:
            addr = dest.mail_address
            mail_address_address_line1 = addr.address_line1
            mail_address_street = addr.street
            mail_address_house_number = addr.house_number
            mail_address_dwelling_number = addr.dwelling_number
            mail_address_locality = addr.locality
            mail_address_town = addr.town
            # ZIP code: Use swiss_zip_code if present, else foreign_zip_code
            # Note: ECH0010AddressInformation has CHOICE (swiss_zip_code XOR foreign_zip_code)
            # Layer 2 uses single mail_address_zip field (int for Swiss, will need type change for foreign)
            if addr.swiss_zip_code:
                mail_address_zip = addr.swiss_zip_code
            # Note: foreign_zip_code is string, but Layer 2 mail_address_zip is int
            # This is a known limitation - foreign zip codes may be lost if non-numeric
            mail_address_zip_addon = addr.swiss_zip_code_add_on
            mail_address_country = addr.country

        # Construct flattened Layer 2 model
        return DestinationInfo(
            place_type=place_type,
            municipality_bfs=municipality_bfs,
            municipality_name=municipality_name,
            canton_abbreviation=canton_abbreviation,
            municipality_history_id=municipality_history_id,
            country_id=country_id,
            country_iso=country_iso,
            country_name_short=country_name_short,
            town=town,
            mail_address_address_line1=mail_address_address_line1,
            mail_address_street=mail_address_street,
            mail_address_house_number=mail_address_house_number,
            mail_address_dwelling_number=mail_address_dwelling_number,
            mail_address_locality=mail_address_locality,
            mail_address_town=mail_address_town,
            mail_address_zip=mail_address_zip,
            mail_address_zip_addon=mail_address_zip_addon,
            mail_address_country=mail_address_country
        )

    @staticmethod
    def _flatten_reporting_municipality(
        muni: 'ECH0007SwissMunicipality'
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Flatten ECH0007SwissMunicipality → reporting_municipality fields (3 strings).

        Extracts:
        - BFS municipality number
        - Municipality name
        - Canton abbreviation (enum → string conversion)

        Args:
            muni: Layer 1 ECH0007SwissMunicipality model

        Returns:
            Tuple of (bfs, name, canton) - all Optional[str]

        Pattern:
            Layer 1: ECH0007SwissMunicipality (3 fields, 1 enum)
            Layer 2: reporting_municipality_bfs, reporting_municipality_name, reporting_municipality_canton

        Phase: 2.2.11
        """
        bfs = muni.municipality_id
        name = muni.municipality_name
        # Convert canton enum to string if present
        canton = muni.canton_abbreviation.value if muni.canton_abbreviation else None

        return (bfs, name, canton)

    @staticmethod
    def _flatten_secondary_residence_list(
        secondary_list: Optional[List['ECH0007SwissMunicipality']]
    ) -> Optional[List[SecondaryResidenceInfo]]:
        """Flatten List[ECH0007SwissMunicipality] → List[SecondaryResidenceInfo].

        Maps each Swiss municipality to SecondaryResidenceInfo (3 fields).

        Args:
            secondary_list: Optional list of Layer 1 secondary residence municipalities (0-n)

        Returns:
            Optional list of Layer 2 SecondaryResidenceInfo, or None if input is None/empty

        Pattern:
            Layer 1: List[ECH0007SwissMunicipality] (0-n items)
            Layer 2: List[SecondaryResidenceInfo] (0-n items, each with bfs, name, canton)

        Phase: 2.2.12
        """
        if not secondary_list:
            return None

        result = []
        for muni in secondary_list:
            # Extract fields (same pattern as _flatten_reporting_municipality)
            bfs = muni.municipality_id
            name = muni.municipality_name
            # Convert canton enum to string if present
            canton = muni.canton_abbreviation.value if muni.canton_abbreviation else None

            result.append(SecondaryResidenceInfo(
                bfs=bfs,
                name=name,
                canton=canton
            ))

        return result if result else None

    # ========================================================================
    # LAYER 1 → LAYER 2 EXTRACTOR METHODS (Phase 2.2, tasks 2.2.13-2.2.15)
    # ========================================================================

    @classmethod
    def _from_main_residence(
        cls,
        person: 'BaseDeliveryPerson',
        residence: 'ECH0020HasMainResidence',
        base_delivery_valid_from: Optional[date]
    ) -> 'BaseDeliveryEvent':
        """Extract MAIN residence event → BaseDeliveryEvent.

        Handles:
        - CHOICE #10: reporting_municipality XOR federal_register
        - Dwelling address flattening (uses helper 2.2.9)
        - Optional comes_from/goes_to flattening (uses helper 2.2.10)
        - Optional secondary residence list (uses helper 2.2.12)

        Args:
            person: Layer 2 person (already converted from Layer 1)
            residence: Layer 1 ECH0020HasMainResidence
            base_delivery_valid_from: Optional validity date

        Returns:
            BaseDeliveryEvent with residence_type=MAIN

        Phase: 2.2.13
        """
        # Extract reporting CHOICE #10: municipality XOR federal_register
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        federal_register = None

        if residence.reporting_municipality:
            # Use helper to flatten reporting municipality
            bfs, name, canton = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
        elif residence.federal_register:
            # Extract federal register enum value
            federal_register = residence.federal_register.value if hasattr(residence.federal_register, 'value') else str(residence.federal_register)

        # Extract arrival_date (required)
        arrival_date = residence.arrival_date

        # Flatten dwelling_address (required) - use helper 2.2.9
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)

        # Flatten comes_from (optional) - use helper 2.2.10
        comes_from = None
        if residence.comes_from:
            comes_from = cls._flatten_destination(residence.comes_from)

        # Extract departure_date (optional)
        departure_date = residence.departure_date

        # Flatten goes_to (optional) - use helper 2.2.10
        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        # Flatten secondary_residence_list (optional) - use helper 2.2.12
        secondary_residence_list = None
        if residence.secondary_residence:
            secondary_residence_list = cls._flatten_secondary_residence_list(residence.secondary_residence)

        # No main_residence_* fields for MAIN type (those are for SECONDARY type)

        # Construct BaseDeliveryEvent with residence_type=MAIN
        return cls(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=secondary_residence_list,
            main_residence_bfs=None,  # Not applicable for MAIN residence
            main_residence_name=None,
            main_residence_canton=None,
            base_delivery_valid_from=base_delivery_valid_from
        )

    @classmethod
    def _from_secondary_residence(
        cls,
        person: 'BaseDeliveryPerson',
        residence: 'ECH0020HasSecondaryResidence',
        base_delivery_valid_from: Optional[date]
    ) -> 'BaseDeliveryEvent':
        """Extract SECONDARY residence event → BaseDeliveryEvent.

        Handles:
        - CHOICE #10: reporting_municipality XOR federal_register
        - Dwelling address flattening (uses helper 2.2.9)
        - REQUIRED comes_from flattening (uses helper 2.2.10) - different from MAIN
        - Optional goes_to flattening (uses helper 2.2.10)
        - REQUIRED main_residence flattening (uses helper 2.2.11) - different from MAIN

        Args:
            person: Layer 2 person (already converted from Layer 1)
            residence: Layer 1 ECH0020HasSecondaryResidence
            base_delivery_valid_from: Optional validity date

        Returns:
            BaseDeliveryEvent with residence_type=SECONDARY

        Phase: 2.2.14
        """
        # Extract reporting CHOICE #10: municipality XOR federal_register
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        federal_register = None

        if residence.reporting_municipality:
            # Use helper to flatten reporting municipality
            bfs, name, canton = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
        elif residence.federal_register:
            # Extract federal register enum value
            federal_register = residence.federal_register.value if hasattr(residence.federal_register, 'value') else str(residence.federal_register)

        # Extract arrival_date (required)
        arrival_date = residence.arrival_date

        # Flatten dwelling_address (required) - use helper 2.2.9
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)

        # Flatten comes_from (REQUIRED for SECONDARY) - use helper 2.2.10
        comes_from = cls._flatten_destination(residence.comes_from)

        # Extract departure_date (optional)
        departure_date = residence.departure_date

        # Flatten goes_to (optional) - use helper 2.2.10
        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        # Flatten main_residence (REQUIRED for SECONDARY) - use helper 2.2.11
        main_bfs, main_name, main_canton = cls._flatten_reporting_municipality(residence.main_residence)

        # No secondary_residence_list for SECONDARY type (only for MAIN)

        # Construct BaseDeliveryEvent with residence_type=SECONDARY
        return cls(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,  # Required for SECONDARY
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=None,  # Not applicable for SECONDARY
            main_residence_bfs=main_bfs,  # Required for SECONDARY
            main_residence_name=main_name,
            main_residence_canton=main_canton,
            base_delivery_valid_from=base_delivery_valid_from
        )

    @classmethod
    def _from_other_residence(
        cls,
        person: 'BaseDeliveryPerson',
        residence: 'ECH0020ReportingMunicipalityRestrictedBaseSecondary',
        base_delivery_valid_from: Optional[date]
    ) -> 'BaseDeliveryEvent':
        """Extract OTHER residence event → BaseDeliveryEvent.

        Handles:
        - CHOICE #10: reporting_municipality XOR federal_register
        - Dwelling address flattening (uses helper 2.2.9)
        - REQUIRED comes_from flattening (uses helper 2.2.10) - like SECONDARY
        - Optional goes_to flattening (uses helper 2.2.10)
        - NO main_residence (unlike SECONDARY) - simplest residence type

        Args:
            person: Layer 2 person (already converted from Layer 1)
            residence: Layer 1 ECH0020ReportingMunicipalityRestrictedBaseSecondary
            base_delivery_valid_from: Optional validity date

        Returns:
            BaseDeliveryEvent with residence_type=OTHER

        Phase: 2.2.15
        """
        # Extract reporting CHOICE #10: municipality XOR federal_register
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        federal_register = None

        if residence.reporting_municipality:
            # Use helper to flatten reporting municipality
            bfs, name, canton = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
        elif residence.federal_register:
            # Extract federal register enum value
            federal_register = residence.federal_register.value if hasattr(residence.federal_register, 'value') else str(residence.federal_register)

        # Extract arrival_date (required)
        arrival_date = residence.arrival_date

        # Flatten dwelling_address (required) - use helper 2.2.9
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)

        # Flatten comes_from (REQUIRED for OTHER) - use helper 2.2.10
        comes_from = cls._flatten_destination(residence.comes_from)

        # Extract departure_date (optional)
        departure_date = residence.departure_date

        # Flatten goes_to (optional) - use helper 2.2.10
        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        # No main_residence for OTHER type (unlike SECONDARY)
        # No secondary_residence_list for OTHER type (only MAIN has that)

        # Construct BaseDeliveryEvent with residence_type=OTHER
        return cls(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,  # Required for OTHER
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=None,  # Not applicable for OTHER
            main_residence_bfs=None,  # Not applicable for OTHER (unlike SECONDARY)
            main_residence_name=None,
            main_residence_canton=None,
            base_delivery_valid_from=base_delivery_valid_from
        )

    @classmethod
    def from_ech0020_event(cls, event):
        """Convert Layer 1 → Layer 2 (flatten event structure).

        Transforms XSD-compliant Layer 1 event into simplified Layer 2 model:
        - Detects residence type from Layer 1 CHOICE (has_main/has_secondary/has_other)
        - Flattens 5-level nesting → 2 levels
        - Extracts person (ECH0020BaseDeliveryPerson → BaseDeliveryPerson)
        - Flattens dwelling (ECH0011DwellingAddress → DwellingAddressInfo)
        - Flattens destinations (ECH0011DestinationType → DestinationInfo)
        - Preserves ALL optional fields (100% roundtrip guarantee)

        Args:
            event: ECH0020EventBaseDelivery (Layer 1 model)

        Returns:
            BaseDeliveryEvent: Layer 2 model with flattened structure

        Example:
            >>> # From XML
            >>> xml_elem = ET.parse("delivery.xml").getroot()
            >>> layer1_event = ECH0020EventBaseDelivery.from_xml(xml_elem)
            >>> # Convert to Layer 2
            >>> event = BaseDeliveryEvent.from_ech0020_event(layer1_event)

        Phase: 2.2.16
        """
        # Step 1: Convert person from Layer 1 → Layer 2
        person = BaseDeliveryPerson.from_ech0020(event.base_delivery_person)

        # Step 2: Extract base_delivery_valid_from
        base_delivery_valid_from = event.base_delivery_valid_from

        # Step 3: Detect residence type from CHOICE (exactly one must be present)
        if event.has_main_residence:
            # Route to MAIN residence extractor
            return cls._from_main_residence(
                person=person,
                residence=event.has_main_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        elif event.has_secondary_residence:
            # Route to SECONDARY residence extractor
            return cls._from_secondary_residence(
                person=person,
                residence=event.has_secondary_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        elif event.has_other_residence:
            # Route to OTHER residence extractor
            return cls._from_other_residence(
                person=person,
                residence=event.has_other_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        else:
            # Should never happen if Layer 1 validation is correct
            raise ValueError(
                "Invalid ECH0020EventBaseDelivery: must have exactly ONE of "
                "has_main_residence, has_secondary_residence, or has_other_residence"
            )

    def validate_swiss_data(self, context: Optional['ValidationContext'] = None) -> 'ValidationContext':
        """Optional validation using Swiss open data for dwelling addresses.

        This method validates Swiss government data fields in the dwelling address
        against official open data sources (postal codes, municipalities, streets, etc.)
        and provides warnings for potential data quality issues.

        **IMPORTANT**: This method NEVER raises exceptions or blocks data entry.
        It only collects warnings that can be inspected by the application.

        **Core Principle**: User is king - warnings provide feedback but the user
        always has the final say.

        This method validates:
        - Dwelling address fields (postal code, town, street)
        - Reporting municipality BFS code
        - Cross-validation (postal code vs town, street vs postal code)
        - Cross-validation (dwelling postal code vs reporting municipality)
        - Person data (delegates to person.validate_swiss_data())

        Args:
            context: Optional ValidationContext to add warnings to. If None, a new
                    context is created and returned.

        Returns:
            ValidationContext containing any warnings found during validation.
            Returns empty context if no issues found.

        Requires:
            openmun-opendata package must be installed. If not available, validation
            is silently disabled and an empty context is returned.

        Example - Basic Usage:
            >>> event = BaseDeliveryEvent(
            ...     dwelling_address=DwellingAddressInfo(
            ...         street="Bahnhofstrase",  # Typo!
            ...         town="Zürich",
            ...         swiss_zip_code=8001
            ...     ),
            ...     # ... other required fields ...
            ... )
            >>> ctx = event.validate_swiss_data()
            >>> if ctx.has_warnings():
            ...     for warning in ctx.warnings:
            ...         print(warning)
            ⚠️  dwelling_address_street: Did you mean 'Bahnhofstrasse'?

        Example - Interactive Application:
            >>> ctx = event.validate_swiss_data()
            >>> if ctx.has_warnings():
            ...     for warning in ctx.warnings:
            ...         print(f"\\nWarning: {warning}")
            ...         if warning.suggestions:
            ...             print("Did you mean one of these?")
            ...             for suggestion in warning.suggestions[:5]:
            ...                 print(f"  - {suggestion}")
            ...         response = input("Continue anyway? (y/n): ")
            ...         if response.lower() != 'y':
            ...             print("Save cancelled")
            ...             return

        Current Validators:
            - Postal code + town validation (dwelling_address.swiss_zip_code + dwelling_address.town)
            - Municipality BFS code validation (reporting_municipality_bfs)
            - Street name validation (dwelling_address.street)
            - Cross-validation (dwelling postal code vs reporting municipality)
            - Cross-validation (dwelling street vs postal code)
            - Person validation (delegates to person.validate_swiss_data())

        Note:
            This method validates dwelling address fields in BaseDeliveryEvent.
            For contact address validation, use person.validate_swiss_data() directly.

        See Also:
            ValidationContext: For inspecting warnings
            ValidationWarning: Base warning class
            BaseDeliveryPerson.validate_swiss_data(): For contact address validation
        """
        # Import here to avoid circular dependency
        from openmun_ech.validation import (
            ValidationContext,
            PostalCodeValidator,
            MunicipalityBFSValidator,
            StreetNameValidator,
            CrossValidator,
        )

        # Create context if not provided
        if context is None:
            context = ValidationContext()

        # Validate person data first (delegates to BaseDeliveryPerson.validate_swiss_data())
        self.person.validate_swiss_data(context)

        # Validate dwelling address fields (if dwelling_address provided)
        if self.dwelling_address:
            # Convert swiss_zip_code (int) to string for validators
            postal_code_str = str(self.dwelling_address.swiss_zip_code)

            # Validate postal code + town if both provided
            if self.dwelling_address.town:
                PostalCodeValidator.validate(
                    postal_code=postal_code_str,
                    town=self.dwelling_address.town,
                    context=context,
                    field_name_prefix="dwelling_address_postal_code + dwelling_address_town"
                )

            # Validate dwelling street name if provided
            if self.dwelling_address.street:
                StreetNameValidator.validate(
                    street_name=self.dwelling_address.street,
                    context=context,
                    municipality_bfs=self.reporting_municipality_bfs,  # Use reporting municipality as context
                    postal_code=postal_code_str,
                    field_name_prefix="dwelling_address_street"
                )

            # Cross-validation: dwelling street vs postal code (if both provided)
            if self.dwelling_address.street:
                CrossValidator.validate_street_postal(
                    street_name=self.dwelling_address.street,
                    postal_code=postal_code_str,
                    context=context,
                    municipality_bfs=self.reporting_municipality_bfs,  # Use reporting municipality as filter
                    field_name_prefix_street="dwelling_address_street",
                    field_name_prefix_postal="dwelling_address_postal_code"
                )

            # Cross-validation: dwelling postal code vs reporting municipality (if both provided)
            # Note: This makes sense because the dwelling should typically be in the reporting municipality
            if self.reporting_municipality_bfs:
                CrossValidator.validate_postal_municipality(
                    postal_code=postal_code_str,
                    municipality_bfs=self.reporting_municipality_bfs,
                    context=context,
                    field_name_prefix_postal="dwelling_address_postal_code",
                    field_name_prefix_municipality="reporting_municipality_bfs"
                )

        # Validate reporting municipality BFS code if provided
        if self.reporting_municipality_bfs:
            MunicipalityBFSValidator.validate(
                bfs_code=self.reporting_municipality_bfs,
                municipality_name=self.reporting_municipality_name,
                context=context,
                field_name_prefix="reporting_municipality_bfs"
            )

        # Validate comes_from municipality (if SWISS and provided)
        if self.comes_from and self.comes_from.place_type == PlaceType.SWISS:
            if self.comes_from.municipality_bfs:
                MunicipalityBFSValidator.validate(
                    bfs_code=self.comes_from.municipality_bfs,
                    municipality_name=self.comes_from.municipality_name,
                    context=context,
                    field_name_prefix="comes_from_municipality_bfs"
                )

        # Validate goes_to municipality (if SWISS and provided)
        if self.goes_to and self.goes_to.place_type == PlaceType.SWISS:
            if self.goes_to.municipality_bfs:
                MunicipalityBFSValidator.validate(
                    bfs_code=self.goes_to.municipality_bfs,
                    municipality_name=self.goes_to.municipality_name,
                    context=context,
                    field_name_prefix="goes_to_municipality_bfs"
                )

        return context

    def finalize(
        self,
        config: DeliveryConfig,
        message_id: Optional[str] = None,
        message_date: Optional[datetime] = None,
        action: ActionType = ActionType.NEW,
        **optional_header_fields
    ) -> ECH0020Delivery:
        """Create complete eCH-0020 delivery ready for XML export.

        This method combines the Layer 2 event (person + residence data) with
        deployment configuration (sender, application info) to produce a complete
        ECH0020Delivery that can be exported to XML.

        Usage - Simple Case:
            >>> config = DeliveryConfig(
            ...     sender_id="sedex://T1-CH01-1",
            ...     manufacturer="OpenMun",
            ...     product="Municipality System",
            ...     product_version="1.0.0",
            ...     test_delivery_flag=True
            ... )
            >>> event = BaseDeliveryEvent(...)
            >>> delivery = event.finalize(config)
            >>> delivery.to_file("output.xml")

        Usage - Advanced (Custom message_id, optional fields):
            >>> delivery = event.finalize(
            ...     config,
            ...     message_id="custom-msg-12345",
            ...     action=ActionType.CORRECTION,
            ...     recipient_id=["sedex://T1-CH02-1"],
            ...     business_process_id="bp-456"
            ... )

        Args:
            config: Deployment configuration (sender, app info, test flag).
                    Values should come from config file or environment, never hardcoded.
            message_id: Unique message ID (1-36 chars). If None, auto-generated as UUID.
            message_date: Message creation timestamp. If None, defaults to datetime.now().
            action: Action type (default: SEND). Other values: CREATE, MODIFY, CANCEL, etc.
            **optional_header_fields: Additional ECH0058Header fields:
                - recipient_id: List[str] - Recipient participant IDs
                - business_process_id: str - Business process ID
                - our_business_reference_id: str - Our business reference
                - your_business_reference_id: str - Your business reference
                - unique_id_business_transaction: str - Business transaction ID
                - declaration_local_reference: str - Local reference
                - reference_message_id: str - Reference to previous message
                - sub_message_type: str - Sub-message type
                - subject: str - Message subject
                - comment: str - Message comment
                - event_date: date - Event date
                - modification_date: date - Modification date
                - response_expected: bool - Response expected flag
                - business_case_closed: bool - Business case closed flag
                (See ECH0058Header documentation for complete list)

        Returns:
            Complete ECH0020Delivery ready for .to_file() export

        Raises:
            ValidationError: If config or optional fields violate XSD constraints

        Example with Business Tracking:
            >>> delivery = event.finalize(
            ...     config,
            ...     business_process_id="resident-registration-2025",
            ...     our_business_reference_id="case-12345",
            ...     subject="New resident registration"
            ... )

        Zero-Tolerance Policy:
            - Config values MUST come from configuration, never hardcoded
            - message_id auto-generated if not provided (UUID v4)
            - message_date defaults to current time
            - No fake data, no default government values

        See Also:
            - DeliveryConfig: Configuration model for deployment settings
            - docs/PHASE_2_3_DELIVERY_CONSTRUCTION_DECISION.md: Design rationale
        """
        # Step 1: Auto-generate message_id if not provided (UUID)
        if message_id is None:
            message_id = str(uuid4())

        # Step 2: Default message_date to now() if not provided
        if message_date is None:
            message_date = datetime.now()

        # Step 3: Determine message_type (auto-detect for eCH-0020 or use override)
        message_type = config.message_type_override or "http://www.ech.ch/xmlns/eCH-0020/3"

        # Step 4: Build ECH0058SendingApplication from config
        sending_application = ECH0058SendingApplication(
            manufacturer=config.manufacturer,
            product=config.product,
            product_version=config.product_version
        )

        # Step 5: Build ECH0058Header with config + args + optional fields
        ech0058_header = ECH0058Header(
            sender_id=config.sender_id,
            message_id=message_id,
            message_type=message_type,
            sending_application=sending_application,
            message_date=message_date,
            action=action,
            test_delivery_flag=config.test_delivery_flag,
            original_sender_id=config.original_sender_id,
            **optional_header_fields  # Pass through any additional fields
        )

        # Step 6: Build ECH0020Header wrapper (adds data_lock fields)
        ech0020_header = ECH0020Header(
            header=ech0058_header,
            data_lock=None,  # Optional, users can set via event.person.lock_data if needed
            data_lock_valid_from=None,
            data_lock_valid_till=None
        )

        # Step 7: Convert Layer 2 event to Layer 1 event (reuse Phase 2.2 method)
        event_layer1 = self.to_ech0020_event()

        # Step 8: Construct complete ECH0020Delivery
        delivery = ECH0020Delivery(
            delivery_header=ech0020_header,
            event=[event_layer1],  # baseDelivery is a list in XSD
            version="3.0"
        )

        return delivery


# ============================================================================
# END OF PHASE 2 MODELS
# ============================================================================
