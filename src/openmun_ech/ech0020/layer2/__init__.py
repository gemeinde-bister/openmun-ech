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
from .helpers import _extract_date_of_birth, _extract_person_identification
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
    '_extract_date_of_birth', '_extract_person_identification',
]
