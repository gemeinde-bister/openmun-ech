"""eCH-0129 v6.0.0 — Person and building authority types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 50-88, 1727-1789)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.22, §4.23)

Types in this module depend on:
- eCH-0129 base_types (ECH0129DateRange, ECH0129Contact)
- eCH-0129 enums (PhoneCategory, EmailCategory)
- eCH-0044 v4 (ECH0044PersonIdentificationLight)
- eCH-0097 v2 (ECH0097OrganisationIdentification)
- eCH-0010 v6 (ECH0010v6AddressInformation)

Anonymous inline identification choice:
  personType.identification, personOnlyType.identification, and
  buildingAuthorityType.contactPerson all share the same anonymous inline
  complexType: xs:choice of eCH-0044:personIdentificationLightType or
  eCH-0097:organisationIdentificationType. A shared helper class
  ECH0129IdentificationChoice handles this structure. Element names
  differ from the named personIdentificationType (§4.23.1.1) which
  uses 'individual'/'organisation' — the anonymous types use
  'personIdentification'/'organisationIdentification'.
"""

from typing import Optional, Self

from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0010.v6 import ECH0010v6AddressInformation
from openmun_ech.ech0044 import ECH0044PersonIdentificationLight
from openmun_ech.ech0097 import ECH0097OrganisationIdentification
from openmun_ech.ech0129.enums import EmailCategory, PhoneCategory
from openmun_ech.ech0129.v6.base_types import ECH0129Contact, ECH0129DateRange


# ---------------------------------------------------------------------------
# phoneType (§4.23.1.4)
# XSD lines 50-58
# ---------------------------------------------------------------------------

class ECH0129Phone(ECHModel):
    """eCH-0129 phone number with optional category.

    XSD: phoneType — xs:sequence.
    PDF: §4.23.1.4 (page 95)

    - xs:choice (minOccurs="0"): phoneCategory enum OR otherPhoneCategory free text
    - phoneNumber: phoneNumberType (xs:string, maxLength=20, pattern \\d{10,20}) REQUIRED
    - validity: dateRangeType (optional)

    The choice is optional — both category fields can be absent.
    When present, exactly one of phoneCategory or otherPhoneCategory.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'phone'

    phone_category: Optional[PhoneCategory] = xml_field(
        'phoneCategory', default=None
    )
    other_phone_category: Optional[str] = xml_field(
        'otherPhoneCategory', default=None, max_length=100
    )
    phone_number: str = xml_field(
        'phoneNumber', max_length=20, pattern=r'^\d{10,20}$'
    )
    validity: Optional[ECH0129DateRange] = xml_field('validity', default=None)

    @model_validator(mode='after')
    def validate_category_choice(self) -> Self:
        """Enforce xs:choice: at most one category field."""
        if self.phone_category is not None and self.other_phone_category is not None:
            raise ValueError(
                "phoneType: only one of phone_category or "
                "other_phone_category allowed"
            )
        return self


# ---------------------------------------------------------------------------
# emailType (§4.23.1.3)
# XSD lines 79-87
# ---------------------------------------------------------------------------

class ECH0129Email(ECHModel):
    """eCH-0129 email address with optional category.

    XSD: emailType — xs:sequence.
    PDF: §4.23.1.3 (page 95)

    - xs:choice (minOccurs="0"): emailCategory enum OR otherEmailCategory free text
    - emailAddress: emailAddressType (xs:string, maxLength=100) REQUIRED
    - validity: dateRangeType (optional)

    The choice is optional — both category fields can be absent.
    When present, exactly one of emailCategory or otherEmailCategory.

    Note: XSD email regex includes umlauts (äöü etc.). Constraint applied
    via maxLength only — overly strict regex validation risks rejecting
    real Swiss email addresses.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'email'

    email_category: Optional[EmailCategory] = xml_field(
        'emailCategory', default=None
    )
    other_email_category: Optional[str] = xml_field(
        'otherEmailCategory', default=None, max_length=100
    )
    email_address: str = xml_field('emailAddress', max_length=100)
    validity: Optional[ECH0129DateRange] = xml_field('validity', default=None)

    @model_validator(mode='after')
    def validate_category_choice(self) -> Self:
        """Enforce xs:choice: at most one category field."""
        if self.email_category is not None and self.other_email_category is not None:
            raise ValueError(
                "emailType: only one of email_category or "
                "other_email_category allowed"
            )
        return self


# ---------------------------------------------------------------------------
# Anonymous inline identification choice
# Used by personType.identification, personOnlyType.identification,
# and buildingAuthorityType.contactPerson
# XSD: identical anonymous complexType in lines 1733-1737, 1765-1769, 1781-1785
# ---------------------------------------------------------------------------

class ECH0129IdentificationChoice(ECHModel):
    """Anonymous inline identification choice (person or organisation).

    Used by personType, personOnlyType (as 'identification'), and
    buildingAuthorityType (as 'contactPerson'). The parent field's
    xml_name overrides __xml_element__ during serialization.

    XSD: anonymous xs:complexType with xs:choice.
    Choice branches:
    - personIdentification: eCH-0044:personIdentificationLightType
    - organisationIdentification: eCH-0097:organisationIdentificationType

    Uses wrapper pattern for cross-namespace serialization: the choice
    branch element is in eCH-0129 namespace, its children are in the
    external standard's namespace.

    Note: different element names from the named personIdentificationType
    (§4.23.1.1) which uses 'individual'/'organisation'.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'identification'

    person_identification: Optional[ECH0044PersonIdentificationLight] = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4, default=None
    )
    organisation_identification: Optional[ECH0097OrganisationIdentification] = xml_field(
        'organisationIdentification', wrapper=True, child_ns=NS.ECH0097_V2, default=None
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one branch must be set."""
        count = sum(v is not None for v in [
            self.person_identification, self.organisation_identification
        ])
        if count == 0:
            raise ValueError(
                "identification choice: must set one of "
                "person_identification or organisation_identification"
            )
        if count > 1:
            raise ValueError(
                "identification choice: only one of "
                "person_identification or organisation_identification allowed"
            )
        return self


# ---------------------------------------------------------------------------
# buildingAuthorityType (§4.22)
# XSD lines 1727-1743
# ---------------------------------------------------------------------------

class ECH0129BuildingAuthority(ECHModel):
    """eCH-0129 building authority.

    XSD: buildingAuthorityType — xs:sequence.
    PDF: §4.22 (page 92-93)

    - buildingAuthorityIdentificationType: eCH-0097:organisationIdentificationType REQUIRED
    - description: longDescriptionType (xs:token, maxLength=100) OPTIONAL
    - shortDescription: shortDescriptionType (xs:token, maxLength=40) OPTIONAL
    - contactPerson: anonymous inline choice (person or org identification) OPTIONAL
    - contact: contactType OPTIONAL
    - address: eCH-0010:addressInformationType OPTIONAL
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingAuthority'

    building_authority_identification_type: ECH0097OrganisationIdentification = xml_field(
        'buildingAuthorityIdentificationType', wrapper=True, child_ns=NS.ECH0097_V2
    )
    description: Optional[str] = xml_field(
        'description', default=None, max_length=100
    )
    short_description: Optional[str] = xml_field(
        'shortDescription', default=None, max_length=40
    )
    contact_person: Optional[ECH0129IdentificationChoice] = xml_field(
        'contactPerson', default=None
    )
    contact: Optional[ECH0129Contact] = xml_field('contact', default=None)
    address: Optional[ECH0010v6AddressInformation] = xml_field(
        'address', wrapper=True, child_ns=NS.ECH0010_V6, default=None
    )


# ---------------------------------------------------------------------------
# buildingAuthorityOnlyType (§4.22)
# XSD lines 1744-1754
# ---------------------------------------------------------------------------

class ECH0129BuildingAuthorityOnly(ECHModel):
    """eCH-0129 building authority (restricted — identification only).

    XSD: buildingAuthorityOnlyType — xs:restriction of buildingAuthorityType.
    PDF: §4.22 (page 92-93)

    Removes: contactPerson, contact, address.
    Keeps: buildingAuthorityIdentificationType (required), description, shortDescription.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingAuthority'

    building_authority_identification_type: ECH0097OrganisationIdentification = xml_field(
        'buildingAuthorityIdentificationType', wrapper=True, child_ns=NS.ECH0097_V2
    )
    description: Optional[str] = xml_field(
        'description', default=None, max_length=100
    )
    short_description: Optional[str] = xml_field(
        'shortDescription', default=None, max_length=40
    )


# ---------------------------------------------------------------------------
# personType (§4.23)
# XSD lines 1762-1777
# ---------------------------------------------------------------------------

class ECH0129Person(ECHModel):
    """eCH-0129 person (contact person for building administration).

    XSD: personType — xs:sequence.
    PDF: §4.23 (page 93-96)

    - identification: anonymous inline choice (person or org) REQUIRED
    - address: eCH-0010:addressInformationType OPTIONAL
    - email: emailType OPTIONAL
    - phone: phoneType OPTIONAL
    - protected: protectedType (xs:boolean) OPTIONAL

    The 'identification' element contains an anonymous inline xs:choice
    of eCH-0044:personIdentificationLightType or
    eCH-0097:organisationIdentificationType. Uses element names
    'personIdentification'/'organisationIdentification' — different from
    the named personIdentificationType (§4.23.1.1) which uses
    'individual'/'organisation'.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'person'

    identification: ECH0129IdentificationChoice = xml_field('identification')
    address: Optional[ECH0010v6AddressInformation] = xml_field(
        'address', wrapper=True, child_ns=NS.ECH0010_V6, default=None
    )
    email: Optional[ECH0129Email] = xml_field('email', default=None)
    phone: Optional[ECH0129Phone] = xml_field('phone', default=None)
    protected: Optional[bool] = xml_field('protected', default=None)


# ---------------------------------------------------------------------------
# personOnlyType (§4.23)
# XSD lines 1778-1789
# ---------------------------------------------------------------------------

class ECH0129PersonOnly(ECHModel):
    """eCH-0129 person (restricted — identification only).

    XSD: personOnlyType — standalone type with only identification element.
    PDF: §4.23 (page 93-96)

    Removes: address, email, phone, protected.
    Keeps: identification (required).
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'person'

    identification: ECH0129IdentificationChoice = xml_field('identification')
