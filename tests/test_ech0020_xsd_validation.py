"""eCH-0020 v3.0 XSD Validation Tests

Tests XML → Pydantic → XML roundtrip with XSD schema validation.

This test validates that our Pydantic models produce XML that:
1. Conforms to the official eCH-0020 v3.0 XSD schema
2. Uses correct namespaces (not mixed namespaces)
3. Passes strict XSD validation

⚠️ CRITICAL: Zero Tolerance Policy
- XML MUST validate against official eCH XSD schemas
- NO namespace mismatches allowed
- ALL referenced schemas must be available
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict
import urllib.request
import shutil

import pytest

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

from openmun_ech.ech0020.v3 import ECH0020Delivery


# Schema URLs from eCH.ch
ECH_SCHEMAS = {
    'eCH-0020-3-0.xsd': 'https://www.ech.ch/xmlns/eCH-0020/3/eCH-0020-3-0.xsd',
    'eCH-0011-8-1.xsd': 'https://www.ech.ch/xmlns/eCH-0011/8/eCH-0011-8-1.xsd',
    'eCH-0044-4-1.xsd': 'https://www.ech.ch/xmlns/eCH-0044/4/eCH-0044-4-1.xsd',
    'eCH-0021-7-0.xsd': 'https://www.ech.ch/xmlns/eCH-0021/7/eCH-0021-7-0.xsd',
    'eCH-0010-6-0.xsd': 'https://www.ech.ch/xmlns/eCH-0010/6/eCH-0010-6-0.xsd',
    'eCH-0007-6-0.xsd': 'https://www.ech.ch/xmlns/eCH-0007/6/eCH-0007-6-0.xsd',
    'eCH-0008-3-0.xsd': 'https://www.ech.ch/xmlns/eCH-0008/3/eCH-0008-3-0.xsd',
    'eCH-0058-5-0.xsd': 'https://www.ech.ch/xmlns/eCH-0058/5/eCH-0058-5-0.xsd',
}


def get_schema_cache_dir() -> Path:
    """Get or create schema cache directory."""
    cache_dir = Path(__file__).parent.parent / '.schema_cache' / 'eCH'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_schema(schema_name: str, url: str, cache_dir: Path) -> Path:
    """Download XSD schema from eCH.ch if not already cached.

    Args:
        schema_name: Name of the schema file
        url: URL to download from
        cache_dir: Directory to cache schemas

    Returns:
        Path to the cached schema file
    """
    schema_path = cache_dir / schema_name

    if schema_path.exists():
        return schema_path

    print(f"Downloading {schema_name} from {url}...")

    try:
        with urllib.request.urlopen(url) as response:
            with open(schema_path, 'wb') as f:
                shutil.copyfileobj(response, f)
        print(f"  ✓ Downloaded to {schema_path}")
        return schema_path
    except Exception as e:
        print(f"  ✗ Failed to download: {e}")
        raise


def ensure_schemas() -> Path:
    """Ensure all required eCH schemas are downloaded.

    Returns:
        Path to the eCH-0020-3-0.xsd schema
    """
    cache_dir = get_schema_cache_dir()

    for schema_name, url in ECH_SCHEMAS.items():
        download_schema(schema_name, url, cache_dir)

    return cache_dir / 'eCH-0020-3-0.xsd'


def count_elements(elem: ET.Element) -> Dict[str, int]:
    """Count elements by tag in XML tree.

    Args:
        elem: XML element

    Returns:
        Dictionary of tag name → count
    """
    counts = {}
    for child in elem.iter():
        # Strip namespace for readability
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        counts[tag] = counts.get(tag, 0) + 1
    return counts


def check_namespaces(elem: ET.Element) -> list[str]:
    """Check for namespace mismatches in XML.

    Args:
        elem: XML root element

    Returns:
        List of namespace issues found
    """
    issues = []

    # Check birthAddonData specifically (known bug location)
    for birth_addon in elem.iter():
        if 'birthAddonData' in birth_addon.tag:
            if 'eCH-0021' in birth_addon.tag:
                issues.append(
                    f"birthAddonData uses wrong namespace: {birth_addon.tag}\n"
                    f"  Expected: {{http://www.ech.ch/xmlns/eCH-0020/3}}birthAddonData\n"
                    f"  Got:      {birth_addon.tag}"
                )

    return issues


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed (pip install xmlschema)")
class TestECH0020XSDValidation:
    """Test eCH-0020 v3.0 XSD validation with auto-downloaded schemas."""

    def test_schemas_available(self):
        """Verify all required eCH schemas can be downloaded."""
        schema_path = ensure_schemas()
        assert schema_path.exists(), f"eCH-0020 schema not found at {schema_path}"

    def test_production_file_validates_against_xsd(self, production_data_path, skip_if_no_production_data):
        """Test that original production file validates against XSD.

        This establishes baseline - if the original doesn't validate,
        we know there's an issue with the schema download or the production data.
        """
        xml_file = production_data_path / "data_6172-570.xml"

        if not xml_file.exists():
            pytest.skip(f"Production file not found: {xml_file}")

        # Download schemas
        schema_path = ensure_schemas()

        # Load schema
        schema = xmlschema.XMLSchema(str(schema_path))

        # Validate original production file
        try:
            schema.validate(str(xml_file))
        except xmlschema.XMLSchemaException as e:
            pytest.fail(
                f"Original production file does NOT validate against eCH-0020 XSD!\n"
                f"File: {xml_file}\n"
                f"Error: {e}\n"
                f"This suggests either:\n"
                f"  1. Production data is invalid\n"
                f"  2. Schema download failed\n"
                f"  3. Wrong schema version"
            )

    def test_roundtrip_output_validates_against_xsd(self, production_data_path, skip_if_no_production_data):
        """Test that our Pydantic-generated XML validates against XSD.

        This is the CRITICAL test that will catch namespace bugs.
        """
        xml_file = production_data_path / "data_6172-570.xml"

        if not xml_file.exists():
            pytest.skip(f"Production file not found: {xml_file}")

        # Download schemas
        schema_path = ensure_schemas()

        # Load schema
        schema = xmlschema.XMLSchema(str(schema_path))

        # Parse original
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import to Pydantic
        delivery = ECH0020Delivery.from_xml(root)

        # Export back to XML
        exported = delivery.to_xml()

        # Write to temp file for validation
        temp_file = Path('/tmp/test_ech0020_exported.xml')
        exported_tree = ET.ElementTree(exported)
        ET.indent(exported_tree, space='  ')
        exported_tree.write(temp_file, encoding='utf-8', xml_declaration=True)

        # Check for namespace issues first
        namespace_issues = check_namespaces(exported)
        if namespace_issues:
            pytest.fail(
                f"Namespace issues detected in exported XML:\n" +
                "\n".join(f"  - {issue}" for issue in namespace_issues)
            )

        # Validate exported XML against XSD
        try:
            schema.validate(str(temp_file))
        except xmlschema.XMLSchemaException as e:
            # Get more details
            orig_element_count = len(list(root.iter()))
            exp_element_count = len(list(exported.iter()))

            pytest.fail(
                f"Exported XML does NOT validate against eCH-0020 XSD!\n"
                f"Original file: {xml_file}\n"
                f"Exported file: {temp_file}\n"
                f"Original elements: {orig_element_count}\n"
                f"Exported elements: {exp_element_count}\n"
                f"\nValidation error:\n{e}\n"
                f"\nThis indicates a BUG in our Pydantic models or serialization."
            )

    def test_all_production_files_validate(self, ech0020_base_delivery_files):
        """Test all production base delivery files validate after roundtrip."""
        if not ech0020_base_delivery_files:
            pytest.skip("No base delivery files available")

        # Download schemas
        schema_path = ensure_schemas()
        schema = xmlschema.XMLSchema(str(schema_path))

        failures = []

        for xml_file in ech0020_base_delivery_files:
            try:
                # Parse original
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Import to Pydantic
                delivery = ECH0020Delivery.from_xml(root)

                # Export back to XML
                exported = delivery.to_xml()

                # Check namespaces
                namespace_issues = check_namespaces(exported)

                # Write to temp file
                temp_file = Path(f'/tmp/test_ech0020_{xml_file.stem}.xml')
                exported_tree = ET.ElementTree(exported)
                ET.indent(exported_tree, space='  ')
                exported_tree.write(temp_file, encoding='utf-8', xml_declaration=True)

                # Validate
                try:
                    schema.validate(str(temp_file))
                except xmlschema.XMLSchemaException as e:
                    failures.append({
                        'file': xml_file.name,
                        'error': str(e),
                        'namespace_issues': namespace_issues
                    })

            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': f"Exception: {str(e)}"
                })

        if failures:
            msg = f"\n{len(failures)}/{len(ech0020_base_delivery_files)} files failed XSD validation:\n\n"
            for failure in failures[:5]:
                msg += f"File: {failure['file']}\n"
                msg += f"  Error: {failure['error']}\n"
                if 'namespace_issues' in failure and failure['namespace_issues']:
                    msg += f"  Namespace issues: {len(failure['namespace_issues'])}\n"
                msg += "\n"

            if len(failures) > 5:
                msg += f"... and {len(failures) - 5} more failures\n"

            pytest.fail(msg)
