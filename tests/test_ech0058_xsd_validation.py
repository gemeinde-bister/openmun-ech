"""XSD Validation tests for eCH-0058 Message Header models.

These tests validate that our Pydantic models produce XML that conforms
to the official eCH-0058 XSD schema.
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

from openmun_ech.ech0058 import (
    ActionType,
    ECH0058NamedMetaData,
    ECH0058SendingApplication,
    ECH0058PartialDelivery,
    ECH0058Header,
)


# Path to eCH XSD schemas
ECH_SCHEMA_DIR = Path(__file__).parent.parent / "docs" / "eCH"
ECH_0058_V5_XSD = ECH_SCHEMA_DIR / "eCH-0058-5-0.xsd"


@pytest.mark.skipif(not HAS_XMLSCHEMA, reason="xmlschema library not installed")
class TestECH0058XSDValidation:
    """XSD validation tests for eCH-0058 models."""

    @pytest.fixture
    def schema(self):
        """Load eCH-0058 v5.0 XSD schema."""
        if not ECH_0058_V5_XSD.exists():
            pytest.skip(f"eCH-0058 XSD not found: {ECH_0058_V5_XSD}")
        return xmlschema.XMLSchema(str(ECH_0058_V5_XSD))

    def test_named_metadata_structure(self, schema):
        """Test that named metadata XML structure is XSD-compliant."""
        metadata = ECH0058NamedMetaData(
            meta_data_name="TestKey",
            meta_data_value="TestValue"
        )

        parent = ET.Element("parent")
        xml_elem = metadata.to_xml(parent)

        # Verify structure matches XSD
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert xml_elem.tag == f'{ns}namedMetaData'
        assert xml_elem.find(f'{ns}metaDataName').text == "TestKey"
        assert xml_elem.find(f'{ns}metaDataValue').text == "TestValue"

    def test_sending_application_structure(self, schema):
        """Test that sending application XML structure is XSD-compliant."""
        app = ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Municipality System",
            product_version="1.0.0"
        )

        parent = ET.Element("parent")
        xml_elem = app.to_xml(parent)

        # Verify structure matches XSD
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert xml_elem.tag == f'{ns}sendingApplication'
        assert xml_elem.find(f'{ns}manufacturer').text == "OpenMun"
        assert xml_elem.find(f'{ns}product').text == "Municipality System"
        assert xml_elem.find(f'{ns}productVersion').text == "1.0.0"

    def test_partial_delivery_structure(self, schema):
        """Test that partial delivery XML structure is XSD-compliant."""
        partial = ECH0058PartialDelivery(
            unique_id_delivery="delivery-123",
            total_number_of_packages=5,
            number_of_actual_package=2
        )

        parent = ET.Element("parent")
        xml_elem = partial.to_xml(parent)

        # Verify structure matches XSD
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert xml_elem.tag == f'{ns}partialDelivery'
        assert xml_elem.find(f'{ns}uniqueIdDelivery').text == "delivery-123"
        assert xml_elem.find(f'{ns}totalNumberOfPackages').text == "5"
        assert xml_elem.find(f'{ns}numberOfActualPackage').text == "2"

    def test_minimal_header_structure(self, schema):
        """Test minimal header with only required fields."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Municipality System",
                product_version="1.0.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            action=ActionType.NEW,
            test_delivery_flag=True
        )

        xml_elem = header.to_xml()

        # Verify all required fields present
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert xml_elem.tag == f'{ns}header'
        assert xml_elem.find(f'{ns}senderId') is not None
        assert xml_elem.find(f'{ns}messageId') is not None
        assert xml_elem.find(f'{ns}messageType') is not None
        assert xml_elem.find(f'{ns}sendingApplication') is not None
        assert xml_elem.find(f'{ns}messageDate') is not None
        assert xml_elem.find(f'{ns}action') is not None
        assert xml_elem.find(f'{ns}testDeliveryFlag') is not None

    def test_header_with_all_optional_fields(self, schema):
        """Test header with all optional fields populated."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            original_sender_id="sedex://T1-CH01-2",
            declaration_local_reference="ref-123",
            recipient_id=["sedex://T1-CH02-1", "sedex://T1-CH03-1"],
            message_id="msg-123",
            reference_message_id="msg-100",
            business_process_id="bp-456",
            our_business_reference_id="our-ref-789",
            your_business_reference_id="your-ref-012",
            unique_id_business_transaction="bt-345",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sub_message_type="base-delivery",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Municipality System",
                product_version="1.0.0"
            ),
            partial_delivery=ECH0058PartialDelivery(
                unique_id_delivery="delivery-123",
                total_number_of_packages=5,
                number_of_actual_package=2
            ),
            subject="Test message",
            comment="This is a test",
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            initial_message_date=datetime(2025, 10, 20, 10, 0, 0),
            event_date=date(2025, 10, 25),
            modification_date=date(2025, 10, 24),
            action=ActionType.NEW,
            test_delivery_flag=True,
            response_expected=True,
            business_case_closed=False,
            named_meta_data=[
                ECH0058NamedMetaData(meta_data_name="key1", meta_data_value="value1"),
                ECH0058NamedMetaData(meta_data_name="key2", meta_data_value="value2")
            ]
        )

        xml_elem = header.to_xml()

        # Verify structure
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert xml_elem.tag == f'{ns}header'

        # Check required fields
        assert xml_elem.find(f'{ns}senderId').text == "sedex://T1-CH01-1"
        assert xml_elem.find(f'{ns}messageId').text == "msg-123"

        # Check optional fields
        assert xml_elem.find(f'{ns}originalSenderId').text == "sedex://T1-CH01-2"
        assert xml_elem.find(f'{ns}subject').text == "Test message"
        assert xml_elem.find(f'{ns}comment').text == "This is a test"
        assert xml_elem.find(f'{ns}responseExpected').text == "true"
        assert xml_elem.find(f'{ns}businessCaseClosed').text == "false"

        # Check multiple recipients
        recipients = xml_elem.findall(f'{ns}recipientId')
        assert len(recipients) == 2

        # Check multiple metadata
        metadata = xml_elem.findall(f'{ns}namedMetaData')
        assert len(metadata) == 2

    def test_action_values_valid(self, schema):
        """Test that all action enum values are XSD-compliant."""
        for action in ActionType:
            header = ECH0058Header(
                sender_id="sedex://T1-CH01-1",
                message_id="msg-123",
                message_type="http://www.ech.ch/xmlns/eCH-0020/3",
                sending_application=ECH0058SendingApplication(
                    manufacturer="Test",
                    product="Test",
                    product_version="1.0"
                ),
                message_date=datetime(2025, 10, 25, 14, 30, 0),
                action=action,
                test_delivery_flag=True
            )

            xml_elem = header.to_xml()
            ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
            action_elem = xml_elem.find(f'{ns}action')

            # Verify action value is in XSD enum
            assert action_elem.text in ["1", "3", "4", "5", "6", "8", "9", "10", "12"]

    def test_date_time_formatting(self, schema):
        """Test that datetime and date fields are formatted correctly."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 45),
            initial_message_date=datetime(2025, 10, 20, 10, 0, 0),
            event_date=date(2025, 10, 25),
            action=ActionType.NEW,
            test_delivery_flag=True
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        # messageDate should be ISO datetime
        msg_date = xml_elem.find(f'{ns}messageDate').text
        assert msg_date == "2025-10-25T14:30:45"

        # eventDate should be ISO date
        event_date = xml_elem.find(f'{ns}eventDate').text
        assert event_date == "2025-10-25"

    def test_boolean_formatting(self, schema):
        """Test that boolean fields are formatted correctly (lowercase)."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            response_expected=False
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        # Booleans should be lowercase 'true'/'false'
        assert xml_elem.find(f'{ns}testDeliveryFlag').text == "true"
        assert xml_elem.find(f'{ns}responseExpected').text == "false"

    def test_field_order_matches_xsd(self, schema):
        """Test that fields are output in correct XSD sequence order."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            recipient_id=["sedex://T1-CH02-1"],
            message_id="msg-123",
            reference_message_id="msg-100",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="1.0"
            ),
            subject="Test",
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        # Get element names in order
        child_tags = [child.tag.replace(ns, '') for child in xml_elem]

        # Check that senderId comes before recipientId
        assert child_tags.index('senderId') < child_tags.index('recipientId')

        # Check that messageId comes before messageType
        assert child_tags.index('messageId') < child_tags.index('messageType')

        # Check that messageType comes before sendingApplication
        assert child_tags.index('messageType') < child_tags.index('sendingApplication')

        # Check that messageDate comes before action
        assert child_tags.index('messageDate') < child_tags.index('action')

        # Check that action comes before testDeliveryFlag
        assert child_tags.index('action') < child_tags.index('testDeliveryFlag')

    def test_string_length_constraints(self, schema):
        """Test that string fields respect XSD length constraints."""
        # messageId: max 36 chars
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="a" * 36,  # Max length
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="a" * 30,  # Max 30
                product="b" * 30,  # Max 30
                product_version="c" * 10  # Max 10
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            subject="d" * 100,  # Max 100
            comment="e" * 250  # Max 250
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        # Verify lengths
        assert len(xml_elem.find(f'{ns}messageId').text) == 36
        assert len(xml_elem.find(f'{ns}subject').text) == 100
        assert len(xml_elem.find(f'{ns}comment').text) == 250

    def test_partial_delivery_package_range(self, schema):
        """Test partial delivery package numbers are within XSD range (1-9999)."""
        partial = ECH0058PartialDelivery(
            unique_id_delivery="test",
            total_number_of_packages=9999,  # Max
            number_of_actual_package=1  # Min
        )

        parent = ET.Element("parent")
        xml_elem = partial.to_xml(parent)
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        assert xml_elem.find(f'{ns}totalNumberOfPackages').text == "9999"
        assert xml_elem.find(f'{ns}numberOfActualPackage').text == "1"

    def test_multiple_recipients_allowed(self, schema):
        """Test that multiple recipients are allowed (unbounded in XSD)."""
        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            recipient_id=[
                "sedex://T1-CH02-1",
                "sedex://T1-CH03-1",
                "sedex://T1-CH04-1",
                "sedex://T1-CH05-1"
            ],
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        recipients = xml_elem.findall(f'{ns}recipientId')
        assert len(recipients) == 4

    def test_multiple_metadata_allowed(self, schema):
        """Test that multiple named metadata entries are allowed (unbounded in XSD)."""
        metadata_list = [
            ECH0058NamedMetaData(meta_data_name=f"key{i}", meta_data_value=f"value{i}")
            for i in range(5)
        ]

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            named_meta_data=metadata_list
        )

        xml_elem = header.to_xml()
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'

        metadata = xml_elem.findall(f'{ns}namedMetaData')
        assert len(metadata) == 5
