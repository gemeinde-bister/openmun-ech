"""Tests for eCH-0097 Organisation Identification models."""

import xml.etree.ElementTree as ET

import pytest
from pydantic import ValidationError

from openmun_ech.ech0097 import (
    ECH0097NamedOrganisationId,
    ECH0097OrganisationIdentification,
    ECH0097OrganisationIdentificationRoot,
    ECH0097UidStructure,
    UidOrganisationIdCategory,
    validate_uid_checksum,
)

NS_0097 = 'http://www.ech.ch/xmlns/eCH-0097/2'


# --- Module 11 checksum ---


class TestUidChecksum:
    """Test Module 11 checksum algorithm (PDF §3.4.2)."""

    def test_pdf_example_valid(self):
        """PDF example: 10932255 → check digit 1 → 109322551."""
        assert validate_uid_checksum(109322551) is True

    def test_check_digit_zero(self):
        """When product sum is divisible by 11, check digit = 0."""
        # 100000000: payload 10000000, products = 1*5+0+0+0+0+0+0+0 = 5
        # 5 % 11 = 5, check = 11 - 5 = 6 → 100000006
        assert validate_uid_checksum(100000006) is True
        assert validate_uid_checksum(100000001) is False

    def test_invalid_checksum(self):
        """Wrong check digit should fail."""
        assert validate_uid_checksum(109322550) is False
        assert validate_uid_checksum(109322552) is False

    def test_out_of_range(self):
        """Numbers outside 9-digit range should fail."""
        assert validate_uid_checksum(0) is False
        assert validate_uid_checksum(1234567890) is False


# --- Enum ---


class TestUidOrganisationIdCategory:
    """Test UID category enum."""

    def test_values(self):
        assert UidOrganisationIdCategory.CHE.value == "CHE"
        assert UidOrganisationIdCategory.ADM.value == "ADM"

    def test_from_string(self):
        assert UidOrganisationIdCategory("CHE") == UidOrganisationIdCategory.CHE
        assert UidOrganisationIdCategory("ADM") == UidOrganisationIdCategory.ADM

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            UidOrganisationIdCategory("XXX")


# --- ECH0097UidStructure ---


class TestECH0097UidStructure:
    """Test UID structure model."""

    def test_create_valid(self):
        uid = ECH0097UidStructure(
            uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
            uid_organisation_id=109322551,
        )
        assert uid.uid_organisation_id_categorie == UidOrganisationIdCategory.CHE
        assert uid.uid_organisation_id == 109322551

    def test_adm_category(self):
        uid = ECH0097UidStructure(
            uid_organisation_id_categorie=UidOrganisationIdCategory.ADM,
            uid_organisation_id=109322551,
        )
        assert uid.uid_organisation_id_categorie == UidOrganisationIdCategory.ADM

    def test_uid_too_small(self):
        with pytest.raises(ValidationError, match="must be 1-999999999"):
            ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=0,
            )

    def test_uid_too_large(self):
        with pytest.raises(ValidationError, match="must be 1-999999999"):
            ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=1000000000,
            )

    def test_uid_invalid_checksum(self):
        with pytest.raises(ValidationError, match="Module 11 checksum"):
            ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322550,
            )

    def test_to_xml(self):
        uid = ECH0097UidStructure(
            uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
            uid_organisation_id=109322551,
        )
        xml = uid.to_xml()

        assert xml.tag == f'{{{NS_0097}}}uid'

        cat = xml.find(f'{{{NS_0097}}}uidOrganisationIdCategorie')
        assert cat is not None
        assert cat.text == "CHE"

        oid = xml.find(f'{{{NS_0097}}}uidOrganisationId')
        assert oid is not None
        assert oid.text == "109322551"

    def test_from_xml(self):
        xml_str = f"""
        <uid xmlns="{NS_0097}">
            <uidOrganisationIdCategorie>CHE</uidOrganisationIdCategorie>
            <uidOrganisationId>109322551</uidOrganisationId>
        </uid>
        """
        elem = ET.fromstring(xml_str)
        uid = ECH0097UidStructure.from_xml(elem)

        assert uid.uid_organisation_id_categorie == UidOrganisationIdCategory.CHE
        assert uid.uid_organisation_id == 109322551

    def test_roundtrip(self):
        original = ECH0097UidStructure(
            uid_organisation_id_categorie=UidOrganisationIdCategory.ADM,
            uid_organisation_id=109322551,
        )
        xml = original.to_xml()
        restored = ECH0097UidStructure.from_xml(xml)

        assert restored.uid_organisation_id_categorie == original.uid_organisation_id_categorie
        assert restored.uid_organisation_id == original.uid_organisation_id


# --- ECH0097NamedOrganisationId ---


class TestECH0097NamedOrganisationId:
    """Test named organisation identifier model."""

    def test_create_federal(self):
        """Federal identifier: CH.BUR"""
        nid = ECH0097NamedOrganisationId(
            organisation_id_category="CH.BUR",
            organisation_id="123456",
        )
        assert nid.organisation_id_category == "CH.BUR"
        assert nid.organisation_id == "123456"

    def test_create_municipal(self):
        """Municipal identifier: MU.6172"""
        nid = ECH0097NamedOrganisationId(
            organisation_id_category="MU.6172",
            organisation_id="789",
        )
        assert nid.organisation_id_category == "MU.6172"

    def test_create_local(self):
        """Local identifier: LOC"""
        nid = ECH0097NamedOrganisationId(
            organisation_id_category="LOC",
            organisation_id="internal-42",
        )
        assert nid.organisation_id_category == "LOC"

    def test_empty_category_rejected(self):
        with pytest.raises(ValidationError):
            ECH0097NamedOrganisationId(
                organisation_id_category="",
                organisation_id="123",
            )

    def test_empty_id_rejected(self):
        with pytest.raises(ValidationError):
            ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="",
            )

    def test_category_too_long(self):
        with pytest.raises(ValidationError):
            ECH0097NamedOrganisationId(
                organisation_id_category="A" * 21,
                organisation_id="123",
            )

    def test_to_xml(self):
        nid = ECH0097NamedOrganisationId(
            organisation_id_category="CH.MWST",
            organisation_id="123456",
        )
        xml = nid.to_xml()

        assert xml.tag == f'{{{NS_0097}}}namedOrganisationId'

        cat = xml.find(f'{{{NS_0097}}}organisationIdCategory')
        assert cat is not None
        assert cat.text == "CH.MWST"

        oid = xml.find(f'{{{NS_0097}}}organisationId')
        assert oid is not None
        assert oid.text == "123456"

    def test_from_xml(self):
        xml_str = f"""
        <namedOrganisationId xmlns="{NS_0097}">
            <organisationIdCategory>CH.HR</organisationIdCategory>
            <organisationId>CH-550.1.032.746-3</organisationId>
        </namedOrganisationId>
        """
        elem = ET.fromstring(xml_str)
        nid = ECH0097NamedOrganisationId.from_xml(elem)

        assert nid.organisation_id_category == "CH.HR"
        assert nid.organisation_id == "CH-550.1.032.746-3"

    def test_roundtrip(self):
        original = ECH0097NamedOrganisationId(
            organisation_id_category="CT.VS",
            organisation_id="98765",
        )
        xml = original.to_xml()
        restored = ECH0097NamedOrganisationId.from_xml(xml)

        assert restored.organisation_id_category == original.organisation_id_category
        assert restored.organisation_id == original.organisation_id


# --- ECH0097OrganisationIdentification ---


class TestECH0097OrganisationIdentification:
    """Test organisation identification container."""

    def test_create_minimal(self):
        """Only required fields: localOrganisationId + name."""
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123456",
            ),
            organisation_name="Test AG",
        )
        assert org.uid is None
        assert org.organisation_name == "Test AG"
        assert org.other_organisation_id == []
        assert org.organisation_legal_name is None
        assert org.organisation_additional_name is None
        assert org.legal_form is None

    def test_create_full(self):
        """All fields populated."""
        org = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123456",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR",
                    organisation_id="CH-550.1.032.746-3",
                ),
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.MWST",
                    organisation_id="CHE109322551MWST",
                ),
            ],
            organisation_name="Beispiel AG",
            organisation_legal_name="Beispiel Aktiengesellschaft",
            organisation_additional_name="Treuhand und Beratung",
            legal_form="0106",
        )
        assert org.uid.uid_organisation_id == 109322551
        assert len(org.other_organisation_id) == 2
        assert org.legal_form == "0106"

    def test_uid_optional(self):
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC",
                organisation_id="1",
            ),
            organisation_name="No UID GmbH",
        )
        assert org.uid is None

    def test_other_organisation_ids_empty_list(self):
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC",
                organisation_id="1",
            ),
            organisation_name="Test",
        )
        assert org.other_organisation_id == []

    def test_legal_form_valid_two_digit(self):
        """Two-digit category code (e.g., '01' = Privatrecht)."""
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC", organisation_id="1",
            ),
            organisation_name="Test",
            legal_form="01",
        )
        assert org.legal_form == "01"

    def test_legal_form_valid_four_digit(self):
        """Four-digit specific code (e.g., '0106' = Aktiengesellschaft)."""
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC", organisation_id="1",
            ),
            organisation_name="Test",
            legal_form="0106",
        )
        assert org.legal_form == "0106"

    def test_legal_form_invalid_letters(self):
        with pytest.raises(ValidationError, match="2-4 digits"):
            ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC", organisation_id="1",
                ),
                organisation_name="Test",
                legal_form="AG",
            )

    def test_legal_form_invalid_one_digit(self):
        with pytest.raises(ValidationError):
            ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC", organisation_id="1",
                ),
                organisation_name="Test",
                legal_form="1",
            )

    def test_legal_form_invalid_five_digits(self):
        with pytest.raises(ValidationError):
            ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC", organisation_id="1",
                ),
                organisation_name="Test",
                legal_form="12345",
            )

    def test_capital_o_in_other_organisation_id(self):
        """XSD uses capital 'O' in OtherOrganisationId element name."""
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC", organisation_id="1",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR", organisation_id="X",
                ),
            ],
            organisation_name="Test",
        )
        xml = org.to_xml()

        # Must be OtherOrganisationId (capital O), not otherOrganisationId
        other = xml.find(f'{{{NS_0097}}}OtherOrganisationId')
        assert other is not None, "Expected capital 'O' in OtherOrganisationId"

        # Lowercase must NOT exist
        other_lower = xml.find(f'{{{NS_0097}}}otherOrganisationId')
        assert other_lower is None

    def test_to_xml_minimal(self):
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123456",
            ),
            organisation_name="Minimal AG",
        )
        xml = org.to_xml()

        assert xml.tag == f'{{{NS_0097}}}organisationIdentification'

        # Required fields present
        local = xml.find(f'{{{NS_0097}}}localOrganisationId')
        assert local is not None
        name = xml.find(f'{{{NS_0097}}}organisationName')
        assert name is not None
        assert name.text == "Minimal AG"

        # Optional fields absent
        assert xml.find(f'{{{NS_0097}}}uid') is None
        assert xml.find(f'{{{NS_0097}}}OtherOrganisationId') is None
        assert xml.find(f'{{{NS_0097}}}organisationLegalName') is None
        assert xml.find(f'{{{NS_0097}}}organisationAdditionalName') is None
        assert xml.find(f'{{{NS_0097}}}legalForm') is None

    def test_to_xml_full(self):
        org = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123456",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR",
                    organisation_id="HR-001",
                ),
            ],
            organisation_name="Full AG",
            organisation_legal_name="Full Aktiengesellschaft",
            organisation_additional_name="Beratung",
            legal_form="0106",
        )
        xml = org.to_xml()

        # All fields present
        assert xml.find(f'{{{NS_0097}}}uid') is not None
        assert xml.find(f'{{{NS_0097}}}localOrganisationId') is not None
        assert xml.find(f'{{{NS_0097}}}OtherOrganisationId') is not None
        assert xml.find(f'{{{NS_0097}}}organisationName').text == "Full AG"
        assert xml.find(f'{{{NS_0097}}}organisationLegalName').text == "Full Aktiengesellschaft"
        assert xml.find(f'{{{NS_0097}}}organisationAdditionalName').text == "Beratung"
        assert xml.find(f'{{{NS_0097}}}legalForm').text == "0106"

    def test_from_xml_minimal(self):
        xml_str = f"""
        <organisationIdentification xmlns="{NS_0097}">
            <localOrganisationId>
                <organisationIdCategory>CH.BUR</organisationIdCategory>
                <organisationId>123456</organisationId>
            </localOrganisationId>
            <organisationName>Parsed AG</organisationName>
        </organisationIdentification>
        """
        elem = ET.fromstring(xml_str)
        org = ECH0097OrganisationIdentification.from_xml(elem)

        assert org.uid is None
        assert org.local_organisation_id.organisation_id_category == "CH.BUR"
        assert org.organisation_name == "Parsed AG"
        assert org.other_organisation_id == []

    def test_from_xml_full(self):
        xml_str = f"""
        <organisationIdentification xmlns="{NS_0097}">
            <uid>
                <uidOrganisationIdCategorie>CHE</uidOrganisationIdCategorie>
                <uidOrganisationId>109322551</uidOrganisationId>
            </uid>
            <localOrganisationId>
                <organisationIdCategory>CH.BUR</organisationIdCategory>
                <organisationId>123456</organisationId>
            </localOrganisationId>
            <OtherOrganisationId>
                <organisationIdCategory>CH.HR</organisationIdCategory>
                <organisationId>HR-001</organisationId>
            </OtherOrganisationId>
            <OtherOrganisationId>
                <organisationIdCategory>CH.MWST</organisationIdCategory>
                <organisationId>MWST-002</organisationId>
            </OtherOrganisationId>
            <organisationName>Full AG</organisationName>
            <organisationLegalName>Full Aktiengesellschaft</organisationLegalName>
            <organisationAdditionalName>Beratung</organisationAdditionalName>
            <legalForm>0106</legalForm>
        </organisationIdentification>
        """
        elem = ET.fromstring(xml_str)
        org = ECH0097OrganisationIdentification.from_xml(elem)

        assert org.uid.uid_organisation_id == 109322551
        assert org.uid.uid_organisation_id_categorie == UidOrganisationIdCategory.CHE
        assert org.local_organisation_id.organisation_id == "123456"
        assert len(org.other_organisation_id) == 2
        assert org.other_organisation_id[0].organisation_id_category == "CH.HR"
        assert org.other_organisation_id[1].organisation_id_category == "CH.MWST"
        assert org.organisation_name == "Full AG"
        assert org.organisation_legal_name == "Full Aktiengesellschaft"
        assert org.organisation_additional_name == "Beratung"
        assert org.legal_form == "0106"

    def test_from_xml_missing_required_name(self):
        xml_str = f"""
        <organisationIdentification xmlns="{NS_0097}">
            <localOrganisationId>
                <organisationIdCategory>LOC</organisationIdCategory>
                <organisationId>1</organisationId>
            </localOrganisationId>
        </organisationIdentification>
        """
        elem = ET.fromstring(xml_str)
        with pytest.raises(ValueError, match="Missing required field: organisationName"):
            ECH0097OrganisationIdentification.from_xml(elem)

    def test_roundtrip_minimal(self):
        original = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123456",
            ),
            organisation_name="Roundtrip AG",
        )
        xml = original.to_xml()
        restored = ECH0097OrganisationIdentification.from_xml(xml)

        assert restored.uid is None
        assert restored.local_organisation_id.organisation_id_category == "CH.BUR"
        assert restored.local_organisation_id.organisation_id == "123456"
        assert restored.organisation_name == "Roundtrip AG"
        assert restored.other_organisation_id == []

    def test_roundtrip_full(self):
        original = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="654321",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR",
                    organisation_id="HR-999",
                ),
            ],
            organisation_name="Roundtrip Full AG",
            organisation_legal_name="Roundtrip Full Aktiengesellschaft",
            organisation_additional_name="Immobilien",
            legal_form="0106",
        )
        xml = original.to_xml()
        restored = ECH0097OrganisationIdentification.from_xml(xml)

        assert restored.uid.uid_organisation_id == 109322551
        assert restored.uid.uid_organisation_id_categorie == UidOrganisationIdCategory.CHE
        assert restored.local_organisation_id.organisation_id == "654321"
        assert len(restored.other_organisation_id) == 1
        assert restored.other_organisation_id[0].organisation_id == "HR-999"
        assert restored.organisation_name == "Roundtrip Full AG"
        assert restored.organisation_legal_name == "Roundtrip Full Aktiengesellschaft"
        assert restored.organisation_additional_name == "Immobilien"
        assert restored.legal_form == "0106"


# --- Root element ---


class TestECH0097OrganisationIdentificationRoot:
    """Test root element wrapper."""

    def test_create(self):
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC",
                    organisation_id="1",
                ),
                organisation_name="Root Test",
            ),
        )
        assert root.organisation_identification.organisation_name == "Root Test"

    def test_to_xml(self):
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC",
                    organisation_id="1",
                ),
                organisation_name="Root Test",
            ),
        )
        xml = root.to_xml()

        assert xml.tag == f'{{{NS_0097}}}organisationIdentificationRoot'
        inner = xml.find(f'{{{NS_0097}}}organisationIdentification')
        assert inner is not None
        assert inner.find(f'{{{NS_0097}}}organisationName').text == "Root Test"

    def test_from_xml(self):
        xml_str = f"""
        <organisationIdentificationRoot xmlns="{NS_0097}">
            <organisationIdentification>
                <localOrganisationId>
                    <organisationIdCategory>LOC</organisationIdCategory>
                    <organisationId>1</organisationId>
                </localOrganisationId>
                <organisationName>Parsed Root</organisationName>
            </organisationIdentification>
        </organisationIdentificationRoot>
        """
        elem = ET.fromstring(xml_str)
        root = ECH0097OrganisationIdentificationRoot.from_xml(elem)

        assert root.organisation_identification.organisation_name == "Parsed Root"

    def test_roundtrip(self):
        original = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                uid=ECH0097UidStructure(
                    uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                    uid_organisation_id=109322551,
                ),
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="CH.BUR",
                    organisation_id="999",
                ),
                organisation_name="Roundtrip Root AG",
            ),
        )
        xml = original.to_xml()
        restored = ECH0097OrganisationIdentificationRoot.from_xml(xml)

        assert restored.organisation_identification.organisation_name == "Roundtrip Root AG"
        assert restored.organisation_identification.uid.uid_organisation_id == 109322551


# --- Real-world scenarios ---


class TestRealWorldScenarios:
    """Test real-world usage patterns."""

    def test_swiss_company_with_uid(self):
        """Typical Swiss AG with UID, BUR, HR, MWST identifiers."""
        org = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="87654321",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR",
                    organisation_id="CH-550.1.032.746-3",
                ),
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.MWST",
                    organisation_id="CHE109322551MWST",
                ),
            ],
            organisation_name="EnBAG Netze AG",
            organisation_legal_name="EnBAG Netze Aktiengesellschaft",
            legal_form="0106",
        )

        # Roundtrip
        xml = org.to_xml()
        restored = ECH0097OrganisationIdentification.from_xml(xml)

        assert restored.uid.uid_organisation_id == 109322551
        assert len(restored.other_organisation_id) == 2
        assert restored.legal_form == "0106"

    def test_municipal_administration(self):
        """Administrative unit (Gemeindeverwaltung) with ADM prefix."""
        org = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.ADM,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="MU.6172",
                organisation_id="1",
            ),
            organisation_name="Gemeindeverwaltung Bister",
            legal_form="0223",
        )

        assert org.uid.uid_organisation_id_categorie == UidOrganisationIdCategory.ADM
        assert org.legal_form == "0223"

    def test_foreign_company(self):
        """Foreign company — no UID, legalForm=0441."""
        org = ECH0097OrganisationIdentification(
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="LOC",
                organisation_id="foreign-001",
            ),
            organisation_name="Example GmbH Deutschland",
            legal_form="0441",
        )

        assert org.uid is None
        assert org.legal_form == "0441"

    def test_building_authority_context(self):
        """As used in eCH-0129 buildingAuthorityType."""
        authority = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.ADM,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="MU.6172",
                organisation_id="bauamt",
            ),
            organisation_name="Bauamt Bister",
            legal_form="0223",
        )

        # Serialize and verify structure for eCH-0129 consumption
        xml = authority.to_xml()
        assert xml.tag == f'{{{NS_0097}}}organisationIdentification'

        # eCH-0129 will embed this under buildingAuthorityIdentificationType
        parent = ET.Element('buildingAuthority')
        authority.to_xml(parent=parent, element_name='buildingAuthorityIdentificationType')

        child = parent.find(f'{{{NS_0097}}}buildingAuthorityIdentificationType')
        assert child is not None
