"""eCH-0058 shared code for v4/v5.

Contains classes and helpers shared between eCH-0058 v4 and v5:
- AnyXMLContent: xs:anyType raw XML container
- _HeaderBase: shared field declarations for ECH0058Header
- _header_to_xml / _header_from_xml: shared serialization helpers
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

from openmun_ech.core import NS

from .enums import ActionType


# ============================================================================
# xs:anyType Support - Arbitrary XML Content
# ============================================================================

class AnyXMLContent(BaseModel):
    """Wrapper for xs:anyType - arbitrary XML content.

    Stores raw XML elements as strings for Pydantic compatibility.
    Used for attachment and extension fields that can contain any well-formed XML.
    """

    xml_content: str = Field(
        ...,
        description="Raw XML content as string"
    )

    @classmethod
    def from_element(cls, elem: ET.Element) -> 'AnyXMLContent':
        """Create from an XML element."""
        xml_str = ET.tostring(elem, encoding='unicode')
        return cls(xml_content=xml_str)

    def to_element(self) -> ET.Element:
        """Convert back to XML element."""
        return ET.fromstring(self.xml_content)

    def to_xml(self, parent: ET.Element) -> ET.Element:
        """Append this arbitrary XML content to parent."""
        elem = self.to_element()
        parent.append(elem)
        return elem


# ============================================================================
# Header Base (shared field declarations for v4/v5)
# ============================================================================

class _HeaderBase(BaseModel):
    """Shared field declarations for ECH0058Header v4/v5.

    Contains all fields common to both versions. Version-specific subclasses
    add extra fields (v5: named_meta_data) and provide to_xml()/from_xml().
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
    sending_application: Any = Field(
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
    partial_delivery: Any = Field(
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
    attachment: Optional[List[AnyXMLContent]] = Field(
        None,
        description="Arbitrary XML attachments (xs:anyType, 0..n)"
    )
    extension: Optional[AnyXMLContent] = Field(
        None,
        description="Arbitrary XML extension (xs:anyType)"
    )

    # eCH-0058 v5.1.0 §1.5 Grundsatz 5 [ZWINGEND]:
    # "Alle Zeitangaben in XML Dokumenten (XML Schema Datentypen xs:datetime
    #  und xs:time) müssen Angaben über die Zeitzone enthalten"
    @field_validator('message_date', 'initial_message_date')
    @classmethod
    def _datetime_must_be_timezone_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError(
                f"eCH-0058 §1.5 Grundsatz 5 [ZWINGEND]: datetime fields must include "
                f"timezone info (got naive datetime {v.isoformat()}). "
                f"Use datetime.now(timezone.utc) or pass tzinfo explicitly."
            )
        return v


# ============================================================================
# Shared serialization helpers
# ============================================================================

def _header_to_xml(
    header: _HeaderBase,
    parent: ET.Element | None,
    namespace: str,
    skip_wrapper: bool,
    *,
    named_meta_data: list | None = None,
) -> ET.Element:
    """Serialize header fields to XML. Common between v4 and v5.

    Args:
        header: Header instance to serialize.
        parent: Parent element (None for standalone).
        namespace: eCH-0058 namespace URI.
        skip_wrapper: If True, serialize children into parent directly
                     (XSD extension inheritance pattern).
        named_meta_data: v5 only — list of NamedMetaData models to serialize.
    """
    if skip_wrapper and parent is not None:
        elem = parent
    elif parent is not None:
        elem = ET.SubElement(parent, f'{{{namespace}}}header')
    else:
        elem = ET.Element(f'{{{namespace}}}header')

    ns = namespace

    # Required: senderId
    ET.SubElement(elem, f'{{{ns}}}senderId').text = header.sender_id

    # Optional: originalSenderId
    if header.original_sender_id:
        ET.SubElement(elem, f'{{{ns}}}originalSenderId').text = header.original_sender_id

    # Optional: declarationLocalReference
    if header.declaration_local_reference:
        ET.SubElement(elem, f'{{{ns}}}declarationLocalReference').text = header.declaration_local_reference

    # Optional: recipientId (multiple)
    if header.recipient_id:
        for recipient in header.recipient_id:
            ET.SubElement(elem, f'{{{ns}}}recipientId').text = recipient

    # Required: messageId
    ET.SubElement(elem, f'{{{ns}}}messageId').text = header.message_id

    # Optional: referenceMessageId
    if header.reference_message_id:
        ET.SubElement(elem, f'{{{ns}}}referenceMessageId').text = header.reference_message_id

    # Optional: businessProcessId
    if header.business_process_id:
        ET.SubElement(elem, f'{{{ns}}}businessProcessId').text = header.business_process_id

    # Optional: ourBusinessReferenceId
    if header.our_business_reference_id:
        ET.SubElement(elem, f'{{{ns}}}ourBusinessReferenceId').text = header.our_business_reference_id

    # Optional: yourBusinessReferenceId
    if header.your_business_reference_id:
        ET.SubElement(elem, f'{{{ns}}}yourBusinessReferenceId').text = header.your_business_reference_id

    # Optional: uniqueIdBusinessTransaction
    if header.unique_id_business_transaction:
        ET.SubElement(elem, f'{{{ns}}}uniqueIdBusinessTransaction').text = header.unique_id_business_transaction

    # Required: messageType
    ET.SubElement(elem, f'{{{ns}}}messageType').text = header.message_type

    # Optional: subMessageType
    if header.sub_message_type:
        ET.SubElement(elem, f'{{{ns}}}subMessageType').text = header.sub_message_type

    # Required: sendingApplication (ECHModel — delegates to its to_xml)
    header.sending_application.to_xml(parent=elem, namespace=ns)

    # Optional: partialDelivery (ECHModel — delegates to its to_xml)
    if header.partial_delivery:
        header.partial_delivery.to_xml(parent=elem, namespace=ns)

    # Optional: subject
    if header.subject:
        ET.SubElement(elem, f'{{{ns}}}subject').text = header.subject

    # Optional: comment
    if header.comment:
        ET.SubElement(elem, f'{{{ns}}}comment').text = header.comment

    # Required: messageDate (datetime)
    ET.SubElement(elem, f'{{{ns}}}messageDate').text = header.message_date.isoformat()

    # Optional: initialMessageDate (datetime)
    if header.initial_message_date:
        ET.SubElement(elem, f'{{{ns}}}initialMessageDate').text = header.initial_message_date.isoformat()

    # Optional: eventDate (date)
    if header.event_date:
        ET.SubElement(elem, f'{{{ns}}}eventDate').text = header.event_date.isoformat()

    # Optional: modificationDate (date)
    if header.modification_date:
        ET.SubElement(elem, f'{{{ns}}}modificationDate').text = header.modification_date.isoformat()

    # Required: action (enum)
    ET.SubElement(elem, f'{{{ns}}}action').text = header.action.value

    # Optional: attachment (multiple, xs:anyType)
    if header.attachment:
        for attach in header.attachment:
            attach_wrapper = ET.SubElement(elem, f'{{{ns}}}attachment')
            attach_wrapper.append(attach.to_element())

    # Required: testDeliveryFlag
    ET.SubElement(elem, f'{{{ns}}}testDeliveryFlag').text = 'true' if header.test_delivery_flag else 'false'

    # Optional: responseExpected
    if header.response_expected is not None:
        ET.SubElement(elem, f'{{{ns}}}responseExpected').text = 'true' if header.response_expected else 'false'

    # Optional: businessCaseClosed
    if header.business_case_closed is not None:
        ET.SubElement(elem, f'{{{ns}}}businessCaseClosed').text = 'true' if header.business_case_closed else 'false'

    # v5 only: namedMetaData (multiple, between businessCaseClosed and extension)
    if named_meta_data:
        for metadata in named_meta_data:
            metadata.to_xml(parent=elem, namespace=ns)

    # Optional: extension (xs:anyType) — always last
    if header.extension:
        ext_wrapper = ET.SubElement(elem, f'{{{ns}}}extension')
        ext_wrapper.append(header.extension.to_element())

    return elem


def _header_from_xml(
    header_cls: type,
    elem: ET.Element,
    namespace: str,
    *,
    sending_app_cls: type,
    partial_delivery_cls: type,
    named_meta_data_cls: type | None = None,
) -> '_HeaderBase':
    """Deserialize header fields from XML. Common between v4 and v5.

    Args:
        header_cls: The concrete Header class to instantiate (v4 or v5).
        elem: XML element to parse.
        namespace: eCH-0058 namespace URI.
        sending_app_cls: Version-specific SendingApplication class.
        partial_delivery_cls: Version-specific PartialDelivery class.
        named_meta_data_cls: v5 only — NamedMetaData class (None for v4).
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
    sending_app = sending_app_cls.from_xml(send_app_elem, namespace=namespace)
    message_date = datetime.fromisoformat(msg_date_elem.text.strip())
    action = ActionType(action_elem.text.strip())
    test_flag = test_flag_elem.text.strip().lower() == 'true'

    # Optional string fields
    orig_sender_elem = elem.find('eCH-0058:originalSenderId', ns)
    original_sender_id = orig_sender_elem.text.strip() if orig_sender_elem is not None and orig_sender_elem.text else None

    decl_ref_elem = elem.find('eCH-0058:declarationLocalReference', ns)
    declaration_local_reference = decl_ref_elem.text.strip() if decl_ref_elem is not None and decl_ref_elem.text else None

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

    # Optional nested models
    partial_elem = elem.find('eCH-0058:partialDelivery', ns)
    partial_delivery = partial_delivery_cls.from_xml(partial_elem, namespace=namespace) if partial_elem is not None else None

    subject_elem = elem.find('eCH-0058:subject', ns)
    subject = subject_elem.text.strip() if subject_elem is not None and subject_elem.text else None

    comment_elem = elem.find('eCH-0058:comment', ns)
    comment = comment_elem.text.strip() if comment_elem is not None and comment_elem.text else None

    # Optional date/datetime fields
    init_date_elem = elem.find('eCH-0058:initialMessageDate', ns)
    initial_message_date = datetime.fromisoformat(init_date_elem.text.strip()) if init_date_elem is not None and init_date_elem.text else None

    event_date_elem = elem.find('eCH-0058:eventDate', ns)
    event_date = date.fromisoformat(event_date_elem.text.strip()) if event_date_elem is not None and event_date_elem.text else None

    mod_date_elem = elem.find('eCH-0058:modificationDate', ns)
    modification_date = date.fromisoformat(mod_date_elem.text.strip()) if mod_date_elem is not None and mod_date_elem.text else None

    # Optional boolean fields
    resp_exp_elem = elem.find('eCH-0058:responseExpected', ns)
    response_expected = resp_exp_elem.text.strip().lower() == 'true' if resp_exp_elem is not None and resp_exp_elem.text else None

    bcc_elem = elem.find('eCH-0058:businessCaseClosed', ns)
    business_case_closed = bcc_elem.text.strip().lower() == 'true' if bcc_elem is not None and bcc_elem.text else None

    # Optional: attachment (multiple, xs:anyType)
    attachment_elems = elem.findall('eCH-0058:attachment', ns)
    attachment = None
    if attachment_elems:
        attachment = []
        for attach_wrapper in attachment_elems:
            if len(attach_wrapper) > 0:
                attachment.append(AnyXMLContent.from_element(attach_wrapper[0]))

    # Optional: extension (xs:anyType)
    extension_elem = elem.find('eCH-0058:extension', ns)
    extension = None
    if extension_elem is not None and len(extension_elem) > 0:
        extension = AnyXMLContent.from_element(extension_elem[0])

    # Build kwargs
    kwargs: dict[str, Any] = dict(
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
        attachment=attachment,
        extension=extension,
    )

    # v5 only: namedMetaData
    if named_meta_data_cls is not None:
        metadata_elems = elem.findall('eCH-0058:namedMetaData', ns)
        kwargs['named_meta_data'] = (
            [named_meta_data_cls.from_xml(m, namespace=namespace) for m in metadata_elems]
            if metadata_elems else None
        )

    return header_cls(**kwargs)
