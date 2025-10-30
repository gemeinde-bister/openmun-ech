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

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union
from datetime import date
from pydantic import BaseModel, Field, field_validator

# Import components we depend on
from openmun_ech.ech0011 import ECH0011Person, ECH0011ReportedPerson
from openmun_ech.ech0044 import ECH0044PersonIdentification
from openmun_ech.ech0058.v4 import ECH0058Header


# ============================================================================
# Generic Field/Value Data Structure
# ============================================================================

class ECH0099DataType(BaseModel):
    """eCH-0099 Generic field/value data pair.

    Used for:
    - personExtendedData: Additional person-specific data
    - generalData: Municipality-wide or delivery-wide data

    XML Schema: eCH-0099 dataType
    """

    field: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Field name (e.g., 'housing_type', 'income_category')"
    )

    value: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Field value (free text)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2',
               element_name: str = 'data') -> ET.Element:
        """Export to eCH-0099 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element (personExtendedData or generalData)

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Field (required)
        field_elem = ET.SubElement(elem, f'{{{namespace}}}field')
        field_elem.text = self.field

        # Value (required)
        value_elem = ET.SubElement(elem, f'{{{namespace}}}value')
        value_elem.text = self.value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099DataType':
        """Import from eCH-0099 XML.

        Args:
            elem: XML element (data container)
            namespace: XML namespace URI

        Returns:
            Parsed data object
        """
        ns = {'eCH-0099': namespace}

        field = elem.find('eCH-0099:field', ns)
        value = elem.find('eCH-0099:value', ns)

        if field is None or field.text is None:
            raise ValueError("Missing required field element")
        if value is None or value.text is None:
            raise ValueError("Missing required value element")

        return cls(
            field=field.text,
            value=value.text
        )


# ============================================================================
# Reported Person (Person + Extended Data)
# ============================================================================

class ECH0099ReportedPerson(BaseModel):
    """eCH-0099 Reported person.

    Contains base person data (eCH-0011 reportedPersonType) plus optional extended
    data fields for statistics-specific information.

    XML Schema: eCH-0099 reportedPersonType
    XSD: baseData uses eCH-0011:reportedPersonType (person + residence)
    """

    base_data: ECH0011ReportedPerson = Field(
        ...,
        description="Person base data from eCH-0011 (reportedPersonType: person + residence)"
    )

    person_extended_data: List[ECH0099DataType] = Field(
        default_factory=list,
        description="Optional person-specific extended data (field/value pairs)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> ET.Element:
        """Export to eCH-0099 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}reportedPerson')
        else:
            elem = ET.Element(f'{{{namespace}}}reportedPerson')

        # baseData (required) - eCH-0099 wrapper containing eCH-0011:reportedPersonType content
        # XSD: <xs:element name="baseData" type="eCH-0011:reportedPersonType"/>
        base_data_wrapper = ET.SubElement(elem, f'{{{namespace}}}baseData')

        # Add person and residence elements (from eCH-0011:reportedPersonType)
        ech0011_ns = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # Person (required)
        self.base_data.person.to_xml(
            parent=base_data_wrapper,
            namespace=ech0011_ns,
            element_name='person'
        )

        # Residence (exactly one of three types - XSD choice)
        if self.base_data.has_main_residence is not None:
            self.base_data.has_main_residence.to_xml(
                parent=base_data_wrapper,
                namespace=ech0011_ns
            )
        elif self.base_data.has_secondary_residence is not None:
            self.base_data.has_secondary_residence.to_xml(
                parent=base_data_wrapper,
                namespace=ech0011_ns
            )
        elif self.base_data.has_other_residence is not None:
            self.base_data.has_other_residence.to_xml(
                parent=base_data_wrapper,
                namespace=ech0011_ns
            )

        # personExtendedData[] (optional)
        for extended_data in self.person_extended_data:
            extended_data.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='personExtendedData'
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099ReportedPerson':
        """Import from eCH-0099 XML.

        Args:
            elem: XML element (reportedPerson container)
            namespace: XML namespace URI

        Returns:
            Parsed reported person object
        """
        ns_0099 = {'eCH-0099': namespace}
        ns_0011 = {'eCH-0011': 'http://www.ech.ch/xmlns/eCH-0011/8'}

        # baseData (required) - in eCH-0099 namespace, contains eCH-0011:reportedPersonType
        base_data_elem = elem.find('eCH-0099:baseData', ns_0099)
        if base_data_elem is None:
            raise ValueError("Missing required baseData element")

        # Parse baseData as eCH-0011:reportedPersonType (person + residence)
        # The baseData element itself doesn't have a namespace in eCH-0011, so we parse its children
        from openmun_ech.ech0011 import (
            ECH0011MainResidence,
            ECH0011SecondaryResidence,
            ECH0011OtherResidence,
        )

        # Person (required)
        person_elem = base_data_elem.find('eCH-0011:person', ns_0011)
        if person_elem is None:
            raise ValueError("Missing required person element in baseData")
        person = ECH0011Person.from_xml(person_elem, 'http://www.ech.ch/xmlns/eCH-0011/8')

        # Residence (exactly one of three - XSD choice)
        has_main_residence = None
        has_secondary_residence = None
        has_other_residence = None

        main_res_elem = base_data_elem.find('eCH-0011:hasMainResidence', ns_0011)
        if main_res_elem is not None:
            has_main_residence = ECH0011MainResidence.from_xml(main_res_elem, 'http://www.ech.ch/xmlns/eCH-0011/8')

        sec_res_elem = base_data_elem.find('eCH-0011:hasSecondaryResidence', ns_0011)
        if sec_res_elem is not None:
            has_secondary_residence = ECH0011SecondaryResidence.from_xml(sec_res_elem, 'http://www.ech.ch/xmlns/eCH-0011/8')

        other_res_elem = base_data_elem.find('eCH-0011:hasOtherResidence', ns_0011)
        if other_res_elem is not None:
            has_other_residence = ECH0011OtherResidence.from_xml(other_res_elem, 'http://www.ech.ch/xmlns/eCH-0011/8')

        # Create the ECH0011ReportedPerson from the parsed components
        base_data = ECH0011ReportedPerson(
            person=person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence
        )

        # personExtendedData[] (optional)
        person_extended_data = []
        for extended_elem in elem.findall('eCH-0099:personExtendedData', ns_0099):
            person_extended_data.append(
                ECH0099DataType.from_xml(extended_elem, namespace=namespace)
            )

        return cls(
            base_data=base_data,
            person_extended_data=person_extended_data
        )


# ============================================================================
# Delivery (Top-Level Container for Statistics Submission)
# ============================================================================

class ECH0099Delivery(BaseModel):
    """eCH-0099 Statistics delivery.

    Top-level container for sending person data to BFS for validation or
    statistics purposes. This is the main message type sent via sedex.

    XML Schema: eCH-0099 deliveryType
    Root Element: <delivery version="2.1">
    """

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

    def to_xml(self, namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> ET.Element:
        """Export to eCH-0099 XML.

        Creates the root <delivery> element with version attribute.

        Args:
            namespace: XML namespace URI

        Returns:
            Root XML Element
        """
        # Create root element with version attribute
        root = ET.Element(f'{{{namespace}}}delivery')
        root.set('version', self.version)

        # deliveryHeader (required) - wrapper in eCH-0099 namespace, content in eCH-0058/4
        # Create wrapper element manually, then use skip_wrapper to flatten eCH-0058 fields into it
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}deliveryHeader')
        self.delivery_header.to_xml(
            parent=header_wrapper,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4',
            skip_wrapper=True
        )

        # reportedPerson[] (required, at least one)
        for person in self.reported_person:
            person.to_xml(parent=root, namespace=namespace)

        # generalData[] (optional)
        for general_data in self.general_data:
            general_data.to_xml(
                parent=root,
                namespace=namespace,
                element_name='generalData'
            )

        return root

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099Delivery':
        """Import from eCH-0099 XML.

        Args:
            elem: XML root element (<delivery>)
            namespace: XML namespace URI

        Returns:
            Parsed delivery object
        """
        ns_0099 = {'eCH-0099': namespace}

        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # deliveryHeader (required) - in eCH-0099 namespace
        delivery_header_elem = elem.find('eCH-0099:deliveryHeader', ns_0099)
        if delivery_header_elem is None:
            raise ValueError("Missing required deliveryHeader element")

        delivery_header = ECH0058Header.from_xml(
            delivery_header_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4'
        )

        # reportedPerson[] (required, at least one)
        reported_person = []
        for person_elem in elem.findall('eCH-0099:reportedPerson', ns_0099):
            reported_person.append(
                ECH0099ReportedPerson.from_xml(person_elem, namespace=namespace)
            )

        if not reported_person:
            raise ValueError("At least one reportedPerson is required")

        # generalData[] (optional)
        general_data = []
        for data_elem in elem.findall('eCH-0099:generalData', ns_0099):
            general_data.append(
                ECH0099DataType.from_xml(data_elem, namespace=namespace)
            )

        return cls(
            delivery_header=delivery_header,
            reported_person=reported_person,
            general_data=general_data,
            version=version
        )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'ECH0099Delivery':
        """Parse eCH-0099 delivery from XML file.

        Convenience method that handles file I/O and delegates to from_xml().

        Args:
            file_path: Path to XML file (str or Path object)

        Returns:
            Parsed ECH0099Delivery model

        Raises:
            FileNotFoundError: If file doesn't exist
            ET.ParseError: If XML is malformed
            ValueError: If delivery structure is invalid

        Example:
            >>> delivery = ECH0099Delivery.from_file("statpop.xml")
            >>> delivery = ECH0099Delivery.from_file(Path("/path/to/file.xml"))
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
        """Write eCH-0099 delivery to XML file.

        Convenience method that handles XML serialization and file I/O.

        Args:
            file_path: Path to output XML file (str or Path object)
            encoding: XML encoding (default 'utf-8')
            xml_declaration: Include <?xml version="1.0"?> declaration (default True)
            pretty_print: Format with indentation for readability (default True)

        Example:
            >>> delivery = ECH0099Delivery(...)
            >>> delivery.to_file("statpop.xml")
            >>> delivery.to_file(Path("/path/to/file.xml"))
        """
        # Convert to Path object for consistency
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Serialize to XML element
        root = self.to_xml()

        # Pretty print if requested
        if pretty_print:
            self._indent_xml(root)

        # Create ElementTree and write to file
        tree = ET.ElementTree(root)
        tree.write(
            path,
            encoding=encoding,
            xml_declaration=xml_declaration,
            method='xml'
        )

    @staticmethod
    def _indent_xml(elem: ET.Element, level: int = 0) -> None:
        """Add whitespace for pretty-printing XML.

        Modifies element tree in-place to add newlines and indentation.

        Args:
            elem: Element to indent
            level: Current indentation level
        """
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                ECH0099Delivery._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


# ============================================================================
# BFS Response Types (Optional - for receiving responses)
# ============================================================================

class ECH0099ErrorInfo(BaseModel):
    """eCH-0099 Error information.

    Returned by BFS in validation reports to indicate errors found
    in submitted person data.

    XML Schema: eCH-0099 errorInfoType
    """

    code: str = Field(
        ...,
        description="Numeric error code (range and meaning defined by BFS)"
    )

    text: str = Field(
        ...,
        description="Textual error description (meaning defined by BFS)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2',
               element_name: str = 'errorInfo') -> ET.Element:
        """Export to eCH-0099 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # code (required)
        code_elem = ET.SubElement(elem, f'{{{namespace}}}code')
        code_elem.text = self.code

        # text (required)
        text_elem = ET.SubElement(elem, f'{{{namespace}}}text')
        text_elem.text = self.text

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099ErrorInfo':
        """Import from eCH-0099 XML.

        Args:
            elem: XML element (errorInfo container)
            namespace: XML namespace URI

        Returns:
            Parsed error info object
        """
        ns = {'eCH-0099': namespace}

        code = elem.find('eCH-0099:code', ns)
        text = elem.find('eCH-0099:text', ns)

        if code is None or code.text is None:
            raise ValueError("Missing required code element")
        if text is None or text.text is None:
            raise ValueError("Missing required text element")

        return cls(
            code=code.text,
            text=text.text
        )


class ECH0099PersonError(BaseModel):
    """eCH-0099 Person-specific error.

    Links a person (by identification) to one or more errors found
    in their data.

    XML Schema: eCH-0099 validationReportType/personError
    """

    person_identification: ECH0044PersonIdentification = Field(
        ...,
        description="Person this error relates to"
    )

    error_info: List[ECH0099ErrorInfo] = Field(
        ...,
        min_length=1,
        description="List of errors for this person (at least one required)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> ET.Element:
        """Export to eCH-0099 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}personError')
        else:
            elem = ET.Element(f'{{{namespace}}}personError')

        # personIdentification (required) - wrapper in eCH-0099, content from eCH-0044
        self.person_identification.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0044/4',
            element_name='personIdentification',
            wrapper_namespace=namespace
        )

        # errorInfo[] (required, at least one)
        for error in self.error_info:
            error.to_xml(parent=elem, namespace=namespace, element_name='errorInfo')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099PersonError':
        """Import from eCH-0099 XML.

        Args:
            elem: XML element (personError container)
            namespace: XML namespace URI

        Returns:
            Parsed person error object
        """
        ns_0099 = {'eCH-0099': namespace}

        # personIdentification (required) - in eCH-0099 namespace
        person_id_elem = elem.find('eCH-0099:personIdentification', ns_0099)
        if person_id_elem is None:
            raise ValueError("Missing required personIdentification element")

        person_identification = ECH0044PersonIdentification.from_xml(
            person_id_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0044/4'
        )

        # errorInfo[] (required, at least one)
        error_info = []
        for error_elem in elem.findall('eCH-0099:errorInfo', ns_0099):
            error_info.append(
                ECH0099ErrorInfo.from_xml(error_elem, namespace=namespace)
            )

        if not error_info:
            raise ValueError("At least one errorInfo is required")

        return cls(
            person_identification=person_identification,
            error_info=error_info
        )


class ECH0099ValidationReport(BaseModel):
    """eCH-0099 Validation report.

    BFS response containing validation results for a submitted delivery.
    Includes general errors (delivery-wide) and person-specific errors.

    XML Schema: eCH-0099 validationReportType
    Root Element: <validationReport version="2.1">
    """

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

    def to_xml(self, namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> ET.Element:
        """Export to eCH-0099 XML.

        Creates the root <validationReport> element with version attribute.

        Args:
            namespace: XML namespace URI

        Returns:
            Root XML Element
        """
        # Create root element with version attribute
        root = ET.Element(f'{{{namespace}}}validationReport')
        root.set('version', self.version)

        # validationReportHeader (required) - wrapper in eCH-0099 namespace, content in eCH-0058/4
        # Create wrapper element manually, then use skip_wrapper to flatten eCH-0058 fields into it
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}validationReportHeader')
        self.validation_report_header.to_xml(
            parent=header_wrapper,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4',
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
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099ValidationReport':
        """Import from eCH-0099 XML.

        Args:
            elem: XML root element (<validationReport>)
            namespace: XML namespace URI

        Returns:
            Parsed validation report object
        """
        ns_0099 = {'eCH-0099': namespace}

        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # validationReportHeader (required) - in eCH-0099 namespace
        header_elem = elem.find('eCH-0099:validationReportHeader', ns_0099)
        if header_elem is None:
            raise ValueError("Missing required validationReportHeader element")

        validation_report_header = ECH0058Header.from_xml(
            header_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4'
        )

        # generalError[] (optional)
        general_error = []
        for error_elem in elem.findall('eCH-0099:generalError', ns_0099):
            general_error.append(
                ECH0099ErrorInfo.from_xml(error_elem, namespace=namespace)
            )

        # personError[] (optional)
        person_error = []
        for person_error_elem in elem.findall('eCH-0099:personError', ns_0099):
            person_error.append(
                ECH0099PersonError.from_xml(person_error_elem, namespace=namespace)
            )

        # generalData[] (optional)
        general_data = []
        for data_elem in elem.findall('eCH-0099:generalData', ns_0099):
            general_data.append(
                ECH0099DataType.from_xml(data_elem, namespace=namespace)
            )

        return cls(
            validation_report_header=validation_report_header,
            general_error=general_error,
            person_error=person_error,
            general_data=general_data,
            version=version
        )


class ECH0099Receipt(BaseModel):
    """eCH-0099 Receipt.

    BFS acknowledgment that a delivery was received and passed to the
    processing pipeline. This is a business-level receipt (not sedex receipt).

    XML Schema: eCH-0099 receiptType
    Root Element: <receipt version="2.1">
    """

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

    def to_xml(self, namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> ET.Element:
        """Export to eCH-0099 XML.

        Creates the root <receipt> element with version attribute.

        Args:
            namespace: XML namespace URI

        Returns:
            Root XML Element
        """
        # Create root element with version attribute
        root = ET.Element(f'{{{namespace}}}receipt')
        root.set('version', self.version)

        # receiptHeader (required) - wrapper in eCH-0099 namespace, content in eCH-0058/4
        # Create wrapper element manually, then use skip_wrapper to flatten eCH-0058 fields into it
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}receiptHeader')
        self.receipt_header.to_xml(
            parent=header_wrapper,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4',
            skip_wrapper=True
        )

        # eventTime (required)
        event_time_elem = ET.SubElement(root, f'{{{namespace}}}eventTime')
        event_time_elem.text = self.event_time.isoformat()

        return root

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0099/2') -> 'ECH0099Receipt':
        """Import from eCH-0099 XML.

        Args:
            elem: XML root element (<receipt>)
            namespace: XML namespace URI

        Returns:
            Parsed receipt object
        """
        ns_0099 = {'eCH-0099': namespace}

        # Version attribute (required)
        version = elem.get('version')
        if version is None:
            raise ValueError("Missing required version attribute")

        # receiptHeader (required) - in eCH-0099 namespace
        header_elem = elem.find('eCH-0099:receiptHeader', ns_0099)
        if header_elem is None:
            raise ValueError("Missing required receiptHeader element")

        receipt_header = ECH0058Header.from_xml(
            header_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0058/4'
        )

        # eventTime (required)
        event_time_elem = elem.find('eCH-0099:eventTime', ns_0099)
        if event_time_elem is None or event_time_elem.text is None:
            raise ValueError("Missing required eventTime element")

        event_time = date.fromisoformat(event_time_elem.text)

        return cls(
            receipt_header=receipt_header,
            event_time=event_time,
            version=version
        )
