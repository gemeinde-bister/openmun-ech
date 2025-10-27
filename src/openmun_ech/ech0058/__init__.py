"""eCH-0058 Message Header - Versioned exports.

Available versions:
- v4: eCH-0058 v4.0 (used by eCH-0099 v2.1) - WITHOUT namedMetaData field
- v5: eCH-0058 v5.0 (used by eCH-0020 v3.0/v5.0) - WITH namedMetaData field

Default export: v5 (latest)

Version differences:
- v5 adds namedMetaData field (optional, key-value pairs)
- All other fields are identical between v4 and v5
"""

# Export enums (shared between v4 and v5)
from .enums import ActionType

# Export v5 as default (latest version)
from .v5 import (
    AnyXMLContent,
    ECH0058NamedMetaData,
    ECH0058SendingApplication,
    ECH0058PartialDelivery,
    ECH0058Header,
)

# Import v4 explicitly for version-specific usage
from . import v4
from . import v5

__all__ = [
    # Default exports (v5)
    'AnyXMLContent',
    'ActionType',
    'ECH0058NamedMetaData',
    'ECH0058SendingApplication',
    'ECH0058PartialDelivery',
    'ECH0058Header',
    # Version modules for explicit imports
    'v4',
    'v5',
]
