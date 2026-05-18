"""eCH-0020 Layer 2: Layer 1 to Layer 2 extraction helpers."""

from datetime import date
from typing import Optional, Tuple, Union

from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044DatePartiallyKnown,
    Sex,
)

from .types import DatePrecision, PersonIdentification


# ============================================================================
# LAYER 1 → LAYER 2 EXTRACTION HELPERS
# ============================================================================


def extract_date_of_birth(
    dob: Optional[ECH0044DatePartiallyKnown],
) -> Optional[date]:
    """Extract a date from an eCH-0044 DatePartiallyKnown CHOICE type.

    Handles all three XSD choice branches:
    - yearMonthDay → date as-is
    - yearMonth (string "YYYY-MM") → first day of month
    - year (string "YYYY") → January 1st

    Note: This loses precision information. Use extract_date_of_birth_with_precision()
    for lossless roundtrips.

    Returns None if dob is None or no branch is set.
    """
    result, _ = extract_date_of_birth_with_precision(dob)
    return result


def extract_date_of_birth_with_precision(
    dob: Optional[ECH0044DatePartiallyKnown],
) -> Tuple[Optional[date], DatePrecision]:
    """Extract date and precision from an eCH-0044 DatePartiallyKnown CHOICE type.

    Returns a tuple of (date, precision) preserving the original XSD branch:
    - yearMonthDay → (date, FULL)
    - yearMonth "YYYY-MM" → (date(year, month, 1), YEAR_MONTH)
    - year "YYYY" → (date(year, 1, 1), YEAR_ONLY)
    - None → (None, FULL)
    """
    if dob is None:
        return None, DatePrecision.FULL
    if dob.year_month_day:
        return dob.year_month_day, DatePrecision.FULL
    if dob.year_month:
        parts = dob.year_month.split('-')
        return date(int(parts[0]), int(parts[1]), 1), DatePrecision.YEAR_MONTH
    if dob.year:
        return date(int(dob.year), 1, 1), DatePrecision.YEAR_ONLY
    return None, DatePrecision.FULL


def date_to_partially_known(
    d: date,
    precision: DatePrecision,
) -> ECH0044DatePartiallyKnown:
    """Construct ECH0044DatePartiallyKnown from a date and precision.

    Uses the ECH0044DatePartiallyKnown factory methods to create the
    correct XSD CHOICE branch based on precision.
    """
    if precision == DatePrecision.YEAR_MONTH:
        return ECH0044DatePartiallyKnown.from_year_month(d.year, d.month)
    elif precision == DatePrecision.YEAR_ONLY:
        return ECH0044DatePartiallyKnown.from_year(d.year)
    else:
        return ECH0044DatePartiallyKnown.from_date(d)


def extract_person_identification(
    person_id: Union[ECH0044PersonIdentification, ECH0044PersonIdentificationLight],
) -> PersonIdentification:
    """Extract a Layer 2 PersonIdentification from a Layer 1 eCH-0044 object.

    Handles both Full and Light variants. Both share the same field names;
    Light has Optional where Full has required fields.

    Preserves date_of_birth precision for lossless roundtrips.
    """
    # local_person_id — required on Full, Optional on Light
    local_person_id = None
    local_person_id_category = None
    if person_id.local_person_id:
        local_person_id = person_id.local_person_id.person_id
        local_person_id_category = person_id.local_person_id.person_id_category

    # sex — required Sex enum on Full, Optional on Light
    sex = person_id.sex.value if person_id.sex else None

    dob, dob_precision = extract_date_of_birth_with_precision(person_id.date_of_birth)

    return PersonIdentification(
        vn=person_id.vn,
        local_person_id=local_person_id,
        local_person_id_category=local_person_id_category,
        official_name=person_id.official_name,
        first_name=person_id.first_name,
        original_name=person_id.original_name,
        sex=sex,
        date_of_birth=dob,
        date_of_birth_precision=dob_precision if dob_precision != DatePrecision.FULL else None,
    )


# Deprecated aliases — use the unprefixed versions
_extract_date_of_birth = extract_date_of_birth
_extract_person_identification = extract_person_identification
