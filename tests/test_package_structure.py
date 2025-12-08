"""Test top-level package structure and organization.

This test suite validates that the package structure follows the documented
design: Layer 1 at top-level, Layer 2 and validation in submodules.

What This File Tests
====================
1. Top-level package has expected Layer 1 exports
2. Layer 2 is NOT at top level (requires explicit import)
3. Validation is NOT at top level (requires explicit import)
4. Submodules (ech0020, validation) exist and are importable
5. Module docstring mentions both layers

Test Coverage
=============
- 9 top-level Layer 1 exports
- 2 submodules (ech0020, validation)
- Docstring content verification
- Import isolation verification

Data Policy
===========
This test file contains NO government data, NO personal data, NO production data.
It only tests package structure and import mechanics.

Related Documentation
=====================
- docs/LAYER2_API_EXPOSURE_PLAN.md: API exposure strategy
- src/openmun_ech/__init__.py: Top-level package definition
- src/openmun_ech/ech0020/__init__.py: Layer 2 API definition
"""


class TestTopLevelPackageImports:
    """Test top-level package exports (Layer 1 components)."""

    def test_package_has_expected_exports(self):
        """Verify top-level package exports Layer 1 components."""
        import openmun_ech

        # Expected exports (11 total)
        expected = {
            'VersionRouter',
            'ECH0020Version',
            'ECH0007Municipality',
            'ECH0008Country',
            'ECH0010MailAddress',
            'ECH0011Person',
            'ECH0021PersonAdditionalData',
            'ECH0044PersonIdentification',
            'ECH0058Header',
            'get_label',  # i18n label lookup
            'get_desc',   # spec documentation lookup
        }

        # Verify __all__ matches expected
        actual = set(openmun_ech.__all__)
        assert actual == expected, (
            f"Top-level exports mismatch.\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}\n"
            f"Missing: {expected - actual}\n"
            f"Extra: {actual - expected}"
        )

    def test_layer1_components_importable(self):
        """Verify all Layer 1 components can be imported from top-level."""
        from openmun_ech import (
            VersionRouter,
            ECH0020Version,
            ECH0007Municipality,
            ECH0008Country,
            ECH0010MailAddress,
            ECH0011Person,
            ECH0021PersonAdditionalData,
            ECH0044PersonIdentification,
            ECH0058Header,
        )

        # Verify all imported successfully (not None)
        assert VersionRouter is not None
        assert ECH0020Version is not None
        assert ECH0007Municipality is not None
        assert ECH0008Country is not None
        assert ECH0010MailAddress is not None
        assert ECH0011Person is not None
        assert ECH0021PersonAdditionalData is not None
        assert ECH0044PersonIdentification is not None
        assert ECH0058Header is not None


class TestLayer2NotAtTopLevel:
    """Verify Layer 2 is NOT at top-level (requires explicit import)."""

    def test_layer2_classes_not_at_toplevel(self):
        """Verify Layer 2 classes are NOT available at top level."""
        import openmun_ech

        # Layer 2 classes should NOT be at top level
        layer2_classes = [
            'BaseDeliveryPerson',
            'BaseDeliveryEvent',
            'DeliveryConfig',
        ]

        for cls_name in layer2_classes:
            assert not hasattr(openmun_ech, cls_name), (
                f"{cls_name} should NOT be at top level. "
                f"Users must import explicitly: "
                f"from openmun_ech.ech0020 import {cls_name}"
            )

    def test_layer2_requires_explicit_import(self):
        """Verify Layer 2 requires explicit submodule import."""
        # This should work (explicit import)
        from openmun_ech.ech0020 import BaseDeliveryPerson

        assert BaseDeliveryPerson is not None

        # Verify it's NOT available at top level
        import openmun_ech
        assert not hasattr(openmun_ech, 'BaseDeliveryPerson')


class TestValidationNotAtTopLevel:
    """Verify validation is NOT at top-level (requires explicit import)."""

    def test_validation_classes_not_at_toplevel(self):
        """Verify validation classes are NOT available at top level."""
        import openmun_ech

        # Validation classes should NOT be at top level
        validation_classes = [
            'ValidationContext',
            'ValidationWarning',
            'PostalCodeValidator',
        ]

        for cls_name in validation_classes:
            assert not hasattr(openmun_ech, cls_name), (
                f"{cls_name} should NOT be at top level. "
                f"Users must import explicitly: "
                f"from openmun_ech.validation import {cls_name}"
            )

    def test_validation_requires_explicit_import(self):
        """Verify validation requires explicit submodule import."""
        # This should work (explicit import)
        from openmun_ech.validation import ValidationContext

        assert ValidationContext is not None

        # Verify it's NOT available at top level
        import openmun_ech
        assert not hasattr(openmun_ech, 'ValidationContext')


class TestSubmodulesExist:
    """Verify expected submodules exist and are importable."""

    def test_ech0020_submodule_exists(self):
        """Verify ech0020 submodule exists."""
        import openmun_ech
        assert hasattr(openmun_ech, 'ech0020')

    def test_validation_submodule_exists(self):
        """Verify validation submodule exists."""
        import openmun_ech
        assert hasattr(openmun_ech, 'validation')

    def test_ech0020_submodule_importable(self):
        """Verify ech0020 submodule can be imported."""
        import openmun_ech.ech0020

        # Should have __all__
        assert hasattr(openmun_ech.ech0020, '__all__')
        # Should have Layer 2 classes
        assert hasattr(openmun_ech.ech0020, 'BaseDeliveryPerson')
        assert hasattr(openmun_ech.ech0020, 'BaseDeliveryEvent')

    def test_validation_submodule_importable(self):
        """Verify validation submodule can be imported."""
        import openmun_ech.validation

        # Should have __all__
        assert hasattr(openmun_ech.validation, '__all__')
        # Should have validation classes
        assert hasattr(openmun_ech.validation, 'ValidationContext')
        assert hasattr(openmun_ech.validation, 'PostalCodeValidator')


class TestModuleDocstring:
    """Verify module docstring content."""

    def test_docstring_exists(self):
        """Verify top-level module has docstring."""
        import openmun_ech

        assert openmun_ech.__doc__ is not None
        assert len(openmun_ech.__doc__) > 100

    def test_docstring_mentions_layer2(self):
        """Verify docstring mentions Layer 2."""
        import openmun_ech

        assert 'Layer 2' in openmun_ech.__doc__
        assert 'Layer 2 API' in openmun_ech.__doc__

    def test_docstring_mentions_layer1(self):
        """Verify docstring mentions Layer 1."""
        import openmun_ech

        assert 'Layer 1' in openmun_ech.__doc__
        assert 'Layer 1 API' in openmun_ech.__doc__

    def test_docstring_mentions_validation(self):
        """Verify docstring mentions validation."""
        import openmun_ech

        docstring_lower = openmun_ech.__doc__.lower()
        assert 'validation' in docstring_lower

    def test_docstring_has_no_emojis(self):
        """Verify docstring contains no emojis."""
        import openmun_ech

        # Check for emoji unicode ranges
        # Emojis typically start at U+1F300
        has_emoji = any(ord(char) >= 0x1F300 for char in openmun_ech.__doc__)
        assert not has_emoji, "Module docstring should not contain emojis"

    def test_docstring_mentions_submodules(self):
        """Verify docstring documents submodule structure."""
        import openmun_ech

        # Should mention key submodules
        assert 'ech0020' in openmun_ech.__doc__
        assert 'validation' in openmun_ech.__doc__


class TestImportPaths:
    """Verify documented import paths work correctly."""

    def test_layer2_import_path(self):
        """Verify documented Layer 2 import path works."""
        # As documented in module docstring
        from openmun_ech.ech0020 import BaseDeliveryPerson, BaseDeliveryEvent
        from openmun_ech.ech0020 import DeliveryConfig

        assert BaseDeliveryPerson is not None
        assert BaseDeliveryEvent is not None
        assert DeliveryConfig is not None

    def test_layer1_import_path(self):
        """Verify documented Layer 1 import path works."""
        # As documented in module docstring
        from openmun_ech import ECH0058Header, ECH0007Municipality

        assert ECH0058Header is not None
        assert ECH0007Municipality is not None

    def test_validation_import_path(self):
        """Verify documented validation import path works."""
        # As documented in module docstring
        from openmun_ech.validation import ValidationContext

        assert ValidationContext is not None


if __name__ == "__main__":
    # Run tests when executed directly
    import pytest

    exit_code = pytest.main([__file__, '-v'])
    exit(exit_code)
