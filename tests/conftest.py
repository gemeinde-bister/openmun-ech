"""Shared pytest fixtures for eCH model testing.

This module provides fixtures for testing eCH standards with production data.

⚠️ CRITICAL: Zero Tolerance Policy for Government Data
- NO defaults, NO fallbacks, NO assumptions
- Every field affects real people's legal status
- NEVER bypass Pydantic validation
"""

import sys
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET

import pytest

from openmun_ech.config import get_primary_production_data_path


@pytest.fixture(scope="session")
def production_data_path() -> Optional[Path]:
    """Get production sedex data directory path.

    Returns:
        Path to production data, or None if not available

    Configuration:
        See config.yaml.sample for configuration options.
        Supports both environment variables and config.yaml file.
    """
    return get_primary_production_data_path()


@pytest.fixture(scope="session")
def skip_if_no_production_data(production_data_path):
    """Skip test if production data is not available.

    This allows tests to pass in CI/CD without production data.
    """
    if production_data_path is None:
        pytest.skip("Production data not available")


def find_ech_files(
    data_dir: Path,
    namespace: str,
    event_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Path]:
    """Find eCH XML files matching criteria.

    Args:
        data_dir: Production data directory
        namespace: eCH namespace to match (e.g., 'http://www.ech.ch/xmlns/eCH-0020/3')
        event_type: Optional event type to filter (e.g., 'moveIn', 'correctReporting')
        limit: Optional limit on number of files to return

    Returns:
        List of matching XML file paths
    """
    matching_files = []

    for xml_file in sorted(data_dir.glob("data_*.xml")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Check namespace
            if namespace not in root.tag:
                continue

            # If event_type specified, check for that event
            if event_type:
                ns_prefix = root.tag.split("}")[0] + "}"
                event_found = False
                for child in root:
                    if child.tag == f"{ns_prefix}{event_type}":
                        event_found = True
                        break
                if not event_found:
                    continue

            matching_files.append(xml_file)

            if limit and len(matching_files) >= limit:
                break

        except Exception:
            # Skip files that can't be parsed
            continue

    return matching_files


@pytest.fixture
def ech0020_base_delivery_files(production_data_path) -> List[Path]:
    """Get all eCH-0020 v3.0 base delivery files.

    Returns:
        List of paths to base delivery XML files
    """
    if production_data_path is None:
        return []

    return find_ech_files(
        production_data_path,
        namespace="http://www.ech.ch/xmlns/eCH-0020/3",
        event_type="baseDelivery"
    )


@pytest.fixture
def ech0020_event_files(production_data_path):
    """Factory fixture to get eCH-0020 files by event type.

    Usage:
        def test_movein(ech0020_event_files):
            files = ech0020_event_files('moveIn')
            assert len(files) > 0

    Args:
        event_type: Event type to find (e.g., 'moveIn', 'correctReporting')

    Returns:
        Callable that returns list of matching files
    """
    def _get_files(event_type: str, limit: Optional[int] = None) -> List[Path]:
        if production_data_path is None:
            return []

        return find_ech_files(
            production_data_path,
            namespace="http://www.ech.ch/xmlns/eCH-0020/3",
            event_type=event_type,
            limit=limit
        )

    return _get_files


@pytest.fixture
def ech0099_files(production_data_path) -> List[Path]:
    """Get all eCH-0099 v2.1 statistics delivery files.

    Returns:
        List of paths to eCH-0099 XML files
    """
    if production_data_path is None:
        return []

    return find_ech_files(
        production_data_path,
        namespace="http://www.ech.ch/xmlns/eCH-0099/2"
    )
