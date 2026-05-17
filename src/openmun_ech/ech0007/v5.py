"""eCH-0007 Swiss Municipality and Country Data.

Standard: eCH-0007 v5.0 (Swiss municipalities)
Version stability: Used identically in eCH-0020 v3.0 and v5.0

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/municipality_mapper.py
"""

from enum import Enum
from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field


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


class ECH0007SwissMunicipality(ECHModel):
    """eCH-0007 Swiss Municipality.

    Represents a Swiss municipality with BFS number and canton.

    XML Schema: eCH-0007 swissMunicipalityType
    """

    __xml_ns__ = NS.ECH0007_V5
    __xml_element__ = 'swissMunicipality'

    municipality_id: Optional[str] = xml_field(
        'municipalityId', default=None, min_length=1, max_length=4,
        description="BFS municipality number (1-4 digits, optional per XSD)"
    )
    municipality_name: str = xml_field(
        'municipalityName', min_length=1, max_length=40,
        description="Official municipality name (required)"
    )
    canton_abbreviation: Optional[CantonAbbreviation] = xml_field(
        'cantonAbbreviation', default=None,
        description="Two-letter canton code (optional per XSD)"
    )
    history_municipality_id: Optional[str] = xml_field(
        'historyMunicipalityId', default=None,
        description="Historical BFS number for merged municipalities"
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate BFS municipality number format.

        XSD: xs:int, minInclusive=1, maxInclusive=9999, totalDigits=4 (eCH-0007 §4.1).
        """
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"Municipality ID must be numeric, got: {v}")
        int_val = int(v)
        if int_val < 1 or int_val > 9999:
            raise ValueError(
                f"Municipality ID must be 1-9999 (eCH-0007 §4.1), got: {v}"
            )
        return v

    @field_validator('history_municipality_id')
    @classmethod
    def validate_history_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate history municipality ID format.

        XSD v5: xs:int (unbounded). XSD v6: pattern added for min/max (RfC 2012-53).
        We accept any positive integer as string.
        """
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        if int(v) < 1:
            raise ValueError(f"History municipality ID must be >= 1, got: {v}")
        return v


class ECH0007SwissAndFLMunicipality(ECHModel):
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

    __xml_ns__ = NS.ECH0007_V5
    __xml_element__ = 'swissAndFlMunicipality'

    municipality_id: str = xml_field(
        'municipalityId', min_length=1, max_length=4,
        description="BFS municipality number (1-4 digits, REQUIRED)"
    )
    municipality_name: str = xml_field(
        'municipalityName', min_length=1, max_length=40,
        description="Official municipality name (REQUIRED)"
    )
    canton_fl_abbreviation: CantonFLAbbreviation = xml_field(
        'cantonFlAbbreviation',
        description="Two-letter canton code including FL (REQUIRED)"
    )
    history_municipality_id: Optional[str] = xml_field(
        'historyMunicipalityId', default=None,
        description="Historical BFS number for merged municipalities (optional)"
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: str) -> str:
        """Validate BFS municipality number format.

        XSD: xs:int, minInclusive=1, maxInclusive=9999, totalDigits=4 (eCH-0007 §4.1).
        Required in swissAndFlMunicipalityType.
        """
        if not v.isdigit():
            raise ValueError(f"Municipality ID must be numeric, got: {v}")
        int_val = int(v)
        if int_val < 1 or int_val > 9999:
            raise ValueError(
                f"Municipality ID must be 1-9999 (eCH-0007 §4.1), got: {v}"
            )
        return v

    @field_validator('history_municipality_id')
    @classmethod
    def validate_history_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate history municipality ID format.

        XSD v5: xs:int (unbounded). XSD v6: pattern added for min/max (RfC 2012-53).
        """
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        if int(v) < 1:
            raise ValueError(f"History municipality ID must be >= 1, got: {v}")
        return v


class ECH0007Municipality(ECHModel):
    """eCH-0007 Municipality (Swiss).

    Wrapper for Swiss municipality data with BFS number and canton.

    Note: eCH-0007 v5 specification defines ONLY Swiss municipalities.
    Foreign municipalities are NOT part of the eCH-0007 standard.

    Note: history_municipality_id is part of ECH0007SwissMunicipality
    per XSD specification.
    """

    __xml_ns__ = NS.ECH0007_V5
    __xml_element__ = 'placeOfOrigin'

    swiss_municipality: ECH0007SwissMunicipality = xml_field('swissMunicipality')

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
