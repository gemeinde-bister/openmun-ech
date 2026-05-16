"""eCH-0099 Person Data Delivery to Statistics.

Standard: eCH-0099 v2.1
Purpose: Send person data to BFS for validation and statistics

Current version: v2.1 (default export)

Layer Architecture:
- Layer 1 (v2.py): XSD-faithful models for XML parsing and export
- Layer 2 (models.py): Simplified models for application use (export only)

Usage - Layer 1 (Advanced, parsing production XML):
    from openmun_ech.ech0099 import (
        ECH0099Delivery,           # Main delivery container
        ECH0099ReportedPerson,     # Person + extended data
        ECH0099DataType,           # Field/value pair
        ECH0099ValidationReport,   # BFS validation results
        ECH0099Receipt,            # BFS acknowledgment
    )

Usage - Layer 2 (Recommended for creating deliveries):
    from openmun_ech.ech0099 import (
        StatisticsPerson,          # Flattened person model
        StatisticsDeliveryEvent,   # Person + residence + extended data
        StatisticsDeliveryConfig,  # Deployment configuration
        DwellingAddressInfo,       # Flattened dwelling address
        DestinationInfo,           # Flattened destination
        PlaceOfOriginInfo,         # Place of origin for Swiss citizens
        ResidenceType,             # MAIN / SECONDARY / OTHER
        PlaceType,                 # UNKNOWN / SWISS / FOREIGN
        NationalityType,           # SWISS / FOREIGN
        finalize_statistics_delivery,  # Finalize multiple events
    )

    # Create and export
    config = StatisticsDeliveryConfig(...)
    person = StatisticsPerson(...)
    event = StatisticsDeliveryEvent(person=person, ...)
    delivery = event.finalize(config)
    delivery.to_file("statpop.xml")
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

# Export Layer 2 models
from .models import (
    # Main API
    StatisticsPerson,
    StatisticsDeliveryEvent,
    StatisticsDeliveryConfig,

    # Supporting models
    DwellingAddressInfo,
    DestinationInfo,
    PlaceOfOriginInfo,

    # Enums
    ResidenceType,
    PlaceType,
    NationalityType,

    # Finalization helper
    finalize_statistics_delivery,
)

# Rebuild models to resolve forward references
ECH0099ReportedPerson.model_rebuild()
ECH0099Delivery.model_rebuild()
ECH0099PersonError.model_rebuild()
ECH0099ValidationReport.model_rebuild()
StatisticsPerson.model_rebuild()
StatisticsDeliveryEvent.model_rebuild()

__all__ = [
    # Layer 1 - Core delivery types
    'ECH0099DataType',
    'ECH0099ReportedPerson',
    'ECH0099Delivery',

    # Layer 1 - BFS response types
    'ECH0099ErrorInfo',
    'ECH0099PersonError',
    'ECH0099ValidationReport',
    'ECH0099Receipt',

    # Layer 2 - Main API
    'StatisticsPerson',
    'StatisticsDeliveryEvent',
    'StatisticsDeliveryConfig',

    # Layer 2 - Supporting models
    'DwellingAddressInfo',
    'DestinationInfo',
    'PlaceOfOriginInfo',

    # Layer 2 - Enums
    'ResidenceType',
    'PlaceType',
    'NationalityType',

    # Layer 2 - Finalization
    'finalize_statistics_delivery',
]
