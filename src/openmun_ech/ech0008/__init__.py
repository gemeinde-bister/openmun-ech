"""eCH-0008 Country Component - Versioned exports.

Available versions:
- v3: eCH-0008 v3.0 (used by eCH-0020 v3.0, eCH-0099 v2.1)

Types:
- ECH0008Country: Full country type with BFS code, ISO code, and name (countryType)
- ECH0008CountryShort: Simple country type with only name (countryShortType)

Usage:
    # Create full country from ISO2 code (recommended)
    country = ECH0008Country.from_iso2('CH', language='de')

    # Create full country from BFS code
    country = ECH0008Country.from_bfs_code('8100', language='de')

    # Create short form with only name
    country_short = ECH0008CountryShort.from_country_name('Schweiz')

    # All data comes from auto-generated bfs_country_codes.py
"""

from openmun_ech.ech0008.v3 import ECH0008Country, ECH0008CountryShort

__all__ = ['ECH0008Country', 'ECH0008CountryShort']
