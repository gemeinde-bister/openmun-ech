"""eCH Pydantic models for Swiss e-government standards.

This package provides two-layer API for working with Swiss eCH standards:

Layer 2 API (Recommended for Creating New Deliveries):
    Simplified models for creating eCH-0020 deliveries from application data.
    Flattens complex XSD structure (7 nesting levels) while maintaining 100%
    XSD compliance and zero data loss.

    >>> from openmun_ech.ech0020 import BaseDeliveryPerson, BaseDeliveryEvent
    >>> from openmun_ech.ech0020 import DeliveryConfig
    >>> # Create person, event, finalize to XML

Layer 1 API (Component Models and Production XML Parsing):
    XSD-faithful models for parsing production XML files and building
    deliveries from components.

    >>> from openmun_ech import ECH0058Header, ECH0007Municipality
    >>> from openmun_ech.ech0020.v3 import ECH0020Delivery
    >>> # Parse existing XML or build from components

Optional Validation:
    Swiss open data validation for postal codes, BFS codes, street names.
    Always optional, provides warnings only, never blocks data entry.

    >>> from openmun_ech.validation import ValidationContext
    >>> # Validate person data against Swiss open data

Package Structure:
- ech0006/: eCH-0006 Residence permit codes (v2)
- ech0007/: eCH-0007 Municipality models (v5)
- ech0008/: eCH-0008 Country models (v3)
- ech0010/: eCH-0010 Address models (v5)
- ech0011/: eCH-0011 Person data models (v8)
- ech0020/: eCH-0020 Population registry models (v3, Layer 2)
- ech0021/: eCH-0021 Person additional data models (v7, v8)
- ech0044/: eCH-0044 Person identification models (v4)
- ech0058/: eCH-0058 Message header models (v4, v5)
- ech0099/: eCH-0099 Statistics delivery models (v2)
- validation/: Optional Swiss open data validation
- utils/: XSD schema caching and validation utilities
- version_router: Automatic version detection and routing

See Also:
    - docs/QUICKSTART.md: Getting started with Layer 2
    - docs/API_REFERENCE.md: Complete API documentation
    - docs/TWO_LAYER_ARCHITECTURE_ROADMAP.md: Architecture details
"""

from openmun_ech.version_router import VersionRouter, ECH0020Version

# Import component models (latest versions)
from openmun_ech.ech0007.v5 import ECH0007SwissMunicipality as ECH0007Municipality
from openmun_ech.ech0008.v3 import ECH0008Country
from openmun_ech.ech0010.v5 import ECH0010MailAddress
from openmun_ech.ech0011.v8 import ECH0011Person
from openmun_ech.ech0021.v8 import ECH0021PersonAdditionalData
from openmun_ech.ech0044.v4 import ECH0044PersonIdentification
from openmun_ech.ech0058.v5 import ECH0058Header
from openmun_ech.i18n import get_label
from openmun_ech.specdoc import get_desc

__all__ = [
    'VersionRouter',
    'ECH0020Version',
    'ECH0007Municipality',
    'ECH0008Country',
    'ECH0010MailAddress',
    'ECH0011Person',
    'ECH0021PersonAdditionalData',
    'ECH0044PersonIdentification',
    'ECH0058Header',
    'get_label',
    'get_desc',
]
