"""Tests for eCH-0099 Layer 2 export functionality.

These tests verify:
1. Layer 2 model creation and validation
2. Layer 2 → Layer 1 conversion
3. Finalization and XML export
4. XSD validation of exported XML

Zero-Tolerance Policy: All tests verify no data invention and fail-fast behavior.
"""

import pytest
from datetime import date, datetime
from pathlib import Path
import tempfile

from openmun_ech.ech0099 import (
    # Layer 2
    StatisticsPerson,
    StatisticsDeliveryEvent,
    StatisticsDeliveryConfig,
    DwellingAddressInfo,
    DestinationInfo,
    PlaceOfOriginInfo,
    ResidenceType,
    PlaceType,
    NationalityType,
    finalize_statistics_delivery,
    # Layer 1
    ECH0099Delivery,
    ECH0099DataType,
)
from openmun_ech.finalize import finalize_0099_layer2


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def swiss_person():
    """Create a valid Swiss person for testing."""
    return StatisticsPerson(
        vn="7561234567890",
        local_person_id="12345",
        local_person_id_category="MU.6172",
        official_name="Müller",
        first_name="Hans",
        sex="1",
        date_of_birth=date(1980, 5, 15),
        birth_place_type=PlaceType.SWISS,
        birth_municipality_bfs=261,
        birth_municipality_name="Zürich",
        birth_municipality_canton="ZH",
        religion="111",
        marital_status="1",
        nationality_type=NationalityType.SWISS,
        nationality_status="2",  # 2 = has known nationality
        nationality_country_name="Schweiz",
        places_of_origin=[
            PlaceOfOriginInfo(origin_name="Zürich", canton="ZH")
        ],
    )


@pytest.fixture
def foreign_person():
    """Create a valid foreign person for testing."""
    return StatisticsPerson(
        local_person_id="67890",
        local_person_id_category="MU.6172",
        official_name="Schmidt",
        first_name="Maria",
        sex="2",
        date_of_birth=date(1985, 3, 20),
        birth_place_type=PlaceType.FOREIGN,
        birth_country_id=8207,
        birth_country_iso2="DE",
        birth_country_name="Deutschland",
        religion="111",
        marital_status="2",
        nationality_type=NationalityType.FOREIGN,
        nationality_status="2",  # 2 = has known nationality
        nationality_country_id=8207,
        nationality_country_iso2="DE",
        nationality_country_name="Deutschland",
        # BFS residence permit code: 02 = B permit (Aufenthaltsbewilligung)
        residence_permit="02",
        residence_permit_valid_from=date(2020, 1, 1),
        residence_permit_valid_till=date(2025, 12, 31),
    )


@pytest.fixture
def dwelling_address():
    """Create a valid dwelling address for testing."""
    return DwellingAddressInfo(
        egid=123456789,
        ewid=1,
        street="Bahnhofstrasse",
        house_number="1",
        town="Zürich",
        swiss_zip_code=8001,
        type_of_household="1",
    )


@pytest.fixture
def config():
    """Create a valid delivery config for testing."""
    return StatisticsDeliveryConfig(
        sender_id="T1-6172-1",
        manufacturer="OpenMun Test",
        product="Test Suite",
        product_version="1.0.0",
        test_delivery_flag=True,
    )


# ============================================================================
# LAYER 2 MODEL VALIDATION TESTS
# ============================================================================

class TestStatisticsPersonValidation:
    """Test StatisticsPerson validation."""

    def test_swiss_person_requires_places_of_origin(self):
        """Swiss person without places of origin should fail."""
        with pytest.raises(ValueError, match="place of origin required"):
            StatisticsPerson(
                local_person_id="12345",
                local_person_id_category="MU.6172",
                official_name="Test",
                first_name="Person",
                sex="1",
                date_of_birth=date(1980, 1, 1),
                birth_place_type=PlaceType.UNKNOWN,
                religion="111",
                marital_status="1",
                nationality_type=NationalityType.SWISS,
                nationality_status="2",
                places_of_origin=[],  # Empty - should fail
            )

    def test_foreign_person_requires_nationality_country(self):
        """Foreign person without nationality country should fail."""
        with pytest.raises(ValueError, match="nationality_country"):
            StatisticsPerson(
                local_person_id="12345",
                local_person_id_category="MU.6172",
                official_name="Test",
                first_name="Person",
                sex="1",
                date_of_birth=date(1980, 1, 1),
                birth_place_type=PlaceType.UNKNOWN,
                religion="111",
                marital_status="1",
                nationality_type=NationalityType.FOREIGN,
                nationality_status="2",
                residence_permit="B",
                # Missing nationality_country_* - should fail
            )

    def test_foreign_person_requires_residence_permit(self, foreign_person):
        """Foreign person without residence permit should fail at conversion."""
        # Create person without residence permit
        person = StatisticsPerson(
            local_person_id="12345",
            local_person_id_category="MU.6172",
            official_name="Test",
            first_name="Person",
            sex="1",
            date_of_birth=date(1980, 1, 1),
            birth_place_type=PlaceType.UNKNOWN,
            religion="111",
            marital_status="1",
            nationality_type=NationalityType.FOREIGN,
            nationality_status="2",
            nationality_country_id=8207,
            nationality_country_iso2="DE",
            nationality_country_name="Deutschland",
            # residence_permit is None - should fail at conversion
        )
        with pytest.raises(ValueError, match="residence_permit required"):
            person.to_ech0011_person()

    def test_swiss_birth_place_requires_municipality_name(self):
        """Swiss birth place without municipality name should fail."""
        with pytest.raises(ValueError, match="birth_municipality_name required"):
            StatisticsPerson(
                local_person_id="12345",
                local_person_id_category="MU.6172",
                official_name="Test",
                first_name="Person",
                sex="1",
                date_of_birth=date(1980, 1, 1),
                birth_place_type=PlaceType.SWISS,
                birth_municipality_bfs=261,
                # birth_municipality_name is None - should fail
                religion="111",
                marital_status="1",
                nationality_type=NationalityType.SWISS,
                nationality_status="2",
                places_of_origin=[PlaceOfOriginInfo(origin_name="Zürich", canton="ZH")],
            )

    def test_invalid_sex_value_rejected(self):
        """Invalid sex value should be rejected."""
        with pytest.raises(ValueError, match="sex must be one of"):
            StatisticsPerson(
                local_person_id="12345",
                local_person_id_category="MU.6172",
                official_name="Test",
                first_name="Person",
                sex="4",  # Invalid
                date_of_birth=date(1980, 1, 1),
                birth_place_type=PlaceType.UNKNOWN,
                religion="111",
                marital_status="1",
                nationality_type=NationalityType.SWISS,
                places_of_origin=[PlaceOfOriginInfo(origin_name="Zürich", canton="ZH")],
            )


class TestStatisticsDeliveryEventValidation:
    """Test StatisticsDeliveryEvent validation."""

    def test_secondary_residence_requires_comes_from(self, swiss_person, dwelling_address):
        """Secondary residence without comes_from should fail."""
        with pytest.raises(ValueError, match="comes_from required"):
            StatisticsDeliveryEvent(
                person=swiss_person,
                residence_type=ResidenceType.SECONDARY,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 1, 1),
                main_residence_name="Bern",
                # comes_from is None - should fail for SECONDARY
            )

    def test_secondary_residence_requires_main_residence_name(self, swiss_person, dwelling_address):
        """Secondary residence without main_residence_name should fail."""
        with pytest.raises(ValueError, match="main_residence_name required"):
            StatisticsDeliveryEvent(
                person=swiss_person,
                residence_type=ResidenceType.SECONDARY,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 1, 1),
                comes_from=DestinationInfo(
                    place_type=PlaceType.SWISS,
                    municipality_name="Bern"
                ),
                # main_residence_name is None - should fail
            )

    def test_other_residence_requires_comes_from(self, swiss_person, dwelling_address):
        """Other residence without comes_from should fail."""
        with pytest.raises(ValueError, match="comes_from required"):
            StatisticsDeliveryEvent(
                person=swiss_person,
                residence_type=ResidenceType.OTHER,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 1, 1),
                # comes_from is None - should fail for OTHER
            )

    def test_main_residence_allows_no_comes_from(self, swiss_person, dwelling_address):
        """Main residence should allow no comes_from."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
            # comes_from is None - OK for MAIN
        )
        assert event.comes_from is None


# ============================================================================
# LAYER 2 → LAYER 1 CONVERSION TESTS
# ============================================================================

class TestLayer2ToLayer1Conversion:
    """Test conversion from Layer 2 to Layer 1 models."""

    def test_swiss_person_conversion(self, swiss_person):
        """Swiss person should convert correctly to ECH0011Person."""
        ech0011_person = swiss_person.to_ech0011_person()

        assert ech0011_person.person_identification.official_name == "Müller"
        assert ech0011_person.person_identification.first_name == "Hans"
        assert ech0011_person.person_identification.vn == "7561234567890"
        assert len(ech0011_person.place_of_origin) == 1
        assert ech0011_person.place_of_origin[0].origin_name == "Zürich"
        assert ech0011_person.residence_permit is None

    def test_foreign_person_conversion(self, foreign_person):
        """Foreign person should convert correctly to ECH0011Person."""
        ech0011_person = foreign_person.to_ech0011_person()

        assert ech0011_person.person_identification.official_name == "Schmidt"
        assert ech0011_person.person_identification.first_name == "Maria"
        assert len(ech0011_person.place_of_origin) == 0
        assert ech0011_person.residence_permit is not None
        # BFS code "02" = B permit (Aufenthaltsbewilligung)
        assert ech0011_person.residence_permit.residence_permit.value == "02"

    def test_event_conversion_main_residence(self, swiss_person, dwelling_address):
        """Event with main residence should convert correctly."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
        )

        reported_person = event.to_ech0099_reported_person()

        assert reported_person.base_data.has_main_residence is not None
        assert reported_person.base_data.has_secondary_residence is None
        assert reported_person.base_data.has_other_residence is None

    def test_event_conversion_secondary_residence(self, swiss_person, dwelling_address):
        """Event with secondary residence should convert correctly."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.SECONDARY,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
            comes_from=DestinationInfo(
                place_type=PlaceType.SWISS,
                municipality_bfs=351,
                municipality_name="Bern"
            ),
            main_residence_bfs=351,
            main_residence_name="Bern",
        )

        reported_person = event.to_ech0099_reported_person()

        assert reported_person.base_data.has_main_residence is None
        assert reported_person.base_data.has_secondary_residence is not None
        assert reported_person.base_data.has_other_residence is None

    def test_extended_data_preserved(self, swiss_person, dwelling_address):
        """Extended data should be preserved in conversion."""
        extended_data = [
            ECH0099DataType(field="test_field", value="test_value"),
            ECH0099DataType(field="another_field", value="another_value"),
        ]

        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
            person_extended_data=extended_data,
        )

        reported_person = event.to_ech0099_reported_person()

        assert len(reported_person.person_extended_data) == 2
        assert reported_person.person_extended_data[0].field == "test_field"
        assert reported_person.person_extended_data[1].field == "another_field"


# ============================================================================
# FINALIZATION TESTS
# ============================================================================

class TestFinalization:
    """Test delivery finalization."""

    def test_finalize_single_event(self, swiss_person, dwelling_address, config):
        """Single event should finalize correctly."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
        )

        delivery = event.finalize(config)

        assert isinstance(delivery, ECH0099Delivery)
        assert len(delivery.reported_person) == 1
        assert delivery.version == "2.1"
        assert delivery.delivery_header.sender_id == "T1-6172-1"
        assert delivery.delivery_header.test_delivery_flag is True

    def test_finalize_multiple_events(self, swiss_person, foreign_person, dwelling_address, config):
        """Multiple events should finalize correctly."""
        events = [
            StatisticsDeliveryEvent(
                person=swiss_person,
                residence_type=ResidenceType.MAIN,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 1, 1),
            ),
            StatisticsDeliveryEvent(
                person=foreign_person,
                residence_type=ResidenceType.MAIN,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 6, 1),
            ),
        ]

        delivery = finalize_statistics_delivery(events, config)

        assert len(delivery.reported_person) == 2

    def test_finalize_empty_events_fails(self, config):
        """Finalizing with no events should fail."""
        with pytest.raises(ValueError, match="At least one"):
            finalize_statistics_delivery([], config)

    def test_finalize_0099_layer2_wrapper(self, swiss_person, dwelling_address, config):
        """finalize_0099_layer2 wrapper should work correctly."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
        )

        delivery = finalize_0099_layer2([event], config)

        assert isinstance(delivery, ECH0099Delivery)
        assert len(delivery.reported_person) == 1


# ============================================================================
# XML EXPORT AND XSD VALIDATION TESTS
# ============================================================================

class TestXmlExport:
    """Test XML export with XSD validation."""

    def test_export_to_file_validates_xsd(self, swiss_person, dwelling_address, config):
        """Exported XML should pass XSD validation."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
        )

        delivery = event.finalize(config)

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = Path(f.name)

        try:
            # This should not raise - XSD validation happens in to_xml()
            delivery.to_file(output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
        finally:
            output_path.unlink(missing_ok=True)

    def test_export_foreign_person_validates_xsd(self, foreign_person, dwelling_address, config):
        """Foreign person export should pass XSD validation."""
        event = StatisticsDeliveryEvent(
            person=foreign_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
        )

        delivery = event.finalize(config)

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = Path(f.name)

        try:
            delivery.to_file(output_path)
            assert output_path.exists()
        finally:
            output_path.unlink(missing_ok=True)

    def test_export_with_extended_data_validates_xsd(self, swiss_person, dwelling_address, config):
        """Export with extended data should pass XSD validation."""
        event = StatisticsDeliveryEvent(
            person=swiss_person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs=261,
            reporting_municipality_name="Zürich",
            dwelling_address=dwelling_address,
            arrival_date=date(2024, 1, 1),
            person_extended_data=[
                ECH0099DataType(field="income_category", value="3"),
                ECH0099DataType(field="housing_type", value="apartment"),
            ],
        )

        delivery = event.finalize(config)

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = Path(f.name)

        try:
            delivery.to_file(output_path)
            assert output_path.exists()
        finally:
            output_path.unlink(missing_ok=True)

    def test_export_multiple_persons_to_single_file(self, swiss_person, foreign_person, dwelling_address, config):
        """Export multiple persons (Swiss + foreign) to single XSD-validated file.

        This is the key integration test verifying that a complete eCH-0099
        delivery with multiple persons passes XSD validation.
        """
        events = [
            StatisticsDeliveryEvent(
                person=swiss_person,
                residence_type=ResidenceType.MAIN,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                reporting_municipality_canton="ZH",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 1, 1),
            ),
            StatisticsDeliveryEvent(
                person=foreign_person,
                residence_type=ResidenceType.MAIN,
                reporting_municipality_bfs=261,
                reporting_municipality_name="Zürich",
                reporting_municipality_canton="ZH",
                dwelling_address=dwelling_address,
                arrival_date=date(2024, 6, 1),
                person_extended_data=[
                    ECH0099DataType(field="employment_status", value="employed"),
                ],
            ),
        ]

        delivery = finalize_statistics_delivery(events, config)

        # Verify structure before export
        assert len(delivery.reported_person) == 2
        assert delivery.version == "2.1"

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Export with XSD validation (validation happens in to_xml())
            delivery.to_file(output_path)

            # Verify file was created with content
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Read back and verify it can be parsed
            reimported = ECH0099Delivery.from_file(output_path)
            assert len(reimported.reported_person) == 2

            # Verify person identities preserved
            person_ids = {
                rp.base_data.person.person_identification.local_person_id.person_id
                for rp in reimported.reported_person
            }
            assert person_ids == {"12345", "67890"}
        finally:
            output_path.unlink(missing_ok=True)


# ============================================================================
# DESTINATION INFO TESTS
# ============================================================================

class TestDestinationInfo:
    """Test DestinationInfo validation."""

    def test_swiss_destination_requires_municipality_name(self):
        """Swiss destination without municipality name should fail."""
        with pytest.raises(ValueError, match="municipality_name required"):
            DestinationInfo(
                place_type=PlaceType.SWISS,
                municipality_bfs=261,
                # municipality_name is None - should fail
            )

    def test_foreign_destination_requires_country(self):
        """Foreign destination without country should fail."""
        with pytest.raises(ValueError, match="country_iso2 or country_id required"):
            DestinationInfo(
                place_type=PlaceType.FOREIGN,
                # No country fields - should fail
            )

    def test_unknown_destination_requires_nothing(self):
        """Unknown destination should require no additional fields."""
        dest = DestinationInfo(place_type=PlaceType.UNKNOWN)
        assert dest.place_type == PlaceType.UNKNOWN
        assert dest.municipality_name is None
        assert dest.country_iso2 is None


# ============================================================================
# DWELLING ADDRESS TESTS
# ============================================================================

class TestDwellingAddressInfo:
    """Test DwellingAddressInfo validation."""

    def test_valid_household_types(self):
        """Valid household types should be accepted."""
        for household_type in ["0", "1", "2", "3"]:
            addr = DwellingAddressInfo(
                town="Zürich",
                swiss_zip_code=8001,
                type_of_household=household_type,
            )
            assert addr.type_of_household == household_type

    def test_invalid_household_type_rejected(self):
        """Invalid household type should be rejected."""
        with pytest.raises(ValueError, match="type_of_household must be one of"):
            DwellingAddressInfo(
                town="Zürich",
                swiss_zip_code=8001,
                type_of_household="4",  # Invalid
            )

    def test_swiss_zip_code_range(self):
        """Swiss zip code must be 4 digits (1000-9999)."""
        # Valid
        addr = DwellingAddressInfo(
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="1",
        )
        assert addr.swiss_zip_code == 8001

        # Too low
        with pytest.raises(ValueError):
            DwellingAddressInfo(
                town="Test",
                swiss_zip_code=999,
                type_of_household="1",
            )

        # Too high
        with pytest.raises(ValueError):
            DwellingAddressInfo(
                town="Test",
                swiss_zip_code=10000,
                type_of_household="1",
            )
