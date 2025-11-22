"""Tests for eCH-0058 Message Header Pydantic models."""

import xml.etree.ElementTree as ET
import pytest
from datetime import datetime, date
from pydantic import ValidationError

from openmun_ech.ech0058 import (
    AnyXMLContent,
    ActionType,
    ECH0058NamedMetaData,
    ECH0058SendingApplication,
    ECH0058PartialDelivery,
    ECH0058Header,
)


class TestActionType:
    """Test action type enum."""

    def test_valid_actions(self):
        """Test all valid action values."""
        assert ActionType.NEW.value == "1"
        assert ActionType.RECALL.value == "3"
        assert ActionType.CORRECTION.value == "4"
        assert ActionType.REQUEST.value == "5"
        assert ActionType.RESPONSE.value == "6"
        assert ActionType.NEGATIVE_REPORT.value == "8"
        assert ActionType.POSITIVE_REPORT.value == "9"
        assert ActionType.FORWARD.value == "10"
        assert ActionType.REMINDER.value == "12"

    def test_total_count(self):
        """Test we have all 9 action types."""
        assert len(ActionType) == 9


class TestAnyXMLContent:
    """Test xs:anyType support via AnyXMLContent wrapper."""

    def test_create_from_simple_element(self):
        """Test creating AnyXMLContent from a simple XML element."""
        # Create arbitrary XML
        elem = ET.Element("customData")
        elem.text = "test content"

        content = AnyXMLContent.from_element(elem)
        assert content.xml_content is not None
        assert "customData" in content.xml_content
        assert "test content" in content.xml_content

    def test_create_from_complex_element(self):
        """Test creating AnyXMLContent from complex nested XML."""
        # Create nested XML structure
        root = ET.Element("attachment")
        child1 = ET.SubElement(root, "document")
        child1.set("type", "pdf")
        child1.text = "document.pdf"
        child2 = ET.SubElement(root, "metadata")
        subchild = ET.SubElement(child2, "author")
        subchild.text = "John Doe"

        content = AnyXMLContent.from_element(root)
        assert "attachment" in content.xml_content
        assert "document" in content.xml_content
        assert "metadata" in content.xml_content
        assert "author" in content.xml_content

    def test_to_element_roundtrip(self):
        """Test XML roundtrip conversion."""
        # Create original element
        original = ET.Element("testElement")
        original.set("attr", "value")
        original.text = "content"

        # Convert to AnyXMLContent and back
        content = AnyXMLContent.from_element(original)
        restored = content.to_element()

        assert restored.tag == "testElement"
        assert restored.get("attr") == "value"
        assert restored.text == "content"

    def test_to_xml_appends_to_parent(self):
        """Test that to_xml() appends element to parent."""
        # Create content
        elem = ET.Element("customElement")
        elem.text = "test"
        content = AnyXMLContent.from_element(elem)

        # Append to parent
        parent = ET.Element("parent")
        content.to_xml(parent)

        # Verify appended
        assert len(parent) == 1
        assert parent[0].tag == "customElement"
        assert parent[0].text == "test"


class TestECH0058NamedMetaData:
    """Test named metadata model."""

    def test_create_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = ECH0058NamedMetaData(
            meta_data_name="TestKey",
            meta_data_value="TestValue"
        )
        assert metadata.meta_data_name == "TestKey"
        assert metadata.meta_data_value == "TestValue"

    def test_validate_name_length(self):
        """Test metadata name length limits."""
        # Too long (21 chars)
        with pytest.raises(ValidationError, match="String should have at most 20 characters"):
            ECH0058NamedMetaData(
                meta_data_name="a" * 21,
                meta_data_value="value"
            )

        # Too short (empty)
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            ECH0058NamedMetaData(
                meta_data_name="",
                meta_data_value="value"
            )

        # Valid max length (20 chars)
        metadata = ECH0058NamedMetaData(
            meta_data_name="a" * 20,
            meta_data_value="value"
        )
        assert len(metadata.meta_data_name) == 20

    def test_validate_value_length(self):
        """Test metadata value length limits."""
        # Too long (51 chars)
        with pytest.raises(ValidationError, match="String should have at most 50 characters"):
            ECH0058NamedMetaData(
                meta_data_name="name",
                meta_data_value="a" * 51
            )

        # Valid max length (50 chars)
        metadata = ECH0058NamedMetaData(
            meta_data_name="name",
            meta_data_value="a" * 50
        )
        assert len(metadata.meta_data_value) == 50

    def test_to_xml(self):
        """Test export to XML."""
        metadata = ECH0058NamedMetaData(
            meta_data_name="TestKey",
            meta_data_value="TestValue"
        )

        parent = ET.Element("parent")
        elem = metadata.to_xml(parent)

        # Check element structure
        assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0058/5}namedMetaData'
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}metaDataName').text == "TestKey"
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}metaDataValue').text == "TestValue"

    def test_from_xml_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0058NamedMetaData(
            meta_data_name="TestKey",
            meta_data_value="TestValue"
        )

        parent = ET.Element("parent")
        xml_elem = original.to_xml(parent)
        parsed = ECH0058NamedMetaData.from_xml(xml_elem)

        assert parsed.meta_data_name == original.meta_data_name
        assert parsed.meta_data_value == original.meta_data_value


class TestECH0058SendingApplication:
    """Test sending application model."""

    def test_create_valid_application(self):
        """Test creating valid sending application."""
        app = ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Municipality System",
            product_version="1.0.0"
        )
        assert app.manufacturer == "OpenMun"
        assert app.product == "Municipality System"
        assert app.product_version == "1.0.0"

    def test_validate_manufacturer_length(self):
        """Test manufacturer length limits."""
        # Too long (31 chars)
        with pytest.raises(ValidationError, match="String should have at most 30 characters"):
            ECH0058SendingApplication(
                manufacturer="a" * 31,
                product="Test",
                product_version="1.0"
            )

        # Valid max length (30 chars)
        app = ECH0058SendingApplication(
            manufacturer="a" * 30,
            product="Test",
            product_version="1.0"
        )
        assert len(app.manufacturer) == 30

    def test_validate_product_length(self):
        """Test product length limits."""
        # Too long (31 chars)
        with pytest.raises(ValidationError, match="String should have at most 30 characters"):
            ECH0058SendingApplication(
                manufacturer="Test",
                product="a" * 31,
                product_version="1.0"
            )

        # Valid max length (30 chars)
        app = ECH0058SendingApplication(
            manufacturer="Test",
            product="a" * 30,
            product_version="1.0"
        )
        assert len(app.product) == 30

    def test_validate_version_length(self):
        """Test version length limits."""
        # Too long (11 chars)
        with pytest.raises(ValidationError, match="String should have at most 10 characters"):
            ECH0058SendingApplication(
                manufacturer="Test",
                product="Test",
                product_version="a" * 11
            )

        # Valid max length (10 chars)
        app = ECH0058SendingApplication(
            manufacturer="Test",
            product="Test",
            product_version="a" * 10
        )
        assert len(app.product_version) == 10

    def test_to_xml(self):
        """Test export to XML."""
        app = ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Municipality System",
            product_version="1.0.0"
        )

        parent = ET.Element("parent")
        elem = app.to_xml(parent)

        # Check element structure
        assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0058/5}sendingApplication'
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}manufacturer').text == "OpenMun"
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}product').text == "Municipality System"
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}productVersion').text == "1.0.0"

    def test_from_xml_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0058SendingApplication(
            manufacturer="OpenMun",
            product="Municipality System",
            product_version="1.0.0"
        )

        parent = ET.Element("parent")
        xml_elem = original.to_xml(parent)
        parsed = ECH0058SendingApplication.from_xml(xml_elem)

        assert parsed.manufacturer == original.manufacturer
        assert parsed.product == original.product
        assert parsed.product_version == original.product_version


class TestECH0058PartialDelivery:
    """Test partial delivery model."""

    def test_create_valid_partial_delivery(self):
        """Test creating valid partial delivery."""
        partial = ECH0058PartialDelivery(
            unique_id_delivery="delivery-123",
            total_number_of_packages=5,
            number_of_actual_package=2
        )
        assert partial.unique_id_delivery == "delivery-123"
        assert partial.total_number_of_packages == 5
        assert partial.number_of_actual_package == 2

    def test_validate_unique_id_length(self):
        """Test unique ID length limits."""
        # Too long (51 chars)
        with pytest.raises(ValidationError, match="String should have at most 50 characters"):
            ECH0058PartialDelivery(
                unique_id_delivery="a" * 51,
                total_number_of_packages=1,
                number_of_actual_package=1
            )

    def test_validate_package_numbers(self):
        """Test package number validation."""
        # Too small (0)
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            ECH0058PartialDelivery(
                unique_id_delivery="test",
                total_number_of_packages=0,
                number_of_actual_package=1
            )

        # Too large (10000)
        with pytest.raises(ValidationError, match="less than or equal to 9999"):
            ECH0058PartialDelivery(
                unique_id_delivery="test",
                total_number_of_packages=10000,
                number_of_actual_package=1
            )

        # Valid range
        partial = ECH0058PartialDelivery(
            unique_id_delivery="test",
            total_number_of_packages=9999,
            number_of_actual_package=9999
        )
        assert partial.total_number_of_packages == 9999

    def test_to_xml(self):
        """Test export to XML."""
        partial = ECH0058PartialDelivery(
            unique_id_delivery="delivery-123",
            total_number_of_packages=5,
            number_of_actual_package=2
        )

        parent = ET.Element("parent")
        elem = partial.to_xml(parent)

        # Check element structure
        assert elem.tag == '{http://www.ech.ch/xmlns/eCH-0058/5}partialDelivery'
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}uniqueIdDelivery').text == "delivery-123"
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}totalNumberOfPackages').text == "5"
        assert elem.find('{http://www.ech.ch/xmlns/eCH-0058/5}numberOfActualPackage').text == "2"

    def test_from_xml_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0058PartialDelivery(
            unique_id_delivery="delivery-123",
            total_number_of_packages=5,
            number_of_actual_package=2
        )

        parent = ET.Element("parent")
        xml_elem = original.to_xml(parent)
        parsed = ECH0058PartialDelivery.from_xml(xml_elem)

        assert parsed.unique_id_delivery == original.unique_id_delivery
        assert parsed.total_number_of_packages == original.total_number_of_packages
        assert parsed.number_of_actual_package == original.number_of_actual_package


class TestECH0058Header:
    """Test message header model."""

    def test_create_minimal_header(self):
        """Test creating header with only required fields."""
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
        assert header.sender_id == "sedex://T1-CH01-1"
        assert header.message_id == "msg-123"
        assert header.test_delivery_flag is True

    def test_create_full_header(self):
        """Test creating header with all fields."""
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
        assert header.sender_id == "sedex://T1-CH01-1"
        assert len(header.recipient_id) == 2
        assert header.response_expected is True
        assert len(header.named_meta_data) == 2

    def test_validate_message_id_length(self):
        """Test message ID length limits."""
        # Too long (37 chars)
        with pytest.raises(ValidationError, match="String should have at most 36 characters"):
            ECH0058Header(
                sender_id="sedex://T1-CH01-1",
                message_id="a" * 37,
                message_type="http://example.com",
                sending_application=ECH0058SendingApplication(
                    manufacturer="Test",
                    product="Test",
                    product_version="1.0"
                ),
                message_date=datetime.now(),
                action=ActionType.NEW,
                test_delivery_flag=True
            )

    def test_to_xml_minimal(self):
        """Test export minimal header to XML."""
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

        elem = header.to_xml()

        # Check element structure
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        assert elem.tag == f'{ns}header'
        assert elem.find(f'{ns}senderId').text == "sedex://T1-CH01-1"
        assert elem.find(f'{ns}messageId').text == "msg-123"
        assert elem.find(f'{ns}messageType').text == "http://www.ech.ch/xmlns/eCH-0020/3"
        assert elem.find(f'{ns}action').text == "1"
        assert elem.find(f'{ns}testDeliveryFlag').text == "true"

    def test_to_xml_with_metadata(self):
        """Test export header with metadata to XML."""
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
            test_delivery_flag=True,
            named_meta_data=[
                ECH0058NamedMetaData(meta_data_name="key1", meta_data_value="value1"),
                ECH0058NamedMetaData(meta_data_name="key2", meta_data_value="value2")
            ]
        )

        elem = header.to_xml()

        # Check metadata
        ns = '{http://www.ech.ch/xmlns/eCH-0058/5}'
        metadata_elems = elem.findall(f'{ns}namedMetaData')
        assert len(metadata_elems) == 2

    def test_from_xml_roundtrip_minimal(self):
        """Test XML roundtrip with minimal header."""
        original = ECH0058Header(
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

        xml_elem = original.to_xml()
        parsed = ECH0058Header.from_xml(xml_elem)

        assert parsed.sender_id == original.sender_id
        assert parsed.message_id == original.message_id
        assert parsed.message_type == original.message_type
        assert parsed.action == original.action
        assert parsed.test_delivery_flag == original.test_delivery_flag

    def test_from_xml_roundtrip_full(self):
        """Test XML roundtrip with full header."""
        original = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            recipient_id=["sedex://T1-CH02-1"],
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Municipality System",
                product_version="1.0.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            action=ActionType.NEW,
            test_delivery_flag=True,
            subject="Test",
            comment="Test comment",
            response_expected=True,
            named_meta_data=[
                ECH0058NamedMetaData(meta_data_name="key1", meta_data_value="value1")
            ]
        )

        xml_elem = original.to_xml()
        parsed = ECH0058Header.from_xml(xml_elem)

        assert parsed.sender_id == original.sender_id
        assert parsed.recipient_id == original.recipient_id
        assert parsed.subject == original.subject
        assert parsed.comment == original.comment
        assert parsed.response_expected == original.response_expected
        assert len(parsed.named_meta_data) == 1
        assert parsed.named_meta_data[0].meta_data_name == "key1"

    def test_header_with_attachment(self):
        """Test header with attachment field (xs:anyType)."""
        # Create attachment XML
        attach_elem = ET.Element("document")
        attach_elem.set("type", "pdf")
        attach_elem.text = "report.pdf"
        attachment = AnyXMLContent.from_element(attach_elem)

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            action=ActionType.NEW,
            test_delivery_flag=True,
            attachment=[attachment]
        )

        assert header.attachment is not None
        assert len(header.attachment) == 1
        assert "document" in header.attachment[0].xml_content

    def test_header_with_multiple_attachments(self):
        """Test header with multiple attachments."""
        # Create two attachments
        attach1 = ET.Element("document")
        attach1.text = "doc1.pdf"
        attach2 = ET.Element("image")
        attach2.text = "image.png"

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            attachment=[
                AnyXMLContent.from_element(attach1),
                AnyXMLContent.from_element(attach2)
            ]
        )

        assert len(header.attachment) == 2

    def test_header_with_extension(self):
        """Test header with extension field (xs:anyType)."""
        # Create extension XML
        ext_elem = ET.Element("customExtension")
        child = ET.SubElement(ext_elem, "field")
        child.text = "value"
        extension = AnyXMLContent.from_element(ext_elem)

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            extension=extension
        )

        assert header.extension is not None
        assert "customExtension" in header.extension.xml_content

    def test_attachment_roundtrip(self):
        """Test attachment field survives XML roundtrip."""
        # Create header with attachment
        attach_elem = ET.Element("attachment")
        attach_elem.set("id", "123")
        data = ET.SubElement(attach_elem, "data")
        data.text = "binary_data_here"

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            action=ActionType.NEW,
            test_delivery_flag=True,
            attachment=[AnyXMLContent.from_element(attach_elem)]
        )

        # Roundtrip
        xml_elem = header.to_xml()
        parsed = ECH0058Header.from_xml(xml_elem)

        # Verify attachment preserved
        assert parsed.attachment is not None
        assert len(parsed.attachment) == 1
        assert "attachment" in parsed.attachment[0].xml_content
        assert "data" in parsed.attachment[0].xml_content

    def test_extension_roundtrip(self):
        """Test extension field survives XML roundtrip."""
        # Create header with extension
        ext_elem = ET.Element("extension")
        ext_elem.set("version", "1.0")
        field = ET.SubElement(ext_elem, "customField")
        field.text = "customValue"

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime(2025, 10, 25, 14, 30, 0),
            action=ActionType.NEW,
            test_delivery_flag=True,
            extension=AnyXMLContent.from_element(ext_elem)
        )

        # Roundtrip
        xml_elem = header.to_xml()
        parsed = ECH0058Header.from_xml(xml_elem)

        # Verify extension preserved
        assert parsed.extension is not None
        assert "extension" in parsed.extension.xml_content
        assert "customField" in parsed.extension.xml_content

    def test_attachment_and_extension_together(self):
        """Test header with both attachment and extension."""
        attach = ET.Element("document")
        attach.text = "file.pdf"
        ext = ET.Element("metadata")
        ext.text = "extra"

        header = ECH0058Header(
            sender_id="sedex://T1-CH01-1",
            message_id="msg-123",
            message_type="http://www.ech.ch/xmlns/eCH-0020/3",
            sending_application=ECH0058SendingApplication(
                manufacturer="OpenMun",
                product="Test",
                product_version="1.0"
            ),
            message_date=datetime.now(),
            action=ActionType.NEW,
            test_delivery_flag=True,
            attachment=[AnyXMLContent.from_element(attach)],
            extension=AnyXMLContent.from_element(ext)
        )

        xml_elem = header.to_xml()
        parsed = ECH0058Header.from_xml(xml_elem)

        assert parsed.attachment is not None
        assert parsed.extension is not None
        assert len(parsed.attachment) == 1
