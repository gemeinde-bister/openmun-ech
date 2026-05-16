"""eCH-0006: Swiss Residence Permit Codes.

Standard: eCH-0006 v2.0
Source: https://www.ech.ch/de/standards/39487

Available versions:
- v2: eCH-0006 v2.0 (used by eCH-0011 v8, eCH-0020 v3)

Types:
- PermitRoot: permitRoot container (ECHModel, declarative XML)
- ResidencePermitType: Main permit type enum (45 values)
- ResidencePermitCategoryType: Base category codes (01-13)
- ResidencePermitRulingType: Ruling/regulation type codes
- ResidencePermitBorderType: Cross-border commuter duration codes
- ResidencePermitShortType: Short-term residence subcategories
- InhabitantControlType: Combined category+ruling codes
- ResidencePermitDetailedType: Most detailed permit codes (leaf nodes)
- ResidencePermitToBeRegisteredType: Mandatory registration subcategories
"""

from .v2 import (
    ResidencePermitCategoryType,
    ResidencePermitRulingType,
    ResidencePermitBorderType,
    ResidencePermitShortType,
    InhabitantControlType,
    ResidencePermitDetailedType,
    ResidencePermitToBeRegisteredType,
    ResidencePermitType,
    PermitRoot,
    get_permit_description,
)

__all__ = [
    # Simple type enums (8 total)
    'ResidencePermitCategoryType',
    'ResidencePermitRulingType',
    'ResidencePermitBorderType',
    'ResidencePermitShortType',
    'InhabitantControlType',
    'ResidencePermitDetailedType',
    'ResidencePermitToBeRegisteredType',
    'ResidencePermitType',
    # Complex type
    'PermitRoot',
    # Helper functions
    'get_permit_description',
]
