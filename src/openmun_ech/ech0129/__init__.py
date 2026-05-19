"""eCH-0129: Datenstandard Objektwesen (Property/Building Data).

Standard: eCH-0129 v6.0.0
Namespace: http://www.ech.ch/xmlns/eCH-0129/6
PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (114 pages)
XSD: eCH-0129-6-0.xsd (1854 lines, 177 named types)

Core data standard for Swiss property/building administration.
Defines entity types for buildings, dwellings, parcels, streets,
ownership, valuation, insurance, construction projects, etc.

Used by: eCH-0133 (Steuerregister), eCH-0134 (Grundbuch), and other
domain interfaces in the Objektwesen standard family.

Implementation: 60 ECHModel classes + 38 enum classes.
See docs/plans/ECH0129_IMPLEMENTATION_PLAN.md for session tracker.
"""

# --- ECHModel classes from v6/ submodules (60 classes) ---

from openmun_ech.ech0129.v6 import (
    # authority_person.py
    ECH0129BuildingAuthority,
    ECH0129BuildingAuthorityOnly,
    ECH0129Email,
    ECH0129IdentificationChoice,
    ECH0129Person,
    ECH0129PersonOnly,
    ECH0129Phone,
    # base_types.py
    ECH0129BuildingDate,
    ECH0129BuildingVolume,
    ECH0129Contact,
    ECH0129Coordinates,
    ECH0129DatePartiallyKnown,
    ECH0129DateRange,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129NamedId,
    ECH0129NamedMetaData,
    ECH0129PersonIdentification,
    # building.py
    ECH0129Building,
    ECH0129BuildingIdentification,
    ECH0129BuildingOnly,
    # cadastral.py
    ECH0129CadastralMap,
    ECH0129CadastralSurveyorRemark,
    ECH0129CoveringAreaOfSDR,
    ECH0129PartialAreaOfBuilding,
    ECH0129Right,
    # construction.py
    ECH0129ConstructionLocalisation,
    ECH0129ConstructionProject,
    ECH0129ConstructionProjectIdentification,
    ECH0129KindOfConstructionWork,
    # dwelling.py
    ECH0129Dwelling,
    ECH0129DwellingIdentification,
    ECH0129DwellingUsage,
    # entrance.py
    ECH0129AddressStreetDescription,
    ECH0129AddressStreetEntry,
    ECH0129BuildingAddress,
    ECH0129BuildingAddressLight,
    ECH0129BuildingEntrance,
    ECH0129BuildingEntranceIdentification,
    ECH0129BuildingEntranceOnly,
    # estimation.py
    ECH0129EstimationObject,
    ECH0129EstimationObjectOnly,
    ECH0129EstimationValue,
    ECH0129Value,
    # insurance.py
    ECH0129InsuranceObject,
    ECH0129InsuranceObjectOnly,
    ECH0129InsuranceSum,
    ECH0129InsuranceValue,
    ECH0129InsuranceVolume,
    # realestate.py
    ECH0129Area,
    ECH0129FiscalOwnership,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
    # street_locality.py
    ECH0129Locality,
    ECH0129LocalityName,
    ECH0129PlaceName,
    ECH0129Street,
    ECH0129StreetDescription,
    ECH0129StreetDescriptionEntry,
    ECH0129StreetSection,
)

# --- Enumerations from enums.py (38 classes) ---

from openmun_ech.ech0129.enums import (
    # Construction (§4.3)
    TypeOfConstructionProject,
    TypeOfPermit,
    ProjectStatus,
    TypeOfClient,
    TypeOfConstruction,
    KindOfWork,
    # Building (§4.5)
    PeriodOfConstruction,
    BuildingCategory,
    BuildingStatus,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    EnergySource,
    InformationSource,
    BuildingVolumeInformationSource,
    BuildingVolumeNorm,
    ThermotechnicalDeviceHeatingType,
    # Dwelling (§4.6)
    DwellingStatus,
    DwellingUsageCode,
    DwellingInformationSource,
    UsageLimitation,
    # Realestate (§4.8)
    RealestateType,
    RealestateStatus,
    # Area (§4.9)
    AreaType,
    AreaDescriptionCode,
    # Insurance/Estimation (§4.13-4.14)
    UsageCode,
    LocationCode,
    ChangeReason,
    TypeOfValue,
    # Street/Cadastral (§4.15-4.19)
    StreetKind,
    StreetStatus,
    StreetLanguage,
    NumberingType,
    PlaceNameType,
    RemarkType,
    # Contact (§4.22-4.23)
    PhoneCategory,
    EmailCategory,
    # Coordinates (§4.24)
    OriginOfCoordinates,
    # Fiscal ownership
    FiscalRelationship,
)

# No model_rebuild() needed — eCH-0129 types have no forward references.
# All cross-standard imports (eCH-0007, 0008, 0010, 0044, 0097) are resolved
# at import time in the v6/ submodules.

__all__ = [
    # ECHModel classes (sorted alphabetically)
    'ECH0129AddressStreetDescription',
    'ECH0129AddressStreetEntry',
    'ECH0129Area',
    'ECH0129Building',
    'ECH0129BuildingAddress',
    'ECH0129BuildingAddressLight',
    'ECH0129BuildingAuthority',
    'ECH0129BuildingAuthorityOnly',
    'ECH0129BuildingDate',
    'ECH0129BuildingEntrance',
    'ECH0129BuildingEntranceIdentification',
    'ECH0129BuildingEntranceOnly',
    'ECH0129BuildingIdentification',
    'ECH0129BuildingOnly',
    'ECH0129BuildingVolume',
    'ECH0129CadastralMap',
    'ECH0129CadastralSurveyorRemark',
    'ECH0129ConstructionLocalisation',
    'ECH0129ConstructionProject',
    'ECH0129ConstructionProjectIdentification',
    'ECH0129Contact',
    'ECH0129Coordinates',
    'ECH0129CoveringAreaOfSDR',
    'ECH0129DatePartiallyKnown',
    'ECH0129DateRange',
    'ECH0129Dwelling',
    'ECH0129DwellingIdentification',
    'ECH0129DwellingUsage',
    'ECH0129Email',
    'ECH0129EstimationObject',
    'ECH0129EstimationObjectOnly',
    'ECH0129EstimationValue',
    'ECH0129FiscalOwnership',
    'ECH0129Heating',
    'ECH0129HotWater',
    'ECH0129IdentificationChoice',
    'ECH0129InsuranceObject',
    'ECH0129InsuranceObjectOnly',
    'ECH0129InsuranceSum',
    'ECH0129InsuranceValue',
    'ECH0129InsuranceVolume',
    'ECH0129KindOfConstructionWork',
    'ECH0129Locality',
    'ECH0129LocalityName',
    'ECH0129NamedId',
    'ECH0129NamedMetaData',
    'ECH0129PartialAreaOfBuilding',
    'ECH0129Person',
    'ECH0129PersonIdentification',
    'ECH0129PersonOnly',
    'ECH0129Phone',
    'ECH0129PlaceName',
    'ECH0129Realestate',
    'ECH0129RealestateIdentification',
    'ECH0129Right',
    'ECH0129Street',
    'ECH0129StreetDescription',
    'ECH0129StreetDescriptionEntry',
    'ECH0129StreetSection',
    'ECH0129Value',
    # Enumerations (sorted alphabetically)
    'AreaDescriptionCode',
    'AreaType',
    'BuildingCategory',
    'BuildingStatus',
    'BuildingVolumeInformationSource',
    'BuildingVolumeNorm',
    'ChangeReason',
    'DwellingInformationSource',
    'DwellingStatus',
    'DwellingUsageCode',
    'EmailCategory',
    'EnergySource',
    'FiscalRelationship',
    'HeatGeneratorHeating',
    'HeatGeneratorHotWater',
    'InformationSource',
    'KindOfWork',
    'LocationCode',
    'NumberingType',
    'OriginOfCoordinates',
    'PeriodOfConstruction',
    'PhoneCategory',
    'PlaceNameType',
    'ProjectStatus',
    'RealestateStatus',
    'RealestateType',
    'RemarkType',
    'StreetKind',
    'StreetLanguage',
    'StreetStatus',
    'ThermotechnicalDeviceHeatingType',
    'TypeOfClient',
    'TypeOfConstruction',
    'TypeOfConstructionProject',
    'TypeOfPermit',
    'TypeOfValue',
    'UsageCode',
    'UsageLimitation',
]
