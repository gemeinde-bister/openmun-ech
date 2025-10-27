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

import xml.etree.ElementTree as ET
from typing import Optional, Dict

from pydantic import BaseModel, Field, field_validator

from openmun_opendata.countries import get_country, get_country_by_bfs


class ECH0008Country(BaseModel):
    """eCH-0008 Country.

    Represents a country with BFS code, ISO code, and multilingual names.

    XML Schema: eCH-0008 v3.0 countryType
    """

    country_id: Optional[str] = Field(
        None,
        min_length=4,
        max_length=4,
        description="BFS country code (4 digits, e.g., '8100' for Switzerland, optional per XSD)"
    )
    country_id_iso2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code (e.g., 'CH')"
    )
    country_name_short: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Short country name (language-specific, max 50 chars per eCH-0008 XSD, required)"
    )

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


    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0008/3',
               element_name: str = 'country',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements (countryId, countryIdISO2, countryNameShort)
            element_name: Name of container element (usually 'country')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)

        Returns:
            XML Element
        """
        # Use wrapper_namespace for the wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Country ID (BFS code) - optional per XSD - always in eCH-0008 namespace
        if self.country_id:
            country_id_elem = ET.SubElement(elem, f'{{{namespace}}}countryId')
            country_id_elem.text = self.country_id

        # Country ISO2 code - optional - always in eCH-0008 namespace
        if self.country_id_iso2:
            iso2_elem = ET.SubElement(elem, f'{{{namespace}}}countryIdISO2')
            iso2_elem.text = self.country_id_iso2

        # Country name short - required - always in eCH-0008 namespace
        name_elem = ET.SubElement(elem, f'{{{namespace}}}countryNameShort')
        name_elem.text = self.country_name_short

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0008/3') -> 'ECH0008Country':
        """Import from XML element.

        Args:
            elem: XML element (country container)
            namespace: XML namespace URI

        Returns:
            Parsed country object

        Raises:
            ValueError: If required fields missing or invalid
        """
        ns = {'eCH-0008': namespace}

        # Extract required field (countryNameShort)
        country_name_elem = elem.find('eCH-0008:countryNameShort', ns)
        if country_name_elem is None or not country_name_elem.text:
            raise ValueError("Missing required field: countryNameShort")

        # Extract optional fields
        country_id_elem = elem.find('eCH-0008:countryId', ns)
        country_id = country_id_elem.text.strip() if country_id_elem is not None and country_id_elem.text else None

        iso2_elem = elem.find('eCH-0008:countryIdISO2', ns)
        iso2 = iso2_elem.text.strip() if iso2_elem is not None and iso2_elem.text else None

        return cls(
            country_id=country_id,
            country_id_iso2=iso2,
            country_name_short=country_name_elem.text.strip()
        )


class ECH0008CountryShort(BaseModel):
    """eCH-0008 Country Short Form.

    Simpler alternative to ECH0008Country when only the country name is needed,
    without BFS code or ISO code.

    XML Schema: eCH-0008 v3.0 countryShortType (XSD lines 32-36)
    PDF Reference: Page 5, Section 4

    Use case (from PDF):
    "Je nach Aufgabenstellung können Schnittstellenstandards welche den eCH-0008
    importieren, den countryType oder den countryShortType verwenden."
    """

    country_name_short: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Short country name (language-specific, max 50 chars per eCH-0008 XSD, required)"
    )

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

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0008/3',
               element_name: str = 'country') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element (usually 'country')

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Country name short - required (only field)
        name_elem = ET.SubElement(elem, f'{{{namespace}}}countryNameShort')
        name_elem.text = self.country_name_short

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0008/3') -> 'ECH0008CountryShort':
        """Import from XML element.

        Args:
            elem: XML element (country container)
            namespace: XML namespace URI

        Returns:
            Parsed country short object

        Raises:
            ValueError: If required field missing or invalid
        """
        ns = {'eCH-0008': namespace}

        # Extract required field (countryNameShort) - only field for countryShortType
        country_name_elem = elem.find('eCH-0008:countryNameShort', ns)
        if country_name_elem is None or not country_name_elem.text:
            raise ValueError("Missing required field: countryNameShort")

        return cls(country_name_short=country_name_elem.text.strip())
