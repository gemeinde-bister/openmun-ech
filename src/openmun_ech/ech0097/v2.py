"""eCH-0097 Enterprise Identification Data.

Standard: eCH-0097 v2.0 (Datenstandard Unternehmensidentifikation)
Version stability: Used in eCH-0129 v6.0

Defines identifying characteristics for enterprises and the exchange format
for electronic transmission of enterprise information between Swiss
government authorities. Complements eCH-0098 (enterprise data).

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO external data lookups
"""

import re
from enum import Enum
from typing import Optional

from pydantic import field_validator

from openmun_ech.core import ECHModel, NS, xml_field


# --- Module 11 checksum (PDF §3.4.2, page 8) ---

_UID_MULTIPLIERS = (5, 4, 3, 2, 7, 6, 5, 4)


def validate_uid_checksum(uid_number: int) -> bool:
    """Validate UID number using Module 11 checksum algorithm.

    The 9th digit is the check digit. Multipliers per position: 5,4,3,2,7,6,5,4.
    Sum of products mod 11 → check digit = 11 - remainder.
    If check digit = 10, the number is invalid (never assigned).
    If remainder = 0, check digit = 0.

    PDF: Section 3.4.2, page 8. Example: 10932255[1] → valid.
    """
    if uid_number < 1 or uid_number > 999999999:
        return False

    digits = str(uid_number).zfill(9)

    payload = [int(d) for d in digits[:8]]
    check_digit = int(digits[8])

    product_sum = sum(d * m for d, m in zip(payload, _UID_MULTIPLIERS))
    remainder = product_sum % 11

    if remainder == 0:
        expected = 0
    else:
        expected = 11 - remainder

    # Check digit 10 means the number is never assigned
    if expected == 10:
        return False

    return check_digit == expected


# --- Enum ---


class UidOrganisationIdCategory(str, Enum):
    """UID category prefix per eCH-0097 v2.0 §3.4.1.

    XSD: uidOrganisationIdCategorieType (lines 50-57)
    PDF: Section 3.4.1, page 7
    """

    CHE = "CHE"  # Unternehmen (Company per UID-Gesetz)
    ADM = "ADM"  # Administrativeinheit (Administrative unit per UID-Gesetz)


# --- Complex Types ---

_LEGAL_FORM_PATTERN = re.compile(r'^\d{2,4}$')


class ECH0097UidStructure(ECHModel):
    """UID structure: category prefix + 9-digit number.

    XSD: uidStructureType (lines 44-49)
    PDF: Section 3.4, page 7

    The UID (Unternehmens-Identifikationsnummer) uniquely identifies
    enterprises across Switzerland. Format: CHE/ADM + 9-digit number
    with Module 11 check digit.
    """

    __xml_ns__ = NS.ECH0097_V2
    __xml_element__ = 'uid'

    # NOTE: XSD uses German spelling "Categorie" (not "Category")
    uid_organisation_id_categorie: UidOrganisationIdCategory = xml_field(
        'uidOrganisationIdCategorie'
    )
    uid_organisation_id: int = xml_field('uidOrganisationId')

    @field_validator('uid_organisation_id')
    @classmethod
    def validate_uid_organisation_id(cls, v: int) -> int:
        """Validate UID number range and checksum.

        XSD: nonNegativeInteger, totalDigits=9, minInclusive=1, maxInclusive=999999999.
        PDF §3.4.2: Module 11 checksum on 9th digit.
        """
        if v < 1 or v > 999999999:
            raise ValueError(
                f"UID organisation ID must be 1-999999999 "
                f"(XSD totalDigits=9, minInclusive=1), got: {v}"
            )
        if not validate_uid_checksum(v):
            raise ValueError(
                f"UID organisation ID {v} has invalid Module 11 checksum "
                f"(eCH-0097 §3.4.2)"
            )
        return v


class ECH0097NamedOrganisationId(ECHModel):
    """Named organisation identifier: category + value.

    XSD: namedOrganisationIdType (lines 25-43)
    PDF: Section 3.5, pages 8-11

    Category naming conventions (PDF §3.5):
    - WW.xxx: Worldwide (GLN, D-U-N-S, TIN)
    - EU.xxx: EU-wide (EORI)
    - CH.xxx: Federal (BUR, HR, MWST, AGIS)
    - CT.xx[.suffix]: Cantonal
    - MU.nnnn[.suffix]: Municipal (BFS number)
    - LOC[.suffix]: Local/system-specific
    """

    __xml_ns__ = NS.ECH0097_V2
    __xml_element__ = 'namedOrganisationId'

    organisation_id_category: str = xml_field(
        'organisationIdCategory', min_length=1, max_length=20
    )
    organisation_id: str = xml_field(
        'organisationId', min_length=1, max_length=20
    )


class ECH0097OrganisationIdentification(ECHModel):
    """Organisation identification container.

    XSD: organisationIdentificationType (lines 14-24)
    PDF: Section 3.3, page 6

    Main type referenced by eCH-0129 for building authority
    and owner identification. Contains UID, local and other
    organisation IDs, names, and legal form.
    """

    __xml_ns__ = NS.ECH0097_V2
    __xml_element__ = 'organisationIdentification'

    uid: Optional[ECH0097UidStructure] = xml_field('uid', default=None)
    local_organisation_id: ECH0097NamedOrganisationId = xml_field(
        'localOrganisationId'
    )
    # NOTE: XSD has capital 'O' — OtherOrganisationId, not otherOrganisationId
    other_organisation_id: list[ECH0097NamedOrganisationId] = xml_field(
        'OtherOrganisationId', is_list=True, default_factory=list
    )
    organisation_name: str = xml_field(
        'organisationName', min_length=1, max_length=255
    )
    organisation_legal_name: Optional[str] = xml_field(
        'organisationLegalName', default=None, min_length=1, max_length=255
    )
    organisation_additional_name: Optional[str] = xml_field(
        'organisationAdditionalName', default=None, min_length=1, max_length=255
    )
    legal_form: Optional[str] = xml_field(
        'legalForm', default=None, min_length=2, max_length=4
    )

    @field_validator('legal_form')
    @classmethod
    def validate_legal_form(cls, v: Optional[str]) -> Optional[str]:
        """Validate legal form code format.

        XSD: pattern \\d{2,4} (2-4 digit BUR nomenclature code).
        PDF: Section 3.7, page 12 — codes are informational, not enumerated in XSD.
        """
        if v is None:
            return None
        if not _LEGAL_FORM_PATTERN.match(v):
            raise ValueError(
                f"Legal form must be 2-4 digits (XSD pattern \\d{{2,4}}), got: '{v}'"
            )
        return v


class ECH0097OrganisationIdentificationRoot(ECHModel):
    """Root element wrapper for standalone XML documents.

    XSD: organisationIdentificationRoot element (lines 79-85)
    """

    __xml_ns__ = NS.ECH0097_V2
    __xml_element__ = 'organisationIdentificationRoot'

    organisation_identification: ECH0097OrganisationIdentification = xml_field(
        'organisationIdentification'
    )
