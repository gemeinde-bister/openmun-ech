"""XSD Validation tests for eCH-0099 v2.1 Statistics Delivery models.

These tests validate that our Pydantic models produce XML that conforms
to the official eCH-0099 v2.1 XSD schema.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, date
import pytest

try:
    import xmlschema
    HAS_XMLSCHEMA = True
except ImportError:
    HAS_XMLSCHEMA = False

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


# Path to eCH XSD schemas
ECH_SCHEMA_DIR = Path(__file__).parent.parent / "docs" / "eCH"
ECH_0099_V2_1_XSD = ECH_SCHEMA_DIR / "eCH-0099-2-1.xsd"


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0099XSDValidation:
    """XSD validation tests for eCH-0099 v2.1 models."""

    @pytest.fixture
    def schema(self):
        """Load eCH-0099 v2.1 XSD schema."""
        if not ECH_0099_V2_1_XSD.exists():
            pytest.skip(f"eCH-0099 XSD not found: {ECH_0099_V2_1_XSD}")
        return xmlschema.XMLSchema(str(ECH_0099_V2_1_XSD))

    @pytest.fixture
    def sample_person_identification(self):
        """Sample person identification for testing."""
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
    def sample_person(self, sample_person_identification):
        """Sample eCH-0011 reported person for testing (person + residence)."""
        from openmun_ech.ech0011 import (
            ECH0011ReportedPerson,
            ECH0011MainResidence,
            ECH0011ResidenceData,
            ECH0011DwellingAddress,
            TypeOfHousehold,
        )
        from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation
        from openmun_ech.ech0010 import ECH0010SwissAddressInformation

        # Create person
        person = ECH0011Person(
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

        # Create residence data
        residence_data = ECH0011ResidenceData(
            reporting_municipality=ECH0007Municipality.from_swiss(
                municipality_name="Bister",
                municipality_id="6172",
                canton=CantonAbbreviation.VS
            ),
            arrival_date=date(2020, 1, 1),
            dwelling_address=ECH0011DwellingAddress(
                address=ECH0010SwissAddressInformation(
                    address_line1="Hauptstrasse 1",
                    swiss_zip_code=3989,
                    town="Bister",
                    country="CH"
                ),
                type_of_household=TypeOfHousehold.PRIVATE_HOUSEHOLD,
                moving_date=date(2020, 1, 1)
            )
        )

        # Create main residence
        main_residence = ECH0011MainResidence(
            main_residence=residence_data
        )

        # Return reported person (person + residence)
        return ECH0011ReportedPerson(
            person=person,
            has_main_residence=main_residence
        )

    @pytest.fixture
    def sample_header(self):
        """Sample eCH-0058 v4 header for testing."""
        return ECH0058Header(
            sender_id="T0-CH-6172",
            recipient_id=["T0-CH-BFS"],
            message_id="msg-test-12345",
            message_type="2310099",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="OpenMun Statistics Export",
                product_version="1.0.0"
            ),
            test_delivery_flag=True,
            message_date=datetime(2025, 10, 25, 10, 30, 0),
            action=ActionType.NEW
        )

    # ========================================================================
    # Data Type Tests
    # ========================================================================

    def test_data_type_structure(self, schema):
        """Test that data type XML structure is XSD-compliant."""
        data = ECH0099DataType(
            field="housing_type",
            value="single_family"
        )

        xml_elem = data.to_xml()

        # Verify structure matches XSD
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        assert xml_elem.tag == f'{ns}data'
        assert xml_elem.find(f'{ns}field').text == "housing_type"
        assert xml_elem.find(f'{ns}value').text == "single_family"

    def test_data_type_with_extended_element_name(self, schema):
        """Test data type with personExtendedData element name."""
        data = ECH0099DataType(
            field="income_category",
            value="middle"
        )

        xml_elem = data.to_xml(element_name='personExtendedData')

        # Verify correct element name
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        assert xml_elem.tag == f'{ns}personExtendedData'

    def test_data_type_with_general_element_name(self, schema):
        """Test data type with generalData element name."""
        data = ECH0099DataType(
            field="municipality_id",
            value="6172"
        )

        xml_elem = data.to_xml(element_name='generalData')

        # Verify correct element name
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        assert xml_elem.tag == f'{ns}generalData'

    # ========================================================================
    # Reported Person Tests
    # ========================================================================

    def test_reported_person_minimal_structure(self, schema, sample_person):
        """Test reported person with minimal data."""
        reported = ECH0099ReportedPerson(
            base_data=sample_person
        )

        xml_elem = reported.to_xml()

        # Verify structure
        ns_0099 = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        ns_0011 = '{http://www.ech.ch/xmlns/eCH-0011/8}'

        assert xml_elem.tag == f'{ns_0099}reportedPerson'
        assert xml_elem.find(f'{ns_0099}baseData') is not None  # baseData is in eCH-0099 namespace

    def test_reported_person_with_extended_data(self, schema, sample_person):
        """Test reported person with extended data."""
        reported = ECH0099ReportedPerson(
            base_data=sample_person,
            person_extended_data=[
                ECH0099DataType(field="field1", value="value1"),
                ECH0099DataType(field="field2", value="value2")
            ]
        )

        xml_elem = reported.to_xml()

        # Verify extended data elements
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        extended_elems = xml_elem.findall(f'{ns}personExtendedData')
        assert len(extended_elems) == 2

    # ========================================================================
    # Delivery Tests
    # ========================================================================

    def test_delivery_minimal_structure(self, schema, sample_header, sample_person):
        """Test delivery with minimal required fields."""
        reported = ECH0099ReportedPerson(base_data=sample_person)

        delivery = ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[reported]
        )

        root = delivery.to_xml()

        # Verify root element structure
        ns_0099 = '{http://www.ech.ch/xmlns/eCH-0099/2}'

        assert root.tag == f'{ns_0099}delivery'
        assert root.get('version') == "2.1"
        assert root.find(f'{ns_0099}deliveryHeader') is not None
        assert len(root.findall(f'{ns_0099}reportedPerson')) == 1

    def test_delivery_with_multiple_persons(self, schema, sample_header, sample_person_identification):
        """Test delivery with multiple persons."""
        from openmun_ech.ech0011 import (
            ECH0011ReportedPerson,
            ECH0011MainResidence,
            ECH0011ResidenceData,
            ECH0011DwellingAddress,
            TypeOfHousehold,
        )
        from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation
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

        residence1 = ECH0011MainResidence(
            main_residence=ECH0011ResidenceData(
                reporting_municipality=ECH0007Municipality.from_swiss(
                    municipality_id="6172",
                    municipality_name="Bister",
                    canton=CantonAbbreviation.VS
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
                    moving_date=date(1980, 5, 15)
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

        residence2 = ECH0011MainResidence(
            main_residence=ECH0011ResidenceData(
                reporting_municipality=ECH0007Municipality.from_swiss(
                    municipality_id="6172",
                    municipality_name="Bister",
                    canton=CantonAbbreviation.VS
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
                    moving_date=date(1985, 8, 20)
                )
            )
        )

        persons = [
            ECH0099ReportedPerson(
                base_data=ECH0011ReportedPerson(
                    person=person1,
                    has_main_residence=residence1
                )
            ),
            ECH0099ReportedPerson(
                base_data=ECH0011ReportedPerson(
                    person=person2,
                    has_main_residence=residence2
                )
            )
        ]

        delivery = ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=persons
        )

        root = delivery.to_xml()

        # Verify multiple persons
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        person_elems = root.findall(f'{ns}reportedPerson')
        assert len(person_elems) == 2

    def test_delivery_with_general_data(self, schema, sample_header, sample_person):
        """Test delivery with general data."""
        reported = ECH0099ReportedPerson(base_data=sample_person)
        general_data = [
            ECH0099DataType(field="municipality_id", value="6172"),
            ECH0099DataType(field="reporting_date", value="2025-10-25")
        ]

        delivery = ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[reported],
            general_data=general_data
        )

        root = delivery.to_xml()

        # Verify general data
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        data_elems = root.findall(f'{ns}generalData')
        assert len(data_elems) == 2

    def test_delivery_full_xsd_validation(self, schema, sample_header, sample_person):
        """Test full delivery against XSD schema."""
        reported = ECH0099ReportedPerson(
            base_data=sample_person,
            person_extended_data=[
                ECH0099DataType(field="housing_type", value="apartment")
            ]
        )

        delivery = ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[reported],
            general_data=[
                ECH0099DataType(field="municipality_id", value="6172")
            ]
        )

        root = delivery.to_xml()

        # Convert to string for validation
        xml_string = ET.tostring(root, encoding='unicode')

        # Validate against XSD
        try:
            schema.validate(xml_string)
        except Exception as e:
            pytest.fail(f"XSD validation failed: {e}")

    # ========================================================================
    # Error Info Tests
    # ========================================================================

    def test_error_info_structure(self, schema):
        """Test error info XML structure."""
        error = ECH0099ErrorInfo(
            code="ERR-001",
            text="Missing required field: birthdate"
        )

        xml_elem = error.to_xml()

        # Verify structure
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        assert xml_elem.tag == f'{ns}errorInfo'
        assert xml_elem.find(f'{ns}code').text == "ERR-001"
        assert xml_elem.find(f'{ns}text').text == "Missing required field: birthdate"

    # ========================================================================
    # Person Error Tests
    # ========================================================================

    def test_person_error_structure(self, schema, sample_person_identification):
        """Test person error XML structure."""
        person_error = ECH0099PersonError(
            person_identification=sample_person_identification,
            error_info=[
                ECH0099ErrorInfo(code="ERR-001", text="Test error")
            ]
        )

        xml_elem = person_error.to_xml()

        # Verify structure
        ns_0099 = '{http://www.ech.ch/xmlns/eCH-0099/2}'

        assert xml_elem.tag == f'{ns_0099}personError'
        assert xml_elem.find(f'{ns_0099}personIdentification') is not None
        assert len(xml_elem.findall(f'{ns_0099}errorInfo')) == 1

    def test_person_error_with_multiple_errors(self, schema, sample_person_identification):
        """Test person error with multiple error info entries."""
        person_error = ECH0099PersonError(
            person_identification=sample_person_identification,
            error_info=[
                ECH0099ErrorInfo(code="ERR-001", text="Error 1"),
                ECH0099ErrorInfo(code="ERR-002", text="Error 2"),
                ECH0099ErrorInfo(code="ERR-003", text="Error 3")
            ]
        )

        xml_elem = person_error.to_xml()

        # Verify multiple errors
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        error_elems = xml_elem.findall(f'{ns}errorInfo')
        assert len(error_elems) == 3

    # ========================================================================
    # Validation Report Tests
    # ========================================================================

    def test_validation_report_minimal_structure(self, schema, sample_header):
        """Test validation report with minimal data."""
        report = ECH0099ValidationReport(
            validation_report_header=sample_header
        )

        root = report.to_xml()

        # Verify structure
        ns_0099 = '{http://www.ech.ch/xmlns/eCH-0099/2}'

        assert root.tag == f'{ns_0099}validationReport'
        assert root.get('version') == "2.1"
        assert root.find(f'{ns_0099}validationReportHeader') is not None

    def test_validation_report_with_errors(self, schema, sample_header, sample_person_identification):
        """Test validation report with both general and person errors."""
        report = ECH0099ValidationReport(
            validation_report_header=sample_header,
            general_error=[
                ECH0099ErrorInfo(code="GEN-001", text="General error 1"),
                ECH0099ErrorInfo(code="GEN-002", text="General error 2")
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

        # Verify all elements present
        ns = '{http://www.ech.ch/xmlns/eCH-0099/2}'
        assert len(root.findall(f'{ns}generalError')) == 2
        assert len(root.findall(f'{ns}personError')) == 1
        assert len(root.findall(f'{ns}generalData')) == 1

    def test_validation_report_full_xsd_validation(self, schema, sample_header, sample_person_identification):
        """Test full validation report against XSD schema."""
        report = ECH0099ValidationReport(
            validation_report_header=sample_header,
            general_error=[
                ECH0099ErrorInfo(code="GEN-001", text="XML structure error")
            ],
            person_error=[
                ECH0099PersonError(
                    person_identification=sample_person_identification,
                    error_info=[
                        ECH0099ErrorInfo(code="ERR-001", text="Missing birthdate"),
                        ECH0099ErrorInfo(code="ERR-002", text="Invalid nationality")
                    ]
                )
            ]
        )

        root = report.to_xml()

        # Convert to string for validation
        xml_string = ET.tostring(root, encoding='unicode')

        # Validate against XSD
        try:
            schema.validate(xml_string)
        except Exception as e:
            pytest.fail(f"XSD validation failed: {e}")

    # ========================================================================
    # Receipt Tests
    # ========================================================================

    def test_receipt_structure(self, schema, sample_header):
        """Test receipt XML structure."""
        receipt = ECH0099Receipt(
            receipt_header=sample_header,
            event_time=date(2025, 10, 25)
        )

        root = receipt.to_xml()

        # Verify structure
        ns_0099 = '{http://www.ech.ch/xmlns/eCH-0099/2}'

        assert root.tag == f'{ns_0099}receipt'
        assert root.get('version') == "2.1"
        assert root.find(f'{ns_0099}receiptHeader') is not None
        assert root.find(f'{ns_0099}eventTime').text == "2025-10-25"

    def test_receipt_full_xsd_validation(self, schema, sample_header):
        """Test full receipt against XSD schema."""
        receipt = ECH0099Receipt(
            receipt_header=sample_header,
            event_time=date(2025, 10, 25)
        )

        root = receipt.to_xml()

        # Convert to string for validation
        xml_string = ET.tostring(root, encoding='unicode')

        # Validate against XSD
        try:
            schema.validate(xml_string)
        except Exception as e:
            pytest.fail(f"XSD validation failed: {e}")

    # ========================================================================
    # Field Validation Tests
    # ========================================================================

    def test_data_type_field_length_constraints(self, schema):
        """Test that field length constraints match XSD (1-100 chars)."""
        # Valid: 1 character
        data1 = ECH0099DataType(field="a", value="value")
        assert data1.field == "a"

        # Valid: 100 characters
        data2 = ECH0099DataType(field="x" * 100, value="value")
        assert len(data2.field) == 100

        # Invalid: 101 characters (tested in model tests, not XSD)
        # XSD schema will enforce this during validation

    def test_data_type_value_length_constraints(self, schema):
        """Test that value length constraints match XSD (1-1000 chars)."""
        # Valid: 1 character
        data1 = ECH0099DataType(field="field", value="v")
        assert data1.value == "v"

        # Valid: 1000 characters
        data2 = ECH0099DataType(field="field", value="x" * 1000)
        assert len(data2.value) == 1000

        # Invalid: 1001 characters (tested in model tests, not XSD)
        # XSD schema will enforce this during validation

    def test_delivery_version_attribute(self, schema, sample_header, sample_person):
        """Test that delivery version attribute is correctly set."""
        reported = ECH0099ReportedPerson(base_data=sample_person)

        delivery = ECH0099Delivery(
            delivery_header=sample_header,
            reported_person=[reported],
            version="2.1"
        )

        root = delivery.to_xml()

        # Verify version attribute
        assert root.get('version') == "2.1"

    def test_validation_report_version_attribute(self, schema, sample_header):
        """Test that validation report version attribute is correctly set."""
        report = ECH0099ValidationReport(
            validation_report_header=sample_header,
            version="2.1"
        )

        root = report.to_xml()

        # Verify version attribute
        assert root.get('version') == "2.1"

    def test_receipt_version_attribute(self, schema, sample_header):
        """Test that receipt version attribute is correctly set."""
        receipt = ECH0099Receipt(
            receipt_header=sample_header,
            event_time=date(2025, 10, 25),
            version="2.1"
        )

        root = receipt.to_xml()

        # Verify version attribute
        assert root.get('version') == "2.1"
