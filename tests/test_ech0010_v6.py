"""Tests for eCH-0010 v6.0 address types.

Verifies the v5→v6 country field change (countryIdIso2Type → countryType),
namespace correctness, and XML serialization roundtrip.
"""

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0010.v6 import (
    ECH0010v6Country,
    ECH0010v6AddressInformation,
    ECH0010v6SwissAddressInformation,
    ECH0010v6PersonMailAddressInfo,
    ECH0010v6MailAddress,
    MrMrs,
)


class TestECH0010v6Country:
    """Test the new v6 countryType (replaces simple countryIdIso2Type)."""

    def test_create_minimal(self):
        c = ECH0010v6Country(country_name_short='Schweiz')
        assert c.country_name_short == 'Schweiz'
        assert c.country_id is None
        assert c.country_id_iso2 is None

    def test_create_full(self):
        c = ECH0010v6Country(
            country_id=8100,
            country_id_iso2='CH',
            country_name_short='Schweiz',
        )
        assert c.country_id == 8100
        assert c.country_id_iso2 == 'CH'

    def test_iso2_uppercase(self):
        c = ECH0010v6Country(country_id_iso2='ch', country_name_short='Schweiz')
        assert c.country_id_iso2 == 'CH'

    def test_country_id_range(self):
        with pytest.raises(Exception):
            ECH0010v6Country(country_id=999, country_name_short='Test')
        with pytest.raises(Exception):
            ECH0010v6Country(country_id=10000, country_name_short='Test')

    def test_xml_namespace_is_v6(self):
        c = ECH0010v6Country(country_name_short='Schweiz')
        xml = c.to_xml()
        assert xml.tag == f'{{{NS.ECH0010_V6}}}country'

    def test_xml_roundtrip(self):
        original = ECH0010v6Country(
            country_id=8100,
            country_id_iso2='CH',
            country_name_short='Schweiz',
        )
        xml = original.to_xml()
        restored = ECH0010v6Country.from_xml(xml)
        assert restored.country_id == original.country_id
        assert restored.country_id_iso2 == original.country_id_iso2
        assert restored.country_name_short == original.country_name_short


class TestECH0010v6AddressInformation:
    """Test v6 addressInformationType with complex country field."""

    def test_create_swiss(self):
        addr = ECH0010v6AddressInformation(
            street='Dorfstrasse',
            house_number='1',
            town='Bister',
            swiss_zip_code=3983,
            country=ECH0010v6Country(country_id_iso2='CH', country_name_short='Schweiz'),
        )
        assert addr.street == 'Dorfstrasse'
        assert addr.swiss_zip_code == 3983
        assert addr.country.country_name_short == 'Schweiz'

    def test_create_foreign(self):
        addr = ECH0010v6AddressInformation(
            town='Berlin',
            foreign_zip_code='10115',
            country=ECH0010v6Country(country_id_iso2='DE', country_name_short='Deutschland'),
        )
        assert addr.foreign_zip_code == '10115'
        assert addr.country.country_id_iso2 == 'DE'

    def test_zip_exclusivity(self):
        with pytest.raises(ValueError, match='Cannot have both'):
            ECH0010v6AddressInformation(
                town='Test',
                swiss_zip_code=3000,
                foreign_zip_code='12345',
                country=ECH0010v6Country(country_name_short='Test'),
            )

    def test_swiss_zip_addon_requires_zip(self):
        with pytest.raises(ValueError, match='swiss_zip_code_add_on requires'):
            ECH0010v6AddressInformation(
                town='Test',
                swiss_zip_code_add_on='00',
                country=ECH0010v6Country(country_name_short='Test'),
            )

    def test_xml_namespace_is_v6(self):
        addr = ECH0010v6AddressInformation(
            town='Bister',
            swiss_zip_code=3983,
            country=ECH0010v6Country(country_name_short='Schweiz'),
        )
        xml = addr.to_xml()
        assert xml.tag == f'{{{NS.ECH0010_V6}}}addressInformation'

    def test_xml_roundtrip(self):
        original = ECH0010v6AddressInformation(
            street='Dorfstrasse',
            house_number='1',
            town='Bister',
            swiss_zip_code=3983,
            country=ECH0010v6Country(
                country_id=8100,
                country_id_iso2='CH',
                country_name_short='Schweiz',
            ),
        )
        xml = original.to_xml()
        restored = ECH0010v6AddressInformation.from_xml(xml)
        assert restored.street == original.street
        assert restored.house_number == original.house_number
        assert restored.town == original.town
        assert restored.swiss_zip_code == original.swiss_zip_code
        assert restored.country.country_id == original.country.country_id
        assert restored.country.country_id_iso2 == original.country.country_id_iso2
        assert restored.country.country_name_short == original.country.country_name_short


class TestECH0010v6SwissAddressInformation:
    """Test v6 swissAddressInformationType."""

    def test_create(self):
        addr = ECH0010v6SwissAddressInformation(
            town='Bister',
            swiss_zip_code=3983,
            country=ECH0010v6Country(country_name_short='Schweiz'),
        )
        assert addr.swiss_zip_code == 3983

    def test_xml_roundtrip(self):
        original = ECH0010v6SwissAddressInformation(
            street='Dorfstrasse',
            town='Bister',
            swiss_zip_code=3983,
            country=ECH0010v6Country(country_id_iso2='CH', country_name_short='Schweiz'),
        )
        xml = original.to_xml()
        restored = ECH0010v6SwissAddressInformation.from_xml(xml)
        assert restored.swiss_zip_code == original.swiss_zip_code
        assert restored.country.country_name_short == original.country.country_name_short


class TestECH0010v6MailAddress:
    """Test v6 mail address with person/organisation choice."""

    def test_person_mail_address(self):
        addr = ECH0010v6MailAddress(
            person=ECH0010v6PersonMailAddressInfo(
                first_name='Karl',
                last_name='Bister',
            ),
            address_information=ECH0010v6AddressInformation(
                town='Bister',
                swiss_zip_code=3983,
                country=ECH0010v6Country(country_name_short='Schweiz'),
            ),
        )
        assert addr.person.last_name == 'Bister'

    def test_person_or_org_required(self):
        with pytest.raises(ValueError, match='Must have either'):
            ECH0010v6MailAddress(
                address_information=ECH0010v6AddressInformation(
                    town='Test',
                    swiss_zip_code=3000,
                    country=ECH0010v6Country(country_name_short='Test'),
                ),
            )


class TestNamespaceDistinction:
    """Verify v5 and v6 produce different namespace URIs."""

    def test_v5_vs_v6_namespace(self):
        from openmun_ech.ech0010.v5 import ECH0010AddressInformation

        v5 = ECH0010AddressInformation(
            town='Test', swiss_zip_code=3000, country='CH',
        )
        v6 = ECH0010v6AddressInformation(
            town='Test', swiss_zip_code=3000,
            country=ECH0010v6Country(country_name_short='Schweiz'),
        )

        v5_xml = v5.to_xml()
        v6_xml = v6.to_xml()

        assert NS.ECH0010_V5 in v5_xml.tag
        assert NS.ECH0010_V6 in v6_xml.tag
        assert v5_xml.tag != v6_xml.tag
