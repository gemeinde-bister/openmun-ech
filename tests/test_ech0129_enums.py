"""Tests for eCH-0129 v6.0.0 enumerations.

Verifies:
1. Value coverage — every XSD enum value is present
2. String coercion — values are usable as strings
3. Invalid rejection — non-existent values raise ValueError
4. No duplicates — each value is unique within its enum
5. Correct count — enum has expected number of members
"""

import pytest

from openmun_ech.ech0129.enums import (
    AreaDescriptionCode,
    AreaType,
    BuildingCategory,
    BuildingStatus,
    BuildingVolumeInformationSource,
    BuildingVolumeNorm,
    ChangeReason,
    DwellingInformationSource,
    DwellingStatus,
    DwellingUsageCode,
    EmailCategory,
    EnergySource,
    FiscalRelationship,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    InformationSource,
    KindOfWork,
    LocationCode,
    NumberingType,
    OriginOfCoordinates,
    PeriodOfConstruction,
    PhoneCategory,
    PlaceNameType,
    ProjectStatus,
    RealestateStatus,
    RealestateType,
    RemarkType,
    StreetKind,
    StreetLanguage,
    StreetStatus,
    ThermotechnicalDeviceHeatingType,
    TypeOfClient,
    TypeOfConstruction,
    TypeOfConstructionProject,
    TypeOfPermit,
    TypeOfValue,
    UsageCode,
    UsageLimitation,
)


# ---------------------------------------------------------------------------
# Value coverage — every XSD enumeration value is present
# ---------------------------------------------------------------------------

# Maps: (EnumClass, expected_values_from_xsd)
ENUM_VALUE_TABLE = [
    (TypeOfConstructionProject, ["6010", "6011", "6012"]),
    (TypeOfPermit, [
        "5000", "5001", "5002", "5003", "5004", "5005", "5006", "5007",
        "5008", "5009", "5011", "5012", "5015", "5021", "5022", "5023",
        "5031", "5041", "5043", "5044", "5051", "5061", "5062", "5063",
        "5064", "5071",
    ]),
    (ProjectStatus, [
        "6701", "6702", "6703", "6704", "6706", "6707", "6708", "6709",
    ]),
    (TypeOfClient, [
        "6101", "6103", "6104", "6107", "6108", "6110", "6111", "6115",
        "6116", "6121", "6122", "6123", "6124", "6131", "6132", "6133",
        "6141", "6142", "6143", "6161", "6151", "6152", "6162", "6163",
    ]),
    (TypeOfConstruction, [
        "6211", "6212", "6213", "6214", "6219",
        "6221", "6222", "6223",
        "6231", "6232", "6233", "6234", "6235",
        "6241", "6242", "6243", "6244", "6245", "6249",
        "6251", "6252", "6253", "6254", "6255", "6256", "6257", "6258", "6259",
        "6261", "6262", "6269",
        "6271", "6272", "6273", "6274", "6276", "6278", "6279",
        "6281", "6282", "6283",
        "6291", "6292", "6293", "6294", "6295", "6296", "6299",
    ]),
    (KindOfWork, ["6001", "6002", "6007"]),
    (PeriodOfConstruction, [
        "8011", "8012", "8013", "8014", "8015", "8016", "8017",
        "8018", "8019", "8020", "8021", "8022", "8023",
    ]),
    (BuildingCategory, ["1010", "1020", "1030", "1040", "1060", "1080"]),
    (BuildingStatus, [
        "1001", "1002", "1003", "1004", "1005", "1007", "1008", "1009",
    ]),
    (HeatGeneratorHeating, [
        "7400", "7410", "7411", "7420", "7421",
        "7430", "7431", "7432", "7433", "7434", "7435", "7436",
        "7440", "7441", "7450", "7451", "7452", "7460", "7461", "7499",
    ]),
    (HeatGeneratorHotWater, [
        "7600", "7610", "7620", "7630", "7632", "7634",
        "7640", "7650", "7651", "7660", "7699",
    ]),
    (EnergySource, [
        "7500", "7501", "7510", "7511", "7512", "7513",
        "7520", "7530", "7540", "7541", "7542", "7543",
        "7550", "7560", "7570", "7580", "7581", "7582", "7598", "7599",
    ]),
    (InformationSource, [
        "852", "853", "855", "857", "858", "859",
        "860", "864", "865", "869", "870", "871",
    ]),
    (BuildingVolumeInformationSource, [
        "869", "858", "853", "852", "857", "851", "870", "878", "859",
    ]),
    (BuildingVolumeNorm, ["961", "962", "969"]),
    (ThermotechnicalDeviceHeatingType, ["7701", "7702", "7703"]),
    (DwellingStatus, [
        "3001", "3002", "3003", "3004", "3005", "3007", "3008", "3009",
    ]),
    (DwellingUsageCode, [
        "3010", "3020", "3030", "3031", "3032", "3033",
        "3034", "3035", "3036", "3037", "3038", "3070",
    ]),
    (DwellingInformationSource, ["3090", "3091", "3092", "3093"]),
    (UsageLimitation, ["3401", "3402", "3403", "3404"]),
    (RealestateType, ["1", "2", "3", "4", "5", "6", "7", "8"]),
    (RealestateStatus, ["0", "1"]),
    (AreaType, ["1", "2", "3"]),
    (AreaDescriptionCode, [str(i) for i in range(26)]),
    (UsageCode, [
        "1199", "1219", "1220", "1230", "1241", "1242", "1252", "1259",
        "1263", "1264", "1265", "1269", "1271", "1272", "1274",
    ]),
    (LocationCode, ["0", "1", "2", "3", "4", "5", "6"]),
    (ChangeReason, ["1001", "1002", "1003", "1004", "1005", "1006"]),
    (TypeOfValue, [
        "1007",
        "2001", "2002", "2003", "2004", "2005", "2006", "2007",
        "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016",
        "9000", "9001", "9002", "9003",
    ]),
    (StreetKind, ["9801", "9802", "9803"]),
    (StreetStatus, ["9811", "9812", "9813", "9814"]),
    (StreetLanguage, ["9901", "9902", "9903", "9904"]),
    (NumberingType, ["9830", "9832", "9835", "9836", "9837", "9839"]),
    (PlaceNameType, ["0", "1", "2", "3"]),
    (RemarkType, ["1", "2", "3", "4", "5", "6"]),
    (PhoneCategory, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]),
    (EmailCategory, ["1", "2"]),
    (OriginOfCoordinates, ["901", "902", "903", "904", "905", "906", "909"]),
    (FiscalRelationship, ["1", "2", "3"]),
]


@pytest.mark.parametrize("enum_cls, expected_values", ENUM_VALUE_TABLE,
                         ids=[cls.__name__ for cls, _ in ENUM_VALUE_TABLE])
def test_value_coverage(enum_cls, expected_values):
    """Every XSD enumeration value must be present in the Python enum."""
    actual_values = {m.value for m in enum_cls}
    expected_set = set(expected_values)
    missing = expected_set - actual_values
    extra = actual_values - expected_set
    assert not missing, f"{enum_cls.__name__}: missing values {missing}"
    assert not extra, f"{enum_cls.__name__}: unexpected extra values {extra}"


@pytest.mark.parametrize("enum_cls, expected_values", ENUM_VALUE_TABLE,
                         ids=[cls.__name__ for cls, _ in ENUM_VALUE_TABLE])
def test_member_count(enum_cls, expected_values):
    """Enum must have exactly as many members as XSD enumeration values."""
    assert len(enum_cls) == len(expected_values), (
        f"{enum_cls.__name__}: expected {len(expected_values)} members, "
        f"got {len(enum_cls)}"
    )


# ---------------------------------------------------------------------------
# String coercion
# ---------------------------------------------------------------------------

def test_string_coercion():
    """Enum values must be usable as plain strings."""
    assert str(BuildingCategory.RESIDENTIAL_ONLY) == "BuildingCategory.RESIDENTIAL_ONLY"
    assert BuildingCategory.RESIDENTIAL_ONLY.value == "1020"
    assert BuildingCategory.RESIDENTIAL_ONLY == "1020"
    assert BuildingCategory.SPECIAL.value == "1080"


def test_string_comparison():
    """Enum members must compare equal to their string value."""
    assert ProjectStatus.COMPLETED == "6704"
    assert EnergySource.GAS == "7520"
    assert RealestateType.LIEGENSCHAFT == "1"
    assert OriginOfCoordinates.BFS == "905"


# ---------------------------------------------------------------------------
# Lookup by value
# ---------------------------------------------------------------------------

def test_lookup_by_value():
    """Enum(value) must return the correct member."""
    assert BuildingStatus("1004") is BuildingStatus.EXISTING
    assert HeatGeneratorHeating("7436") is HeatGeneratorHeating.STOVE
    assert DwellingUsageCode("3070") is DwellingUsageCode.UNINHABITABLE
    assert TypeOfConstruction("6273") is TypeOfConstruction.MEHRFAMILIENHAEUSER
    assert PhoneCategory("10") is PhoneCategory.PAGER


def test_invalid_value_raises():
    """Non-existent values must raise ValueError."""
    with pytest.raises(ValueError):
        BuildingCategory("9999")
    with pytest.raises(ValueError):
        ProjectStatus("6705")  # gap in sequence (6704, 6706)
    with pytest.raises(ValueError):
        DwellingStatus("3006")  # gap in sequence (3005, 3007)
    with pytest.raises(ValueError):
        BuildingStatus("1006")  # gap in sequence (1005, 1007)


# ---------------------------------------------------------------------------
# No duplicate values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("enum_cls, _", ENUM_VALUE_TABLE,
                         ids=[cls.__name__ for cls, _ in ENUM_VALUE_TABLE])
def test_no_duplicate_values(enum_cls, _):
    """No two enum members may share the same value."""
    values = [m.value for m in enum_cls]
    assert len(values) == len(set(values)), (
        f"{enum_cls.__name__}: duplicate values detected"
    )


# ---------------------------------------------------------------------------
# Specific domain checks
# ---------------------------------------------------------------------------

def test_construction_type_count():
    """TypeOfConstruction has 48 values per XSD (largest enum)."""
    assert len(TypeOfConstruction) == 48


def test_type_of_permit_count():
    """TypeOfPermit has 26 values per XSD."""
    assert len(TypeOfPermit) == 26


def test_type_of_client_count():
    """TypeOfClient has 24 values per XSD."""
    assert len(TypeOfClient) == 24


def test_heat_generator_heating_count():
    """HeatGeneratorHeating has 20 values per XSD."""
    assert len(HeatGeneratorHeating) == 20


def test_area_description_code_full_range():
    """AreaDescriptionCode covers 0-25 inclusive (26 values)."""
    assert len(AreaDescriptionCode) == 26
    assert AreaDescriptionCode("0") is AreaDescriptionCode.GEBAEUDE
    assert AreaDescriptionCode("25") is AreaDescriptionCode.UEBRIGE_VEGETATIONSLOSE


def test_type_of_value_count():
    """TypeOfValue has 21 values per XSD."""
    assert len(TypeOfValue) == 21


def test_information_source_count():
    """InformationSource has 12 values per XSD."""
    assert len(InformationSource) == 12


def test_building_volume_information_source_count():
    """BuildingVolumeInformationSource has 9 values per XSD."""
    assert len(BuildingVolumeInformationSource) == 9


def test_period_of_construction_count():
    """PeriodOfConstruction has 13 values (8011-8023)."""
    assert len(PeriodOfConstruction) == 13


def test_fiscal_relationship_is_inline_enum():
    """FiscalRelationship is an inline enum inside fiscalOwnershipType."""
    assert FiscalRelationship.OWNER == "1"
    assert FiscalRelationship.USUFRUCTUARY == "2"
    assert FiscalRelationship.RESIDENTIAL_RIGHT == "3"
    assert len(FiscalRelationship) == 3
