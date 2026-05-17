"""eCH-0099 Layer 2: Simplified Models for Statistics Export.

Layer 2 provides a flattened, user-friendly API for constructing eCH-0099 deliveries
from application data. This layer hides XML complexity while maintaining 100% XSD
compliance through conversion to Layer 1 models.

Architecture:
- Layer 1 (v2.py): XSD-faithful models for XML roundtrip
- Layer 2 (this file): Simplified models for application use (export only)

Design Principles (Zero Tolerance):
1. No default values for government data
2. No data invention
3. Fail hard on missing required data
4. No lossy transformations
5. No schema violations
6. Explicit over implicit

Version Independence:
- This Layer 2 API is independent from eCH-0020
- Standards can evolve separately without coupling

Implementation Status:
- Phase 1: Model Design - COMPLETE
- Phase 2: Layer 2 → Layer 1 Export - COMPLETE
- Phase 3: Finalization API - COMPLETE
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# Import Layer 1 models for conversion
from openmun_ech.ech0099.v2 import (
    ECH0099Delivery,
    ECH0099ReportedPerson,
    ECH0099DataType,
)
from openmun_ech.ech0011 import (
    ECH0011Person,
    ECH0011ReportedPerson,
    ECH0011NameData,
    ECH0011BirthData,
    ECH0011ReligionData,
    ECH0011MaritalData,
    ECH0011NationalityData,
    ECH0011CountryInfo,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathData,
    ECH0011DeathPeriod,
    ECH0011ContactData,
    ECH0011GeneralPlace,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    ECH0011ResidenceData,
    ECH0011MainResidence,
    ECH0011SecondaryResidence,
    ECH0011OtherResidence,
    ECH0011ForeignerName,
    ECH0011SeparationData,
    MaritalStatus,
    SeparationType,
    TypeOfHousehold,
)
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044NamedPersonId,
    ECH0044DatePartiallyKnown,
    Sex,
)
from openmun_ech.ech0007 import ECH0007Municipality, ECH0007SwissMunicipality
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0010 import (
    ECH0010SwissAddressInformation,
    ECH0010MailAddress,
    ECH0010AddressInformation,
    ECH0010PersonMailAddressInfo,
    ECH0010OrganisationMailAddressInfo,
)
from openmun_ech.ech0058.v4 import ECH0058Header, ECH0058SendingApplication
from openmun_ech.ech0058 import ActionType
from openmun_ech.core import NS


# ============================================================================
# ENUMS FOR CHOICE CONSTRAINTS
# ============================================================================

class ResidenceType(str, Enum):
    """Residence type CHOICE (hasMainResidence XOR hasSecondaryResidence XOR hasOtherResidence)."""
    MAIN = "main"
    SECONDARY = "secondary"
    OTHER = "other"


class PlaceType(str, Enum):
    """Place type CHOICE for destinations (unknown XOR swiss_municipality XOR foreign_country)."""
    UNKNOWN = "unknown"
    SWISS = "swiss"
    FOREIGN = "foreign"


class NationalityType(str, Enum):
    """Nationality status CHOICE (Swiss with places of origin XOR Foreign with residence permit)."""
    SWISS = "swiss"
    FOREIGN = "foreign"


# ============================================================================
# SUPPORTING MODELS
# ============================================================================

class PlaceOfOriginInfo(BaseModel):
    """Flattened place of origin for Swiss citizens.

    Maps to eCH-0011:placeOfOriginType.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    # Origin municipality (from eCH-0007)
    origin_name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Name of place of origin (required)"
    )
    canton: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Canton abbreviation, e.g., 'ZH' (required)"
    )
    origin_id: Optional[int] = Field(
        None,
        description="BFS code for place of origin (optional)"
    )
    history_municipality_id: Optional[str] = Field(
        None,
        description="Historical BFS municipality ID (for merged municipalities)"
    )


class DwellingAddressInfo(BaseModel):
    """Flattened dwelling address.

    Maps to eCH-0011:dwellingAddressType which contains:
    - Building/dwelling IDs (optional)
    - eCH-0010:swissAddressInformationType (required)
    - Household type (required)
    - Moving date (optional)
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    # Building and dwelling identifiers (optional)
    egid: Optional[int] = Field(
        None,
        ge=1,
        le=999999999,
        description="Federal Building ID (EGID)"
    )
    ewid: Optional[int] = Field(
        None,
        ge=1,
        le=999,
        description="Federal Dwelling ID (EWID)"
    )
    household_id: Optional[str] = Field(
        None,
        description="Household identifier"
    )

    # Address fields from eCH-0010:swissAddressInformationType
    address_line1: Optional[str] = Field(
        None,
        max_length=60,
        description="Address line 1"
    )
    address_line2: Optional[str] = Field(
        None,
        max_length=60,
        description="Address line 2"
    )
    street: Optional[str] = Field(
        None,
        max_length=60,
        description="Street name"
    )
    house_number: Optional[str] = Field(
        None,
        max_length=12,
        description="House number"
    )
    dwelling_number: Optional[str] = Field(
        None,
        max_length=10,
        description="Dwelling/apartment number"
    )
    locality: Optional[str] = Field(
        None,
        max_length=40,
        description="Locality name"
    )
    town: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Town/city name (required)"
    )
    swiss_zip_code: int = Field(
        ...,
        ge=1000,
        le=9999,
        description="Swiss postal code (required, 4 digits)"
    )
    swiss_zip_code_add_on: Optional[str] = Field(
        None,
        max_length=2,
        description="Postal code add-on (00-99)"
    )
    swiss_zip_code_id: Optional[int] = Field(
        None,
        description="Postal code ID"
    )
    country: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Country code (ISO 3166-1 alpha-2), defaults to 'CH'"
    )

    # Household type (required)
    type_of_household: str = Field(
        ...,
        description="Type of household: '0'=unknown, '1'=single, '2'=family, '3'=non-family"
    )

    # Moving date (optional)
    moving_date: Optional[date] = Field(
        None,
        description="Date of moving into dwelling"
    )

    @field_validator('type_of_household')
    @classmethod
    def validate_household_type(cls, v: str) -> str:
        """Validate household type is valid enum value."""
        valid = {'0', '1', '2', '3'}
        if v not in valid:
            raise ValueError(f"type_of_household must be one of {valid}, got: {v}")
        return v


class DestinationInfo(BaseModel):
    """Flattened destination (comes_from / goes_to).

    Maps to eCH-0011:destinationType with CHOICE:
    - unknown (bool)
    - swissTown (municipality)
    - foreignCountry (country)
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    place_type: PlaceType = Field(
        ...,
        description="Type of destination: UNKNOWN, SWISS, or FOREIGN"
    )

    # Swiss municipality fields (when place_type == SWISS)
    municipality_bfs: Optional[int] = Field(
        None,
        description="BFS municipality number (for Swiss destinations)"
    )
    municipality_name: Optional[str] = Field(
        None,
        max_length=40,
        description="Municipality name (for Swiss destinations)"
    )
    municipality_canton: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Canton abbreviation (for Swiss destinations)"
    )
    municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS municipality ID (for merged municipalities)"
    )

    # Foreign country fields (when place_type == FOREIGN)
    country_id: Optional[int] = Field(
        None,
        description="Country ID (for foreign destinations)"
    )
    country_iso2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code (for foreign destinations)"
    )
    country_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Country name (for foreign destinations)"
    )
    foreign_town: Optional[str] = Field(
        None,
        max_length=100,
        description="Town name in foreign country (for foreign destinations)"
    )

    # Mail address fields (optional - for previous dwelling address)
    mail_address_street: Optional[str] = Field(
        None,
        max_length=60,
        description="Street name at previous address"
    )
    mail_address_house_number: Optional[str] = Field(
        None,
        max_length=12,
        description="House number at previous address"
    )
    mail_address_town: Optional[str] = Field(
        None,
        max_length=40,
        description="Town at previous address"
    )
    mail_address_swiss_zip_code: Optional[int] = Field(
        None,
        ge=1000,
        le=9999,
        description="Swiss postal code at previous address"
    )
    mail_address_swiss_zip_code_addon: Optional[str] = Field(
        None,
        max_length=2,
        description="Swiss postal code add-on at previous address"
    )
    mail_address_foreign_zip_code: Optional[str] = Field(
        None,
        max_length=15,
        description="Foreign postal code at previous address"
    )
    mail_address_country: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Country code at previous address"
    )

    @model_validator(mode='after')
    def validate_place_choice(self) -> 'DestinationInfo':
        """Validate that correct fields are set for place_type."""
        if self.place_type == PlaceType.SWISS:
            if not self.municipality_name:
                raise ValueError("municipality_name required when place_type is SWISS")
        elif self.place_type == PlaceType.FOREIGN:
            if not self.country_iso2 and not self.country_id:
                raise ValueError("country_iso2 or country_id required when place_type is FOREIGN")
        # UNKNOWN requires no additional fields
        return self


# ============================================================================
# MAIN LAYER 2 MODELS
# ============================================================================

class StatisticsPerson(BaseModel):
    """Layer 2 flattened person for eCH-0099 statistics delivery.

    This model flattens the nested eCH-0011:personType structure into a
    user-friendly flat model. Use to_ech0011_person() for conversion to
    Layer 1 models.

    Required Fields:
    - Identification: local_person_id, local_person_id_category, official_name, first_name, sex, date_of_birth
    - Religion: religion
    - Marital: marital_status
    - Nationality: nationality_type (+ places_of_origin OR residence_permit fields)

    Zero-Tolerance Policy:
    - No defaults for government data
    - Missing required fields → ValidationError
    - No data invention
    """
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # ========================================================================
    # Person Identification (eCH-0044)
    # ========================================================================

    vn: Optional[str] = Field(
        None,
        min_length=13,
        max_length=13,
        pattern=r'^\d{13}$',
        description="Swiss social security number (AHVN13), 13 digits"
    )
    local_person_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Local person identifier (required)"
    )
    local_person_id_category: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Category of local person ID, e.g., 'MU.6172' (required)"
    )
    other_person_ids: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Other person IDs (e.g., CH.ZAR, CH.ZEMIS). Each dict has 'person_id' and 'person_id_category' keys."
    )
    eu_person_ids: Optional[List[Dict[str, str]]] = Field(
        None,
        description="EU person IDs. Each dict has 'person_id' and 'person_id_category' keys (e.g., EU.EESSI)."
    )
    official_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official family name (required)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name(s) (required)"
    )
    original_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Original name (maiden name)"
    )
    sex: str = Field(
        ...,
        description="Sex: '1'=male, '2'=female, '3'=other"
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth (required)"
    )

    # ========================================================================
    # Name Data (eCH-0011)
    # ========================================================================

    # Names already covered in identification; additional optional fields:
    call_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Call name / preferred name"
    )
    title: Optional[str] = Field(
        None,
        max_length=50,
        description="Title (Dr., Prof., etc.)"
    )
    alliance_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Alliance name (name through marriage)"
    )
    alias_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Alias name"
    )
    other_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Other name"
    )

    # Foreign name fields (eCH-0011 nameData choice: nameOnForeignPassport XOR declaredForeignName)
    name_on_foreign_passport_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Last name as it appears on foreign passport"
    )
    name_on_foreign_passport_first_name: Optional[str] = Field(
        None,
        max_length=100,
        description="First name as it appears on foreign passport"
    )
    declared_foreign_name_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Declared foreign last name"
    )
    declared_foreign_name_first_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Declared foreign first name"
    )

    # ========================================================================
    # Birth Data (eCH-0011)
    # ========================================================================

    birth_place_type: PlaceType = Field(
        ...,
        description="Type of birth place: UNKNOWN, SWISS, or FOREIGN"
    )

    # Swiss birth place
    birth_municipality_bfs: Optional[int] = Field(
        None,
        description="Birth municipality BFS number (for Swiss birth place)"
    )
    birth_municipality_name: Optional[str] = Field(
        None,
        max_length=40,
        description="Birth municipality name (for Swiss birth place)"
    )
    birth_municipality_canton: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Birth municipality canton (for Swiss birth place)"
    )

    # Foreign birth place
    birth_country_id: Optional[int] = Field(
        None,
        description="Birth country ID (for foreign birth place)"
    )
    birth_country_iso2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Birth country ISO code (for foreign birth place)"
    )
    birth_country_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Birth country name (for foreign birth place)"
    )
    birth_municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS municipality ID for birth place (for merged municipalities)"
    )

    # ========================================================================
    # Religion Data (eCH-0011)
    # ========================================================================

    religion: str = Field(
        ...,
        description="Religion code per BFS (required)"
    )
    religion_valid_from: Optional[date] = Field(
        None,
        description="Date when religion status became valid"
    )

    # ========================================================================
    # Marital Data (eCH-0011)
    # ========================================================================

    marital_status: str = Field(
        ...,
        description="Marital status: '1'=single, '2'=married, '3'=widowed, etc. (required)"
    )
    date_of_marital_status: Optional[date] = Field(
        None,
        description="Date of current marital status"
    )
    marital_cancelation_reason: Optional[str] = Field(
        None,
        description="Reason for marriage/partnership cancelation (per eCH-0011 partnershipAbolition)"
    )
    marital_status_verified: Optional[bool] = Field(
        None,
        description="Official proof of marital status (officialProofOfMaritalStatusYesNo)"
    )

    # Separation data (optional within marital data)
    separation_type: Optional[str] = Field(
        None,
        description="Separation type: '1'=judicial, '2'=de facto"
    )
    separation_since: Optional[date] = Field(
        None,
        description="Date when separation began"
    )
    separation_till: Optional[date] = Field(
        None,
        description="Date when separation ended (if applicable)"
    )

    # ========================================================================
    # Nationality Data (eCH-0011)
    # ========================================================================

    nationality_type: NationalityType = Field(
        ...,
        description="SWISS (with places of origin) or FOREIGN (with residence permit)"
    )

    # REQUIRED: nationality_status from source data - NEVER invent this!
    # Per eCH-0011: 0=unknown, 1=stateless, 2=has known nationality
    nationality_status: str = Field(
        ...,
        description="Nationality status per eCH-0011: 0=unknown, 1=stateless, 2=known. REQUIRED from source data."
    )

    # Swiss nationality - places of origin (when nationality_type == SWISS)
    places_of_origin: List[PlaceOfOriginInfo] = Field(
        default_factory=list,
        description="Places of origin for Swiss citizens (at least one required if SWISS)"
    )

    # Foreign nationality - country info (ALL REQUIRED for foreign nationals)
    nationality_country_id: Optional[int] = Field(
        None,
        description="Nationality country BFS ID (REQUIRED for foreign nationals)"
    )
    nationality_country_iso2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Nationality country ISO code (REQUIRED for foreign nationals)"
    )
    nationality_country_name: Optional[str] = Field(
        None,
        description="Nationality country name (REQUIRED for foreign nationals)"
    )
    nationality_valid_from: Optional[date] = Field(
        None,
        description="Date when nationality status became valid"
    )

    # Foreign nationality - residence permit
    residence_permit: Optional[str] = Field(
        None,
        description="Residence permit category (for foreign nationals)"
    )
    residence_permit_valid_from: Optional[date] = Field(
        None,
        description="Residence permit valid from date"
    )
    residence_permit_valid_till: Optional[date] = Field(
        None,
        description="Residence permit valid till date"
    )
    entry_date: Optional[date] = Field(
        None,
        description="Entry date to Switzerland (for foreign nationals)"
    )

    # ========================================================================
    # Optional Person Data
    # ========================================================================

    death_date: Optional[date] = Field(
        None,
        description="Date of death or start of death period (if deceased)"
    )
    death_date_end: Optional[date] = Field(
        None,
        description="End of death period (for unknown exact date of death)"
    )

    # Death place fields (optional, similar to birth place)
    death_place_type: Optional[PlaceType] = Field(
        None,
        description="Type of death place: UNKNOWN, SWISS, or FOREIGN"
    )

    # Swiss death place
    death_municipality_bfs: Optional[int] = Field(
        None,
        description="Death municipality BFS number (for Swiss death place)"
    )
    death_municipality_name: Optional[str] = Field(
        None,
        max_length=40,
        description="Death municipality name (for Swiss death place)"
    )
    death_municipality_canton: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Death municipality canton (for Swiss death place)"
    )

    # Foreign death place
    death_country_id: Optional[int] = Field(
        None,
        description="Death country ID (for foreign death place)"
    )
    death_country_iso2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Death country ISO code (for foreign death place)"
    )
    death_country_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Death country name (for foreign death place)"
    )

    # ========================================================================
    # Contact Data (eCH-0011 contactData - optional)
    # ========================================================================

    # Contact identification type (CHOICE: person, partner, organization, or none)
    contact_type: Optional[str] = Field(
        None,
        description="Contact type: 'person', 'partner', 'organization', or None"
    )

    # Contact person fields (when contact_type='person')
    contact_person_vn: Optional[str] = Field(
        None,
        description="Contact person VN (AHV-13)"
    )
    contact_person_local_id: Optional[str] = Field(
        None,
        description="Contact person local ID"
    )
    contact_person_local_id_category: Optional[str] = Field(
        None,
        description="Contact person local ID category"
    )
    contact_person_official_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Contact person official name"
    )
    contact_person_first_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Contact person first name"
    )
    contact_person_sex: Optional[str] = Field(
        None,
        description="Contact person sex: '1'=male, '2'=female, '3'=unknown"
    )
    contact_person_date_of_birth: Optional[date] = Field(
        None,
        description="Contact person date of birth"
    )

    # Contact organization fields (when contact_type='organization')
    contact_organization_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Contact organization name"
    )
    contact_organization_id: Optional[str] = Field(
        None,
        description="Contact organization ID (UID)"
    )
    contact_organization_id_category: Optional[str] = Field(
        None,
        description="Contact organization ID category"
    )

    # Contact address fields (required when contact data exists)
    contact_address_line1: Optional[str] = Field(
        None,
        max_length=60,
        description="Contact address line 1 (c/o, attention)"
    )
    contact_address_line2: Optional[str] = Field(
        None,
        max_length=60,
        description="Contact address line 2"
    )
    contact_address_street: Optional[str] = Field(
        None,
        max_length=60,
        description="Contact address street"
    )
    contact_address_house_number: Optional[str] = Field(
        None,
        max_length=12,
        description="Contact address house number"
    )
    contact_address_town: Optional[str] = Field(
        None,
        max_length=40,
        description="Contact address town (required for contact)"
    )
    contact_address_zip_code: Optional[str] = Field(
        None,
        description="Contact address postal code"
    )
    contact_address_swiss_zip_code_addon: Optional[str] = Field(
        None,
        max_length=2,
        description="Contact address Swiss postal code add-on (00-99)"
    )
    contact_address_country: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Contact address country ISO code"
    )

    # Contact validity dates
    contact_valid_from: Optional[date] = Field(
        None,
        description="Contact valid from date"
    )
    contact_valid_till: Optional[date] = Field(
        None,
        description="Contact valid until date"
    )

    language_of_correspondance: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Language of correspondence (ISO 639-1 code, e.g., 'de', 'fr')"
    )

    # Contact salutation (mrMrs)
    contact_mr_mrs: Optional[str] = Field(
        None,
        description="Contact salutation: '1'=Mr, '2'=Mrs, '3'=Company/Neutral"
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================

    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v: str) -> str:
        """Validate sex is valid enum value."""
        valid = {'1', '2', '3'}
        if v not in valid:
            raise ValueError(f"sex must be one of {valid}, got: {v}")
        return v

    @model_validator(mode='after')
    def validate_nationality_choice(self) -> 'StatisticsPerson':
        """Validate nationality CHOICE constraint."""
        if self.nationality_type == NationalityType.SWISS:
            if not self.places_of_origin:
                raise ValueError(
                    "At least one place of origin required when nationality_type is SWISS"
                )
        elif self.nationality_type == NationalityType.FOREIGN:
            if not self.nationality_country_iso2 and not self.nationality_country_id:
                raise ValueError(
                    "nationality_country_iso2 or nationality_country_id required "
                    "when nationality_type is FOREIGN"
                )
        return self

    @model_validator(mode='after')
    def validate_birth_place_choice(self) -> 'StatisticsPerson':
        """Validate birth place CHOICE constraint."""
        if self.birth_place_type == PlaceType.SWISS:
            if not self.birth_municipality_name:
                raise ValueError(
                    "birth_municipality_name required when birth_place_type is SWISS"
                )
        elif self.birth_place_type == PlaceType.FOREIGN:
            if not self.birth_country_iso2 and not self.birth_country_id:
                raise ValueError(
                    "birth_country_iso2 or birth_country_id required "
                    "when birth_place_type is FOREIGN"
                )
        return self

    # ========================================================================
    # CONVERSION TO LAYER 1
    # ========================================================================

    def to_ech0011_person(self) -> ECH0011Person:
        """Convert Layer 2 → ECH0011Person (Layer 1).

        Transforms flattened StatisticsPerson into XSD-compliant nested structure.

        Returns:
            ECH0011Person ready for XML export

        Raises:
            ValueError: If required fields missing or CHOICE constraints violated
        """
        # Build other_person_ids (optional, e.g., CH.ZEMIS, CH.ZAR)
        other_person_id_list = []
        if self.other_person_ids:
            for other_id_dict in self.other_person_ids:
                other_pid = ECH0044NamedPersonId(
                    person_id=other_id_dict['person_id'],
                    person_id_category=other_id_dict['person_id_category']
                )
                other_person_id_list.append(other_pid)

        # Build eu_person_ids (optional, e.g., EU.EESSI)
        eu_person_id_list = []
        if self.eu_person_ids:
            for eu_id_dict in self.eu_person_ids:
                eu_pid = ECH0044NamedPersonId(
                    person_id=eu_id_dict['person_id'],
                    person_id_category=eu_id_dict['person_id_category']
                )
                eu_person_id_list.append(eu_pid)

        # Build person identification (eCH-0044)
        person_identification = ECH0044PersonIdentification(
            vn=self.vn,
            local_person_id=ECH0044NamedPersonId(
                person_id=self.local_person_id,
                person_id_category=self.local_person_id_category
            ),
            other_person_id=other_person_id_list,
            eu_person_id=eu_person_id_list,
            official_name=self.official_name,
            first_name=self.first_name,
            original_name=self.original_name,
            sex=Sex(self.sex),
            date_of_birth=ECH0044DatePartiallyKnown(
                year_month_day=self.date_of_birth
            )
        )

        # Build foreign name data (eCH-0011 CHOICE: nameOnForeignPassport XOR declaredForeignName)
        name_on_foreign_passport = None
        declared_foreign_name = None
        if self.name_on_foreign_passport_name or self.name_on_foreign_passport_first_name:
            name_on_foreign_passport = ECH0011ForeignerName(
                name=self.name_on_foreign_passport_name,
                first_name=self.name_on_foreign_passport_first_name
            )
        elif self.declared_foreign_name_name or self.declared_foreign_name_first_name:
            declared_foreign_name = ECH0011ForeignerName(
                name=self.declared_foreign_name_name,
                first_name=self.declared_foreign_name_first_name
            )

        # Build name data (eCH-0011)
        name_data = ECH0011NameData(
            official_name=self.official_name,
            first_name=self.first_name,
            original_name=self.original_name,
            alliance_name=self.alliance_name,
            alias_name=self.alias_name,
            other_name=self.other_name,
            call_name=self.call_name,
            name_on_foreign_passport=name_on_foreign_passport,
            declared_foreign_name=declared_foreign_name,
        )

        # Build birth data (eCH-0011)
        place_of_birth = self._build_place_of_birth()
        birth_data = ECH0011BirthData(
            date_of_birth=self.date_of_birth,
            place_of_birth=place_of_birth,
            sex=Sex(self.sex)
        )

        # Build religion data (eCH-0011)
        religion_data = ECH0011ReligionData(
            religion=self.religion,
            religion_valid_from=self.religion_valid_from
        )

        # Build separation data (optional)
        separation_data = None
        if self.separation_type or self.separation_since:
            separation_data = ECH0011SeparationData(
                separation=SeparationType(self.separation_type) if self.separation_type else None,
                separation_valid_from=self.separation_since,
                separation_valid_till=self.separation_till
            )

        # Build marital data (eCH-0011)
        marital_data = ECH0011MaritalData(
            marital_status=MaritalStatus(self.marital_status),
            date_of_marital_status=self.date_of_marital_status,
            cancelation_reason=self.marital_cancelation_reason,
            official_proof_of_marital_status_yes_no=self.marital_status_verified,
            separation_data=separation_data
        )

        # Build nationality data (eCH-0011)
        nationality_data = self._build_nationality_data()

        # Build death data (optional)
        death_data = None
        if self.death_date:
            # Build death period
            death_period = ECH0011DeathPeriod(
                date_from=self.death_date,
                date_to=self.death_date_end
            )

            # Build place of death (optional)
            place_of_death = self._build_place_of_death() if self.death_place_type else None

            death_data = ECH0011DeathData(
                death_period=death_period,
                place_of_death=place_of_death
            )

        # Build places of origin OR residence permit (CHOICE)
        place_of_origin_list: List[ECH0011PlaceOfOrigin] = []
        residence_permit = None

        if self.nationality_type == NationalityType.SWISS:
            for origin in self.places_of_origin:
                place_of_origin_list.append(ECH0011PlaceOfOrigin(
                    origin_name=origin.origin_name,
                    canton=origin.canton,
                    place_of_origin_id=origin.origin_id,
                    history_municipality_id=origin.history_municipality_id
                ))
        else:
            if self.residence_permit:
                residence_permit = ECH0011ResidencePermitData(
                    residence_permit=self.residence_permit,
                    residence_permit_valid_from=self.residence_permit_valid_from,
                    residence_permit_valid_till=self.residence_permit_valid_till,
                    entry_date=self.entry_date
                )
            else:
                # Foreign without explicit permit - create minimal permit data
                # The XSD requires residencePermitData for foreigners
                raise ValueError(
                    "residence_permit required for foreign nationals"
                )

        # Build contact data (optional)
        contact_data = self._build_contact_data()

        return ECH0011Person(
            person_identification=person_identification,
            name_data=name_data,
            birth_data=birth_data,
            religion_data=religion_data,
            marital_data=marital_data,
            nationality_data=nationality_data,
            death_data=death_data,
            contact_data=contact_data,
            language_of_correspondance=self.language_of_correspondance,
            place_of_origin=place_of_origin_list,
            residence_permit=residence_permit
        )

    def _build_place_of_birth(self) -> ECH0011GeneralPlace:
        """Build ECH0011GeneralPlace for birth place."""
        if self.birth_place_type == PlaceType.UNKNOWN:
            return ECH0011GeneralPlace(unknown=True)
        elif self.birth_place_type == PlaceType.SWISS:
            swiss_muni = ECH0007SwissMunicipality(
                municipality_id=str(self.birth_municipality_bfs) if self.birth_municipality_bfs else None,
                municipality_name=self.birth_municipality_name,
                canton_abbreviation=self.birth_municipality_canton,
                history_municipality_id=self.birth_municipality_history_id
            )
            return ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality(swiss_municipality=swiss_muni)
            )
        else:  # FOREIGN
            country_id_str = str(self.birth_country_id) if self.birth_country_id else None
            if not self.birth_country_name:
                raise ValueError(
                    f"Person missing birth_country_name for foreign birth place "
                    f"(country_id={self.birth_country_id}, iso2={self.birth_country_iso2}). "
                    f"eCH-0008 countryNameShort is required — cannot invent country names."
                )
            country = ECH0008Country(
                country_id=country_id_str,
                country_id_iso2=self.birth_country_iso2,
                country_name_short=self.birth_country_name
            )
            return ECH0011GeneralPlace(foreign_country=country)

    def _build_place_of_death(self) -> Optional[ECH0011GeneralPlace]:
        """Build ECH0011GeneralPlace for death place (optional)."""
        if not self.death_place_type:
            return None
        if self.death_place_type == PlaceType.UNKNOWN:
            return ECH0011GeneralPlace(unknown=True)
        elif self.death_place_type == PlaceType.SWISS:
            swiss_muni = ECH0007SwissMunicipality(
                municipality_id=str(self.death_municipality_bfs) if self.death_municipality_bfs else None,
                municipality_name=self.death_municipality_name,
                canton_abbreviation=self.death_municipality_canton
            )
            return ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality(swiss_municipality=swiss_muni)
            )
        else:  # FOREIGN
            country_id_str = str(self.death_country_id) if self.death_country_id else None
            if not self.death_country_name:
                raise ValueError(
                    f"Person missing death_country_name for foreign death place "
                    f"(country_id={self.death_country_id}, iso2={self.death_country_iso2}). "
                    f"eCH-0008 countryNameShort is required — cannot invent country names."
                )
            country = ECH0008Country(
                country_id=country_id_str,
                country_id_iso2=self.death_country_iso2,
                country_name_short=self.death_country_name
            )
            return ECH0011GeneralPlace(foreign_country=country)

    def _build_nationality_data(self) -> ECH0011NationalityData:
        """Build ECH0011NationalityData.

        Nationality status per eCH-0011:
        - 0 = unknown/not specified
        - 1 = stateless
        - 2 = has known nationality (both Swiss and foreign)

        ZERO TOLERANCE: nationality_status must be provided from source data.
        We NEVER invent this value - it affects legal status.
        """
        # CRITICAL: Use provided nationality_status, never invent it
        if not self.nationality_status:
            raise ValueError(
                f"nationality_status is required for person {self.local_person_id}. "
                "This field affects legal status and must come from source data."
            )

        if self.nationality_type == NationalityType.SWISS:
            # Swiss citizen - use provided nationality_status
            return ECH0011NationalityData(
                nationality_status=self.nationality_status,
                country_info=[ECH0011CountryInfo(
                    country=ECH0008Country(
                        country_id="8100",
                        country_id_iso2="CH",
                        country_name_short="Schweiz"
                    ),
                    nationality_valid_from=self.nationality_valid_from
                )]
            )
        else:
            # Foreign national - use provided nationality_status
            # country_id must be string
            if not self.nationality_country_id:
                raise ValueError(
                    f"nationality_country_id is required for foreign national {self.local_person_id}"
                )
            if not self.nationality_country_iso2:
                raise ValueError(
                    f"nationality_country_iso2 is required for foreign national {self.local_person_id}"
                )
            if not self.nationality_country_name:
                raise ValueError(
                    f"nationality_country_name is required for foreign national {self.local_person_id}"
                )

            country_id_str = str(self.nationality_country_id)
            country = ECH0008Country(
                country_id=country_id_str,
                country_id_iso2=self.nationality_country_iso2,
                country_name_short=self.nationality_country_name
            )
            return ECH0011NationalityData(
                nationality_status=self.nationality_status,
                country_info=[ECH0011CountryInfo(
                    country=country,
                    nationality_valid_from=self.nationality_valid_from
                )]
            )

    def _build_contact_data(self) -> Optional[ECH0011ContactData]:
        """Build ECH0011ContactData from flattened fields.

        Returns None if no contact data is present.
        """
        # Check if any contact data exists
        has_contact = (
            self.contact_type or
            self.contact_address_town or
            self.contact_person_official_name or
            self.contact_organization_name
        )

        if not has_contact:
            return None

        # Build contact address (required when contact data exists)
        if not self.contact_address_town:
            raise ValueError(
                f"contact_address_town is required when contact data is present "
                f"for person {self.local_person_id}"
            )

        address_info = ECH0010AddressInformation(
            address_line1=self.contact_address_line1,
            address_line2=self.contact_address_line2,
            street=self.contact_address_street,
            house_number=self.contact_address_house_number,
            town=self.contact_address_town,
            swiss_zip_code=int(self.contact_address_zip_code) if self.contact_address_zip_code and self.contact_address_zip_code.isdigit() else None,
            swiss_zip_code_add_on=self.contact_address_swiss_zip_code_addon,
            country=self.contact_address_country or "CH",
        )

        # Build person or organization recipient for mail address
        person_info = None
        org_info = None

        if self.contact_type == 'organization' and self.contact_organization_name:
            org_info = ECH0010OrganisationMailAddressInfo(
                organisation_name=self.contact_organization_name,
            )
        else:
            # Default to person if we have contact person data
            person_info = ECH0010PersonMailAddressInfo(
                mr_mrs=self.contact_mr_mrs,
                first_name=self.contact_person_first_name,
                last_name=self.contact_person_official_name,
            )

        contact_address = ECH0010MailAddress(
            person=person_info,
            organisation=org_info,
            address_information=address_info
        )

        # Build contact identification (optional)
        contact_person = None
        contact_person_partner = None
        contact_organization = None

        if self.contact_type == 'person' and self.contact_person_official_name:
            # Build full person identification
            # Requires: local_id, sex, date_of_birth (caller must ensure these exist)
            local_id = None
            if self.contact_person_local_id and self.contact_person_local_id_category:
                local_id = ECH0044NamedPersonId(
                    person_id=self.contact_person_local_id,
                    person_id_category=self.contact_person_local_id_category
                )
            # PersonIdentification requires sex and date_of_birth
            # If not provided, we cannot create a valid PersonIdentification
            if local_id and self.contact_person_sex and self.contact_person_date_of_birth:
                contact_person = ECH0044PersonIdentification(
                    vn=self.contact_person_vn,
                    local_person_id=local_id,
                    official_name=self.contact_person_official_name,
                    first_name=self.contact_person_first_name or "",
                    sex=self.contact_person_sex,
                    date_of_birth=ECH0044DatePartiallyKnown(
                        year_month_day=self.contact_person_date_of_birth
                    )
                )

        elif self.contact_type == 'partner' and self.contact_person_official_name:
            # Build light person identification (PersonIdentificationLight)
            # sex and date_of_birth are OPTIONAL in this type
            partner_kwargs: Dict[str, Any] = {
                'official_name': self.contact_person_official_name,
                'first_name': self.contact_person_first_name or "",
            }
            # Add optional fields only if provided (no data invention)
            if self.contact_person_vn:
                partner_kwargs['vn'] = self.contact_person_vn
            if self.contact_person_local_id and self.contact_person_local_id_category:
                partner_kwargs['local_person_id'] = ECH0044NamedPersonId(
                    person_id=self.contact_person_local_id,
                    person_id_category=self.contact_person_local_id_category
                )
            if self.contact_person_sex:
                partner_kwargs['sex'] = self.contact_person_sex
            if self.contact_person_date_of_birth:
                partner_kwargs['date_of_birth'] = ECH0044DatePartiallyKnown(
                    year_month_day=self.contact_person_date_of_birth
                )
            contact_person_partner = ECH0044PersonIdentificationLight(**partner_kwargs)

        return ECH0011ContactData(
            contact_person=contact_person,
            contact_person_partner=contact_person_partner,
            contact_organization=contact_organization,
            contact_address=contact_address,
            contact_valid_from=self.contact_valid_from,
            contact_valid_till=self.contact_valid_till
        )


class StatisticsDeliveryEvent(BaseModel):
    """Layer 2 event for eCH-0099 statistics delivery.

    Combines person data with residence information for a complete
    reported person entry. Use to_ech0099_reported_person() for
    conversion to Layer 1 models.

    Zero-Tolerance Policy:
    - All required fields must be explicitly provided
    - No data invention
    - Fail hard on missing required data
    """
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Person data (required)
    person: StatisticsPerson = Field(
        ...,
        description="Person data (required)"
    )

    # Residence type CHOICE
    residence_type: ResidenceType = Field(
        ...,
        description="Type of residence: MAIN, SECONDARY, or OTHER"
    )

    # Reporting municipality (required)
    reporting_municipality_bfs: int = Field(
        ...,
        description="BFS municipality number of reporting municipality (required)"
    )
    reporting_municipality_name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Name of reporting municipality (required)"
    )
    reporting_municipality_canton: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Canton abbreviation of reporting municipality"
    )
    reporting_municipality_history_id: Optional[str] = Field(
        None,
        description="Historical BFS municipality ID (for merged municipalities)"
    )

    # Restricted voting right (eCH-0011 personType)
    restricted_voting_right: Optional[bool] = Field(
        None,
        description="Restricted voting and election right at federation level"
    )

    # Dwelling address (required)
    dwelling_address: DwellingAddressInfo = Field(
        ...,
        description="Dwelling address (required)"
    )

    # Arrival date (required)
    arrival_date: date = Field(
        ...,
        description="Date of arrival at this residence (required)"
    )

    # Comes from (required for SECONDARY and OTHER, optional for MAIN)
    comes_from: Optional[DestinationInfo] = Field(
        None,
        description="Origin location (required for SECONDARY/OTHER residence)"
    )

    # Departure date (optional)
    departure_date: Optional[date] = Field(
        None,
        description="Date of departure from this residence"
    )

    # Goes to (optional)
    goes_to: Optional[DestinationInfo] = Field(
        None,
        description="Destination location"
    )

    # For SECONDARY residence: main residence municipality
    main_residence_bfs: Optional[int] = Field(
        None,
        description="BFS number of main residence (required if residence_type is SECONDARY)"
    )
    main_residence_name: Optional[str] = Field(
        None,
        max_length=40,
        description="Name of main residence municipality (required if residence_type is SECONDARY)"
    )
    main_residence_canton: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Canton of main residence municipality"
    )

    # For MAIN residence: secondary residence municipalities (optional list)
    secondary_residences: List[dict] = Field(
        default_factory=list,
        description="List of secondary residence municipalities (for MAIN residence)"
    )

    # Extended data for statistics (optional)
    person_extended_data: List[ECH0099DataType] = Field(
        default_factory=list,
        description="Optional statistics-specific field/value pairs"
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================

    @model_validator(mode='after')
    def validate_residence_constraints(self) -> 'StatisticsDeliveryEvent':
        """Validate residence-type-specific constraints."""
        if self.residence_type == ResidenceType.SECONDARY:
            if not self.comes_from:
                raise ValueError("comes_from required when residence_type is SECONDARY")
            if not self.main_residence_name:
                raise ValueError("main_residence_name required when residence_type is SECONDARY")
        elif self.residence_type == ResidenceType.OTHER:
            if not self.comes_from:
                raise ValueError("comes_from required when residence_type is OTHER")
        return self

    # ========================================================================
    # CONVERSION TO LAYER 1
    # ========================================================================

    def to_ech0099_reported_person(self) -> ECH0099ReportedPerson:
        """Convert Layer 2 → ECH0099ReportedPerson (Layer 1).

        Returns:
            ECH0099ReportedPerson ready for XML export

        Raises:
            ValueError: If required fields missing or constraints violated
        """
        # Convert person
        ech0011_person = self.person.to_ech0011_person()

        # Build residence
        residence = self._build_residence()

        # Create ECH0011ReportedPerson
        reported_person = ECH0011ReportedPerson(
            person=ech0011_person,
            has_main_residence=residence if self.residence_type == ResidenceType.MAIN else None,
            has_secondary_residence=residence if self.residence_type == ResidenceType.SECONDARY else None,
            has_other_residence=residence if self.residence_type == ResidenceType.OTHER else None
        )

        # Wrap in ECH0099ReportedPerson
        return ECH0099ReportedPerson(
            base_data=reported_person,
            person_extended_data=list(self.person_extended_data)
        )

    def _build_residence(self) -> Union[ECH0011MainResidence, ECH0011SecondaryResidence, ECH0011OtherResidence]:
        """Build appropriate residence type based on residence_type."""
        # Build reporting municipality
        reporting_municipality = ECH0007Municipality(
            swiss_municipality=ECH0007SwissMunicipality(
                municipality_id=str(self.reporting_municipality_bfs),
                municipality_name=self.reporting_municipality_name,
                canton_abbreviation=self.reporting_municipality_canton,
                history_municipality_id=self.reporting_municipality_history_id
            )
        )

        # Build dwelling address
        dwelling_address = self._build_dwelling_address()

        # Build comes_from (if provided)
        comes_from = self._build_destination(self.comes_from) if self.comes_from else None

        # Build goes_to (if provided)
        goes_to = self._build_destination(self.goes_to) if self.goes_to else None

        if self.residence_type == ResidenceType.MAIN:
            # Build residence data
            residence_data = ECH0011ResidenceData(
                reporting_municipality=reporting_municipality,
                arrival_date=self.arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=self.departure_date,
                goes_to=goes_to
            )
            # Build secondary residence list
            secondary_list = []
            for sec in self.secondary_residences:
                secondary_list.append(ECH0007Municipality(
                    swiss_municipality=ECH0007SwissMunicipality(
                        municipality_id=str(sec.get('bfs')) if sec.get('bfs') else None,
                        municipality_name=sec.get('name'),
                        canton_abbreviation=sec.get('canton'),
                        history_municipality_id=sec.get('history_municipality_id')
                    )
                ))
            return ECH0011MainResidence(
                main_residence=residence_data,
                secondary_residence=secondary_list
            )

        elif self.residence_type == ResidenceType.SECONDARY:
            # Build main residence municipality reference
            main_residence = ECH0007Municipality(
                swiss_municipality=ECH0007SwissMunicipality(
                    municipality_id=str(self.main_residence_bfs) if self.main_residence_bfs else None,
                    municipality_name=self.main_residence_name,
                    canton_abbreviation=self.main_residence_canton
                )
            )
            assert comes_from is not None, "comes_from required for SECONDARY"
            return ECH0011SecondaryResidence(
                main_residence=main_residence,
                reporting_municipality=reporting_municipality,
                arrival_date=self.arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=self.departure_date,
                goes_to=goes_to
            )

        else:  # OTHER
            assert comes_from is not None, "comes_from required for OTHER"
            return ECH0011OtherResidence(
                reporting_municipality=reporting_municipality,
                arrival_date=self.arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=self.departure_date,
                goes_to=goes_to
            )

    def _build_dwelling_address(self) -> ECH0011DwellingAddress:
        """Build ECH0011DwellingAddress from DwellingAddressInfo."""
        da = self.dwelling_address
        address = ECH0010SwissAddressInformation(
            address_line1=da.address_line1,
            address_line2=da.address_line2,
            street=da.street,
            house_number=da.house_number,
            dwelling_number=da.dwelling_number,
            locality=da.locality,
            town=da.town,
            swiss_zip_code=da.swiss_zip_code,
            swiss_zip_code_add_on=da.swiss_zip_code_add_on,
            swiss_zip_code_id=da.swiss_zip_code_id,
            country=da.country or "CH"
        )
        return ECH0011DwellingAddress(
            egid=da.egid,
            ewid=da.ewid,
            household_id=da.household_id,
            address=address,
            type_of_household=TypeOfHousehold(da.type_of_household),
            moving_date=da.moving_date
        )

    def _build_destination(self, dest: DestinationInfo) -> ECH0011DestinationType:
        """Build ECH0011DestinationType from DestinationInfo."""
        # Build mail address if present
        # ECH0010AddressInformation requires either swiss_zip_code OR foreign_zip_code
        mail_address = None
        has_zip = dest.mail_address_swiss_zip_code or dest.mail_address_foreign_zip_code
        if (dest.mail_address_town or dest.mail_address_street) and has_zip:
            mail_address = ECH0010AddressInformation(
                street=dest.mail_address_street,
                house_number=dest.mail_address_house_number,
                town=dest.mail_address_town,
                swiss_zip_code=dest.mail_address_swiss_zip_code,
                swiss_zip_code_add_on=dest.mail_address_swiss_zip_code_addon,
                foreign_zip_code=dest.mail_address_foreign_zip_code,
                country=dest.mail_address_country or "CH",
            )

        if dest.place_type == PlaceType.UNKNOWN:
            return ECH0011DestinationType(unknown=True, mail_address=mail_address)
        elif dest.place_type == PlaceType.SWISS:
            swiss_muni = ECH0007SwissMunicipality(
                municipality_id=str(dest.municipality_bfs) if dest.municipality_bfs else None,
                municipality_name=dest.municipality_name,
                canton_abbreviation=dest.municipality_canton,
                history_municipality_id=dest.municipality_history_id
            )
            return ECH0011DestinationType(
                swiss_municipality=ECH0007Municipality(swiss_municipality=swiss_muni),
                mail_address=mail_address
            )
        else:  # FOREIGN
            country_id_str = str(dest.country_id) if dest.country_id else None
            if not dest.country_name:
                raise ValueError(
                    f"Destination missing country_name for foreign destination "
                    f"(country_id={dest.country_id}, iso2={dest.country_iso2}). "
                    f"eCH-0008 countryNameShort is required — cannot invent country names."
                )
            country = ECH0008Country(
                country_id=country_id_str,
                country_id_iso2=dest.country_iso2,
                country_name_short=dest.country_name
            )
            return ECH0011DestinationType(
                foreign_country=country,
                foreign_town=dest.foreign_town,
                mail_address=mail_address
            )

    def finalize(
        self,
        config: 'StatisticsDeliveryConfig',
        message_id: Optional[str] = None,
        message_date: Optional[datetime] = None,
        action: ActionType = ActionType.NEW,
        general_data: Optional[List[ECH0099DataType]] = None,
        **optional_header_fields
    ) -> ECH0099Delivery:
        """Create complete eCH-0099 delivery ready for XML export.

        This method combines the Layer 2 event with deployment configuration
        to produce a complete ECH0099Delivery.

        Args:
            config: Deployment configuration (sender, app info, test flag)
            message_id: Unique message ID (auto-generated UUID if not provided)
            message_date: Message timestamp (defaults to now())
            action: Action type (default: NEW)
            general_data: Optional delivery-wide data
            **optional_header_fields: Additional eCH-0058 header fields

        Returns:
            Complete ECH0099Delivery ready for .to_file() export
        """
        return finalize_statistics_delivery(
            events=[self],
            config=config,
            message_id=message_id,
            message_date=message_date,
            action=action,
            general_data=general_data,
            **optional_header_fields
        )


class StatisticsDeliveryConfig(BaseModel):
    """Configuration for eCH-0099 statistics delivery.

    Values should come from configuration files or environment,
    never hardcoded in application code.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    sender_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Sedex participant ID of sender (required)"
    )
    manufacturer: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Software manufacturer name (required)"
    )
    product: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Product name (required)"
    )
    product_version: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Product version (required)"
    )
    test_delivery_flag: bool = Field(
        ...,
        description="True for test deliveries, False for production (required)"
    )
    original_sender_id: Optional[str] = Field(
        None,
        max_length=50,
        description="Original sender ID (for forwarded messages)"
    )


# ============================================================================
# FINALIZATION HELPER
# ============================================================================

def finalize_statistics_delivery(
    events: List[StatisticsDeliveryEvent],
    config: StatisticsDeliveryConfig,
    message_id: Optional[str] = None,
    message_date: Optional[datetime] = None,
    action: ActionType = ActionType.NEW,
    general_data: Optional[List[ECH0099DataType]] = None,
    **optional_header_fields
) -> ECH0099Delivery:
    """Finalize eCH-0099 statistics delivery from Layer 2 events.

    Builds eCH-0058 v4 header and converts each Layer 2 event to
    ECH0099ReportedPerson.

    Args:
        events: List of StatisticsDeliveryEvent (at least one required)
        config: Deployment configuration
        message_id: Unique message ID (auto-generated UUID if not provided)
        message_date: Message timestamp (defaults to now())
        action: Action type (default: NEW)
        general_data: Optional delivery-wide data
        **optional_header_fields: Additional eCH-0058 header fields

    Returns:
        Complete ECH0099Delivery ready for XML export

    Raises:
        ValueError: If events list is empty
    """
    if not events:
        raise ValueError("At least one StatisticsDeliveryEvent is required")

    msg_id = message_id or str(uuid4())
    msg_date = message_date or datetime.now(timezone.utc)

    # Build eCH-0058 v4 sending application
    sending_application = ECH0058SendingApplication(
        manufacturer=config.manufacturer,
        product=config.product,
        product_version=config.product_version
    )

    # Build eCH-0058 v4 header
    header = ECH0058Header(
        sender_id=config.sender_id,
        message_id=msg_id,
        message_type=NS.ECH0099_V2,
        sending_application=sending_application,
        message_date=msg_date,
        action=action,
        test_delivery_flag=config.test_delivery_flag,
        original_sender_id=config.original_sender_id,
        **optional_header_fields
    )

    # Convert Layer 2 events to Layer 1 reported persons
    reported_persons = [event.to_ech0099_reported_person() for event in events]

    return ECH0099Delivery(
        delivery_header=header,
        reported_person=reported_persons,
        general_data=general_data or []
    )
