"""XSD Schema caching and validation utilities.

This module provides caching for eCH XSD schemas and validation functionality
to ensure all exported XML conforms to official eCH standards.

Zero-Tolerance Policy #5: No Schema Violations
All exported XML MUST validate against the official eCH XSD schemas.
Performance is secondary to correctness for government data.
"""

import shutil
import urllib.request
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False


# Official eCH schema URLs
# Includes all schemas used by the library AND their XSD import dependencies
ECH_SCHEMAS = {
    # Core schemas used by library
    'eCH-0020-3-0.xsd': 'https://www.ech.ch/xmlns/eCH-0020/3/eCH-0020-3-0.xsd',
    'eCH-0011-8-1.xsd': 'https://www.ech.ch/xmlns/eCH-0011/8/eCH-0011-8-1.xsd',
    'eCH-0044-4-1.xsd': 'https://www.ech.ch/xmlns/eCH-0044/4/eCH-0044-4-1.xsd',
    'eCH-0021-7-0.xsd': 'https://www.ech.ch/xmlns/eCH-0021/7/eCH-0021-7-0.xsd',
    'eCH-0021-8-0.xsd': 'https://www.ech.ch/xmlns/eCH-0021/8/eCH-0021-8-0.xsd',
    'eCH-0010-6-0.xsd': 'https://www.ech.ch/xmlns/eCH-0010/6/eCH-0010-6-0.xsd',
    'eCH-0007-6-0.xsd': 'https://www.ech.ch/xmlns/eCH-0007/6/eCH-0007-6-0.xsd',
    'eCH-0008-3-0.xsd': 'https://www.ech.ch/xmlns/eCH-0008/3/eCH-0008-3-0.xsd',
    'eCH-0058-5-0.xsd': 'https://www.ech.ch/xmlns/eCH-0058/5/eCH-0058-5-0.xsd',
    'eCH-0099-2-1.xsd': 'https://www.ech.ch/xmlns/eCH-0099/2/eCH-0099-2-1.xsd',
    # XSD import dependencies (referenced by other schemas)
    'eCH-0006-2-0.xsd': 'https://www.ech.ch/xmlns/eCH-0006/2/eCH-0006-2-0.xsd',
    'eCH-0007-5-0.xsd': 'https://www.ech.ch/xmlns/eCH-0007/5/eCH-0007-5-0.xsd',
    'eCH-0010-5-1.xsd': 'https://www.ech.ch/xmlns/eCH-0010/5/eCH-0010-5-1.xsd',
    'eCH-0058-4-0.xsd': 'https://www.ech.ch/xmlns/eCH-0058/4/eCH-0058-4-0.xsd',
}


def get_schema_cache_dir() -> Path:
    """Get or create schema cache directory.

    Returns:
        Path to .schema_cache/eCH directory in project root
    """
    # Find project root (where .schema_cache should be)
    # Start from this file and go up to find project root
    current = Path(__file__).resolve()

    # Look for typical project root indicators
    for parent in current.parents:
        if (parent / 'pyproject.toml').exists() or (parent / 'setup.py').exists():
            cache_dir = parent / '.schema_cache' / 'eCH'
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir

    # Fallback: use home directory
    cache_dir = Path.home() / '.cache' / 'openmun-ech' / 'schemas' / 'eCH'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_schema(schema_name: str, url: str, cache_dir: Path) -> Path:
    """Download XSD schema from eCH.ch if not already cached.

    Args:
        schema_name: Name of the schema file (e.g., 'eCH-0020-3-0.xsd')
        url: URL to download from
        cache_dir: Directory to cache schemas

    Returns:
        Path to the cached schema file

    Raises:
        Exception: If download fails
    """
    schema_path = cache_dir / schema_name

    if schema_path.exists():
        return schema_path

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(schema_path, 'wb') as f:
                shutil.copyfileobj(response, f)
        return schema_path
    except Exception as e:
        raise RuntimeError(f"Failed to download {schema_name} from {url}: {e}") from e


def ensure_schema(schema_name: str = 'eCH-0020-3-0.xsd') -> Path:
    """Ensure a specific eCH schema is downloaded and cached.

    Args:
        schema_name: Name of the schema file to ensure

    Returns:
        Path to the cached schema file

    Raises:
        ValueError: If schema_name is not in ECH_SCHEMAS
        RuntimeError: If download fails
    """
    if schema_name not in ECH_SCHEMAS:
        raise ValueError(
            f"Unknown schema: {schema_name}. "
            f"Available schemas: {', '.join(ECH_SCHEMAS.keys())}"
        )

    cache_dir = get_schema_cache_dir()
    url = ECH_SCHEMAS[schema_name]
    return download_schema(schema_name, url, cache_dir)


def ensure_all_schemas() -> Path:
    """Ensure all required eCH schemas are downloaded.

    This downloads all schemas defined in ECH_SCHEMAS to enable
    complete XSD validation with schema imports.

    Returns:
        Path to the eCH-0020-3-0.xsd schema (primary schema)
    """
    cache_dir = get_schema_cache_dir()

    for schema_name, url in ECH_SCHEMAS.items():
        download_schema(schema_name, url, cache_dir)

    return cache_dir / 'eCH-0020-3-0.xsd'


def validate_xml(
    xml_element: ET.Element,
    schema_name: str = 'eCH-0020-3-0.xsd',
    raise_on_error: bool = True
) -> bool:
    """Validate XML element against eCH XSD schema.

    Args:
        xml_element: XML element tree to validate
        schema_name: Name of the schema to validate against
        raise_on_error: If True, raise exception on validation failure

    Returns:
        True if valid, False if invalid (when raise_on_error=False)

    Raises:
        ImportError: If xmlschema library is not installed
        ValueError: If schema_name is unknown
        xmlschema.XMLSchemaException: If validation fails and raise_on_error=True
    """
    if not HAS_XMLSCHEMA:
        raise ImportError(
            "xmlschema library is required for XSD validation. "
            "Install with: pip install xmlschema"
        )

    # Ensure schema is downloaded
    schema_path = ensure_schema(schema_name)

    # Ensure all dependent schemas are downloaded (for imports)
    ensure_all_schemas()

    # Load schema
    schema = xmlschema.XMLSchema(str(schema_path))

    # Validate
    if raise_on_error:
        schema.validate(xml_element)
        return True
    else:
        return schema.is_valid(xml_element)


# Singleton schema cache for performance
_SCHEMA_CACHE: dict[str, 'xmlschema.XMLSchema'] = {}


def get_cached_schema(schema_name: str = 'eCH-0020-3-0.xsd') -> 'xmlschema.XMLSchema':
    """Get a cached XMLSchema instance.

    This avoids reloading schemas on every validation call.

    Args:
        schema_name: Name of the schema

    Returns:
        Loaded XMLSchema instance
    """
    if not HAS_XMLSCHEMA:
        raise ImportError(
            "xmlschema library is required. "
            "Install with: pip install xmlschema"
        )

    if schema_name not in _SCHEMA_CACHE:
        schema_path = ensure_schema(schema_name)
        ensure_all_schemas()  # Ensure dependencies
        _SCHEMA_CACHE[schema_name] = xmlschema.XMLSchema(str(schema_path))

    return _SCHEMA_CACHE[schema_name]


def validate_xml_cached(
    xml_element: ET.Element,
    schema_name: str = 'eCH-0020-3-0.xsd',
    raise_on_error: bool = True
) -> bool:
    """Validate XML using cached schema (faster for repeated validations).

    Args:
        xml_element: XML element tree to validate
        schema_name: Name of the schema to validate against
        raise_on_error: If True, raise exception on validation failure

    Returns:
        True if valid, False if invalid (when raise_on_error=False)

    Raises:
        ImportError: If xmlschema library is not installed
        xmlschema.XMLSchemaException: If validation fails and raise_on_error=True
    """
    schema = get_cached_schema(schema_name)

    if raise_on_error:
        schema.validate(xml_element)
        return True
    else:
        return schema.is_valid(xml_element)
