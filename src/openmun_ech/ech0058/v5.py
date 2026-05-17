"""eCH-0058 Message Header v5.0.

Standard: eCH-0058 v5.0 (sedex message header)
Used by: eCH-0020 v3.0/v5.0

Extends v4 with: namedMetaData field (optional key-value pairs).
Shared code lives in _shared.py.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional

from pydantic import Field, field_validator

from openmun_ech.core import ECHModel, xml_field, NS

from ._shared import (  # noqa: F401 — re-exported for backward compatibility
    AnyXMLContent,
    _HeaderBase,
    _header_to_xml,
    _header_from_xml,
)
from .enums import ActionType  # noqa: F401 — re-exported


class ECH0058NamedMetaData(ECHModel):
    """eCH-0058 v5 named metadata (key-value pair)."""

    __xml_ns__ = NS.ECH0058_V5
    __xml_element__ = 'namedMetaData'

    meta_data_name: str = xml_field('metaDataName', min_length=1, max_length=20)
    meta_data_value: str = xml_field('metaDataValue', min_length=1, max_length=50)


class ECH0058SendingApplication(ECHModel):
    """eCH-0058 v5 sending application."""

    __xml_ns__ = NS.ECH0058_V5
    __xml_element__ = 'sendingApplication'

    manufacturer: str = xml_field(min_length=1, max_length=30)
    product: str = xml_field(min_length=1, max_length=30)
    product_version: str = xml_field('productVersion', min_length=1, max_length=10)


class ECH0058PartialDelivery(ECHModel):
    """eCH-0058 v5 partial delivery."""

    __xml_ns__ = NS.ECH0058_V5
    __xml_element__ = 'partialDelivery'

    unique_id_delivery: str = xml_field('uniqueIdDelivery', min_length=1, max_length=50)
    total_number_of_packages: int = xml_field('totalNumberOfPackages', ge=1, le=9999)
    number_of_actual_package: int = xml_field('numberOfActualPackage', ge=1, le=9999)

    @field_validator('number_of_actual_package')
    @classmethod
    def validate_package_number(cls, v: int, info) -> int:
        """Validate package number is within total."""
        return v


class ECH0058Header(_HeaderBase):
    """eCH-0058 v5 message header.

    Complete message header for sedex messages. v5 adds namedMetaData.
    """

    named_meta_data: Optional[List[ECH0058NamedMetaData]] = Field(
        None,
        description="Named metadata key-value pairs"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0058_V5,
        skip_wrapper: bool = False,
    ) -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone).
            namespace: XML namespace URI.
            skip_wrapper: If True, serialize children directly into parent
                         (used when this type is embedded via XSD extension).
        """
        return _header_to_xml(
            self, parent, namespace, skip_wrapper,
            named_meta_data=self.named_meta_data,
        )

    @classmethod
    def from_xml(
        cls,
        elem: ET.Element,
        namespace: str = NS.ECH0058_V5,
    ) -> 'ECH0058Header':
        """Import from XML element."""
        return _header_from_xml(
            cls, elem, namespace,
            sending_app_cls=ECH0058SendingApplication,
            partial_delivery_cls=ECH0058PartialDelivery,
            named_meta_data_cls=ECH0058NamedMetaData,
        )
