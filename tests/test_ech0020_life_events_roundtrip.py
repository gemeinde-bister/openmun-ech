"""eCH-0020 v3.0 Life Events Roundtrip Tests

Tests XML → Pydantic → XML roundtrip for life events with production data.

⚠️ CRITICAL: Zero Tolerance Policy
- NO defaults, NO fallbacks, NO assumptions
- Every field affects real people's legal status
- NEVER bypass Pydantic validation
- Missing data MUST fail, not use defaults

Life Events Tested:
- death (4 files)
- marriage (4 files)
- birth (1 file) ✅ VALIDATED
- changeName (1 file) ✅ VALIDATED
- contact (2 files) ✅ VALIDATED

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


class TestECH0020Death:
    """Test death event roundtrip (4 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have death files."""
        files = ech0020_event_files('death')
        assert len(files) > 0, (
            "No death files found in production data. "
            "Expected ~4 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good death file (data_6172-356.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-356.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventDeath
        assert isinstance(delivery.event, ECH0020EventDeath), (
            f"Expected ECH0020EventDeath, got {type(delivery.event).__name__}"
        )

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_death_roundtrip(self, ech0020_event_files):
        """Test all 4 death files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('death')

        if not files:
            pytest.skip("No death files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventDeath
                assert isinstance(delivery.event, ECH0020EventDeath)

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
            msg = f"\n{len(failures)}/{len(files)} death files failed roundtrip:\n\n"
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


class TestECH0020Marriage:
    """Test marriage event roundtrip (4 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have marriage files."""
        files = ech0020_event_files('marriage')
        assert len(files) > 0, (
            "No marriage files found in production data. "
            "Expected ~4 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good marriage file (data_6172-561.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-561.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventMarriage
        assert isinstance(delivery.event, ECH0020EventMarriage), (
            f"Expected ECH0020EventMarriage, got {type(delivery.event).__name__}"
        )

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_marriage_roundtrip(self, ech0020_event_files):
        """Test all 4 marriage files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('marriage')

        if not files:
            pytest.skip("No marriage files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventMarriage
                assert isinstance(delivery.event, ECH0020EventMarriage)

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
            msg = f"\n{len(failures)}/{len(files)} marriage files failed roundtrip:\n\n"
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


class TestECH0020Birth:
    """Test birth event roundtrip (1 production file)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have birth files."""
        files = ech0020_event_files('birth')
        assert len(files) > 0

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good birth file (data_6172-486.xml)."""
        xml_file = production_data_path / "data_6172-486.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        delivery = ECH0020Delivery.from_xml(root)

        from openmun_ech.ech0020.v3 import ECH0020EventBirth
        assert isinstance(delivery.event, ECH0020EventBirth)

        exported = delivery.to_xml()

        match, differences = compare_element_counts(root, exported)

        assert match, f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_birth_roundtrip(self, ech0020_event_files):
        """Test all 1 birth file for roundtrip."""
        files = ech0020_event_files('birth')

        if not files:
            pytest.skip("No birth files available")

        failures = []

        for xml_file in files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                delivery = ECH0020Delivery.from_xml(root)

                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventBirth
                assert isinstance(delivery.event, ECH0020EventBirth)

                exported_root = delivery.to_xml()
                exported_element_count = len(list(exported_root.iter()))

                match, differences = compare_element_counts(root, exported_root)

                if not match:
                    failures.append({
                        'file': xml_file.name,
                        'original_count': original_element_count,
                        'exported_count': exported_element_count,
                        'differences': differences[:10]
                    })

            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': str(e)
                })

        if failures:
            msg = f"\n{len(failures)}/{len(files)} birth files failed:\n\n"
            for failure in failures[:5]:
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


class TestECH0020ChangeName:
    """Test changeName event roundtrip (1 production file)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have changeName files."""
        files = ech0020_event_files('changeName')
        assert len(files) > 0

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good changeName file (data_6172-563.xml)."""
        xml_file = production_data_path / "data_6172-563.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        delivery = ECH0020Delivery.from_xml(root)

        from openmun_ech.ech0020.v3 import ECH0020EventChangeName
        assert isinstance(delivery.event, ECH0020EventChangeName)

        exported = delivery.to_xml()

        match, differences = compare_element_counts(root, exported)

        assert match, f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_change_name_roundtrip(self, ech0020_event_files):
        """Test all 1 changeName file for roundtrip."""
        files = ech0020_event_files('changeName')

        if not files:
            pytest.skip("No changeName files available")

        failures = []

        for xml_file in files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                delivery = ECH0020Delivery.from_xml(root)

                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventChangeName
                assert isinstance(delivery.event, ECH0020EventChangeName)

                exported_root = delivery.to_xml()
                exported_element_count = len(list(exported_root.iter()))

                match, differences = compare_element_counts(root, exported_root)

                if not match:
                    failures.append({
                        'file': xml_file.name,
                        'original_count': original_element_count,
                        'exported_count': exported_element_count,
                        'differences': differences[:10]
                    })

            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': str(e)
                })

        if failures:
            msg = f"\n{len(failures)}/{len(files)} changeName files failed:\n\n"
            for failure in failures[:5]:
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


class TestECH0020Contact:
    """Test contact event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have contact files."""
        files = ech0020_event_files('contact')
        assert len(files) > 0, "No contact files found in production data"

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good contact file (data_6172-542.xml)."""
        xml_file = production_data_path / "data_6172-542.xml"
        
        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")
        
        # Parse production XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Import to Pydantic
        delivery = ECH0020Delivery.from_xml(root)
        
        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventContact
        assert isinstance(delivery.event, ECH0020EventContact), \
            f"Expected ECH0020EventContact, got {type(delivery.event).__name__}"
        
        # Export back to XML
        exported = delivery.to_xml()
        
        # Compare element counts
        match, differences = compare_element_counts(root, exported)
        
        # Known-good file should have perfect match
        assert match, \
            f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_contact_roundtrip(self, ech0020_event_files):
        """Test all 2 contact files for roundtrip.
        
        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('contact')
        
        if len(files) == 0:
            pytest.skip("No contact files found in production data")
        
        failures = []
        for xml_file in files:
            try:
                # Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Import to Pydantic
                delivery = ECH0020Delivery.from_xml(root)
                
                # Export back to XML
                exported = delivery.to_xml()
                
                # Compare element counts
                original_element_count = len(list(root.iter()))
                exported_element_count = len(list(exported.iter()))
                
                # Check for exact match
                match, differences = compare_element_counts(root, exported)
                
                if not match:
                    failures.append({
                        'file': xml_file.name,
                        'original_count': original_element_count,
                        'exported_count': exported_element_count,
                        'differences': differences[:10]
                    })
            
            except Exception as e:
                failures.append({
                    'file': xml_file.name,
                    'error': str(e)
                })
        
        if failures:
            msg = f"\n{len(failures)}/{len(files)} contact files failed:\n\n"
            for failure in failures[:5]:
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
