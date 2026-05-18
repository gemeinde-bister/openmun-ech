"""eCH-0020 Layer 2: Simplified Models for Application Use.

This module re-exports all Layer 2 classes from the layer2/ package
for backward compatibility. New code should import from
openmun_ech.ech0020.layer2 directly.
"""

from openmun_ech.ech0020.layer2 import *  # noqa: F401,F403
from openmun_ech.ech0020.layer2 import (  # noqa: F401 — explicit for type checkers
    extract_date_of_birth,
    extract_date_of_birth_with_precision,
    extract_person_identification,
    date_to_partially_known,
    # Deprecated aliases
    _extract_date_of_birth,
    _extract_person_identification,
    DeliveryConfig,
    ReportingType,
    PlaceType,
    GuardianType,
    DatePrecision,
    PersonIdentification,
    ParentInfo,
    GuardianInfo,
    BaseDeliveryPerson,
    ResidenceType,
    SecondaryResidenceInfo,
    DwellingAddressInfo,
    DestinationInfo,
    BaseDeliveryEvent,
)
