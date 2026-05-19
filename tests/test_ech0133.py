"""eCH-0133 Domäne Steuern — roundtrip and validation tests.

Tests construction, field validation, XML roundtrip, and xs:choice
enforcement for all 13 eCH-0133 classes.
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
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


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------

def make_realestate_id() -> ECH0129RealestateIdentification:
    return ECH0129RealestateIdentification(
        egrid="CH123456789012",
        number="1234",
    )


def make_realestate() -> ECH0129Realestate:
    return ECH0129Realestate(
        realestate_identification=make_realestate_id(),
        realestate_type=RealestateType.LIEGENSCHAFT,
    )


def make_municipality() -> ECH0007v6SwissMunicipality:
    return ECH0007v6SwissMunicipality(
        municipality_id="6172",
        municipality_name="Bister",
    )


def make_fiscal_ownership() -> ECH0129FiscalOwnership:
    return ECH0129FiscalOwnership(
        accession_date=date(2024, 1, 1),
        fiscal_relationship=FiscalRelationship.OWNER,
        denominator="1.000",
        numerator="1.000",
    )


def make_person_identification() -> ECH0129PersonIdentification:
    return ECH0129PersonIdentification(
        individual=ECH0044PersonIdentificationLight(
            official_name="Müller",
            first_name="Hans",
        ),
    )


def make_fiscal_ownership_info() -> ECH0133FiscalOwnershipInfo:
    return ECH0133FiscalOwnershipInfo(
        fiscal_ownership=make_fiscal_ownership(),
        person_identification=make_person_identification(),
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


def make_header() -> ECH0058Header:
    from datetime import datetime, timezone
    from openmun_ech.ech0058.v5 import ECH0058SendingApplication
    return ECH0058Header(
        sender_id="T4-123456-1",
        recipient_id=["T4-654321-1"],
        message_id="msg-001",
        message_type="0133",
        action="1",
        sending_application=ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Valreg-Test",
            product_version="1.0",
        ),
        message_date=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        test_delivery_flag=True,
    )


# ---------------------------------------------------------------------------
# Helper: XML roundtrip comparison
# ---------------------------------------------------------------------------

def assert_roundtrip(obj, cls=None):
    """Serialize to XML → parse back → serialize again → compare."""
    if cls is None:
        cls = type(obj)

    xml1 = obj.to_xml()
    xml_str1 = ET.tostring(xml1, encoding='unicode')

    obj2 = cls.from_xml(xml1)
    xml2 = obj2.to_xml()
    xml_str2 = ET.tostring(xml2, encoding='unicode')

    assert xml_str1 == xml_str2, (
        f"Roundtrip mismatch:\n  Pass 1: {xml_str1}\n  Pass 2: {xml_str2}"
    )
    return obj2


# ===========================================================================
# Shared helper types
# ===========================================================================

class TestFiscalOwnershipInfo:

    def test_construction(self):
        info = make_fiscal_ownership_info()
        assert info.fiscal_ownership.numerator == "1.000"
        assert info.person_identification.individual.official_name == "Müller"

    def test_roundtrip(self):
        assert_roundtrip(make_fiscal_ownership_info())

    def test_wrapper_namespaces(self):
        """Verify wrapper elements are in eCH-0133 ns, children in eCH-0129 ns."""
        info = make_fiscal_ownership_info()
        xml = info.to_xml()
        # Root element is in eCH-0133 namespace
        assert xml.tag == f'{{{NS.ECH0133_V3}}}fiscalOwnershipInformation'
        # First child (fiscalOwnership) is wrapper in eCH-0133 ns
        fo_elem = xml[0]
        assert fo_elem.tag == f'{{{NS.ECH0133_V3}}}fiscalOwnership'
        # Its children should be in eCH-0129 ns
        for child in fo_elem:
            assert NS.ECH0129_V6 in child.tag


class TestBuildingInfo:

    def test_construction(self):
        info = make_building_info()
        assert info.building.building_category == BuildingCategory.RESIDENTIAL_ONLY
        assert len(info.estimation_object) == 1

    def test_empty_estimation_objects(self):
        info = ECH0133BuildingInfo(building=make_building_only())
        assert info.estimation_object == []

    def test_roundtrip(self):
        assert_roundtrip(make_building_info())


# ===========================================================================
# §4.2 ownerOrBeneficiary
# ===========================================================================

class TestOwnerOrBeneficiary:

    def test_construction(self):
        oob = ECH0133OwnerOrBeneficiary(
            realestate=make_realestate(),
            municipality=make_municipality(),
            fiscal_ownership_information=[make_fiscal_ownership_info()],
        )
        assert len(oob.fiscal_ownership_information) == 1

    def test_multiple_owners(self):
        oob = ECH0133OwnerOrBeneficiary(
            realestate=make_realestate(),
            municipality=make_municipality(),
            fiscal_ownership_information=[
                make_fiscal_ownership_info(),
                make_fiscal_ownership_info(),
            ],
        )
        assert len(oob.fiscal_ownership_information) == 2

    def test_roundtrip(self):
        oob = ECH0133OwnerOrBeneficiary(
            realestate=make_realestate(),
            municipality=make_municipality(),
            fiscal_ownership_information=[make_fiscal_ownership_info()],
        )
        assert_roundtrip(oob)


# ===========================================================================
# §4.3 estimation
# ===========================================================================

class TestEstimationRealestateInfo:

    def test_minimal(self):
        info = ECH0133EstimationRealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
        )
        assert info.area == []
        assert info.estimation_object is None
        assert info.building_information == []

    def test_full(self):
        info = ECH0133EstimationRealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
            area=[make_area()],
            estimation_object=make_estimation_object(),
            building_information=[make_building_info()],
        )
        assert len(info.area) == 1
        assert info.estimation_object is not None
        assert len(info.building_information) == 1

    def test_roundtrip(self):
        info = ECH0133EstimationRealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
            area=[make_area()],
            estimation_object=make_estimation_object(),
            building_information=[make_building_info()],
        )
        assert_roundtrip(info)


class TestEstimation:

    def test_construction(self):
        est = ECH0133Estimation(
            realestate_info=[
                ECH0133EstimationRealestateInfo(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                ),
            ],
        )
        assert len(est.realestate_info) == 1

    def test_roundtrip(self):
        est = ECH0133Estimation(
            realestate_info=[
                ECH0133EstimationRealestateInfo(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                    estimation_object=make_estimation_object(),
                    building_information=[make_building_info()],
                ),
            ],
        )
        assert_roundtrip(est)


# ===========================================================================
# §4.4.1.1 realestateBaseDelivery
# ===========================================================================

class TestRealestateInfo:

    def test_minimal(self):
        info = ECH0133RealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
        )
        assert info.fiscal_ownership_information == []

    def test_full(self):
        info = ECH0133RealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
            area=[make_area()],
            fiscal_ownership_information=[make_fiscal_ownership_info()],
            estimation_object=make_estimation_object(),
            building_information=[make_building_info()],
        )
        assert len(info.fiscal_ownership_information) == 1

    def test_roundtrip(self):
        info = ECH0133RealestateInfo(
            realestate=make_realestate(),
            municipality=make_municipality(),
            area=[make_area()],
            fiscal_ownership_information=[make_fiscal_ownership_info()],
            estimation_object=make_estimation_object(),
            building_information=[make_building_info()],
        )
        assert_roundtrip(info)


class TestRealestateBaseDelivery:

    def test_construction(self):
        rbd = ECH0133RealestateBaseDelivery(
            realestate_information=[
                ECH0133RealestateInfo(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                ),
            ],
        )
        assert len(rbd.realestate_information) == 1

    def test_roundtrip(self):
        rbd = ECH0133RealestateBaseDelivery(
            realestate_information=[
                ECH0133RealestateInfo(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                    fiscal_ownership_information=[make_fiscal_ownership_info()],
                ),
            ],
        )
        assert_roundtrip(rbd)


# ===========================================================================
# §4.4.1.2 estimationBaseDelivery
# ===========================================================================

class TestEstimationInfo:

    def test_choice_realestate(self):
        info = ECH0133EstimationInfo(
            estimation_object=make_estimation_object(),
            realestate_information=ECH0133EstBaseRealestateInfo(
                realestate=make_realestate(),
                municipality=make_municipality(),
            ),
        )
        assert info.realestate_information is not None
        assert info.building_information == []

    def test_choice_building(self):
        info = ECH0133EstimationInfo(
            estimation_object=make_estimation_object(),
            building_information=[
                ECH0133EstBaseBuildingInfo(
                    building=make_building_only(),
                ),
            ],
        )
        assert info.realestate_information is None
        assert len(info.building_information) == 1

    def test_choice_neither_fails(self):
        with pytest.raises(ValueError, match="must set one of"):
            ECH0133EstimationInfo(
                estimation_object=make_estimation_object(),
            )

    def test_choice_both_fails(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            ECH0133EstimationInfo(
                estimation_object=make_estimation_object(),
                realestate_information=ECH0133EstBaseRealestateInfo(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                ),
                building_information=[
                    ECH0133EstBaseBuildingInfo(
                        building=make_building_only(),
                    ),
                ],
            )

    def test_roundtrip_realestate_branch(self):
        info = ECH0133EstimationInfo(
            estimation_object=make_estimation_object(),
            realestate_information=ECH0133EstBaseRealestateInfo(
                realestate=make_realestate(),
                municipality=make_municipality(),
                fiscal_ownership_information=[make_fiscal_ownership_info()],
                building=[make_building_only()],
            ),
        )
        assert_roundtrip(info)

    def test_roundtrip_building_branch(self):
        info = ECH0133EstimationInfo(
            estimation_object=make_estimation_object(),
            building_information=[
                ECH0133EstBaseBuildingInfo(
                    building=make_building_only(),
                    realestate_information=[
                        ECH0133EstBaseBldgRealestateInfo(
                            realestate=make_realestate(),
                            municipality=make_municipality(),
                        ),
                    ],
                ),
            ],
        )
        assert_roundtrip(info)


class TestEstimationBaseDelivery:

    def test_roundtrip(self):
        ebd = ECH0133EstimationBaseDelivery(
            estimation_information=[
                ECH0133EstimationInfo(
                    estimation_object=make_estimation_object(),
                    realestate_information=ECH0133EstBaseRealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                    ),
                ),
            ],
        )
        assert_roundtrip(ebd)


# ===========================================================================
# Root delivery
# ===========================================================================

class TestDelivery:

    def test_choice_owner_or_beneficiary(self):
        d = ECH0133Delivery(
            delivery_header=make_header(),
            owner_or_beneficiary=ECH0133OwnerOrBeneficiary(
                realestate=make_realestate(),
                municipality=make_municipality(),
                fiscal_ownership_information=[make_fiscal_ownership_info()],
            ),
        )
        assert d.owner_or_beneficiary is not None
        assert d.estimation is None

    def test_choice_estimation(self):
        d = ECH0133Delivery(
            delivery_header=make_header(),
            estimation=ECH0133Estimation(
                realestate_info=[
                    ECH0133EstimationRealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                    ),
                ],
            ),
        )
        assert d.estimation is not None

    def test_choice_none_fails(self):
        with pytest.raises(ValueError, match="must set one of"):
            ECH0133Delivery(delivery_header=make_header())

    def test_choice_multiple_fails(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            ECH0133Delivery(
                delivery_header=make_header(),
                owner_or_beneficiary=ECH0133OwnerOrBeneficiary(
                    realestate=make_realestate(),
                    municipality=make_municipality(),
                    fiscal_ownership_information=[make_fiscal_ownership_info()],
                ),
                estimation=ECH0133Estimation(
                    realestate_info=[
                        ECH0133EstimationRealestateInfo(
                            realestate=make_realestate(),
                            municipality=make_municipality(),
                        ),
                    ],
                ),
            )

    def test_roundtrip_owner_or_beneficiary(self):
        d = ECH0133Delivery(
            delivery_header=make_header(),
            owner_or_beneficiary=ECH0133OwnerOrBeneficiary(
                realestate=make_realestate(),
                municipality=make_municipality(),
                fiscal_ownership_information=[make_fiscal_ownership_info()],
            ),
        )
        assert_roundtrip(d)

    def test_roundtrip_estimation(self):
        d = ECH0133Delivery(
            delivery_header=make_header(),
            estimation=ECH0133Estimation(
                realestate_info=[
                    ECH0133EstimationRealestateInfo(
                        realestate=make_realestate(),
                        municipality=make_municipality(),
                        estimation_object=make_estimation_object(),
                        building_information=[make_building_info()],
                    ),
                ],
            ),
        )
        assert_roundtrip(d)

    def test_roundtrip_realestate_base_delivery(self):
        d = ECH0133Delivery(
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
        assert_roundtrip(d)

    def test_roundtrip_estimation_base_delivery(self):
        d = ECH0133Delivery(
            delivery_header=make_header(),
            estimation_base_delivery=ECH0133EstimationBaseDelivery(
                estimation_information=[
                    ECH0133EstimationInfo(
                        estimation_object=make_estimation_object(),
                        realestate_information=ECH0133EstBaseRealestateInfo(
                            realestate=make_realestate(),
                            municipality=make_municipality(),
                            fiscal_ownership_information=[make_fiscal_ownership_info()],
                            building=[make_building_only()],
                        ),
                    ),
                ],
            ),
        )
        assert_roundtrip(d)

    def test_header_namespace(self):
        """Verify deliveryHeader wrapper is in eCH-0133 ns, content in eCH-0058."""
        d = ECH0133Delivery(
            delivery_header=make_header(),
            owner_or_beneficiary=ECH0133OwnerOrBeneficiary(
                realestate=make_realestate(),
                municipality=make_municipality(),
                fiscal_ownership_information=[make_fiscal_ownership_info()],
            ),
        )
        xml = d.to_xml()
        # Root: eCH-0133 namespace
        assert xml.tag == f'{{{NS.ECH0133_V3}}}delivery'
        # First child: deliveryHeader in eCH-0133 ns
        header_elem = xml[0]
        assert header_elem.tag == f'{{{NS.ECH0133_V3}}}deliveryHeader'
        # Header children: eCH-0058 ns
        for child in header_elem:
            assert NS.ECH0058_V5 in child.tag
