"""eCH Pydantic models for structured XML import/export.

This package provides version-aware Pydantic models for Swiss eCH standards,
enabling type-safe, validated import and export of XML data.

Architecture:
- ech0007/: eCH-0007 Municipality models (v5)
- ech0008/: eCH-0008 Country models (v3)
- ech0010/: eCH-0010 Address models (v5)
- ech0011/: eCH-0011 Person data models (v8)
- ech0021/: eCH-0021 Person additional data models (v8)
- ech0044/: eCH-0044 Person identification models (v4)
- ech0058/: eCH-0058 Message header models (v5)
- version_router: Automatic version detection and routing

Example:
    from openmun_ech import ECH0058Header
    from openmun_ech import ECH0007Municipality

    # Use components directly
    header = ECH0058Header(...)
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
]
