"""Tests for eCH-0129 v6.0.0 authority/person types (Session 10).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — choice constraints, field constraints
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. XML element names, ordering (xs:sequence), and cross-namespace wrappers
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0010.v6 import ECH0010v6AddressInformation, ECH0010v6Country
from openmun_ech.ech0044 import ECH0044PersonIdentificationLight
from openmun_ech.ech0097 import ECH0097OrganisationIdentification, ECH0097NamedOrganisationId
from openmun_ech.ech0129.enums import EmailCategory, PhoneCategory
from openmun_ech.ech0129.v6.authority_person import (
    ECH0129BuildingAuthority,
    ECH0129BuildingAuthorityOnly,
    ECH0129Email,
    ECH0129IdentificationChoice,
    ECH0129Person,
    ECH0129PersonOnly,
    ECH0129Phone,
)
from openmun_ech.ech0129.v6.base_types import ECH0129Contact, ECH0129DateRange

NS_0129 = NS.ECH0129_V6
NS_0044 = NS.ECH0044_V4
NS_0097 = NS.ECH0097_V2
NS_0010 = NS.ECH0010_V6


# ===========================================================================
# Helpers
# ===========================================================================

def _make_person_id_light(**kwargs):
    """Create a minimal ECH0044PersonIdentificationLight."""
    defaults = {
        'official_name': 'Meier',
        'first_name': 'Hans',
    }
    defaults.update(kwargs)
    return ECH0044PersonIdentificationLight(**defaults)


def _make_org_id(**kwargs):
    """Create a minimal ECH0097OrganisationIdentification."""
    defaults = {
        'local_organisation_id': ECH0097NamedOrganisationId(
            organisation_id_category='CH.HR',
            organisation_id='CH-123.456.789',
        ),
        'organisation_name': 'Bauamt Gemeinde Bister',
    }
    defaults.update(kwargs)
    return ECH0097OrganisationIdentification(**defaults)


def _make_address(**kwargs):
    """Create a minimal ECH0010v6AddressInformation."""
    defaults = {
        'street': 'Bahnhofstrasse',
        'house_number': '1',
        'town': 'Bister',
        'swiss_zip_code': 3983,
        'country': ECH0010v6Country(
            country_id=8100,
            country_id_iso2='CH',
            country_name_short='Schweiz',
        ),
    }
    defaults.update(kwargs)
    return ECH0010v6AddressInformation(**defaults)


def _make_id_choice_person(**kwargs):
    """Create an IdentificationChoice with person branch."""
    return ECH0129IdentificationChoice(
        person_identification=_make_person_id_light(**kwargs)
    )


def _make_id_choice_org(**kwargs):
    """Create an IdentificationChoice with organisation branch."""
    return ECH0129IdentificationChoice(
        organisation_identification=_make_org_id(**kwargs)
    )


def _roundtrip(cls, obj):
    """Serialize to XML and back, return (xml_elem, reconstructed_obj)."""
    xml_elem = obj.to_xml()
    reconstructed = cls.from_xml(xml_elem)
    return xml_elem, reconstructed


def _child_names(elem):
    """Return list of child element local names (without namespace)."""
    return [child.tag.split('}')[1] if '}' in child.tag else child.tag
            for child in elem]


# ===========================================================================
# ECH0129Phone
# ===========================================================================

class TestPhone:
    """Tests for phoneType (XSD lines 50-58)."""

    def test_minimal(self):
        """Phone with only required field (phoneNumber)."""
        phone = ECH0129Phone(phone_number='0271234567890')
        assert phone.phone_number == '0271234567890'
        assert phone.phone_category is None
        assert phone.other_phone_category is None
        assert phone.validity is None

    def test_with_category_enum(self):
        """Phone with category enum."""
        phone = ECH0129Phone(
            phone_category=PhoneCategory.PRIVATE_PHONE,
            phone_number='0271234567890',
        )
        assert phone.phone_category == PhoneCategory.PRIVATE_PHONE

    def test_with_other_category(self):
        """Phone with free-text category."""
        phone = ECH0129Phone(
            other_phone_category='Notfall',
            phone_number='0271234567890',
        )
        assert phone.other_phone_category == 'Notfall'

    def test_with_validity(self):
        """Phone with validity period."""
        phone = ECH0129Phone(
            phone_number='0271234567890',
            validity=ECH0129DateRange(
                date_from=date(2024, 1, 1),
                date_to=date(2025, 12, 31),
            ),
        )
        assert phone.validity.date_from == date(2024, 1, 1)

    def test_choice_both_categories_rejected(self):
        """Both category fields set — must fail."""
        with pytest.raises(ValueError, match='only one of'):
            ECH0129Phone(
                phone_category=PhoneCategory.PRIVATE_PHONE,
                other_phone_category='Notfall',
                phone_number='0271234567890',
            )

    def test_phone_number_too_short(self):
        """Phone number with fewer than 10 digits — must fail."""
        with pytest.raises(ValueError, match='pattern'):
            ECH0129Phone(phone_number='123456789')

    def test_phone_number_too_long(self):
        """Phone number with more than 20 digits — must fail (max_length=20)."""
        with pytest.raises(ValueError):
            ECH0129Phone(phone_number='123456789012345678901')

    def test_phone_number_non_digits(self):
        """Phone number with non-digit characters — must fail."""
        with pytest.raises(ValueError, match='pattern'):
            ECH0129Phone(phone_number='+41271234567')

    def test_roundtrip_minimal(self):
        """Minimal phone: to_xml() → from_xml()."""
        phone = ECH0129Phone(phone_number='0271234567890')
        xml_elem, rt = _roundtrip(ECH0129Phone, phone)

        assert rt.phone_number == '0271234567890'
        assert rt.phone_category is None
        assert rt.validity is None

    def test_roundtrip_full(self):
        """Full phone with all fields: to_xml() → from_xml()."""
        phone = ECH0129Phone(
            phone_category=PhoneCategory.PRIVATE_MOBILE,
            phone_number='0791234567890',
            validity=ECH0129DateRange(date_from=date(2024, 1, 1)),
        )
        xml_elem, rt = _roundtrip(ECH0129Phone, phone)

        assert rt.phone_category == PhoneCategory.PRIVATE_MOBILE
        assert rt.phone_number == '0791234567890'
        assert rt.validity.date_from == date(2024, 1, 1)

    def test_roundtrip_other_category(self):
        """Phone with other_phone_category: to_xml() → from_xml()."""
        phone = ECH0129Phone(
            other_phone_category='Satellitentelefon',
            phone_number='0271234567890',
        )
        xml_elem, rt = _roundtrip(ECH0129Phone, phone)

        assert rt.other_phone_category == 'Satellitentelefon'
        assert rt.phone_category is None

    def test_xml_element_order(self):
        """Verify xs:sequence element order: category, phoneNumber, validity."""
        phone = ECH0129Phone(
            phone_category=PhoneCategory.PRIVATE_PHONE,
            phone_number='0271234567890',
            validity=ECH0129DateRange(date_from=date(2024, 1, 1)),
        )
        xml_elem = phone.to_xml()
        names = _child_names(xml_elem)
        assert names == ['phoneCategory', 'phoneNumber', 'validity']


# ===========================================================================
# ECH0129Email
# ===========================================================================

class TestEmail:
    """Tests for emailType (XSD lines 79-87)."""

    def test_minimal(self):
        """Email with only required field (emailAddress)."""
        email = ECH0129Email(email_address='hans@example.ch')
        assert email.email_address == 'hans@example.ch'
        assert email.email_category is None
        assert email.other_email_category is None

    def test_with_category_enum(self):
        """Email with category enum."""
        email = ECH0129Email(
            email_category=EmailCategory.PRIVATE,
            email_address='hans@example.ch',
        )
        assert email.email_category == EmailCategory.PRIVATE

    def test_with_other_category(self):
        """Email with free-text category."""
        email = ECH0129Email(
            other_email_category='Newsletter',
            email_address='info@example.ch',
        )
        assert email.other_email_category == 'Newsletter'

    def test_choice_both_categories_rejected(self):
        """Both category fields set — must fail."""
        with pytest.raises(ValueError, match='only one of'):
            ECH0129Email(
                email_category=EmailCategory.PRIVATE,
                other_email_category='Newsletter',
                email_address='hans@example.ch',
            )

    def test_email_too_long(self):
        """Email address exceeding maxLength=100."""
        with pytest.raises(ValueError):
            ECH0129Email(email_address='a' * 96 + '@b.ch')

    def test_roundtrip_minimal(self):
        """Minimal email: to_xml() → from_xml()."""
        email = ECH0129Email(email_address='hans@example.ch')
        _, rt = _roundtrip(ECH0129Email, email)

        assert rt.email_address == 'hans@example.ch'
        assert rt.email_category is None

    def test_roundtrip_full(self):
        """Full email with all fields: to_xml() → from_xml()."""
        email = ECH0129Email(
            email_category=EmailCategory.BUSINESS,
            email_address='bauamt@bister.ch',
            validity=ECH0129DateRange(
                date_from=date(2024, 1, 1),
                date_to=date(2025, 12, 31),
            ),
        )
        _, rt = _roundtrip(ECH0129Email, email)

        assert rt.email_category == EmailCategory.BUSINESS
        assert rt.email_address == 'bauamt@bister.ch'
        assert rt.validity.date_to == date(2025, 12, 31)

    def test_xml_element_order(self):
        """Verify xs:sequence element order: category, emailAddress, validity."""
        email = ECH0129Email(
            email_category=EmailCategory.PRIVATE,
            email_address='hans@example.ch',
            validity=ECH0129DateRange(date_from=date(2024, 1, 1)),
        )
        xml_elem = email.to_xml()
        names = _child_names(xml_elem)
        assert names == ['emailCategory', 'emailAddress', 'validity']


# ===========================================================================
# ECH0129IdentificationChoice
# ===========================================================================

class TestIdentificationChoice:
    """Tests for anonymous inline identification choice."""

    def test_person_branch(self):
        """Create with person identification."""
        choice = _make_id_choice_person()
        assert choice.person_identification is not None
        assert choice.organisation_identification is None

    def test_org_branch(self):
        """Create with organisation identification."""
        choice = _make_id_choice_org()
        assert choice.organisation_identification is not None
        assert choice.person_identification is None

    def test_none_rejected(self):
        """No branch set — must fail."""
        with pytest.raises(ValueError, match='must set one of'):
            ECH0129IdentificationChoice()

    def test_both_rejected(self):
        """Both branches set — must fail."""
        with pytest.raises(ValueError, match='only one of'):
            ECH0129IdentificationChoice(
                person_identification=_make_person_id_light(),
                organisation_identification=_make_org_id(),
            )

    def test_roundtrip_person(self):
        """Person branch: to_xml() → from_xml()."""
        choice = _make_id_choice_person()
        xml_elem, rt = _roundtrip(ECH0129IdentificationChoice, choice)

        assert rt.person_identification is not None
        assert rt.person_identification.official_name == 'Meier'
        assert rt.person_identification.first_name == 'Hans'
        assert rt.organisation_identification is None

    def test_roundtrip_org(self):
        """Organisation branch: to_xml() → from_xml()."""
        choice = _make_id_choice_org()
        xml_elem, rt = _roundtrip(ECH0129IdentificationChoice, choice)

        assert rt.organisation_identification is not None
        assert rt.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'
        assert rt.person_identification is None

    def test_xml_person_branch_structure(self):
        """Verify XML: <identification><personIdentification><eCH-0044:...>."""
        choice = _make_id_choice_person()
        xml_elem = choice.to_xml()

        # Root element in eCH-0129 namespace
        assert xml_elem.tag == f'{{{NS_0129}}}identification'

        # Choice branch: personIdentification wrapper in eCH-0129 ns
        person_elem = xml_elem.find(f'{{{NS_0129}}}personIdentification')
        assert person_elem is not None

        # Children in eCH-0044 namespace
        name_elem = person_elem.find(f'{{{NS_0044}}}officialName')
        assert name_elem is not None
        assert name_elem.text == 'Meier'

    def test_xml_org_branch_structure(self):
        """Verify XML: <identification><organisationIdentification><eCH-0097:...>."""
        choice = _make_id_choice_org()
        xml_elem = choice.to_xml()

        # Root element in eCH-0129 namespace
        assert xml_elem.tag == f'{{{NS_0129}}}identification'

        # Choice branch: organisationIdentification wrapper in eCH-0129 ns
        org_elem = xml_elem.find(f'{{{NS_0129}}}organisationIdentification')
        assert org_elem is not None

        # Children in eCH-0097 namespace
        name_elem = org_elem.find(f'{{{NS_0097}}}organisationName')
        assert name_elem is not None
        assert name_elem.text == 'Bauamt Gemeinde Bister'


# ===========================================================================
# ECH0129BuildingAuthority
# ===========================================================================

class TestBuildingAuthority:
    """Tests for buildingAuthorityType (XSD lines 1727-1743)."""

    def test_minimal(self):
        """Building authority with only required field."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
        )
        assert ba.building_authority_identification_type.organisation_name == 'Bauamt Gemeinde Bister'
        assert ba.description is None
        assert ba.short_description is None
        assert ba.contact_person is None
        assert ba.contact is None
        assert ba.address is None

    def test_full(self):
        """Building authority with all fields."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            description='Bauamt der Gemeinde Bister',
            short_description='Bauamt Bister',
            contact_person=_make_id_choice_person(),
            contact=ECH0129Contact(
                email_address='bauamt@bister.ch',
                phone_number='0271234567890',
            ),
            address=_make_address(),
        )
        assert ba.description == 'Bauamt der Gemeinde Bister'
        assert ba.short_description == 'Bauamt Bister'
        assert ba.contact_person.person_identification.first_name == 'Hans'
        assert ba.contact.email_address == 'bauamt@bister.ch'
        assert ba.address.town == 'Bister'

    def test_description_too_long(self):
        """Description exceeding maxLength=100."""
        with pytest.raises(ValueError):
            ECH0129BuildingAuthority(
                building_authority_identification_type=_make_org_id(),
                description='x' * 101,
            )

    def test_short_description_too_long(self):
        """Short description exceeding maxLength=40."""
        with pytest.raises(ValueError):
            ECH0129BuildingAuthority(
                building_authority_identification_type=_make_org_id(),
                short_description='x' * 41,
            )

    def test_roundtrip_minimal(self):
        """Minimal building authority: to_xml() → from_xml()."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
        )
        _, rt = _roundtrip(ECH0129BuildingAuthority, ba)

        assert rt.building_authority_identification_type.organisation_name == 'Bauamt Gemeinde Bister'
        assert rt.description is None
        assert rt.contact_person is None

    def test_roundtrip_full(self):
        """Full building authority: to_xml() → from_xml()."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            description='Bauamt der Gemeinde Bister',
            short_description='Bauamt',
            contact_person=_make_id_choice_person(),
            contact=ECH0129Contact(phone_number='0271234567890'),
            address=_make_address(),
        )
        _, rt = _roundtrip(ECH0129BuildingAuthority, ba)

        assert rt.description == 'Bauamt der Gemeinde Bister'
        assert rt.short_description == 'Bauamt'
        assert rt.contact_person.person_identification.official_name == 'Meier'
        assert rt.contact.phone_number == '0271234567890'
        assert rt.address.town == 'Bister'

    def test_contact_person_with_org(self):
        """Contact person can be an organisation too."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            contact_person=_make_id_choice_org(),
        )
        _, rt = _roundtrip(ECH0129BuildingAuthority, ba)

        assert rt.contact_person.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'

    def test_xml_element_order(self):
        """Verify xs:sequence element order."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            description='Test',
            short_description='T',
            contact_person=_make_id_choice_person(),
            contact=ECH0129Contact(phone_number='0271234567890'),
            address=_make_address(),
        )
        xml_elem = ba.to_xml()
        names = _child_names(xml_elem)
        assert names == [
            'buildingAuthorityIdentificationType',
            'description',
            'shortDescription',
            'contactPerson',
            'contact',
            'address',
        ]

    def test_xml_identification_wrapper(self):
        """buildingAuthorityIdentificationType wraps eCH-0097 content."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
        )
        xml_elem = ba.to_xml()

        id_elem = xml_elem.find(f'{{{NS_0129}}}buildingAuthorityIdentificationType')
        assert id_elem is not None

        # Children should be in eCH-0097 namespace
        org_name = id_elem.find(f'{{{NS_0097}}}organisationName')
        assert org_name is not None
        assert org_name.text == 'Bauamt Gemeinde Bister'

    def test_xml_address_wrapper(self):
        """address wraps eCH-0010 v6 content."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            address=_make_address(),
        )
        xml_elem = ba.to_xml()

        addr_elem = xml_elem.find(f'{{{NS_0129}}}address')
        assert addr_elem is not None

        # Children should be in eCH-0010 v6 namespace
        town = addr_elem.find(f'{{{NS_0010}}}town')
        assert town is not None
        assert town.text == 'Bister'

    def test_xml_contact_person_wrapper_name(self):
        """contactPerson uses 'contactPerson' as element name, not 'identification'."""
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            contact_person=_make_id_choice_person(),
        )
        xml_elem = ba.to_xml()

        # Element name should be 'contactPerson' not 'identification'
        cp_elem = xml_elem.find(f'{{{NS_0129}}}contactPerson')
        assert cp_elem is not None

        # Should NOT have an 'identification' child
        id_elem = xml_elem.find(f'{{{NS_0129}}}identification')
        assert id_elem is None


# ===========================================================================
# ECH0129BuildingAuthorityOnly
# ===========================================================================

class TestBuildingAuthorityOnly:
    """Tests for buildingAuthorityOnlyType (XSD lines 1744-1754)."""

    def test_minimal(self):
        """Restricted type with only required field."""
        ba = ECH0129BuildingAuthorityOnly(
            building_authority_identification_type=_make_org_id(),
        )
        assert ba.building_authority_identification_type.organisation_name == 'Bauamt Gemeinde Bister'
        assert ba.description is None
        assert ba.short_description is None

    def test_with_descriptions(self):
        """Restricted type with optional descriptions."""
        ba = ECH0129BuildingAuthorityOnly(
            building_authority_identification_type=_make_org_id(),
            description='Bauamt',
            short_description='BA',
        )
        assert ba.description == 'Bauamt'
        assert ba.short_description == 'BA'

    def test_no_contact_person_field(self):
        """Restricted type should not have contactPerson, contact, address."""
        assert not hasattr(ECH0129BuildingAuthorityOnly, 'contact_person') or \
               'contact_person' not in ECH0129BuildingAuthorityOnly.model_fields

    def test_no_contact_field(self):
        assert 'contact' not in ECH0129BuildingAuthorityOnly.model_fields

    def test_no_address_field(self):
        assert 'address' not in ECH0129BuildingAuthorityOnly.model_fields

    def test_roundtrip(self):
        """Roundtrip: to_xml() → from_xml()."""
        ba = ECH0129BuildingAuthorityOnly(
            building_authority_identification_type=_make_org_id(),
            description='Test',
        )
        _, rt = _roundtrip(ECH0129BuildingAuthorityOnly, ba)

        assert rt.building_authority_identification_type.organisation_name == 'Bauamt Gemeinde Bister'
        assert rt.description == 'Test'

    def test_xml_element_order(self):
        """Verify xs:sequence element order."""
        ba = ECH0129BuildingAuthorityOnly(
            building_authority_identification_type=_make_org_id(),
            description='Test',
            short_description='T',
        )
        xml_elem = ba.to_xml()
        names = _child_names(xml_elem)
        assert names == [
            'buildingAuthorityIdentificationType',
            'description',
            'shortDescription',
        ]


# ===========================================================================
# ECH0129Person
# ===========================================================================

class TestPerson:
    """Tests for personType (XSD lines 1762-1777)."""

    def test_minimal_with_person(self):
        """Person with only required identification (person branch)."""
        person = ECH0129Person(identification=_make_id_choice_person())
        assert person.identification.person_identification.official_name == 'Meier'
        assert person.address is None
        assert person.email is None
        assert person.phone is None
        assert person.protected is None

    def test_minimal_with_org(self):
        """Person with only required identification (org branch)."""
        person = ECH0129Person(identification=_make_id_choice_org())
        assert person.identification.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'

    def test_full(self):
        """Person with all fields populated."""
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            address=_make_address(),
            email=ECH0129Email(email_address='hans@example.ch'),
            phone=ECH0129Phone(phone_number='0271234567890'),
            protected=True,
        )
        assert person.address.town == 'Bister'
        assert person.email.email_address == 'hans@example.ch'
        assert person.phone.phone_number == '0271234567890'
        assert person.protected is True

    def test_protected_false(self):
        """Protected can be explicitly False."""
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            protected=False,
        )
        assert person.protected is False

    def test_roundtrip_minimal(self):
        """Minimal person: to_xml() → from_xml()."""
        person = ECH0129Person(identification=_make_id_choice_person())
        _, rt = _roundtrip(ECH0129Person, person)

        assert rt.identification.person_identification.official_name == 'Meier'
        assert rt.address is None
        assert rt.email is None
        assert rt.phone is None
        assert rt.protected is None

    def test_roundtrip_full(self):
        """Full person: to_xml() → from_xml()."""
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            address=_make_address(),
            email=ECH0129Email(
                email_category=EmailCategory.BUSINESS,
                email_address='bauamt@bister.ch',
            ),
            phone=ECH0129Phone(
                phone_category=PhoneCategory.BUSINESS_DIRECT,
                phone_number='0271234567890',
            ),
            protected=True,
        )
        _, rt = _roundtrip(ECH0129Person, person)

        assert rt.identification.person_identification.first_name == 'Hans'
        assert rt.address.swiss_zip_code == 3983
        assert rt.email.email_category == EmailCategory.BUSINESS
        assert rt.email.email_address == 'bauamt@bister.ch'
        assert rt.phone.phone_category == PhoneCategory.BUSINESS_DIRECT
        assert rt.phone.phone_number == '0271234567890'
        assert rt.protected is True

    def test_roundtrip_org_identification(self):
        """Person with org identification: to_xml() → from_xml()."""
        person = ECH0129Person(identification=_make_id_choice_org())
        _, rt = _roundtrip(ECH0129Person, person)

        assert rt.identification.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'
        assert rt.identification.person_identification is None

    def test_xml_element_order(self):
        """Verify xs:sequence element order."""
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            address=_make_address(),
            email=ECH0129Email(email_address='a@b.ch'),
            phone=ECH0129Phone(phone_number='0271234567890'),
            protected=False,
        )
        xml_elem = person.to_xml()
        names = _child_names(xml_elem)
        assert names == ['identification', 'address', 'email', 'phone', 'protected']

    def test_xml_identification_structure(self):
        """Verify nested structure: person > identification > personIdentification > eCH-0044."""
        person = ECH0129Person(identification=_make_id_choice_person())
        xml_elem = person.to_xml()

        # <eCH-0129:person>
        assert xml_elem.tag == f'{{{NS_0129}}}person'

        # <eCH-0129:identification>
        id_elem = xml_elem.find(f'{{{NS_0129}}}identification')
        assert id_elem is not None

        # <eCH-0129:personIdentification>
        pi_elem = id_elem.find(f'{{{NS_0129}}}personIdentification')
        assert pi_elem is not None

        # <eCH-0044:officialName>
        name = pi_elem.find(f'{{{NS_0044}}}officialName')
        assert name is not None
        assert name.text == 'Meier'

    def test_xml_address_wrapper(self):
        """address wraps eCH-0010 v6 content."""
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            address=_make_address(),
        )
        xml_elem = person.to_xml()

        addr_elem = xml_elem.find(f'{{{NS_0129}}}address')
        assert addr_elem is not None

        town = addr_elem.find(f'{{{NS_0010}}}town')
        assert town is not None
        assert town.text == 'Bister'


# ===========================================================================
# ECH0129PersonOnly
# ===========================================================================

class TestPersonOnly:
    """Tests for personOnlyType (XSD lines 1778-1789)."""

    def test_with_person(self):
        """PersonOnly with person identification."""
        po = ECH0129PersonOnly(identification=_make_id_choice_person())
        assert po.identification.person_identification.official_name == 'Meier'

    def test_with_org(self):
        """PersonOnly with organisation identification."""
        po = ECH0129PersonOnly(identification=_make_id_choice_org())
        assert po.identification.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'

    def test_no_address_field(self):
        """Restricted type should not have address, email, phone, protected."""
        assert 'address' not in ECH0129PersonOnly.model_fields

    def test_no_email_field(self):
        assert 'email' not in ECH0129PersonOnly.model_fields

    def test_no_phone_field(self):
        assert 'phone' not in ECH0129PersonOnly.model_fields

    def test_no_protected_field(self):
        assert 'protected' not in ECH0129PersonOnly.model_fields

    def test_roundtrip_person(self):
        """PersonOnly with person: to_xml() → from_xml()."""
        po = ECH0129PersonOnly(identification=_make_id_choice_person())
        _, rt = _roundtrip(ECH0129PersonOnly, po)

        assert rt.identification.person_identification.official_name == 'Meier'
        assert rt.identification.person_identification.first_name == 'Hans'

    def test_roundtrip_org(self):
        """PersonOnly with org: to_xml() → from_xml()."""
        po = ECH0129PersonOnly(identification=_make_id_choice_org())
        _, rt = _roundtrip(ECH0129PersonOnly, po)

        assert rt.identification.organisation_identification.organisation_name == 'Bauamt Gemeinde Bister'

    def test_xml_only_identification(self):
        """PersonOnly serializes only the identification element."""
        po = ECH0129PersonOnly(identification=_make_id_choice_person())
        xml_elem = po.to_xml()
        names = _child_names(xml_elem)
        assert names == ['identification']

    def test_same_element_name_as_person(self):
        """PersonOnly uses same __xml_element__ 'person' as personType."""
        po = ECH0129PersonOnly(identification=_make_id_choice_person())
        xml_elem = po.to_xml()
        assert xml_elem.tag == f'{{{NS_0129}}}person'


# ===========================================================================
# Double roundtrip stability
# ===========================================================================

class TestDoubleRoundtrip:
    """Verify serialize → parse → serialize → parse produces identical results."""

    def _double_roundtrip(self, cls, obj):
        xml1 = obj.to_xml()
        rt1 = cls.from_xml(xml1)
        xml2 = rt1.to_xml()
        rt2 = cls.from_xml(xml2)
        return rt1, rt2, ET.tostring(xml1), ET.tostring(xml2)

    def test_phone(self):
        phone = ECH0129Phone(
            phone_category=PhoneCategory.PRIVATE_MOBILE,
            phone_number='0791234567890',
            validity=ECH0129DateRange(date_from=date(2024, 1, 1)),
        )
        rt1, rt2, xml1, xml2 = self._double_roundtrip(ECH0129Phone, phone)
        assert xml1 == xml2

    def test_email(self):
        email = ECH0129Email(
            email_category=EmailCategory.BUSINESS,
            email_address='bauamt@bister.ch',
            validity=ECH0129DateRange(date_to=date(2025, 12, 31)),
        )
        rt1, rt2, xml1, xml2 = self._double_roundtrip(ECH0129Email, email)
        assert xml1 == xml2

    def test_building_authority(self):
        ba = ECH0129BuildingAuthority(
            building_authority_identification_type=_make_org_id(),
            description='Bauamt',
            contact_person=_make_id_choice_person(),
            contact=ECH0129Contact(phone_number='0271234567890'),
            address=_make_address(),
        )
        rt1, rt2, xml1, xml2 = self._double_roundtrip(ECH0129BuildingAuthority, ba)
        assert xml1 == xml2

    def test_person(self):
        person = ECH0129Person(
            identification=_make_id_choice_person(),
            address=_make_address(),
            email=ECH0129Email(email_address='hans@bister.ch'),
            phone=ECH0129Phone(phone_number='0271234567890'),
            protected=True,
        )
        rt1, rt2, xml1, xml2 = self._double_roundtrip(ECH0129Person, person)
        assert xml1 == xml2

    def test_person_only(self):
        po = ECH0129PersonOnly(identification=_make_id_choice_org())
        rt1, rt2, xml1, xml2 = self._double_roundtrip(ECH0129PersonOnly, po)
        assert xml1 == xml2
