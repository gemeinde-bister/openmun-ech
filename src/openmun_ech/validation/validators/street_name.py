"""Street name validator for Swiss addresses.

This module provides validation for Swiss street names against the official
federal street directory (Amtliches Strassenverzeichnis from swisstopo).

Core Principle: Provide helpful warnings without blocking user input.
"""

from typing import Optional
from ..context import ValidationContext
from ..warnings import StreetNotFoundWarning, StreetNameWarning
from ..cache import StreetCache


class StreetNameValidator:
    """Validator for Swiss street names.

    This validator checks if a street name exists in the official Swiss street
    directory (Amtliches Strassenverzeichnis). It can optionally filter by
    municipality or postal code for more precise validation.

    The validator uses fuzzy matching to handle:
    - Case variations (Bahnhofstrasse vs bahnhofstrasse)
    - Umlauts (Zürich vs Zurich)
    - Abbreviations (Bahnhofstr vs Bahnhofstrasse)

    The validator uses a RAM-cached singleton for fast lookups after initial load.

    Class Attributes:
        _cache: Shared street cache instance (lazy-initialized)

    Example - Direct Usage:
        >>> from openmun_ech.validation import ValidationContext, StreetNameValidator
        >>>
        >>> ctx = ValidationContext()
        >>> StreetNameValidator.validate(
        ...     street_name="Bahnhofstrase",  # Typo
        ...     municipality_bfs="261",
        ...     context=ctx
        ... )
        >>> if ctx.has_warnings():
        ...     print(ctx.warnings[0])
        ⚠️  street: Did you mean 'Bahnhofstrasse'?

    Example - Through BaseDeliveryPerson:
        >>> from openmun_ech.ech0020.models import BaseDeliveryPerson
        >>>
        >>> person = BaseDeliveryPerson(
        ...     contact_address_street="Bahnhofstrase",  # Typo
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

    _cache: Optional[StreetCache] = None

    @classmethod
    def _get_cache(cls) -> StreetCache:
        """Get or create the street cache instance.

        Returns:
            Shared StreetCache singleton instance.
        """
        if cls._cache is None:
            cls._cache = StreetCache()
        return cls._cache

    @classmethod
    def validate(
        cls,
        street_name: str,
        context: ValidationContext,
        municipality_bfs: Optional[str] = None,
        municipality_name: Optional[str] = None,
        postal_code: Optional[str] = None,
        field_name_prefix: str = "street"
    ) -> None:
        """Validate street name against Swiss street directory.

        This method checks if the street name exists in the official Swiss
        street directory. It can optionally filter by municipality or postal
        code for more precise validation.

        Args:
            street_name: The street name to validate (e.g., "Bahnhofstrasse")
            context: ValidationContext to add warnings to
            municipality_bfs: Optional BFS municipality code to filter (e.g., "261" for Zürich)
            municipality_name: Optional municipality name (for display purposes)
            postal_code: Optional postal code to filter (e.g., "8001")
            field_name_prefix: Field name prefix for warning messages (default: "street")

        Side Effects:
            May add StreetNotFoundWarning or StreetNameWarning to context.
            Never modifies input data or raises exceptions.

        Example - Exact Match:
            >>> ctx = ValidationContext()
            >>> StreetNameValidator.validate("Bahnhofstrasse", ctx, municipality_bfs="261")
            >>> ctx.has_warnings()
            False

        Example - Not Found:
            >>> ctx = ValidationContext()
            >>> StreetNameValidator.validate("Nonsense Street", ctx, municipality_bfs="261")
            >>> ctx.has_warnings()
            True
            >>> print(ctx.warnings[0])
            ⚠️  street: Street 'Nonsense Street' not found in Swiss street directory

        Example - Fuzzy Match (Suggestions):
            >>> ctx = ValidationContext()
            >>> StreetNameValidator.validate("Bahnhofstr", ctx, municipality_bfs="261")
            >>> ctx.has_warnings()
            False  # Fuzzy match succeeded (abbreviation)
        """
        # Skip validation if cache not available (openmun-opendata not installed)
        cache = cls._get_cache()
        if not cache.is_available():
            return

        # Normalize input
        street_name_clean = street_name.strip()

        # If street name is empty, skip validation
        if not street_name_clean:
            return

        # Search for street (with optional filters)
        matches = cache.find_by_name(
            street_name=street_name_clean,
            municipality_bfs=municipality_bfs,
            postal_code=postal_code
        )

        if not matches:
            # Street not found - add warning
            context.add_warning(StreetNotFoundWarning(
                street_name=street_name_clean,
                municipality_bfs=municipality_bfs,
                postal_code=postal_code,
                municipality_name=municipality_name,
                field_name_prefix=field_name_prefix
            ))
            return

        # Check if entered name exactly matches any result
        normalized_search = cache._normalize_street_name(street_name_clean)
        exact_match = any(
            cache._normalize_street_name(match.name) == normalized_search
            for match in matches
        )

        if exact_match:
            # Exact match found - no warning needed
            return

        # Fuzzy match found - provide suggestions (info level, not warning)
        suggested_streets = [match.name for match in matches[:5]]  # Top 5 matches
        context.add_warning(StreetNameWarning(
            street_entered=street_name_clean,
            suggested_streets=suggested_streets,
            municipality_name=municipality_name or (matches[0].municipality_name if matches else None),
            field_name_prefix=field_name_prefix
        ))
