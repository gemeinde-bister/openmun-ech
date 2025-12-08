"""Neutral finalize helpers for composing eCH deliveries with eCH-0058 headers.

This module provides small, standard-specific helpers that build the eCH-0058
header once and wrap one or more payload entries into the correct delivery
container. It complements the single-event convenience method on
`BaseDeliveryEvent.finalize()` without changing existing public APIs.

Design goals:
- Minimal and explicit; no magic dispatch
- Sequential processing; robust over speed
- No namespace pollution (not added to top-level exports)

Notes on eCH-0020:
- Multi-person exports must use baseDelivery (eventBaseDelivery list)
- Mixing unrelated single event kinds (e.g., moveIn + moveOut) in one delivery
  is not supported by the schema; create separate deliveries for those.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional
from uuid import uuid4

from openmun_ech.ech0020 import BaseDeliveryEvent, DeliveryConfig
from openmun_ech.ech0020.v3 import ECH0020Delivery, ECH0020Header
from openmun_ech.ech0099 import ECH0099Delivery, ECH0099ReportedPerson
from openmun_ech.ech0058 import ActionType, ECH0058SendingApplication as ECH0058SendingApplicationV5
from openmun_ech.ech0058 import v5 as ech0058_v5
from openmun_ech.ech0058 import v4 as ech0058_v4


def finalize_0020_base(
    events: Iterable[BaseDeliveryEvent],
    config: DeliveryConfig,
    message_id: Optional[str] = None,
    message_date: Optional[datetime] = None,
    action: ActionType = ActionType.NEW,
    **optional_header_fields,
) -> ECH0020Delivery:
    """Finalize a baseDelivery (multiple people) eCH-0020 message.

    Builds an eCH-0058 v5 header once and converts each Layer 2
    `BaseDeliveryEvent` to its Layer 1 `eventBaseDelivery`, returning an
    `ECH0020Delivery` with a list payload (baseDelivery/messages).
    """
    msg_id = message_id or str(uuid4())
    msg_date = message_date or datetime.now()

    message_type = config.message_type_override or "http://www.ech.ch/xmlns/eCH-0020/3"

    sending_application = ech0058_v5.ECH0058SendingApplication(
        manufacturer=config.manufacturer,
        product=config.product,
        product_version=config.product_version,
    )

    header = ech0058_v5.ECH0058Header(
        sender_id=config.sender_id,
        message_id=msg_id,
        message_type=message_type,
        sending_application=sending_application,
        message_date=msg_date,
        action=action,
        test_delivery_flag=config.test_delivery_flag,
        original_sender_id=config.original_sender_id,
        **optional_header_fields,
    )

    delivery_header = ECH0020Header(
        header=header,
        data_lock=None,
        data_lock_valid_from=None,
        data_lock_valid_till=None,
    )

    layer1_events: List = [e.to_ech0020_event() for e in events]

    return ECH0020Delivery(
        delivery_header=delivery_header,
        event=layer1_events,
        version="3.0",
    )


def finalize_0099(
    persons: Iterable[ECH0099ReportedPerson],
    config: DeliveryConfig,
    message_id: Optional[str] = None,
    message_date: Optional[datetime] = None,
    action: ActionType = ActionType.NEW,
    **optional_header_fields,
) -> ECH0099Delivery:
    """Finalize an eCH-0099 delivery with one or more reported persons.

    eCH-0099 uses eCH-0058 v4 headers and supports multiple `reportedPerson`
    entries within a single delivery.
    """
    msg_id = message_id or str(uuid4())
    msg_date = message_date or datetime.now()

    message_type = "http://www.ech.ch/xmlns/eCH-0099/2"

    sending_application = ech0058_v4.ECH0058SendingApplication(
        manufacturer=config.manufacturer,
        product=config.product,
        product_version=config.product_version,
    )

    header = ech0058_v4.ECH0058Header(
        sender_id=config.sender_id,
        message_id=msg_id,
        message_type=message_type,
        sending_application=sending_application,
        message_date=msg_date,
        action=action,
        test_delivery_flag=config.test_delivery_flag,
        original_sender_id=config.original_sender_id,
        **optional_header_fields,
    )

    return ECH0099Delivery(
        delivery_header=header,
        reported_person=list(persons),
    )


