"""eCH-0010 Mail Address Data v5.1.

Standard: eCH-0010 v5.1 (Mail addresses)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides address structures for Swiss and foreign addresses,
supporting both person and organisation addresses.

ARCHITECTURE: Declarative ECHModel (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/address_mapper.py
"""

from enum import Enum
from typing import Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field


class MrMrs(str, Enum):
    """Salutation codes per eCH-0010 mrMrsType.

    NOTE: Value assignment is OPPOSITE of eCH-0044 Sex enum.
    eCH-0010: 1=Frau, 2=Herr. eCH-0044: 1=male, 2=female.
    """
    FEMALE = "1"   # Frau (Mrs/Woman)
    MALE = "2"     # Herr (Mr/Man)
    MISS = "3"     # Fräulein (Miss) — deprecated per RFC 2019-43


class ECH0010PersonMailAddressInfo(ECHModel):
    """eCH-0010 Person information in mail address.

    Represents a person's name and optional salutation/title
    in a mail address context (simpler than full person data).

    XML Schema: eCH-0010 personMailAddressInfoType
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'person'

    mr_mrs: Optional[MrMrs] = xml_field('mrMrs', default=None)
    title: Optional[str] = xml_field('title', default=None, max_length=50)
    first_name: Optional[str] = xml_field('firstName', default=None, max_length=30)
    last_name: str = xml_field('lastName', max_length=30)


class ECH0010OrganisationMailAddressInfo(ECHModel):
    """eCH-0010 Organisation information in mail address.

    Represents an organisation with optional contact person details.

    XML Schema: eCH-0010 organisationMailAddressInfoType
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'organisation'

    organisation_name: str = xml_field('organisationName', max_length=60)
    organisation_name_add_on1: Optional[str] = xml_field(
        'organisationNameAddOn1', default=None, max_length=60
    )
    organisation_name_add_on2: Optional[str] = xml_field(
        'organisationNameAddOn2', default=None, max_length=60
    )
    mr_mrs: Optional[MrMrs] = xml_field('mrMrs', default=None)
    title: Optional[str] = xml_field('title', default=None, max_length=50)
    first_name: Optional[str] = xml_field('firstName', default=None, max_length=30)
    last_name: Optional[str] = xml_field('lastName', default=None, max_length=30)


class ECH0010AddressInformation(ECHModel):
    """eCH-0010 Address information.

    Represents Swiss or foreign address with flexible structure.
    Supports both structured (street/number) and free-form (addressLine) formats.

    XML Schema: eCH-0010 addressInformationType
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'addressInformation'

    # Free-form address lines (optional)
    address_line1: Optional[str] = xml_field('addressLine1', default=None, max_length=60)
    address_line2: Optional[str] = xml_field('addressLine2', default=None, max_length=60)

    # Structured street address (optional sequence)
    street: Optional[str] = xml_field('street', default=None, max_length=60)
    house_number: Optional[str] = xml_field('houseNumber', default=None, max_length=12)
    dwelling_number: Optional[str] = xml_field('dwellingNumber', default=None, max_length=10)

    # PO Box (optional sequence)
    post_office_box_number: Optional[int] = xml_field(
        'postOfficeBoxNumber', default=None, le=99999999
    )
    post_office_box_text: Optional[str] = xml_field(
        'postOfficeBoxText', default=None, max_length=15
    )

    # Town/locality
    locality: Optional[str] = xml_field('locality', default=None, max_length=40)
    town: str = xml_field('town', max_length=40)

    # Postal code (choice: Swiss OR foreign)
    swiss_zip_code: Optional[int] = xml_field(
        'swissZipCode', default=None, ge=1000, le=9999
    )
    swiss_zip_code_add_on: Optional[str] = xml_field(
        'swissZipCodeAddOn', default=None, max_length=2
    )
    swiss_zip_code_id: Optional[int] = xml_field('swissZipCodeId', default=None)
    foreign_zip_code: Optional[str] = xml_field(
        'foreignZipCode', default=None, max_length=15
    )

    # Country (required)
    country: str = xml_field('country', min_length=1, max_length=2)

    @field_validator('country')
    @classmethod
    def validate_country_uppercase(cls, v: str) -> str:
        """Convert country code to uppercase."""
        return v.upper()

    @model_validator(mode='after')
    def validate_zip_code_exclusivity(self) -> Self:
        """Validate zip code choice constraints.

        Per eCH-0010 XSD v5.1: xs:choice between swissZipCode sequence and
        foreignZipCode (minOccurs=0). Both branches are mutually exclusive,
        but the foreign branch allows absent element (no zip code at all).

        Per PDF §2.6: foreignZipCode is "(optional)" within the choice.
        """
        has_swiss = self.swiss_zip_code is not None
        has_foreign = self.foreign_zip_code is not None

        if has_swiss and has_foreign:
            raise ValueError("Cannot have both swiss_zip_code and foreign_zip_code")

        # swissZipCodeAddOn and swissZipCodeId are part of the Swiss sequence
        # where swissZipCode is required — they cannot exist without it
        if not has_swiss:
            if self.swiss_zip_code_add_on is not None:
                raise ValueError(
                    "swiss_zip_code_add_on requires swiss_zip_code "
                    "(part of swissZipCode sequence)"
                )
            if self.swiss_zip_code_id is not None:
                raise ValueError(
                    "swiss_zip_code_id requires swiss_zip_code "
                    "(part of swissZipCode sequence)"
                )

        return self

    @model_validator(mode='after')
    def validate_po_box_sequence(self) -> Self:
        """Validate PO Box sequence: if number present, text must also be present.

        Per eCH-0010 XSD: postOfficeBoxText is required if in the sequence.
        """
        if self.post_office_box_number is not None and not self.post_office_box_text:
            raise ValueError("post_office_box_text is required when post_office_box_number is present")

        return self


class ECH0010MailAddress(ECHModel):
    """eCH-0010 Mail address (top-level).

    Represents a complete mail address with either person or organisation
    recipient information plus address details.

    XML Schema: eCH-0010 mailAddressType
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'mailAddress'

    person: Optional[ECH0010PersonMailAddressInfo] = xml_field('person', default=None)
    organisation: Optional[ECH0010OrganisationMailAddressInfo] = xml_field(
        'organisation', default=None
    )
    address_information: ECH0010AddressInformation = xml_field('addressInformation')

    @model_validator(mode='after')
    def validate_person_or_organisation(self) -> Self:
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


class ECH0010PersonMailAddress(ECHModel):
    """eCH-0010 Person-specific mail address.

    A mail address with required person information (no organisation option).
    Unlike mailAddressType which has a choice, this type always has a person.

    XML Schema: eCH-0010 personMailAddressType (XSD lines 18-23)
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'personMailAddress'

    person: ECH0010PersonMailAddressInfo = xml_field('person')
    address_information: ECH0010AddressInformation = xml_field('addressInformation')


class ECH0010OrganisationMailAddress(ECHModel):
    """eCH-0010 Organisation-specific mail address.

    A mail address with required organisation information (no person option).
    Unlike mailAddressType which has a choice, this type always has an organisation.

    XML Schema: eCH-0010 organisationMailAddressType (XSD lines 32-37)
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'organisationMailAddress'

    organisation: ECH0010OrganisationMailAddressInfo = xml_field('organisation')
    address_information: ECH0010AddressInformation = xml_field('addressInformation')


class ECH0010SwissAddressInformation(ECHModel):
    """eCH-0010 Swiss-only address information.

    Similar to addressInformationType but enforces Swiss addresses:
    - No PO Box fields (postOfficeBoxNumber, postOfficeBoxText)
    - Only swissZipCode (no foreignZipCode option)
    - swissZipCode is REQUIRED (not optional)

    XML Schema: eCH-0010 swissAddressInformationType (XSD lines 75-97)
    """

    __xml_ns__ = NS.ECH0010_V5
    __xml_element__ = 'address'

    # Free-form address lines (optional)
    address_line1: Optional[str] = xml_field('addressLine1', default=None, max_length=60)
    address_line2: Optional[str] = xml_field('addressLine2', default=None, max_length=60)

    # Structured address (street sequence - optional as a group)
    street: Optional[str] = xml_field('street', default=None, max_length=60)
    house_number: Optional[str] = xml_field('houseNumber', default=None, max_length=12)
    dwelling_number: Optional[str] = xml_field('dwellingNumber', default=None, max_length=10)

    # Locality (optional)
    locality: Optional[str] = xml_field('locality', default=None, max_length=40)

    # Town (required)
    town: str = xml_field('town', max_length=40)

    # Swiss ZIP code (REQUIRED - unlike addressInformationType)
    swiss_zip_code: int = xml_field('swissZipCode', ge=1000, le=9999)
    swiss_zip_code_add_on: Optional[str] = xml_field(
        'swissZipCodeAddOn', default=None, max_length=2
    )
    swiss_zip_code_id: Optional[int] = xml_field('swissZipCodeId', default=None)

    # Country (required, restricted to countryIdIso2Type)
    country: str = xml_field('country', min_length=1, max_length=2)

    @field_validator('country')
    @classmethod
    def validate_country_uppercase(cls, v: str) -> str:
        """Ensure country code is uppercase."""
        return v.upper()
