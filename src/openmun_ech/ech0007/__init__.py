"""eCH-0007 Municipality Component - Versioned exports.

Available versions:
- v5: eCH-0007 v5.0 (used by eCH-0020 v3.0, eCH-0099 v2.1)
- v6: eCH-0007 v6.0 (used by eCH-0129 v6.0)

Types:
- ECH0007Municipality: Wrapper for Swiss municipality (placeOfOrigin, etc.)
- ECH0007SwissMunicipality: swissMunicipalityType (optional fields)
- ECH0007SwissAndFLMunicipality: swissAndFlMunicipalityType (required fields + FL)
- CantonAbbreviation: 26 Swiss canton codes (for swissMunicipalityType)
- CantonFLAbbreviation: 27 canton codes including FL (for swissAndFlMunicipalityType)

v6 types (separate classes with v6 namespace):
- ECH0007v6SwissMunicipality: v6 swissMunicipalityType
- ECH0007v6SwissAndFLMunicipality: v6 swissAndFlMunicipalityType
"""

from openmun_ech.ech0007.v5 import (
    ECH0007Municipality,
    ECH0007SwissMunicipality,
    ECH0007SwissAndFLMunicipality,
    CantonAbbreviation,
    CantonFLAbbreviation,
)
from openmun_ech.ech0007.v6 import (
    ECH0007v6SwissMunicipality,
    ECH0007v6SwissAndFLMunicipality,
)

# Import versioned modules for explicit selection
from . import v5  # noqa: F401
from . import v6  # noqa: F401

__all__ = [
    # Default exports (v5 — used by eCH-0020, eCH-0099)
    'ECH0007Municipality',
    'ECH0007SwissMunicipality',
    'ECH0007SwissAndFLMunicipality',
    'CantonAbbreviation',
    'CantonFLAbbreviation',
    # v6 exports (used by eCH-0129)
    'ECH0007v6SwissMunicipality',
    'ECH0007v6SwissAndFLMunicipality',
    # Version modules
    'v5',
    'v6',
]
