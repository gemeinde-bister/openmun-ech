"""eCH-0020 v3.0 Base Delivery Roundtrip Tests

Tests XML → Pydantic → XML roundtrip with production data.

⚠️ CRITICAL: Zero Tolerance Policy
- NO defaults, NO fallbacks, NO assumptions
- Every field affects real people's legal status
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

from openmun_ech.ech0020.v3 import ECH0020Delivery


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


class TestECH0020BaseDeliveryRoundtrip:
    """Test eCH-0020 v3.0 base delivery roundtrip with production data."""

    def test_has_production_files(self, ech0020_base_delivery_files):
        """Verify we have production base delivery files."""
        assert len(ech0020_base_delivery_files) > 0, (
            "No eCH-0020 base delivery files found in production data. "
            "Set OPENMUN_PRODUCTION_DATA environment variable if needed."
        )

    def test_all_base_deliveries_roundtrip(self, ech0020_base_delivery_files):
        """Test all base delivery files for XML → Pydantic → XML roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        if not ech0020_base_delivery_files:
            pytest.skip("No base delivery files available")

        failures = []

        for xml_file in ech0020_base_delivery_files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Verify it's eCH-0020 v3.0
                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                # Count persons in base delivery
                persons_count = len(list(root.findall(
                    './/{http://www.ech.ch/xmlns/eCH-0020/3}baseDeliveryPerson'
                )))
                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT - no defaults, no fallbacks)
                delivery = ECH0020Delivery.from_xml(root)

                # Verify import
                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None
                assert isinstance(delivery.event, list)

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
                        'persons': persons_count,
                        'differences': differences[:10]  # First 10 diffs
                    })

            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': str(e)
                })

        # Report all failures at once
        if failures:
            msg = f"\n{len(failures)}/{len(ech0020_base_delivery_files)} files failed roundtrip:\n\n"
            for failure in failures[:5]:  # Show first 5
                msg += f"File: {failure['file']}\n"
                if 'error' in failure:
                    msg += f"  Error: {failure['error']}\n"
                else:
                    msg += f"  Original: {failure['original_count']} elements, {failure['persons']} persons\n"
                    msg += f"  Exported: {failure['exported_count']} elements\n"
                    msg += f"  Differences: {len(failure['differences'])} total\n"
                    for diff in failure['differences'][:5]:
                        msg += f"    - {diff}\n"
                msg += "\n"

            if len(failures) > 5:
                msg += f"... and {len(failures) - 5} more failures\n"

            pytest.fail(msg)


class TestECH0020BaseDeliverySingleFile:
    """Test with a single known-good base delivery file for quick validation."""

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with the known-good base delivery file (data_6172-570.xml).

        This file has been verified to work correctly:
        - 39 persons
        - 4400 elements
        - Perfect roundtrip (100% match)
        """
        xml_file = production_data_path / "data_6172-570.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

        # Verify expected counts
        orig_count = len(list(root.iter()))
        exp_count = len(list(exported.iter()))
        assert orig_count == 4400, f"Expected 4400 elements, got {orig_count}"
        assert exp_count == 4400, f"Expected 4400 elements after export, got {exp_count}"

        persons = len(list(root.findall(
            './/{http://www.ech.ch/xmlns/eCH-0020/3}baseDeliveryPerson'
        )))
        assert persons == 39, f"Expected 39 persons, got {persons}"
