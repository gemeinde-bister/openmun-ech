"""eCH-0021 Person Additional Data.

This package provides Pydantic models for eCH-0021 (Person Additional Data).

Available versions:
- v7: eCH-0021 v7.0 (required for eCH-0020 v3.0 compatibility)
- v8: eCH-0021 v8.0 (current stable version, default)

Default import is from v8 (current stable version).

Version differences:
- v7 includes politicalRightDataType (removed in v8)
- v8 includes addressLockType (not in v7)
- All other types identical (97% code reuse)

Usage:
    # Default (v8)
    from openmun_ech.ech0021 import ECH0021PersonAdditionalData

    # Explicit v7 (for eCH-0020 v3.0)
    from openmun_ech.ech0021 import v7
    political_data = v7.ECH0021PoliticalRightData(...)

    # Explicit v8
    from openmun_ech.ech0021 import v8
"""

from .enums import (
    # Enums and simple types
    TypeOfRelationship,
    CareType,
    KindOfEmployment,
    YesNo,
    MrMrs,
    UIDOrganisationIdCategory,
    DataLockType,  # v7 only (changed to yesNoType in v8)
)

from .v8 import (
    # Core data types
    ECH0021PersonAdditionalData,
    ECH0021LockData,
    ECH0021PlaceOfOriginAddonData,
    ECH0021MaritalDataAddon,

    # Birth addon
    ECH0021NameOfParent,
    ECH0021BirthAddonData,

    # Job data
    ECH0021JobData,
    ECH0021OccupationData,
    ECH0021UIDStructure,

    # Relationships
    ECH0021Partner,
    ECH0021MaritalRelationship,
    ECH0021ParentalRelationship,
    ECH0021GuardianMeasureInfo,
    ECH0021GuardianRelationship,

    # Optional (low priority)
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021HealthInsuranceData,
    ECH0021MatrimonialInheritanceArrangementData,
)

# Import versioned modules for explicit version selection
from . import v7
from . import v8

__all__ = [
    # Enums
    'TypeOfRelationship',
    'CareType',
    'KindOfEmployment',
    'YesNo',
    'MrMrs',
    'UIDOrganisationIdCategory',
    'DataLockType',  # v7 only

    # Core types
    'ECH0021PersonAdditionalData',
    'ECH0021LockData',
    'ECH0021PlaceOfOriginAddonData',
    'ECH0021MaritalDataAddon',

    # Birth
    'ECH0021NameOfParent',
    'ECH0021BirthAddonData',

    # Job
    'ECH0021JobData',
    'ECH0021OccupationData',
    'ECH0021UIDStructure',

    # Relationships
    'ECH0021Partner',
    'ECH0021MaritalRelationship',
    'ECH0021ParentalRelationship',
    'ECH0021GuardianMeasureInfo',
    'ECH0021GuardianRelationship',

    # Optional
    'ECH0021ArmedForcesData',
    'ECH0021CivilDefenseData',
    'ECH0021FireServiceData',
    'ECH0021HealthInsuranceData',
    'ECH0021MatrimonialInheritanceArrangementData',

    # Version modules
    'v7',
    'v8',
]
