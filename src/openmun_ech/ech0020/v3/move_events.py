"""eCH-0020 v3.0 — Move Events."""

import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

from openmun_ech.core import NS
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0011 import (
    ECH0011ContactData,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    FederalRegister,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .person_types import ECH0020BaseDeliveryRestrictedMoveInPerson


class ECH0020ReportingMunicipalityRestrictedMoveIn(BaseModel):
    """Restricted reporting municipality for move-in events.

    XSD restriction of reportingMunicipalityType with required fields for move-in.

    XSD: reportingMunicipalityRestrictedMoveInType (eCH-0020-3-0.xsd lines 502-516)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - comesFrom: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    - departureDate: EXCLUDED (not part of move-in)
    - goesTo: EXCLUDED (not part of move-in)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields for move-in event
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        alias='comesFrom',
        description='Previous residence where person came from (REQUIRED)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)

        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMoveIn':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address
        )


class ECH0020ReportingMunicipalityRestrictedMoveOut(BaseModel):
    """Restricted reporting municipality for move-out events.

    XSD restriction of reportingMunicipalityType with required fields for move-out.

    XSD: reportingMunicipalityRestrictedMoveOutType (eCH-0020-3-0.xsd lines 517-530)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - departureDate: REQUIRED (was optional)
    - goesTo: REQUIRED (was optional)
    - arrivalDate: EXCLUDED (not part of move-out)
    - comesFrom: EXCLUDED (not part of move-out)
    - dwellingAddress: EXCLUDED (not part of move-out)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person was registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields for move-out event
    departure_date: date = Field(
        ...,
        alias='departureDate',
        description='Date of departure from this municipality (REQUIRED)'
    )
    goes_to: ECH0011DestinationType = Field(
        ...,
        alias='goesTo',
        description='Destination where person is going (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
        departure_elem.text = self.departure_date.isoformat()

        # Create wrapper element in parent namespace
        goesTo_wrapper = ET.SubElement(elem, f'{{{namespace}}}goesTo')
        goesTo_content = self.goes_to.to_xml(namespace=ns_011)
        for child in goesTo_content:
            goesTo_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMoveOut':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is None or not departure_elem.text:
            raise ValueError("reportingMunicipalityRestrictedMoveOutType requires departureDate")
        departure_date = date.fromisoformat(departure_elem.text)

        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveOutType requires goesTo")
        goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedMove(BaseModel):
    """Restricted reporting municipality for internal move events.

    XSD restriction of reportingMunicipalityType for moves within same municipality.

    XSD: reportingMunicipalityRestrictedMoveType (eCH-0020-3-0.xsd lines 531-543)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - dwellingAddress: REQUIRED (the new address within municipality)
    - arrivalDate: EXCLUDED (person stays in same municipality)
    - comesFrom: EXCLUDED (internal move)
    - departureDate: EXCLUDED (internal move)
    - goesTo: EXCLUDED (internal move)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person remains registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED field for internal move event
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='New dwelling address within municipality (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required field
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMove':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required field
        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            dwelling_address=dwelling_address
        )


# ============================================================================
# MOVE-IN EVENT HELPER TYPES (Inline complexType extensions for eventMoveIn)
# ============================================================================

class ECH0020HasMainResidenceMoveIn(BaseModel):
    """Main residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with optional secondary residences.
    This is an inline anonymous type from eventMoveIn XSD definition (lines 546-559).

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType
    """

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')

    # Extension: additional secondary residences
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = Field(
        None,
        alias='secondaryResidence',
        description='Secondary residence municipalities (0-n)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'hasMainResidence'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required base fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Extension: secondary residences
        if self.secondary_residence:
            for sec_res in self.secondary_residence:
                # Create wrapper element

                secondaryResidence_wrapper = ET.SubElement(elem, f'{{{namespace}}}secondaryResidence')

                secondaryResidence_content = sec_res.to_xml(namespace=ns_007)

                for child in secondaryResidence_content:

                    secondaryResidence_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020HasMainResidenceMoveIn':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("hasMainResidence requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("hasMainResidence requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("hasMainResidence requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Extension: secondary residences
        secondary_residence = None
        sec_res_elems = element.findall(f'{{{ns_020}}}secondaryResidence')
        if sec_res_elems:
            secondary_residence = [ECH0007SwissMunicipality.from_xml(e) for e in sec_res_elems]

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            secondary_residence=secondary_residence
        )


class ECH0020HasSecondaryResidenceMoveIn(BaseModel):
    """Secondary residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with required main residence.
    This is an inline anonymous type from eventMoveIn XSD definition (lines 560-570).

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType
    """

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = Field(
        ...,
        alias='mainResidence',
        description='Main residence municipality (required for secondary residence)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'hasSecondaryResidence'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required base fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Extension: main residence
        # Create wrapper element in parent namespace
        mainResidence_wrapper = ET.SubElement(elem, f'{{{namespace}}}mainResidence')
        mainResidence_content = self.main_residence.to_xml(namespace=ns_007)
        for child in mainResidence_content:
            mainResidence_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020HasSecondaryResidenceMoveIn':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("hasSecondaryResidence requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("hasSecondaryResidence requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("hasSecondaryResidence requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Extension: main residence
        main_res_elem = element.find(f'{{{ns_020}}}mainResidence')
        if main_res_elem is None:
            raise ValueError("hasSecondaryResidence requires mainResidence")
        main_residence = ECH0007SwissMunicipality.from_xml(main_res_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            main_residence=main_residence
        )


# ============================================================================
# EVENT TYPES - MOVEMENT/RESIDENCE (Move-in, Move-out, Move)
# ============================================================================

class ECH0020EventMoveIn(BaseModel):
    """Move-in event - person moves into municipality from another location.

    XSD: eventMoveIn (eCH-0020-3-0.xsd lines 544-574)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - moveInPerson: Person data (baseDeliveryRestrictedMoveInPersonType, required)
    - CHOICE: hasMainResidence OR hasSecondaryResidence OR hasOtherResidence
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    move_in_person: 'ECH0020BaseDeliveryRestrictedMoveInPerson' = Field(
        ...,
        alias='moveInPerson',
        description='Person moving into municipality'
    )

    # XSD CHOICE: exactly one of three residence types
    has_main_residence: Optional[ECH0020HasMainResidenceMoveIn] = Field(
        None,
        alias='hasMainResidence',
        description='Person establishes main residence in this municipality'
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidenceMoveIn] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Person establishes secondary residence in this municipality'
    )
    has_other_residence: Optional['ECH0020ReportingMunicipalityRestrictedMoveIn'] = Field(
        None,
        alias='hasOtherResidence',
        description='Person has other residence type in this municipality'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMoveIn'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # moveInPerson (required)
        self.move_in_person.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='moveInPerson'
        )

        # CHOICE: exactly one residence type
        if self.has_main_residence:
            self.has_main_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasMainResidence'
            )
        elif self.has_secondary_residence:
            self.has_secondary_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasSecondaryResidence'
            )
        elif self.has_other_residence:
            self.has_other_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasOtherResidence'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMoveIn':
        """Parse from XML element."""
        ns = NS.ECH0020_V3

        # moveInPerson (required)
        person_elem = elem.find(f'{{{ns}}}moveInPerson')
        if person_elem is None:
            raise ValueError("eventMoveIn requires moveInPerson")
        move_in_person = ECH0020BaseDeliveryRestrictedMoveInPerson.from_xml(person_elem)

        # CHOICE: exactly one residence type
        has_main_residence = None
        main_res_elem = elem.find(f'{{{ns}}}hasMainResidence')
        if main_res_elem is not None:
            has_main_residence = ECH0020HasMainResidenceMoveIn.from_xml(main_res_elem)

        has_secondary_residence = None
        sec_res_elem = elem.find(f'{{{ns}}}hasSecondaryResidence')
        if sec_res_elem is not None:
            has_secondary_residence = ECH0020HasSecondaryResidenceMoveIn.from_xml(sec_res_elem)

        has_other_residence = None
        other_res_elem = elem.find(f'{{{ns}}}hasOtherResidence')
        if other_res_elem is not None:
            has_other_residence = ECH0020ReportingMunicipalityRestrictedMoveIn.from_xml(other_res_elem)

        # extension: Not implemented

        return cls(
            move_in_person=move_in_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence
        )


class ECH0020EventMove(BaseModel):
    """Internal move event - person moves to new address within same municipality.

    XSD: eventMove (eCH-0020-3-0.xsd lines 575-581)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - movePerson: Person identification (required)
    - moveReportingMunicipality: New dwelling address (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    move_person: ECH0044PersonIdentification = Field(
        ...,
        alias='movePerson',
        description='Person moving to new address within municipality'
    )
    move_reporting_municipality: 'ECH0020ReportingMunicipalityRestrictedMove' = Field(
        ...,
        alias='moveReportingMunicipality',
        description='New dwelling address and municipality information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMove'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # movePerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.move_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='movePerson',
            wrapper_namespace=ns_020
        )

        # moveReportingMunicipality (required)
        self.move_reporting_municipality.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='moveReportingMunicipality'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMove':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

        # movePerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}movePerson')
        if person_elem is None:
            raise ValueError("eventMove requires movePerson")
        move_person = ECH0044PersonIdentification.from_xml(person_elem)

        # moveReportingMunicipality (required)
        municipality_elem = elem.find(f'{{{ns_020}}}moveReportingMunicipality')
        if municipality_elem is None:
            raise ValueError("eventMove requires moveReportingMunicipality")
        move_reporting_municipality = ECH0020ReportingMunicipalityRestrictedMove.from_xml(municipality_elem)

        # extension: Not implemented

        return cls(
            move_person=move_person,
            move_reporting_municipality=move_reporting_municipality
        )


class ECH0020EventContact(BaseModel):
    """Contact update event - person's contact information changes.

    XSD: eventContact (eCH-0020-3-0.xsd lines 582-588)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - contactPerson: Person identification (required)
    - contactData: New contact information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    contact_person: ECH0044PersonIdentification = Field(
        ...,
        alias='contactPerson',
        description='Person whose contact information is being updated'
    )
    contact_data: ECH0011ContactData = Field(
        ...,
        alias='contactData',
        description='New contact information (email, phone, etc.)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventContact'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling.

        Namespace wrapper pattern:
        - Wrapper elements (contactPerson, contactData) in eCH-0020 (no prefix)
        - Content inside wrappers from eCH-0044 and eCH-0011 (with prefix)
        """
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # contactPerson (required) - wrapper in ns_020, content in ns_044
        self.contact_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='contactPerson',
            wrapper_namespace=ns_020
        )

        # contactData (required) - wrapper in ns_020, content in ns_011
        self.contact_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='contactData',
            wrapper_namespace=ns_020
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventContact':
        """Parse from XML element.

        Namespace wrapper pattern:
        - Wrapper elements (contactPerson, contactData) are in eCH-0020 (no prefix)
        - Content inside wrappers is from eCH-0044 and eCH-0011 (with prefix)
        """
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

        # contactPerson (required) - wrapper in ns_020
        person_elem = elem.find(f'{{{ns_020}}}contactPerson')
        if person_elem is None:
            raise ValueError("eventContact requires contactPerson")
        contact_person = ECH0044PersonIdentification.from_xml(person_elem)

        # contactData (required) - wrapper in ns_020
        data_elem = elem.find(f'{{{ns_020}}}contactData')
        if data_elem is None:
            raise ValueError("eventContact requires contactData")
        contact_data = ECH0011ContactData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            contact_person=contact_person,
            contact_data=contact_data
        )


class ECH0020EventMoveOut(BaseModel):
    """Move-out event - person moves out of municipality to another location.

    XSD: eventMoveOut (eCH-0020-3-0.xsd lines 589-595)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - moveOutPerson: Person identification (required)
    - moveOutReportingDestination: Departure date and destination (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    move_out_person: ECH0044PersonIdentification = Field(
        ...,
        alias='moveOutPerson',
        description='Person moving out of municipality'
    )
    move_out_reporting_destination: 'ECH0020ReportingMunicipalityRestrictedMoveOut' = Field(
        ...,
        alias='moveOutReportingDestination',
        description='Departure date and destination information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMoveOut'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # moveOutPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.move_out_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='moveOutPerson',
            wrapper_namespace=ns_020
        )

        # moveOutReportingDestination (required)
        self.move_out_reporting_destination.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='moveOutReportingDestination'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMoveOut':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

        # moveOutPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}moveOutPerson')
        if person_elem is None:
            raise ValueError("eventMoveOut requires moveOutPerson")
        move_out_person = ECH0044PersonIdentification.from_xml(person_elem)

        # moveOutReportingDestination (required)
        destination_elem = elem.find(f'{{{ns_020}}}moveOutReportingDestination')
        if destination_elem is None:
            raise ValueError("eventMoveOut requires moveOutReportingDestination")
        move_out_reporting_destination = ECH0020ReportingMunicipalityRestrictedMoveOut.from_xml(destination_elem)

        # extension: Not implemented

        return cls(
            move_out_person=move_out_person,
            move_out_reporting_destination=move_out_reporting_destination
        )


class ECH0020EventChangeResidenceType(BaseModel):
    """Change residence type event - person changes from main/secondary/other residence.

    XSD: eventChangeResidenceTypeType (eCH-0020-3-0.xsd lines 596-603)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeResidenceTypePerson: Person data (required)
    - changeResidenceTypeReportingRelationship: New residence relationship (required)
    - residenceTypeValidFrom: Validity start date (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    change_residence_type_person: 'ECH0020BaseDeliveryRestrictedMoveInPerson' = Field(
        ...,
        alias='changeResidenceTypePerson',
        description='Person whose residence type is changing'
    )
    change_residence_type_reporting_relationship: 'ECH0020ReportingMunicipalityRestrictedMoveIn' = Field(
        ...,
        alias='changeResidenceTypeReportingRelationship',
        description='New residence relationship information'
    )

    # Optional field
    residence_type_valid_from: Optional[date] = Field(
        None,
        alias='residenceTypeValidFrom',
        description='Date from which new residence type is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeResidenceTypeType'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns}}}{element_name}')

        # changeResidenceTypePerson (required)
        self.change_residence_type_person.to_xml(
            parent=elem,
            namespace=ns,
            element_name='changeResidenceTypePerson'
        )

        # changeResidenceTypeReportingRelationship (required)
        self.change_residence_type_reporting_relationship.to_xml(
            parent=elem,
            namespace=ns,
            element_name='changeResidenceTypeReportingRelationship'
        )

        # residenceTypeValidFrom (optional)
        if self.residence_type_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns}}}residenceTypeValidFrom')
            valid_from_elem.text = self.residence_type_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeResidenceType':
        """Parse from XML element."""
        ns = NS.ECH0020_V3

        # changeResidenceTypePerson (required)
        person_elem = elem.find(f'{{{ns}}}changeResidenceTypePerson')
        if person_elem is None:
            raise ValueError("eventChangeResidenceTypeType requires changeResidenceTypePerson")
        change_residence_type_person = ECH0020BaseDeliveryRestrictedMoveInPerson.from_xml(person_elem)

        # changeResidenceTypeReportingRelationship (required)
        relationship_elem = elem.find(f'{{{ns}}}changeResidenceTypeReportingRelationship')
        if relationship_elem is None:
            raise ValueError("eventChangeResidenceTypeType requires changeResidenceTypeReportingRelationship")
        change_residence_type_reporting_relationship = ECH0020ReportingMunicipalityRestrictedMoveIn.from_xml(relationship_elem)

        # residenceTypeValidFrom (optional)
        residence_type_valid_from = None
        valid_from_elem = elem.find(f'{{{ns}}}residenceTypeValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            residence_type_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            change_residence_type_person=change_residence_type_person,
            change_residence_type_reporting_relationship=change_residence_type_reporting_relationship,
            residence_type_valid_from=residence_type_valid_from
        )


