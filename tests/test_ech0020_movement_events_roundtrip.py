"""eCH-0020 v3.0 Movement Events Roundtrip Tests

Tests XML → Pydantic → XML roundtrip for movement events with production data.

⚠️ CRITICAL: Zero Tolerance Policy
- NO defaults, NO fallbacks, NO assumptions
- Every field affects real people's legal status
- NEVER bypass Pydantic validation
- Missing data MUST fail, not use defaults

Movement Events Tested:
- moveIn (20 files)
- moveOut (12 files)
- move (9 files)

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


class TestECH0020MoveIn:
    """Test moveIn event roundtrip (20 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have moveIn files."""
        files = ech0020_event_files('moveIn')
        assert len(files) > 0, (
            "No moveIn files found in production data. "
            "Expected ~20 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good moveIn file (data_6172-349.xml).

        This file has been verified to work correctly:
        - 124 elements
        - Perfect roundtrip (100% match)
        """
        xml_file = production_data_path / "data_6172-349.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventMoveIn
        assert isinstance(delivery.event, ECH0020EventMoveIn)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

        # Verify expected count
        orig_count = len(list(root.iter()))
        exp_count = len(list(exported.iter()))
        assert orig_count == 124, f"Expected 124 elements, got {orig_count}"
        assert exp_count == 124, f"Expected 124 elements after export, got {exp_count}"

    def test_all_movein_roundtrip(self, ech0020_event_files):
        """Test all 20 moveIn files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('moveIn')

        if not files:
            pytest.skip("No moveIn files available")

        failures = []

        for xml_file in files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Verify it's eCH-0020 v3.0
                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT - no defaults, no fallbacks)
                delivery = ECH0020Delivery.from_xml(root)

                # Verify import
                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventMoveIn
                assert isinstance(delivery.event, ECH0020EventMoveIn)

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
            msg = f"\n{len(failures)}/{len(files)} moveIn files failed roundtrip:\n\n"
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


class TestECH0020MoveOut:
    """Test moveOut event roundtrip (12 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have moveOut files."""
        files = ech0020_event_files('moveOut')
        assert len(files) > 0, (
            "No moveOut files found in production data. "
            "Expected ~12 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good moveOut file.

        This will use the first available moveOut file as the regression test.
        """
        # Find first moveOut file
        files = []
        for xml_file in sorted(production_data_path.glob("data_*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                if root.find('.//{http://www.ech.ch/xmlns/eCH-0020/3}moveOut') is not None:
                    files.append(xml_file)
                    break
            except Exception:
                continue

        if not files:
            pytest.skip("No moveOut files found")

        xml_file = files[0]

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventMoveOut
        assert isinstance(delivery.event, ECH0020EventMoveOut)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file {xml_file.name} should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_moveout_roundtrip(self, ech0020_event_files):
        """Test all 12 moveOut files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('moveOut')

        if not files:
            pytest.skip("No moveOut files available")

        failures = []

        for xml_file in files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Verify it's eCH-0020 v3.0
                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT - no defaults, no fallbacks)
                delivery = ECH0020Delivery.from_xml(root)

                # Verify import
                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventMoveOut
                assert isinstance(delivery.event, ECH0020EventMoveOut)

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
            msg = f"\n{len(failures)}/{len(files)} moveOut files failed roundtrip:\n\n"
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


class TestECH0020Move:
    """Test move event roundtrip (9 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have move files."""
        files = ech0020_event_files('move')
        assert len(files) > 0, (
            "No move files found in production data. "
            "Expected ~9 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good move file.

        This will use the first available move file as the regression test.
        """
        # Find first move file
        files = []
        for xml_file in sorted(production_data_path.glob("data_*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                if root.find('.//{http://www.ech.ch/xmlns/eCH-0020/3}move') is not None:
                    files.append(xml_file)
                    break
            except Exception:
                continue

        if not files:
            pytest.skip("No move files found")

        xml_file = files[0]

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventMove
        assert isinstance(delivery.event, ECH0020EventMove)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file {xml_file.name} should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_move_roundtrip(self, ech0020_event_files):
        """Test all 9 move files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('move')

        if not files:
            pytest.skip("No move files available")

        failures = []

        for xml_file in files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Verify it's eCH-0020 v3.0
                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT - no defaults, no fallbacks)
                delivery = ECH0020Delivery.from_xml(root)

                # Verify import
                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventMove
                assert isinstance(delivery.event, ECH0020EventMove)

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
            msg = f"\n{len(failures)}/{len(files)} move files failed roundtrip:\n\n"
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
