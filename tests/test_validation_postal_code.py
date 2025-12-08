"""Tests for postal code validation using Swiss open data.

These tests verify that postal code validation works correctly with
the openmun-opendata library and that warnings are generated appropriately.
"""

from datetime import date
import pytest

from openmun_ech.validation import (
    ValidationContext,
    ValidationSeverity,
    PostalCodeWarning,
    PostalCodeNotFoundWarning,
    PostalCodeValidator,
    PostalCodeCache,
)
from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType


class TestPostalCodeCache:
    """Test the PostalCodeCache singleton."""

    def test_singleton_pattern(self):
        """Test that PostalCodeCache returns same instance."""
        cache1 = PostalCodeCache()
        cache2 = PostalCodeCache()

        assert cache1 is cache2, "PostalCodeCache should be a singleton"

    def test_normalize_postal_code(self):
        """Test postal code normalization."""
        assert PostalCodeCache.normalize_postal_code("8001") == "8001"
        assert PostalCodeCache.normalize_postal_code(" 8001 ") == "8001"
        assert PostalCodeCache.normalize_postal_code("801") == "0801"
        assert PostalCodeCache.normalize_postal_code("1") == "0001"
        assert PostalCodeCache.normalize_postal_code("  123  ") == "0123"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_get_localities_zurich(self):
        """Test getting localities for Zürich postal code."""
        cache = PostalCodeCache()
        localities = cache.get_localities("8001")

        assert len(localities) > 0, "Should find localities for 8001"
        locality_names = [loc.locality_name for loc in localities]
        assert any("Zürich" in name for name in locality_names), \
            "Should find Zürich in localities"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_get_localities_invalid(self):
        """Test getting localities for invalid postal code."""
        cache = PostalCodeCache()
        localities = cache.get_localities("9999")

        assert len(localities) == 0, "Should not find localities for invalid code"


class TestPostalCodeValidator:
    """Test the PostalCodeValidator."""

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_correct_match(self):
        """Test that correct postal code + town passes without warning."""
        ctx = ValidationContext()

        PostalCodeValidator.validate(
            postal_code="8001",
            town="Zürich",
            context=ctx
        )

        assert not ctx.has_warnings(), \
            "Correct match should not generate warnings"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_mismatch(self):
        """Test that incorrect town triggers warning."""
        ctx = ValidationContext()

        PostalCodeValidator.validate(
            postal_code="8001",
            town="Basel",
            context=ctx
        )

        assert ctx.has_warnings(), "Mismatch should generate warning"
        warning = ctx.warnings[0]
        assert isinstance(warning, PostalCodeWarning), \
            "Should generate PostalCodeWarning"
        assert "Zürich" in warning.message, \
            "Warning should mention correct town"
        assert "8001" in warning.message, \
            "Warning should mention postal code"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_invalid_postal_code(self):
        """Test that invalid postal code triggers warning."""
        ctx = ValidationContext()

        PostalCodeValidator.validate(
            postal_code="9999",
            town="Test",
            context=ctx
        )

        assert ctx.has_warnings(), "Invalid postal code should generate warning"
        warning = ctx.warnings[0]
        assert isinstance(warning, PostalCodeNotFoundWarning), \
            "Should generate PostalCodeNotFoundWarning"
        assert "9999" in warning.message, \
            "Warning should mention postal code"
        assert "not found" in warning.message.lower(), \
            "Warning should indicate postal code not found"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_fuzzy_match_case_insensitive(self):
        """Test case-insensitive matching."""
        ctx = ValidationContext()

        PostalCodeValidator.validate(
            postal_code="8001",
            town="zürich",  # lowercase
            context=ctx
        )

        assert not ctx.has_warnings(), \
            "Case-insensitive match should work"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_fuzzy_match_ascii_variant(self):
        """Test ASCII variant matching (u instead of ü)."""
        ctx = ValidationContext()

        PostalCodeValidator.validate(
            postal_code="8001",
            town="Zurich",  # ASCII variant
            context=ctx
        )

        assert not ctx.has_warnings(), \
            "ASCII variant match should work"


class TestBaseDeliveryPersonValidation:
    """Test validation integration with BaseDeliveryPerson."""

    def _create_minimal_person(self, postal_code: str, town: str) -> BaseDeliveryPerson:
        """Create a minimal person with specified postal code and town."""
        return BaseDeliveryPerson(
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",
            nationalities=[{
                'country_id': '8100',
                'country_iso': 'CH',
                'country_name_short': 'Schweiz'
            }],
            places_of_origin=[{
                'bfs_code': '261',
                'name': 'Zürich',
                'canton': 'ZH'
            }],
            contact_address_postal_code=postal_code,
            contact_address_town=town,
            data_lock="0",
            paper_lock="0"
        )

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_swiss_data_no_warnings(self):
        """Test validate_swiss_data with correct data."""
        person = self._create_minimal_person("8001", "Zürich")

        ctx = person.validate_swiss_data()

        assert not ctx.has_warnings(), \
            "Correct data should not generate warnings"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_swiss_data_with_warnings(self):
        """Test validate_swiss_data with incorrect data."""
        person = self._create_minimal_person("8001", "Basel")

        ctx = person.validate_swiss_data()

        assert ctx.has_warnings(), \
            "Incorrect data should generate warnings"
        assert len(ctx.warnings) == 1, \
            "Should have exactly one warning"
        warning = ctx.warnings[0]
        assert isinstance(warning, PostalCodeWarning), \
            "Should be a PostalCodeWarning"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validate_swiss_data_reuse_context(self):
        """Test reusing ValidationContext for multiple validations."""
        person1 = self._create_minimal_person("8001", "Basel")  # Wrong
        person2 = self._create_minimal_person("3001", "Zürich")  # Wrong (Bern postal code)

        ctx = ValidationContext()
        person1.validate_swiss_data(ctx)
        person2.validate_swiss_data(ctx)

        assert ctx.count() == 2, \
            "Should have warnings from both persons"

    def test_validate_swiss_data_no_postal_code(self):
        """Test validation when postal code not provided."""
        person = BaseDeliveryPerson(
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Müller",
            first_name="Hans",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",
            nationalities=[{
                'country_id': '8100',
                'country_iso': 'CH',
                'country_name_short': 'Schweiz'
            }],
            places_of_origin=[{
                'bfs_code': '261',
                'name': 'Zürich',
                'canton': 'ZH'
            }],
            # No contact_address_postal_code
            data_lock="0",
            paper_lock="0"
        )

        ctx = person.validate_swiss_data()

        assert not ctx.has_warnings(), \
            "Should not validate when postal code not provided"

    @pytest.mark.skipif(not PostalCodeCache().is_available(),
                       reason="openmun-opendata not available")
    def test_validation_warnings_have_suggestions(self):
        """Test that PostalCodeWarning includes suggestions."""
        person = self._create_minimal_person("8001", "Basel")

        ctx = person.validate_swiss_data()

        assert ctx.has_warnings()
        warning = ctx.warnings[0]
        assert warning.suggestions is not None, \
            "Warning should have suggestions"
        assert len(warning.suggestions) > 0, \
            "Should have at least one suggestion"
        assert any("Zürich" in s for s in warning.suggestions), \
            "Suggestions should include Zürich"


class TestValidationContext:
    """Test ValidationContext functionality."""

    def test_context_empty_initially(self):
        """Test that new context has no warnings."""
        ctx = ValidationContext()

        assert len(ctx) == 0
        assert not ctx.has_warnings()
        assert len(ctx.warnings) == 0

    def test_context_add_warning(self):
        """Test adding warnings to context."""
        ctx = ValidationContext()
        warning = PostalCodeNotFoundWarning(postal_code="9999")

        ctx.add_warning(warning)

        assert len(ctx) == 1
        assert ctx.has_warnings()
        assert ctx.warnings[0] == warning

    def test_context_filter_by_severity(self):
        """Test filtering warnings by severity."""
        ctx = ValidationContext()

        # Add warnings with different severities
        ctx.add_warning(PostalCodeNotFoundWarning(postal_code="9999"))  # WARNING
        ctx.add_warning(PostalCodeWarning("8001", "Basel", ["Zürich"]))  # WARNING

        warnings = ctx.get_warnings_by_severity(ValidationSeverity.WARNING)
        errors = ctx.get_warnings_by_severity(ValidationSeverity.ERROR)

        assert len(warnings) == 2
        assert len(errors) == 0

    def test_context_count(self):
        """Test counting warnings."""
        ctx = ValidationContext()

        assert ctx.count() == 0

        ctx.add_warning(PostalCodeNotFoundWarning(postal_code="9999"))
        assert ctx.count() == 1

        ctx.add_warning(PostalCodeWarning("8001", "Basel", ["Zürich"]))
        assert ctx.count() == 2

    def test_context_clear(self):
        """Test clearing warnings from context."""
        ctx = ValidationContext()
        ctx.add_warning(PostalCodeNotFoundWarning(postal_code="9999"))

        assert len(ctx) == 1

        ctx.clear()

        assert len(ctx) == 0
        assert not ctx.has_warnings()

    def test_context_bool(self):
        """Test context boolean conversion."""
        ctx = ValidationContext()

        assert not ctx  # Empty context is False

        ctx.add_warning(PostalCodeNotFoundWarning(postal_code="9999"))

        assert ctx  # Context with warnings is True

    def test_context_str(self):
        """Test context string representation."""
        ctx = ValidationContext()
        ctx.add_warning(PostalCodeNotFoundWarning(postal_code="9999"))

        s = str(ctx)

        assert "9999" in s
        assert "Validation warnings" in s
