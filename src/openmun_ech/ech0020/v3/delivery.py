"""eCH-0020 v3.0 — Delivery."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union, Literal
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0021 import DataLockType
from openmun_ech.ech0044 import ECH0044PersonIdentification
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
# HEADER TYPE (custom override — extension base with skip_wrapper)
# ============================================================================

class ECH0020Header(BaseModel):
    """Delivery header — extends eCH-0058 header with data lock.

    XSD: headerType (eCH-0020-3-0.xsd lines 894-904)
    Custom override: ECH0058Header.to_xml(skip_wrapper=True) flattens base fields.
    """

    header: ECH0058Header = Field(..., description='Base header per eCH-0058')
    data_lock: Optional[DataLockType] = Field(None, alias='dataLock')
    data_lock_valid_from: Optional[date] = Field(None, alias='dataLockValidFrom')
    data_lock_valid_till: Optional[date] = Field(None, alias='dataLockValidTill')

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(self, parent: Optional[ET.Element], namespace: str, element_name: str) -> ET.Element:
        ns_020 = NS.ECH0020_V3
        ns_058 = NS.ECH0058_V5

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Flatten eCH-0058 header fields (extension base)
        self.header.to_xml(parent=elem, namespace=ns_058, skip_wrapper=True)

        if self.data_lock is not None:
            ET.SubElement(elem, f'{{{ns_020}}}dataLock').text = self.data_lock.value
        if self.data_lock_valid_from is not None:
            ET.SubElement(elem, f'{{{ns_020}}}dataLockValidFrom').text = self.data_lock_valid_from.isoformat()
        if self.data_lock_valid_till is not None:
            ET.SubElement(elem, f'{{{ns_020}}}dataLockValidTill').text = self.data_lock_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020Header':
        ns_020 = NS.ECH0020_V3

        header = ECH0058Header.from_xml(elem)

        data_lock = None
        dl_elem = elem.find(f'{{{ns_020}}}dataLock')
        if dl_elem is not None and dl_elem.text:
            data_lock = DataLockType(dl_elem.text)

        data_lock_valid_from = None
        vf_elem = elem.find(f'{{{ns_020}}}dataLockValidFrom')
        if vf_elem is not None and vf_elem.text:
            data_lock_valid_from = date.fromisoformat(vf_elem.text)

        data_lock_valid_till = None
        vt_elem = elem.find(f'{{{ns_020}}}dataLockValidTill')
        if vt_elem is not None and vt_elem.text:
            data_lock_valid_till = date.fromisoformat(vt_elem.text)

        return cls(
            header=header,
            data_lock=data_lock,
            data_lock_valid_from=data_lock_valid_from,
            data_lock_valid_till=data_lock_valid_till,
        )


# ============================================================================
# INFO / REPORT TYPES (fully declarative)
# ============================================================================

class ECH0020Info(ECHModel):
    """Status/error information block.

    XSD: infoType (eCH-0020-3-0.xsd lines 996-1011)
    All fields optional per XSD. Used in positive/negative reports.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'info'

    code: Optional[str] = xml_field('code', default=None, min_length=1, max_length=250)
    text_english: Optional[str] = xml_field('textEnglish', default=None, min_length=1)
    text_german: Optional[str] = xml_field('textGerman', default=None, min_length=1)
    text_french: Optional[str] = xml_field('textFrench', default=None, min_length=1)
    text_italian: Optional[str] = xml_field('textItalian', default=None, min_length=1)


class ECH0020PersonError(ECHModel):
    """Person-specific error in a negative report.

    XSD: inline complexType in negativeReportType (eCH-0020-3-0.xsd lines 1020-1027)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'personError'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    error_info: List[ECH0020Info] = xml_field(
        'errorInfo', is_list=True, min_length=1,
    )


class ECH0020NegativeReport(ECHModel):
    """Negative report (error/rejection).

    XSD: negativeReportType (eCH-0020-3-0.xsd lines 1017-1029)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'negativeReport'

    general_error: Optional[List[ECH0020Info]] = xml_field(
        'generalError', default=None, is_list=True,
    )
    person_error: Optional[List[ECH0020PersonError]] = xml_field(
        'personError', default=None, is_list=True,
    )


class ECH0020PersonResponse(ECHModel):
    """Person-specific response in a positive report.

    XSD: inline complexType in positiveReportType (eCH-0020-3-0.xsd lines 1033-1040)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'personResponse'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    response: List[ECH0020Info] = xml_field(
        'response', is_list=True, min_length=1,
    )


class ECH0020PositiveReport(ECHModel):
    """Positive report (acknowledgment).

    XSD: positiveReportType (eCH-0020-3-0.xsd lines 1030-1042)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'positiveReport'

    general_response: Optional[List[ECH0020Info]] = xml_field(
        'generalResponse', default=None, is_list=True,
    )
    person_response: Optional[List[ECH0020PersonResponse]] = xml_field(
        'personResponse', default=None, is_list=True,
    )


# ============================================================================
# DELIVERY TYPE (custom override — 65-element CHOICE dispatch)
# ============================================================================

# XSD v3.0 has one case where the delivery CHOICE element name differs from the
# event type name: element "changeResidencePermit" uses type "eventEntryResidencePermit"
# (fixed in v4.0 by renaming the type to match). Our class name follows the type,
# so the auto-derived element name would be wrong.
_EVENT_ELEMENT_NAME_OVERRIDES = {
    'ECH0020EventEntryResidencePermit': 'changeResidencePermit',
}

ECH0020EventType = Union[
    List[ECH0020EventBaseDelivery],
    List[ECH0020EventKeyExchange],
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
    """Main delivery container — root element with 65-element CHOICE.

    XSD: deliveryType (eCH-0020-3-0.xsd lines 905-995)
    Custom override: event dispatch logic, version attribute.
    Note: element name "changeResidencePermit" differs from type name
    "eventEntryResidencePermit" in v3.0 XSD (fixed in v4.0, see Anhang D RFC 2018-52).
    """

    delivery_header: ECH0020Header = Field(..., alias='deliveryHeader')
    event: ECH0020EventType = Field(..., description='Event data (XSD CHOICE of 65 event types)')
    version: Literal["3.0"] = Field("3.0")

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'delivery'
    ) -> ET.Element:
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        elem.set('version', self.version)

        # deliveryHeader
        self.delivery_header.to_xml(parent=elem, namespace=namespace, element_name='deliveryHeader')

        # Event dispatch
        if isinstance(self.event, list):
            if len(self.event) > 0:
                if isinstance(self.event[0], ECH0020EventBaseDelivery):
                    base_elem = ET.SubElement(elem, f'{{{namespace}}}baseDelivery')
                    for msg in self.event:
                        msgs_elem = ET.SubElement(base_elem, f'{{{namespace}}}messages')
                        # Move children from msg's element into messages (skip_wrapper equivalent)
                        msg_root = msg.to_xml(namespace=namespace)
                        for child in msg_root:
                            msgs_elem.append(child)
                elif isinstance(self.event[0], ECH0020EventKeyExchange):
                    key_elem = ET.SubElement(elem, f'{{{namespace}}}keyExchange')
                    for msg in self.event:
                        msgs_elem = ET.SubElement(key_elem, f'{{{namespace}}}messages')
                        msg_root = msg.to_xml(namespace=namespace)
                        for child in msg_root:
                            msgs_elem.append(child)
        else:
            event_type = type(self.event).__name__
            if event_type.startswith('ECH0020Event'):
                # Check for XSD naming exceptions (element name != type name)
                event_name = _EVENT_ELEMENT_NAME_OVERRIDES.get(event_type)
                if event_name is None:
                    event_name = event_type[12:]
                    event_name = event_name[0].lower() + event_name[1:]
                self.event.to_xml(parent=elem, namespace=namespace, element_name=event_name)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020Delivery':
        ns = {'eCH-0020': NS.ECH0020_V3}

        version = element.get('version')
        if version is None:
            raise ValueError(
                "delivery element missing required 'version' attribute "
                "(eCH-0020 v3.0 XSD: use='required')."
            )

        header_elem = element.find('eCH-0020:deliveryHeader', ns)
        if header_elem is None:
            raise ValueError("delivery requires deliveryHeader")
        delivery_header = ECH0020Header.from_xml(header_elem)

        # Event dispatch (CHOICE of 71 types)
        base_elem = element.find('eCH-0020:baseDelivery', ns)
        if base_elem is not None:
            messages = []
            for msg_elem in base_elem.findall('eCH-0020:messages', ns):
                messages.append(ECH0020EventBaseDelivery.from_xml(msg_elem))
            if len(messages) == 0:
                raise ValueError("baseDelivery requires at least one messages element")
            event = messages

        elif element.find('eCH-0020:correctReporting', ns) is not None:
            event = ECH0020EventCorrectReporting.from_xml(element.find('eCH-0020:correctReporting', ns))

        elif element.find('eCH-0020:moveIn', ns) is not None:
            event = ECH0020EventMoveIn.from_xml(element.find('eCH-0020:moveIn', ns))

        elif element.find('eCH-0020:correctContact', ns) is not None:
            event = ECH0020EventCorrectContact.from_xml(element.find('eCH-0020:correctContact', ns))

        elif element.find('eCH-0020:moveOut', ns) is not None:
            event = ECH0020EventMoveOut.from_xml(element.find('eCH-0020:moveOut', ns))

        elif element.find('eCH-0020:move', ns) is not None:
            event = ECH0020EventMove.from_xml(element.find('eCH-0020:move', ns))

        elif element.find('eCH-0020:death', ns) is not None:
            event = ECH0020EventDeath.from_xml(element.find('eCH-0020:death', ns))

        elif element.find('eCH-0020:marriage', ns) is not None:
            event = ECH0020EventMarriage.from_xml(element.find('eCH-0020:marriage', ns))

        elif element.find('eCH-0020:correctMaritalInfo', ns) is not None:
            event = ECH0020EventCorrectMaritalInfo.from_xml(element.find('eCH-0020:correctMaritalInfo', ns))

        elif element.find('eCH-0020:correctBirthInfo', ns) is not None:
            event = ECH0020EventCorrectBirthInfo.from_xml(element.find('eCH-0020:correctBirthInfo', ns))

        elif element.find('eCH-0020:correctIdentification', ns) is not None:
            event = ECH0020EventCorrectIdentification.from_xml(element.find('eCH-0020:correctIdentification', ns))

        elif element.find('eCH-0020:correctName', ns) is not None:
            event = ECH0020EventCorrectName.from_xml(element.find('eCH-0020:correctName', ns))

        elif element.find('eCH-0020:correctPersonAdditionalData', ns) is not None:
            event = ECH0020EventCorrectPersonAdditionalData.from_xml(element.find('eCH-0020:correctPersonAdditionalData', ns))

        elif element.find('eCH-0020:correctResidencePermit', ns) is not None:
            event = ECH0020EventCorrectResidencePermit.from_xml(element.find('eCH-0020:correctResidencePermit', ns))

        elif element.find('eCH-0020:correctParentalRelationship', ns) is not None:
            event = ECH0020EventCorrectParentalRelationship.from_xml(element.find('eCH-0020:correctParentalRelationship', ns))

        elif element.find('eCH-0020:correctPlaceOfOrigin', ns) is not None:
            event = ECH0020EventCorrectPlaceOfOrigin.from_xml(element.find('eCH-0020:correctPlaceOfOrigin', ns))

        elif element.find('eCH-0020:birth', ns) is not None:
            event = ECH0020EventBirth.from_xml(element.find('eCH-0020:birth', ns))

        elif element.find('eCH-0020:changeName', ns) is not None:
            event = ECH0020EventChangeName.from_xml(element.find('eCH-0020:changeName', ns))

        elif element.find('eCH-0020:contact', ns) is not None:
            event = ECH0020EventContact.from_xml(element.find('eCH-0020:contact', ns))

        else:
            supported = "baseDelivery, correctReporting, moveIn, correctContact, moveOut, move, death, marriage, correctMaritalInfo, correctBirthInfo, correctIdentification, correctName, correctPersonAdditionalData, correctResidencePermit, correctParentalRelationship, correctPlaceOfOrigin, birth, changeName, contact"
            raise NotImplementedError(
                f"Unsupported event type. Currently implemented (19 types): {supported}"
            )

        return cls(delivery_header=delivery_header, event=event, version=version)

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'ECH0020Delivery':
        """Parse eCH-0020 delivery from XML file."""
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
        """Write eCH-0020 delivery to XML file."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        root = self.to_xml()
        if pretty_print:
            ET.indent(root, space='  ')
        tree = ET.ElementTree(root)
        tree.write(path, encoding=encoding, xml_declaration=xml_declaration, method='xml')
