"""Utilities for openmun-ech.

This module provides utility functions for working with eCH standards.

XSD Schema Validation:
    Cached schema loading and XML validation against official eCH XSD schemas.

    >>> from openmun_ech.utils import validate_xml_cached
    >>> import xml.etree.ElementTree as ET
    >>>
    >>> # Parse your XML
    >>> root = ET.fromstring(xml_string)
    >>>
    >>> # Validate against eCH-0020 v3.0 schema
    >>> validate_xml_cached(root, 'eCH-0020-3-0.xsd')

    Schemas are downloaded once from ech.ch and cached locally.

Available Schemas:
    - eCH-0006-2-0.xsd: Residence permits
    - eCH-0007-5-0.xsd, eCH-0007-6-0.xsd: Municipalities
    - eCH-0008-3-0.xsd: Countries
    - eCH-0010-5-1.xsd, eCH-0010-6-0.xsd: Addresses
    - eCH-0011-8-1.xsd: Person data
    - eCH-0020-3-0.xsd: Population registry events
    - eCH-0021-7-0.xsd, eCH-0021-8-0.xsd: Person additional data
    - eCH-0044-4-1.xsd: Person identification
    - eCH-0058-4-0.xsd, eCH-0058-5-0.xsd: Message headers
    - eCH-0099-2-1.xsd: Statistics delivery
"""

from .schema_cache import (
    # Schema registry
    ECH_SCHEMAS,
    # Cache management
    get_schema_cache_dir,
    ensure_schema,
    ensure_all_schemas,
    # Validation functions
    validate_xml,
    validate_xml_cached,
    get_cached_schema,
)

__all__ = [
    # Schema registry
    'ECH_SCHEMAS',
    # Cache management
    'get_schema_cache_dir',
    'ensure_schema',
    'ensure_all_schemas',
    # Validation functions
    'validate_xml',
    'validate_xml_cached',
    'get_cached_schema',
]
