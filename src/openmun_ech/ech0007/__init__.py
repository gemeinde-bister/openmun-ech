"""eCH-0007 Municipality Component - Versioned exports.

Available versions:
- v5: eCH-0007 v5.0 (used by eCH-0020 v3.0, eCH-0099 v2.1)

Types:
- ECH0007Municipality: Wrapper for Swiss municipality (placeOfOrigin, etc.)
- ECH0007SwissMunicipality: swissMunicipalityType (optional fields)
- ECH0007SwissAndFLMunicipality: swissAndFlMunicipalityType (required fields + FL)
- CantonAbbreviation: 26 Swiss canton codes (for swissMunicipalityType)
- CantonFLAbbreviation: 27 canton codes including FL (for swissAndFlMunicipalityType)
"""

from openmun_ech.ech0007.v5 import (
    ECH0007Municipality,
    ECH0007SwissMunicipality,
    ECH0007SwissAndFLMunicipality,
    CantonAbbreviation,
    CantonFLAbbreviation,
)

__all__ = [
    'ECH0007Municipality',
    'ECH0007SwissMunicipality',
    'ECH0007SwissAndFLMunicipality',
    'CantonAbbreviation',
    'CantonFLAbbreviation',
]
