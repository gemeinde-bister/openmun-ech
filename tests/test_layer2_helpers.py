"""Tests for Layer 2 extraction helpers."""

from datetime import date

import pytest

from openmun_ech.ech0044 import (
    ECH0044DatePartiallyKnown,
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044NamedPersonId,
    Sex,
)
from openmun_ech.ech0020.models import (
    _extract_date_of_birth,
    _extract_person_identification,
    PersonIdentification,
)


# ============================================================================
# _extract_date_of_birth
# ============================================================================


class TestExtractDateOfBirth:
    """Test _extract_date_of_birth helper."""

    def test_none_returns_none(self):
        assert _extract_date_of_birth(None) is None

    def test_full_date(self):
        dob = ECH0044DatePartiallyKnown(year_month_day=date(1990, 5, 15))
        assert _extract_date_of_birth(dob) == date(1990, 5, 15)

    def test_year_month(self):
        dob = ECH0044DatePartiallyKnown(year_month="1990-05")
        result = _extract_date_of_birth(dob)
        assert result == date(1990, 5, 1)

    def test_year_only(self):
        dob = ECH0044DatePartiallyKnown(year="1990")
        result = _extract_date_of_birth(dob)
        assert result == date(1990, 1, 1)

    def test_year_month_january(self):
        dob = ECH0044DatePartiallyKnown(year_month="2000-01")
        assert _extract_date_of_birth(dob) == date(2000, 1, 1)

    def test_year_month_december(self):
        dob = ECH0044DatePartiallyKnown(year_month="1985-12")
        assert _extract_date_of_birth(dob) == date(1985, 12, 1)


# ============================================================================
# _extract_person_identification — Full (ECH0044PersonIdentification)
# ============================================================================


class TestExtractPersonIdentificationFull:
    """Test _extract_person_identification with Full variant."""

    def _make_full(self, **overrides):
        defaults = dict(
            vn="7561234567890",
            local_person_id=ECH0044NamedPersonId(
                person_id="12345", person_id_category="veka.id"
            ),
            official_name="Müller",
            first_name="Hans",
            sex=Sex.MALE,
            date_of_birth=ECH0044DatePartiallyKnown(year_month_day=date(1990, 5, 15)),
        )
        defaults.update(overrides)
        return ECH0044PersonIdentification(**defaults)

    def test_full_extraction(self):
        pid = self._make_full()
        result = _extract_person_identification(pid)
        assert isinstance(result, PersonIdentification)
        assert result.vn == "7561234567890"
        assert result.local_person_id == "12345"
        assert result.local_person_id_category == "veka.id"
        assert result.official_name == "Müller"
        assert result.first_name == "Hans"
        assert result.sex == Sex.MALE
        assert result.date_of_birth == date(1990, 5, 15)

    def test_full_without_vn(self):
        pid = self._make_full(vn=None)
        result = _extract_person_identification(pid)
        assert result.vn is None

    def test_full_with_original_name(self):
        pid = self._make_full(original_name="Schmidt")
        result = _extract_person_identification(pid)
        assert result.original_name == "Schmidt"

    def test_full_with_partial_date(self):
        pid = self._make_full(
            date_of_birth=ECH0044DatePartiallyKnown(year_month="1990-05")
        )
        result = _extract_person_identification(pid)
        assert result.date_of_birth == date(1990, 5, 1)


# ============================================================================
# _extract_person_identification — Light (ECH0044PersonIdentificationLight)
# ============================================================================


class TestExtractPersonIdentificationLight:
    """Test _extract_person_identification with Light variant."""

    def _make_light(self, **overrides):
        defaults = dict(
            official_name="Meier",
            first_name="Anna",
        )
        defaults.update(overrides)
        return ECH0044PersonIdentificationLight(**defaults)

    def test_minimal_light(self):
        pid = self._make_light()
        result = _extract_person_identification(pid)
        assert result.official_name == "Meier"
        assert result.first_name == "Anna"
        assert result.vn is None
        assert result.local_person_id is None
        assert result.sex is None
        assert result.date_of_birth is None

    def test_light_with_all_fields(self):
        pid = self._make_light(
            vn="7569876543210",
            local_person_id=ECH0044NamedPersonId(
                person_id="999", person_id_category="ext.id"
            ),
            sex=Sex.FEMALE,
            date_of_birth=ECH0044DatePartiallyKnown(year_month_day=date(1985, 3, 20)),
        )
        result = _extract_person_identification(pid)
        assert result.vn == "7569876543210"
        assert result.local_person_id == "999"
        assert result.local_person_id_category == "ext.id"
        assert result.sex == Sex.FEMALE
        assert result.date_of_birth == date(1985, 3, 20)

    def test_light_sex_none(self):
        """Light variant allows sex=None (optional)."""
        pid = self._make_light(sex=None)
        result = _extract_person_identification(pid)
        assert result.sex is None
