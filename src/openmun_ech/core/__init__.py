"""Core infrastructure for openmun-ech.

Public API:
    NS — Namespace constants for all eCH standards and versions.
    ECHModel — Base class for declarative XML models.
    xml_field — Field descriptor with XML serialization metadata.
"""

from openmun_ech.core.fields import XmlMeta, xml_field
from openmun_ech.core.model import ECHModel
from openmun_ech.core.namespace import NS

__all__ = ['NS', 'ECHModel', 'XmlMeta', 'xml_field']
