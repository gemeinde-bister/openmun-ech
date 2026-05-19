"""eCH-0007 Swiss Municipality and Country Data v6.0.

Standard: eCH-0007 v6.0 (Swiss municipalities)
Version stability: Used by eCH-0129 v6.0 (Objektwesen)

Structural changes from v5: None — same types, same fields, same cardinality.
Only constraint tightening: historyMunicipalityId adds minInclusive=10001,
maxInclusive=99999 (RfC 2012-53). Namespace changes from /5 to /6.

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO external data lookups
"""

from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0007.v5 import (
    CantonAbbreviation,
    CantonFLAbbreviation,
)


class ECH0007v6SwissMunicipality(ECHModel):
    """eCH-0007 v6 Swiss Municipality (swissMunicipalityType).

    XSD: eCH-0007-6-0.xsd swissMunicipalityType
    Identical to v5 except namespace and historyMunicipalityId range constraint.
    """

    __xml_ns__ = NS.ECH0007_V6
    __xml_element__ = 'swissMunicipality'

    municipality_id: Optional[str] = xml_field(
        'municipalityId', default=None, min_length=1, max_length=4,
    )
    municipality_name: str = xml_field(
        'municipalityName', min_length=1, max_length=40,
    )
    canton_abbreviation: Optional[CantonAbbreviation] = xml_field(
        'cantonAbbreviation', default=None,
    )
    history_municipality_id: Optional[str] = xml_field(
        'historyMunicipalityId', default=None,
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate BFS municipality number format.

        XSD: xs:int, minInclusive=1, maxInclusive=9999, totalDigits=4.
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

        XSD v6: minInclusive=10001, maxInclusive=99999 (RfC 2012-53).
        Tighter than v5 which was unbounded.
        """
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        int_val = int(v)
        if int_val < 10001 or int_val > 99999:
            raise ValueError(
                f"History municipality ID must be 10001-99999 "
                f"(eCH-0007 v6 RfC 2012-53), got: {v}"
            )
        return v


class ECH0007v6SwissAndFLMunicipality(ECHModel):
    """eCH-0007 v6 Swiss + FL Municipality (swissAndFlMunicipalityType).

    XSD: eCH-0007-6-0.xsd swissAndFlMunicipalityType
    All fields REQUIRED (except historyMunicipalityId).
    Uses CantonFLAbbreviation (27 values including FL).
    """

    __xml_ns__ = NS.ECH0007_V6
    __xml_element__ = 'swissAndFlMunicipality'

    municipality_id: str = xml_field(
        'municipalityId', min_length=1, max_length=4,
    )
    municipality_name: str = xml_field(
        'municipalityName', min_length=1, max_length=40,
    )
    canton_fl_abbreviation: CantonFLAbbreviation = xml_field(
        'cantonFlAbbreviation',
    )
    history_municipality_id: Optional[str] = xml_field(
        'historyMunicipalityId', default=None,
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: str) -> str:
        """Validate BFS municipality number format.

        XSD: xs:int, minInclusive=1, maxInclusive=9999, totalDigits=4.
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

        XSD v6: minInclusive=10001, maxInclusive=99999 (RfC 2012-53).
        """
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"History municipality ID must be numeric, got: {v}")
        int_val = int(v)
        if int_val < 10001 or int_val > 99999:
            raise ValueError(
                f"History municipality ID must be 10001-99999 "
                f"(eCH-0007 v6 RfC 2012-53), got: {v}"
            )
        return v
