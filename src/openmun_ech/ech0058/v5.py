"""eCH-0058 Message Header v5.0.

Standard: eCH-0058 v5.0 (sedex message header)
Version stability: Used in eCH-0020 v3.0/v5.0 and other eCH standards

This component provides message header structures for sedex messaging including:
- Message identification (senderId, recipientId, messageId)
- Message type and action
- Sending application information
- Test delivery flag
- Business references and dates
- Partial delivery support
- Named metadata

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, model_validator

# Import enums from this package
from .enums import ActionType


# ============================================================================
# xs:anyType Support - Arbitrary XML Content
# ============================================================================

class AnyXMLContent(BaseModel):
    """Wrapper for xs:anyType - arbitrary XML content.

    This class handles XSD's anyType by storing raw XML elements.
    Used for attachment and extension fields that can contain any well-formed XML.

    Note: We cannot validate the structure as xs:anyType accepts any XML.
    We store and reproduce it faithfully.
    """

    # Store XML as string for Pydantic compatibility
    xml_content: str = Field(
        ...,
        description="Raw XML content as string"
    )

    @classmethod
    def from_element(cls, elem: ET.Element) -> 'AnyXMLContent':
        """Create from an XML element.

        Args:
            elem: XML Element (any structure)

        Returns:
            AnyXMLContent instance
        """
        # Serialize element to string (without XML declaration)
        xml_str = ET.tostring(elem, encoding='unicode')
        return cls(xml_content=xml_str)

    def to_element(self) -> ET.Element:
        """Convert back to XML element.

        Returns:
            Parsed XML Element

        Raises:
            ET.ParseError: If XML is malformed
        """
        return ET.fromstring(self.xml_content)

    def to_xml(self, parent: ET.Element) -> ET.Element:
        """Append this arbitrary XML content to parent.

        Args:
            parent: Parent element to append to

        Returns:
            The appended element
        """
        elem = self.to_element()
        parent.append(elem)
        return elem


# ============================================================================
# Named Metadata
# ============================================================================

class ECH0058NamedMetaData(BaseModel):
    """eCH-0058 Named metadata.

    Key-value pair for custom metadata.

    XML Schema: eCH-0058 namedMetaDataType
    """

    meta_data_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Metadata name (1-20 characters)"
    )
    meta_data_value: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Metadata value (1-50 characters)"
    )

    def to_xml(self, parent: ET.Element,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        elem = ET.SubElement(parent, f'{{{namespace}}}namedMetaData')

        # Metadata name (required)
        name_elem = ET.SubElement(elem, f'{{{namespace}}}metaDataName')
        name_elem.text = self.meta_data_name

        # Metadata value (required)
        value_elem = ET.SubElement(elem, f'{{{namespace}}}metaDataValue')
        value_elem.text = self.meta_data_value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> 'ECH0058NamedMetaData':
        """Import from XML element.

        Args:
            elem: XML element (namedMetaData)
            namespace: XML namespace URI

        Returns:
            Parsed metadata object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0058': namespace}

        name_elem = elem.find('eCH-0058:metaDataName', ns)
        if name_elem is None or not name_elem.text:
            raise ValueError("Missing required field: metaDataName")

        value_elem = elem.find('eCH-0058:metaDataValue', ns)
        if value_elem is None or not value_elem.text:
            raise ValueError("Missing required field: metaDataValue")

        return cls(
            meta_data_name=name_elem.text.strip(),
            meta_data_value=value_elem.text.strip()
        )


# ============================================================================
# Sending Application
# ============================================================================

class ECH0058SendingApplication(BaseModel):
    """eCH-0058 Sending application.

    Information about the software that generated this message.

    XML Schema: eCH-0058 sendingApplicationType
    """

    manufacturer: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Software manufacturer name (1-30 characters)"
    )
    product: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Product name (1-30 characters)"
    )
    product_version: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Product version (1-10 characters)"
    )

    def to_xml(self, parent: ET.Element,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        elem = ET.SubElement(parent, f'{{{namespace}}}sendingApplication')

        # Manufacturer (required)
        manuf_elem = ET.SubElement(elem, f'{{{namespace}}}manufacturer')
        manuf_elem.text = self.manufacturer

        # Product (required)
        product_elem = ET.SubElement(elem, f'{{{namespace}}}product')
        product_elem.text = self.product

        # Product version (required)
        version_elem = ET.SubElement(elem, f'{{{namespace}}}productVersion')
        version_elem.text = self.product_version

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> 'ECH0058SendingApplication':
        """Import from XML element.

        Args:
            elem: XML element (sendingApplication)
            namespace: XML namespace URI

        Returns:
            Parsed sending application object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0058': namespace}

        manuf_elem = elem.find('eCH-0058:manufacturer', ns)
        if manuf_elem is None or not manuf_elem.text:
            raise ValueError("Missing required field: manufacturer")

        product_elem = elem.find('eCH-0058:product', ns)
        if product_elem is None or not product_elem.text:
            raise ValueError("Missing required field: product")

        version_elem = elem.find('eCH-0058:productVersion', ns)
        if version_elem is None or not version_elem.text:
            raise ValueError("Missing required field: productVersion")

        return cls(
            manufacturer=manuf_elem.text.strip(),
            product=product_elem.text.strip(),
            product_version=version_elem.text.strip()
        )


# ============================================================================
# Partial Delivery
# ============================================================================

class ECH0058PartialDelivery(BaseModel):
    """eCH-0058 Partial delivery.

    Information for multi-part message deliveries.

    XML Schema: eCH-0058 partialDeliveryType
    """

    unique_id_delivery: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique delivery identifier (1-50 characters)"
    )
    total_number_of_packages: int = Field(
        ...,
        ge=1,
        le=9999,
        description="Total number of packages (1-9999)"
    )
    number_of_actual_package: int = Field(
        ...,
        ge=1,
        le=9999,
        description="Number of this package (1-9999)"
    )

    @field_validator('number_of_actual_package')
    @classmethod
    def validate_package_number(cls, v: int, info) -> int:
        """Validate package number is within total."""
        # Note: info.data may not have total_number_of_packages yet during validation
        # This will be validated at runtime
        return v

    def to_xml(self, parent: ET.Element,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        elem = ET.SubElement(parent, f'{{{namespace}}}partialDelivery')

        # Unique ID (required)
        uid_elem = ET.SubElement(elem, f'{{{namespace}}}uniqueIdDelivery')
        uid_elem.text = self.unique_id_delivery

        # Total number (required)
        total_elem = ET.SubElement(elem, f'{{{namespace}}}totalNumberOfPackages')
        total_elem.text = str(self.total_number_of_packages)

        # Current number (required)
        current_elem = ET.SubElement(elem, f'{{{namespace}}}numberOfActualPackage')
        current_elem.text = str(self.number_of_actual_package)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> 'ECH0058PartialDelivery':
        """Import from XML element.

        Args:
            elem: XML element (partialDelivery)
            namespace: XML namespace URI

        Returns:
            Parsed partial delivery object

        Raises:
            ValueError: If required fields missing or invalid
        """
        ns = {'eCH-0058': namespace}

        uid_elem = elem.find('eCH-0058:uniqueIdDelivery', ns)
        if uid_elem is None or not uid_elem.text:
            raise ValueError("Missing required field: uniqueIdDelivery")

        total_elem = elem.find('eCH-0058:totalNumberOfPackages', ns)
        if total_elem is None or not total_elem.text:
            raise ValueError("Missing required field: totalNumberOfPackages")

        current_elem = elem.find('eCH-0058:numberOfActualPackage', ns)
        if current_elem is None or not current_elem.text:
            raise ValueError("Missing required field: numberOfActualPackage")

        return cls(
            unique_id_delivery=uid_elem.text.strip(),
            total_number_of_packages=int(total_elem.text.strip()),
            number_of_actual_package=int(current_elem.text.strip())
        )


# ============================================================================
# Message Header
# ============================================================================

class ECH0058Header(BaseModel):
    """eCH-0058 Message header.

    Complete message header for sedex messages. Contains identification,
    routing, business context, and metadata.

    XML Schema: eCH-0058 headerType
    """

    # Required fields
    sender_id: str = Field(
        ...,
        description="Sender participant ID (anyURI)"
    )
    message_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Unique message ID (1-36 characters)"
    )
    message_type: str = Field(
        ...,
        description="Message type URI (anyURI)"
    )
    sending_application: ECH0058SendingApplication = Field(
        ...,
        description="Information about sending application"
    )
    message_date: datetime = Field(
        ...,
        description="Message creation date/time"
    )
    action: ActionType = Field(
        ...,
        description="Action to be performed"
    )
    test_delivery_flag: bool = Field(
        ...,
        description="True if this is a test message"
    )

    # Optional fields
    original_sender_id: Optional[str] = Field(
        None,
        description="Original sender ID if forwarded (anyURI)"
    )
    declaration_local_reference: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Local reference (1-100 characters)"
    )
    recipient_id: Optional[List[str]] = Field(
        None,
        description="Recipient participant IDs (anyURI, 0..n)"
    )
    reference_message_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=36,
        description="Reference to previous message (1-36 characters)"
    )
    business_process_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        description="Business process ID (1-128 characters)"
    )
    our_business_reference_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Our business reference (1-50 characters)"
    )
    your_business_reference_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Your business reference (1-50 characters)"
    )
    unique_id_business_transaction: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Unique business transaction ID (1-50 characters)"
    )
    sub_message_type: Optional[str] = Field(
        None,
        min_length=1,
        max_length=36,
        description="Sub-message type (1-36 characters)"
    )
    partial_delivery: Optional[ECH0058PartialDelivery] = Field(
        None,
        description="Partial delivery information"
    )
    subject: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Message subject (1-100 characters)"
    )
    comment: Optional[str] = Field(
        None,
        min_length=1,
        max_length=250,
        description="Message comment (1-250 characters)"
    )
    initial_message_date: Optional[datetime] = Field(
        None,
        description="Initial message date/time"
    )
    event_date: Optional[date] = Field(
        None,
        description="Event date"
    )
    modification_date: Optional[date] = Field(
        None,
        description="Modification date"
    )
    response_expected: Optional[bool] = Field(
        None,
        description="True if response is expected"
    )
    business_case_closed: Optional[bool] = Field(
        None,
        description="True if business case is closed"
    )
    named_meta_data: Optional[List[ECH0058NamedMetaData]] = Field(
        None,
        description="Named metadata key-value pairs"
    )
    attachment: Optional[List[AnyXMLContent]] = Field(
        None,
        description="Arbitrary XML attachments (xs:anyType, 0..n)"
    )
    extension: Optional[AnyXMLContent] = Field(
        None,
        description="Arbitrary XML extension (xs:anyType)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5',
               skip_wrapper: bool = False) -> ET.Element:
        """Export to XML element.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            skip_wrapper: If True, serialize children directly into parent
                         (used when this type is embedded via XSD extension)

        Returns:
            XML Element
        """
        if skip_wrapper and parent is not None:
            # Type used via XSD extension - serialize children into parent directly
            elem = parent
        elif parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}header')
        else:
            elem = ET.Element(f'{{{namespace}}}header')

        # Required fields
        sender_elem = ET.SubElement(elem, f'{{{namespace}}}senderId')
        sender_elem.text = self.sender_id

        # Optional: originalSenderId
        if self.original_sender_id:
            orig_sender = ET.SubElement(elem, f'{{{namespace}}}originalSenderId')
            orig_sender.text = self.original_sender_id

        # Optional: declarationLocalReference
        if self.declaration_local_reference:
            decl_ref = ET.SubElement(elem, f'{{{namespace}}}declarationLocalReference')
            decl_ref.text = self.declaration_local_reference

        # Optional: recipientId (multiple)
        if self.recipient_id:
            for recipient in self.recipient_id:
                recipient_elem = ET.SubElement(elem, f'{{{namespace}}}recipientId')
                recipient_elem.text = recipient

        # Required: messageId
        msg_id = ET.SubElement(elem, f'{{{namespace}}}messageId')
        msg_id.text = self.message_id

        # Optional: referenceMessageId
        if self.reference_message_id:
            ref_msg = ET.SubElement(elem, f'{{{namespace}}}referenceMessageId')
            ref_msg.text = self.reference_message_id

        # Optional: businessProcessId
        if self.business_process_id:
            bp_id = ET.SubElement(elem, f'{{{namespace}}}businessProcessId')
            bp_id.text = self.business_process_id

        # Optional: ourBusinessReferenceId
        if self.our_business_reference_id:
            our_ref = ET.SubElement(elem, f'{{{namespace}}}ourBusinessReferenceId')
            our_ref.text = self.our_business_reference_id

        # Optional: yourBusinessReferenceId
        if self.your_business_reference_id:
            your_ref = ET.SubElement(elem, f'{{{namespace}}}yourBusinessReferenceId')
            your_ref.text = self.your_business_reference_id

        # Optional: uniqueIdBusinessTransaction
        if self.unique_id_business_transaction:
            uid_bt = ET.SubElement(elem, f'{{{namespace}}}uniqueIdBusinessTransaction')
            uid_bt.text = self.unique_id_business_transaction

        # Required: messageType
        msg_type = ET.SubElement(elem, f'{{{namespace}}}messageType')
        msg_type.text = self.message_type

        # Optional: subMessageType
        if self.sub_message_type:
            sub_type = ET.SubElement(elem, f'{{{namespace}}}subMessageType')
            sub_type.text = self.sub_message_type

        # Required: sendingApplication
        self.sending_application.to_xml(elem, namespace)

        # Optional: partialDelivery
        if self.partial_delivery:
            self.partial_delivery.to_xml(elem, namespace)

        # Optional: subject
        if self.subject:
            subject_elem = ET.SubElement(elem, f'{{{namespace}}}subject')
            subject_elem.text = self.subject

        # Optional: comment
        if self.comment:
            comment_elem = ET.SubElement(elem, f'{{{namespace}}}comment')
            comment_elem.text = self.comment

        # Required: messageDate
        msg_date = ET.SubElement(elem, f'{{{namespace}}}messageDate')
        msg_date.text = self.message_date.isoformat()

        # Optional: initialMessageDate
        if self.initial_message_date:
            init_date = ET.SubElement(elem, f'{{{namespace}}}initialMessageDate')
            init_date.text = self.initial_message_date.isoformat()

        # Optional: eventDate
        if self.event_date:
            event_elem = ET.SubElement(elem, f'{{{namespace}}}eventDate')
            event_elem.text = self.event_date.isoformat()

        # Optional: modificationDate
        if self.modification_date:
            mod_date = ET.SubElement(elem, f'{{{namespace}}}modificationDate')
            mod_date.text = self.modification_date.isoformat()

        # Required: action
        action_elem = ET.SubElement(elem, f'{{{namespace}}}action')
        action_elem.text = self.action.value

        # Optional: attachment (multiple, xs:anyType)
        if self.attachment:
            for attach in self.attachment:
                # xs:anyType - create eCH-0058 wrapper element, append arbitrary XML as child
                attach_wrapper = ET.SubElement(elem, f'{{{namespace}}}attachment')
                attach_content = attach.to_element()
                attach_wrapper.append(attach_content)

        # Required: testDeliveryFlag
        test_flag = ET.SubElement(elem, f'{{{namespace}}}testDeliveryFlag')
        test_flag.text = 'true' if self.test_delivery_flag else 'false'

        # Optional: responseExpected
        if self.response_expected is not None:
            resp_exp = ET.SubElement(elem, f'{{{namespace}}}responseExpected')
            resp_exp.text = 'true' if self.response_expected else 'false'

        # Optional: businessCaseClosed
        if self.business_case_closed is not None:
            bcc = ET.SubElement(elem, f'{{{namespace}}}businessCaseClosed')
            bcc.text = 'true' if self.business_case_closed else 'false'

        # Optional: namedMetaData (multiple)
        if self.named_meta_data:
            for metadata in self.named_meta_data:
                metadata.to_xml(elem, namespace)

        # Optional: extension (xs:anyType)
        if self.extension:
            # xs:anyType - create eCH-0058 wrapper element, append arbitrary XML as child
            ext_wrapper = ET.SubElement(elem, f'{{{namespace}}}extension')
            ext_content = self.extension.to_element()
            ext_wrapper.append(ext_content)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0058/5') -> 'ECH0058Header':
        """Import from XML element.

        Args:
            elem: XML element (header)
            namespace: XML namespace URI

        Returns:
            Parsed header object

        Raises:
            ValueError: If required fields missing or invalid
        """
        ns = {'eCH-0058': namespace}

        # Required fields
        sender_elem = elem.find('eCH-0058:senderId', ns)
        if sender_elem is None or not sender_elem.text:
            raise ValueError("Missing required field: senderId")

        msg_id_elem = elem.find('eCH-0058:messageId', ns)
        if msg_id_elem is None or not msg_id_elem.text:
            raise ValueError("Missing required field: messageId")

        msg_type_elem = elem.find('eCH-0058:messageType', ns)
        if msg_type_elem is None or not msg_type_elem.text:
            raise ValueError("Missing required field: messageType")

        send_app_elem = elem.find('eCH-0058:sendingApplication', ns)
        if send_app_elem is None:
            raise ValueError("Missing required field: sendingApplication")

        msg_date_elem = elem.find('eCH-0058:messageDate', ns)
        if msg_date_elem is None or not msg_date_elem.text:
            raise ValueError("Missing required field: messageDate")

        action_elem = elem.find('eCH-0058:action', ns)
        if action_elem is None or not action_elem.text:
            raise ValueError("Missing required field: action")

        test_flag_elem = elem.find('eCH-0058:testDeliveryFlag', ns)
        if test_flag_elem is None or not test_flag_elem.text:
            raise ValueError("Missing required field: testDeliveryFlag")

        # Parse required fields
        sending_app = ECH0058SendingApplication.from_xml(send_app_elem, namespace)
        message_date = datetime.fromisoformat(msg_date_elem.text.strip())
        action = ActionType(action_elem.text.strip())
        test_flag = test_flag_elem.text.strip().lower() == 'true'

        # Optional fields
        orig_sender_elem = elem.find('eCH-0058:originalSenderId', ns)
        original_sender_id = orig_sender_elem.text.strip() if orig_sender_elem is not None and orig_sender_elem.text else None

        decl_ref_elem = elem.find('eCH-0058:declarationLocalReference', ns)
        declaration_local_reference = decl_ref_elem.text.strip() if decl_ref_elem is not None and decl_ref_elem.text else None

        # recipientId (multiple)
        recipient_elems = elem.findall('eCH-0058:recipientId', ns)
        recipient_id = [r.text.strip() for r in recipient_elems if r.text] if recipient_elems else None

        ref_msg_elem = elem.find('eCH-0058:referenceMessageId', ns)
        reference_message_id = ref_msg_elem.text.strip() if ref_msg_elem is not None and ref_msg_elem.text else None

        bp_id_elem = elem.find('eCH-0058:businessProcessId', ns)
        business_process_id = bp_id_elem.text.strip() if bp_id_elem is not None and bp_id_elem.text else None

        our_ref_elem = elem.find('eCH-0058:ourBusinessReferenceId', ns)
        our_business_reference_id = our_ref_elem.text.strip() if our_ref_elem is not None and our_ref_elem.text else None

        your_ref_elem = elem.find('eCH-0058:yourBusinessReferenceId', ns)
        your_business_reference_id = your_ref_elem.text.strip() if your_ref_elem is not None and your_ref_elem.text else None

        uid_bt_elem = elem.find('eCH-0058:uniqueIdBusinessTransaction', ns)
        unique_id_business_transaction = uid_bt_elem.text.strip() if uid_bt_elem is not None and uid_bt_elem.text else None

        sub_type_elem = elem.find('eCH-0058:subMessageType', ns)
        sub_message_type = sub_type_elem.text.strip() if sub_type_elem is not None and sub_type_elem.text else None

        # partialDelivery
        partial_elem = elem.find('eCH-0058:partialDelivery', ns)
        partial_delivery = ECH0058PartialDelivery.from_xml(partial_elem, namespace) if partial_elem is not None else None

        subject_elem = elem.find('eCH-0058:subject', ns)
        subject = subject_elem.text.strip() if subject_elem is not None and subject_elem.text else None

        comment_elem = elem.find('eCH-0058:comment', ns)
        comment = comment_elem.text.strip() if comment_elem is not None and comment_elem.text else None

        init_date_elem = elem.find('eCH-0058:initialMessageDate', ns)
        initial_message_date = datetime.fromisoformat(init_date_elem.text.strip()) if init_date_elem is not None and init_date_elem.text else None

        event_date_elem = elem.find('eCH-0058:eventDate', ns)
        event_date = date.fromisoformat(event_date_elem.text.strip()) if event_date_elem is not None and event_date_elem.text else None

        mod_date_elem = elem.find('eCH-0058:modificationDate', ns)
        modification_date = date.fromisoformat(mod_date_elem.text.strip()) if mod_date_elem is not None and mod_date_elem.text else None

        resp_exp_elem = elem.find('eCH-0058:responseExpected', ns)
        response_expected = resp_exp_elem.text.strip().lower() == 'true' if resp_exp_elem is not None and resp_exp_elem.text else None

        bcc_elem = elem.find('eCH-0058:businessCaseClosed', ns)
        business_case_closed = bcc_elem.text.strip().lower() == 'true' if bcc_elem is not None and bcc_elem.text else None

        # namedMetaData (multiple)
        metadata_elems = elem.findall('eCH-0058:namedMetaData', ns)
        named_meta_data = [ECH0058NamedMetaData.from_xml(m, namespace) for m in metadata_elems] if metadata_elems else None

        # attachment (multiple, xs:anyType)
        # Note: The element name is "attachment" but content is arbitrary XML
        attachment_elems = elem.findall('eCH-0058:attachment', ns)
        attachment = None
        if attachment_elems:
            # Each attachment element is an eCH-0058 wrapper containing arbitrary child
            attachment = []
            for attach_wrapper in attachment_elems:
                # Extract the first child (the actual attachment content)
                if len(attach_wrapper) > 0:
                    attach_content = attach_wrapper[0]
                    attachment.append(AnyXMLContent.from_element(attach_content))

        # extension (xs:anyType)
        extension_elem = elem.find('eCH-0058:extension', ns)
        extension = None
        if extension_elem is not None and len(extension_elem) > 0:
            # Extract the first child (the actual extension content)
            ext_content = extension_elem[0]
            extension = AnyXMLContent.from_element(ext_content)

        return cls(
            sender_id=sender_elem.text.strip(),
            message_id=msg_id_elem.text.strip(),
            message_type=msg_type_elem.text.strip(),
            sending_application=sending_app,
            message_date=message_date,
            action=action,
            test_delivery_flag=test_flag,
            original_sender_id=original_sender_id,
            declaration_local_reference=declaration_local_reference,
            recipient_id=recipient_id,
            reference_message_id=reference_message_id,
            business_process_id=business_process_id,
            our_business_reference_id=our_business_reference_id,
            your_business_reference_id=your_business_reference_id,
            unique_id_business_transaction=unique_id_business_transaction,
            sub_message_type=sub_message_type,
            partial_delivery=partial_delivery,
            subject=subject,
            comment=comment,
            initial_message_date=initial_message_date,
            event_date=event_date,
            modification_date=modification_date,
            response_expected=response_expected,
            business_case_closed=business_case_closed,
            named_meta_data=named_meta_data,
            attachment=attachment,
            extension=extension
        )
