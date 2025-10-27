"""eCH-0007 Swiss Municipality and Country Data.

Standard: eCH-0007 v5.0 (Swiss municipalities)
Version stability: Used identically in eCH-0020 v3.0 and v5.0

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/municipality_mapper.py
"""

import xml.etree.ElementTree as ET
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CantonAbbreviation(str, Enum):
    """Swiss canton abbreviations."""
    ZH = "ZH"  # Zürich
    BE = "BE"  # Bern
    LU = "LU"  # Luzern
    UR = "UR"  # Uri
    SZ = "SZ"  # Schwyz
    OW = "OW"  # Obwalden
    NW = "NW"  # Nidwalden
    GL = "GL"  # Glarus
    ZG = "ZG"  # Zug
    FR = "FR"  # Fribourg
    SO = "SO"  # Solothurn
    BS = "BS"  # Basel-Stadt
    BL = "BL"  # Basel-Landschaft
    SH = "SH"  # Schaffhausen
    AR = "AR"  # Appenzell Ausserrhoden
    AI = "AI"  # Appenzell Innerrhoden
    SG = "SG"  # St. Gallen
    GR = "GR"  # Graubünden
    AG = "AG"  # Aargau
    TG = "TG"  # Thurgau
    TI = "TI"  # Ticino
    VD = "VD"  # Vaud
    VS = "VS"  # Valais
    NE = "NE"  # Neuchâtel
    GE = "GE"  # Genève
    JU = "JU"  # Jura


class CantonFLAbbreviation(str, Enum):
    """Swiss canton + Liechtenstein abbreviations (eCH-0007 cantonFlAbbreviationType).

    Contains all 26 Swiss cantons plus FL (Fürstentum Liechtenstein).

    Background (from eCH-0007 v5 PDF page 3-4):
    Certain administrative tasks in Liechtenstein are handled by Swiss federal authorities.
    For this reason, the official municipality registry includes a value range for
    Liechtenstein municipalities. Two separate types are maintained in the schema to
    better distinguish use cases - population control/statistics.

    XSD Source: eCH-0007-5-0.xsd lines 21-51 (27 enumeration values)
    """
    ZH = "ZH"  # Zürich
    BE = "BE"  # Bern
    LU = "LU"  # Luzern
    UR = "UR"  # Uri
    SZ = "SZ"  # Schwyz
    OW = "OW"  # Obwalden
    NW = "NW"  # Nidwalden
    GL = "GL"  # Glarus
    ZG = "ZG"  # Zug
    FR = "FR"  # Fribourg
    SO = "SO"  # Solothurn
    BS = "BS"  # Basel-Stadt
    BL = "BL"  # Basel-Landschaft
    SH = "SH"  # Schaffhausen
    AR = "AR"  # Appenzell Ausserrhoden
    AI = "AI"  # Appenzell Innerrhoden
    SG = "SG"  # St. Gallen
    GR = "GR"  # Graubünden
    AG = "AG"  # Aargau
    TG = "TG"  # Thurgau
    TI = "TI"  # Ticino
    VD = "VD"  # Vaud
    VS = "VS"  # Valais
    NE = "NE"  # Neuchâtel
    GE = "GE"  # Genève
    JU = "JU"  # Jura
    FL = "FL"  # Fürstentum Liechtenstein (Principality of Liechtenstein)


class ECH0007SwissMunicipality(BaseModel):
    """eCH-0007 Swiss Municipality.

    Represents a Swiss municipality with BFS number and canton.

    XML Schema: eCH-0007 swissMunicipalityType
    """
    municipality_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=4,
        description="BFS municipality number (1-4 digits, optional per XSD)"
    )
    municipality_name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Official municipality name (required)"
    )
    canton_abbreviation: Optional[CantonAbbreviation] = Field(
        None,
        description="Two-letter canton code (optional per XSD)"
    )
    history_municipality_id: Optional[str] = Field(
        None,
        max_length=12,
        description="Historical BFS number for merged municipalities"
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate BFS municipality number format."""
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"Municipality ID must be numeric, got: {v}")
        if not (1 <= len(v) <= 4):
            raise ValueError(f"Municipality ID must be 1-4 digits, got: {v}")
        return v

    @field_validator('history_municipality_id')
    @classmethod
    def validate_history_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate history municipality ID format."""
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        if len(v) > 12:
            raise ValueError(f"History municipality ID max 12 digits, got: {v}")
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}swissMunicipality')
        else:
            elem = ET.Element(f'{{{namespace}}}swissMunicipality')

        # Municipality ID (optional)
        if self.municipality_id:
            mun_id = ET.SubElement(elem, f'{{{namespace}}}municipalityId')
            mun_id.text = self.municipality_id

        # Municipality name (required)
        mun_name = ET.SubElement(elem, f'{{{namespace}}}municipalityName')
        mun_name.text = self.municipality_name

        # Canton abbreviation (optional)
        if self.canton_abbreviation:
            canton = ET.SubElement(elem, f'{{{namespace}}}cantonAbbreviation')
            canton.text = self.canton_abbreviation.value

        # History municipality ID (optional)
        if self.history_municipality_id:
            hist_id = ET.SubElement(elem, f'{{{namespace}}}historyMunicipalityId')
            hist_id.text = self.history_municipality_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5') -> 'ECH0007SwissMunicipality':
        """Import from XML element.

        Args:
            elem: XML element (swissMunicipality)
            namespace: XML namespace URI

        Returns:
            Parsed municipality object

        Raises:
            ValueError: If required fields missing or invalid
        """
        ns = {'eCH-0007': namespace}

        # Extract municipality name (required)
        mun_name_elem = elem.find('eCH-0007:municipalityName', ns)
        if mun_name_elem is None or not mun_name_elem.text:
            raise ValueError("Missing required field: municipalityName")

        # Extract optional fields
        mun_id_elem = elem.find('eCH-0007:municipalityId', ns)
        mun_id = mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None

        canton_elem = elem.find('eCH-0007:cantonAbbreviation', ns)
        canton = CantonAbbreviation(canton_elem.text.strip()) if canton_elem is not None and canton_elem.text else None

        hist_elem = elem.find('eCH-0007:historyMunicipalityId', ns)
        hist_id = hist_elem.text.strip() if hist_elem is not None and hist_elem.text else None

        return cls(
            municipality_id=mun_id,
            municipality_name=mun_name_elem.text.strip(),
            canton_abbreviation=canton,
            history_municipality_id=hist_id
        )


class ECH0007SwissAndFLMunicipality(BaseModel):
    """eCH-0007 Swiss + FL Municipality (swissAndFlMunicipalityType).

    Represents a Swiss or Liechtenstein municipality with REQUIRED fields.

    Difference from ECH0007SwissMunicipality:
    - All fields REQUIRED (except historyMunicipalityId)
    - Uses CantonFLAbbreviation (27 values including FL)
    - Used for contexts requiring Liechtenstein support

    Background (eCH-0007 v5 PDF page 3-4):
    Swiss federal authorities handle certain administrative tasks for Liechtenstein.
    This type is used for population control/statistics contexts that include FL.

    XML Schema: eCH-0007 swissAndFlMunicipalityType (XSD lines 95-102)
    """
    municipality_id: str = Field(
        ...,
        min_length=1,
        max_length=4,
        description="BFS municipality number (1-4 digits, REQUIRED)"
    )
    municipality_name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Official municipality name (REQUIRED)"
    )
    canton_fl_abbreviation: CantonFLAbbreviation = Field(
        ...,
        description="Two-letter canton code including FL (REQUIRED)"
    )
    history_municipality_id: Optional[str] = Field(
        None,
        max_length=12,
        description="Historical BFS number for merged municipalities (optional)"
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: str) -> str:
        """Validate BFS municipality number format."""
        if not v.isdigit():
            raise ValueError(f"Municipality ID must be numeric, got: {v}")
        if not (1 <= len(v) <= 4):
            raise ValueError(f"Municipality ID must be 1-4 digits, got: {v}")
        return v

    @field_validator('history_municipality_id')
    @classmethod
    def validate_history_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate history municipality ID format."""
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        if len(v) > 12:
            raise ValueError(f"History municipality ID max 12 digits, got: {v}")
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}swissAndFlMunicipality')
        else:
            elem = ET.Element(f'{{{namespace}}}swissAndFlMunicipality')

        # Municipality ID (REQUIRED)
        mun_id = ET.SubElement(elem, f'{{{namespace}}}municipalityId')
        mun_id.text = self.municipality_id

        # Municipality name (REQUIRED)
        mun_name = ET.SubElement(elem, f'{{{namespace}}}municipalityName')
        mun_name.text = self.municipality_name

        # Canton FL abbreviation (REQUIRED)
        canton = ET.SubElement(elem, f'{{{namespace}}}cantonFlAbbreviation')
        canton.text = self.canton_fl_abbreviation.value

        # History municipality ID (optional)
        if self.history_municipality_id:
            hist_id = ET.SubElement(elem, f'{{{namespace}}}historyMunicipalityId')
            hist_id.text = self.history_municipality_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5') -> 'ECH0007SwissAndFLMunicipality':
        """Import from XML element.

        Args:
            elem: XML element (swissAndFlMunicipality)
            namespace: XML namespace URI

        Returns:
            Parsed municipality object

        Raises:
            ValueError: If required fields missing or invalid
        """
        ns = {'eCH-0007': namespace}

        # Extract municipality ID (REQUIRED)
        mun_id_elem = elem.find('eCH-0007:municipalityId', ns)
        if mun_id_elem is None or not mun_id_elem.text:
            raise ValueError("Missing required field: municipalityId")

        # Extract municipality name (REQUIRED)
        mun_name_elem = elem.find('eCH-0007:municipalityName', ns)
        if mun_name_elem is None or not mun_name_elem.text:
            raise ValueError("Missing required field: municipalityName")

        # Extract canton FL abbreviation (REQUIRED)
        canton_elem = elem.find('eCH-0007:cantonFlAbbreviation', ns)
        if canton_elem is None or not canton_elem.text:
            raise ValueError("Missing required field: cantonFlAbbreviation")

        # Extract optional history ID
        hist_elem = elem.find('eCH-0007:historyMunicipalityId', ns)
        hist_id = hist_elem.text.strip() if hist_elem is not None and hist_elem.text else None

        return cls(
            municipality_id=mun_id_elem.text.strip(),
            municipality_name=mun_name_elem.text.strip(),
            canton_fl_abbreviation=CantonFLAbbreviation(canton_elem.text.strip()),
            history_municipality_id=hist_id
        )


class ECH0007Municipality(BaseModel):
    """eCH-0007 Municipality (Swiss).

    Wrapper for Swiss municipality data with BFS number and canton.

    Note: eCH-0007 v5 specification defines ONLY Swiss municipalities.
    Foreign municipalities are NOT part of the eCH-0007 standard.

    Note: history_municipality_id is part of ECH0007SwissMunicipality
    per XSD specification.
    """
    swiss_municipality: ECH0007SwissMunicipality

    @property
    def name(self) -> str:
        """Get municipality name."""
        return self.swiss_municipality.municipality_name

    @property
    def history_municipality_id(self) -> Optional[str]:
        """Get history municipality ID."""
        return self.swiss_municipality.history_municipality_id

    @classmethod
    def from_swiss(cls, municipality_id: Optional[str], municipality_name: str,
                   canton: Optional[CantonAbbreviation],
                   history_id: Optional[str] = None) -> 'ECH0007Municipality':
        """Create Swiss municipality.

        Args:
            municipality_id: BFS municipality number (optional per XSD)
            municipality_name: Official municipality name (required)
            canton: Canton abbreviation (optional per XSD)
            history_id: Optional historical BFS number

        Returns:
            Municipality instance
        """
        return cls(
            swiss_municipality=ECH0007SwissMunicipality(
                municipality_id=municipality_id,
                municipality_name=municipality_name,
                canton_abbreviation=canton,
                history_municipality_id=history_id
            )
        )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5',
               element_name: str = 'placeOfOrigin') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI
            element_name: Name of container element (varies by context)

        Returns:
            XML Element
        """
        if parent is not None:
            container = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            container = ET.Element(f'{{{namespace}}}{element_name}')

        # Export Swiss municipality
        self.swiss_municipality.to_xml(container, namespace)

        return container

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0007/5') -> 'ECH0007Municipality':
        """Import from XML element.

        Args:
            elem: XML container element (e.g., placeOfOrigin, placeOfBirth)
            namespace: XML namespace URI

        Returns:
            Parsed municipality object

        Note: history_municipality_id is parsed inside ECH0007SwissMunicipality
        per XSD specification.
        """
        ns = {'eCH-0007': namespace}

        # Check for Swiss municipality
        swiss_elem = elem.find('eCH-0007:swissMunicipality', ns)
        if swiss_elem is None:
            raise ValueError("Missing required element: swissMunicipality")

        swiss_mun = ECH0007SwissMunicipality.from_xml(swiss_elem, namespace)

        return cls(swiss_municipality=swiss_mun)
