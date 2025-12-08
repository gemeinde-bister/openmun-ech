"""Tests for eCH-0099 v2.1 Person Data Delivery to Statistics.

Standard: eCH-0099 v2.1
Purpose: Validate Pydantic models for BFS statistics delivery
"""

import pytest
import xml.etree.ElementTree as ET
from datetime import date, datetime

from openmun_ech.ech0099 import (
    ECH0099DataType,
    ECH0099ReportedPerson,
    ECH0099Delivery,
    ECH0099ErrorInfo,
    ECH0099PersonError,
    ECH0099ValidationReport,
    ECH0099Receipt,
)
from openmun_ech.ech0011 import (
    ECH0011Person,
    ECH0011NameData,
    ECH0011BirthData,
    ECH0011GeneralPlace,
    ECH0011PlaceOfOrigin,
    ECH0011ReligionData,
    ECH0011MaritalData,
    ECH0011NationalityData,
    ECH0011CountryInfo,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification, ECH0044DatePartiallyKnown, ECH0044NamedPersonId
from openmun_ech.ech0058.v4 import ECH0058Header, ECH0058SendingApplication, ActionType
from openmun_ech.ech0008 import ECH0008Country


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_person_identification():
    """Sample person identification."""
    return ECH0044PersonIdentification(
        vn="7560123456789",
        local_person_id=ECH0044NamedPersonId(
            person_id_category="veka.id",
            person_id="MU.6172.1"
        ),
        official_name="Meier",
        first_name="Hans",
        sex="1",
        date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1980, 5, 15))
    )


@pytest.fixture
def sample_person(sample_person_identification):
    """Sample eCH-0011 person."""
    return ECH0011Person(
        person_identification=sample_person_identification,
        name_data=ECH0011NameData(
            official_name="Meier",
            first_name="Hans"
        ),
        birth_data=ECH0011BirthData(
            date_of_birth=date(1980, 5, 15),
            place_of_birth=ECH0011GeneralPlace(unknown=True),
            sex="1"
        ),
        religion_data=ECH0011ReligionData(religion="111"),
        marital_data=ECH0011MaritalData(marital_status="1"),
        nationality_data=ECH0011NationalityData(
            nationality_status="0",
            country_info=[
                ECH0011CountryInfo(
                    country=ECH0008Country(country_name_short="Schweiz"),
                    nationality_valid_from=date(1980, 5, 15)
                )
            ]
        ),
        place_of_origin=[
            ECH0011PlaceOfOrigin(
                origin_name="Bern",
                canton="BE"
            )
        ]
    )


@pytest.fixture
def sample_reported_person(sample_person):
    """Sample eCH-0011 reported person (person + residence)."""
    from openmun_ech.ech0011.v8 import (
        ECH0011ReportedPerson,
        ECH0011MainResidence,
        ECH0011ResidenceData,
        ECH0011DwellingAddress,
        TypeOfHousehold,
    )
    from openmun_ech.ech0007 import ECH0007Municipality, ECH0007SwissMunicipality
    from openmun_ech.ech0010 import ECH0010SwissAddressInformation

    # Create a reported person with a main residence
    return ECH0011ReportedPerson(
        person=sample_person,
        has_main_residence=ECH0011MainResidence(
            main_residence=ECH0011ResidenceData(
                reporting_municipality=ECH0007Municipality(
                    swiss_municipality=ECH0007SwissMunicipality(
                        municipality_id="6172",
                        municipality_name="Bister",
                        canton_fl_abbreviation="VS"
                    )
                ),
                arrival_date=date(2020, 1, 15),
                dwelling_address=ECH0011DwellingAddress(
                    address=ECH0010SwissAddressInformation(
                        address_line1="Hauptstrasse 1",
                        swiss_zip_code=3989,
                        town="Bister",
                        country="CH"
                    ),
                    type_of_household=TypeOfHousehold.PRIVATE_HOUSEHOLD,
                    egid=12345,
                    ewid=1
                )
            )
        )
    )


@pytest.fixture
def sample_header():
    """Sample eCH-0058 v4 header."""
    return ECH0058Header(
        sender_id="T0-CH-6172",
        recipient_id=["T0-CH-BFS"],
        message_id="msg-12345",
        message_type="2310099",
        sending_application=ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="OpenMun Statistics Export",
            product_version="1.0.0"
        ),
        action=ActionType.NEW,
        test_delivery_flag=True,
        message_date=datetime(2025, 10, 25, 10, 30, 0)
    )


# ============================================================================
# ECH0099DataType Tests
# ============================================================================

def test_data_type_creation():
    """Test creating a data type instance."""
    data = ECH0099DataType(
        field="housing_type",
        value="single_family"
    )

    assert data.field == "housing_type"
    assert data.value == "single_family"


def test_data_type_min_length_validation():
    """Test field and value minimum length validation."""
    # Empty field should fail
    with pytest.raises(ValueError, match="String should have at least 1 character"):
        ECH0099DataType(field="", value="test")

    # Empty value should fail
    with pytest.raises(ValueError, match="String should have at least 1 character"):
        ECH0099DataType(field="test", value="")


def test_data_type_max_length_validation():
    """Test field and value maximum length validation."""
    # Field too long (>100 chars)
    with pytest.raises(ValueError, match="String should have at most 100 characters"):
        ECH0099DataType(
            field="x" * 101,
            value="test"
        )

    # Value too long (>1000 chars)
    with pytest.raises(ValueError, match="String should have at most 1000 characters"):
        ECH0099DataType(
            field="test",
            value="x" * 1001
        )


def test_data_type_to_xml():
    """Test data type XML export."""
    data = ECH0099DataType(
        field="income_category",
        value="middle"
    )

    elem = data.to_xml()

    # Check structure
    assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}data'

    # Check field
    field_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}field')
    assert field_elem is not None
    assert field_elem.text == "income_category"

    # Check value
    value_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}value')
    assert value_elem is not None
    assert value_elem.text == "middle"


def test_data_type_xml_roundtrip():
    """Test data type XML export and import roundtrip."""
    original = ECH0099DataType(
        field="education_level",
        value="university"
    )

    xml = original.to_xml()
    restored = ECH0099DataType.from_xml(xml)

    assert restored.field == original.field
    assert restored.value == original.value


def test_data_type_custom_element_name():
    """Test data type with custom element name (personExtendedData vs generalData)."""
    data = ECH0099DataType(field="test", value="value")

    # Test with personExtendedData
    elem1 = data.to_xml(element_name='personExtendedData')
    assert elem1.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}personExtendedData'

    # Test with generalData
    elem2 = data.to_xml(element_name='generalData')
    assert elem2.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}generalData'


# ============================================================================
# ECH0099ReportedPerson Tests
# ============================================================================

def test_reported_person_minimal(sample_reported_person):
    """Test creating a reported person with minimal data."""
    reported = ECH0099ReportedPerson(
        base_data=sample_reported_person
    )

    assert reported.base_data == sample_reported_person
    assert reported.person_extended_data == []


def test_reported_person_with_extended_data(sample_reported_person):
    """Test creating a reported person with extended data."""
    extended_data = [
        ECH0099DataType(field="housing_type", value="apartment"),
        ECH0099DataType(field="employment_sector", value="public")
    ]

    reported = ECH0099ReportedPerson(
        base_data=sample_reported_person,
        person_extended_data=extended_data
    )

    assert reported.base_data == sample_reported_person
    assert len(reported.person_extended_data) == 2
    assert reported.person_extended_data[0].field == "housing_type"
    assert reported.person_extended_data[1].field == "employment_sector"


def test_reported_person_to_xml(sample_reported_person):
    """Test reported person XML export."""
    extended_data = [
        ECH0099DataType(field="test_field", value="test_value")
    ]

    reported = ECH0099ReportedPerson(
        base_data=sample_reported_person,
        person_extended_data=extended_data
    )

    elem = reported.to_xml()

    # Check structure
    assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}reportedPerson'

    # Check baseData exists (eCH-0099 namespace wrapping eCH-0011 content)
    base_data_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}baseData')
    assert base_data_elem is not None

    # Check personExtendedData
    extended_elems = elem.findall('{http://www.ech.ch/xmlns/eCH-0099/2}personExtendedData')
    assert len(extended_elems) == 1


def test_reported_person_xml_roundtrip(sample_reported_person):
    """Test reported person XML export and import roundtrip."""
    original = ECH0099ReportedPerson(
        base_data=sample_reported_person,
        person_extended_data=[
            ECH0099DataType(field="field1", value="value1"),
            ECH0099DataType(field="field2", value="value2")
        ]
    )

    xml = original.to_xml()
    restored = ECH0099ReportedPerson.from_xml(xml)

    assert restored.base_data.person.person_identification.vn == original.base_data.person.person_identification.vn
    assert len(restored.person_extended_data) == 2
    assert restored.person_extended_data[0].field == "field1"
    assert restored.person_extended_data[1].field == "field2"


# ============================================================================
# ECH0099Delivery Tests
# ============================================================================

def test_delivery_minimal(sample_header, sample_reported_person):
    """Test creating a delivery with minimal data."""
    reported = ECH0099ReportedPerson(base_data=sample_reported_person)

    delivery = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=[reported]
    )

    assert delivery.delivery_header == sample_header
    assert len(delivery.reported_person) == 1
    assert delivery.general_data == []
    assert delivery.version == "2.1"


def test_delivery_with_multiple_persons(sample_header, sample_person_identification):
    """Test delivery with multiple persons."""
    from openmun_ech.ech0011.v8 import (
        ECH0011ReportedPerson,
        ECH0011MainResidence,
        ECH0011ResidenceData,
        ECH0011DwellingAddress,
        TypeOfHousehold,
    )
    from openmun_ech.ech0007 import ECH0007Municipality, ECH0007SwissMunicipality
    from openmun_ech.ech0010 import ECH0010SwissAddressInformation

    # Create first person with residence
    person1 = ECH0011Person(
        person_identification=ECH0044PersonIdentification(
            vn="7560123456789",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.1"
            ),
            official_name="Meier",
            first_name="Hans",
            sex="1",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1980, 5, 15))
        ),
        name_data=ECH0011NameData(official_name="Meier", first_name="Hans"),
        birth_data=ECH0011BirthData(date_of_birth=date(1980, 5, 15), place_of_birth=ECH0011GeneralPlace(unknown=True), sex="1"),
        religion_data=ECH0011ReligionData(religion="111"),
        marital_data=ECH0011MaritalData(marital_status="1"),
        nationality_data=ECH0011NationalityData(
            nationality_status="0",
            country_info=[ECH0011CountryInfo(
                country=ECH0008Country(country_name_short="Schweiz"),
                nationality_valid_from=date(1980, 5, 15)
            )]
        ),
        place_of_origin=[ECH0011PlaceOfOrigin(origin_name="Bern", canton="BE")]
    )

    reported_person1 = ECH0011ReportedPerson(
        person=person1,
        has_main_residence=ECH0011MainResidence(
            main_residence=ECH0011ResidenceData(
                reporting_municipality=ECH0007Municipality(
                    swiss_municipality=ECH0007SwissMunicipality(
                        municipality_id="6172",
                        municipality_name="Bister",
                        canton_fl_abbreviation="VS"
                    )
                ),
                arrival_date=date(1980, 5, 15),
                dwelling_address=ECH0011DwellingAddress(
                    address=ECH0010SwissAddressInformation(
                        address_line1="Hauptstrasse 1",
                        swiss_zip_code=3989,
                        town="Bister",
                        country="CH"
                    ),
                    type_of_household=TypeOfHousehold.PRIVATE_HOUSEHOLD,
                    egid=12345,
                    ewid=1
                )
            )
        )
    )

    # Create second person with residence
    person2 = ECH0011Person(
        person_identification=ECH0044PersonIdentification(
            vn="7569876543210",
            local_person_id=ECH0044NamedPersonId(
                person_id_category="veka.id",
                person_id="MU.6172.2"
            ),
            official_name="Müller",
            first_name="Maria",
            sex="2",
            date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1985, 8, 20))
        ),
        name_data=ECH0011NameData(official_name="Müller", first_name="Maria"),
        birth_data=ECH0011BirthData(date_of_birth=date(1985, 8, 20), place_of_birth=ECH0011GeneralPlace(unknown=True), sex="2"),
        religion_data=ECH0011ReligionData(religion="111"),
        marital_data=ECH0011MaritalData(marital_status="1"),
        nationality_data=ECH0011NationalityData(
            nationality_status="0",
            country_info=[ECH0011CountryInfo(
                country=ECH0008Country(country_name_short="Schweiz"),
                nationality_valid_from=date(1985, 8, 20)
            )]
        ),
        place_of_origin=[ECH0011PlaceOfOrigin(origin_name="Zürich", canton="ZH")]
    )

    reported_person2 = ECH0011ReportedPerson(
        person=person2,
        has_main_residence=ECH0011MainResidence(
            main_residence=ECH0011ResidenceData(
                reporting_municipality=ECH0007Municipality(
                    swiss_municipality=ECH0007SwissMunicipality(
                        municipality_id="6172",
                        municipality_name="Bister",
                        canton_fl_abbreviation="VS"
                    )
                ),
                arrival_date=date(1985, 8, 20),
                dwelling_address=ECH0011DwellingAddress(
                    address=ECH0010SwissAddressInformation(
                        address_line1="Dorfstrasse 5",
                        swiss_zip_code=3989,
                        town="Bister",
                        country="CH"
                    ),
                    type_of_household=TypeOfHousehold.PRIVATE_HOUSEHOLD,
                    egid=12346,
                    ewid=1
                )
            )
        )
    )

    persons = [
        ECH0099ReportedPerson(base_data=reported_person1),
        ECH0099ReportedPerson(base_data=reported_person2)
    ]

    delivery = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=persons
    )

    assert len(delivery.reported_person) == 2


def test_delivery_with_general_data(sample_header, sample_reported_person):
    """Test delivery with general data."""
    reported = ECH0099ReportedPerson(base_data=sample_reported_person)
    general_data = [
        ECH0099DataType(field="municipality_id", value="6172"),
        ECH0099DataType(field="reporting_date", value="2025-10-25")
    ]

    delivery = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=[reported],
        general_data=general_data
    )

    assert len(delivery.general_data) == 2
    assert delivery.general_data[0].field == "municipality_id"


def test_delivery_requires_at_least_one_person(sample_header):
    """Test that delivery requires at least one person."""
    with pytest.raises(ValueError, match="at least 1 item"):
        ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[]
        )


def test_delivery_version_validation(sample_header, sample_reported_person):
    """Test that delivery version must be '2.1'."""
    reported = ECH0099ReportedPerson(base_data=sample_reported_person)

    # Valid version
    delivery = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=[reported],
        version="2.1"
    )
    assert delivery.version == "2.1"

    # Invalid version
    with pytest.raises(ValueError, match="Version must be '2.1'"):
        ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[reported],
            version="3.0"
        )


def test_delivery_to_xml(sample_header, sample_reported_person):
    """Test delivery XML export."""
    reported = ECH0099ReportedPerson(base_data=sample_reported_person)
    general_data = [ECH0099DataType(field="test", value="data")]

    delivery = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=[reported],
        general_data=general_data
    )

    root = delivery.to_xml()

    # Check root element
    assert root.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}delivery'
    assert root.get('version') == "2.1"

    # Check deliveryHeader (eCH-0099 namespace wraps eCH-0058 content)
    header_elem = root.find('{http://www.ech.ch/xmlns/eCH-0099/2}deliveryHeader')
    assert header_elem is not None

    # Check reportedPerson
    person_elems = root.findall('{http://www.ech.ch/xmlns/eCH-0099/2}reportedPerson')
    assert len(person_elems) == 1

    # Check generalData
    data_elems = root.findall('{http://www.ech.ch/xmlns/eCH-0099/2}generalData')
    assert len(data_elems) == 1


def test_delivery_xml_roundtrip(sample_header, sample_reported_person):
    """Test delivery XML export and import roundtrip."""
    original = ECH0099Delivery(
        delivery_header=sample_header,
        reported_person=[
            ECH0099ReportedPerson(
                base_data=sample_reported_person,
                person_extended_data=[
                    ECH0099DataType(field="test", value="value")
                ]
            )
        ],
        general_data=[
            ECH0099DataType(field="general", value="data")
        ]
    )

    xml = original.to_xml()
    restored = ECH0099Delivery.from_xml(xml)

    assert restored.version == "2.1"
    assert restored.delivery_header.sender_id == sample_header.sender_id
    assert len(restored.reported_person) == 1
    assert len(restored.general_data) == 1


# ============================================================================
# ECH0099ErrorInfo Tests
# ============================================================================

def test_error_info_creation():
    """Test creating error info."""
    error = ECH0099ErrorInfo(
        code="ERR-001",
        text="Missing required field: birthdate"
    )

    assert error.code == "ERR-001"
    assert error.text == "Missing required field: birthdate"


def test_error_info_to_xml():
    """Test error info XML export."""
    error = ECH0099ErrorInfo(
        code="ERR-002",
        text="Invalid VN format"
    )

    elem = error.to_xml()

    assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}errorInfo'

    code_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}code')
    assert code_elem is not None
    assert code_elem.text == "ERR-002"

    text_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}text')
    assert text_elem is not None
    assert text_elem.text == "Invalid VN format"


def test_error_info_xml_roundtrip():
    """Test error info XML roundtrip."""
    original = ECH0099ErrorInfo(
        code="ERR-123",
        text="Test error message"
    )

    xml = original.to_xml()
    restored = ECH0099ErrorInfo.from_xml(xml)

    assert restored.code == original.code
    assert restored.text == original.text


# ============================================================================
# ECH0099PersonError Tests
# ============================================================================

def test_person_error_creation(sample_person_identification):
    """Test creating person error."""
    errors = [
        ECH0099ErrorInfo(code="ERR-001", text="Missing birthdate"),
        ECH0099ErrorInfo(code="ERR-002", text="Invalid nationality")
    ]

    person_error = ECH0099PersonError(
        person_identification=sample_person_identification,
        error_info=errors
    )

    assert person_error.person_identification == sample_person_identification
    assert len(person_error.error_info) == 2


def test_person_error_requires_at_least_one_error(sample_person_identification):
    """Test that person error requires at least one error."""
    with pytest.raises(ValueError, match="at least 1 item"):
        ECH0099PersonError(
            person_identification=sample_person_identification,
            error_info=[]
        )


def test_person_error_to_xml(sample_person_identification):
    """Test person error XML export."""
    person_error = ECH0099PersonError(
        person_identification=sample_person_identification,
        error_info=[
            ECH0099ErrorInfo(code="ERR-001", text="Test error")
        ]
    )

    elem = person_error.to_xml()

    assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}personError'

    # Check personIdentification (eCH-0099 namespace wraps eCH-0044 content)
    person_id_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0099/2}personIdentification')
    assert person_id_elem is not None

    # Check errorInfo
    error_elems = elem.findall('{http://www.ech.ch/xmlns/eCH-0099/2}errorInfo')
    assert len(error_elems) == 1


def test_person_error_xml_roundtrip(sample_person_identification):
    """Test person error XML roundtrip."""
    original = ECH0099PersonError(
        person_identification=sample_person_identification,
        error_info=[
            ECH0099ErrorInfo(code="ERR-001", text="Error 1"),
            ECH0099ErrorInfo(code="ERR-002", text="Error 2")
        ]
    )

    xml = original.to_xml()
    restored = ECH0099PersonError.from_xml(xml)

    assert restored.person_identification.vn == sample_person_identification.vn
    assert len(restored.error_info) == 2
    assert restored.error_info[0].code == "ERR-001"


# ============================================================================
# ECH0099ValidationReport Tests
# ============================================================================

def test_validation_report_minimal(sample_header):
    """Test creating validation report with minimal data."""
    report = ECH0099ValidationReport(
        validation_report_header=sample_header
    )

    assert report.validation_report_header == sample_header
    assert report.general_error == []
    assert report.person_error == []
    assert report.general_data == []
    assert report.version == "2.1"


def test_validation_report_with_errors(sample_header, sample_person_identification):
    """Test validation report with errors."""
    general_errors = [
        ECH0099ErrorInfo(code="GEN-001", text="Invalid XML structure")
    ]

    person_errors = [
        ECH0099PersonError(
            person_identification=sample_person_identification,
            error_info=[
                ECH0099ErrorInfo(code="ERR-001", text="Missing data")
            ]
        )
    ]

    report = ECH0099ValidationReport(
        validation_report_header=sample_header,
        general_error=general_errors,
        person_error=person_errors
    )

    assert len(report.general_error) == 1
    assert len(report.person_error) == 1


def test_validation_report_version_validation(sample_header):
    """Test validation report version must be '2.1'."""
    # Valid
    report = ECH0099ValidationReport(
        validation_report_header=sample_header,
        version="2.1"
    )
    assert report.version == "2.1"

    # Invalid
    with pytest.raises(ValueError, match="Version must be '2.1'"):
        ECH0099ValidationReport(
            validation_report_header=sample_header,
            version="1.0"
        )


def test_validation_report_to_xml(sample_header, sample_person_identification):
    """Test validation report XML export."""
    report = ECH0099ValidationReport(
        validation_report_header=sample_header,
        general_error=[
            ECH0099ErrorInfo(code="GEN-001", text="General error")
        ],
        person_error=[
            ECH0099PersonError(
                person_identification=sample_person_identification,
                error_info=[
                    ECH0099ErrorInfo(code="ERR-001", text="Person error")
                ]
            )
        ],
        general_data=[
            ECH0099DataType(field="report_date", value="2025-10-25")
        ]
    )

    root = report.to_xml()

    # Check root
    assert root.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}validationReport'
    assert root.get('version') == "2.1"

    # Check header (eCH-0099 namespace wraps eCH-0058 content)
    header_elem = root.find('{http://www.ech.ch/xmlns/eCH-0099/2}validationReportHeader')
    assert header_elem is not None

    # Check errors
    general_error_elems = root.findall('{http://www.ech.ch/xmlns/eCH-0099/2}generalError')
    assert len(general_error_elems) == 1

    person_error_elems = root.findall('{http://www.ech.ch/xmlns/eCH-0099/2}personError')
    assert len(person_error_elems) == 1

    data_elems = root.findall('{http://www.ech.ch/xmlns/eCH-0099/2}generalData')
    assert len(data_elems) == 1


def test_validation_report_xml_roundtrip(sample_header, sample_person_identification):
    """Test validation report XML roundtrip."""
    original = ECH0099ValidationReport(
        validation_report_header=sample_header,
        general_error=[
            ECH0099ErrorInfo(code="GEN-001", text="General error")
        ],
        person_error=[
            ECH0099PersonError(
                person_identification=sample_person_identification,
                error_info=[
                    ECH0099ErrorInfo(code="ERR-001", text="Person error")
                ]
            )
        ]
    )

    xml = original.to_xml()
    restored = ECH0099ValidationReport.from_xml(xml)

    assert restored.version == "2.1"
    assert len(restored.general_error) == 1
    assert len(restored.person_error) == 1


# ============================================================================
# ECH0099Receipt Tests
# ============================================================================

def test_receipt_creation(sample_header):
    """Test creating receipt."""
    receipt = ECH0099Receipt(
        receipt_header=sample_header,
        event_time=date(2025, 10, 25)
    )

    assert receipt.receipt_header == sample_header
    assert receipt.event_time == date(2025, 10, 25)
    assert receipt.version == "2.1"


def test_receipt_version_validation(sample_header):
    """Test receipt version must be '2.1'."""
    # Valid
    receipt = ECH0099Receipt(
        receipt_header=sample_header,
        event_time=date(2025, 10, 25),
        version="2.1"
    )
    assert receipt.version == "2.1"

    # Invalid
    with pytest.raises(ValueError, match="Version must be '2.1'"):
        ECH0099Receipt(
            receipt_header=sample_header,
            event_time=date(2025, 10, 25),
            version="2.0"
        )


def test_receipt_to_xml(sample_header):
    """Test receipt XML export."""
    receipt = ECH0099Receipt(
        receipt_header=sample_header,
        event_time=date(2025, 10, 25)
    )

    root = receipt.to_xml()

    # Check root
    assert root.tag == '{http://www.ech.ch/xmlns/eCH-0099/2}receipt'
    assert root.get('version') == "2.1"

    # Check header (eCH-0099 namespace wraps eCH-0058 content)
    header_elem = root.find('{http://www.ech.ch/xmlns/eCH-0099/2}receiptHeader')
    assert header_elem is not None

    # Check eventTime
    event_time_elem = root.find('{http://www.ech.ch/xmlns/eCH-0099/2}eventTime')
    assert event_time_elem is not None
    assert event_time_elem.text == "2025-10-25"


def test_receipt_xml_roundtrip(sample_header):
    """Test receipt XML roundtrip."""
    original = ECH0099Receipt(
        receipt_header=sample_header,
        event_time=date(2025, 10, 25)
    )

    xml = original.to_xml()
    restored = ECH0099Receipt.from_xml(xml)

    assert restored.version == "2.1"
    assert restored.event_time == original.event_time
    assert restored.receipt_header.sender_id == sample_header.sender_id
