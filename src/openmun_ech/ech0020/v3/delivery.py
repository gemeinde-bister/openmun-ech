"""eCH-0020 v3.0 — Delivery."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union, Literal
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from openmun_ech.utils.schema_cache import validate_xml_cached
from openmun_ech.core import NS
from openmun_ech.ech0021 import DataLockType
from openmun_ech.ech0058 import ECH0058Header

from .base_delivery import (
    ECH0020EventBaseDelivery,
    ECH0020EventKeyExchange,
    ECH0020EventDataRequest,
)
from .life_events import (
    ECH0020EventAdoption,
    ECH0020EventChildRelationship,
    ECH0020EventNaturalizeForeigner,
    ECH0020EventNaturalizeSwiss,
    ECH0020EventUndoCitizen,
    ECH0020EventUndoSwiss,
    ECH0020EventChangeOrigin,
    ECH0020EventBirth,
    ECH0020EventMarriage,
    ECH0020EventPartnership,
    ECH0020EventSeparation,
    ECH0020EventUndoSeparation,
    ECH0020EventDivorce,
    ECH0020EventUndoMarriage,
    ECH0020EventUndoPartnership,
    ECH0020EventDeath,
    ECH0020EventMissing,
    ECH0020EventUndoMissing,
)
from .correction_events import (
    ECH0020EventMaritalStatusPartner,
    ECH0020EventChangeName,
    ECH0020EventChangeSex,
    ECH0020EventCorrectIdentification,
    ECH0020EventIdentificationConversion,
    ECH0020EventCorrectName,
    ECH0020EventCorrectNationality,
    ECH0020EventCorrectContact,
    ECH0020EventCorrectReligion,
    ECH0020EventCorrectPlaceOfOrigin,
    ECH0020EventCorrectResidencePermit,
    ECH0020EventCorrectMaritalInfo,
    ECH0020EventCorrectBirthInfo,
    ECH0020EventCorrectGuardianRelationship,
    ECH0020EventCorrectParentalRelationship,
    ECH0020EventCorrectReporting,
    ECH0020EventCorrectOccupation,
    ECH0020EventCorrectDeathData,
)
from .move_events import (
    ECH0020EventMoveIn,
    ECH0020EventMove,
    ECH0020EventContact,
    ECH0020EventMoveOut,
    ECH0020EventChangeResidenceType,
)
from .admin_events import (
    ECH0020EventChangeReligion,
    ECH0020EventChangeOccupation,
    ECH0020EventGuardianMeasure,
    ECH0020EventUndoGuardian,
    ECH0020EventChangeGuardian,
    ECH0020EventChangeNationality,
    ECH0020EventEntryResidencePermit,
    ECH0020EventDataLock,
    ECH0020EventPaperLock,
    ECH0020EventCare,
    ECH0020EventCorrectPersonAdditionalData,
    ECH0020EventCorrectPoliticalRightData,
    ECH0020EventCorrectDataLock,
    ECH0020EventCorrectPaperLock,
    ECH0020EventAnnounceDuplicate,
    ECH0020EventDeletedInRegister,
    ECH0020EventChangeArmedForces,
    ECH0020EventChangeCivilDefense,
    ECH0020EventChangeFireService,
    ECH0020EventChangeHealthInsurance,
    ECH0020EventChangeMatrimonialInheritanceArrangement,
)


# ============================================================================
# TYPE: headerType
# ============================================================================

class ECH0020Header(BaseModel):
    """Delivery header per eCH-0020 v3.0.

    Extends eCH-0058 header with optional data lock information.

    XSD: headerType (eCH-0020-3-0.xsd lines 894-904)
    PDF: Event reporting standard
    """

    header: ECH0058Header = Field(
        ...,
        description='Base header per eCH-0058'
    )
    data_lock: Optional[DataLockType] = Field(
        None,
        alias='dataLock',
        description='Data lock type (0=none, 1=address, 2=information)'
    )
    data_lock_valid_from: Optional[date] = Field(
        None,
        alias='dataLockValidFrom',
        description='Date from which the data lock is valid'
    )
    data_lock_valid_till: Optional[date] = Field(
        None,
        alias='dataLockValidTill',
        description='Date until which the data lock is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = NS.ECH0020_V3
        ns_058 = NS.ECH0058_V5

        # Create header element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Embed eCH-0058 header fields directly (extension base)
        # Use skip_wrapper=True to flatten eCH-0058 fields into this element
        self.header.to_xml(parent=elem, namespace=ns_058, skip_wrapper=True)

        # dataLock (optional)
        if self.data_lock is not None:
            data_lock_elem = ET.SubElement(elem, f'{{{ns_020}}}dataLock')
            data_lock_elem.text = self.data_lock.value

        # dataLockValidFrom (optional)
        if self.data_lock_valid_from is not None:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}dataLockValidFrom')
            valid_from_elem.text = self.data_lock_valid_from.isoformat()

        # dataLockValidTill (optional)
        if self.data_lock_valid_till is not None:
            valid_till_elem = ET.SubElement(elem, f'{{{ns_020}}}dataLockValidTill')
            valid_till_elem.text = self.data_lock_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020Header':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_058 = NS.ECH0058_V5

        # Parse eCH-0058 base header (extension base - fields are inline)
        header = ECH0058Header.from_xml(elem)

        # dataLock (optional)
        data_lock = None
        data_lock_elem = elem.find(f'{{{ns_020}}}dataLock')
        if data_lock_elem is not None and data_lock_elem.text:
            data_lock = DataLockType(data_lock_elem.text)

        # dataLockValidFrom (optional)
        data_lock_valid_from = None
        valid_from_elem = elem.find(f'{{{ns_020}}}dataLockValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            data_lock_valid_from = date.fromisoformat(valid_from_elem.text)

        # dataLockValidTill (optional)
        data_lock_valid_till = None
        valid_till_elem = elem.find(f'{{{ns_020}}}dataLockValidTill')
        if valid_till_elem is not None and valid_till_elem.text:
            data_lock_valid_till = date.fromisoformat(valid_till_elem.text)

        return cls(
            header=header,
            data_lock=data_lock,
            data_lock_valid_from=data_lock_valid_from,
            data_lock_valid_till=data_lock_valid_till
        )


# ============================================================================
# TYPE: infoType
# ============================================================================

class ECH0020Info(BaseModel):
    """Information/error message per eCH-0020 v3.0.

    Simple text container for info messages, errors, warnings.

    XSD: infoType (eCH-0020-3-0.xsd lines 996-1016)
    PDF: Event reporting standard
    """

    info_text: str = Field(
        ...,
        alias='infoText',
        min_length=1,
        description='Information text (min length 1)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        # Create info element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # infoText (required)
        info_text_elem = ET.SubElement(elem, f'{{{namespace}}}infoText')
        info_text_elem.text = self.info_text

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020Info':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3

        # infoText (required)
        info_text_elem = elem.find(f'{{{ns_020}}}infoText')
        if info_text_elem is None or not info_text_elem.text:
            raise ValueError("infoType requires infoText")

        return cls(info_text=info_text_elem.text)


# ============================================================================
# TYPE: negativeReportType
# ============================================================================

class ECH0020NegativeReport(BaseModel):
    """Negative report (error/rejection) per eCH-0020 v3.0.

    Reports errors or rejections of event processing.

    XSD: negativeReportType (eCH-0020-3-0.xsd lines 1017-1029)
    PDF: Event reporting standard
    """

    negative_report_info: List['ECH0020Info'] = Field(
        ...,
        alias='negativeReportInfo',
        description='Error/rejection information (unbounded)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        # Create negativeReport element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # negativeReportInfo (required, unbounded)
        for info in self.negative_report_info:
            info.to_xml(elem, namespace, 'negativeReportInfo')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020NegativeReport':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3

        # negativeReportInfo (required, unbounded)
        negative_report_info = []
        for info_elem in elem.findall(f'{{{ns_020}}}negativeReportInfo'):
            negative_report_info.append(ECH0020Info.from_xml(info_elem))

        if not negative_report_info:
            raise ValueError("negativeReportType requires at least one negativeReportInfo")

        return cls(negative_report_info=negative_report_info)


# ============================================================================
# TYPE: positiveReportType
# ============================================================================

class ECH0020PositiveReport(BaseModel):
    """Positive report (acknowledgment) per eCH-0020 v3.0.

    Reports successful processing of events.

    XSD: positiveReportType (eCH-0020-3-0.xsd lines 1030-1042)
    PDF: Event reporting standard
    """

    positive_report_info: List['ECH0020Info'] = Field(
        ...,
        alias='positiveReportInfo',
        description='Success acknowledgment information (unbounded)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        # Create positiveReport element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # positiveReportInfo (required, unbounded)
        for info in self.positive_report_info:
            info.to_xml(elem, namespace, 'positiveReportInfo')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020PositiveReport':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3

        # positiveReportInfo (required, unbounded)
        positive_report_info = []
        for info_elem in elem.findall(f'{{{ns_020}}}positiveReportInfo'):
            positive_report_info.append(ECH0020Info.from_xml(info_elem))

        if not positive_report_info:
            raise ValueError("positiveReportType requires at least one positiveReportInfo")

        return cls(positive_report_info=positive_report_info)


# ============================================================================
# TYPE: deliveryType (MAIN DELIVERY CONTAINER with 71 event types!)
# ============================================================================

# Define all event type aliases for the massive Union
ECH0020EventType = Union[
    List[ECH0020EventBaseDelivery],  # baseDelivery/messages
    List[ECH0020EventKeyExchange],   # keyExchange/messages
    ECH0020EventDataRequest,
    ECH0020EventIdentificationConversion,
    ECH0020EventAnnounceDuplicate,
    ECH0020EventDeletedInRegister,
    ECH0020EventAdoption,
    ECH0020EventChildRelationship,
    ECH0020EventNaturalizeForeigner,
    ECH0020EventNaturalizeSwiss,
    ECH0020EventUndoCitizen,
    ECH0020EventUndoSwiss,
    ECH0020EventChangeOrigin,
    ECH0020EventBirth,
    ECH0020EventMarriage,
    ECH0020EventPartnership,
    ECH0020EventSeparation,
    ECH0020EventUndoSeparation,
    ECH0020EventDivorce,
    ECH0020EventUndoMarriage,
    ECH0020EventUndoPartnership,
    ECH0020EventDeath,
    ECH0020EventMissing,
    ECH0020EventUndoMissing,
    ECH0020EventMaritalStatusPartner,
    ECH0020EventChangeName,
    ECH0020EventChangeSex,
    ECH0020EventMoveIn,
    ECH0020EventMove,
    ECH0020EventContact,
    ECH0020EventMoveOut,
    ECH0020EventChangeResidenceType,
    ECH0020EventChangeReligion,
    ECH0020EventChangeOccupation,
    ECH0020EventGuardianMeasure,
    ECH0020EventUndoGuardian,
    ECH0020EventChangeGuardian,
    ECH0020EventChangeNationality,
    ECH0020EventEntryResidencePermit,
    ECH0020EventDataLock,
    ECH0020EventPaperLock,
    ECH0020EventCare,
    ECH0020EventChangeArmedForces,
    ECH0020EventChangeCivilDefense,
    ECH0020EventChangeFireService,
    ECH0020EventChangeHealthInsurance,
    ECH0020EventChangeMatrimonialInheritanceArrangement,
    ECH0020EventCorrectGuardianRelationship,
    ECH0020EventCorrectParentalRelationship,
    ECH0020EventCorrectReporting,
    ECH0020EventCorrectOccupation,
    ECH0020EventCorrectIdentification,
    ECH0020EventCorrectName,
    ECH0020EventCorrectNationality,
    ECH0020EventCorrectContact,
    ECH0020EventCorrectReligion,
    ECH0020EventCorrectPlaceOfOrigin,
    ECH0020EventCorrectResidencePermit,
    ECH0020EventCorrectMaritalInfo,
    ECH0020EventCorrectBirthInfo,
    ECH0020EventCorrectDeathData,
    ECH0020EventCorrectPersonAdditionalData,
    ECH0020EventCorrectPoliticalRightData,
    ECH0020EventCorrectDataLock,
    ECH0020EventCorrectPaperLock,
]


class ECH0020Delivery(BaseModel):
    """Main delivery container per eCH-0020 v3.0.

    Root element containing header and one of 71 possible event types.

    XSD: deliveryType (eCH-0020-3-0.xsd lines 905-995)
    PDF: Event reporting standard
    """

    delivery_header: 'ECH0020Header' = Field(
        ...,
        alias='deliveryHeader',
        description='Delivery header'
    )
    event: ECH0020EventType = Field(
        ...,
        description='Event data (XSD CHOICE of 71 event types)'
    )
    version: Literal["3.0"] = Field(
        "3.0",
        description='eCH-0020 version (required attribute, fixed to "3.0")'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'delivery'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'delivery')

        Returns:
            XML element with complete delivery data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Set version attribute
        elem.set('version', self.version)

        # 1. deliveryHeader (required)
        self.delivery_header.to_xml(parent=elem, namespace=namespace, element_name='deliveryHeader')

        # 2. event (CHOICE of 71 types)
        # The event is a Union type - serialize based on actual type
        if isinstance(self.event, list):
            # baseDelivery or keyExchange (both use lists)
            if len(self.event) > 0:
                if isinstance(self.event[0], ECH0020EventBaseDelivery):
                    # baseDelivery - each message gets its own messages wrapper
                    base_elem = ET.SubElement(elem, f'{{{namespace}}}baseDelivery')
                    for msg in self.event:
                        # Create a messages wrapper for each person
                        # <messages> has TYPE eventBaseDelivery, so skip wrapper
                        msgs_elem = ET.SubElement(base_elem, f'{{{namespace}}}messages')
                        msg.to_xml(parent=msgs_elem, namespace=namespace, skip_wrapper=True)
                elif isinstance(self.event[0], ECH0020EventKeyExchange):
                    # keyExchange
                    key_elem = ET.SubElement(elem, f'{{{namespace}}}keyExchange')
                    msgs_elem = ET.SubElement(key_elem, f'{{{namespace}}}messages')
                    for msg in self.event:
                        msg.to_xml(parent=msgs_elem, namespace=namespace)
        else:
            # Single event - call its to_xml method
            # Event name is derived from class name
            event_type = type(self.event).__name__
            if event_type.startswith('ECH0020Event'):
                # Convert ECH0020EventMoveIn → moveIn
                event_name = event_type[12:]
                event_name = event_name[0].lower() + event_name[1:]
                self.event.to_xml(parent=elem, namespace=namespace, element_name=event_name)

        # Zero-Tolerance Policy #5: No Schema Violations
        # Always validate exported XML against official eCH XSD schemas
        validate_xml_cached(elem, schema_name='eCH-0020-3-0.xsd', raise_on_error=True)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020Delivery':
        """Parse from XML element.

        Args:
            element: XML element (delivery)

        Returns:
            Parsed ECH0020Delivery model
        """
        ns = {'eCH-0020': NS.ECH0020_V3}

        # Parse version attribute
        version = element.get('version', '3.0')

        # Parse deliveryHeader
        header_elem = element.find('eCH-0020:deliveryHeader', ns)
        if header_elem is None:
            raise ValueError("delivery requires deliveryHeader")
        delivery_header = ECH0020Header.from_xml(header_elem)

        # Parse event (CHOICE of 71 types)
        # Check for baseDelivery first (most common)
        base_elem = element.find('eCH-0020:baseDelivery', ns)
        if base_elem is not None:
            # baseDelivery contains multiple messages elements (each of type eventBaseDelivery)
            messages = []
            for msg_elem in base_elem.findall('eCH-0020:messages', ns):
                messages.append(ECH0020EventBaseDelivery.from_xml(msg_elem))
            if len(messages) == 0:
                raise ValueError("baseDelivery requires at least one messages element")
            event = messages

        # Check for correctReporting
        elif element.find('eCH-0020:correctReporting', ns) is not None:
            correct_elem = element.find('eCH-0020:correctReporting', ns)
            event = ECH0020EventCorrectReporting.from_xml(correct_elem)

        # Check for moveIn
        elif element.find('eCH-0020:moveIn', ns) is not None:
            movein_elem = element.find('eCH-0020:moveIn', ns)
            event = ECH0020EventMoveIn.from_xml(movein_elem)

        # Check for correctContact
        elif element.find('eCH-0020:correctContact', ns) is not None:
            correct_elem = element.find('eCH-0020:correctContact', ns)
            event = ECH0020EventCorrectContact.from_xml(correct_elem)

        # Check for moveOut
        elif element.find('eCH-0020:moveOut', ns) is not None:
            moveout_elem = element.find('eCH-0020:moveOut', ns)
            event = ECH0020EventMoveOut.from_xml(moveout_elem)

        # Check for move
        elif element.find('eCH-0020:move', ns) is not None:
            move_elem = element.find('eCH-0020:move', ns)
            event = ECH0020EventMove.from_xml(move_elem)

        # Check for death
        elif element.find('eCH-0020:death', ns) is not None:
            death_elem = element.find('eCH-0020:death', ns)
            event = ECH0020EventDeath.from_xml(death_elem)

        # Check for marriage
        elif element.find('eCH-0020:marriage', ns) is not None:
            marriage_elem = element.find('eCH-0020:marriage', ns)
            event = ECH0020EventMarriage.from_xml(marriage_elem)

        # Check for correctMaritalInfo
        elif element.find('eCH-0020:correctMaritalInfo', ns) is not None:
            correct_elem = element.find('eCH-0020:correctMaritalInfo', ns)
            event = ECH0020EventCorrectMaritalInfo.from_xml(correct_elem)

        # Check for correctBirthInfo
        elif element.find('eCH-0020:correctBirthInfo', ns) is not None:
            correct_elem = element.find('eCH-0020:correctBirthInfo', ns)
            event = ECH0020EventCorrectBirthInfo.from_xml(correct_elem)

        # Check for correctIdentification
        elif element.find('eCH-0020:correctIdentification', ns) is not None:
            correct_elem = element.find('eCH-0020:correctIdentification', ns)
            event = ECH0020EventCorrectIdentification.from_xml(correct_elem)

        # Check for correctName
        elif element.find('eCH-0020:correctName', ns) is not None:
            correct_elem = element.find('eCH-0020:correctName', ns)
            event = ECH0020EventCorrectName.from_xml(correct_elem)

        # Check for correctPersonAdditionalData
        elif element.find('eCH-0020:correctPersonAdditionalData', ns) is not None:
            correct_elem = element.find('eCH-0020:correctPersonAdditionalData', ns)
            event = ECH0020EventCorrectPersonAdditionalData.from_xml(correct_elem)

        # Check for correctResidencePermit
        elif element.find('eCH-0020:correctResidencePermit', ns) is not None:
            correct_elem = element.find('eCH-0020:correctResidencePermit', ns)
            event = ECH0020EventCorrectResidencePermit.from_xml(correct_elem)

        # Check for correctParentalRelationship
        elif element.find('eCH-0020:correctParentalRelationship', ns) is not None:
            correct_elem = element.find('eCH-0020:correctParentalRelationship', ns)
            event = ECH0020EventCorrectParentalRelationship.from_xml(correct_elem)

        # Check for correctPlaceOfOrigin
        elif element.find('eCH-0020:correctPlaceOfOrigin', ns) is not None:
            correct_elem = element.find('eCH-0020:correctPlaceOfOrigin', ns)
            event = ECH0020EventCorrectPlaceOfOrigin.from_xml(correct_elem)

        # Check for birth
        elif element.find('eCH-0020:birth', ns) is not None:
            birth_elem = element.find('eCH-0020:birth', ns)
            event = ECH0020EventBirth.from_xml(birth_elem)

        # Check for changeName
        elif element.find('eCH-0020:changeName', ns) is not None:
            change_elem = element.find('eCH-0020:changeName', ns)
            event = ECH0020EventChangeName.from_xml(change_elem)

        # Check for contact
        elif element.find('eCH-0020:contact', ns) is not None:
            contact_elem = element.find('eCH-0020:contact', ns)
            event = ECH0020EventContact.from_xml(contact_elem)

        else:
            # All 19 event types found in production data are implemented.
            # Additional event types from the eCH-0020 spec can be added when production examples become available.
            supported = "baseDelivery, correctReporting, moveIn, correctContact, moveOut, move, death, marriage, correctMaritalInfo, correctBirthInfo, correctIdentification, correctName, correctPersonAdditionalData, correctResidencePermit, correctParentalRelationship, correctPlaceOfOrigin, birth, changeName, contact"
            raise NotImplementedError(
                f"Unsupported event type. Currently implemented (19 types): {supported}"
            )

        return cls(
            delivery_header=delivery_header,
            event=event,
            version=version
        )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'ECH0020Delivery':
        """Parse eCH-0020 delivery from XML file.

        Convenience method that handles file I/O and delegates to from_xml().

        Args:
            file_path: Path to XML file (str or Path object)

        Returns:
            Parsed ECH0020Delivery model

        Raises:
            FileNotFoundError: If file doesn't exist
            ET.ParseError: If XML is malformed
            ValueError: If delivery structure is invalid

        Example:
            >>> delivery = ECH0020Delivery.from_file("export.xml")
            >>> delivery = ECH0020Delivery.from_file(Path("/path/to/file.xml"))
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        return cls.from_xml(root)

    def to_file(
        self,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        xml_declaration: bool = True,
        pretty_print: bool = True
    ) -> None:
        """Write eCH-0020 delivery to XML file.

        Convenience method that handles XML serialization and file I/O.

        Args:
            file_path: Path to output XML file (str or Path object)
            encoding: XML encoding (default 'utf-8')
            xml_declaration: Include <?xml version="1.0"?> declaration (default True)
            pretty_print: Format with indentation for readability (default True)

        Example:
            >>> delivery = ECH0020Delivery(...)
            >>> delivery.to_file("export.xml")
            >>> delivery.to_file(Path("/path/to/file.xml"))
        """
        # Convert to Path object for consistency
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Serialize to XML element
        root = self.to_xml()

        # Pretty print if requested
        if pretty_print:
            ET.indent(root, space='  ')

        # Create ElementTree and write to file
        tree = ET.ElementTree(root)
        tree.write(
            path,
            encoding=encoding,
            xml_declaration=xml_declaration,
            method='xml'
        )
