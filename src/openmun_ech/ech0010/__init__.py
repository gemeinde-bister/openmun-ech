"""eCH-0010 Address component - Versioned exports.

Available versions:
- v5: eCH-0010 v5.1 (used by eCH-0020 v3.0, eCH-0099 v2.1)
- v6: eCH-0010 v6.0 (used by eCH-0129 v6.0)

Key v5→v6 change: 'country' field changed from countryIdIso2Type (2-letter string)
to countryType (complex: countryId + countryIdISO2 + countryNameShort).
"""

from openmun_ech.ech0010.v5 import (
    MrMrs,
    ECH0010PersonMailAddressInfo,
    ECH0010OrganisationMailAddressInfo,
    ECH0010AddressInformation,
    ECH0010MailAddress,
    ECH0010PersonMailAddress,
    ECH0010OrganisationMailAddress,
    ECH0010SwissAddressInformation,
)
from openmun_ech.ech0010.v6 import (
    ECH0010v6Country,
    ECH0010v6PersonMailAddressInfo,
    ECH0010v6OrganisationMailAddressInfo,
    ECH0010v6AddressInformation,
    ECH0010v6MailAddress,
    ECH0010v6PersonMailAddress,
    ECH0010v6OrganisationMailAddress,
    ECH0010v6SwissAddressInformation,
)

# Import versioned modules for explicit selection
from . import v5  # noqa: F401
from . import v6  # noqa: F401

__all__ = [
    # Default exports (v5 — used by eCH-0020, eCH-0099)
    'MrMrs',
    'ECH0010PersonMailAddressInfo',
    'ECH0010OrganisationMailAddressInfo',
    'ECH0010AddressInformation',
    'ECH0010MailAddress',
    'ECH0010PersonMailAddress',
    'ECH0010OrganisationMailAddress',
    'ECH0010SwissAddressInformation',
    # v6 exports (used by eCH-0129)
    'ECH0010v6Country',
    'ECH0010v6PersonMailAddressInfo',
    'ECH0010v6OrganisationMailAddressInfo',
    'ECH0010v6AddressInformation',
    'ECH0010v6MailAddress',
    'ECH0010v6PersonMailAddress',
    'ECH0010v6OrganisationMailAddress',
    'ECH0010v6SwissAddressInformation',
    # Version modules
    'v5',
    'v6',
]
