"""eCH-0133 Objektwesen — Domäne Steuern.

Standard: eCH-0133 v3.0 (XSD version 3.0, document version 2.1.0)
Purpose: Tax domain messages for property valuations and fiscal ownership

Depends on: eCH-0129 v6.0.0 (Objektwesen), eCH-0058 v5, eCH-0007 v6

Message types:
- ownerOrBeneficiary: Report fiscal ownership changes (ST → BV, GV)
- estimation: Report property valuations (SA → ST)
- realestateBaseDelivery: Full parcel dump with ownership + valuations (SA → ST)
- estimationBaseDelivery: Full valuation dump with linked parcels (SA → ST)

Usage:
    from openmun_ech.ech0133 import (
        ECH0133Delivery,                  # Root delivery element
        ECH0133OwnerOrBeneficiary,        # §4.2 ownership message
        ECH0133Estimation,                # §4.3 valuation message
        ECH0133RealestateBaseDelivery,    # §4.4.1.1 parcel dump
        ECH0133EstimationBaseDelivery,    # §4.4.1.2 valuation dump
    )
"""

from .v3 import (
    # Shared helper types
    ECH0133FiscalOwnershipInfo,
    ECH0133BuildingInfo,

    # §4.2 ownerOrBeneficiary
    ECH0133OwnerOrBeneficiary,

    # §4.3 estimation
    ECH0133EstimationRealestateInfo,
    ECH0133Estimation,

    # §4.4.1.1 realestateBaseDelivery
    ECH0133RealestateInfo,
    ECH0133RealestateBaseDelivery,

    # §4.4.1.2 estimationBaseDelivery
    ECH0133EstBaseBldgRealestateInfo,
    ECH0133EstBaseRealestateInfo,
    ECH0133EstBaseBuildingInfo,
    ECH0133EstimationInfo,
    ECH0133EstimationBaseDelivery,

    # Root delivery
    ECH0133Delivery,
)

# Resolve forward references
ECH0133FiscalOwnershipInfo.model_rebuild()
ECH0133BuildingInfo.model_rebuild()
ECH0133OwnerOrBeneficiary.model_rebuild()
ECH0133EstimationRealestateInfo.model_rebuild()
ECH0133Estimation.model_rebuild()
ECH0133RealestateInfo.model_rebuild()
ECH0133RealestateBaseDelivery.model_rebuild()
ECH0133EstBaseBldgRealestateInfo.model_rebuild()
ECH0133EstBaseRealestateInfo.model_rebuild()
ECH0133EstBaseBuildingInfo.model_rebuild()
ECH0133EstimationInfo.model_rebuild()
ECH0133EstimationBaseDelivery.model_rebuild()
ECH0133Delivery.model_rebuild()

__all__ = [
    # Shared helper types
    'ECH0133FiscalOwnershipInfo',
    'ECH0133BuildingInfo',

    # §4.2 ownerOrBeneficiary
    'ECH0133OwnerOrBeneficiary',

    # §4.3 estimation
    'ECH0133EstimationRealestateInfo',
    'ECH0133Estimation',

    # §4.4.1.1 realestateBaseDelivery
    'ECH0133RealestateInfo',
    'ECH0133RealestateBaseDelivery',

    # §4.4.1.2 estimationBaseDelivery
    'ECH0133EstBaseBldgRealestateInfo',
    'ECH0133EstBaseRealestateInfo',
    'ECH0133EstBaseBuildingInfo',
    'ECH0133EstimationInfo',
    'ECH0133EstimationBaseDelivery',

    # Root delivery
    'ECH0133Delivery',
]
