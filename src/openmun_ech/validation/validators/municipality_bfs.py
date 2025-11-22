"""Municipality BFS code validator for Swiss open data validation.

This module provides validation for BFS (Bundesamt für Statistik / Federal
Statistical Office) municipality codes using official Swiss municipality data
from the openmun-opendata library.

BFS codes are critical identifiers used throughout Swiss government systems.
They must be validated to ensure accurate data exchange.

Core Principles:
1. User is king - validation provides warnings but never blocks data
2. Fast - RAM-cached municipality data for instant lookups
3. Accurate - Uses official BFS municipality database
4. Optional - Silently disabled if openmun-opendata not available
"""

from typing import Optional

from ..warnings import MunicipalityBFSWarning
from ..context import ValidationContext
from ..cache import MunicipalityCache


class MunicipalityBFSValidator:
    """Validator for Swiss BFS municipality codes.

    This validator checks if BFS codes exist in the official Swiss municipality
    database. It provides warnings for invalid codes but never blocks data entry.

    The validator is stateless and uses a shared MunicipalityCache singleton
    for data lookups.

    Example - Valid BFS Code:
        >>> from openmun_ech.validation import ValidationContext, MunicipalityBFSValidator
        >>> ctx = ValidationContext()
        >>> MunicipalityBFSValidator.validate(
        ...     bfs_code="261",  # Zürich
        ...     municipality_name="Zürich",
        ...     context=ctx
        ... )
        >>> ctx.has_warnings()
        False

    Example - Invalid BFS Code:
        >>> ctx = ValidationContext()
        >>> MunicipalityBFSValidator.validate(
        ...     bfs_code="99999",
        ...     municipality_name="Somewhere",
        ...     context=ctx
        ... )
        >>> ctx.has_warnings()
        True
        >>> print(ctx.warnings[0].message)
        BFS code 99999 not found in Swiss municipality database. Municipality name provided: Somewhere

    Note:
        Requires openmun-opendata package. If not available, validation
        is silently disabled.
    """

    _cache: Optional[MunicipalityCache] = None

    @classmethod
    def _get_cache(cls) -> MunicipalityCache:
        """Get or create the municipality cache instance.

        Returns:
            Shared MunicipalityCache singleton instance.
        """
        if cls._cache is None:
            cls._cache = MunicipalityCache()
        return cls._cache

    @classmethod
    def validate(
        cls,
        bfs_code: str,
        municipality_name: Optional[str],
        context: ValidationContext,
        field_name_prefix: str = "municipality_bfs"
    ) -> None:
        """Validate BFS municipality code.

        This method checks if the BFS code exists in the official Swiss
        municipality database. It adds warnings to the context for invalid
        codes but never raises exceptions.

        Args:
            bfs_code: The BFS municipality code to validate (e.g., "261" for Zürich)
            municipality_name: The municipality name (optional, for better error messages)
            context: ValidationContext to add warnings to
            field_name_prefix: Field name prefix for warning messages (default: "municipality_bfs")

        Side Effects:
            May add MunicipalityBFSWarning to context.
            Never modifies input data or raises exceptions.

        Example - Valid Code:
            >>> ctx = ValidationContext()
            >>> MunicipalityBFSValidator.validate("261", "Zürich", ctx)
            >>> ctx.has_warnings()
            False

        Example - Invalid Code:
            >>> ctx = ValidationContext()
            >>> MunicipalityBFSValidator.validate("99999", "Invalid", ctx)
            >>> ctx.has_warnings()
            True
        """
        # Skip validation if cache not available (openmun-opendata not installed)
        cache = cls._get_cache()
        if not cache.is_available():
            return

        # Normalize input
        bfs_code_clean = bfs_code.strip()

        # Lookup municipality by BFS code
        municipality = cache.get_by_bfs_code(bfs_code_clean)

        if not municipality:
            # BFS code not found - add warning
            context.add_warning(MunicipalityBFSWarning(
                bfs_code=bfs_code,
                municipality_name=municipality_name,
                field_name_prefix=field_name_prefix
            ))
            return

        # BFS code found - validation passed (no warning)
