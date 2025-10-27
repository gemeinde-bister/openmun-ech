"""eCH-0099 v2.1 Statistics Delivery Roundtrip Tests

Tests XML → Pydantic → XML roundtrip with production data.

⚠️ CRITICAL: Zero Tolerance Policy
- NO defaults, NO fallbacks, NO assumptions
- Every field affects government statistics accuracy
- NEVER bypass Pydantic validation
- Missing data MUST fail, not use defaults

Success Criteria:
- Original element count MUST equal exported element count
- Zero data loss required
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

import pytest

from openmun_ech.ech0099.v2 import ECH0099Delivery


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


def compare_element_counts(original: ET.Element, exported: ET.Element) -> tuple[bool, list[str]]:
    """Compare element counts between two XML trees.

    Args:
        original: Original production XML root
        exported: Exported XML root from Pydantic

    Returns:
        Tuple of (match: bool, differences: list of difference strings)
    """
    orig_counts = count_elements(original)
    exp_counts = count_elements(exported)

    differences = []

    # Check for missing elements
    for tag in sorted(orig_counts.keys()):
        orig_count = orig_counts[tag]
        exp_count = exp_counts.get(tag, 0)

        if orig_count != exp_count:
            diff_type = 'MISSING' if exp_count < orig_count else 'EXTRA'
            diff_amount = abs(orig_count - exp_count)
            differences.append(
                f"{tag}: {orig_count} → {exp_count} ({diff_type} {diff_amount})"
            )

    # Check for unexpected elements
    for tag in sorted(exp_counts.keys()):
        if tag not in orig_counts:
            differences.append(f"{tag}: 0 → {exp_counts[tag]} (UNEXPECTED)")

    return len(differences) == 0, differences


class TestECH0099Roundtrip:
    """Test eCH-0099 v2.1 statistics delivery roundtrip with production data."""

    def test_has_production_files(self, ech0099_files):
        """Verify we have production eCH-0099 files."""
        assert len(ech0099_files) > 0, (
            "No eCH-0099 files found in production data. "
            "Set OPENMUN_PRODUCTION_DATA environment variable if needed."
        )

    def test_all_files_roundtrip(self, ech0099_files):
        """Test all eCH-0099 files for roundtrip validity.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        if not ech0099_files:
            pytest.skip("No eCH-0099 production files available")

        failures = []

        for xml_file in ech0099_files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Verify it's eCH-0099 v2.x
                assert "http://www.ech.ch/xmlns/eCH-0099/2" in root.tag, (
                    f"Not an eCH-0099 v2.x file: {xml_file.name}"
                )

                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT)
                delivery = ECH0099Delivery.from_xml(root)
                assert isinstance(delivery, ECH0099Delivery)

                # Step 3: Export Pydantic → XML
                exported_root = delivery.to_xml()
                exported_element_count = len(list(exported_root.iter()))

                # Step 4: Compare element counts (MUST match exactly)
                match, differences = compare_element_counts(root, exported_root)

                if not match:
                    failures.append({
                        'file': xml_file.name,
                        'original_count': original_element_count,
                        'exported_count': exported_element_count,
                        'differences': differences[:10]  # First 10 diffs
                    })

            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': str(e)
                })

        # Report all failures at once
        if failures:
            msg = f"\n{len(failures)}/{len(ech0099_files)} files failed roundtrip validation:\n\n"
            for failure in failures[:5]:  # Show first 5
                msg += f"File: {failure['file']}\n"
                if 'error' in failure:
                    msg += f"  Error: {failure['error']}\n"
                else:
                    msg += f"  Original: {failure['original_count']} elements\n"
                    msg += f"  Exported: {failure['exported_count']} elements\n"
                    msg += f"  Differences: {len(failure['differences'])} total\n"
                    for diff in failure['differences'][:5]:
                        msg += f"    - {diff}\n"
                msg += "\n"

            if len(failures) > 5:
                msg += f"... and {len(failures) - 5} more failures\n"

            pytest.fail(msg)


class TestECH0099SingleFile:
    """Test with a single known-good eCH-0099 file for quick validation."""

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with a known-good eCH-0099 file.

        This test uses the most recent eCH-0099 file that has been
        verified to work correctly with our implementation.
        """
        # Try to find the most recent eCH-0099 file
        ech0099_pattern = "data_6172-*.xml"
        ech0099_files = []

        for xml_file in sorted(production_data_path.glob(ech0099_pattern)):
            try:
                with open(xml_file, 'r') as f:
                    content = f.read(500)
                    if 'xmlns="http://www.ech.ch/xmlns/eCH-0099/2"' in content:
                        ech0099_files.append(xml_file)
            except Exception:
                pass

        if not ech0099_files:
            pytest.skip("No eCH-0099 files found in production data")

        # Use the most recent file
        xml_file = ech0099_files[-1]

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0099Delivery.from_xml(root)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Roundtrip failed for {xml_file.name}!\n"
            f"Differences: {differences[:10]}\n"
            f"This indicates data loss in serialization."
        )

        # Verify counts match
        orig_count = len(list(root.iter()))
        exp_count = len(list(exported.iter()))
        assert orig_count == exp_count, (
            f"Element count mismatch: {orig_count} → {exp_count}"
        )
