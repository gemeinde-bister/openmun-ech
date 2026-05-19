"""XSD Validation tests for eCH-0097 Organisation Identification models.

eCH-0097 has a root element (organisationIdentificationRoot), so we can
do full document-level XSD validation unlike library-only schemas.
"""

import xml.etree.ElementTree as ET

import pytest

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

from openmun_ech.ech0097 import (
    ECH0097NamedOrganisationId,
    ECH0097OrganisationIdentification,
    ECH0097OrganisationIdentificationRoot,
    ECH0097UidStructure,
    UidOrganisationIdCategory,
)
from openmun_ech.utils.schema_cache import get_cached_schema


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0097XSDValidation:
    """XSD validation tests for eCH-0097 models."""

    @pytest.fixture
    def schema(self):
        """Load eCH-0097 v2.0 XSD schema."""
        return get_cached_schema('eCH-0097-2-0.xsd')

    def test_root_minimal_valid(self, schema):
        """Minimal valid document: localOrganisationId + name."""
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="CH.BUR",
                    organisation_id="123456",
                ),
                organisation_name="Minimal AG",
            ),
        )
        xml = root.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        schema.validate(xml_str)

    def test_root_full_valid(self, schema):
        """Full document with all fields populated."""
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
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
                        organisation_id="HR-001",
                    ),
                    ECH0097NamedOrganisationId(
                        organisation_id_category="CH.MWST",
                        organisation_id="CHE109322551MWST",
                    ),
                ],
                organisation_name="Full AG",
                organisation_legal_name="Full Aktiengesellschaft",
                organisation_additional_name="Beratung und Treuhand",
                legal_form="0106",
            ),
        )
        xml = root.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        schema.validate(xml_str)

    def test_root_adm_category_valid(self, schema):
        """Administrative unit with ADM prefix."""
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
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
            ),
        )
        xml = root.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        schema.validate(xml_str)

    def test_root_multiple_other_ids_valid(self, schema):
        """Multiple OtherOrganisationId entries."""
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="CH.BUR",
                    organisation_id="111111",
                ),
                other_organisation_id=[
                    ECH0097NamedOrganisationId(
                        organisation_id_category="CH.HR",
                        organisation_id="HR-A",
                    ),
                    ECH0097NamedOrganisationId(
                        organisation_id_category="CH.MWST",
                        organisation_id="MWST-B",
                    ),
                    ECH0097NamedOrganisationId(
                        organisation_id_category="WW.GLN",
                        organisation_id="7612345678901",
                    ),
                ],
                organisation_name="Multi-ID AG",
            ),
        )
        xml = root.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        schema.validate(xml_str)


class TestECH0097ManualValidation:
    """Manual structure validation (no xmlschema required)."""

    def test_element_order_in_organisation_identification(self):
        """XSD sequence order: uid, localOrgId, OtherOrgId, name, legalName, additionalName, legalForm."""
        org = ECH0097OrganisationIdentification(
            uid=ECH0097UidStructure(
                uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                uid_organisation_id=109322551,
            ),
            local_organisation_id=ECH0097NamedOrganisationId(
                organisation_id_category="CH.BUR",
                organisation_id="123",
            ),
            other_organisation_id=[
                ECH0097NamedOrganisationId(
                    organisation_id_category="CH.HR",
                    organisation_id="HR-1",
                ),
            ],
            organisation_name="Order AG",
            organisation_legal_name="Order Aktiengesellschaft",
            organisation_additional_name="Beratung",
            legal_form="0106",
        )
        xml = org.to_xml()
        children = list(xml)

        expected_order = [
            'uid',
            'localOrganisationId',
            'OtherOrganisationId',
            'organisationName',
            'organisationLegalName',
            'organisationAdditionalName',
            'legalForm',
        ]

        ns = 'http://www.ech.ch/xmlns/eCH-0097/2'
        actual_order = [child.tag.replace(f'{{{ns}}}', '') for child in children]
        assert actual_order == expected_order

    def test_element_order_in_uid_structure(self):
        """XSD sequence: uidOrganisationIdCategorie, uidOrganisationId."""
        uid = ECH0097UidStructure(
            uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
            uid_organisation_id=109322551,
        )
        xml = uid.to_xml()
        children = list(xml)

        ns = 'http://www.ech.ch/xmlns/eCH-0097/2'
        assert children[0].tag == f'{{{ns}}}uidOrganisationIdCategorie'
        assert children[1].tag == f'{{{ns}}}uidOrganisationId'

    def test_namespace_correctness(self):
        """All elements use correct eCH-0097 namespace."""
        root = ECH0097OrganisationIdentificationRoot(
            organisation_identification=ECH0097OrganisationIdentification(
                uid=ECH0097UidStructure(
                    uid_organisation_id_categorie=UidOrganisationIdCategory.CHE,
                    uid_organisation_id=109322551,
                ),
                local_organisation_id=ECH0097NamedOrganisationId(
                    organisation_id_category="LOC",
                    organisation_id="1",
                ),
                organisation_name="NS Test",
            ),
        )
        xml = root.to_xml()

        expected_ns = 'http://www.ech.ch/xmlns/eCH-0097/2'

        def check_namespace(elem):
            if elem.tag.startswith('{'):
                ns = elem.tag[1:elem.tag.find('}')]
                assert ns == expected_ns, f"Wrong namespace on {elem.tag}: {ns}"
            for child in elem:
                check_namespace(child)

        check_namespace(xml)

    def test_double_roundtrip_stability(self):
        """XML output is deterministic across multiple roundtrips."""
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
                other_organisation_id=[
                    ECH0097NamedOrganisationId(
                        organisation_id_category="CH.HR",
                        organisation_id="HR-X",
                    ),
                ],
                organisation_name="Stability AG",
                organisation_legal_name="Stability Aktiengesellschaft",
                legal_form="0106",
            ),
        )

        # First roundtrip
        xml1 = original.to_xml()
        restored1 = ECH0097OrganisationIdentificationRoot.from_xml(xml1)

        # Second roundtrip
        xml2 = restored1.to_xml()
        restored2 = ECH0097OrganisationIdentificationRoot.from_xml(xml2)
        xml3 = restored2.to_xml()

        # XML output should be identical
        str1 = ET.tostring(xml1, encoding='unicode')
        str2 = ET.tostring(xml2, encoding='unicode')
        str3 = ET.tostring(xml3, encoding='unicode')

        assert str1 == str2 == str3
