"""Canton code validator for Swiss open data validation.

This module provides validation for Swiss canton abbreviations (2-letter codes).
The 26 official Swiss canton codes are: ZH, BE, LU, UR, SZ, OW, NW, GL, ZG, FR,
SO, BS, BL, SH, AR, AI, SG, GR, AG, TG, TI, VD, VS, NE, GE, JU.

Canton codes are standardized identifiers used throughout Swiss government systems
and must be validated to ensure data quality.

Core Principles:
1. User is king - validation provides warnings but never blocks data
2. Fast - Simple set lookup (O(1))
3. Accurate - Uses official Swiss canton abbreviations
4. No dependencies - Uses built-in Python only
"""

from typing import Set

from ..warnings import CantonCodeWarning
from ..context import ValidationContext


class CantonCodeValidator:
    """Validator for Swiss canton codes.

    This validator checks if canton abbreviations are valid Swiss canton codes.
    It provides warnings for invalid codes but never blocks data entry.

    The validator is stateless and uses a static set of 26 Swiss cantons.

    Example - Valid Canton Code:
        >>> from openmun_ech.validation import ValidationContext, CantonCodeValidator
        >>> ctx = ValidationContext()
        >>> CantonCodeValidator.validate("ZH", ctx)
        >>> ctx.has_warnings()
        False

    Example - Invalid Canton Code:
        >>> ctx = ValidationContext()
        >>> CantonCodeValidator.validate("XX", ctx)
        >>> ctx.has_warnings()
        True
        >>> print(ctx.warnings[0].message)
        Invalid canton code 'XX'. Valid codes: ZH, BE, LU, ...

    Note:
        This validator requires no external dependencies and works with any
        Python installation.
    """

    # All 26 Swiss canton codes (static, never changes)
    VALID_CANTONS: Set[str] = {
        "ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR",
        "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG",
        "TI", "VD", "VS", "NE", "GE", "JU"
    }

    @classmethod
    def validate(
        cls,
        canton_code: str,
        context: ValidationContext,
        field_name_prefix: str = "canton"
    ) -> None:
        """Validate Swiss canton code.

        This method checks if the canton code is one of the 26 official Swiss
        canton abbreviations. It adds warnings to the context for invalid
        codes but never raises exceptions.

        Args:
            canton_code: The canton code to validate (e.g., "ZH", "BE", "GE")
            context: ValidationContext to add warnings to
            field_name_prefix: Field name prefix for warning messages (default: "canton")

        Side Effects:
            May add CantonCodeWarning to context.
            Never modifies input data or raises exceptions.

        Example - Valid Code:
            >>> ctx = ValidationContext()
            >>> CantonCodeValidator.validate("ZH", ctx)
            >>> ctx.has_warnings()
            False

        Example - Invalid Code:
            >>> ctx = ValidationContext()
            >>> CantonCodeValidator.validate("XX", ctx, "birth_canton")
            >>> ctx.has_warnings()
            True
            >>> ctx.warnings[0].field_name
            'birth_canton'
        """
        # Skip validation if canton code not provided
        if not canton_code:
            return

        # Normalize to uppercase for case-insensitive comparison
        canton_upper = canton_code.strip().upper()

        # Check if canton code is valid
        if canton_upper not in cls.VALID_CANTONS:
            # Invalid canton code - add warning
            context.add_warning(CantonCodeWarning(
                canton_code=canton_code,
                field_name_prefix=field_name_prefix
            ))
