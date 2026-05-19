"""eCH-0129 v6.0.0 — Right, cadastral map, surveyor remark, SDR/partial area types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 1500-1577)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.11, §4.17, §4.18, §4.20, §4.21)
"""

from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import RemarkType
from openmun_ech.ech0129.v6.realestate import ECH0129RealestateIdentification


# ---------------------------------------------------------------------------
# rightType (§4.11)
# XSD lines 1500-1504
# ---------------------------------------------------------------------------

class ECH0129Right(ECHModel):
    """eCH-0129 right (Recht).

    XSD: rightType — xs:sequence of 2 elements.
    PDF: §4.11 (page 69)

    Fields (in XSD order):
    - EREID: EREIDType (xs:normalizedString, no length constraints) (REQUIRED)
    - protected: protectedType (xs:boolean), minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'right'

    ereid: str = xml_field('EREID')
    protected: Optional[bool] = xml_field('protected', default=None)


# ---------------------------------------------------------------------------
# cadastralMapType (§4.17)
# XSD lines 1513-1517
# ---------------------------------------------------------------------------

class ECH0129CadastralMap(ECHModel):
    """eCH-0129 cadastral map reference.

    XSD: cadastralMapType — xs:sequence of 2 required elements.
    PDF: §4.17 (page 86)

    Fields (in XSD order, ALL required):
    - mapNumber: mapNumberType (xs:token, minLength=1, maxLength=12)
    - identDN: identDNType (xs:token, minLength=1, maxLength=12)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'cadastralMap'

    map_number: str = xml_field('mapNumber', min_length=1, max_length=12)
    ident_dn: str = xml_field('identDN', min_length=1, max_length=12)


# ---------------------------------------------------------------------------
# cadastralSurveyorRemarkType (§4.18)
# XSD lines 1539-1545
# ---------------------------------------------------------------------------

class ECH0129CadastralSurveyorRemark(ECHModel):
    """eCH-0129 cadastral surveyor remark.

    XSD: cadastralSurveyorRemarkType — xs:sequence of 4 elements.
    PDF: §4.18 (page 87)

    Fields (in XSD order):
    - remarkType: remarkTypeType enum 1-6 (REQUIRED)
    - remarkOtherType: remarkOtherTypeType (xs:token, no constraints), minOccurs="0"
    - remarkText: remarkTextType (xs:token, no constraints) (REQUIRED)
    - objectID: objectIDType (xs:token, no constraints) (REQUIRED)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'cadastralSurveyorRemark'

    remark_type: RemarkType = xml_field('remarkType')
    remark_other_type: Optional[str] = xml_field('remarkOtherType', default=None)
    remark_text: str = xml_field('remarkText')
    object_id: str = xml_field('objectID')


# ---------------------------------------------------------------------------
# coveringAreaOfSDRType (§4.20)
# XSD lines 1566-1570
# ---------------------------------------------------------------------------

class ECH0129CoveringAreaOfSDR(ECHModel):
    """eCH-0129 covering area of SDR (Selbstaendiges und Dauerndes Recht).

    XSD: coveringAreaOfSDRType — xs:sequence of 2 required elements.
    PDF: §4.20 (page 89)

    Fields (in XSD order, ALL required):
    - squareMeasure: squareMeasureType (xs:decimal, 0.0-1000000000.0)
    - realestateIdentification: realestateIdentificationType

    squareMeasure stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'coveringAreaOfSDR'

    square_measure: str = xml_field('squareMeasure')
    realestate_identification: ECH0129RealestateIdentification = xml_field(
        'realestateIdentification'
    )

    @field_validator('square_measure')
    @classmethod
    def validate_square_measure(cls, v: str) -> str:
        """XSD: squareMeasureType — xs:decimal, 0.0–1000000000.0."""
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"squareMeasure must be a valid decimal, got: '{v}'")
        if d < Decimal('0.0') or d > Decimal('1000000000.0'):
            raise ValueError(
                f"squareMeasure must be 0.0–1000000000.0, got: {v}"
            )
        return v


# ---------------------------------------------------------------------------
# partialAreaOfBuildingType (§4.21)
# XSD lines 1573-1577
# ---------------------------------------------------------------------------

class ECH0129PartialAreaOfBuilding(ECHModel):
    """eCH-0129 partial area of building.

    XSD: partialAreaOfBuildingType — xs:sequence of 1 optional element.
    PDF: §4.21 (page 89)

    Fields:
    - squareMeasure: squareMeasureType (xs:decimal, 0.0-1000000000.0), minOccurs="0"

    squareMeasure stored as str for lossless xs:decimal round-trip.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'partialAreaOfBuilding'

    square_measure: Optional[str] = xml_field('squareMeasure', default=None)

    @field_validator('square_measure')
    @classmethod
    def validate_square_measure(cls, v: Optional[str]) -> Optional[str]:
        """XSD: squareMeasureType — xs:decimal, 0.0–1000000000.0."""
        if v is None:
            return v
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"squareMeasure must be a valid decimal, got: '{v}'")
        if d < Decimal('0.0') or d > Decimal('1000000000.0'):
            raise ValueError(
                f"squareMeasure must be 0.0–1000000000.0, got: {v}"
            )
        return v
