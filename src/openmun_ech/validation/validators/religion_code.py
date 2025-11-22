"""Religion code validator (warning-only).

Validates that a provided religion code exists in the eCH-0011 ReligionCode
enum. Adds a non-blocking warning to ValidationContext if unknown.
"""

from typing import Optional, List

from ...ech0011.enums import ReligionCode
from ..context import ValidationContext
from ..warnings import ValidationWarning, ValidationSeverity


class ReligionCodeValidator:
    """Warning-only validator for religion codes.

    - Does not raise exceptions
    - Adds a WARNING if the code is not in ReligionCode enum
    """

    @classmethod
    def validate(
        cls,
        code: Optional[str],
        context: ValidationContext,
        field_name_prefix: str = "religion"
    ) -> None:
        if not code:
            return

        allowed: List[str] = [e.value for e in ReligionCode]
        if code not in allowed:
            context.add_warning(ValidationWarning(
                field_name=field_name_prefix,
                field_value=code,
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Religion code '{code}' is not in the eCH-0011 code list. "
                    f"Accepted values include: {', '.join(allowed)}"
                ),
                suggestions=allowed,
            ))


