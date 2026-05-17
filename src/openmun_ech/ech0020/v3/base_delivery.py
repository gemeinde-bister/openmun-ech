"""eCH-0020 v3.0 — Base Delivery."""

import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

from openmun_ech.core import NS
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0011 import (
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    FederalRegister,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .person_types import (
    ECH0020BaseDeliveryPerson,
    ECH0020ReportingMunicipalityRestrictedBaseSecondary,
    ECH0020HasMainResidence,
    ECH0020HasSecondaryResidence,
)


# TYPE 13/89: EVENT BASE DELIVERY
# ============================================================================

class ECH0020EventBaseDelivery(BaseModel):
    """Base delivery event structure.

    Base deliveries are complete snapshots of a municipality's population register.
    This event type contains person data plus residence information.

    XSD: eventBaseDelivery (eCH-0020-3-0.xsd lines 173-203)
    PDF: Unknown section (base delivery event structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - baseDeliveryPerson: Complete person data (required)
    - CHOICE: hasMainResidence OR hasSecondaryResidence OR hasOtherResidence
    - baseDeliveryValidFrom: Validity start date (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    base_delivery_person: 'ECH0020BaseDeliveryPerson' = Field(
        ...,
        alias='baseDeliveryPerson',
        description='Complete person data for base delivery'
    )

    # XSD CHOICE: exactly one of three residence types
    has_main_residence: Optional[ECH0020HasMainResidence] = Field(
        None,
        alias='hasMainResidence',
        description='Person has main residence in this municipality'
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidence] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Person has secondary residence in this municipality'
    )
    has_other_residence: Optional['ECH0020ReportingMunicipalityRestrictedBaseSecondary'] = Field(
        None,
        alias='hasOtherResidence',
        description='Person has other residence type in this municipality'
    )

    # Optional fields
    base_delivery_valid_from: Optional[date] = Field(
        None,
        alias='baseDeliveryValidFrom',
        description='Date from which this base delivery is valid'
    )

    # Note: extension element not implemented (xs:element ref="eCH-0020:extension")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventBaseDelivery':
        """Validate XSD CHOICE: exactly ONE residence type must be present."""
        has_main = self.has_main_residence is not None
        has_secondary = self.has_secondary_residence is not None
        has_other = self.has_other_residence is not None

        residence_count = sum([has_main, has_secondary, has_other])

        if residence_count == 0:
            raise ValueError(
                "eventBaseDelivery requires exactly ONE of: hasMainResidence, "
                "hasSecondaryResidence, or hasOtherResidence"
            )
        if residence_count > 1:
            raise ValueError(
                f"eventBaseDelivery allows only ONE residence type, but {residence_count} were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventBaseDelivery',
        skip_wrapper: bool = False
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI
            element_name: Name of the XML element
            skip_wrapper: If True, serialize children directly into parent
                         (used when this type is embedded without element wrapper)

        Returns:
            XML Element
        """
        if skip_wrapper and parent is not None:
            # Type used inline - serialize children into parent directly
            elem = parent
        elif parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # 1. baseDeliveryPerson (required)
        self.base_delivery_person.to_xml(
            parent=elem, namespace=namespace, element_name='baseDeliveryPerson'
        )

        # 2. CHOICE: residence type
        if self.has_main_residence:
            # hasMainResidence extends reportingMunicipalityRestrictedBaseMainType
            main_elem = ET.SubElement(elem, f'{{{namespace}}}hasMainResidence')

            # Base fields from reportingMunicipalityRestrictedBaseMainType
            if self.has_main_residence.reporting_municipality:
                # Create wrapper element in eCH-0020 namespace
                reporting_mun_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}reportingMunicipality')
                mun_content = self.has_main_residence.reporting_municipality.to_xml(namespace=ns_007)
                for child in mun_content:
                    reporting_mun_wrapper.append(child)
            elif self.has_main_residence.federal_register:
                reg_elem = ET.SubElement(main_elem, f'{{{namespace}}}federalRegister')
                reg_elem.text = self.has_main_residence.federal_register.value

            arrival_elem = ET.SubElement(main_elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.has_main_residence.arrival_date.isoformat()

            if self.has_main_residence.comes_from:
                # Create wrapper element in eCH-0020 namespace
                comes_from_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}comesFrom')
                comes_from_content = self.has_main_residence.comes_from.to_xml(namespace=ns_011)
                for child in comes_from_content:
                    comes_from_wrapper.append(child)

            # Create wrapper element in eCH-0020 namespace
            dwelling_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}dwellingAddress')
            dwelling_content = self.has_main_residence.dwelling_address.to_xml(namespace=ns_011)
            for child in dwelling_content:
                dwelling_wrapper.append(child)

            if self.has_main_residence.departure_date:
                dep_elem = ET.SubElement(main_elem, f'{{{namespace}}}departureDate')
                dep_elem.text = self.has_main_residence.departure_date.isoformat()

            if self.has_main_residence.goes_to:
                # Create wrapper element in eCH-0020 namespace
                goes_to_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}goesTo')
                goes_to_content = self.has_main_residence.goes_to.to_xml(namespace=ns_011)
                for child in goes_to_content:
                    goes_to_wrapper.append(child)

            # Extension: secondaryResidence (0-n)
            if self.has_main_residence.secondary_residence:
                for sec_res in self.has_main_residence.secondary_residence:
                    # Create wrapper element in eCH-0020 namespace
                    sec_res_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}secondaryResidence')
                    sec_res_content = sec_res.to_xml(namespace=ns_007)
                    for child in sec_res_content:
                        sec_res_wrapper.append(child)

        elif self.has_secondary_residence:
            # hasSecondaryResidence extends reportingMunicipalityRestrictedBaseSecondaryType
            sec_elem = ET.SubElement(elem, f'{{{namespace}}}hasSecondaryResidence')

            # Base fields
            if self.has_secondary_residence.reporting_municipality:
                # Create wrapper element in eCH-0020 namespace
                reporting_mun_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}reportingMunicipality')
                mun_content = self.has_secondary_residence.reporting_municipality.to_xml(namespace=ns_007)
                for child in mun_content:
                    reporting_mun_wrapper.append(child)
            elif self.has_secondary_residence.federal_register:
                reg_elem = ET.SubElement(sec_elem, f'{{{namespace}}}federalRegister')
                reg_elem.text = self.has_secondary_residence.federal_register.value

            arrival_elem = ET.SubElement(sec_elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.has_secondary_residence.arrival_date.isoformat()

            # Create wrapper element in eCH-0020 namespace
            comes_from_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}comesFrom')
            comes_from_content = self.has_secondary_residence.comes_from.to_xml(namespace=ns_011)
            for child in comes_from_content:
                comes_from_wrapper.append(child)

            # Create wrapper element in eCH-0020 namespace
            dwelling_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}dwellingAddress')
            dwelling_content = self.has_secondary_residence.dwelling_address.to_xml(namespace=ns_011)
            for child in dwelling_content:
                dwelling_wrapper.append(child)

            if self.has_secondary_residence.departure_date:
                dep_elem = ET.SubElement(sec_elem, f'{{{namespace}}}departureDate')
                dep_elem.text = self.has_secondary_residence.departure_date.isoformat()

            if self.has_secondary_residence.goes_to:
                # Create wrapper element in eCH-0020 namespace
                goes_to_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}goesTo')
                goes_to_content = self.has_secondary_residence.goes_to.to_xml(namespace=ns_011)
                for child in goes_to_content:
                    goes_to_wrapper.append(child)

            # Extension: mainResidence (required)
            # Create wrapper element in eCH-0020 namespace
            main_res_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}mainResidence')
            main_res_content = self.has_secondary_residence.main_residence.to_xml(namespace=ns_007)
            for child in main_res_content:
                main_res_wrapper.append(child)

        elif self.has_other_residence:
            # hasOtherResidence uses reportingMunicipalityRestrictedBaseSecondaryType directly
            self.has_other_residence.to_xml(
                parent=elem, namespace=namespace, element_name='hasOtherResidence'
            )

        # 3. baseDeliveryValidFrom (optional)
        if self.base_delivery_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}baseDeliveryValidFrom')
            valid_elem.text = self.base_delivery_valid_from.isoformat()

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventBaseDelivery':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # Required: baseDeliveryPerson
        person_elem = element.find(f'{{{ns_020}}}baseDeliveryPerson')
        if person_elem is None:
            raise ValueError("eventBaseDelivery requires baseDeliveryPerson")
        base_delivery_person = ECH0020BaseDeliveryPerson.from_xml(person_elem)

        # CHOICE: residence type (parse all three, validate later)
        has_main_residence = None
        main_elem = element.find(f'{{{ns_020}}}hasMainResidence')
        if main_elem is not None:
            # Parse base fields
            reporting_municipality = None
            mun_elem = main_elem.find(f'{{{ns_020}}}reportingMunicipality')
            if mun_elem is not None:
                reporting_municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

            federal_register = None
            reg_elem = main_elem.find(f'{{{ns_020}}}federalRegister')
            if reg_elem is not None and reg_elem.text:
                federal_register = FederalRegister(reg_elem.text)

            arr_elem = main_elem.find(f'{{{ns_020}}}arrivalDate')
            if arr_elem is None or not arr_elem.text:
                raise ValueError("hasMainResidence requires arrivalDate")
            arrival_date = date.fromisoformat(arr_elem.text)

            comes_from = None
            cf_elem = main_elem.find(f'{{{ns_020}}}comesFrom')
            if cf_elem is not None:
                comes_from = ECH0011DestinationType.from_xml(cf_elem)

            dw_elem = main_elem.find(f'{{{ns_020}}}dwellingAddress')
            if dw_elem is None:
                raise ValueError("hasMainResidence requires dwellingAddress")
            dwelling_address = ECH0011DwellingAddress.from_xml(dw_elem)

            departure_date = None
            dep_elem = main_elem.find(f'{{{ns_020}}}departureDate')
            if dep_elem is not None and dep_elem.text:
                departure_date = date.fromisoformat(dep_elem.text)

            goes_to = None
            gt_elem = main_elem.find(f'{{{ns_020}}}goesTo')
            if gt_elem is not None:
                goes_to = ECH0011DestinationType.from_xml(gt_elem)

            # Extension: secondaryResidence (0-n)
            secondary_residence = None
            sec_elems = main_elem.findall(f'{{{ns_020}}}secondaryResidence')
            if sec_elems:
                secondary_residence = [ECH0007SwissMunicipality.from_xml(e) for e in sec_elems]

            has_main_residence = ECH0020HasMainResidence(
                reporting_municipality=reporting_municipality,
                federal_register=federal_register,
                arrival_date=arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=departure_date,
                goes_to=goes_to,
                secondary_residence=secondary_residence
            )

        has_secondary_residence = None
        sec_elem = element.find(f'{{{ns_020}}}hasSecondaryResidence')
        if sec_elem is not None:
            # Parse base fields
            reporting_municipality = None
            mun_elem = sec_elem.find(f'{{{ns_020}}}reportingMunicipality')
            if mun_elem is not None:
                reporting_municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

            federal_register = None
            reg_elem = sec_elem.find(f'{{{ns_020}}}federalRegister')
            if reg_elem is not None and reg_elem.text:
                federal_register = FederalRegister(reg_elem.text)

            arr_elem = sec_elem.find(f'{{{ns_020}}}arrivalDate')
            if arr_elem is None or not arr_elem.text:
                raise ValueError("hasSecondaryResidence requires arrivalDate")
            arrival_date = date.fromisoformat(arr_elem.text)

            cf_elem = sec_elem.find(f'{{{ns_020}}}comesFrom')
            if cf_elem is None:
                raise ValueError("hasSecondaryResidence requires comesFrom")
            comes_from = ECH0011DestinationType.from_xml(cf_elem)

            dw_elem = sec_elem.find(f'{{{ns_020}}}dwellingAddress')
            if dw_elem is None:
                raise ValueError("hasSecondaryResidence requires dwellingAddress")
            dwelling_address = ECH0011DwellingAddress.from_xml(dw_elem)

            departure_date = None
            dep_elem = sec_elem.find(f'{{{ns_020}}}departureDate')
            if dep_elem is not None and dep_elem.text:
                departure_date = date.fromisoformat(dep_elem.text)

            goes_to = None
            gt_elem = sec_elem.find(f'{{{ns_020}}}goesTo')
            if gt_elem is not None:
                goes_to = ECH0011DestinationType.from_xml(gt_elem)

            # Extension: mainResidence (required)
            main_res_elem = sec_elem.find(f'{{{ns_020}}}mainResidence')
            if main_res_elem is None:
                raise ValueError("hasSecondaryResidence requires mainResidence")
            main_residence = ECH0007SwissMunicipality.from_xml(main_res_elem)

            has_secondary_residence = ECH0020HasSecondaryResidence(
                reporting_municipality=reporting_municipality,
                federal_register=federal_register,
                arrival_date=arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=departure_date,
                goes_to=goes_to,
                main_residence=main_residence
            )

        has_other_residence = None
        other_elem = element.find(f'{{{ns_020}}}hasOtherResidence')
        if other_elem is not None:
            has_other_residence = ECH0020ReportingMunicipalityRestrictedBaseSecondary.from_xml(other_elem)

        # Optional: baseDeliveryValidFrom
        base_delivery_valid_from = None
        valid_elem = element.find(f'{{{ns_020}}}baseDeliveryValidFrom')
        if valid_elem is not None and valid_elem.text:
            base_delivery_valid_from = date.fromisoformat(valid_elem.text)

        return cls(
            base_delivery_person=base_delivery_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence,
            base_delivery_valid_from=base_delivery_valid_from
        )


# ============================================================================
# TYPE 14/89: EVENT KEY EXCHANGE
# ============================================================================

class ECH0020EventKeyExchange(BaseModel):
    """Key exchange event for synchronizing person identifiers.

    Used for exchanging encryption keys or synchronizing person identifiers
    between municipalities and federal systems.

    XSD: eventKeyExchange (eCH-0020-3-0.xsd lines 204-209)
    PDF: Unknown section (key exchange event)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - keyExchangePerson: Person identification(s) for key exchange (1-n, required)
    - extension: Extension element (optional, not implemented)
    """

    key_exchange_person: List[ECH0044PersonIdentification] = Field(
        ...,
        alias='keyExchangePerson',
        min_length=1,
        description='Person identification(s) for key exchange (at least 1 required)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventKeyExchange'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_044 = NS.ECH0044_V4

        # keyExchangePerson (1-n, required)
        for person in self.key_exchange_person:
            # Create wrapper element

            keyExchangePerson_wrapper = ET.SubElement(elem, f'{{{namespace}}}keyExchangePerson')

            keyExchangePerson_content = person.to_xml(namespace=ns_044)

            for child in keyExchangePerson_content:

                keyExchangePerson_wrapper.append(child)

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventKeyExchange':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3

        # keyExchangePerson (1-n, required)
        person_elems = element.findall(f'{{{ns_020}}}keyExchangePerson')
        if not person_elems:
            raise ValueError("eventKeyExchange requires at least one keyExchangePerson")

        key_exchange_person = [
            ECH0044PersonIdentification.from_xml(elem) for elem in person_elems
        ]

        return cls(key_exchange_person=key_exchange_person)


# ============================================================================
# TYPE 15/89: EVENT DATA REQUEST
# ============================================================================

class ECH0020EventDataRequest(BaseModel):
    """Data request event for querying person information.

    Used to request person data from other municipalities or federal systems.

    XSD: eventDataRequest (eCH-0020-3-0.xsd lines 210-216)
    PDF: Unknown section (data request event)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - dataRequestPerson: Person identification(s) for data request (0-n, optional)
    - municipality: Municipality to request from (optional)
    - dataValidFrom: Date from which data is valid (optional)
    - extension: Extension element (optional, not implemented)
    """

    data_request_person: Optional[List[ECH0044PersonIdentification]] = Field(
        None,
        alias='dataRequestPerson',
        description='Person identification(s) for data request (0-n)'
    )
    municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='municipality',
        description='Municipality to request data from'
    )
    data_valid_from: Optional[date] = Field(
        None,
        alias='dataValidFrom',
        description='Date from which requested data should be valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventDataRequest'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_044 = NS.ECH0044_V4

        # dataRequestPerson (0-n, optional)
        if self.data_request_person:
            for person in self.data_request_person:
                # Create wrapper element

                dataRequestPerson_wrapper = ET.SubElement(elem, f'{{{namespace}}}dataRequestPerson')

                dataRequestPerson_content = person.to_xml(namespace=ns_044)

                for child in dataRequestPerson_content:

                    dataRequestPerson_wrapper.append(child)

        # municipality (optional)
        if self.municipality:
            # Create wrapper element in parent namespace
            municipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}municipality')
            municipality_content = self.municipality.to_xml(namespace=ns_007)
            for child in municipality_content:
                municipality_wrapper.append(child)

        # dataValidFrom (optional)
        if self.data_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}dataValidFrom')
            valid_elem.text = self.data_valid_from.isoformat()

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventDataRequest':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3

        # dataRequestPerson (0-n, optional)
        data_request_person = None
        person_elems = element.findall(f'{{{ns_020}}}dataRequestPerson')
        if person_elems:
            data_request_person = [
                ECH0044PersonIdentification.from_xml(elem) for elem in person_elems
            ]

        # municipality (optional)
        municipality = None
        mun_elem = element.find(f'{{{ns_020}}}municipality')
        if mun_elem is not None:
            municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

        # dataValidFrom (optional)
        data_valid_from = None
        valid_elem = element.find(f'{{{ns_020}}}dataValidFrom')
        if valid_elem is not None and valid_elem.text:
            data_valid_from = date.fromisoformat(valid_elem.text)

        return cls(
            data_request_person=data_request_person,
            municipality=municipality,
            data_valid_from=data_valid_from
        )


