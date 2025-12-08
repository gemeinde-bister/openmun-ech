"""Test Layer 2 API exports from openmun_ech.ech0020.

This test suite validates that the Layer 2 public API is properly exposed and
all advertised exports are importable and of the correct type.

What This File Tests
====================
1. All main API classes can be imported
2. All supporting model classes can be imported
3. All enum classes can be imported
4. Layer 1 advanced API is accessible
5. All exports in __all__ are actually importable
6. No broken imports or missing classes

Test Coverage
=============
- 3 main API classes: BaseDeliveryPerson, BaseDeliveryEvent, DeliveryConfig
- 6 supporting models: PersonIdentification, ParentInfo, GuardianInfo,
  SecondaryResidenceInfo, DwellingAddressInfo, DestinationInfo
- 5 enums: ResidenceType, ReportingType, PlaceType, GuardianType, DatePrecision
- 1 Layer 1 class: ECH0020Delivery

Total: 15 exports verified

Data Policy
===========
This test file contains NO government data, NO personal data, NO production data.
It only tests import mechanics and type correctness.

Related Documentation
=====================
- docs/LAYER2_API_EXPOSURE_PLAN.md: Implementation plan
- src/openmun_ech/ech0020/__init__.py: API definition
- docs/TWO_LAYER_ARCHITECTURE_ROADMAP.md: Overall roadmap
"""

from enum import Enum


class TestLayer2MainAPIImports:
    """Test main API classes can be imported and are correct types."""

    def test_base_delivery_person_import(self):
        """Verify BaseDeliveryPerson can be imported."""
        from openmun_ech.ech0020 import BaseDeliveryPerson

        assert isinstance(BaseDeliveryPerson, type)
        assert hasattr(BaseDeliveryPerson, '__doc__')
        assert BaseDeliveryPerson.__doc__ is not None

    def test_base_delivery_event_import(self):
        """Verify BaseDeliveryEvent can be imported."""
        from openmun_ech.ech0020 import BaseDeliveryEvent

        assert isinstance(BaseDeliveryEvent, type)
        assert hasattr(BaseDeliveryEvent, '__doc__')
        assert BaseDeliveryEvent.__doc__ is not None

    def test_delivery_config_import(self):
        """Verify DeliveryConfig can be imported."""
        from openmun_ech.ech0020 import DeliveryConfig

        assert isinstance(DeliveryConfig, type)
        assert hasattr(DeliveryConfig, '__doc__')
        assert DeliveryConfig.__doc__ is not None


class TestLayer2SupportingModelsImports:
    """Test supporting model classes can be imported and are correct types."""

    def test_person_identification_import(self):
        """Verify PersonIdentification can be imported."""
        from openmun_ech.ech0020 import PersonIdentification

        assert isinstance(PersonIdentification, type)
        assert hasattr(PersonIdentification, '__doc__')
        assert PersonIdentification.__doc__ is not None

    def test_parent_info_import(self):
        """Verify ParentInfo can be imported."""
        from openmun_ech.ech0020 import ParentInfo

        assert isinstance(ParentInfo, type)
        assert hasattr(ParentInfo, '__doc__')
        assert ParentInfo.__doc__ is not None

    def test_guardian_info_import(self):
        """Verify GuardianInfo can be imported."""
        from openmun_ech.ech0020 import GuardianInfo

        assert isinstance(GuardianInfo, type)
        assert hasattr(GuardianInfo, '__doc__')
        assert GuardianInfo.__doc__ is not None

    def test_secondary_residence_info_import(self):
        """Verify SecondaryResidenceInfo can be imported."""
        from openmun_ech.ech0020 import SecondaryResidenceInfo

        assert isinstance(SecondaryResidenceInfo, type)
        assert hasattr(SecondaryResidenceInfo, '__doc__')
        assert SecondaryResidenceInfo.__doc__ is not None

    def test_dwelling_address_info_import(self):
        """Verify DwellingAddressInfo can be imported."""
        from openmun_ech.ech0020 import DwellingAddressInfo

        assert isinstance(DwellingAddressInfo, type)
        assert hasattr(DwellingAddressInfo, '__doc__')
        assert DwellingAddressInfo.__doc__ is not None

    def test_destination_info_import(self):
        """Verify DestinationInfo can be imported."""
        from openmun_ech.ech0020 import DestinationInfo

        assert isinstance(DestinationInfo, type)
        assert hasattr(DestinationInfo, '__doc__')
        assert DestinationInfo.__doc__ is not None


class TestLayer2EnumsImports:
    """Test enum classes can be imported and are correct types."""

    def test_residence_type_import(self):
        """Verify ResidenceType enum can be imported."""
        from openmun_ech.ech0020 import ResidenceType

        assert issubclass(ResidenceType, Enum)
        assert hasattr(ResidenceType, '__doc__')
        assert ResidenceType.__doc__ is not None

        # Verify expected values exist
        assert hasattr(ResidenceType, 'MAIN')
        assert hasattr(ResidenceType, 'SECONDARY')
        assert hasattr(ResidenceType, 'OTHER')

    def test_reporting_type_import(self):
        """Verify ReportingType enum can be imported."""
        from openmun_ech.ech0020 import ReportingType

        assert issubclass(ReportingType, Enum)
        assert hasattr(ReportingType, '__doc__')
        assert ReportingType.__doc__ is not None

    def test_place_type_import(self):
        """Verify PlaceType enum can be imported."""
        from openmun_ech.ech0020 import PlaceType

        assert issubclass(PlaceType, Enum)
        assert hasattr(PlaceType, '__doc__')
        assert PlaceType.__doc__ is not None

    def test_guardian_type_import(self):
        """Verify GuardianType enum can be imported."""
        from openmun_ech.ech0020 import GuardianType

        assert issubclass(GuardianType, Enum)
        assert hasattr(GuardianType, '__doc__')
        assert GuardianType.__doc__ is not None

    def test_date_precision_import(self):
        """Verify DatePrecision enum can be imported."""
        from openmun_ech.ech0020 import DatePrecision

        assert issubclass(DatePrecision, Enum)
        assert hasattr(DatePrecision, '__doc__')
        assert DatePrecision.__doc__ is not None


class TestLayer1AdvancedImport:
    """Test Layer 1 API is available for advanced users."""

    def test_ech0020_delivery_import(self):
        """Verify ECH0020Delivery (Layer 1) can be imported."""
        from openmun_ech.ech0020 import ECH0020Delivery

        assert isinstance(ECH0020Delivery, type)
        assert hasattr(ECH0020Delivery, '__doc__')
        assert ECH0020Delivery.__doc__ is not None


class TestAllExportsComplete:
    """Verify __all__ list matches actual exports and all are importable."""

    def test_all_exports_in_all_list(self):
        """Verify every export in __all__ is actually importable."""
        import openmun_ech.ech0020 as ech0020

        # Get __all__ list
        assert hasattr(ech0020, '__all__')
        exports = ech0020.__all__

        # Verify it's not empty
        assert len(exports) > 0, "__all__ list is empty"

        # Verify each export is importable
        for name in exports:
            assert hasattr(ech0020, name), (
                f"{name} is in __all__ but not importable from ech0020 module"
            )

    def test_all_list_count(self):
        """Verify __all__ contains expected number of exports.

        Expected exports (15 total):
        - 3 main API classes
        - 6 supporting models
        - 5 enums
        - 1 Layer 1 class
        """
        import openmun_ech.ech0020 as ech0020

        expected_count = 15
        actual_count = len(ech0020.__all__)

        assert actual_count == expected_count, (
            f"Expected {expected_count} exports in __all__, "
            f"but found {actual_count}. "
            f"Exports: {', '.join(ech0020.__all__)}"
        )

    def test_expected_exports_present(self):
        """Verify all expected exports are in __all__ list."""
        import openmun_ech.ech0020 as ech0020

        expected_exports = {
            # Main API (3)
            'BaseDeliveryPerson',
            'BaseDeliveryEvent',
            'DeliveryConfig',

            # Supporting models (6)
            'PersonIdentification',
            'ParentInfo',
            'GuardianInfo',
            'SecondaryResidenceInfo',
            'DwellingAddressInfo',
            'DestinationInfo',

            # Enums (5)
            'ResidenceType',
            'ReportingType',
            'PlaceType',
            'GuardianType',
            'DatePrecision',

            # Layer 1 (1)
            'ECH0020Delivery',
        }

        actual_exports = set(ech0020.__all__)

        missing = expected_exports - actual_exports
        extra = actual_exports - expected_exports

        assert not missing, f"Missing exports in __all__: {missing}"
        assert not extra, f"Unexpected exports in __all__: {extra}"


class TestBulkImport:
    """Test that all exports can be imported in a single statement."""

    def test_bulk_import_all_exports(self):
        """Verify all exports can be imported together in one statement."""
        from openmun_ech.ech0020 import (
            # Main API
            BaseDeliveryPerson,
            BaseDeliveryEvent,
            DeliveryConfig,
            # Supporting models
            PersonIdentification,
            ParentInfo,
            GuardianInfo,
            SecondaryResidenceInfo,
            DwellingAddressInfo,
            DestinationInfo,
            # Enums
            ResidenceType,
            ReportingType,
            PlaceType,
            GuardianType,
            DatePrecision,
            # Layer 1
            ECH0020Delivery,
        )

        # Verify all imported successfully (not None)
        assert BaseDeliveryPerson is not None
        assert BaseDeliveryEvent is not None
        assert DeliveryConfig is not None
        assert PersonIdentification is not None
        assert ParentInfo is not None
        assert GuardianInfo is not None
        assert SecondaryResidenceInfo is not None
        assert DwellingAddressInfo is not None
        assert DestinationInfo is not None
        assert ResidenceType is not None
        assert ReportingType is not None
        assert PlaceType is not None
        assert GuardianType is not None
        assert DatePrecision is not None
        assert ECH0020Delivery is not None


if __name__ == "__main__":
    # Run tests when executed directly
    import pytest

    exit_code = pytest.main([__file__, '-v'])
    exit(exit_code)
