"""Tests for eCH-0021 v7 implementation.

Tests the v7-specific types and verifies compatibility with eCH-0020 v3.0.
"""

import xml.etree.ElementTree as ET
from openmun_ech.ech0021 import v7


def test_political_right_data_roundtrip():
    """Test ECH0021PoliticalRightData XML roundtrip."""
    # Create with restriction
    original = v7.ECH0021PoliticalRightData(
        restricted_voting_and_election_right_federation=True
    )

    # Serialize to XML
    xml_elem = original.to_xml()

    # Verify XML structure
    assert xml_elem.tag == '{http://www.ech.ch/xmlns/eCH-0021/7}politicalRightData'
    restriction_elem = xml_elem.find(
        '{http://www.ech.ch/xmlns/eCH-0021/7}restrictedVotingAndElectionRightFederation'
    )
    assert restriction_elem is not None
    assert restriction_elem.text == 'true'

    # Parse back
    restored = v7.ECH0021PoliticalRightData.from_xml(xml_elem)

    # Verify exact match
    assert restored.restricted_voting_and_election_right_federation == original.restricted_voting_and_election_right_federation


def test_political_right_data_no_restriction():
    """Test ECH0021PoliticalRightData with no restriction."""
    # Create without restriction
    original = v7.ECH0021PoliticalRightData(
        restricted_voting_and_election_right_federation=False
    )

    # Serialize and parse
    xml_elem = original.to_xml()
    restored = v7.ECH0021PoliticalRightData.from_xml(xml_elem)

    assert restored.restricted_voting_and_election_right_federation is False


def test_political_right_data_optional():
    """Test ECH0021PoliticalRightData with optional field None."""
    # Create with None (optional field)
    original = v7.ECH0021PoliticalRightData()

    # Serialize to XML
    xml_elem = original.to_xml()

    # Verify no restriction element
    restriction_elem = xml_elem.find(
        '{http://www.ech.ch/xmlns/eCH-0021/7}restrictedVotingAndElectionRightFederation'
    )
    assert restriction_elem is None

    # Parse back
    restored = v7.ECH0021PoliticalRightData.from_xml(xml_elem)

    assert restored.restricted_voting_and_election_right_federation is None


def test_political_right_data_alias():
    """Test ECH0021PoliticalRightData accepts both snake_case and camelCase."""
    # Test snake_case (Python style)
    data1 = v7.ECH0021PoliticalRightData(
        restricted_voting_and_election_right_federation=True
    )
    assert data1.restricted_voting_and_election_right_federation is True

    # Test camelCase (XML style via alias)
    data2 = v7.ECH0021PoliticalRightData(
        restrictedVotingAndElectionRightFederation=True
    )
    assert data2.restricted_voting_and_election_right_federation is True


def test_v7_has_all_required_types():
    """Verify v7 has all required types."""
    # Should be able to import all shared types from v7
    assert hasattr(v7, 'ECH0021PersonAdditionalData')
    assert hasattr(v7, 'ECH0021LockData')
    assert hasattr(v7, 'ECH0021MaritalRelationship')
    assert hasattr(v7, 'ECH0021JobData')
    assert hasattr(v7, 'TypeOfRelationship')
    assert hasattr(v7, 'YesNo')

    # v7-specific type
    assert hasattr(v7, 'ECH0021PoliticalRightData')

    # v7 and v8 are SEPARATE implementations (full copy, not shared)
    # This ensures diff-ability and verifiability per government data rules
    from openmun_ech.ech0021 import v8
    assert v7.ECH0021PersonAdditionalData is not v8.ECH0021PersonAdditionalData
    assert v7.ECH0021LockData is not v8.ECH0021LockData


def test_v7_vs_v8_differences():
    """Verify version differences between v7 and v8."""
    from openmun_ech.ech0021 import v7, v8

    # v7 has politicalRightData, v8 does not
    assert hasattr(v7, 'ECH0021PoliticalRightData')
    assert not hasattr(v8, 'ECH0021PoliticalRightData')

    # Both should have all shared types
    shared_types = [
        'ECH0021PersonAdditionalData',
        'ECH0021LockData',
        'ECH0021BirthAddonData',
        'ECH0021JobData',
        'ECH0021MaritalRelationship',
    ]

    for type_name in shared_types:
        assert hasattr(v7, type_name), f"v7 missing {type_name}"
        assert hasattr(v8, type_name), f"v8 missing {type_name}"


def test_module_level_imports():
    """Test that v7 and v8 can be imported from package root."""
    from openmun_ech.ech0021 import v7, v8

    # Verify modules are accessible
    assert v7 is not None
    assert v8 is not None

    # Verify default import is v8
    from openmun_ech.ech0021 import ECH0021PersonAdditionalData
    assert ECH0021PersonAdditionalData is v8.ECH0021PersonAdditionalData
