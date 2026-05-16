"""eCH-0008 Country Data.

Standard: eCH-0008 v3.0 (Country codes)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides country identification using BFS country codes,
ISO codes, and multilingual names.

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/country_mapper.py
"""

from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_opendata.countries import get_country, get_country_by_bfs


class ECH0008Country(ECHModel):
    """eCH-0008 Country.

    Represents a country with BFS code, ISO code, and multilingual names.

    XML Schema: eCH-0008 v3.0 countryType
    """

    __xml_ns__ = NS.ECH0008_V3
    __xml_element__ = 'country'

    country_id: Optional[str] = xml_field('countryId', default=None, min_length=4, max_length=4)
    country_id_iso2: Optional[str] = xml_field('countryIdISO2', default=None, min_length=2, max_length=2)
    country_name_short: str = xml_field('countryNameShort', min_length=1, max_length=50)

    @field_validator('country_id')
    @classmethod
    def validate_country_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate BFS country code format."""
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"Country ID must be numeric, got: {v}")
        if len(v) != 4:
            raise ValueError(f"Country ID must be exactly 4 digits, got: {v}")
        return v

    @field_validator('country_id_iso2')
    @classmethod
    def validate_iso2(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO2 code format."""
        if v is None:
            return None
        if len(v) != 2:
            raise ValueError(f"ISO2 code must be exactly 2 characters, got: {v}")
        return v.upper()

    @classmethod
    def from_bfs_code(cls, bfs_code: str, language: str = 'de') -> 'ECH0008Country':
        """Create country from BFS code.

        Args:
            bfs_code: BFS country code (e.g., '8100')
            language: Language for country name ('de', 'fr', 'it', 'en')

        Returns:
            Country instance

        Raises:
            ValueError: If BFS code not found
        """
        country = get_country_by_bfs(bfs_code)
        if not country:
            raise ValueError(f"Unknown BFS country code: {bfs_code}")

        return cls(
            country_id=bfs_code,
            country_id_iso2=country.iso2,
            country_name_short=country.get_name(language)
        )

    @classmethod
    def from_iso2(cls, iso2_code: str, language: str = 'de') -> 'ECH0008Country':
        """Create country from ISO2 code.

        Args:
            iso2_code: ISO 3166-1 alpha-2 code (e.g., 'CH')
            language: Language for country name ('de', 'fr', 'it', 'en')

        Returns:
            Country instance

        Raises:
            ValueError: If ISO2 code not found
        """
        country = get_country(iso2_code)
        if not country:
            raise ValueError(f"Unknown ISO2 country code: {iso2_code}")

        return cls(
            country_id=country.bfs_code,
            country_id_iso2=country.iso2,
            country_name_short=country.get_name(language)
        )


class ECH0008CountryShort(ECHModel):
    """eCH-0008 Country Short Form.

    Simpler alternative to ECH0008Country when only the country name is needed,
    without BFS code or ISO code.

    XML Schema: eCH-0008 v3.0 countryShortType (XSD lines 32-36)
    PDF Reference: Page 5, Section 4

    Use case (from PDF):
    "Je nach Aufgabenstellung können Schnittstellenstandards welche den eCH-0008
    importieren, den countryType oder den countryShortType verwenden."
    """

    __xml_ns__ = NS.ECH0008_V3
    __xml_element__ = 'country'

    country_name_short: str = xml_field('countryNameShort', min_length=1, max_length=50)

    @classmethod
    def from_country_name(cls, country_name: str) -> 'ECH0008CountryShort':
        """Create country short form from name.

        Args:
            country_name: Country name (any language)

        Returns:
            Country short instance

        Raises:
            ValueError: If name is invalid
        """
        if not country_name or len(country_name.strip()) == 0:
            raise ValueError("Country name cannot be empty")
        if len(country_name) > 50:
            raise ValueError(f"Country name too long (max 50 chars): {country_name}")

        return cls(country_name_short=country_name.strip())
