"""eCH-0020 v3.0 — Move Events."""

from typing import Optional, List
from datetime import date
from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0011 import (
    ECH0011ContactData,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    FederalRegister,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .person_types import ECH0020BaseDeliveryRestrictedMoveInPerson


class ECH0020ReportingMunicipalityRestrictedMoveIn(ECHModel):
    """Restricted reporting municipality for move-in events.

    XSD restriction of reportingMunicipalityType with required fields for move-in.

    XSD: reportingMunicipalityRestrictedMoveInType (eCH-0020-3-0.xsd lines 502-516)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # REQUIRED fields for move-in event
    arrival_date: date = xml_field('arrivalDate')
    comes_from: ECH0011DestinationType = xml_field(
        'comesFrom', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMoveIn':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveInType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveInType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self


class ECH0020ReportingMunicipalityRestrictedMoveOut(ECHModel):
    """Restricted reporting municipality for move-out events.

    XSD restriction of reportingMunicipalityType with required fields for move-out.

    XSD: reportingMunicipalityRestrictedMoveOutType (eCH-0020-3-0.xsd lines 517-530)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # REQUIRED fields for move-out event
    departure_date: date = xml_field('departureDate')
    goes_to: ECH0011DestinationType = xml_field(
        'goesTo', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMoveOut':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveOutType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveOutType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self


class ECH0020ReportingMunicipalityRestrictedMove(ECHModel):
    """Restricted reporting municipality for internal move events.

    XSD restriction of reportingMunicipalityType for moves within same municipality.

    XSD: reportingMunicipalityRestrictedMoveType (eCH-0020-3-0.xsd lines 531-543)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # REQUIRED field for internal move event
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMove':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self


# ============================================================================
# MOVE-IN EVENT HELPER TYPES (Inline complexType extensions for eventMoveIn)
# ============================================================================

class ECH0020HasMainResidenceMoveIn(ECHModel):
    """Main residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with optional secondary residences.

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType (lines 546-559)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'hasMainResidence'

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )
    arrival_date: date = xml_field('arrivalDate')
    comes_from: ECH0011DestinationType = xml_field(
        'comesFrom', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # Extension: additional secondary residences
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = xml_field(
        'secondaryResidence', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5, is_list=True,
    )

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasMainResidenceMoveIn':
        """Validate XSD CHOICE: reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError("hasMainResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasMainResidence allows either reportingMunicipality OR federalRegister, not both")

        return self


class ECH0020HasSecondaryResidenceMoveIn(ECHModel):
    """Secondary residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with required main residence.

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType (lines 560-570)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'hasSecondaryResidence'

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )
    arrival_date: date = xml_field('arrivalDate')
    comes_from: ECH0011DestinationType = xml_field(
        'comesFrom', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = xml_field(
        'mainResidence', wrapper=True, child_ns=NS.ECH0007_V5,
    )

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasSecondaryResidenceMoveIn':
        """Validate XSD CHOICE: reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError("hasSecondaryResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasSecondaryResidence allows either reportingMunicipality OR federalRegister, not both")

        return self


# ============================================================================
# EVENT TYPES - MOVEMENT/RESIDENCE (Move-in, Move-out, Move)
# ============================================================================

class ECH0020EventMoveIn(ECHModel):
    """Move-in event - person moves into municipality from another location.

    XSD: eventMoveIn (eCH-0020-3-0.xsd lines 544-574)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMoveIn'

    move_in_person: ECH0020BaseDeliveryRestrictedMoveInPerson = xml_field('moveInPerson')

    # XSD CHOICE: exactly one of three residence types
    has_main_residence: Optional[ECH0020HasMainResidenceMoveIn] = xml_field(
        'hasMainResidence', default=None,
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidenceMoveIn] = xml_field(
        'hasSecondaryResidence', default=None,
    )
    has_other_residence: Optional[ECH0020ReportingMunicipalityRestrictedMoveIn] = xml_field(
        'hasOtherResidence', default=None,
    )

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventMoveIn':
        """Validate XSD CHOICE: exactly ONE of hasMainResidence, hasSecondaryResidence, or hasOtherResidence."""
        residences = [
            self.has_main_residence,
            self.has_secondary_residence,
            self.has_other_residence
        ]
        set_count = sum(1 for r in residences if r is not None)

        if set_count == 0:
            raise ValueError(
                "eventMoveIn requires exactly one of: hasMainResidence, "
                "hasSecondaryResidence, or hasOtherResidence"
            )
        if set_count > 1:
            raise ValueError(
                f"eventMoveIn allows only one residence type, but {set_count} are set"
            )

        return self


class ECH0020EventMove(ECHModel):
    """Internal move event - person moves to new address within same municipality.

    XSD: eventMove (eCH-0020-3-0.xsd lines 575-581)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMove'

    move_person: ECH0044PersonIdentification = xml_field(
        'movePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    move_reporting_municipality: ECH0020ReportingMunicipalityRestrictedMove = xml_field(
        'moveReportingMunicipality',
    )


class ECH0020EventContact(ECHModel):
    """Contact update event - person's contact information changes.

    XSD: eventContact (eCH-0020-3-0.xsd lines 582-588)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventContact'

    contact_person: ECH0044PersonIdentification = xml_field(
        'contactPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    contact_data: ECH0011ContactData = xml_field(
        'contactData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventMoveOut(ECHModel):
    """Move-out event - person moves out of municipality to another location.

    XSD: eventMoveOut (eCH-0020-3-0.xsd lines 589-595)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMoveOut'

    move_out_person: ECH0044PersonIdentification = xml_field(
        'moveOutPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    move_out_reporting_destination: ECH0020ReportingMunicipalityRestrictedMoveOut = xml_field(
        'moveOutReportingDestination',
    )


class ECH0020EventChangeResidenceType(ECHModel):
    """Change residence type event - person changes from main/secondary/other residence.

    XSD: eventChangeResidenceTypeType (eCH-0020-3-0.xsd lines 596-603)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeResidenceTypeType'

    change_residence_type_person: ECH0020BaseDeliveryRestrictedMoveInPerson = xml_field(
        'changeResidenceTypePerson',
    )
    change_residence_type_reporting_relationship: ECH0020ReportingMunicipalityRestrictedMoveIn = xml_field(
        'changeResidenceTypeReportingRelationship',
    )
    residence_type_valid_from: Optional[date] = xml_field(
        'residenceTypeValidFrom', default=None,
    )
