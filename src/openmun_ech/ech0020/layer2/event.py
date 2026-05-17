"""eCH-0020 Layer 2: Event models (BaseDeliveryEvent and supporting types).

Phase 2 adds event wrapper (residence/dwelling) for complete eCH-0020 delivery.
Phase 1 = person data, Phase 2 = WHERE person lives.

Layer 2 hides:
- Namespace wrappers (ECH0020HasMainResidence, ECH0020HasSecondaryResidence, etc.)
- XSD CHOICE complexity (validators enforce)
- Nesting levels (5 → 2)

Layer 2 exposes:
- ALL fields (100% roundtrip guarantee)
- All optional fields
- All rare fields
"""

from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Import Layer 1 models for conversion
from openmun_ech.ech0020.v3 import (
    ECH0020EventBaseDelivery,
    ECH0020HasMainResidence,
    ECH0020HasSecondaryResidence,
    ECH0020ReportingMunicipalityRestrictedBaseSecondary,
    ECH0020Delivery,
    ECH0020Header,
)
from openmun_ech.ech0058 import ECH0058Header, ECH0058SendingApplication, ActionType
from openmun_ech.ech0011 import (
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    TypeOfHousehold,
    FederalRegister,
)
from openmun_ech.ech0007 import ECH0007Municipality, ECH0007SwissMunicipality
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0010 import (
    ECH0010AddressInformation,
    ECH0010SwissAddressInformation,
)
from openmun_ech.core import NS

from .person import BaseDeliveryPerson
from .config import DeliveryConfig
from .types import PlaceType


# ============================================================================
# PHASE 2: EVENT MODELS (Base Delivery Event)
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

    Example:
        Person lives in Zürich (main), has vacation home in Davos (secondary):
        >>> sec = SecondaryResidenceInfo(
        ...     bfs="3851",
        ...     name="Davos",
        ...     canton="GR",
        ...     history_id="3851"
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
    history_id: Optional[str] = Field(
        None,
        description="Historical BFS number for merged municipalities"
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
    mail_address_swiss_zip_code: Optional[int] = Field(
        None,
        le=9999,
        description="Mail address Swiss ZIP code (4 digits, e.g., 8001)"
    )
    mail_address_swiss_zip_code_addon: Optional[str] = Field(
        None,
        description="Mail address Swiss ZIP add-on (e.g., '02')"
    )
    mail_address_foreign_zip_code: Optional[str] = Field(
        None,
        max_length=15,
        description="Mail address foreign ZIP code (e.g., '65812' for Germany)"
    )
    mail_address_country: Optional[str] = Field(
        None,
        description="Mail address country at destination (optional, e.g., 'CH')"
    )

    @model_validator(mode='after')
    def validate_place_choice(self) -> 'DestinationInfo':
        """Validate XSD CHOICE #11: place type determines required fields."""
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

    @model_validator(mode='after')
    def validate_mail_address_zip_choice(self) -> 'DestinationInfo':
        """Validate mail address ZIP code CHOICE: swiss XOR foreign."""
        has_swiss = self.mail_address_swiss_zip_code is not None
        has_foreign = self.mail_address_foreign_zip_code is not None

        if has_swiss and has_foreign:
            raise ValueError(
                "Cannot have both mail_address_swiss_zip_code and mail_address_foreign_zip_code"
            )

        # Swiss zip add-on only valid with Swiss zip code
        if self.mail_address_swiss_zip_code_addon and not has_swiss:
            raise ValueError(
                "mail_address_swiss_zip_code_addon requires mail_address_swiss_zip_code"
            )

        return self


class BaseDeliveryEvent(BaseModel):
    """Layer 2: Base delivery event (person + residence).

    Complete eCH-0020 base delivery combining person data (Phase 1) with
    residence/dwelling data (Phase 2).

    This model represents a complete base delivery event: WHO (person) lives WHERE
    (dwelling address in municipality).
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
    reporting_municipality_history_id: Optional[str] = Field(
        None,
        description=(
            "Reporting municipality historical BFS number (for merged municipalities). "
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
        """Validate XSD CHOICE #10: reporting_municipality XOR federal_register."""
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
        """Validate type-specific field requirements."""
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
        """Convert DwellingAddressInfo (Layer 2) → ECH0011DwellingAddress (Layer 1)."""
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
        """Convert DestinationInfo (Layer 2) → ECH0011DestinationType (Layer 1)."""
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

        # Convert optional mail address
        if any([
            dest.mail_address_address_line1,
            dest.mail_address_street,
            dest.mail_address_house_number,
            dest.mail_address_dwelling_number,
            dest.mail_address_locality,
            dest.mail_address_town,
            dest.mail_address_swiss_zip_code,
            dest.mail_address_swiss_zip_code_addon,
            dest.mail_address_foreign_zip_code,
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
                swiss_zip_code=dest.mail_address_swiss_zip_code,
                swiss_zip_code_add_on=dest.mail_address_swiss_zip_code_addon,
                foreign_zip_code=dest.mail_address_foreign_zip_code,
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
        canton: Optional[str],
        history_id: Optional[str] = None
    ) -> ECH0007SwissMunicipality:
        """Convert reporting municipality fields → ECH0007SwissMunicipality."""
        return ECH0007SwissMunicipality(
            municipality_id=bfs,
            municipality_name=name,
            canton_abbreviation=canton,
            history_municipality_id=history_id
        )

    def _convert_secondary_residence_list(
        self,
        secondary_list: Optional[List[SecondaryResidenceInfo]]
    ) -> Optional[List[ECH0007SwissMunicipality]]:
        """Convert List[SecondaryResidenceInfo] → List[ECH0007SwissMunicipality]."""
        if not secondary_list:
            return None

        return [
            ECH0007SwissMunicipality(
                municipality_id=sec.bfs,
                municipality_name=sec.name,
                canton_abbreviation=sec.canton,
                history_municipality_id=sec.history_id
            )
            for sec in secondary_list
        ]

    def _build_main_residence(self) -> ECH0020HasMainResidence:
        """Build ECH0020HasMainResidence from Layer 2 MAIN residence fields."""
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton,
                self.reporting_municipality_history_id
            )
        elif self.federal_register:
            federal_register = FederalRegister(self.federal_register)

        # Convert required fields
        dwelling_address = self._convert_dwelling_address(self.dwelling_address)

        # Convert optional fields
        comes_from = self._convert_destination(self.comes_from) if self.comes_from else None
        goes_to = self._convert_destination(self.goes_to) if self.goes_to else None
        secondary_residence = self._convert_secondary_residence_list(self.secondary_residence_list)

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
        """Build ECH0020HasSecondaryResidence from Layer 2 SECONDARY residence fields."""
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton,
                self.reporting_municipality_history_id
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
        """Build ECH0020ReportingMunicipalityRestrictedBaseSecondary from Layer 2 OTHER residence fields."""
        # Handle CHOICE #10: reporting_municipality XOR federal_register
        reporting_municipality = None
        federal_register = None

        if self.reporting_municipality_bfs and self.reporting_municipality_name:
            reporting_municipality = self._convert_reporting_municipality(
                self.reporting_municipality_bfs,
                self.reporting_municipality_name,
                self.reporting_municipality_canton,
                self.reporting_municipality_history_id
            )
        elif self.federal_register:
            federal_register = FederalRegister(self.federal_register)

        # Convert required fields
        dwelling_address = self._convert_dwelling_address(self.dwelling_address)
        comes_from = self._convert_destination(self.comes_from)  # REQUIRED for OTHER

        # Convert optional fields
        goes_to = self._convert_destination(self.goes_to) if self.goes_to else None

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
        """Convert Layer 2 → Layer 1 (ECH0020EventBaseDelivery)."""
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
    # LAYER 1 → LAYER 2 CONVERSION HELPERS
    # ========================================================================

    @staticmethod
    def _flatten_dwelling_address(dwelling: 'ECH0011DwellingAddress') -> DwellingAddressInfo:
        """Flatten ECH0011DwellingAddress + ECH0010SwissAddressInformation → DwellingAddressInfo."""
        addr = dwelling.address

        return DwellingAddressInfo(
            egid=dwelling.egid,
            ewid=dwelling.ewid,
            household_id=dwelling.household_id,
            address_line1=addr.address_line1,
            address_line2=addr.address_line2,
            street=addr.street,
            house_number=addr.house_number,
            dwelling_number=addr.dwelling_number,
            locality=addr.locality,
            town=addr.town,
            swiss_zip_code=addr.swiss_zip_code,
            swiss_zip_code_add_on=addr.swiss_zip_code_add_on,
            swiss_zip_code_id=addr.swiss_zip_code_id,
            country=addr.country,
            type_of_household=dwelling.type_of_household.value,
            moving_date=dwelling.moving_date
        )

    @staticmethod
    def _flatten_destination(dest: 'ECH0011DestinationType') -> DestinationInfo:
        """Flatten ECH0011DestinationType → DestinationInfo (CHOICE #11)."""
        # Detect place type from Layer 1 CHOICE
        if dest.unknown:
            place_type = PlaceType.UNKNOWN
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
            swiss_muni = dest.swiss_municipality.swiss_municipality
            municipality_bfs = swiss_muni.municipality_id
            municipality_name = swiss_muni.municipality_name
            canton_abbreviation = swiss_muni.canton_abbreviation.value if swiss_muni.canton_abbreviation else None
            municipality_history_id = swiss_muni.history_municipality_id
            country_id = None
            country_iso = None
            country_name_short = None
            town = None

        elif dest.foreign_country:
            place_type = PlaceType.FOREIGN
            country = dest.foreign_country
            country_id = country.country_id
            country_iso = country.country_id_iso2
            country_name_short = country.country_name_short
            town = dest.foreign_town
            municipality_bfs = None
            municipality_name = None
            canton_abbreviation = None
            municipality_history_id = None

        else:
            raise ValueError(
                "Invalid ECH0011DestinationType: must have exactly ONE of "
                "unknown, swiss_municipality, or foreign_country"
            )

        # Extract optional mail address
        mail_address_address_line1 = None
        mail_address_street = None
        mail_address_house_number = None
        mail_address_dwelling_number = None
        mail_address_locality = None
        mail_address_town = None
        mail_address_swiss_zip_code = None
        mail_address_swiss_zip_code_addon = None
        mail_address_foreign_zip_code = None
        mail_address_country = None

        if dest.mail_address:
            addr = dest.mail_address
            mail_address_address_line1 = addr.address_line1
            mail_address_street = addr.street
            mail_address_house_number = addr.house_number
            mail_address_dwelling_number = addr.dwelling_number
            mail_address_locality = addr.locality
            mail_address_town = addr.town
            mail_address_swiss_zip_code = addr.swiss_zip_code
            mail_address_swiss_zip_code_addon = addr.swiss_zip_code_add_on
            mail_address_foreign_zip_code = addr.foreign_zip_code
            mail_address_country = addr.country

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
            mail_address_swiss_zip_code=mail_address_swiss_zip_code,
            mail_address_swiss_zip_code_addon=mail_address_swiss_zip_code_addon,
            mail_address_foreign_zip_code=mail_address_foreign_zip_code,
            mail_address_country=mail_address_country
        )

    @staticmethod
    def _flatten_reporting_municipality(
        muni: 'ECH0007SwissMunicipality'
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Flatten ECH0007SwissMunicipality → reporting_municipality fields."""
        bfs = muni.municipality_id
        name = muni.municipality_name
        canton = muni.canton_abbreviation.value if muni.canton_abbreviation else None
        history_id = muni.history_municipality_id
        return (bfs, name, canton, history_id)

    @staticmethod
    def _flatten_secondary_residence_list(
        secondary_list: Optional[List['ECH0007SwissMunicipality']]
    ) -> Optional[List[SecondaryResidenceInfo]]:
        """Flatten List[ECH0007SwissMunicipality] → List[SecondaryResidenceInfo]."""
        if not secondary_list:
            return None

        result = []
        for muni in secondary_list:
            bfs = muni.municipality_id
            name = muni.municipality_name
            canton = muni.canton_abbreviation.value if muni.canton_abbreviation else None
            history_id = muni.history_municipality_id

            result.append(SecondaryResidenceInfo(
                bfs=bfs,
                name=name,
                canton=canton,
                history_id=history_id
            ))

        return result if result else None

    # ========================================================================
    # LAYER 1 → LAYER 2 EXTRACTOR METHODS
    # ========================================================================

    @classmethod
    def _from_main_residence(
        cls,
        person: 'BaseDeliveryPerson',
        residence: 'ECH0020HasMainResidence',
        base_delivery_valid_from: Optional[date]
    ) -> 'BaseDeliveryEvent':
        """Extract MAIN residence event → BaseDeliveryEvent."""
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        reporting_municipality_history_id = None
        federal_register = None

        if residence.reporting_municipality:
            bfs, name, canton, history_id = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
            reporting_municipality_history_id = history_id
        elif residence.federal_register:
            federal_register = residence.federal_register.value

        arrival_date = residence.arrival_date
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)

        comes_from = None
        if residence.comes_from:
            comes_from = cls._flatten_destination(residence.comes_from)

        departure_date = residence.departure_date

        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        secondary_residence_list = None
        if residence.secondary_residence:
            secondary_residence_list = cls._flatten_secondary_residence_list(residence.secondary_residence)

        return cls(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            reporting_municipality_history_id=reporting_municipality_history_id,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=secondary_residence_list,
            main_residence_bfs=None,
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
        """Extract SECONDARY residence event → BaseDeliveryEvent."""
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        reporting_municipality_history_id = None
        federal_register = None

        if residence.reporting_municipality:
            bfs, name, canton, history_id = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
            reporting_municipality_history_id = history_id
        elif residence.federal_register:
            federal_register = residence.federal_register.value

        arrival_date = residence.arrival_date
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)
        comes_from = cls._flatten_destination(residence.comes_from)

        departure_date = residence.departure_date

        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        main_bfs, main_name, main_canton, _ = cls._flatten_reporting_municipality(residence.main_residence)

        return cls(
            person=person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            reporting_municipality_history_id=reporting_municipality_history_id,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=None,
            main_residence_bfs=main_bfs,
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
        """Extract OTHER residence event → BaseDeliveryEvent."""
        reporting_municipality_bfs = None
        reporting_municipality_name = None
        reporting_municipality_canton = None
        reporting_municipality_history_id = None
        federal_register = None

        if residence.reporting_municipality:
            bfs, name, canton, history_id = cls._flatten_reporting_municipality(residence.reporting_municipality)
            reporting_municipality_bfs = bfs
            reporting_municipality_name = name
            reporting_municipality_canton = canton
            reporting_municipality_history_id = history_id
        elif residence.federal_register:
            federal_register = residence.federal_register.value

        arrival_date = residence.arrival_date
        dwelling_address = cls._flatten_dwelling_address(residence.dwelling_address)
        comes_from = cls._flatten_destination(residence.comes_from)

        departure_date = residence.departure_date

        goes_to = None
        if residence.goes_to:
            goes_to = cls._flatten_destination(residence.goes_to)

        return cls(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs=reporting_municipality_bfs,
            reporting_municipality_name=reporting_municipality_name,
            reporting_municipality_canton=reporting_municipality_canton,
            reporting_municipality_history_id=reporting_municipality_history_id,
            federal_register=federal_register,
            arrival_date=arrival_date,
            dwelling_address=dwelling_address,
            comes_from=comes_from,
            departure_date=departure_date,
            goes_to=goes_to,
            secondary_residence_list=None,
            main_residence_bfs=None,
            main_residence_name=None,
            main_residence_canton=None,
            base_delivery_valid_from=base_delivery_valid_from
        )

    @classmethod
    def from_ech0020_event(cls, event):
        """Convert Layer 1 → Layer 2 (flatten event structure)."""
        # Step 1: Convert person from Layer 1 → Layer 2
        person = BaseDeliveryPerson.from_ech0020(event.base_delivery_person)

        # Step 2: Extract base_delivery_valid_from
        base_delivery_valid_from = event.base_delivery_valid_from

        # Step 3: Detect residence type from CHOICE (exactly one must be present)
        if event.has_main_residence:
            return cls._from_main_residence(
                person=person,
                residence=event.has_main_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        elif event.has_secondary_residence:
            return cls._from_secondary_residence(
                person=person,
                residence=event.has_secondary_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        elif event.has_other_residence:
            return cls._from_other_residence(
                person=person,
                residence=event.has_other_residence,
                base_delivery_valid_from=base_delivery_valid_from
            )
        else:
            raise ValueError(
                "Invalid ECH0020EventBaseDelivery: must have exactly ONE of "
                "has_main_residence, has_secondary_residence, or has_other_residence"
            )

    def validate_swiss_data(self, context: Optional['ValidationContext'] = None) -> 'ValidationContext':
        """Optional validation using Swiss open data for dwelling addresses."""
        # Import here to avoid circular dependency
        from openmun_ech.validation import (
            ValidationContext,
            PostalCodeValidator,
            MunicipalityBFSValidator,
            StreetNameValidator,
            CrossValidator,
        )

        if context is None:
            context = ValidationContext()

        # Validate person data first
        self.person.validate_swiss_data(context)

        # Validate dwelling address fields
        if self.dwelling_address:
            postal_code_str = str(self.dwelling_address.swiss_zip_code)

            if self.dwelling_address.town:
                PostalCodeValidator.validate(
                    postal_code=postal_code_str,
                    town=self.dwelling_address.town,
                    context=context,
                    field_name_prefix="dwelling_address_postal_code + dwelling_address_town"
                )

            if self.dwelling_address.street:
                StreetNameValidator.validate(
                    street_name=self.dwelling_address.street,
                    context=context,
                    municipality_bfs=self.reporting_municipality_bfs,
                    postal_code=postal_code_str,
                    field_name_prefix="dwelling_address_street"
                )

            if self.dwelling_address.street:
                CrossValidator.validate_street_postal(
                    street_name=self.dwelling_address.street,
                    postal_code=postal_code_str,
                    context=context,
                    municipality_bfs=self.reporting_municipality_bfs,
                    field_name_prefix_street="dwelling_address_street",
                    field_name_prefix_postal="dwelling_address_postal_code"
                )

            if self.reporting_municipality_bfs:
                CrossValidator.validate_postal_municipality(
                    postal_code=postal_code_str,
                    municipality_bfs=self.reporting_municipality_bfs,
                    context=context,
                    field_name_prefix_postal="dwelling_address_postal_code",
                    field_name_prefix_municipality="reporting_municipality_bfs"
                )

        if self.reporting_municipality_bfs:
            MunicipalityBFSValidator.validate(
                bfs_code=self.reporting_municipality_bfs,
                municipality_name=self.reporting_municipality_name,
                context=context,
                field_name_prefix="reporting_municipality_bfs"
            )

        if self.comes_from and self.comes_from.place_type == PlaceType.SWISS:
            if self.comes_from.municipality_bfs:
                MunicipalityBFSValidator.validate(
                    bfs_code=self.comes_from.municipality_bfs,
                    municipality_name=self.comes_from.municipality_name,
                    context=context,
                    field_name_prefix="comes_from_municipality_bfs"
                )

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
        """Create complete eCH-0020 delivery ready for XML export."""
        # Step 1: Auto-generate message_id if not provided (UUID)
        if message_id is None:
            message_id = str(uuid4())

        # Step 2: Default message_date to now() if not provided
        if message_date is None:
            message_date = datetime.now(timezone.utc)

        # Step 3: Determine message_type
        message_type = config.message_type_override or NS.ECH0020_V3

        # Step 4: Build ECH0058SendingApplication from config
        sending_application = ECH0058SendingApplication(
            manufacturer=config.manufacturer,
            product=config.product,
            product_version=config.product_version
        )

        # Step 5: Build ECH0058Header
        ech0058_header = ECH0058Header(
            sender_id=config.sender_id,
            message_id=message_id,
            message_type=message_type,
            sending_application=sending_application,
            message_date=message_date,
            action=action,
            test_delivery_flag=config.test_delivery_flag,
            original_sender_id=config.original_sender_id,
            **optional_header_fields
        )

        # Step 6: Build ECH0020Header wrapper
        ech0020_header = ECH0020Header(
            header=ech0058_header,
            data_lock=None,
            data_lock_valid_from=None,
            data_lock_valid_till=None
        )

        # Step 7: Convert Layer 2 event to Layer 1 event
        event_layer1 = self.to_ech0020_event()

        # Step 8: Construct complete ECH0020Delivery
        delivery = ECH0020Delivery(
            delivery_header=ech0020_header,
            event=[event_layer1],
            version="3.0"
        )

        return delivery
