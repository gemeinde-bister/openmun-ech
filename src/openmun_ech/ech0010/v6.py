"""eCH-0010 Mail Address Data v6.0.

Standard: eCH-0010 v6.0 (Mail addresses)
Version stability: Used by eCH-0129 v6.0 (Objektwesen)

Key change from v5: The 'country' field in addressInformationType and
swissAddressInformationType changed from countryIdIso2Type (simple 2-letter string)
to countryType (complex: countryId + countryIdISO2 + countryNameShort).
Also: countryIdISO2Type minLength changed from 1 to 2.

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO external data lookups
"""

from typing import Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0010.v5 import MrMrs  # Enum unchanged between versions


class ECH0010v6Country(ECHModel):
    """eCH-0010 v6 Country (countryType).

    New in v6 — replaces the simple countryIdIso2Type string.

    XSD: eCH-0010-6-0.xsd countryType
    Fields: countryId (optional int 1000-9999), countryIdISO2 (optional 2-char),
            countryNameShort (required, max 50 chars).
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'country'

    country_id: Optional[int] = xml_field(
        'countryId', default=None, ge=1000, le=9999,
    )
    country_id_iso2: Optional[str] = xml_field(
        'countryIdISO2', default=None, min_length=2, max_length=2,
    )
    country_name_short: str = xml_field(
        'countryNameShort', max_length=50,
    )

    @field_validator('country_id_iso2')
    @classmethod
    def validate_iso2_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure ISO2 code is uppercase."""
        if v is None:
            return None
        return v.upper()


class ECH0010v6PersonMailAddressInfo(ECHModel):
    """eCH-0010 v6 Person information in mail address.

    XSD: eCH-0010-6-0.xsd personMailAddressInfoType
    Identical to v5 except namespace.
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'person'

    mr_mrs: Optional[MrMrs] = xml_field('mrMrs', default=None)
    title: Optional[str] = xml_field('title', default=None, max_length=50)
    first_name: Optional[str] = xml_field('firstName', default=None, max_length=30)
    last_name: str = xml_field('lastName', max_length=30)


class ECH0010v6OrganisationMailAddressInfo(ECHModel):
    """eCH-0010 v6 Organisation information in mail address.

    XSD: eCH-0010-6-0.xsd organisationMailAddressInfoType
    Identical to v5 except namespace.
    """

    __xml_ns__ = NS.ECH0010_V6
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


class ECH0010v6AddressInformation(ECHModel):
    """eCH-0010 v6 Address information (addressInformationType).

    XSD: eCH-0010-6-0.xsd addressInformationType
    Key change from v5: 'country' is now countryType (complex) instead of
    countryIdIso2Type (simple string).
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'addressInformation'

    address_line1: Optional[str] = xml_field('addressLine1', default=None, max_length=60)
    address_line2: Optional[str] = xml_field('addressLine2', default=None, max_length=60)

    street: Optional[str] = xml_field('street', default=None, max_length=60)
    house_number: Optional[str] = xml_field('houseNumber', default=None, max_length=12)
    dwelling_number: Optional[str] = xml_field('dwellingNumber', default=None, max_length=10)

    post_office_box_number: Optional[int] = xml_field(
        'postOfficeBoxNumber', default=None, le=99999999
    )
    post_office_box_text: Optional[str] = xml_field(
        'postOfficeBoxText', default=None, max_length=15
    )

    locality: Optional[str] = xml_field('locality', default=None, max_length=40)
    town: str = xml_field('town', max_length=40)

    # xs:choice: Swiss zip code sequence OR foreign zip code
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

    # v6 change: country is now countryType (complex), not countryIdIso2Type (string)
    country: ECH0010v6Country = xml_field('country')

    @model_validator(mode='after')
    def validate_zip_code_exclusivity(self) -> Self:
        """Validate zip code choice constraints.

        Per eCH-0010 XSD: xs:choice between swissZipCode sequence and foreignZipCode.
        """
        has_swiss = self.swiss_zip_code is not None
        has_foreign = self.foreign_zip_code is not None

        if has_swiss and has_foreign:
            raise ValueError("Cannot have both swiss_zip_code and foreign_zip_code")

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
        """Validate PO Box sequence: if number present, text must also be present."""
        if self.post_office_box_number is not None and not self.post_office_box_text:
            raise ValueError(
                "post_office_box_text is required when post_office_box_number is present"
            )
        return self


class ECH0010v6MailAddress(ECHModel):
    """eCH-0010 v6 Mail address (top-level, mailAddressType).

    XSD: eCH-0010-6-0.xsd mailAddressType
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'mailAddress'

    person: Optional[ECH0010v6PersonMailAddressInfo] = xml_field('person', default=None)
    organisation: Optional[ECH0010v6OrganisationMailAddressInfo] = xml_field(
        'organisation', default=None
    )
    address_information: ECH0010v6AddressInformation = xml_field('addressInformation')

    @model_validator(mode='after')
    def validate_person_or_organisation(self) -> Self:
        """Validate that exactly one of person or organisation is set."""
        has_person = self.person is not None
        has_org = self.organisation is not None

        if has_person and has_org:
            raise ValueError("Cannot have both person and organisation")
        if not has_person and not has_org:
            raise ValueError("Must have either person or organisation")

        return self


class ECH0010v6PersonMailAddress(ECHModel):
    """eCH-0010 v6 Person-specific mail address (personMailAddressType).

    XSD: eCH-0010-6-0.xsd personMailAddressType
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'personMailAddress'

    person: ECH0010v6PersonMailAddressInfo = xml_field('person')
    address_information: ECH0010v6AddressInformation = xml_field('addressInformation')


class ECH0010v6OrganisationMailAddress(ECHModel):
    """eCH-0010 v6 Organisation-specific mail address (organisationMailAddressType).

    XSD: eCH-0010-6-0.xsd organisationMailAddressType
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'organisationMailAddress'

    organisation: ECH0010v6OrganisationMailAddressInfo = xml_field('organisation')
    address_information: ECH0010v6AddressInformation = xml_field('addressInformation')


class ECH0010v6SwissAddressInformation(ECHModel):
    """eCH-0010 v6 Swiss-only address information (swissAddressInformationType).

    XSD: eCH-0010-6-0.xsd swissAddressInformationType
    v6 change: 'country' is now countryType (complex), not countryIdIso2Type (string).
    """

    __xml_ns__ = NS.ECH0010_V6
    __xml_element__ = 'address'

    address_line1: Optional[str] = xml_field('addressLine1', default=None, max_length=60)
    address_line2: Optional[str] = xml_field('addressLine2', default=None, max_length=60)

    street: Optional[str] = xml_field('street', default=None, max_length=60)
    house_number: Optional[str] = xml_field('houseNumber', default=None, max_length=12)
    dwelling_number: Optional[str] = xml_field('dwellingNumber', default=None, max_length=10)

    locality: Optional[str] = xml_field('locality', default=None, max_length=40)
    town: str = xml_field('town', max_length=40)

    swiss_zip_code: int = xml_field('swissZipCode', ge=1000, le=9999)
    swiss_zip_code_add_on: Optional[str] = xml_field(
        'swissZipCodeAddOn', default=None, max_length=2
    )
    swiss_zip_code_id: Optional[int] = xml_field('swissZipCodeId', default=None)

    # v6 change: country is now countryType (complex)
    country: ECH0010v6Country = xml_field('country')
