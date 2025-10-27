"""eCH-0044 Person Identification Component.

Standard: eCH-0044 (Person Identification)
Supported versions: v4.1

This component provides person identification structures used across
multiple eCH standards (eCH-0020, eCH-0099, etc.).

Component composition:
- Date handling (partially known dates)
- Person ID management (VN, local IDs, other IDs, EU IDs)
- Basic person data (name, sex, birth date)

Version notes:
- v4.1 is used in eCH-0020 v3.0 and eCH-0099 v2.1
"""

# Import v4 (current version)
from openmun_ech.ech0044.v4 import (
    Sex,
    ECH0044DatePartiallyKnown,
    ECH0044NamedPersonId,
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationKeyOnly,
    ECH0044PersonIdentificationLight,
)

# Default exports (v4)
__all__ = [
    # Enums
    'Sex',
    # v4 models (current)
    'ECH0044DatePartiallyKnown',
    'ECH0044NamedPersonId',
    'ECH0044PersonIdentification',
    'ECH0044PersonIdentificationKeyOnly',
    'ECH0044PersonIdentificationLight',
]
