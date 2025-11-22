"""Validation warning classes for Swiss open data validation.

This module provides warning classes that are used to report potential
data quality issues without blocking data entry. All warnings are
informational only and never raise exceptions.

Core Principle: User is king - warnings provide feedback but never prevent
data entry or modification.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity levels for validation warnings.

    Attributes:
        INFO: Informational message (e.g., data enrichment suggestions)
        WARNING: Potential issue detected (e.g., postal code mismatch)
        ERROR: Likely incorrect data (but still allowed)
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationWarning(BaseModel):
    """Base class for all validation warnings.

    Validation warnings are informational only - they never block data entry.
    Applications can inspect warnings and optionally prompt users for confirmation,
    but the final decision always rests with the user.

    Attributes:
        field_name: Name of the field(s) being validated
        field_value: Current value of the field(s)
        severity: Warning severity level
        message: Human-readable description of the issue
        suggestions: Optional list of suggested corrections

    Example:
        >>> warning = ValidationWarning(
        ...     field_name="postal_code",
        ...     field_value="8001",
        ...     severity=ValidationSeverity.WARNING,
        ...     message="Postal code 8001 is typically associated with Zürich",
        ...     suggestions=["Zürich", "Zürich Sihlpost"]
        ... )
        >>> print(warning)
        ⚠️  postal_code: Postal code 8001 is typically associated with Zürich
    """

    field_name: str = Field(..., description="Name of the field(s) being validated")
    field_value: str = Field(..., description="Current value of the field(s)")
    severity: ValidationSeverity = Field(..., description="Warning severity level")
    message: str = Field(..., description="Human-readable description of the issue")
    suggestions: Optional[List[str]] = Field(
        None,
        description="Optional list of suggested corrections"
    )

    def __str__(self) -> str:
        """Return human-readable warning message.

        Returns:
            Formatted warning string with emoji indicator based on severity.
        """
        severity_emoji = {
            ValidationSeverity.INFO: "ℹ️",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.ERROR: "❌"
        }
        emoji = severity_emoji.get(self.severity, "⚠️")
        return f"{emoji}  {self.field_name}: {self.message}"


class PostalCodeWarning(ValidationWarning):
    """Validation warning for postal code + town mismatches.

    This warning is raised when a postal code does not match the entered town name.
    Swiss postal codes can map to multiple localities, so this warning includes
    all valid town names for the given postal code.

    Attributes:
        postal_code: The postal code being validated
        town_entered: The town name entered by the user
        valid_towns: List of valid town names for this postal code

    Example:
        >>> warning = PostalCodeWarning(
        ...     postal_code="8001",
        ...     town_entered="Basel",
        ...     valid_towns=["Zürich", "Zürich Sihlpost"]
        ... )
        >>> print(warning)
        ⚠️  dwelling_address_postal_code + dwelling_address_town: Postal code 8001 is typically associated with: Zürich, Zürich Sihlpost
        >>> warning.suggestions
        ['Zürich', 'Zürich Sihlpost']
    """

    postal_code: str = Field(..., description="Postal code being validated")
    town_entered: str = Field(..., description="Town name entered by user")
    valid_towns: List[str] = Field(..., description="Valid town names for this postal code")

    def __init__(self, postal_code: str, town_entered: str, valid_towns: List[str],
                 field_name_prefix: str = "postal_code + town", **kwargs):
        """Initialize postal code warning.

        Args:
            postal_code: The postal code being validated
            town_entered: The town name entered by the user
            valid_towns: List of valid town names for this postal code
            field_name_prefix: Prefix for field name (e.g., "contact_address", "dwelling_address")
            **kwargs: Additional keyword arguments passed to parent class
        """
        # Format message with up to 3 town suggestions
        towns_display = ", ".join(valid_towns[:3])
        if len(valid_towns) > 3:
            towns_display += f" (and {len(valid_towns) - 3} more)"

        super().__init__(
            field_name=field_name_prefix,
            field_value=f"{postal_code} / {town_entered}",
            severity=ValidationSeverity.WARNING,
            message=f"Postal code {postal_code} is typically associated with: {towns_display}",
            suggestions=valid_towns,
            postal_code=postal_code,
            town_entered=town_entered,
            valid_towns=valid_towns,
            **kwargs
        )


class PostalCodeNotFoundWarning(ValidationWarning):
    """Validation warning for postal codes not found in the Swiss database.

    This warning is raised when a postal code is not found in the official
    Swiss postal code database. This may indicate:
    - A foreign address (Liechtenstein uses Swiss postal codes but may not be in database)
    - A typo in the postal code
    - An outdated postal code (historical codes that are no longer valid)

    Attributes:
        postal_code: The postal code that was not found

    Example:
        >>> warning = PostalCodeNotFoundWarning(postal_code="9999")
        >>> print(warning)
        ⚠️  dwelling_address_postal_code: Postal code 9999 not found in Swiss postal code database
    """

    postal_code: str = Field(..., description="Postal code that was not found")

    def __init__(self, postal_code: str, field_name_prefix: str = "postal_code", **kwargs):
        """Initialize postal code not found warning.

        Args:
            postal_code: The postal code that was not found
            field_name_prefix: Prefix for field name (e.g., "contact_address", "dwelling_address")
            **kwargs: Additional keyword arguments passed to parent class
        """
        super().__init__(
            field_name=field_name_prefix,
            field_value=postal_code,
            severity=ValidationSeverity.WARNING,
            message=(
                f"Postal code {postal_code} not found in Swiss postal code database. "
                f"This may be a foreign address or a typo."
            ),
            suggestions=None,
            postal_code=postal_code,
            **kwargs
        )


class MunicipalityBFSWarning(ValidationWarning):
    """Validation warning for invalid BFS municipality codes.

    This warning is raised when a BFS (Bundesamt für Statistik / Federal Statistical
    Office) municipality code is not found in the official Swiss municipality database.
    This may indicate:
    - A typo in the BFS code
    - An outdated/historical BFS code (for merged municipalities)
    - A completely invalid code

    BFS codes are official Swiss municipality identifiers used throughout government
    systems. They are critical for accurate data exchange and must be validated.

    Attributes:
        bfs_code: The BFS code that was not found
        municipality_name: The municipality name provided (if any)

    Example:
        >>> warning = MunicipalityBFSWarning(
        ...     bfs_code="99999",
        ...     municipality_name="Zürich"
        ... )
        >>> print(warning)
        ⚠️  birth_municipality_bfs: BFS code 99999 not found in Swiss municipality database
    """

    bfs_code: str = Field(..., description="BFS code that was not found")
    municipality_name: Optional[str] = Field(None, description="Municipality name provided")

    def __init__(
        self,
        bfs_code: str,
        municipality_name: Optional[str] = None,
        field_name_prefix: str = "municipality_bfs",
        **kwargs
    ):
        """Initialize municipality BFS warning.

        Args:
            bfs_code: The BFS code that was not found
            municipality_name: The municipality name provided (if any)
            field_name_prefix: Prefix for field name (e.g., "birth_municipality", "reporting_municipality")
            **kwargs: Additional keyword arguments passed to parent class
        """
        # Build message
        message = f"BFS code {bfs_code} not found in Swiss municipality database."

        if municipality_name:
            message += f" Municipality name provided: {municipality_name}"

        super().__init__(
            field_name=field_name_prefix,
            field_value=bfs_code,
            severity=ValidationSeverity.WARNING,
            message=message,
            suggestions=None,
            bfs_code=bfs_code,
            municipality_name=municipality_name,
            **kwargs
        )


class CantonCodeWarning(ValidationWarning):
    """Validation warning for invalid Swiss canton codes.

    This warning is raised when a canton abbreviation is not one of the 26 official
    Swiss canton codes (ZH, BE, LU, UR, SZ, OW, NW, GL, ZG, FR, SO, BS, BL, SH,
    AR, AI, SG, GR, AG, TG, TI, VD, VS, NE, GE, JU).

    Canton codes are standardized 2-letter abbreviations used throughout Swiss
    government systems and must be validated.

    Attributes:
        canton_code: The canton code that was invalid
        valid_cantons: List of valid canton codes (for reference)

    Example:
        >>> warning = CantonCodeWarning(canton_code="XX")
        >>> print(warning)
        ⚠️  canton: Invalid canton code 'XX'. Valid codes: ZH, BE, LU, UR, SZ, OW, NW, GL, ZG, FR, SO, BS, BL, SH, AR, AI, SG, GR, AG, TG, TI, VD, VS, NE, GE, JU
    """

    canton_code: str = Field(..., description="Canton code that was invalid")
    valid_cantons: List[str] = Field(..., description="List of valid canton codes")

    def __init__(
        self,
        canton_code: str,
        field_name_prefix: str = "canton",
        **kwargs
    ):
        """Initialize canton code warning.

        Args:
            canton_code: The canton code that was invalid
            field_name_prefix: Prefix for field name (e.g., "birth_canton", "marriage_canton")
            **kwargs: Additional keyword arguments passed to parent class
        """
        # All 26 Swiss canton codes
        valid_cantons = [
            "ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR",
            "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG",
            "TI", "VD", "VS", "NE", "GE", "JU"
        ]

        # Build message with valid codes
        cantons_str = ", ".join(valid_cantons)
        message = f"Invalid canton code '{canton_code}'. Valid codes: {cantons_str}"

        super().__init__(
            field_name=field_name_prefix,
            field_value=canton_code,
            severity=ValidationSeverity.WARNING,
            message=message,
            suggestions=valid_cantons,
            canton_code=canton_code,
            valid_cantons=valid_cantons,
            **kwargs
        )


class StreetNotFoundWarning(ValidationWarning):
    """Validation warning for street names not found in the Swiss street directory.

    This warning is raised when a street name is not found in the official
    Swiss street directory (Amtliches Strassenverzeichnis) for a given
    municipality or postal code. This may indicate:
    - A typo in the street name
    - A very new street not yet in the database
    - An informal street name (not the official name)
    - A foreign address (outside Switzerland)

    Attributes:
        street_name: The street name that was not found
        municipality_bfs: Optional BFS code that was searched
        postal_code: Optional postal code that was searched

    Example:
        >>> warning = StreetNotFoundWarning(
        ...     street_name="Bahnhofstrase",  # Typo
        ...     municipality_bfs="261"
        ... )
        >>> print(warning)
        ⚠️  contact_address_street: Street 'Bahnhofstrase' not found in Zürich (BFS 261)
    """

    street_name: str = Field(..., description="Street name that was not found")
    municipality_bfs: Optional[str] = Field(None, description="BFS code searched")
    postal_code: Optional[str] = Field(None, description="Postal code searched")

    def __init__(
        self,
        street_name: str,
        municipality_bfs: Optional[str] = None,
        postal_code: Optional[str] = None,
        municipality_name: Optional[str] = None,
        field_name_prefix: str = "street",
        **kwargs
    ):
        """Initialize street not found warning.

        Args:
            street_name: The street name that was not found
            municipality_bfs: Optional BFS code that was searched
            postal_code: Optional postal code that was searched
            municipality_name: Optional municipality name (for display)
            field_name_prefix: Prefix for field name (e.g., "contact_address", "dwelling_address")
            **kwargs: Additional keyword arguments passed to parent class
        """
        # Build context message
        context_parts = []
        if municipality_name and municipality_bfs:
            context_parts.append(f"{municipality_name} (BFS {municipality_bfs})")
        elif municipality_bfs:
            context_parts.append(f"BFS {municipality_bfs}")

        if postal_code:
            context_parts.append(f"postal code {postal_code}")

        context_str = " in " + " / ".join(context_parts) if context_parts else ""

        message = (
            f"Street '{street_name}' not found in Swiss street directory{context_str}. "
            f"This may be a typo, an informal name, or a very new street."
        )

        super().__init__(
            field_name=field_name_prefix,
            field_value=street_name,
            severity=ValidationSeverity.WARNING,
            message=message,
            suggestions=None,
            street_name=street_name,
            municipality_bfs=municipality_bfs,
            postal_code=postal_code,
            **kwargs
        )


class StreetNameWarning(ValidationWarning):
    """Validation warning for street name mismatches or suggestions.

    This warning is raised when a street name is found but there are better
    matches or potential typos detected. It provides suggestions for the
    correct street name.

    Attributes:
        street_entered: The street name entered by the user
        suggested_streets: List of suggested street names
        municipality_name: Optional municipality name for context

    Example:
        >>> warning = StreetNameWarning(
        ...     street_entered="Bahnhofstrase",  # Typo
        ...     suggested_streets=["Bahnhofstrasse"],
        ...     municipality_name="Zürich"
        ... )
        >>> print(warning)
        ⚠️  contact_address_street: Did you mean 'Bahnhofstrasse'?
    """

    street_entered: str = Field(..., description="Street name entered by user")
    suggested_streets: List[str] = Field(..., description="Suggested street names")
    municipality_name: Optional[str] = Field(None, description="Municipality name for context")

    def __init__(
        self,
        street_entered: str,
        suggested_streets: List[str],
        municipality_name: Optional[str] = None,
        field_name_prefix: str = "street",
        **kwargs
    ):
        """Initialize street name warning.

        Args:
            street_entered: The street name entered by the user
            suggested_streets: List of suggested street names
            municipality_name: Optional municipality name for context
            field_name_prefix: Prefix for field name (e.g., "contact_address", "dwelling_address")
            **kwargs: Additional keyword arguments passed to parent class
        """
        # Build message with suggestions
        if len(suggested_streets) == 1:
            message = f"Did you mean '{suggested_streets[0]}'?"
        else:
            # Show up to 3 suggestions
            streets_display = ", ".join(f"'{s}'" for s in suggested_streets[:3])
            if len(suggested_streets) > 3:
                streets_display += f" (and {len(suggested_streets) - 3} more)"
            message = f"Similar streets found: {streets_display}"

        if municipality_name:
            message += f" (in {municipality_name})"

        super().__init__(
            field_name=field_name_prefix,
            field_value=street_entered,
            severity=ValidationSeverity.INFO,
            message=message,
            suggestions=suggested_streets,
            street_entered=street_entered,
            suggested_streets=suggested_streets,
            municipality_name=municipality_name,
            **kwargs
        )


class CrossValidationWarning(ValidationWarning):
    """Validation warning for cross-field validation failures.

    This warning is raised when multiple fields are inconsistent with each other,
    such as:
    - Postal code doesn't match municipality BFS code
    - Street doesn't exist in the given postal code
    - Municipality doesn't serve the given postal code

    Attributes:
        field1_name: Name of the first field
        field1_value: Value of the first field
        field2_name: Name of the second field
        field2_value: Value of the second field
        inconsistency_type: Type of inconsistency detected

    Example:
        >>> warning = CrossValidationWarning(
        ...     field1_name="postal_code",
        ...     field1_value="8001",
        ...     field2_name="municipality_bfs",
        ...     field2_value="4001",
        ...     inconsistency_type="postal_municipality_mismatch",
        ...     message="Postal code 8001 (Zürich) doesn't match BFS 4001 (Basel)"
        ... )
        >>> print(warning)
        ⚠️  postal_code + municipality_bfs: Postal code 8001 (Zürich) doesn't match BFS 4001 (Basel)
    """

    field1_name: str = Field(..., description="Name of first field")
    field1_value: str = Field(..., description="Value of first field")
    field2_name: str = Field(..., description="Name of second field")
    field2_value: str = Field(..., description="Value of second field")
    inconsistency_type: str = Field(..., description="Type of inconsistency")

    def __init__(
        self,
        field1_name: str,
        field1_value: str,
        field2_name: str,
        field2_value: str,
        inconsistency_type: str,
        message: str,
        suggestions: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize cross-validation warning.

        Args:
            field1_name: Name of the first field
            field1_value: Value of the first field
            field2_name: Name of the second field
            field2_value: Value of the second field
            inconsistency_type: Type of inconsistency (e.g., "postal_municipality_mismatch")
            message: Human-readable description of the inconsistency
            suggestions: Optional list of suggested corrections
            **kwargs: Additional keyword arguments passed to parent class
        """
        super().__init__(
            field_name=f"{field1_name} + {field2_name}",
            field_value=f"{field1_value} / {field2_value}",
            severity=ValidationSeverity.WARNING,
            message=message,
            suggestions=suggestions,
            field1_name=field1_name,
            field1_value=field1_value,
            field2_name=field2_name,
            field2_value=field2_value,
            inconsistency_type=inconsistency_type,
            **kwargs
        )
