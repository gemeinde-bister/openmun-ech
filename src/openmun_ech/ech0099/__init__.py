"""eCH-0099 Person Data Delivery to Statistics.

Standard: eCH-0099 v2.1
Purpose: Send person data to BFS for validation and statistics

Current version: v2.1 (default export)

Usage:
    from openmun_ech.ech0099 import (
        ECH0099Delivery,           # Main delivery container
        ECH0099ReportedPerson,     # Person + extended data
        ECH0099DataType,           # Field/value pair
        ECH0099ValidationReport,   # BFS validation results
        ECH0099Receipt,            # BFS acknowledgment
        ECH0099ErrorInfo,          # Error details
        ECH0099PersonError,        # Person-specific error
    )
"""

# Export v2 as default (v2.1 is still referred to as v2 per eCH convention)
from .v2 import (
    ECH0099DataType,
    ECH0099ReportedPerson,
    ECH0099Delivery,
    ECH0099ErrorInfo,
    ECH0099PersonError,
    ECH0099ValidationReport,
    ECH0099Receipt,
)

# Rebuild models to resolve forward references
ECH0099ReportedPerson.model_rebuild()
ECH0099Delivery.model_rebuild()
ECH0099PersonError.model_rebuild()
ECH0099ValidationReport.model_rebuild()

__all__ = [
    # Core delivery types
    'ECH0099DataType',
    'ECH0099ReportedPerson',
    'ECH0099Delivery',

    # BFS response types
    'ECH0099ErrorInfo',
    'ECH0099PersonError',
    'ECH0099ValidationReport',
    'ECH0099Receipt',
]
