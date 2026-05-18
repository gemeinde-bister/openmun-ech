"""eCH-0020 Layer 2: Simplified Models for Application Use.

This package provides a flattened, user-friendly API for constructing eCH-0020
deliveries from application data. Layer 2 hides XML complexity while maintaining
100% XSD compliance through conversion to Layer 1 models.
"""

from .config import DeliveryConfig
from .types import (
    ReportingType, PlaceType, GuardianType, DatePrecision,
    PersonIdentification, ParentInfo, GuardianInfo,
)
from .helpers import (
    extract_date_of_birth,
    extract_date_of_birth_with_precision,
    extract_person_identification,
    date_to_partially_known,
    # Deprecated aliases (underscore-prefixed)
    _extract_date_of_birth,
    _extract_person_identification,
)
from .person import BaseDeliveryPerson
from .event import (
    ResidenceType, SecondaryResidenceInfo, DwellingAddressInfo,
    DestinationInfo, BaseDeliveryEvent,
)

__all__ = [
    'DeliveryConfig',
    'ReportingType', 'PlaceType', 'GuardianType', 'DatePrecision',
    'PersonIdentification', 'ParentInfo', 'GuardianInfo',
    'BaseDeliveryPerson',
    'ResidenceType', 'SecondaryResidenceInfo', 'DwellingAddressInfo',
    'DestinationInfo', 'BaseDeliveryEvent',
    # Public helper API
    'extract_date_of_birth', 'extract_date_of_birth_with_precision',
    'extract_person_identification', 'date_to_partially_known',
    # Deprecated aliases (kept for backward compatibility)
    '_extract_date_of_birth', '_extract_person_identification',
]
