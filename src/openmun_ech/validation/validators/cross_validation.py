"""Cross-field validators for Swiss open data.

This module provides validators that check consistency across multiple fields,
such as postal code vs municipality, street vs postal code, etc.

Core Principle: Provide helpful warnings without blocking user input.
"""

from typing import Optional, List
from ..context import ValidationContext
from ..warnings import CrossValidationWarning
from ..cache import PostalCodeCache, MunicipalityCache, StreetCache


class CrossValidator:
    """Validator for cross-field consistency checks.

    This validator checks that multiple fields are consistent with each other
    using official Swiss open data. It can detect inconsistencies like:

    - Postal code doesn't match municipality
    - Street doesn't exist in postal code
    - Municipality doesn't serve postal code

    The validator uses RAM-cached singletons for fast lookups after initial load.

    Class Attributes:
        _postal_cache: Shared postal code cache instance (lazy-initialized)
        _municipality_cache: Shared municipality cache instance (lazy-initialized)
        _street_cache: Shared street cache instance (lazy-initialized)

    Example - Postal Code vs Municipality:
        >>> from openmun_ech.validation import ValidationContext, CrossValidator
        >>>
        >>> ctx = ValidationContext()
        >>> CrossValidator.validate_postal_municipality(
        ...     postal_code="8001",  # Zürich
        ...     municipality_bfs="4001",  # Basel - WRONG!
        ...     context=ctx
        ... )
        >>> if ctx.has_warnings():
        ...     print(ctx.warnings[0])
        ⚠️  postal_code + municipality_bfs: Postal code 8001 belongs to Zürich, but BFS 4001 is Basel

    Example - Street vs Postal Code:
        >>> ctx = ValidationContext()
        >>> CrossValidator.validate_street_postal(
        ...     street_name="Bahnhofstrasse",
        ...     postal_code="8001",  # Zürich - correct
        ...     context=ctx
        ... )
        >>> ctx.has_warnings()
        False  # Bahnhofstrasse exists in Zürich

    Note:
        Requires openmun-opendata package. If not available, validation
        is silently disabled.
    """

    _postal_cache: Optional[PostalCodeCache] = None
    _municipality_cache: Optional[MunicipalityCache] = None
    _street_cache: Optional[StreetCache] = None

    @classmethod
    def _get_postal_cache(cls) -> PostalCodeCache:
        """Get or create the postal code cache instance."""
        if cls._postal_cache is None:
            cls._postal_cache = PostalCodeCache()
        return cls._postal_cache

    @classmethod
    def _get_municipality_cache(cls) -> MunicipalityCache:
        """Get or create the municipality cache instance."""
        if cls._municipality_cache is None:
            cls._municipality_cache = MunicipalityCache()
        return cls._municipality_cache

    @classmethod
    def _get_street_cache(cls) -> StreetCache:
        """Get or create the street cache instance."""
        if cls._street_cache is None:
            cls._street_cache = StreetCache()
        return cls._street_cache

    @classmethod
    def validate_postal_municipality(
        cls,
        postal_code: str,
        municipality_bfs: str,
        context: ValidationContext,
        field_name_prefix_postal: str = "postal_code",
        field_name_prefix_municipality: str = "municipality_bfs"
    ) -> None:
        """Validate that postal code matches municipality.

        Checks if the given postal code is served by the given municipality.
        Swiss municipalities can have multiple postal codes, and postal codes
        can span multiple municipalities (though less common).

        Args:
            postal_code: The postal code to check (e.g., "8001")
            municipality_bfs: The BFS municipality code (e.g., "261" for Zürich)
            context: ValidationContext to add warnings to
            field_name_prefix_postal: Field name prefix for postal code
            field_name_prefix_municipality: Field name prefix for municipality

        Side Effects:
            May add CrossValidationWarning to context if inconsistency detected.
            Never modifies input data or raises exceptions.

        Example:
            >>> ctx = ValidationContext()
            >>> CrossValidator.validate_postal_municipality("8001", "261", ctx)
            >>> ctx.has_warnings()
            False  # 8001 is Zürich, BFS 261 is Zürich - match!

            >>> ctx = ValidationContext()
            >>> CrossValidator.validate_postal_municipality("8001", "4001", ctx)
            >>> ctx.has_warnings()
            True  # 8001 is Zürich, but BFS 4001 is Basel - mismatch!
        """
        # Skip validation if caches not available
        postal_cache = cls._get_postal_cache()
        municipality_cache = cls._get_municipality_cache()

        if not postal_cache.is_available() or not municipality_cache.is_available():
            return

        # Normalize inputs
        postal_code_clean = postal_cache.normalize_postal_code(postal_code)
        municipality_bfs_clean = str(municipality_bfs).strip()

        # Get postal code localities
        localities = postal_cache.get_localities(postal_code_clean)
        if not localities:
            # Postal code not found - PostalCodeValidator will handle this
            return

        # Get municipality info
        municipality = municipality_cache.get_by_bfs_code(municipality_bfs_clean)
        if not municipality:
            # Municipality not found - MunicipalityBFSValidator will handle this
            return

        # Check if postal code serves this municipality
        # Compare municipality BFS codes from postal code data
        postal_municipalities = set()
        for locality in localities:
            # PostalLocalityV1 has bfs_number field (BFS code)
            if hasattr(locality, 'bfs_number') and locality.bfs_number:
                postal_municipalities.add(str(locality.bfs_number))

        if municipality_bfs_clean not in postal_municipalities:
            # Postal code doesn't serve this municipality - add warning
            # Build locality names for message
            locality_names = [loc.locality_name for loc in localities[:3]]
            if len(localities) > 3:
                locality_str = f"{', '.join(locality_names)} (and {len(localities) - 3} more)"
            else:
                locality_str = ', '.join(locality_names)

            message = (
                f"Postal code {postal_code} belongs to {locality_str}, "
                f"but BFS {municipality_bfs} is {municipality.name}"
            )

            context.add_warning(CrossValidationWarning(
                field1_name=field_name_prefix_postal,
                field1_value=postal_code,
                field2_name=field_name_prefix_municipality,
                field2_value=municipality_bfs,
                inconsistency_type="postal_municipality_mismatch",
                message=message,
                suggestions=[loc.locality_name for loc in localities]
            ))

    @classmethod
    def validate_street_postal(
        cls,
        street_name: str,
        postal_code: str,
        context: ValidationContext,
        municipality_bfs: Optional[str] = None,
        field_name_prefix_street: str = "street",
        field_name_prefix_postal: str = "postal_code"
    ) -> None:
        """Validate that street exists in postal code area.

        Checks if the given street name exists in the area served by the
        given postal code. Can optionally also filter by municipality for
        more precise validation.

        Args:
            street_name: The street name to check (e.g., "Bahnhofstrasse")
            postal_code: The postal code (e.g., "8001")
            context: ValidationContext to add warnings to
            municipality_bfs: Optional BFS code for additional filtering
            field_name_prefix_street: Field name prefix for street
            field_name_prefix_postal: Field name prefix for postal code

        Side Effects:
            May add CrossValidationWarning to context if street not in postal area.
            Never modifies input data or raises exceptions.

        Example:
            >>> ctx = ValidationContext()
            >>> CrossValidator.validate_street_postal("Bahnhofstrasse", "8001", ctx)
            >>> ctx.has_warnings()
            False  # Bahnhofstrasse exists in 8001 Zürich

            >>> ctx = ValidationContext()
            >>> CrossValidator.validate_street_postal("Bahnhofstrasse", "3004", ctx)
            >>> ctx.has_warnings()
            True  # Bahnhofstrasse Zürich not in 3004 Bern postal area
        """
        # Skip validation if caches not available
        street_cache = cls._get_street_cache()
        postal_cache = cls._get_postal_cache()

        if not street_cache.is_available() or not postal_cache.is_available():
            return

        # Normalize inputs
        street_name_clean = street_name.strip()
        postal_code_clean = postal_cache.normalize_postal_code(postal_code)

        if not street_name_clean:
            return

        # Find street with postal code filter
        matches = street_cache.find_by_name(
            street_name=street_name_clean,
            postal_code=postal_code_clean,
            municipality_bfs=municipality_bfs
        )

        if not matches:
            # Street doesn't exist in this postal code area
            # Get postal code locality for message
            localities = postal_cache.get_localities(postal_code_clean)
            if not localities:
                # Postal code not found - PostalCodeValidator will handle this
                return

            locality_name = localities[0].locality_name

            message = (
                f"Street '{street_name}' not found in postal code {postal_code} "
                f"({locality_name})"
            )

            # Try to find the street in other postal codes for suggestions
            all_matches = street_cache.find_by_name(
                street_name=street_name_clean,
                municipality_bfs=municipality_bfs
            )

            suggestions: Optional[List[str]] = None
            if all_matches:
                # Build suggestions with postal codes
                suggestions = []
                for match in all_matches[:3]:
                    postal_codes_str = ', '.join(match.postal_code_list[:2])
                    suggestions.append(
                        f"{match.name} in {match.municipality_name} ({postal_codes_str})"
                    )

            context.add_warning(CrossValidationWarning(
                field1_name=field_name_prefix_street,
                field1_value=street_name,
                field2_name=field_name_prefix_postal,
                field2_value=postal_code,
                inconsistency_type="street_postal_mismatch",
                message=message,
                suggestions=suggestions
            ))
