"""Version detection and routing for eCH-0020 standards.

Automatically detects eCH-0020 version from XML and routes to correct
importer/exporter implementation.
"""

import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import Union


class ECH0020Version(str, Enum):
    """Supported eCH-0020 versions."""
    V3_0 = "3.0"
    V5_0 = "5.0"


class VersionRouter:
    """Routes eCH-0020 operations to correct version-specific implementation."""

    # Namespace mappings for version detection
    NAMESPACE_MAP = {
        'http://www.ech.ch/xmlns/eCH-0020/3': ECH0020Version.V3_0,
        'http://www.ech.ch/xmlns/eCH-0020-3/3': ECH0020Version.V3_0,  # Alternative
        'http://www.ech.ch/xmlns/eCH-0020/5': ECH0020Version.V5_0,
        'http://www.ech.ch/xmlns/eCH-0020-5/5': ECH0020Version.V5_0,  # Alternative
    }

    @staticmethod
    def detect_version_from_file(xml_path: Union[str, Path]) -> ECH0020Version:
        """Detect eCH-0020 version from XML file.

        Args:
            xml_path: Path to XML file

        Returns:
            Detected version

        Raises:
            ValueError: If version cannot be detected
        """
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return VersionRouter.detect_version_from_string(content)

    @staticmethod
    def detect_version_from_string(xml_content: str) -> ECH0020Version:
        """Detect eCH-0020 version from XML string.

        Detection strategy:
        1. Check root element namespace
        2. Check version attribute if present
        3. Check schemaLocation hints

        Args:
            xml_content: XML content as string

        Returns:
            Detected version

        Raises:
            ValueError: If version cannot be detected
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}")

        # Strategy 1: Check root namespace
        namespace = VersionRouter._extract_namespace(root.tag)
        if namespace in VersionRouter.NAMESPACE_MAP:
            return VersionRouter.NAMESPACE_MAP[namespace]

        # Strategy 2: Check version attribute
        version_attr = root.get('version') or root.get('{http://www.ech.ch/xmlns/eCH-0020/3}version')
        if version_attr:
            if version_attr.startswith('3.'):
                return ECH0020Version.V3_0
            elif version_attr.startswith('5.'):
                return ECH0020Version.V5_0

        # Strategy 3: Check schemaLocation
        schema_location = root.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', '')
        if 'eCH-0020/3' in schema_location or 'eCH-0020-3' in schema_location:
            return ECH0020Version.V3_0
        elif 'eCH-0020/5' in schema_location or 'eCH-0020-5' in schema_location:
            return ECH0020Version.V5_0

        raise ValueError(
            "Cannot detect eCH-0020 version. "
            "No recognizable namespace, version attribute, or schemaLocation found."
        )

    @staticmethod
    def _extract_namespace(tag: str) -> str:
        """Extract namespace URI from qualified tag name.

        Args:
            tag: Tag name, possibly with namespace

        Returns:
            Namespace URI or empty string
        """
        if tag.startswith('{'):
            return tag[1:tag.index('}')]
        return ''

    @staticmethod
    def get_importer(version: ECH0020Version):
        """Get importer instance for specific version.

        Args:
            version: eCH-0020 version

        Returns:
            Version-specific importer instance

        Note:
            Currently returns placeholder. Will be implemented with actual
            importers in migration phases.
        """
        if version == ECH0020Version.V3_0:
            # Will import from openmun.importers.sedex_importer_v3
            from openmun.importers.sedex_importer import SedexImporter
            return SedexImporter()  # Current importer handles v3
        elif version == ECH0020Version.V5_0:
            raise NotImplementedError("eCH-0020 v5.0 importer not yet implemented")
        else:
            raise ValueError(f"Unsupported version: {version}")

    @staticmethod
    def get_exporter(version: ECH0020Version):
        """Get exporter instance for specific version.

        Args:
            version: eCH-0020 version

        Returns:
            Version-specific exporter instance

        Note:
            Currently returns placeholder. Will be implemented with actual
            exporters in migration phases.
        """
        if version == ECH0020Version.V3_0:
            # Will import from openmun.exporters.ech0020_v3_pydantic_exporter
            from openmun.exporters.ech0020_v3_exporter import ECH0020v3Exporter
            return ECH0020v3Exporter()  # Current exporter handles v3
        elif version == ECH0020Version.V5_0:
            raise NotImplementedError("eCH-0020 v5.0 exporter not yet implemented")
        else:
            raise ValueError(f"Unsupported version: {version}")
