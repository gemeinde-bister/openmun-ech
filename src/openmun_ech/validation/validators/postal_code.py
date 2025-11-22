"""Postal code validator for Swiss addresses.

This module provides validation for Swiss postal codes against town names,
using official Swiss open data from the Federal Office of Topography.

Core Principle: Provide helpful warnings without blocking user input.
"""

from typing import Optional
from ..context import ValidationContext
from ..warnings import PostalCodeWarning, PostalCodeNotFoundWarning
from ..cache import PostalCodeCache


class PostalCodeValidator:
    """Validator for Swiss postal code + town combinations.

    This validator checks if a postal code matches the entered town name
    using official Swiss postal code data. It provides warnings for mismatches
    but never blocks data entry.

    The validator uses a RAM-cached singleton for fast lookups after initial load.

    Class Attributes:
        _cache: Shared postal code cache instance (lazy-initialized)

    Example - Direct Usage:
        >>> from openmun_ech.validation import ValidationContext, PostalCodeValidator
        >>>
        >>> ctx = ValidationContext()
        >>> PostalCodeValidator.validate(
        ...     postal_code="8001",
        ...     town="Basel",
        ...     context=ctx
        ... )
        >>> if ctx.has_warnings():
        ...     print(ctx.warnings[0])
        ⚠️  dwelling_address_postal_code + dwelling_address_town: Postal code 8001 is typically associated with: Zürich, Zürich Sihlpost

    Example - Through BaseDeliveryPerson:
        >>> from openmun_ech.ech0020.models import BaseDeliveryPerson
        >>>
        >>> person = BaseDeliveryPerson(
        ...     dwelling_address_postal_code="8001",
        ...     dwelling_address_town="Basel",
        ...     # ... other fields ...
        ... )
        >>>
        >>> ctx = person.validate_swiss_data()
        >>> if ctx.has_warnings():
        ...     for warning in ctx.warnings:
        ...         print(warning)

    Note:
        Requires openmun-opendata package. If not available, validation
        is silently disabled.
    """

    _cache: Optional[PostalCodeCache] = None

    @classmethod
    def _get_cache(cls) -> PostalCodeCache:
        """Get or create the postal code cache instance.

        Returns:
            Shared PostalCodeCache singleton instance.
        """
        if cls._cache is None:
            cls._cache = PostalCodeCache()
        return cls._cache

    @classmethod
    def validate(
        cls,
        postal_code: str,
        town: str,
        context: ValidationContext,
        field_name_prefix: str = "postal_code + town"
    ) -> None:
        """Validate postal code + town combination.

        This method checks if the postal code matches the town name using
        official Swiss postal code data. It adds warnings to the context
        for any mismatches but never raises exceptions.

        Args:
            postal_code: The postal code to validate (e.g., "8001", " 8001 ", "801")
            town: The town name to validate (e.g., "Zürich", "Basel")
            context: ValidationContext to add warnings to
            field_name_prefix: Field name prefix for warning messages (default: "postal_code + town")

        Side Effects:
            May add PostalCodeWarning or PostalCodeNotFoundWarning to context.
            Never modifies input data or raises exceptions.

        Example - Correct Match:
            >>> ctx = ValidationContext()
            >>> PostalCodeValidator.validate("8001", "Zürich", ctx)
            >>> ctx.has_warnings()
            False

        Example - Mismatch:
            >>> ctx = ValidationContext()
            >>> PostalCodeValidator.validate("8001", "Basel", ctx)
            >>> ctx.has_warnings()
            True
            >>> print(ctx.warnings[0].suggestions)
            ['Zürich', 'Zürich Sihlpost']

        Example - Unknown Postal Code:
            >>> ctx = ValidationContext()
            >>> PostalCodeValidator.validate("9999", "Test", ctx)
            >>> ctx.has_warnings()
            True
            >>> "not found" in str(ctx.warnings[0])
            True
        """
        # Skip validation if cache not available (openmun-opendata not installed)
        cache = cls._get_cache()
        if not cache.is_available():
            return

        # Normalize inputs
        postal_code_clean = cache.normalize_postal_code(postal_code)
        town_clean = town.strip()

        # Lookup valid localities for this postal code
        localities = cache.get_localities(postal_code_clean)

        if not localities:
            # Postal code not found in Swiss database
            context.add_warning(PostalCodeNotFoundWarning(
                postal_code=postal_code,
                field_name_prefix=field_name_prefix
            ))
            return

        # Extract valid town names from localities
        valid_towns = [loc.locality_name for loc in localities]

        # Check if entered town matches any valid locality (case-insensitive)
        town_lower = town_clean.lower()
        matches = [
            t for t in valid_towns
            if cls._fuzzy_match_town(t, town_lower)
        ]

        if not matches:
            # Town doesn't match any valid locality - add warning
            context.add_warning(PostalCodeWarning(
                postal_code=postal_code,
                town_entered=town,
                valid_towns=valid_towns,
                field_name_prefix=field_name_prefix
            ))

    @staticmethod
    def _fuzzy_match_town(valid_town: str, entered_town_lower: str) -> bool:
        """Fuzzy match town names (case-insensitive, handles common variations).

        Args:
            valid_town: Official town name from postal code database
            entered_town_lower: User-entered town name (already lowercased)

        Returns:
            True if towns match (fuzzy), False otherwise.

        Examples:
            >>> PostalCodeValidator._fuzzy_match_town("Zürich", "zürich")
            True
            >>> PostalCodeValidator._fuzzy_match_town("Zürich", "zurich")  # ASCII variant
            True
            >>> PostalCodeValidator._fuzzy_match_town("Zürich Sihlpost", "zürich")  # Partial
            True
            >>> PostalCodeValidator._fuzzy_match_town("Basel", "zürich")
            False
        """
        valid_lower = valid_town.lower()

        # Exact match (case-insensitive)
        if valid_lower == entered_town_lower:
            return True

        # Partial match (entered town is beginning of valid town)
        # Example: "Zürich" matches "Zürich Sihlpost"
        if valid_lower.startswith(entered_town_lower):
            return True

        # ASCII variant match (ü -> u, ä -> a, ö -> o, etc.)
        valid_ascii = PostalCodeValidator._to_ascii(valid_lower)
        entered_ascii = PostalCodeValidator._to_ascii(entered_town_lower)

        if valid_ascii == entered_ascii:
            return True

        if valid_ascii.startswith(entered_ascii):
            return True

        return False

    @staticmethod
    def _to_ascii(text: str) -> str:
        """Convert text to ASCII approximation (for fuzzy matching).

        Converts Swiss German umlauts and special characters to ASCII equivalents.

        Args:
            text: Text to convert (should already be lowercased)

        Returns:
            ASCII approximation of the text

        Examples:
            >>> PostalCodeValidator._to_ascii("zürich")
            'zurich'
            >>> PostalCodeValidator._to_ascii("bern")
            'bern'
            >>> PostalCodeValidator._to_ascii("genève")
            'geneve'
        """
        # Swiss German umlauts
        replacements = {
            'ä': 'a', 'ö': 'o', 'ü': 'u',
            'à': 'a', 'è': 'e', 'é': 'e', 'ê': 'e',
            'ô': 'o', 'û': 'u', 'ç': 'c'
        }

        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)

        return result
