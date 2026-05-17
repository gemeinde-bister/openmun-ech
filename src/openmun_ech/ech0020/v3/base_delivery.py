"""eCH-0020 v3.0 — Base Delivery."""

from typing import Optional, List
from datetime import date
from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .person_types import (
    ECH0020BaseDeliveryPerson,
    ECH0020ReportingMunicipalityRestrictedBaseSecondary,
    ECH0020HasMainResidence,
    ECH0020HasSecondaryResidence,
)


class ECH0020EventBaseDelivery(ECHModel):
    """Base delivery event — complete population register snapshot.

    XSD: eventBaseDelivery (eCH-0020-3-0.xsd lines 173-203)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventBaseDelivery'

    base_delivery_person: ECH0020BaseDeliveryPerson = xml_field('baseDeliveryPerson')

    # XSD CHOICE: exactly one residence type
    has_main_residence: Optional[ECH0020HasMainResidence] = xml_field(
        'hasMainResidence', default=None,
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidence] = xml_field(
        'hasSecondaryResidence', default=None,
    )
    has_other_residence: Optional[ECH0020ReportingMunicipalityRestrictedBaseSecondary] = xml_field(
        'hasOtherResidence', default=None,
    )

    base_delivery_valid_from: Optional[date] = xml_field('baseDeliveryValidFrom', default=None)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventBaseDelivery':
        """Validate XSD CHOICE: exactly ONE residence type must be present."""
        residence_count = sum([
            self.has_main_residence is not None,
            self.has_secondary_residence is not None,
            self.has_other_residence is not None,
        ])

        if residence_count == 0:
            raise ValueError(
                "eventBaseDelivery requires exactly ONE of: hasMainResidence, "
                "hasSecondaryResidence, or hasOtherResidence"
            )
        if residence_count > 1:
            raise ValueError(
                f"eventBaseDelivery allows only ONE residence type, but {residence_count} were provided"
            )

        return self


class ECH0020EventKeyExchange(ECHModel):
    """Key exchange event for synchronizing person identifiers.

    XSD: eventKeyExchange (eCH-0020-3-0.xsd lines 204-209)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventKeyExchange'

    key_exchange_person: List[ECH0044PersonIdentification] = xml_field(
        'keyExchangePerson', wrapper=True, child_ns=NS.ECH0044_V4,
        is_list=True, min_length=1,
    )


class ECH0020EventDataRequest(ECHModel):
    """Data request event for querying person information.

    XSD: eventDataRequest (eCH-0020-3-0.xsd lines 210-216)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventDataRequest'

    data_request_person: Optional[List[ECH0044PersonIdentification]] = xml_field(
        'dataRequestPerson', default=None,
        wrapper=True, child_ns=NS.ECH0044_V4, is_list=True,
    )
    municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'municipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    data_valid_from: Optional[date] = xml_field('dataValidFrom', default=None)
