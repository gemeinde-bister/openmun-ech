"""eCH-0006: Swiss Residence Permit Codes.

Standard: eCH-0006 v2.0
Source: https://www.ech.ch/de/standards/39487

This package defines residence permit type enumerations used in eCH-0011
residencePermitData. Common Swiss permits: L (short stay), B (residence),
C (settlement), F (provisional), N (asylum), G (cross-border).
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
