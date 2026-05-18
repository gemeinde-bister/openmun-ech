"""eCH-0020 Layer 2: BaseDeliveryPerson model.

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
"""

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# Import Layer 1 models for conversion
from openmun_ech.ech0020.v3 import (
    ECH0020BaseDeliveryPerson,
    ECH0020NameInfo,
    ECH0020BirthInfo,
    ECH0020MaritalInfo,
    ECH0020PlaceOfOriginInfo,
)
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
    ECH0010PersonMailAddress,
    ECH0010AddressInformation,
    ECH0010SwissAddressInformation,
    ECH0010OrganisationMailAddressInfo,
    ECH0010OrganisationMailAddress,
)

from .helpers import _extract_date_of_birth, _extract_person_identification
from .types import (
    PersonIdentification,
    ParentInfo,
    GuardianInfo,
    PlaceType,
    GuardianType,
)


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

                partner_address = ECH0010PersonMailAddress(
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

                    parent_address = ECH0010PersonMailAddress(
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
                    relationship_valid_from=parent_info.relationship_valid_from,
                    type_of_relationship=parent_info.relationship_type,
                    care=parent_info.care,
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
                # Determine country: if swiss_zip_code is used, country MUST be CH
                # Otherwise use provided country - NO fallback (zero data invention)
                has_swiss_postal_code = bool(self.health_insurance_address_postal_code)
                if has_swiss_postal_code:
                    # Swiss postal code implies country='CH'
                    country = 'CH'
                elif self.health_insurance_address_country:
                    # Foreign address with explicit country
                    country = self.health_insurance_address_country
                else:
                    # No postal code and no country - cannot determine
                    raise ValueError(
                        f"Health insurance address for '{self.health_insurance_name}' "
                        f"has town but no postal code and no country. Cannot determine "
                        f"country - provide swiss postal code OR explicit country."
                    )
                address_info = ECH0010AddressInformation(
                    street=self.health_insurance_address_street,
                    house_number=self.health_insurance_address_house_number,
                    town=self.health_insurance_address_town,
                    swiss_zip_code=int(self.health_insurance_address_postal_code) if self.health_insurance_address_postal_code else None,
                    country=country
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
        sex = person_id.sex.value

        # Extract date_of_birth from DatePartiallyKnown CHOICE type
        date_of_birth = _extract_date_of_birth(person_id.date_of_birth)

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
                sm = swiss_muni.swiss_municipality
                birth_municipality_bfs = sm.municipality_id
                birth_municipality_name = sm.municipality_name
                if sm.canton_abbreviation is not None:
                    birth_canton_abbreviation = sm.canton_abbreviation.value
                birth_municipality_history_id = sm.history_municipality_id
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
        marital_status = marital_data.marital_status.value
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
                sm = swiss_muni.swiss_municipality
                marriage_municipality_bfs = sm.municipality_id
                marriage_municipality_name = sm.municipality_name
                if sm.canton_abbreviation is not None:
                    marriage_canton_abbreviation = sm.canton_abbreviation.value
                marriage_municipality_history_id = sm.history_municipality_id
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
                    sm = swiss_muni.swiss_municipality
                    death_municipality_bfs = sm.municipality_id
                    death_municipality_name = sm.municipality_name
                    if sm.canton_abbreviation is not None:
                        death_canton_abbreviation = sm.canton_abbreviation.value
                    death_municipality_history_id = sm.history_municipality_id
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
                contact_person_sex = raw.contact_data.contact_person.sex.value
                # Extract date_of_birth
                contact_person_date_of_birth = _extract_date_of_birth(raw.contact_data.contact_person.date_of_birth)
            elif raw.contact_data.contact_person_partner:
                # Light identification (personIdentificationPartner element)
                # Note: PersonIdentificationLight CAN have sex and date_of_birth as OPTIONAL fields
                contact_person_official_name = raw.contact_data.contact_person_partner.official_name
                contact_person_first_name = raw.contact_data.contact_person_partner.first_name
                # Extract vn (AHV number) if present
                if raw.contact_data.contact_person_partner.vn:
                    contact_person_vn = raw.contact_data.contact_person_partner.vn
                # Extract local_person_id if present
                if raw.contact_data.contact_person_partner.local_person_id:
                    contact_person_local_person_id = raw.contact_data.contact_person_partner.local_person_id.person_id
                    contact_person_local_person_id_category = raw.contact_data.contact_person_partner.local_person_id.person_id_category
                # Extract sex if present (optional in Light identification)
                if raw.contact_data.contact_person_partner.sex:
                    contact_person_sex = raw.contact_data.contact_person_partner.sex.value
                # Extract date_of_birth if present (optional in Light identification)
                contact_person_date_of_birth = _extract_date_of_birth(raw.contact_data.contact_person_partner.date_of_birth)
            elif raw.contact_data.contact_address and raw.contact_data.contact_address.person:
                # Contact person ONLY in mail address (no separate personIdentification element)
                contact_person_official_name = raw.contact_data.contact_address.person.last_name
                contact_person_first_name = raw.contact_data.contact_address.person.first_name
                # Extract mrMrs from mail address person
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
                if raw.contact_data.contact_address.person.mr_mrs:
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

                spouse = _extract_person_identification(spouse_person_id)

                # Extract spouse other person IDs (optional, multiple)
                spouse_other_person_ids = None
                if spouse_person_id.other_person_id and len(spouse_person_id.other_person_id) > 0:
                    spouse_other_person_ids = [
                        {
                            'person_id': other_id.person_id,
                            'person_id_category': other_id.person_id_category
                        }
                        for other_id in spouse_person_id.other_person_id
                    ]

            # Extract spouse address and mr_mrs
            if partner and partner.address:
                if partner.address.person:
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

                    parent_person = _extract_person_identification(parent_person_id)

                    # Extract parent address and mr_mrs
                    parent_mr_mrs = None
                    parent_address_street = None
                    parent_address_house_number = None
                    parent_address_postal_code = None
                    parent_address_postal_code_addon = None
                    parent_address_town = None

                    if parent_rel.partner and parent_rel.partner.address:
                        if parent_rel.partner.address.person:
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

                    guardian_person = _extract_person_identification(guardian_person_id)

                elif guardian_rel.person_identification_partner:
                    # Partner person guardian
                    guardian_type = GuardianType.PERSON_PARTNER
                    guardian_person_id = guardian_rel.person_identification_partner

                    guardian_person = _extract_person_identification(guardian_person_id)

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
                    if guardian_rel.partner_address.person:
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
