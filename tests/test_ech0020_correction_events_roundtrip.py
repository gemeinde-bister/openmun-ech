"""eCH-0020 v3.0 Correction Events Roundtrip Tests

Tests XML → Pydantic → XML roundtrip for correction events with production data.

⚠️ CRITICAL: Zero Tolerance Policy
- NO defaults, NO fallbacks, NO assumptions
- Every field affects real people's legal status
- NEVER bypass Pydantic validation
- Missing data MUST fail, not use defaults

Correction Events Tested:
- correctReporting (95 files)
- correctContact (16 files)
- correctMaritalInfo (4 files)
- correctBirthInfo (2 files)
- correctIdentification (2 files)
- correctName (2 files)
- correctPersonAdditionalData (2 files)
- correctResidencePermit (2 files)
- correctParentalRelationship (1 file) ✅ VALIDATED
- correctPlaceOfOrigin (1 file) ✅ VALIDATED

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


class TestECH0020CorrectReporting:
    """Test correctReporting event roundtrip (95 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctReporting files."""
        files = ech0020_event_files('correctReporting')
        assert len(files) > 0, (
            "No correctReporting files found in production data. "
            "Expected ~95 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctReporting file (data_6172-314.xml).

        This file has been verified to work correctly:
        - 51 elements
        - Perfect roundtrip (100% match)
        """
        xml_file = production_data_path / "data_6172-314.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectReporting
        assert isinstance(delivery.event, ECH0020EventCorrectReporting)

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
        assert orig_count == 51, f"Expected 51 elements, got {orig_count}"
        assert exp_count == 51, f"Expected 51 elements after export, got {exp_count}"

    def test_all_correct_reporting_roundtrip(self, ech0020_event_files):
        """Test all 95 correctReporting files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctReporting')

        if not files:
            pytest.skip("No correctReporting files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectReporting
                assert isinstance(delivery.event, ECH0020EventCorrectReporting)

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
            msg = f"\n{len(failures)}/{len(files)} correctReporting files failed roundtrip:\n\n"
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


class TestECH0020CorrectContact:
    """Test correctContact event roundtrip (16 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctContact files."""
        files = ech0020_event_files('correctContact')
        assert len(files) > 0, (
            "No correctContact files found in production data. "
            "Expected ~16 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctContact file.

        This will use the first available correctContact file as the regression test.
        """
        # Find first correctContact file
        files = []
        for xml_file in sorted(production_data_path.glob("data_*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                if root.find('.//{http://www.ech.ch/xmlns/eCH-0020/3}correctContact') is not None:
                    files.append(xml_file)
                    break
            except Exception:
                continue

        if not files:
            pytest.skip("No correctContact files found")

        xml_file = files[0]

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectContact
        assert isinstance(delivery.event, ECH0020EventCorrectContact)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file {xml_file.name} should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_correct_contact_roundtrip(self, ech0020_event_files):
        """Test all 16 correctContact files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctContact')

        if not files:
            pytest.skip("No correctContact files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectContact
                assert isinstance(delivery.event, ECH0020EventCorrectContact)

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
            msg = f"\n{len(failures)}/{len(files)} correctContact files failed roundtrip:\n\n"
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


class TestECH0020CorrectMaritalInfo:
    """Test correctMaritalInfo event roundtrip (4 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctMaritalInfo files."""
        files = ech0020_event_files('correctMaritalInfo')
        assert len(files) > 0, (
            "No correctMaritalInfo files found in production data. "
            "Expected ~4 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctMaritalInfo file (data_6172-499.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-499.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectMaritalInfo
        assert isinstance(delivery.event, ECH0020EventCorrectMaritalInfo), (
            f"Expected ECH0020EventCorrectMaritalInfo, got {type(delivery.event).__name__}"
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

    def test_all_correct_marital_info_roundtrip(self, ech0020_event_files):
        """Test all 4 correctMaritalInfo files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctMaritalInfo')

        if not files:
            pytest.skip("No correctMaritalInfo files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectMaritalInfo
                assert isinstance(delivery.event, ECH0020EventCorrectMaritalInfo)

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
            msg = f"\n{len(failures)}/{len(files)} correctMaritalInfo files failed roundtrip:\n\n"
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


class TestECH0020CorrectBirthInfo:
    """Test correctBirthInfo event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctBirthInfo files."""
        files = ech0020_event_files('correctBirthInfo')
        assert len(files) > 0, (
            "No correctBirthInfo files found in production data. "
            "Expected ~2 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctBirthInfo file (data_6172-477.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-477.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectBirthInfo
        assert isinstance(delivery.event, ECH0020EventCorrectBirthInfo), (
            f"Expected ECH0020EventCorrectBirthInfo, got {type(delivery.event).__name__}"
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

    def test_all_correct_birth_info_roundtrip(self, ech0020_event_files):
        """Test all 2 correctBirthInfo files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctBirthInfo')

        if not files:
            pytest.skip("No correctBirthInfo files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectBirthInfo
                assert isinstance(delivery.event, ECH0020EventCorrectBirthInfo)

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
            msg = f"\n{len(failures)}/{len(files)} correctBirthInfo files failed roundtrip:\n\n"
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


class TestECH0020CorrectIdentification:
    """Test correctIdentification event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctIdentification files."""
        files = ech0020_event_files('correctIdentification')
        assert len(files) > 0, (
            "No correctIdentification files found in production data. "
            "Expected ~2 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctIdentification file (data_6172-479.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-479.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectIdentification
        assert isinstance(delivery.event, ECH0020EventCorrectIdentification), (
            f"Expected ECH0020EventCorrectIdentification, got {type(delivery.event).__name__}"
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

    def test_all_correct_identification_roundtrip(self, ech0020_event_files):
        """Test all 2 correctIdentification files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctIdentification')

        if not files:
            pytest.skip("No correctIdentification files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectIdentification
                assert isinstance(delivery.event, ECH0020EventCorrectIdentification)

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
            msg = f"\n{len(failures)}/{len(files)} correctIdentification files failed roundtrip:\n\n"
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


class TestECH0020CorrectName:
    """Test correctName event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctName files."""
        files = ech0020_event_files('correctName')
        assert len(files) > 0, (
            "No correctName files found in production data. "
            "Expected ~2 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctName file (data_6172-476.xml).

        This file will be verified to work correctly during initial test run.
        """
        xml_file = production_data_path / "data_6172-476.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectName
        assert isinstance(delivery.event, ECH0020EventCorrectName), (
            f"Expected ECH0020EventCorrectName, got {type(delivery.event).__name__}"
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

    def test_all_correct_name_roundtrip(self, ech0020_event_files):
        """Test all 2 correctName files for roundtrip.

        This test validates:
        1. Production XML can be parsed without errors
        2. from_xml() imports all data into Pydantic (zero defaults/fallbacks)
        3. to_xml() exports all data back to XML
        4. Element counts match exactly (zero data loss)
        """
        files = ech0020_event_files('correctName')

        if not files:
            pytest.skip("No correctName files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectName
                assert isinstance(delivery.event, ECH0020EventCorrectName)

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
            msg = f"\n{len(failures)}/{len(files)} correctName files failed roundtrip:\n\n"
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


class TestECH0020CorrectPersonAdditionalData:
    """Test correctPersonAdditionalData event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctPersonAdditionalData files."""
        files = ech0020_event_files('correctPersonAdditionalData')
        assert len(files) > 0, (
            "No correctPersonAdditionalData files found in production data. "
            "Expected ~2 files."
        )

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctPersonAdditionalData file (data_6172-478.xml)."""
        xml_file = production_data_path / "data_6172-478.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        # Parse
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Import
        delivery = ECH0020Delivery.from_xml(root)

        # Verify event type
        from openmun_ech.ech0020.v3 import ECH0020EventCorrectPersonAdditionalData
        assert isinstance(delivery.event, ECH0020EventCorrectPersonAdditionalData)

        # Export
        exported = delivery.to_xml()

        # Compare
        match, differences = compare_element_counts(root, exported)

        assert match, (
            f"Known-good file should have perfect match!\n"
            f"Differences: {differences}\n"
            f"This regression indicates a breaking change was introduced."
        )

    def test_all_correct_person_additional_data_roundtrip(self, ech0020_event_files):
        """Test all 2 correctPersonAdditionalData files for roundtrip."""
        files = ech0020_event_files('correctPersonAdditionalData')

        if not files:
            pytest.skip("No correctPersonAdditionalData files available")

        failures = []

        for xml_file in files:
            try:
                # Step 1: Parse production XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                assert "http://www.ech.ch/xmlns/eCH-0020/3" in root.tag

                original_element_count = len(list(root.iter()))

                # Step 2: Import to Pydantic (STRICT)
                delivery = ECH0020Delivery.from_xml(root)

                assert isinstance(delivery, ECH0020Delivery)
                assert delivery.event is not None

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectPersonAdditionalData
                assert isinstance(delivery.event, ECH0020EventCorrectPersonAdditionalData)

                # Step 3: Export Pydantic → XML
                exported_root = delivery.to_xml()
                exported_element_count = len(list(exported_root.iter()))

                # Step 4: Compare element counts
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
            msg = f"\n{len(failures)}/{len(files)} correctPersonAdditionalData files failed:\n\n"
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


class TestECH0020CorrectResidencePermit:
    """Test correctResidencePermit event roundtrip (2 production files)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctResidencePermit files."""
        files = ech0020_event_files('correctResidencePermit')
        assert len(files) > 0

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctResidencePermit file (data_6172-538.xml)."""
        xml_file = production_data_path / "data_6172-538.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        delivery = ECH0020Delivery.from_xml(root)

        from openmun_ech.ech0020.v3 import ECH0020EventCorrectResidencePermit
        assert isinstance(delivery.event, ECH0020EventCorrectResidencePermit)

        exported = delivery.to_xml()

        match, differences = compare_element_counts(root, exported)

        assert match, f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_correct_residence_permit_roundtrip(self, ech0020_event_files):
        """Test all 2 correctResidencePermit files for roundtrip."""
        files = ech0020_event_files('correctResidencePermit')

        if not files:
            pytest.skip("No correctResidencePermit files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectResidencePermit
                assert isinstance(delivery.event, ECH0020EventCorrectResidencePermit)

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
            msg = f"\n{len(failures)}/{len(files)} correctResidencePermit files failed:\n\n"
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


class TestECH0020CorrectParentalRelationship:
    """Test correctParentalRelationship event roundtrip (1 production file)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctParentalRelationship files."""
        files = ech0020_event_files('correctParentalRelationship')
        assert len(files) > 0

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctParentalRelationship file (data_6172-498.xml)."""
        xml_file = production_data_path / "data_6172-498.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        delivery = ECH0020Delivery.from_xml(root)

        from openmun_ech.ech0020.v3 import ECH0020EventCorrectParentalRelationship
        assert isinstance(delivery.event, ECH0020EventCorrectParentalRelationship)

        exported = delivery.to_xml()

        match, differences = compare_element_counts(root, exported)

        assert match, f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_correct_parental_relationship_roundtrip(self, ech0020_event_files):
        """Test all 1 correctParentalRelationship file for roundtrip."""
        files = ech0020_event_files('correctParentalRelationship')

        if not files:
            pytest.skip("No correctParentalRelationship files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectParentalRelationship
                assert isinstance(delivery.event, ECH0020EventCorrectParentalRelationship)

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
            msg = f"\n{len(failures)}/{len(files)} correctParentalRelationship files failed:\n\n"
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


class TestECH0020CorrectPlaceOfOrigin:
    """Test correctPlaceOfOrigin event roundtrip (1 production file)."""

    def test_has_production_files(self, ech0020_event_files):
        """Verify we have correctPlaceOfOrigin files."""
        files = ech0020_event_files('correctPlaceOfOrigin')
        assert len(files) > 0

    def test_known_good_file(self, production_data_path, skip_if_no_production_data):
        """Test with known-good correctPlaceOfOrigin file (data_6172-497.xml)."""
        xml_file = production_data_path / "data_6172-497.xml"

        if not xml_file.exists():
            pytest.skip(f"Known-good file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        delivery = ECH0020Delivery.from_xml(root)

        from openmun_ech.ech0020.v3 import ECH0020EventCorrectPlaceOfOrigin
        assert isinstance(delivery.event, ECH0020EventCorrectPlaceOfOrigin)

        exported = delivery.to_xml()

        match, differences = compare_element_counts(root, exported)

        assert match, f"Known-good file should have perfect match!\nDifferences: {differences}"

    def test_all_correct_place_of_origin_roundtrip(self, ech0020_event_files):
        """Test all 1 correctPlaceOfOrigin file for roundtrip."""
        files = ech0020_event_files('correctPlaceOfOrigin')

        if not files:
            pytest.skip("No correctPlaceOfOrigin files available")

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

                from openmun_ech.ech0020.v3 import ECH0020EventCorrectPlaceOfOrigin
                assert isinstance(delivery.event, ECH0020EventCorrectPlaceOfOrigin)

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
            msg = f"\n{len(failures)}/{len(files)} correctPlaceOfOrigin files failed:\n\n"
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
