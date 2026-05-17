"""eCH-0099 Person Data Delivery to Statistics v2.1.

Standard: eCH-0099 v2.1 (Person data delivery to BFS)
Version stability: Uses eCH-0058 v4, eCH-0011 v8, eCH-0044 v4

This component provides structures for delivering person data to the Swiss
Federal Statistical Office (BFS) for validation and statistics purposes.

Use cases:
- Statistics delivery: Send person data to BFS
- Validation: Pre-validate person data before official submission
- Receipt handling: Process BFS acknowledgments
- Error reports: Handle BFS validation results

ARCHITECTURE: Declarative ECHModel (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union
from datetime import date
from pydantic import Field, field_validator

from openmun_ech.core import ECHModel, xml_field, NS
from openmun_ech.ech0011 import ECH0011ReportedPerson
from openmun_ech.ech0044 import ECH0044PersonIdentification
from openmun_ech.ech0058.v4 import ECH0058Header


# ============================================================================
# Generic Field/Value Data Structure
# ============================================================================

class ECH0099DataType(ECHModel):
    """eCH-0099 Generic field/value data pair.

    Used for personExtendedData and generalData elements.
    XML Schema: eCH-0099 dataType
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'data'

    field: str = xml_field(min_length=1, max_length=100)
    value: str = xml_field(min_length=1, max_length=1000)


# ============================================================================
# Reported Person (Person + Extended Data)
# ============================================================================

class ECH0099ReportedPerson(ECHModel):
    """eCH-0099 Reported person.

    Contains base person data (eCH-0011 reportedPersonType) plus optional
    extended data fields for statistics-specific information.

    XML Schema: eCH-0099 reportedPersonType
    XSD: baseData uses eCH-0011:reportedPersonType (person + residence)
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'reportedPerson'

    base_data: ECH0011ReportedPerson = xml_field(
        'baseData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    person_extended_data: List[ECH0099DataType] = xml_field(
        'personExtendedData', is_list=True, default_factory=list,
    )


# ============================================================================
# Delivery (Top-Level Container for Statistics Submission)
# ============================================================================

class ECH0099Delivery(ECHModel):
    """eCH-0099 Statistics delivery.

    Top-level container for sending person data to BFS for validation or
    statistics purposes. This is the main message type sent via sedex.

    XML Schema: eCH-0099 deliveryType
    Root Element: <delivery version="2.1">

    Custom override: version attribute + skip_wrapper for eCH-0058 header.
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'delivery'

    delivery_header: ECH0058Header = Field(
        ...,
        description="sedex message header (eCH-0058 v4)"
    )

    reported_person: List[ECH0099ReportedPerson] = Field(
        ...,
        min_length=1,
        description="List of persons to report (at least one required)"
    )

    general_data: List[ECH0099DataType] = Field(
        default_factory=list,
        description="Optional delivery-wide or municipality-wide data"
    )

    version: str = Field(
        default="2.1",
        description="Schema version (always '2.1' for this standard)"
    )

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version is exactly '2.1'."""
        if v != "2.1":
            raise ValueError(f"Version must be '2.1', got: {v}")
        return v

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0099_V2,
        element_name: str = 'delivery',
        **_kw,
    ) -> ET.Element:
        """Export to eCH-0099 XML.

        Custom override: version attribute + skip_wrapper for eCH-0058 header.
        """
        if parent is not None:
            root = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            root = ET.Element(f'{{{namespace}}}{element_name}')

        root.set('version', self.version)

        # deliveryHeader — wrapper in eCH-0099, content flattened from eCH-0058
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}deliveryHeader')
        self.delivery_header.to_xml(
            parent=header_wrapper,
            namespace=NS.ECH0058_V4,
            skip_wrapper=True
        )

        # reportedPerson[] (required, at least one)
        for person in self.reported_person:
            person.to_xml(parent=root, namespace=namespace)

        # generalData[] (optional)
        for data in self.general_data:
            data.to_xml(parent=root, namespace=namespace, element_name='generalData')

        return root

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = NS.ECH0099_V2) -> 'ECH0099Delivery':
        """Import from eCH-0099 XML."""
        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # deliveryHeader (required)
        delivery_header_elem = elem.find(f'{{{namespace}}}deliveryHeader')
        if delivery_header_elem is None:
            raise ValueError("Missing required deliveryHeader element")
        delivery_header = ECH0058Header.from_xml(
            delivery_header_elem, namespace=NS.ECH0058_V4
        )

        # reportedPerson[] (required, at least one)
        reported_person = [
            ECH0099ReportedPerson.from_xml(pe, namespace=namespace)
            for pe in elem.findall(f'{{{namespace}}}reportedPerson')
        ]
        if not reported_person:
            raise ValueError("At least one reportedPerson is required")

        # generalData[] (optional)
        general_data = [
            ECH0099DataType.from_xml(de, namespace=namespace)
            for de in elem.findall(f'{{{namespace}}}generalData')
        ]

        return cls(
            delivery_header=delivery_header,
            reported_person=reported_person,
            general_data=general_data,
            version=version
        )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'ECH0099Delivery':
        """Parse eCH-0099 delivery from XML file."""
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
        """Write eCH-0099 delivery to XML file."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        root = self.to_xml()
        if pretty_print:
            ET.indent(root, space='  ')
        tree = ET.ElementTree(root)
        tree.write(path, encoding=encoding, xml_declaration=xml_declaration, method='xml')


# ============================================================================
# BFS Response Types
# ============================================================================

class ECH0099ErrorInfo(ECHModel):
    """eCH-0099 Error information.

    Returned by BFS in validation reports to indicate errors found
    in submitted person data.

    XML Schema: eCH-0099 errorInfoType
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'errorInfo'

    code: str = xml_field()
    text: str = xml_field()


class ECH0099PersonError(ECHModel):
    """eCH-0099 Person-specific error.

    Links a person (by identification) to one or more errors found
    in their data.

    XML Schema: eCH-0099 validationReportType/personError
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'personError'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    error_info: List[ECH0099ErrorInfo] = xml_field(
        'errorInfo', is_list=True, min_length=1,
    )


class ECH0099ValidationReport(ECHModel):
    """eCH-0099 Validation report.

    BFS response containing validation results for a submitted delivery.

    XML Schema: eCH-0099 validationReportType
    Root Element: <validationReport version="2.1">

    Custom override: version attribute + skip_wrapper for eCH-0058 header.
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'validationReport'

    validation_report_header: ECH0058Header = Field(
        ...,
        description="sedex message header (eCH-0058 v4)"
    )

    general_error: List[ECH0099ErrorInfo] = Field(
        default_factory=list,
        description="General errors not specific to any person"
    )

    person_error: List[ECH0099PersonError] = Field(
        default_factory=list,
        description="Person-specific errors"
    )

    general_data: List[ECH0099DataType] = Field(
        default_factory=list,
        description="Optional validation-wide data"
    )

    version: str = Field(
        default="2.1",
        description="Schema version (always '2.1' for this standard)"
    )

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version is exactly '2.1'."""
        if v != "2.1":
            raise ValueError(f"Version must be '2.1', got: {v}")
        return v

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0099_V2,
        element_name: str = 'validationReport',
        **_kw,
    ) -> ET.Element:
        """Export to eCH-0099 XML.

        Custom override: version attribute + skip_wrapper for eCH-0058 header.
        """
        if parent is not None:
            root = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            root = ET.Element(f'{{{namespace}}}{element_name}')

        root.set('version', self.version)

        # validationReportHeader — wrapper in eCH-0099, content flattened from eCH-0058
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}validationReportHeader')
        self.validation_report_header.to_xml(
            parent=header_wrapper,
            namespace=NS.ECH0058_V4,
            skip_wrapper=True
        )

        # generalError[] (optional)
        for error in self.general_error:
            error.to_xml(parent=root, namespace=namespace, element_name='generalError')

        # personError[] (optional)
        for person_error in self.person_error:
            person_error.to_xml(parent=root, namespace=namespace)

        # generalData[] (optional)
        for data in self.general_data:
            data.to_xml(parent=root, namespace=namespace, element_name='generalData')

        return root

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = NS.ECH0099_V2) -> 'ECH0099ValidationReport':
        """Import from eCH-0099 XML."""
        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # validationReportHeader (required)
        header_elem = elem.find(f'{{{namespace}}}validationReportHeader')
        if header_elem is None:
            raise ValueError("Missing required validationReportHeader element")
        validation_report_header = ECH0058Header.from_xml(
            header_elem, namespace=NS.ECH0058_V4
        )

        # generalError[] (optional)
        general_error = [
            ECH0099ErrorInfo.from_xml(e, namespace=namespace)
            for e in elem.findall(f'{{{namespace}}}generalError')
        ]

        # personError[] (optional)
        person_error = [
            ECH0099PersonError.from_xml(e, namespace=namespace)
            for e in elem.findall(f'{{{namespace}}}personError')
        ]

        # generalData[] (optional)
        general_data = [
            ECH0099DataType.from_xml(e, namespace=namespace)
            for e in elem.findall(f'{{{namespace}}}generalData')
        ]

        return cls(
            validation_report_header=validation_report_header,
            general_error=general_error,
            person_error=person_error,
            general_data=general_data,
            version=version
        )


class ECH0099Receipt(ECHModel):
    """eCH-0099 Receipt.

    BFS acknowledgment that a delivery was received and passed to the
    processing pipeline. This is a business-level receipt (not sedex receipt).

    XML Schema: eCH-0099 receiptType
    Root Element: <receipt version="2.1">

    Custom override: version attribute + skip_wrapper for eCH-0058 header.
    """

    __xml_ns__ = NS.ECH0099_V2
    __xml_element__ = 'receipt'

    receipt_header: ECH0058Header = Field(
        ...,
        description="sedex message header (eCH-0058 v4)"
    )

    event_time: date = Field(
        ...,
        description="Timestamp when delivery entered processing pipeline"
    )

    version: str = Field(
        default="2.1",
        description="Schema version (always '2.1' for this standard)"
    )

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version is exactly '2.1'."""
        if v != "2.1":
            raise ValueError(f"Version must be '2.1', got: {v}")
        return v

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0099_V2,
        element_name: str = 'receipt',
        **_kw,
    ) -> ET.Element:
        """Export to eCH-0099 XML.

        Custom override: version attribute + skip_wrapper for eCH-0058 header.
        """
        if parent is not None:
            root = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            root = ET.Element(f'{{{namespace}}}{element_name}')

        root.set('version', self.version)

        # receiptHeader — wrapper in eCH-0099, content flattened from eCH-0058
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}receiptHeader')
        self.receipt_header.to_xml(
            parent=header_wrapper,
            namespace=NS.ECH0058_V4,
            skip_wrapper=True
        )

        # eventTime (required)
        event_time_elem = ET.SubElement(root, f'{{{namespace}}}eventTime')
        event_time_elem.text = self.event_time.isoformat()

        return root

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = NS.ECH0099_V2) -> 'ECH0099Receipt':
        """Import from eCH-0099 XML."""
        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # receiptHeader (required)
        header_elem = elem.find(f'{{{namespace}}}receiptHeader')
        if header_elem is None:
            raise ValueError("Missing required receiptHeader element")
        receipt_header = ECH0058Header.from_xml(
            header_elem, namespace=NS.ECH0058_V4
        )

        # eventTime (required)
        event_time_elem = elem.find(f'{{{namespace}}}eventTime')
        if event_time_elem is None or event_time_elem.text is None:
            raise ValueError("Missing required eventTime element")
        event_time = date.fromisoformat(event_time_elem.text)

        return cls(
            receipt_header=receipt_header,
            event_time=event_time,
            version=version
        )
