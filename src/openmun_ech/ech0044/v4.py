"""eCH-0044 Person Identification v4.1.

Standard: eCH-0044 v4.1 (Person Identification)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides person identification structures including:
- Person IDs (VN, local person ID, other IDs, EU person IDs)
- Basic person data (name, sex, date of birth)
- Support for partially known birth dates

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/person_mapper.py
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Literal, Union
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class Sex(str, Enum):
    """Sex codes per eCH-0044 sexType.

    XSD: sexType (lines 81-87)
    PDF: Section 3.2.4 sex - Geschlecht (page 7)
    """
    MALE = "1"      # männlich (male)
    FEMALE = "2"    # weiblich (female)
    UNKNOWN = "3"   # unbestimmt (undetermined/unknown)


class ECH0044DatePartiallyKnown(BaseModel):
    """eCH-0044 Partially known date.

    Represents a date that may be:
    - Fully known (year, month, day)
    - Partially known (year and month only)
    - Minimally known (year only)

    This is a choice type - exactly ONE of the three fields must be set.

    XML Schema: eCH-0044 datePartiallyKnownType
    """

    year_month_day: Optional[date] = Field(
        None,
        description="Full date (year, month, day)"
    )
    year_month: Optional[str] = Field(
        None,
        pattern=r'^\d{4}-\d{2}$',
        description="Partial date (year and month, format: YYYY-MM)"
    )
    year: Optional[str] = Field(
        None,
        pattern=r'^\d{4}$',
        description="Minimal date (year only, format: YYYY)"
    )

    @field_validator('year_month', 'year')
    @classmethod
    def validate_date_parts(cls, v, info):
        """Validate year-month and year formats."""
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4',
               element_name: str = 'dateOfBirth') -> ET.Element:
        """Export to eCH-0044 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element

        Raises:
            ValueError: If multiple or no date types are set
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Choice: exactly one must be set
        date_count = sum([
            self.year_month_day is not None,
            self.year_month is not None,
            self.year is not None
        ])

        if date_count == 0:
            raise ValueError("Must specify one of: year_month_day, year_month, or year")
        if date_count > 1:
            raise ValueError("Can only specify one of: year_month_day, year_month, or year")

        if self.year_month_day:
            # Full date
            ymd_elem = ET.SubElement(elem, f'{{{namespace}}}yearMonthDay')
            ymd_elem.text = self.year_month_day.isoformat()
        elif self.year_month:
            # Partial date (year-month)
            ym_elem = ET.SubElement(elem, f'{{{namespace}}}yearMonth')
            ym_elem.text = self.year_month
        elif self.year:
            # Minimal date (year only)
            y_elem = ET.SubElement(elem, f'{{{namespace}}}year')
            y_elem.text = self.year

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4') -> 'ECH0044DatePartiallyKnown':
        """Import from eCH-0044 XML.

        Args:
            elem: XML element (date container)
            namespace: XML namespace URI

        Returns:
            Parsed date object

        Raises:
            ValueError: If validation fails
        """
        ns = {'eCH-0044': namespace}

        # Check for full date
        ymd_elem = elem.find('eCH-0044:yearMonthDay', ns)
        ymd = date.fromisoformat(ymd_elem.text.strip()) if ymd_elem is not None and ymd_elem.text else None

        # Check for year-month
        ym_elem = elem.find('eCH-0044:yearMonth', ns)
        ym = ym_elem.text.strip() if ym_elem is not None and ym_elem.text else None

        # Check for year only
        y_elem = elem.find('eCH-0044:year', ns)
        y = y_elem.text.strip() if y_elem is not None and y_elem.text else None

        return cls(
            year_month_day=ymd,
            year_month=ym,
            year=y
        )

    @classmethod
    def from_date(cls, d: date) -> 'ECH0044DatePartiallyKnown':
        """Create from a full date (convenience factory).

        Args:
            d: Date object

        Returns:
            DatePartiallyKnown with year_month_day set
        """
        return cls(year_month_day=d)

    @classmethod
    def from_year_month(cls, year: int, month: int) -> 'ECH0044DatePartiallyKnown':
        """Create from year and month (convenience factory).

        Args:
            year: Year (e.g., 1990)
            month: Month (1-12)

        Returns:
            DatePartiallyKnown with year_month set
        """
        return cls(year_month=f"{year:04d}-{month:02d}")

    @classmethod
    def from_year(cls, year: int) -> 'ECH0044DatePartiallyKnown':
        """Create from year only (convenience factory).

        Args:
            year: Year (e.g., 1990)

        Returns:
            DatePartiallyKnown with year set
        """
        return cls(year=f"{year:04d}")


class ECH0044NamedPersonId(BaseModel):
    """eCH-0044 Named person ID.

    Represents a person identifier with a category and value.
    Used for local person IDs, other person IDs, and EU person IDs.

    Common categories:
    - "veka.id" - Municipality-specific ID
    - "sedex.id" - Sedex participant ID
    - "eWID" - Dwelling ID
    - "EGID" - Building ID
    - Custom municipality codes

    XML Schema: eCH-0044 namedPersonIdType
    """

    person_id_category: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Category/type of person ID (required)"
    )
    person_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Person ID value (required)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4',
               element_name: str = 'localPersonId') -> ET.Element:
        """Export to eCH-0044 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element (localPersonId, otherPersonId, euPersonId)

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Person ID category (required)
        category_elem = ET.SubElement(elem, f'{{{namespace}}}personIdCategory')
        category_elem.text = self.person_id_category

        # Person ID value (required)
        id_elem = ET.SubElement(elem, f'{{{namespace}}}personId')
        id_elem.text = self.person_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4') -> 'ECH0044NamedPersonId':
        """Import from eCH-0044 XML.

        Args:
            elem: XML element (namedPersonId container)
            namespace: XML namespace URI

        Returns:
            Parsed named person ID object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0044': namespace}

        # Category (required)
        category_elem = elem.find('eCH-0044:personIdCategory', ns)
        if category_elem is None or not category_elem.text:
            raise ValueError("Missing required field: personIdCategory")

        # ID value (required)
        id_elem = elem.find('eCH-0044:personId', ns)
        if id_elem is None or not id_elem.text:
            raise ValueError("Missing required field: personId")

        return cls(
            person_id_category=category_elem.text.strip(),
            person_id=id_elem.text.strip()
        )


class ECH0044PersonIdentification(BaseModel):
    """eCH-0044 Person identification (full version).

    Contains complete person identification information including:
    - VN (AHV-13 number) - optional
    - Local person ID - required
    - Other person IDs - optional (multiple)
    - EU person IDs - optional (multiple)
    - Official name - required
    - First name - required
    - Original name - optional
    - Sex - required (1=male, 2=female, 3=unknown)
    - Date of birth - required (may be partially known)

    XML Schema: eCH-0044 personIdentificationType
    """

    vn: Optional[str] = Field(
        None,
        pattern=r'^756\d{10}$',
        description="AHV-13 number (Swiss social security number, format: 756XXXXXXXXXX)"
    )
    local_person_id: ECH0044NamedPersonId = Field(
        ...,
        description="Local person ID (required)"
    )
    other_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="Other person IDs (optional, multiple)"
    )
    eu_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="EU person IDs (optional, multiple)"
    )
    official_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official family name (required)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official first name (required)"
    )
    original_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Birth name / maiden name"
    )
    sex: Sex = Field(
        ...,
        description="Sex (required): 1=male, 2=female, 3=unknown"
    )
    date_of_birth: ECH0044DatePartiallyKnown = Field(
        ...,
        description="Date of birth (required, may be partially known)"
    )

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number.

        The VN must be:
        - 13 digits
        - Start with 756 (Swiss country code)
        - Between 7560000000001 and 7569999999999
        """
        if v is None:
            return v

        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")

        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")

        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4',
               element_name: str = 'personIdentification',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0044 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements
            element_name: Name of container element
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)

        Returns:
            XML Element
        """
        # Use wrapper_namespace for the wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # VN (optional)
        if self.vn:
            vn_elem = ET.SubElement(elem, f'{{{namespace}}}vn')
            vn_elem.text = self.vn

        # Local person ID (required)
        self.local_person_id.to_xml(elem, namespace, 'localPersonId')

        # Other person IDs (optional, multiple)
        for other_id in self.other_person_id:
            other_id.to_xml(elem, namespace, 'otherPersonId')

        # EU person IDs (optional, multiple)
        for eu_id in self.eu_person_id:
            eu_id.to_xml(elem, namespace, 'euPersonId')

        # Official name (required)
        official_elem = ET.SubElement(elem, f'{{{namespace}}}officialName')
        official_elem.text = self.official_name

        # First name (required)
        first_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
        first_elem.text = self.first_name

        # Original name (optional)
        if self.original_name:
            original_elem = ET.SubElement(elem, f'{{{namespace}}}originalName')
            original_elem.text = self.original_name

        # Sex (required)
        sex_elem = ET.SubElement(elem, f'{{{namespace}}}sex')
        sex_elem.text = self.sex.value if hasattr(self.sex, 'value') else str(self.sex)

        # Date of birth (required)
        self.date_of_birth.to_xml(elem, namespace, 'dateOfBirth')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4') -> 'ECH0044PersonIdentification':
        """Import from eCH-0044 XML.

        Args:
            elem: XML element (personIdentification container)
            namespace: XML namespace URI

        Returns:
            Parsed person identification object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0044': namespace}

        # VN (optional)
        vn_elem = elem.find('eCH-0044:vn', ns)
        vn = vn_elem.text.strip() if vn_elem is not None and vn_elem.text else None

        # Local person ID (required)
        local_id_elem = elem.find('eCH-0044:localPersonId', ns)
        if local_id_elem is None:
            raise ValueError("Missing required field: localPersonId")
        local_id = ECH0044NamedPersonId.from_xml(local_id_elem, namespace)

        # Other person IDs (optional, multiple)
        other_ids = []
        for other_elem in elem.findall('eCH-0044:otherPersonId', ns):
            other_ids.append(ECH0044NamedPersonId.from_xml(other_elem, namespace))

        # EU person IDs (optional, multiple)
        eu_ids = []
        for eu_elem in elem.findall('eCH-0044:euPersonId', ns):
            eu_ids.append(ECH0044NamedPersonId.from_xml(eu_elem, namespace))

        # Official name (required)
        official_elem = elem.find('eCH-0044:officialName', ns)
        if official_elem is None or not official_elem.text:
            raise ValueError("Missing required field: officialName")

        # First name (required)
        first_elem = elem.find('eCH-0044:firstName', ns)
        if first_elem is None or not first_elem.text:
            raise ValueError("Missing required field: firstName")

        # Original name (optional)
        original_elem = elem.find('eCH-0044:originalName', ns)
        original = original_elem.text.strip() if original_elem is not None and original_elem.text else None

        # Sex (required)
        sex_elem = elem.find('eCH-0044:sex', ns)
        if sex_elem is None or not sex_elem.text:
            raise ValueError("Missing required field: sex")

        # Date of birth (required)
        dob_elem = elem.find('eCH-0044:dateOfBirth', ns)
        if dob_elem is None:
            raise ValueError("Missing required field: dateOfBirth")
        dob = ECH0044DatePartiallyKnown.from_xml(dob_elem, namespace)

        return cls(
            vn=vn,
            local_person_id=local_id,
            other_person_id=other_ids,
            eu_person_id=eu_ids,
            official_name=official_elem.text.strip(),
            first_name=first_elem.text.strip(),
            original_name=original,
            sex=sex_elem.text.strip(),
            date_of_birth=dob
        )


class ECH0044PersonIdentificationKeyOnly(BaseModel):
    """eCH-0044 Person identification (key only).

    Contains only identification keys without personal data (name, sex, birth).
    Used for privacy-sensitive contexts or ID-only references where personal
    data should not be transmitted.

    Contains:
    - VN (AHV-13 number) - optional
    - Local person ID - required
    - Other person IDs - optional (multiple)
    - EU person IDs - optional (multiple)

    XML Schema: eCH-0044 personIdentificationKeyOnlyType
    XSD Lines: 41-48
    """

    vn: Optional[str] = Field(
        None,
        pattern=r'^756\d{10}$',
        description="AHV-13 number (Swiss social security number, format: 756XXXXXXXXXX)"
    )
    local_person_id: ECH0044NamedPersonId = Field(
        ...,
        description="Local person ID (required)"
    )
    other_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="Other person IDs (optional, multiple)"
    )
    eu_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="EU person IDs (optional, multiple)"
    )

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number."""
        if v is None:
            return v

        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")

        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")

        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4',
               element_name: str = 'personIdentificationKeyOnly') -> ET.Element:
        """Export to eCH-0044 XML.

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

        # VN (optional)
        if self.vn:
            vn_elem = ET.SubElement(elem, f'{{{namespace}}}vn')
            vn_elem.text = self.vn

        # Local person ID (required)
        self.local_person_id.to_xml(elem, namespace=namespace, element_name='localPersonId')

        # Other person IDs (optional, multiple)
        for other_id in self.other_person_id:
            other_id.to_xml(elem, namespace=namespace, element_name='otherPersonId')

        # EU person IDs (optional, multiple)
        for eu_id in self.eu_person_id:
            eu_id.to_xml(elem, namespace=namespace, element_name='euPersonId')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0044PersonIdentificationKeyOnly':
        """Parse from eCH-0044 XML.

        Args:
            elem: XML element to parse

        Returns:
            ECH0044PersonIdentificationKeyOnly instance

        Raises:
            ValueError: If required fields are missing
        """
        ns = {'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'}

        # VN (optional)
        vn_elem = elem.find('eCH-0044:vn', ns)
        vn = vn_elem.text.strip() if vn_elem is not None and vn_elem.text else None

        # Local person ID (required)
        local_id_elem = elem.find('eCH-0044:localPersonId', ns)
        if local_id_elem is None:
            raise ValueError("Missing required field: localPersonId")
        local_person_id = ECH0044NamedPersonId.from_xml(local_id_elem)

        # Other person IDs (optional, multiple)
        other_person_id = [
            ECH0044NamedPersonId.from_xml(e)
            for e in elem.findall('eCH-0044:otherPersonId', ns)
        ]

        # EU person IDs (optional, multiple)
        eu_person_id = [
            ECH0044NamedPersonId.from_xml(e)
            for e in elem.findall('eCH-0044:euPersonId', ns)
        ]

        return cls(
            vn=vn,
            local_person_id=local_person_id,
            other_person_id=other_person_id,
            eu_person_id=eu_person_id,
        )


class ECH0044PersonIdentificationLight(BaseModel):
    """eCH-0044 Person identification (light version).

    Lighter version of person identification with fewer required fields.
    Used in relationships where full identification is not always available.

    Contains:
    - VN (AHV-13 number) - optional
    - Local person ID - optional
    - Other person IDs - optional (multiple)
    - Official name - required
    - First name - required
    - Original name - optional
    - Sex - optional
    - Date of birth - optional (may be partially known)

    XML Schema: eCH-0044 personIdentificationLightType
    """

    vn: Optional[str] = Field(
        None,
        pattern=r'^756\d{10}$',
        description="AHV-13 number (Swiss social security number, format: 756XXXXXXXXXX)"
    )
    local_person_id: Optional[ECH0044NamedPersonId] = Field(
        None,
        description="Local person ID (optional)"
    )
    other_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="Other person IDs (optional, multiple)"
    )
    official_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official family name (required)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Official first name (required)"
    )
    original_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Birth name / maiden name"
    )
    sex: Optional[Sex] = Field(
        None,
        description="Sex (optional): 1=male, 2=female, 3=unknown"
    )
    date_of_birth: Optional[ECH0044DatePartiallyKnown] = Field(
        None,
        description="Date of birth (optional, may be partially known)"
    )

    @field_validator('vn')
    @classmethod
    def validate_vn(cls, v):
        """Validate VN (AHV-13) number."""
        if v is None:
            return v

        if not v.isdigit() or len(v) != 13:
            raise ValueError("VN must be exactly 13 digits")

        vn_int = int(v)
        if not (7560000000001 <= vn_int <= 7569999999999):
            raise ValueError("VN must be between 7560000000001 and 7569999999999")

        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4',
               element_name: str = 'personIdentificationPartner',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0044 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements
            element_name: Name of container element
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)
        """
        # Use wrapper_namespace for the wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # VN (optional)
        if self.vn:
            vn_elem = ET.SubElement(elem, f'{{{namespace}}}vn')
            vn_elem.text = self.vn

        # Local person ID (optional)
        if self.local_person_id:
            self.local_person_id.to_xml(elem, namespace, 'localPersonId')

        # Other person IDs (optional, multiple)
        for other_id in self.other_person_id:
            other_id.to_xml(elem, namespace, 'otherPersonId')

        # Official name (required)
        official_elem = ET.SubElement(elem, f'{{{namespace}}}officialName')
        official_elem.text = self.official_name

        # First name (required)
        first_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
        first_elem.text = self.first_name

        # Original name (optional)
        if self.original_name:
            original_elem = ET.SubElement(elem, f'{{{namespace}}}originalName')
            original_elem.text = self.original_name

        # Sex (optional)
        if self.sex:
            sex_elem = ET.SubElement(elem, f'{{{namespace}}}sex')
            sex_elem.text = self.sex.value if hasattr(self.sex, 'value') else str(self.sex)

        # Date of birth (optional)
        if self.date_of_birth:
            self.date_of_birth.to_xml(elem, namespace, 'dateOfBirth')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0044/4') -> 'ECH0044PersonIdentificationLight':
        """Import from eCH-0044 XML."""
        ns = {'eCH-0044': namespace}

        # VN (optional)
        vn_elem = elem.find('eCH-0044:vn', ns)
        vn = vn_elem.text.strip() if vn_elem is not None and vn_elem.text else None

        # Local person ID (optional)
        local_elem = elem.find('eCH-0044:localPersonId', ns)
        local_id = ECH0044NamedPersonId.from_xml(local_elem, namespace) if local_elem is not None else None

        # Other person IDs (optional, multiple)
        other_ids = []
        for other_elem in elem.findall('eCH-0044:otherPersonId', ns):
            other_ids.append(ECH0044NamedPersonId.from_xml(other_elem, namespace))

        # Official name (required)
        official_elem = elem.find('eCH-0044:officialName', ns)
        if official_elem is None or not official_elem.text:
            raise ValueError("Missing required field: officialName")

        # First name (required)
        first_elem = elem.find('eCH-0044:firstName', ns)
        if first_elem is None or not first_elem.text:
            raise ValueError("Missing required field: firstName")

        # Original name (optional)
        original_elem = elem.find('eCH-0044:originalName', ns)
        original = original_elem.text.strip() if original_elem is not None and original_elem.text else None

        # Sex (optional)
        sex_elem = elem.find('eCH-0044:sex', ns)
        sex = sex_elem.text.strip() if sex_elem is not None and sex_elem.text else None

        # Date of birth (optional)
        dob_elem = elem.find('eCH-0044:dateOfBirth', ns)
        dob = ECH0044DatePartiallyKnown.from_xml(dob_elem, namespace) if dob_elem is not None else None

        return cls(
            vn=vn,
            local_person_id=local_id,
            other_person_id=other_ids,
            official_name=official_elem.text.strip(),
            first_name=first_elem.text.strip(),
            original_name=original,
            sex=sex,
            date_of_birth=dob
        )
