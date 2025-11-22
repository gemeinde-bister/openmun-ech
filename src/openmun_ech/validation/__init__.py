"""Swiss open data validation layer for openmun-ech.

This package provides optional validation of Swiss government data fields
using official open data sources. Validation is always optional and provides
warnings only - it never blocks data entry or modification.

Core Principles:
1. User is king - warnings provide feedback but never prevent data entry
2. Fast - RAM-cached data for instant lookups
3. Accurate - Uses official Swiss government data
4. Optional - Completely opt-in, never required

Quick Start:
    >>> from openmun_ech.ech0020.models import BaseDeliveryPerson
    >>> from openmun_ech.validation import ValidationContext
    >>>
    >>> person = BaseDeliveryPerson(
    ...     dwelling_address_postal_code="8001",
    ...     dwelling_address_town="Basel",  # Wrong!
    ...     # ... other fields ...
    ... )
    >>>
    >>> # Validate (optional)
    >>> ctx = person.validate_swiss_data()
    >>> if ctx.has_warnings():
    ...     for warning in ctx.warnings:
    ...         print(warning)
    ⚠️  dwelling_address_postal_code + dwelling_address_town: Postal code 8001 is typically associated with: Zürich, Zürich Sihlpost

Public API:
    - ValidationContext: Context for collecting warnings
    - ValidationWarning: Base warning class
    - ValidationSeverity: Severity levels (INFO, WARNING, ERROR)
    - PostalCodeWarning: Specific warning for postal code mismatches
    - PostalCodeNotFoundWarning: Warning for unknown postal codes
    - PostalCodeValidator: Validator for postal codes
    - PostalCodeCache: RAM cache for postal code data
    - MunicipalityBFSWarning: Warning for invalid BFS municipality codes
    - MunicipalityBFSValidator: Validator for BFS codes
    - MunicipalityCache: RAM cache for municipality data
    - CantonCodeWarning: Warning for invalid canton codes
    - CantonCodeValidator: Validator for Swiss canton codes
    - StreetNotFoundWarning: Warning for streets not in directory
    - StreetNameWarning: Warning for street name suggestions
    - StreetNameValidator: Validator for Swiss street names
    - StreetCache: RAM cache for street data
    - CrossValidationWarning: Warning for cross-field inconsistencies
    - CrossValidator: Validator for cross-field consistency

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
"""

from .context import ValidationContext
from .warnings import (
    ValidationWarning,
    ValidationSeverity,
    PostalCodeWarning,
    PostalCodeNotFoundWarning,
    MunicipalityBFSWarning,
    CantonCodeWarning,
    StreetNotFoundWarning,
    StreetNameWarning,
    CrossValidationWarning,
)
from .cache import PostalCodeCache, MunicipalityCache, StreetCache
from .validators import (
    PostalCodeValidator,
    MunicipalityBFSValidator,
    CantonCodeValidator,
    StreetNameValidator,
    CrossValidator,
    ReligionCodeValidator,
)

__all__ = [
    # Context
    "ValidationContext",

    # Warnings
    "ValidationWarning",
    "ValidationSeverity",
    "PostalCodeWarning",
    "PostalCodeNotFoundWarning",
    "MunicipalityBFSWarning",
    "CantonCodeWarning",
    "StreetNotFoundWarning",
    "StreetNameWarning",
    "CrossValidationWarning",

    # Cache
    "PostalCodeCache",
    "MunicipalityCache",
    "StreetCache",

    # Validators
    "PostalCodeValidator",
    "MunicipalityBFSValidator",
    "CantonCodeValidator",
    "StreetNameValidator",
    "CrossValidator",
    "ReligionCodeValidator",
]

__version__ = "0.1.0"
