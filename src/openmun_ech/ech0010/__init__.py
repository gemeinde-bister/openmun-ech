"""eCH-0010 Address component.

Exports versioned address models.
"""

from openmun_ech.ech0010.v5 import (
    ECH0010PersonMailAddressInfo,
    ECH0010OrganisationMailAddressInfo,
    ECH0010AddressInformation,
    ECH0010MailAddress,
    ECH0010PersonMailAddress,
    ECH0010OrganisationMailAddress,
    ECH0010SwissAddressInformation,
)

__all__ = [
    'ECH0010PersonMailAddressInfo',
    'ECH0010OrganisationMailAddressInfo',
    'ECH0010AddressInformation',
    'ECH0010MailAddress',
    'ECH0010PersonMailAddress',
    'ECH0010OrganisationMailAddress',
    'ECH0010SwissAddressInformation',
]
