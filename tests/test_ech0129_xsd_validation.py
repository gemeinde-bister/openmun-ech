"""XSD validation and double roundtrip tests for eCH-0129 v6.0.0.

Validates all 20 root element declarations against the official XSD.
Also tests double-roundtrip stability (serialize → parse → serialize → compare).
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

from openmun_ech.ech0129 import (
    AreaDescriptionCode,
    AreaType,
    BuildingCategory,
    BuildingStatus,
    BuildingVolumeNorm,
    ChangeReason,
    DwellingStatus,
    DwellingUsageCode,
    FiscalRelationship,
    KindOfWork,
    OriginOfCoordinates,
    PlaceNameType,
    ProjectStatus,
    RealestateType,
    RemarkType,
    StreetKind,
    StreetLanguage,
    StreetStatus,
    TypeOfValue,
    ECH0129Area,
    ECH0129Building,
    ECH0129BuildingDate,
    ECH0129BuildingEntrance,
    ECH0129BuildingEntranceOnly,
    ECH0129BuildingOnly,
    ECH0129CadastralMap,
    ECH0129CadastralSurveyorRemark,
    ECH0129ConstructionProject,
    ECH0129ConstructionProjectIdentification,
    ECH0129Coordinates,
    ECH0129CoveringAreaOfSDR,
    ECH0129Dwelling,
    ECH0129DwellingUsage,
    ECH0129EstimationObject,
    ECH0129EstimationValue,
    ECH0129FiscalOwnership,
    ECH0129Heating,
    ECH0129InsuranceObject,
    ECH0129InsuranceSum,
    ECH0129InsuranceValue,
    ECH0129InsuranceVolume,
    ECH0129KindOfConstructionWork,
    ECH0129Locality,
    ECH0129LocalityName,
    ECH0129NamedId,
    ECH0129PartialAreaOfBuilding,
    ECH0129PlaceName,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
    ECH0129Right,
    ECH0129Street,
    ECH0129StreetDescription,
    ECH0129StreetDescriptionEntry,
    ECH0129StreetSection,
    ECH0129Value,
)
from openmun_ech.ech0129.enums import EnergySource
from openmun_ech.utils.schema_cache import get_cached_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_named_id(category: str = "MU.6172", value: str = "1") -> ECH0129NamedId:
    return ECH0129NamedId(id_category=category, id_value=value)


def make_realestate_id() -> ECH0129RealestateIdentification:
    return ECH0129RealestateIdentification(
        egrid="CH123456789012",
        number="1234",
    )


def make_street_section() -> ECH0129StreetSection:
    return ECH0129StreetSection(
        esid=10000001,
        swiss_zip_code=3983,
        swiss_zip_code_add_on="00",
    )


# ---------------------------------------------------------------------------
# Root element builders — one per XSD root element declaration
# ---------------------------------------------------------------------------

ROOT_BUILDERS: dict[str, callable] = {}


def _register(name: str):
    def decorator(fn):
        ROOT_BUILDERS[name] = fn
        return fn
    return decorator


@_register('constructionProject')
def _build_construction_project():
    return ECH0129ConstructionProject(
        construction_project_identification=ECH0129ConstructionProjectIdentification(
            local_id=[make_named_id("BAU", "2024-001")],
        ),
        status=ProjectStatus.CONSTRUCTION_STARTED,
        description="Neubau Einfamilienhaus",
    )


@_register('building')
def _build_building():
    return ECH0129Building(
        building_category=BuildingCategory.RESIDENTIAL_ONLY,
        egid=123456789,
        status=BuildingStatus.EXISTING,
        number_of_floors=2,
        date_of_construction=ECH0129BuildingDate(year_month_day=date(1990, 1, 1)),
        heating=[
            ECH0129Heating(
                heat_generator_heating="7411",
                energy_source_heating=EnergySource.AIR,
            ),
        ],
        building_entrance=[
            ECH0129BuildingEntrance(
                local_id=make_named_id("ENTR", "1"),
                street_section=make_street_section(),
            ),
        ],
    )


@_register('buildingOnly')
def _build_building_only():
    return ECH0129BuildingOnly(
        building_category=BuildingCategory.NON_RESIDENTIAL,
    )


@_register('buildingEntrance')
def _build_building_entrance():
    return ECH0129BuildingEntrance(
        local_id=make_named_id("ENTR", "1"),
        street_section=make_street_section(),
    )


@_register('buildingEntranceOnly')
def _build_building_entrance_only():
    return ECH0129BuildingEntranceOnly(
        local_id=make_named_id("ENTR", "1"),
    )


@_register('dwelling')
def _build_dwelling():
    return ECH0129Dwelling(
        local_id=[make_named_id("WHNG", "1")],
        ewid=1,
        no_of_habitable_rooms=3,
        floor=3100,
        kitchen=True,
        status=DwellingStatus.EXISTING,
        dwelling_usage=ECH0129DwellingUsage(
            usage_code=DwellingUsageCode.MAIN_RESIDENCE,
        ),
    )


@_register('realestate')
def _build_realestate():
    return ECH0129Realestate(
        realestate_identification=make_realestate_id(),
        realestate_type=RealestateType.LIEGENSCHAFT,
        coordinates=ECH0129Coordinates(
            east="2634000.000",
            north="1128000.000",
            origin_of_coordinates=OriginOfCoordinates.BUILDING_APPLICATION,
        ),
    )


@_register('locality')
def _build_locality():
    return ECH0129Locality(
        swiss_zip_code=3983,
        swiss_zip_code_add_on="00",
        name=ECH0129LocalityName(
            name_long="Bister",
            name_short="Bister",
        ),
    )


@_register('fiscalOwnership')
def _build_fiscal_ownership():
    return ECH0129FiscalOwnership(
        accession_date=date(2024, 1, 1),
        fiscal_relationship=FiscalRelationship.OWNER,
        denominator="1.000",
        numerator="1.000",
    )


@_register('area')
def _build_area():
    return ECH0129Area(
        area_type=AreaType.GROUND_COVER,
        area_description_code=AreaDescriptionCode.GEBAEUDE,
        area_description="Wohngebaeude",
        area_value="450.00",
    )


@_register('insuranceObject')
def _build_insurance_object():
    return ECH0129InsuranceObject(
        local_id=make_named_id("GVA", "VS-001"),
        insurance_number="VS-001",
        insurance_value=ECH0129InsuranceValue(
            local_id=make_named_id("VW", "001"),
            valid_from=date(2024, 1, 1),
            change_reason=ChangeReason.NEW_VALUE,
            insurance_sum=ECH0129InsuranceSum(amount="500000.00"),
        ),
        volume=ECH0129InsuranceVolume(
            volume=800,
            norm=BuildingVolumeNorm.SIA_416,
        ),
    )


@_register('street')
def _build_street():
    return ECH0129Street(
        esid=10000001,
        street_kind=StreetKind.STREET,
        description=ECH0129StreetDescription(
            entries=[
                ECH0129StreetDescriptionEntry(
                    language=StreetLanguage.GERMAN,
                    description_long="Dorfstrasse",
                )
            ]
        ),
        street_status=StreetStatus.EXISTING,
    )


@_register('right')
def _build_right():
    return ECH0129Right(ereid="EREID-001")


@_register('cadastralMap')
def _build_cadastral_map():
    return ECH0129CadastralMap(
        map_number="1234",
        ident_dn="DN-001",
    )


@_register('cadastralSurveyorRemark')
def _build_cadastral_surveyor_remark():
    return ECH0129CadastralSurveyorRemark(
        remark_type=RemarkType.OTHER,
        remark_text="Test remark",
        object_id="OBJ-001",
    )


@_register('placeName')
def _build_place_name():
    return ECH0129PlaceName(
        place_name_type=PlaceNameType.ORTSNAME,
        local_geographical_name="Bister",
    )


@_register('coveringAreaOfSDR')
def _build_covering_area_of_sdr():
    return ECH0129CoveringAreaOfSDR(
        square_measure="500.00",
        realestate_identification=make_realestate_id(),
    )


@_register('partialAreaOfBuilding')
def _build_partial_area_of_building():
    return ECH0129PartialAreaOfBuilding(
        square_measure="120.50",
    )


@_register('kindOfConstructionWork')
def _build_kind_of_construction_work():
    return ECH0129KindOfConstructionWork(
        kind_of_work=KindOfWork.NEW_CONSTRUCTION,
        energetic_restauration=True,
    )


@_register('estimationObject')
def _build_estimation_object():
    return ECH0129EstimationObject(
        local_id=make_named_id("SCHT", "001"),
        volume=500,
        year_of_construction="1985",
        description="Einfamilienhaus",
        estimation_value=[
            ECH0129EstimationValue(
                local_id=make_named_id("SW", "001"),
                value=ECH0129Value(amount="250000.00"),
                type_of_value=TypeOfValue.TAX_VALUE,
            ),
        ],
    )


# Verify all 20 root elements are registered
_EXPECTED_ROOT_ELEMENTS = [
    'constructionProject', 'building', 'buildingOnly',
    'buildingEntrance', 'buildingEntranceOnly', 'dwelling',
    'realestate', 'locality', 'fiscalOwnership', 'area',
    'insuranceObject', 'street', 'right', 'cadastralMap',
    'cadastralSurveyorRemark', 'placeName', 'coveringAreaOfSDR',
    'partialAreaOfBuilding', 'kindOfConstructionWork', 'estimationObject',
]

assert set(ROOT_BUILDERS.keys()) == set(_EXPECTED_ROOT_ELEMENTS), (
    f"Missing: {set(_EXPECTED_ROOT_ELEMENTS) - set(ROOT_BUILDERS.keys())}, "
    f"Extra: {set(ROOT_BUILDERS.keys()) - set(_EXPECTED_ROOT_ELEMENTS)}"
)


# ---------------------------------------------------------------------------
# XSD Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0129XSDValidation:
    """Validate all 20 root elements against the official eCH-0129 v6.0.0 XSD."""

    @pytest.fixture(scope='class')
    def schema(self):
        return get_cached_schema('eCH-0129-6-0.xsd')

    @pytest.mark.parametrize('element_name', _EXPECTED_ROOT_ELEMENTS)
    def test_root_element_validates(self, schema, element_name):
        """Each root element must produce XSD-valid XML."""
        obj = ROOT_BUILDERS[element_name]()
        xml = obj.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        schema.validate(xml_str)


# ---------------------------------------------------------------------------
# Double Roundtrip Stability Tests
# ---------------------------------------------------------------------------

class TestDoubleRoundtripStability:
    """Verify serialize → parse → serialize → parse → serialize is stable."""

    @pytest.mark.parametrize('element_name', _EXPECTED_ROOT_ELEMENTS)
    def test_double_roundtrip(self, element_name):
        """XML output is deterministic across two roundtrips."""
        obj = ROOT_BUILDERS[element_name]()
        model_class = type(obj)

        # First roundtrip
        xml1 = obj.to_xml()
        str1 = ET.tostring(xml1, encoding='unicode')
        restored1 = model_class.from_xml(xml1)

        # Second roundtrip
        xml2 = restored1.to_xml()
        str2 = ET.tostring(xml2, encoding='unicode')
        restored2 = model_class.from_xml(xml2)

        # Third serialization
        xml3 = restored2.to_xml()
        str3 = ET.tostring(xml3, encoding='unicode')

        assert str1 == str2, (
            f"Roundtrip 1 mismatch for {element_name}:\n"
            f"  Original: {str1}\n"
            f"  After RT: {str2}"
        )
        assert str2 == str3, (
            f"Roundtrip 2 mismatch for {element_name}:\n"
            f"  RT1: {str2}\n"
            f"  RT2: {str3}"
        )


# ---------------------------------------------------------------------------
# Namespace correctness
# ---------------------------------------------------------------------------

class TestNamespaceCorrectness:
    """All root-level elements use the correct eCH-0129 v6 namespace."""

    ECH0129_NS = 'http://www.ech.ch/xmlns/eCH-0129/6'

    @pytest.mark.parametrize('element_name', _EXPECTED_ROOT_ELEMENTS)
    def test_root_namespace(self, element_name):
        """Root element tag uses eCH-0129 v6 namespace."""
        obj = ROOT_BUILDERS[element_name]()
        xml = obj.to_xml()
        ns, local = xml.tag[1:].split('}', 1)
        assert ns == self.ECH0129_NS, (
            f"Root element '{element_name}' has namespace '{ns}', "
            f"expected '{self.ECH0129_NS}'"
        )
        assert local == element_name, (
            f"Root element local name is '{local}', expected '{element_name}'"
        )
