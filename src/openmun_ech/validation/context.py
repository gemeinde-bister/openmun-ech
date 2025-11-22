"""Validation context for collecting warnings without raising exceptions.

This module provides the ValidationContext class which is used to collect
validation warnings during Swiss open data validation. The context never
raises exceptions, allowing users to complete data entry while still being
informed of potential issues.

Core Principle: User is king - validation provides feedback but never blocks.
"""

from typing import List, Optional
from .warnings import ValidationWarning, ValidationSeverity


class ValidationContext:
    """Context for collecting validation warnings without raising exceptions.

    The ValidationContext accumulates warnings during validation but never
    raises exceptions. This allows the user to complete data entry regardless
    of validation issues, while still providing feedback about potential problems.

    Applications can inspect the collected warnings and optionally prompt users
    for confirmation, but the final decision always rests with the user.

    Attributes:
        warnings: List of collected validation warnings

    Example - Basic Usage:
        >>> from openmun_ech.validation import ValidationContext
        >>> from openmun_ech.ech0020.models import BaseDeliveryPerson
        >>>
        >>> person = BaseDeliveryPerson(
        ...     dwelling_address_postal_code="8001",
        ...     dwelling_address_town="Basel",  # Wrong!
        ...     # ... other required fields ...
        ... )
        >>>
        >>> ctx = person.validate_swiss_data()
        >>> if ctx.has_warnings():
        ...     for warning in ctx.warnings:
        ...         print(warning)

    Example - Interactive Validation:
        >>> ctx = person.validate_swiss_data()
        >>> if ctx.has_warnings():
        ...     for warning in ctx.warnings:
        ...         print(f"\\nWarning: {warning}")
        ...         if warning.suggestions:
        ...             print("Suggestions:")
        ...             for suggestion in warning.suggestions[:5]:
        ...                 print(f"  - {suggestion}")
        ...         response = input("Continue anyway? (y/n): ")
        ...         if response.lower() != 'y':
        ...             print("Cancelled")
        ...             break

    Example - Filter by Severity:
        >>> ctx = person.validate_swiss_data()
        >>> if ctx.has_warnings(ValidationSeverity.ERROR):
        ...     print("Critical issues found!")
        >>>
        >>> errors = ctx.get_warnings_by_severity(ValidationSeverity.ERROR)
        >>> for error in errors:
        ...     print(error)
    """

    def __init__(self):
        """Initialize empty validation context."""
        self.warnings: List[ValidationWarning] = []

    def add_warning(self, warning: ValidationWarning) -> None:
        """Add a validation warning to the context.

        This method never raises exceptions. It simply accumulates warnings
        for later inspection.

        Args:
            warning: The validation warning to add
        """
        self.warnings.append(warning)

    def has_warnings(self, severity: Optional[ValidationSeverity] = None) -> bool:
        """Check if any warnings exist, optionally filtered by severity.

        Args:
            severity: Optional severity level to filter by. If None, checks
                     for any warnings regardless of severity.

        Returns:
            True if warnings exist (matching the severity if specified), False otherwise.

        Examples:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> ctx.has_warnings()  # Check for any warnings
            True
            >>> ctx.has_warnings(ValidationSeverity.ERROR)  # Check for errors only
            False
        """
        if severity is None:
            return len(self.warnings) > 0
        return any(w.severity == severity for w in self.warnings)

    def get_warnings(self, field_name: Optional[str] = None) -> List[ValidationWarning]:
        """Get warnings, optionally filtered by field name.

        Args:
            field_name: Optional field name to filter by. If None, returns all warnings.

        Returns:
            List of validation warnings matching the filter criteria.

        Examples:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> all_warnings = ctx.get_warnings()
            >>> postal_warnings = ctx.get_warnings("dwelling_address_postal_code")
        """
        if field_name is None:
            return self.warnings
        return [w for w in self.warnings if w.field_name == field_name]

    def get_warnings_by_severity(self, severity: ValidationSeverity) -> List[ValidationWarning]:
        """Get warnings filtered by severity level.

        Args:
            severity: The severity level to filter by.

        Returns:
            List of validation warnings matching the specified severity.

        Examples:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> errors = ctx.get_warnings_by_severity(ValidationSeverity.ERROR)
            >>> warnings = ctx.get_warnings_by_severity(ValidationSeverity.WARNING)
        """
        return [w for w in self.warnings if w.severity == severity]

    def clear(self) -> None:
        """Clear all warnings from the context.

        This is useful if you want to reuse the same context object for
        multiple validation runs.

        Example:
            >>> ctx = ValidationContext()
            >>> person1.validate_swiss_data(ctx)
            >>> print(f"Person 1: {len(ctx.warnings)} warnings")
            >>> ctx.clear()
            >>> person2.validate_swiss_data(ctx)
            >>> print(f"Person 2: {len(ctx.warnings)} warnings")
        """
        self.warnings.clear()

    def count(self, severity: Optional[ValidationSeverity] = None) -> int:
        """Count warnings, optionally filtered by severity.

        Args:
            severity: Optional severity level to filter by. If None, counts all warnings.

        Returns:
            Number of warnings matching the filter criteria.

        Examples:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> total = ctx.count()
            >>> errors = ctx.count(ValidationSeverity.ERROR)
            >>> warnings = ctx.count(ValidationSeverity.WARNING)
        """
        if severity is None:
            return len(self.warnings)
        return sum(1 for w in self.warnings if w.severity == severity)

    def __len__(self) -> int:
        """Return the total number of warnings.

        Returns:
            Total number of warnings in the context.

        Example:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> print(f"Found {len(ctx)} warnings")
        """
        return len(self.warnings)

    def __bool__(self) -> bool:
        """Return True if context has any warnings.

        Returns:
            True if warnings exist, False otherwise.

        Example:
            >>> ctx = ValidationContext()
            >>> # ... validation that adds warnings ...
            >>> if ctx:
            ...     print("Warnings found!")
        """
        return len(self.warnings) > 0

    def __repr__(self) -> str:
        """Return developer-friendly string representation.

        Returns:
            String representation showing warning count and severity breakdown.
        """
        if not self.warnings:
            return "ValidationContext(warnings=0)"

        errors = self.count(ValidationSeverity.ERROR)
        warnings = self.count(ValidationSeverity.WARNING)
        infos = self.count(ValidationSeverity.INFO)

        return (
            f"ValidationContext(warnings={len(self.warnings)}, "
            f"errors={errors}, warnings={warnings}, info={infos})"
        )

    def __str__(self) -> str:
        """Return user-friendly string representation.

        Returns:
            Formatted string listing all warnings.
        """
        if not self.warnings:
            return "No validation warnings"

        lines = [f"Validation warnings ({len(self.warnings)}):"]
        for i, warning in enumerate(self.warnings, 1):
            lines.append(f"  {i}. {warning}")

        return "\n".join(lines)
