"""eCH-0020 Layer 2: Layer 1 to Layer 2 extraction helpers."""

from datetime import date
from typing import Optional, Union

from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044DatePartiallyKnown,
    Sex,
)

from .types import PersonIdentification


# ============================================================================
# LAYER 1 → LAYER 2 EXTRACTION HELPERS
# ============================================================================


def _extract_date_of_birth(
    dob: Optional[ECH0044DatePartiallyKnown],
) -> Optional[date]:
    """Extract a date from an eCH-0044 DatePartiallyKnown CHOICE type.

    Handles all three XSD choice branches:
    - yearMonthDay → date as-is
    - yearMonth (string "YYYY-MM") → first day of month
    - year (string "YYYY") → January 1st

    Returns None if dob is None or no branch is set.
    """
    if dob is None:
        return None
    if dob.year_month_day:
        return dob.year_month_day
    if dob.year_month:
        # year_month is a string like "1990-05"
        parts = dob.year_month.split('-')
        return date(int(parts[0]), int(parts[1]), 1)
    if dob.year:
        # year is a string like "1990"
        return date(int(dob.year), 1, 1)
    return None


def _extract_person_identification(
    person_id: Union[ECH0044PersonIdentification, ECH0044PersonIdentificationLight],
) -> PersonIdentification:
    """Extract a Layer 2 PersonIdentification from a Layer 1 eCH-0044 object.

    Handles both Full and Light variants. Both share the same field names;
    Light has Optional where Full has required fields.
    """
    # local_person_id — required on Full, Optional on Light
    local_person_id = None
    local_person_id_category = None
    if person_id.local_person_id:
        local_person_id = person_id.local_person_id.person_id
        local_person_id_category = person_id.local_person_id.person_id_category

    # sex — required Sex enum on Full, Optional on Light
    sex = person_id.sex.value if person_id.sex else None

    return PersonIdentification(
        vn=person_id.vn,
        local_person_id=local_person_id,
        local_person_id_category=local_person_id_category,
        official_name=person_id.official_name,
        first_name=person_id.first_name,
        original_name=person_id.original_name,
        sex=sex,
        date_of_birth=_extract_date_of_birth(person_id.date_of_birth),
    )
