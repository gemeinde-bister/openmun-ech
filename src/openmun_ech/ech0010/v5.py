"""eCH-0010 Mail Address Data v5.1.

Standard: eCH-0010 v5.1 (Mail addresses)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides address structures for Swiss and foreign addresses,
supporting both person and organisation addresses.

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/address_mapper.py
"""

import xml.etree.ElementTree as ET
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ECH0010PersonMailAddressInfo(BaseModel):
    """eCH-0010 Person information in mail address.

    Represents a person's name and optional salutation/title
    in a mail address context (simpler than full person data).

    XML Schema: eCH-0010 personMailAddressInfoType
    """

    mr_mrs: Optional[Literal["1", "2", "3"]] = Field(
        None,
        description="Salutation: 1=Frau (Mrs/Woman), 2=Herr (Mr/Man), 3=deprecated (historically Fräulein/Miss, RFC 2019-43)"
    )
    title: Optional[str] = Field(
        None,
        max_length=50,
        description="Academic/professional title (e.g., 'Dr.', 'Prof.')"
    )
    first_name: Optional[str] = Field(
        None,
        max_length=30,
        description="First name"
    )
    last_name: str = Field(
        ...,
        max_length=30,
        description="Last name (required)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5',
               element_name: str = 'person') -> ET.Element:
        """Export to eCH-0010 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # MrMrs (optional)
        if self.mr_mrs:
            mr_mrs_elem = ET.SubElement(elem, f'{{{namespace}}}mrMrs')
            mr_mrs_elem.text = self.mr_mrs

        # Title (optional)
        if self.title:
            title_elem = ET.SubElement(elem, f'{{{namespace}}}title')
            title_elem.text = self.title

        # First name (optional)
        if self.first_name:
            first_name_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
            first_name_elem.text = self.first_name

        # Last name (required)
        last_name_elem = ET.SubElement(elem, f'{{{namespace}}}lastName')
        last_name_elem.text = self.last_name

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5') -> 'ECH0010PersonMailAddressInfo':
        """Import from eCH-0010 XML.

        Args:
            elem: XML element (person container)
            namespace: XML namespace URI

        Returns:
            Parsed person object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0010': namespace}

        # Extract optional fields
        mr_mrs_elem = elem.find('eCH-0010:mrMrs', ns)
        mr_mrs = mr_mrs_elem.text.strip() if mr_mrs_elem is not None and mr_mrs_elem.text else None

        title_elem = elem.find('eCH-0010:title', ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else None

        first_name_elem = elem.find('eCH-0010:firstName', ns)
        first_name = first_name_elem.text.strip() if first_name_elem is not None and first_name_elem.text else None

        # Extract required field
        last_name_elem = elem.find('eCH-0010:lastName', ns)
        if last_name_elem is None or not last_name_elem.text:
            raise ValueError("Missing required field: lastName")

        return cls(
            mr_mrs=mr_mrs,
            title=title,
            first_name=first_name,
            last_name=last_name_elem.text.strip()
        )


class ECH0010OrganisationMailAddressInfo(BaseModel):
    """eCH-0010 Organisation information in mail address.

    Represents an organisation with optional contact person details.

    XML Schema: eCH-0010 organisationMailAddressInfoType
    """

    organisation_name: str = Field(
        ...,
        max_length=60,
        description="Organisation name (required)"
    )
    organisation_name_add_on1: Optional[str] = Field(
        None,
        max_length=60,
        description="Organisation name addition 1 (e.g., department)"
    )
    organisation_name_add_on2: Optional[str] = Field(
        None,
        max_length=60,
        description="Organisation name addition 2 (e.g., sub-department)"
    )

    # Optional contact person within organisation
    mr_mrs: Optional[Literal["1", "2", "3"]] = Field(
        None,
        description="Contact person salutation: 1=Frau (Mrs/Woman), 2=Herr (Mr/Man), 3=deprecated (historically Fräulein/Miss, RFC 2019-43)"
    )
    title: Optional[str] = Field(
        None,
        max_length=50,
        description="Contact person title"
    )
    first_name: Optional[str] = Field(
        None,
        max_length=30,
        description="Contact person first name"
    )
    last_name: Optional[str] = Field(
        None,
        max_length=30,
        description="Contact person last name"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5',
               element_name: str = 'organisation') -> ET.Element:
        """Export to eCH-0010 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Organisation name (required)
        org_name_elem = ET.SubElement(elem, f'{{{namespace}}}organisationName')
        org_name_elem.text = self.organisation_name

        # Organisation name add-ons (optional)
        if self.organisation_name_add_on1:
            addon1_elem = ET.SubElement(elem, f'{{{namespace}}}organisationNameAddOn1')
            addon1_elem.text = self.organisation_name_add_on1

        if self.organisation_name_add_on2:
            addon2_elem = ET.SubElement(elem, f'{{{namespace}}}organisationNameAddOn2')
            addon2_elem.text = self.organisation_name_add_on2

        # Contact person details (all optional)
        if self.mr_mrs:
            mr_mrs_elem = ET.SubElement(elem, f'{{{namespace}}}mrMrs')
            mr_mrs_elem.text = self.mr_mrs

        if self.title:
            title_elem = ET.SubElement(elem, f'{{{namespace}}}title')
            title_elem.text = self.title

        if self.first_name:
            first_name_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
            first_name_elem.text = self.first_name

        if self.last_name:
            last_name_elem = ET.SubElement(elem, f'{{{namespace}}}lastName')
            last_name_elem.text = self.last_name

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5') -> 'ECH0010OrganisationMailAddressInfo':
        """Import from eCH-0010 XML.

        Args:
            elem: XML element (organisation container)
            namespace: XML namespace URI

        Returns:
            Parsed organisation object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0010': namespace}

        # Extract required field
        org_name_elem = elem.find('eCH-0010:organisationName', ns)
        if org_name_elem is None or not org_name_elem.text:
            raise ValueError("Missing required field: organisationName")

        # Extract optional fields
        addon1_elem = elem.find('eCH-0010:organisationNameAddOn1', ns)
        addon1 = addon1_elem.text.strip() if addon1_elem is not None and addon1_elem.text else None

        addon2_elem = elem.find('eCH-0010:organisationNameAddOn2', ns)
        addon2 = addon2_elem.text.strip() if addon2_elem is not None and addon2_elem.text else None

        mr_mrs_elem = elem.find('eCH-0010:mrMrs', ns)
        mr_mrs = mr_mrs_elem.text.strip() if mr_mrs_elem is not None and mr_mrs_elem.text else None

        title_elem = elem.find('eCH-0010:title', ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else None

        first_name_elem = elem.find('eCH-0010:firstName', ns)
        first_name = first_name_elem.text.strip() if first_name_elem is not None and first_name_elem.text else None

        last_name_elem = elem.find('eCH-0010:lastName', ns)
        last_name = last_name_elem.text.strip() if last_name_elem is not None and last_name_elem.text else None

        return cls(
            organisation_name=org_name_elem.text.strip(),
            organisation_name_add_on1=addon1,
            organisation_name_add_on2=addon2,
            mr_mrs=mr_mrs,
            title=title,
            first_name=first_name,
            last_name=last_name
        )


class ECH0010AddressInformation(BaseModel):
    """eCH-0010 Address information.

    Represents Swiss or foreign address with flexible structure.
    Supports both structured (street/number) and free-form (addressLine) formats.

    XML Schema: eCH-0010 addressInformationType
    """

    # Free-form address lines (optional)
    address_line1: Optional[str] = Field(
        None,
        max_length=60,
        description="Free-form address line 1"
    )
    address_line2: Optional[str] = Field(
        None,
        max_length=60,
        description="Free-form address line 2"
    )

    # Structured street address (optional sequence)
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

    # PO Box (optional sequence)
    post_office_box_number: Optional[int] = Field(
        None,
        le=99999999,
        description="PO Box number"
    )
    post_office_box_text: Optional[str] = Field(
        None,
        max_length=15,
        description="PO Box text (required if box number present)"
    )

    # Town/locality
    locality: Optional[str] = Field(
        None,
        max_length=40,
        description="Locality (e.g., district within town)"
    )
    town: str = Field(
        ...,
        max_length=40,
        description="Town/city name (required)"
    )

    # Postal code (choice: Swiss OR foreign)
    swiss_zip_code: Optional[int] = Field(
        None,
        ge=1000,
        le=9999,
        description="Swiss ZIP code (1000-9999)"
    )
    swiss_zip_code_add_on: Optional[str] = Field(
        None,
        max_length=2,
        description="Swiss ZIP code addition"
    )
    swiss_zip_code_id: Optional[int] = Field(
        None,
        description="Swiss ZIP code ID (ONRP number)"
    )
    foreign_zip_code: Optional[str] = Field(
        None,
        max_length=15,
        description="Foreign ZIP/postal code"
    )

    # Country (required)
    country: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Country code (ISO 3166-1 alpha-2, 1-2 chars, e.g., 'CH')"
    )

    @field_validator('country')
    @classmethod
    def validate_country_uppercase(cls, v: str) -> str:
        """Convert country code to uppercase."""
        return v.upper()

    @model_validator(mode='after')
    def validate_zip_code_exclusivity(self) -> 'ECH0010AddressInformation':
        """Validate that either swiss_zip_code OR foreign_zip_code is present, not both.

        Per eCH-0010 XSD: choice between swissZipCode sequence or foreignZipCode.
        """
        has_swiss = self.swiss_zip_code is not None
        has_foreign = self.foreign_zip_code is not None

        if has_swiss and has_foreign:
            raise ValueError("Cannot have both swiss_zip_code and foreign_zip_code")

        if not has_swiss and not has_foreign:
            raise ValueError("Must have either swiss_zip_code or foreign_zip_code")

        return self

    @model_validator(mode='after')
    def validate_po_box_sequence(self) -> 'ECH0010AddressInformation':
        """Validate PO Box sequence: if number present, text must also be present.

        Per eCH-0010 XSD: postOfficeBoxText is required if in the sequence.
        """
        if self.post_office_box_number is not None and not self.post_office_box_text:
            raise ValueError("post_office_box_text is required when post_office_box_number is present")

        return self

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5',
               element_name: str = 'addressInformation',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0010 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements (street, town, etc.)
            element_name: Name of container element (default: 'addressInformation', can be 'mailAddress' in eCH-0011)
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)

        Returns:
            XML Element
        """
        # Use wrapper_namespace for the wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Free-form address lines (optional)
        if self.address_line1:
            line1 = ET.SubElement(elem, f'{{{namespace}}}addressLine1')
            line1.text = self.address_line1

        if self.address_line2:
            line2 = ET.SubElement(elem, f'{{{namespace}}}addressLine2')
            line2.text = self.address_line2

        # Street address sequence (optional)
        if self.street:
            street_elem = ET.SubElement(elem, f'{{{namespace}}}street')
            street_elem.text = self.street

            if self.house_number:
                house_elem = ET.SubElement(elem, f'{{{namespace}}}houseNumber')
                house_elem.text = self.house_number

            if self.dwelling_number:
                dwelling_elem = ET.SubElement(elem, f'{{{namespace}}}dwellingNumber')
                dwelling_elem.text = self.dwelling_number

        # PO Box sequence (optional)
        if self.post_office_box_number is not None or self.post_office_box_text:
            if self.post_office_box_number is not None:
                po_num_elem = ET.SubElement(elem, f'{{{namespace}}}postOfficeBoxNumber')
                po_num_elem.text = str(self.post_office_box_number)

            if self.post_office_box_text:
                po_text_elem = ET.SubElement(elem, f'{{{namespace}}}postOfficeBoxText')
                po_text_elem.text = self.post_office_box_text

        # Locality (optional)
        if self.locality:
            locality_elem = ET.SubElement(elem, f'{{{namespace}}}locality')
            locality_elem.text = self.locality

        # Town (required)
        town_elem = ET.SubElement(elem, f'{{{namespace}}}town')
        town_elem.text = self.town

        # ZIP code (choice: Swiss or foreign)
        if self.swiss_zip_code is not None:
            zip_elem = ET.SubElement(elem, f'{{{namespace}}}swissZipCode')
            zip_elem.text = str(self.swiss_zip_code)

            if self.swiss_zip_code_add_on:
                addon_elem = ET.SubElement(elem, f'{{{namespace}}}swissZipCodeAddOn')
                addon_elem.text = self.swiss_zip_code_add_on

            if self.swiss_zip_code_id is not None:
                id_elem = ET.SubElement(elem, f'{{{namespace}}}swissZipCodeId')
                id_elem.text = str(self.swiss_zip_code_id)
        else:
            # Foreign ZIP code
            foreign_zip_elem = ET.SubElement(elem, f'{{{namespace}}}foreignZipCode')
            foreign_zip_elem.text = self.foreign_zip_code or ""

        # Country (required)
        country_elem = ET.SubElement(elem, f'{{{namespace}}}country')
        country_elem.text = self.country

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5') -> 'ECH0010AddressInformation':
        """Import from eCH-0010 XML.

        Args:
            elem: XML element (addressInformation container)
            namespace: XML namespace URI

        Returns:
            Parsed address object

        Raises:
            ValueError: If required fields missing or validation fails
        """
        ns = {'eCH-0010': namespace}

        # Extract optional fields
        line1_elem = elem.find('eCH-0010:addressLine1', ns)
        line1 = line1_elem.text.strip() if line1_elem is not None and line1_elem.text else None

        line2_elem = elem.find('eCH-0010:addressLine2', ns)
        line2 = line2_elem.text.strip() if line2_elem is not None and line2_elem.text else None

        street_elem = elem.find('eCH-0010:street', ns)
        street = street_elem.text.strip() if street_elem is not None and street_elem.text else None

        house_elem = elem.find('eCH-0010:houseNumber', ns)
        house_number = house_elem.text.strip() if house_elem is not None and house_elem.text else None

        dwelling_elem = elem.find('eCH-0010:dwellingNumber', ns)
        dwelling_number = dwelling_elem.text.strip() if dwelling_elem is not None and dwelling_elem.text else None

        po_num_elem = elem.find('eCH-0010:postOfficeBoxNumber', ns)
        po_number = int(po_num_elem.text) if po_num_elem is not None and po_num_elem.text else None

        po_text_elem = elem.find('eCH-0010:postOfficeBoxText', ns)
        po_text = po_text_elem.text.strip() if po_text_elem is not None and po_text_elem.text else None

        locality_elem = elem.find('eCH-0010:locality', ns)
        locality = locality_elem.text.strip() if locality_elem is not None and locality_elem.text else None

        # Extract required fields
        town_elem = elem.find('eCH-0010:town', ns)
        if town_elem is None or not town_elem.text:
            raise ValueError("Missing required field: town")

        # Extract ZIP code (choice: Swiss or foreign)
        swiss_zip_elem = elem.find('eCH-0010:swissZipCode', ns)
        swiss_zip = int(swiss_zip_elem.text) if swiss_zip_elem is not None and swiss_zip_elem.text else None

        swiss_addon_elem = elem.find('eCH-0010:swissZipCodeAddOn', ns)
        swiss_addon = swiss_addon_elem.text.strip() if swiss_addon_elem is not None and swiss_addon_elem.text else None

        swiss_id_elem = elem.find('eCH-0010:swissZipCodeId', ns)
        swiss_id = int(swiss_id_elem.text) if swiss_id_elem is not None and swiss_id_elem.text else None

        foreign_zip_elem = elem.find('eCH-0010:foreignZipCode', ns)
        foreign_zip = foreign_zip_elem.text.strip() if foreign_zip_elem is not None and foreign_zip_elem.text else None

        # Extract country (required)
        country_elem = elem.find('eCH-0010:country', ns)
        if country_elem is None or not country_elem.text:
            raise ValueError("Missing required field: country")

        return cls(
            address_line1=line1,
            address_line2=line2,
            street=street,
            house_number=house_number,
            dwelling_number=dwelling_number,
            post_office_box_number=po_number,
            post_office_box_text=po_text,
            locality=locality,
            town=town_elem.text.strip(),
            swiss_zip_code=swiss_zip,
            swiss_zip_code_add_on=swiss_addon,
            swiss_zip_code_id=swiss_id,
            foreign_zip_code=foreign_zip,
            country=country_elem.text.strip()
        )


class ECH0010MailAddress(BaseModel):
    """eCH-0010 Mail address (top-level).

    Represents a complete mail address with either person or organisation
    recipient information plus address details.

    XML Schema: eCH-0010 mailAddressType
    """

    person: Optional[ECH0010PersonMailAddressInfo] = Field(
        None,
        description="Person recipient (mutually exclusive with organisation)"
    )
    organisation: Optional[ECH0010OrganisationMailAddressInfo] = Field(
        None,
        description="Organisation recipient (mutually exclusive with person)"
    )
    address_information: ECH0010AddressInformation = Field(
        ...,
        description="Address details (required)"
    )

    @model_validator(mode='after')
    def validate_person_or_organisation(self) -> 'ECH0010MailAddress':
        """Validate that exactly one of person or organisation is set.

        Per eCH-0010 XSD: choice between person and organisation.
        """
        has_person = self.person is not None
        has_org = self.organisation is not None

        if has_person and has_org:
            raise ValueError("Cannot have both person and organisation")

        if not has_person and not has_org:
            raise ValueError("Must have either person or organisation")

        return self

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5',
               element_name: str = 'mailAddress',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0010 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements (person, addressInformation)
            element_name: Element name (default: 'mailAddress', can be overridden for eCH-0011 'contactAddress')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)

        Returns:
            XML Element
        """
        # Use wrapper_namespace for the wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Person or organisation (choice) - always in eCH-0010 namespace
        if self.person:
            self.person.to_xml(elem, namespace, 'person')
        else:
            self.organisation.to_xml(elem, namespace, 'organisation')

        # Address information (required) - always in eCH-0010 namespace
        self.address_information.to_xml(elem, namespace, 'addressInformation')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0010/5') -> 'ECH0010MailAddress':
        """Import from eCH-0010 XML.

        Args:
            elem: XML element (mailAddress container)
            namespace: XML namespace URI

        Returns:
            Parsed mail address object

        Raises:
            ValueError: If required fields missing or validation fails
        """
        ns = {'eCH-0010': namespace}

        # Extract person or organisation (choice)
        person_elem = elem.find('eCH-0010:person', ns)
        person = ECH0010PersonMailAddressInfo.from_xml(person_elem, namespace) if person_elem is not None else None

        org_elem = elem.find('eCH-0010:organisation', ns)
        organisation = ECH0010OrganisationMailAddressInfo.from_xml(org_elem, namespace) if org_elem is not None else None

        # Extract address information (required)
        addr_elem = elem.find('eCH-0010:addressInformation', ns)
        if addr_elem is None:
            raise ValueError("Missing required element: addressInformation")
        address_information = ECH0010AddressInformation.from_xml(addr_elem, namespace)

        return cls(
            person=person,
            organisation=organisation,
            address_information=address_information
        )


class ECH0010PersonMailAddress(BaseModel):
    """eCH-0010 Person-specific mail address.

    A mail address with required person information (no organisation option).
    Unlike mailAddressType which has a choice, this type always has a person.

    XML Schema: eCH-0010 personMailAddressType (XSD lines 18-23)
    """

    person: ECH0010PersonMailAddressInfo = Field(
        ...,
        description="Person information (required)"
    )
    address_information: ECH0010AddressInformation = Field(
        ...,
        description="Address information (required)"
    )

    def to_xml(self, parent: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> None:
        """Serialize to XML element."""
        ns_prefix = f"{{{namespace}}}"

        # Add person
        person_elem = ET.SubElement(parent, f"{ns_prefix}person")
        self.person.to_xml(person_elem, namespace)

        # Add address information
        addr_elem = ET.SubElement(parent, f"{ns_prefix}addressInformation")
        self.address_information.to_xml(addr_elem, namespace)

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> "ECH0010PersonMailAddress":
        """Deserialize from XML element."""
        ns = {'eCH-0010': namespace}

        # Extract person (required)
        person_elem = elem.find('eCH-0010:person', ns)
        if person_elem is None:
            raise ValueError("Missing required element: person")
        person = ECH0010PersonMailAddressInfo.from_xml(person_elem, namespace)

        # Extract address information (required)
        addr_elem = elem.find('eCH-0010:addressInformation', ns)
        if addr_elem is None:
            raise ValueError("Missing required element: addressInformation")
        address_information = ECH0010AddressInformation.from_xml(addr_elem, namespace)

        return cls(
            person=person,
            address_information=address_information
        )


class ECH0010OrganisationMailAddress(BaseModel):
    """eCH-0010 Organisation-specific mail address.

    A mail address with required organisation information (no person option).
    Unlike mailAddressType which has a choice, this type always has an organisation.

    XML Schema: eCH-0010 organisationMailAddressType (XSD lines 32-37)
    """

    organisation: ECH0010OrganisationMailAddressInfo = Field(
        ...,
        description="Organisation information (required)"
    )
    address_information: ECH0010AddressInformation = Field(
        ...,
        description="Address information (required)"
    )

    def to_xml(self, parent: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> None:
        """Serialize to XML element."""
        ns_prefix = f"{{{namespace}}}"

        # Add organisation
        org_elem = ET.SubElement(parent, f"{ns_prefix}organisation")
        self.organisation.to_xml(org_elem, namespace)

        # Add address information
        addr_elem = ET.SubElement(parent, f"{ns_prefix}addressInformation")
        self.address_information.to_xml(addr_elem, namespace)

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> "ECH0010OrganisationMailAddress":
        """Deserialize from XML element."""
        ns = {'eCH-0010': namespace}

        # Extract organisation (required)
        org_elem = elem.find('eCH-0010:organisation', ns)
        if org_elem is None:
            raise ValueError("Missing required element: organisation")
        organisation = ECH0010OrganisationMailAddressInfo.from_xml(org_elem, namespace)

        # Extract address information (required)
        addr_elem = elem.find('eCH-0010:addressInformation', ns)
        if addr_elem is None:
            raise ValueError("Missing required element: addressInformation")
        address_information = ECH0010AddressInformation.from_xml(addr_elem, namespace)

        return cls(
            organisation=organisation,
            address_information=address_information
        )


class ECH0010SwissAddressInformation(BaseModel):
    """eCH-0010 Swiss-only address information.

    Similar to addressInformationType but enforces Swiss addresses:
    - No PO Box fields (postOfficeBoxNumber, postOfficeBoxText)
    - Only swissZipCode (no foreignZipCode option)
    - swissZipCode is REQUIRED (not optional)

    XML Schema: eCH-0010 swissAddressInformationType (XSD lines 75-97)
    """

    # Free-form address lines (optional)
    address_line1: Optional[str] = Field(
        None,
        max_length=60,
        description="First address line (optional, free-form)"
    )
    address_line2: Optional[str] = Field(
        None,
        max_length=60,
        description="Second address line (optional, free-form)"
    )

    # Structured address (street sequence - optional as a group)
    street: Optional[str] = Field(
        None,
        max_length=60,
        description="Street name (required if street sequence used)"
    )
    house_number: Optional[str] = Field(
        None,
        max_length=12,
        description="House number (optional within street sequence)"
    )
    dwelling_number: Optional[str] = Field(
        None,
        max_length=10,
        description="Dwelling/apartment number (optional within street sequence)"
    )

    # Locality (optional)
    locality: Optional[str] = Field(
        None,
        max_length=40,
        description="Locality/district name (optional)"
    )

    # Town (required)
    town: str = Field(
        ...,
        max_length=40,
        description="Town/city name (required)"
    )

    # Swiss ZIP code (REQUIRED - unlike addressInformationType)
    swiss_zip_code: int = Field(
        ...,
        ge=1000,
        le=9999,
        description="Swiss postal code (4 digits, REQUIRED)"
    )
    swiss_zip_code_add_on: Optional[str] = Field(
        None,
        max_length=2,
        description="Swiss postal code add-on (e.g., '01')"
    )
    swiss_zip_code_id: Optional[int] = Field(
        None,
        description="Official Swiss postal code ID"
    )

    # Country (required, restricted to countryIdIso2Type)
    country: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Country code (ISO 3166-1 alpha-2, 1-2 chars, typically 'CH')"
    )

    @field_validator('country')
    @classmethod
    def validate_country_uppercase(cls, v: str) -> str:
        """Ensure country code is uppercase."""
        return v.upper()

    def to_xml(self, parent: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> None:
        """Serialize to XML element."""
        ns_prefix = f"{{{namespace}}}"

        # Add optional address lines
        if self.address_line1:
            ET.SubElement(parent, f"{ns_prefix}addressLine1").text = self.address_line1
        if self.address_line2:
            ET.SubElement(parent, f"{ns_prefix}addressLine2").text = self.address_line2

        # Add street sequence (optional as a group)
        if self.street:
            ET.SubElement(parent, f"{ns_prefix}street").text = self.street
            if self.house_number:
                ET.SubElement(parent, f"{ns_prefix}houseNumber").text = self.house_number
            if self.dwelling_number:
                ET.SubElement(parent, f"{ns_prefix}dwellingNumber").text = self.dwelling_number

        # Add locality (optional)
        if self.locality:
            ET.SubElement(parent, f"{ns_prefix}locality").text = self.locality

        # Add town (required)
        ET.SubElement(parent, f"{ns_prefix}town").text = self.town

        # Add Swiss ZIP code (REQUIRED)
        ET.SubElement(parent, f"{ns_prefix}swissZipCode").text = str(self.swiss_zip_code)
        if self.swiss_zip_code_add_on:
            ET.SubElement(parent, f"{ns_prefix}swissZipCodeAddOn").text = self.swiss_zip_code_add_on
        if self.swiss_zip_code_id is not None:
            ET.SubElement(parent, f"{ns_prefix}swissZipCodeId").text = str(self.swiss_zip_code_id)

        # Add country (required)
        ET.SubElement(parent, f"{ns_prefix}country").text = self.country

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str = "http://www.ech.ch/xmlns/eCH-0010/5") -> "ECH0010SwissAddressInformation":
        """Deserialize from XML element."""
        ns = {'eCH-0010': namespace}

        # Extract optional address lines
        address_line1 = elem.findtext('eCH-0010:addressLine1', None, ns)
        address_line2 = elem.findtext('eCH-0010:addressLine2', None, ns)

        # Extract street sequence (optional)
        street = elem.findtext('eCH-0010:street', None, ns)
        house_number = elem.findtext('eCH-0010:houseNumber', None, ns)
        dwelling_number = elem.findtext('eCH-0010:dwellingNumber', None, ns)

        # Extract locality (optional)
        locality = elem.findtext('eCH-0010:locality', None, ns)

        # Extract town (required)
        town = elem.findtext('eCH-0010:town', None, ns)
        if town is None:
            raise ValueError("Missing required element: town")

        # Extract Swiss ZIP code (REQUIRED)
        swiss_zip_code_text = elem.findtext('eCH-0010:swissZipCode', None, ns)
        if swiss_zip_code_text is None:
            raise ValueError("Missing required element: swissZipCode")
        swiss_zip_code = int(swiss_zip_code_text)

        swiss_zip_code_add_on = elem.findtext('eCH-0010:swissZipCodeAddOn', None, ns)

        swiss_zip_code_id_text = elem.findtext('eCH-0010:swissZipCodeId', None, ns)
        swiss_zip_code_id = int(swiss_zip_code_id_text) if swiss_zip_code_id_text else None

        # Extract country (required)
        country = elem.findtext('eCH-0010:country', None, ns)
        if country is None:
            raise ValueError("Missing required element: country")

        return cls(
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
            country=country
        )
