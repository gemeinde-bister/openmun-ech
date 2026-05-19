"""eCH-0133 XSD validation tests.

Validates all 4 delivery message types against the official
eCH-0133-3-0.xsd schema.
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.ech0007.v6 import ECH0007v6SwissMunicipality
from openmun_ech.ech0058.v5 import ECH0058Header
from openmun_ech.ech0044.v4 import ECH0044PersonIdentificationLight
from openmun_ech.ech0129 import (
    ECH0129Area,
    ECH0129BuildingOnly,
    ECH0129EstimationObject,
    ECH0129FiscalOwnership,
    ECH0129PersonIdentification,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
    ECH0129Value,
)
from openmun_ech.ech0129.enums import (
    AreaDescriptionCode,
    AreaType,
    BuildingCategory,
    FiscalRelationship,
    RealestateType,
    TypeOfValue,
)
from openmun_ech.ech0133 import (
    ECH0133BuildingInfo,
    ECH0133Delivery,
    ECH0133EstBaseBldgRealestateInfo,
    ECH0133EstBaseBuildingInfo,
    ECH0133EstBaseRealestateInfo,
    ECH0133Estimation,
    ECH0133EstimationBaseDelivery,
    ECH0133EstimationInfo,
    ECH0133EstimationRealestateInfo,
    ECH0133FiscalOwnershipInfo,
    ECH0133OwnerOrBeneficiary,
    ECH0133RealestateBaseDelivery,
    ECH0133RealestateInfo,
)

try:
    from openmun_ech.utils.schema_cache import get_cached_schema
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------

def make_header() -> ECH0058Header:
    from datetime import datetime, timezone
    from openmun_ech.ech0058.v5 import ECH0058SendingApplication
    return ECH0058Header(
        sender_id="T4-123456-1",
        recipient_id=["T4-654321-1"],
        message_id="msg-xsd-001",
        message_type="0133",
        action="1",
        sending_application=ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Valreg-XSD-Test",
            product_version="1.0",
        ),
        message_date=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        test_delivery_flag=True,
    )


def make_realestate() -> ECH0129Realestate:
    return ECH0129Realestate(
        realestate_identification=ECH0129RealestateIdentification(
            egrid="CH123456789012",
            number="1234",
        ),
        realestate_type=RealestateType.LIEGENSCHAFT,
    )


def make_municipality() -> ECH0007v6SwissMunicipality:
    return ECH0007v6SwissMunicipality(
        municipality_id="6172",
        municipality_name="Bister",
    )


def make_fiscal_ownership_info() -> ECH0133FiscalOwnershipInfo:
    return ECH0133FiscalOwnershipInfo(
        fiscal_ownership=ECH0129FiscalOwnership(
            accession_date=date(2024, 1, 1),
            fiscal_relationship=FiscalRelationship.OWNER,
            denominator="1.000",
            numerator="1.000",
        ),
        person_identification=ECH0129PersonIdentification(
            individual=ECH0044PersonIdentificationLight(
                official_name="Müller",
                first_name="Hans",
            ),
        ),
    )


def make_area() -> ECH0129Area:
    return ECH0129Area(
        area_type=AreaType.GROUND_COVER,
        area_description_code=AreaDescriptionCode.GEBAEUDE,
        area_description="Wohngebaeude",
        area_value="450.00",
    )


def make_building_only() -> ECH0129BuildingOnly:
    return ECH0129BuildingOnly(
        building_category=BuildingCategory.RESIDENTIAL_ONLY,
    )


def make_estimation_object() -> ECH0129EstimationObject:
    from openmun_ech.ech0129 import ECH0129NamedId, ECH0129EstimationValue
    return ECH0129EstimationObject(
        local_id=ECH0129NamedId(id_category="SCH", id_value="001"),
        year_of_construction="2020",
        estimation_value=[
            ECH0129EstimationValue(
                local_id=ECH0129NamedId(id_category="VAL", id_value="001"),
                value=ECH0129Value(amount="500000.00"),
                type_of_value=TypeOfValue.TAX_VALUE,
            ),
        ],
    )


def make_building_info() -> ECH0133BuildingInfo:
    return ECH0133BuildingInfo(
        building=make_building_only(),
        estimation_object=[make_estimation_object()],
    )


# ---------------------------------------------------------------------------
# XSD validation tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0133XSDValidation:

    @pytest.fixture
    def schema(self):
        """Load eCH-0133 v3.0 XSD schema."""
        return get_cached_schema('eCH-0133-3-0.xsd')

    def test_owner_or_beneficiary_delivery(self, schema):
        """§4.2 ownerOrBeneficiary — validate against XSD."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            owner_or_beneficiary=ECH0133OwnerOrBeneficiary(
                realestate=make_realestate(),
                municipality=make_municipality(),
                fiscal_ownership_information=[make_fiscal_ownership_info()],
            ),
        )
        xml = delivery.to_xml()
        ET.indent(xml, space='  ')
        schema.validate(xml)

    def test_estimation_delivery(self, schema):
        """§4.3 estimation — validate against XSD."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            estimation=ECH0133Estimation(
                realestate_info=[
                    ECH0133EstimationRealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                        area=[make_area()],
                        estimation_object=make_estimation_object(),
                        building_information=[make_building_info()],
                    ),
                ],
            ),
        )
        xml = delivery.to_xml()
        ET.indent(xml, space='  ')
        schema.validate(xml)

    def test_realestate_base_delivery(self, schema):
        """§4.4.1.1 realestateBaseDelivery — validate against XSD."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            realestate_base_delivery=ECH0133RealestateBaseDelivery(
                realestate_information=[
                    ECH0133RealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                        area=[make_area()],
                        fiscal_ownership_information=[make_fiscal_ownership_info()],
                        estimation_object=make_estimation_object(),
                        building_information=[make_building_info()],
                    ),
                ],
            ),
        )
        xml = delivery.to_xml()
        ET.indent(xml, space='  ')
        schema.validate(xml)

    def test_estimation_base_delivery_realestate_branch(self, schema):
        """§4.4.1.2 estimationBaseDelivery (choice A: realestate) — validate against XSD."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            estimation_base_delivery=ECH0133EstimationBaseDelivery(
                estimation_information=[
                    ECH0133EstimationInfo(
                        estimation_object=make_estimation_object(),
                        realestate_information=ECH0133EstBaseRealestateInfo(
                            realestate=make_realestate(),
                            municipality=make_municipality(),
                            area=[make_area()],
                            fiscal_ownership_information=[make_fiscal_ownership_info()],
                            building=[make_building_only()],
                        ),
                    ),
                ],
            ),
        )
        xml = delivery.to_xml()
        ET.indent(xml, space='  ')
        schema.validate(xml)

    def test_estimation_base_delivery_building_branch(self, schema):
        """§4.4.1.2 estimationBaseDelivery (choice B: building) — validate against XSD."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            estimation_base_delivery=ECH0133EstimationBaseDelivery(
                estimation_information=[
                    ECH0133EstimationInfo(
                        estimation_object=make_estimation_object(),
                        building_information=[
                            ECH0133EstBaseBuildingInfo(
                                building=make_building_only(),
                                realestate_information=[
                                    ECH0133EstBaseBldgRealestateInfo(
                                        realestate=make_realestate(),
                                        municipality=make_municipality(),
                                        fiscal_ownership_information=[
                                            make_fiscal_ownership_info(),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )
        xml = delivery.to_xml()
        ET.indent(xml, space='  ')
        schema.validate(xml)

    def test_double_roundtrip_stability(self, schema):
        """Serialize → parse → serialize → validate — XML is stable."""
        delivery = ECH0133Delivery(
            delivery_header=make_header(),
            realestate_base_delivery=ECH0133RealestateBaseDelivery(
                realestate_information=[
                    ECH0133RealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                        area=[make_area()],
                        fiscal_ownership_information=[make_fiscal_ownership_info()],
                        estimation_object=make_estimation_object(),
                        building_information=[make_building_info()],
                    ),
                ],
            ),
        )

        # Pass 1
        xml1 = delivery.to_xml()
        xml_str1 = ET.tostring(xml1, encoding='unicode')
        schema.validate(xml1)

        # Parse back and re-serialize
        delivery2 = ECH0133Delivery.from_xml(xml1)
        xml2 = delivery2.to_xml()
        xml_str2 = ET.tostring(xml2, encoding='unicode')
        schema.validate(xml2)

        assert xml_str1 == xml_str2
