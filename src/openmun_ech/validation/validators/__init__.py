"""Validators for Swiss open data validation.

This package contains validator classes for specific data types.
Each validator validates one or more related fields and adds warnings
to the ValidationContext without raising exceptions.
"""

from .postal_code import PostalCodeValidator
from .municipality_bfs import MunicipalityBFSValidator
from .canton_code import CantonCodeValidator
from .street_name import StreetNameValidator
from .cross_validation import CrossValidator
from .religion_code import ReligionCodeValidator

__all__ = [
    "PostalCodeValidator",
    "MunicipalityBFSValidator",
    "CantonCodeValidator",
    "StreetNameValidator",
    "CrossValidator",
    "ReligionCodeValidator",
]
