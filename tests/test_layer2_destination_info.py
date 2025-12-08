"""Test Layer 2 DestinationInfo model validation.

This test validates DestinationInfo, which represents where a person
comes from or goes to during residence changes.

What This File Tests
====================
1. Mail address ZIP code CHOICE validation (swiss XOR foreign)
2. Mail address swiss zip add-on requires swiss zip
3. Valid combinations of mail address fields
4. DestinationInfo with mail address roundtrip

eCH-0010 XSD Constraint
=======================
Mail address can have either:
- swiss_zip_code sequence (swiss_zip_code + optional swiss_zip_code_add_on)
- foreign_zip_code (string, max 15 chars)

But NOT both. This is a CHOICE in the XSD.

Data Policy
===========
- Personal data: Fictive/anonymized
- BFS data: Real opendata fixtures
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from openmun_ech.ech0020.models import (
    BaseDeliveryPerson,
    BaseDeliveryEvent,
    DeliveryConfig,
    DwellingAddressInfo,
    DestinationInfo,
    PlaceType,
    ResidenceType,
)


class TestDestinationInfoMailAddressZipValidation:
    """Test mail address ZIP code CHOICE validation."""

    def test_swiss_zip_only_valid(self):
        """Test that Swiss ZIP code alone is valid."""
        dest = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH",
            mail_address_street="Bahnhofstrasse",
            mail_address_house_number="1",
            mail_address_town="Zürich",
            mail_address_swiss_zip_code=8001,
            mail_address_country="CH"
        )
        assert dest.mail_address_swiss_zip_code == 8001
        assert dest.mail_address_foreign_zip_code is None

    def test_swiss_zip_with_addon_valid(self):
        """Test that Swiss ZIP code with add-on is valid."""
        dest = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH",
            mail_address_street="Bahnhofstrasse",
            mail_address_house_number="1",
            mail_address_town="Zürich",
            mail_address_swiss_zip_code=8001,
            mail_address_swiss_zip_code_addon="02",
            mail_address_country="CH"
        )
        assert dest.mail_address_swiss_zip_code == 8001
        assert dest.mail_address_swiss_zip_code_addon == "02"

    def test_foreign_zip_only_valid(self):
        """Test that foreign ZIP code alone is valid."""
        dest = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="DE",
            country_name_short="Deutschland",
            town="Berlin",
            mail_address_street="Beispielstrasse",
            mail_address_house_number="1",
            mail_address_town="Berlin",
            mail_address_foreign_zip_code="10115",
            mail_address_country="DE"
        )
        assert dest.mail_address_foreign_zip_code == "10115"
        assert dest.mail_address_swiss_zip_code is None

    def test_no_zip_valid(self):
        """Test that no ZIP code is valid (mail address without ZIP)."""
        dest = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH",
            mail_address_street="Bahnhofstrasse",
            mail_address_town="Zürich",
            mail_address_country="CH"
        )
        assert dest.mail_address_swiss_zip_code is None
        assert dest.mail_address_foreign_zip_code is None

    def test_both_swiss_and_foreign_zip_fails(self):
        """Test that both Swiss and foreign ZIP codes fails validation.

        Per eCH-0010 XSD: CHOICE means one or the other, not both.
        """
        with pytest.raises(ValueError) as exc_info:
            DestinationInfo(
                place_type=PlaceType.SWISS,
                municipality_bfs="261",
                municipality_name="Zürich",
                canton_abbreviation="ZH",
                mail_address_street="Test",
                mail_address_town="Test",
                mail_address_swiss_zip_code=8001,
                mail_address_foreign_zip_code="10115",  # INVALID: both set
                mail_address_country="CH"
            )
        assert "both" in str(exc_info.value).lower()
        assert "swiss" in str(exc_info.value).lower() or "foreign" in str(exc_info.value).lower()

    def test_swiss_zip_addon_without_swiss_zip_fails(self):
        """Test that Swiss ZIP add-on without Swiss ZIP fails.

        The add-on is only meaningful with a Swiss ZIP code.
        """
        with pytest.raises(ValueError) as exc_info:
            DestinationInfo(
                place_type=PlaceType.FOREIGN,
                country_iso="DE",
                country_name_short="Deutschland",
                town="Berlin",
                mail_address_street="Test",
                mail_address_town="Berlin",
                mail_address_swiss_zip_code_addon="02",  # INVALID: add-on without ZIP
                mail_address_country="DE"
            )
        assert "addon" in str(exc_info.value).lower() or "add_on" in str(exc_info.value).lower()

    def test_swiss_zip_max_value(self):
        """Test that Swiss ZIP code respects max value (9999)."""
        dest = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="261",
            municipality_name="Zürich",
            canton_abbreviation="ZH",
            mail_address_swiss_zip_code=9999
        )
        assert dest.mail_address_swiss_zip_code == 9999

    def test_foreign_zip_max_length(self):
        """Test that foreign ZIP code can be up to 15 chars."""
        dest = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="US",
            country_name_short="USA",
            town="New York",
            mail_address_foreign_zip_code="12345-6789-1234"  # 15 chars with dashes
        )
        assert len(dest.mail_address_foreign_zip_code) == 15


class TestDestinationInfoMailAddressRoundtrip:
    """Test mail address roundtrip through XML."""

    def test_swiss_mail_address_roundtrip(self):
        """Test Swiss mail address roundtrip: Layer 2 → XML → Layer 2."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-MAIL-CH",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="MailTest",
            first_name="Swiss",
            sex="1",
            date_of_birth=date(1980, 5, 15),
            vn="7561234567890",
            local_person_id="MAIL-CH-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        # comes_from with Swiss mail address
        comes_from = DestinationInfo(
            place_type=PlaceType.SWISS,
            municipality_bfs="351",
            municipality_name="Bern",
            canton_abbreviation="BE",
            mail_address_street="Bundesplatz",
            mail_address_house_number="3",
            mail_address_town="Bern",
            mail_address_swiss_zip_code=3003,
            mail_address_swiss_zip_code_addon="01",
            mail_address_country="CH"
        )

        dwelling = DwellingAddressInfo(
            street="Test Street",
            house_number="1",
            town="Basel",
            swiss_zip_code=4001,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="2701",
            reporting_municipality_name="Basel",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling,
            comes_from=comes_from
        )

        delivery = original_event.finalize(config)

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "swiss_mail.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify mail address preserved
            rt_comes_from = roundtrip_event.comes_from
            assert rt_comes_from.mail_address_street == "Bundesplatz"
            assert rt_comes_from.mail_address_house_number == "3"
            assert rt_comes_from.mail_address_town == "Bern"
            assert rt_comes_from.mail_address_swiss_zip_code == 3003
            assert rt_comes_from.mail_address_swiss_zip_code_addon == "01"
            assert rt_comes_from.mail_address_country == "CH"
            assert rt_comes_from.mail_address_foreign_zip_code is None

    def test_foreign_mail_address_roundtrip(self):
        """Test foreign mail address roundtrip: Layer 2 → XML → Layer 2."""
        config = DeliveryConfig(
            sender_id="sedex://T1-TEST-MAIL-DE",
            manufacturer="Test",
            product="Test",
            product_version="1.0",
            test_delivery_flag=True
        )

        person = BaseDeliveryPerson(
            official_name="MailTest",
            first_name="Foreign",
            sex="2",
            date_of_birth=date(1985, 8, 20),
            vn="7569876543210",
            local_person_id="MAIL-DE-001",
            local_person_id_category="MU.6172",
            religion="111",
            marital_status="1",
            nationality_status="1",
            data_lock="0",
            places_of_origin=[{"bfs_code": "261", "name": "Zürich", "canton": "ZH"}],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich"
        )

        # comes_from with foreign mail address
        comes_from = DestinationInfo(
            place_type=PlaceType.FOREIGN,
            country_iso="DE",
            country_name_short="Deutschland",
            town="Berlin",
            mail_address_street="Unter den Linden",
            mail_address_house_number="77",
            mail_address_town="Berlin",
            mail_address_foreign_zip_code="10117",
            mail_address_country="DE"
        )

        dwelling = DwellingAddressInfo(
            street="Test Street",
            house_number="2",
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="1"
        )

        original_event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.OTHER,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 2, 1),
            dwelling_address=dwelling,
            comes_from=comes_from
        )

        delivery = original_event.finalize(config)

        # Roundtrip through XML
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "foreign_mail.xml"
            delivery.to_file(xml_path)

            from openmun_ech.ech0020.v3 import ECH0020Delivery
            xml_root = ET.fromstring(xml_path.read_text())
            roundtrip_delivery = ECH0020Delivery.from_xml(xml_root)
            roundtrip_event = BaseDeliveryEvent.from_ech0020_event(roundtrip_delivery.event[0])

            # Verify mail address preserved
            rt_comes_from = roundtrip_event.comes_from
            assert rt_comes_from.mail_address_street == "Unter den Linden"
            assert rt_comes_from.mail_address_house_number == "77"
            assert rt_comes_from.mail_address_town == "Berlin"
            assert rt_comes_from.mail_address_foreign_zip_code == "10117"
            assert rt_comes_from.mail_address_country == "DE"
            assert rt_comes_from.mail_address_swiss_zip_code is None
