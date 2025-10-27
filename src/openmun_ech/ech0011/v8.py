"""eCH-0011 Person Basic Data v8.1.

Standard: eCH-0011 v8.1 (Person data)
Version stability: Used in eCH-0020 v3.0, eCH-0099 v2.1

This component provides person data structures including name, birth,
religion, marital status, and nationality information.

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/person_mapper.py
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Dict
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator

# Import components we depend on
from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044NamedPersonId
)
from openmun_ech.ech0010 import ECH0010MailAddress, ECH0010SwissAddressInformation, ECH0010AddressInformation
from openmun_ech.ech0006 import ResidencePermitType

# Import enums from this package
from .enums import (
    Sex,
    ReligionCode,
    MaritalStatus,
    SeparationType,
    CancelationReason,
    NationalityStatus,
    TypeOfResidence,
    TypeOfHousehold,
)

# Import ConfigDict for model_config
from pydantic import ConfigDict


class ECH0011SwissMunicipalityWithoutBFS(BaseModel):
    """eCH-0011 Swiss municipality without mandatory BFS number.

    This is a variant of the standard Swiss municipality type where the BFS
    number (municipalityId) is optional and the historyMunicipalityId field
    is not included.

    XML Schema: eCH-0011 swissMunicipalityWithoutBFS
    XSD Lines: 335-341

    Note: This type is defined in the XSD but does not appear to be referenced
    anywhere. However, it's implemented for 100% XSD parity.
    """

    municipality_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=4,
        description="BFS municipality number (1-4 digits, optional)"
    )
    municipality_name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Official municipality name (required)"
    )
    canton_abbreviation: Optional[CantonAbbreviation] = Field(
        None,
        description="Two-letter canton code (optional)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False
    )

    @field_validator('municipality_id')
    @classmethod
    def validate_municipality_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate BFS municipality number format."""
        if v is None:
            return None
        if not v.isdigit():
            raise ValueError(f"Municipality ID must be numeric, got: {v}")
        if not (1 <= len(v) <= 4):
            raise ValueError(f"Municipality ID must be 1-4 digits, got: {v}")
        return v

    def to_xml(self, parent: ET.Element, tag: str = "swissMunicipalityWithoutBFS",
               nsmap: Optional[dict] = None) -> ET.Element:
        """Convert to XML element.

        Args:
            parent: Parent XML element
            tag: Tag name for this element
            nsmap: Namespace map (optional)

        Returns:
            Created XML element
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0007": "http://www.ech.ch/xmlns/eCH-0007/6"
            }

        elem = ET.SubElement(parent, f"{{{nsmap[None]}}}{tag}")

        # Municipality ID (optional)
        if self.municipality_id:
            mun_id = ET.SubElement(elem, f"{{{nsmap['eCH-0007']}}}municipalityId")
            mun_id.text = self.municipality_id

        # Municipality name (required)
        mun_name = ET.SubElement(elem, f"{{{nsmap['eCH-0007']}}}municipalityName")
        mun_name.text = self.municipality_name

        # Canton abbreviation (optional)
        if self.canton_abbreviation:
            canton = ET.SubElement(elem, f"{{{nsmap['eCH-0007']}}}cantonAbbreviation")
            canton.text = self.canton_abbreviation.value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, nsmap: Optional[dict] = None) -> 'ECH0011SwissMunicipalityWithoutBFS':
        """Create instance from XML element.

        Args:
            elem: XML element (swissMunicipalityWithoutBFS)
            nsmap: Namespace map (optional)

        Returns:
            ECH0011SwissMunicipalityWithoutBFS instance
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0007": "http://www.ech.ch/xmlns/eCH-0007/6"
            }

        ns_0007 = nsmap['eCH-0007']

        # Extract municipality name (required)
        mun_name_elem = elem.find(f"{{{ns_0007}}}municipalityName")
        if mun_name_elem is None or not mun_name_elem.text:
            raise ValueError("Missing required field: municipalityName")

        # Extract optional municipality ID
        mun_id_elem = elem.find(f"{{{ns_0007}}}municipalityId")
        mun_id = mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None

        # Extract optional canton abbreviation
        canton_elem = elem.find(f"{{{ns_0007}}}cantonAbbreviation")
        canton = CantonAbbreviation(canton_elem.text.strip()) if canton_elem is not None and canton_elem.text else None

        return cls(
            municipality_id=mun_id,
            municipality_name=mun_name_elem.text.strip(),
            canton_abbreviation=canton
        )


class ECH0011ForeignerName(BaseModel):
    """eCH-0011 Foreigner name information.

    Used for foreign names on passports or declared foreign names.

    XML Schema: eCH-0011 foreignerNameType
    """

    name: Optional[str] = Field(
        None,
        max_length=100,
        description="Foreign last name"
    )
    first_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Foreign first name"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'nameOnForeignPassport') -> ET.Element:
        """Export to eCH-0011 XML.

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

        # Name (optional)
        if self.name:
            name_elem = ET.SubElement(elem, f'{{{namespace}}}name')
            name_elem.text = self.name

        # First name (optional)
        if self.first_name:
            first_name_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
            first_name_elem.text = self.first_name

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011ForeignerName':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (foreigner name container)
            namespace: XML namespace URI

        Returns:
            Parsed foreigner name object
        """
        ns = {'eCH-0011': namespace}

        name_elem = elem.find('eCH-0011:name', ns)
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else None

        first_name_elem = elem.find('eCH-0011:firstName', ns)
        first_name = first_name_elem.text.strip() if first_name_elem is not None and first_name_elem.text else None

        return cls(name=name, first_name=first_name)


class ECH0011NameData(BaseModel):
    """eCH-0011 Name data.

    Contains all name information for a person including official names,
    original names, alliance names, and foreign names.

    XML Schema: eCH-0011 nameDataType
    """

    official_name: str = Field(
        ...,
        max_length=100,
        description="Official family name (required)"
    )
    first_name: str = Field(
        ...,
        max_length=100,
        description="Official first name (required)"
    )
    original_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Birth name / maiden name"
    )
    alliance_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Alliance name (partner's name in double-name situations)"
    )
    alias_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Alias / künstlername"
    )
    other_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Other name"
    )
    call_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Call name / preferred first name"
    )

    # Choice: name on foreign passport OR declared foreign name (optional)
    name_on_foreign_passport: Optional[ECH0011ForeignerName] = Field(
        None,
        description="Name as it appears on foreign passport"
    )
    declared_foreign_name: Optional[ECH0011ForeignerName] = Field(
        None,
        description="Declared foreign name"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}nameData')
        else:
            elem = ET.Element(f'{{{namespace}}}nameData')

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

        # Alliance name (optional)
        if self.alliance_name:
            alliance_elem = ET.SubElement(elem, f'{{{namespace}}}allianceName')
            alliance_elem.text = self.alliance_name

        # Alias name (optional)
        if self.alias_name:
            alias_elem = ET.SubElement(elem, f'{{{namespace}}}aliasName')
            alias_elem.text = self.alias_name

        # Other name (optional)
        if self.other_name:
            other_elem = ET.SubElement(elem, f'{{{namespace}}}otherName')
            other_elem.text = self.other_name

        # Call name (optional)
        if self.call_name:
            call_elem = ET.SubElement(elem, f'{{{namespace}}}callName')
            call_elem.text = self.call_name

        # Foreign passport name (optional, choice with declared foreign name)
        if self.name_on_foreign_passport:
            self.name_on_foreign_passport.to_xml(elem, namespace, 'nameOnForeignPassport')
        elif self.declared_foreign_name:
            self.declared_foreign_name.to_xml(elem, namespace, 'declaredForeignName')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011NameData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (nameData container)
            namespace: XML namespace URI

        Returns:
            Parsed name data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Required fields
        official_elem = elem.find('eCH-0011:officialName', ns)
        if official_elem is None or not official_elem.text:
            raise ValueError("Missing required field: officialName")

        first_elem = elem.find('eCH-0011:firstName', ns)
        if first_elem is None or not first_elem.text:
            raise ValueError("Missing required field: firstName")

        # Optional fields
        original_elem = elem.find('eCH-0011:originalName', ns)
        original = original_elem.text.strip() if original_elem is not None and original_elem.text else None

        alliance_elem = elem.find('eCH-0011:allianceName', ns)
        alliance = alliance_elem.text.strip() if alliance_elem is not None and alliance_elem.text else None

        alias_elem = elem.find('eCH-0011:aliasName', ns)
        alias = alias_elem.text.strip() if alias_elem is not None and alias_elem.text else None

        other_elem = elem.find('eCH-0011:otherName', ns)
        other = other_elem.text.strip() if other_elem is not None and other_elem.text else None

        call_elem = elem.find('eCH-0011:callName', ns)
        call = call_elem.text.strip() if call_elem is not None and call_elem.text else None

        # Foreign names (choice)
        foreign_passport_elem = elem.find('eCH-0011:nameOnForeignPassport', ns)
        foreign_passport = ECH0011ForeignerName.from_xml(foreign_passport_elem, namespace) if foreign_passport_elem is not None else None

        declared_foreign_elem = elem.find('eCH-0011:declaredForeignName', ns)
        declared_foreign = ECH0011ForeignerName.from_xml(declared_foreign_elem, namespace) if declared_foreign_elem is not None else None

        return cls(
            official_name=official_elem.text.strip(),
            first_name=first_elem.text.strip(),
            original_name=original,
            alliance_name=alliance,
            alias_name=alias,
            other_name=other,
            call_name=call,
            name_on_foreign_passport=foreign_passport,
            declared_foreign_name=declared_foreign
        )


class ECH0011GeneralPlace(BaseModel):
    """eCH-0011 General place (birth/death location).

    Represents a place that can be:
    - Unknown
    - Swiss municipality (uses eCH-0007)
    - Foreign country (uses eCH-0008) with optional town

    XML Schema: eCH-0011 generalPlaceType
    """

    unknown: Optional[bool] = Field(
        None,
        description="True if place is unknown"
    )
    swiss_municipality: Optional[ECH0007Municipality] = Field(
        None,
        description="Swiss municipality (if applicable)"
    )
    foreign_country: Optional[ECH0008Country] = Field(
        None,
        description="Foreign country (if applicable)"
    )
    foreign_town: Optional[str] = Field(
        None,
        max_length=100,
        description="Town name in foreign country"
    )

    @field_validator('swiss_municipality', 'foreign_country')
    @classmethod
    def validate_mutually_exclusive(cls, v, info):
        """Validate that only one place type is set."""
        # This is called for each field, so we can't do full validation here
        # Will rely on to_xml/from_xml to enforce the choice
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'placeOfBirth') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element

        Raises:
            ValueError: If multiple or no place types are set
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Choice: unknown, swissTown, or foreignCountry
        place_count = sum([
            self.unknown is True,
            self.swiss_municipality is not None,
            self.foreign_country is not None
        ])

        if place_count == 0:
            raise ValueError("Must specify one of: unknown, swiss_municipality, or foreign_country")
        if place_count > 1:
            raise ValueError("Can only specify one of: unknown, swiss_municipality, or foreign_country")

        if self.unknown:
            # Unknown place (XSD uses "0" for true, per spec)
            unknown_elem = ET.SubElement(elem, f'{{{namespace}}}unknown')
            unknown_elem.text = "0"
        elif self.swiss_municipality:
            # Swiss municipality - swissTown wrapper in eCH-0011, content in eCH-0007
            swiss_town_elem = ET.SubElement(elem, f'{{{namespace}}}swissTown')
            # Serialize municipality content (municipalityId, municipalityName, etc.) in eCH-0007 namespace
            swiss_muni = self.swiss_municipality.swiss_municipality
            ech0007_ns = 'http://www.ech.ch/xmlns/eCH-0007/5'
            if swiss_muni.municipality_id:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}municipalityId').text = swiss_muni.municipality_id
            ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}municipalityName').text = swiss_muni.municipality_name
            if swiss_muni.canton_abbreviation:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}cantonAbbreviation').text = swiss_muni.canton_abbreviation.value
            if swiss_muni.history_municipality_id:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}historyMunicipalityId').text = swiss_muni.history_municipality_id
        elif self.foreign_country:
            # Foreign country - wrapper in eCH-0011, content in eCH-0008
            foreign_elem = ET.SubElement(elem, f'{{{namespace}}}foreignCountry')
            self.foreign_country.to_xml(
                parent=foreign_elem,
                namespace='http://www.ech.ch/xmlns/eCH-0008/3',  # Content namespace
                element_name='country',
                wrapper_namespace=namespace  # Wrapper in eCH-0011
            )

            # Optional town within foreign country
            if self.foreign_town:
                town_elem = ET.SubElement(foreign_elem, f'{{{namespace}}}town')
                town_elem.text = self.foreign_town

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011GeneralPlace':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (generalPlace container)
            namespace: XML namespace URI

        Returns:
            Parsed general place object

        Raises:
            ValueError: If validation fails
        """
        ns = {
            'eCH-0011': namespace,
            'eCH-0007': 'http://www.ech.ch/xmlns/eCH-0007/5',
            'eCH-0008': 'http://www.ech.ch/xmlns/eCH-0008/3'
        }

        # Check for unknown
        unknown_elem = elem.find('eCH-0011:unknown', ns)
        unknown = unknown_elem is not None

        # Check for Swiss municipality - swissTown element in eCH-0011 namespace
        # Parse swissMunicipalityType content directly (municipalityId, municipalityName, etc.)
        swiss_elem = elem.find('eCH-0011:swissTown', ns)
        swiss_mun = None
        if swiss_elem is not None:
            from openmun_ech.ech0007 import ECH0007SwissMunicipality
            mun_id_elem = swiss_elem.find('eCH-0007:municipalityId', ns)
            mun_name_elem = swiss_elem.find('eCH-0007:municipalityName', ns)
            canton_elem = swiss_elem.find('eCH-0007:cantonAbbreviation', ns)
            hist_id_elem = swiss_elem.find('eCH-0007:historyMunicipalityId', ns)

            if mun_name_elem is not None and mun_name_elem.text:
                swiss_municipality = ECH0007SwissMunicipality(
                    municipality_id=mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None,
                    municipality_name=mun_name_elem.text.strip(),
                    canton_abbreviation=canton_elem.text.strip() if canton_elem is not None and canton_elem.text else None,
                    history_municipality_id=hist_id_elem.text.strip() if hist_id_elem is not None and hist_id_elem.text else None
                )
                swiss_mun = ECH0007Municipality(swiss_municipality=swiss_municipality)

        # Check for foreign country
        foreign_container = elem.find('eCH-0011:foreignCountry', ns)
        foreign_country = None
        foreign_town = None

        if foreign_container is not None:
            # country element is in eCH-0011 namespace (wrapper), content is in eCH-0008
            country_elem = foreign_container.find('eCH-0011:country', ns)
            if country_elem is not None:
                foreign_country = ECH0008Country.from_xml(country_elem, 'http://www.ech.ch/xmlns/eCH-0008/3')

            town_elem = foreign_container.find('eCH-0011:town', ns)
            foreign_town = town_elem.text.strip() if town_elem is not None and town_elem.text else None

        return cls(
            unknown=unknown if unknown else None,
            swiss_municipality=swiss_mun,
            foreign_country=foreign_country,
            foreign_town=foreign_town
        )


class ECH0011BirthData(BaseModel):
    """eCH-0011 Birth data.

    Contains birth information including date, place, and sex.

    XML Schema: eCH-0011 birthDataType
    """

    date_of_birth: date = Field(
        ...,
        description="Date of birth (required)"
    )
    place_of_birth: ECH0011GeneralPlace = Field(
        ...,
        description="Place of birth (required)"
    )
    sex: Sex = Field(
        ...,
        description="Sex: 1=male, 2=female, 3=unknown (required)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}birthData')
        else:
            elem = ET.Element(f'{{{namespace}}}birthData')

        # Date of birth (required) - uses eCH-0044 datePartiallyKnownType
        dob_elem = ET.SubElement(elem, f'{{{namespace}}}dateOfBirth')
        # yearMonthDay is in eCH-0044 namespace per XSD
        ymd_elem = ET.SubElement(dob_elem, '{http://www.ech.ch/xmlns/eCH-0044/4}yearMonthDay')
        ymd_elem.text = self.date_of_birth.isoformat()

        # Place of birth (required)
        self.place_of_birth.to_xml(elem, namespace, 'placeOfBirth')

        # Sex (required)
        sex_elem = ET.SubElement(elem, f'{{{namespace}}}sex')
        sex_elem.text = self.sex

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011BirthData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (birthData container)
            namespace: XML namespace URI

        Returns:
            Parsed birth data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Date of birth (required) - uses eCH-0044 datePartiallyKnownType
        dob_elem = elem.find('eCH-0011:dateOfBirth', ns)
        if dob_elem is None:
            raise ValueError("Missing required field: dateOfBirth")
        # Parse yearMonthDay element (full date) - in eCH-0044 namespace
        ns_0044 = {'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'}
        ymd_elem = dob_elem.find('eCH-0044:yearMonthDay', ns_0044)
        if ymd_elem is None or not ymd_elem.text:
            raise ValueError("Missing yearMonthDay in dateOfBirth")
        dob = date.fromisoformat(ymd_elem.text.strip())

        # Place of birth (required)
        place_elem = elem.find('eCH-0011:placeOfBirth', ns)
        if place_elem is None:
            raise ValueError("Missing required field: placeOfBirth")
        place = ECH0011GeneralPlace.from_xml(place_elem, namespace)

        # Sex (required)
        sex_elem = elem.find('eCH-0011:sex', ns)
        if sex_elem is None or not sex_elem.text:
            raise ValueError("Missing required field: sex")

        return cls(
            date_of_birth=dob,
            place_of_birth=place,
            sex=sex_elem.text.strip()
        )


class ECH0011ReligionData(BaseModel):
    """eCH-0011 Religion data.

    Contains religion code (3-6 digits) and optional validity date.

    XML Schema: eCH-0011 religionDataType
    """

    religion: str = Field(
        ...,
        min_length=3,
        max_length=6,
        pattern=r'^\d{3,6}$',
        description="Religion code (3-6 digits, required)"
    )
    religion_valid_from: Optional[date] = Field(
        None,
        description="Date from which religion is valid"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
        element_name: str = 'religionData',
        wrapper_namespace: Optional[str] = None
    ) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of the element to create
            wrapper_namespace: Optional wrapper namespace (for cross-schema composition)

        Returns:
            XML Element

        Note:
            When wrapper_namespace is provided, creates:
            <wrapper_namespace:element_name>
              <namespace:religionData>...</namespace:religionData>
            </wrapper_namespace:element_name>
        """
        # Handle wrapper namespace (for eCH-0020 cross-schema composition)
        # When wrapper_namespace is provided, create element in wrapper namespace
        # Content (children) will still use the original namespace
        if wrapper_namespace is not None and parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_namespace}}}{element_name}')
        else:
            # Standard behavior - create in own namespace
            if parent is not None:
                elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
            else:
                elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Religion code (required)
        religion_elem = ET.SubElement(elem, f'{{{namespace}}}religion')
        religion_elem.text = self.religion

        # Valid from date (optional)
        if self.religion_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}religionValidFrom')
            valid_elem.text = self.religion_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011ReligionData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (religionData container)
            namespace: XML namespace URI

        Returns:
            Parsed religion data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Religion code (required)
        religion_elem = elem.find('eCH-0011:religion', ns)
        if religion_elem is None or not religion_elem.text:
            raise ValueError("Missing required field: religion")

        # Valid from date (optional)
        valid_elem = elem.find('eCH-0011:religionValidFrom', ns)
        valid_from = date.fromisoformat(valid_elem.text.strip()) if valid_elem is not None and valid_elem.text else None

        return cls(
            religion=religion_elem.text.strip(),
            religion_valid_from=valid_from
        )


class ECH0011SeparationData(BaseModel):
    """eCH-0011 Separation data.

    Contains information about marital separation.

    XML Schema: eCH-0011 separationDataType
    """

    separation: Optional[SeparationType] = Field(
        None,
        description="Separation type: 1=judicial, 2=de facto"
    )
    separation_valid_from: Optional[date] = Field(
        None,
        description="Separation start date"
    )
    separation_valid_till: Optional[date] = Field(
        None,
        description="Separation end date"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}separationData')
        else:
            elem = ET.Element(f'{{{namespace}}}separationData')

        # Separation type (optional)
        if self.separation:
            sep_elem = ET.SubElement(elem, f'{{{namespace}}}separation')
            sep_elem.text = self.separation

        # Valid from (optional)
        if self.separation_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}separationValidFrom')
            from_elem.text = self.separation_valid_from.isoformat()

        # Valid till (optional)
        if self.separation_valid_till:
            till_elem = ET.SubElement(elem, f'{{{namespace}}}separationValidTill')
            till_elem.text = self.separation_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011SeparationData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (separationData container)
            namespace: XML namespace URI

        Returns:
            Parsed separation data object
        """
        ns = {'eCH-0011': namespace}

        # Separation type (optional)
        sep_elem = elem.find('eCH-0011:separation', ns)
        sep = sep_elem.text.strip() if sep_elem is not None and sep_elem.text else None

        # Valid from (optional)
        from_elem = elem.find('eCH-0011:separationValidFrom', ns)
        valid_from = date.fromisoformat(from_elem.text.strip()) if from_elem is not None and from_elem.text else None

        # Valid till (optional)
        till_elem = elem.find('eCH-0011:separationValidTill', ns)
        valid_till = date.fromisoformat(till_elem.text.strip()) if till_elem is not None and till_elem.text else None

        return cls(
            separation=sep,
            separation_valid_from=valid_from,
            separation_valid_till=valid_till
        )


class ECH0011MaritalData(BaseModel):
    """eCH-0011 Marital data.

    Contains marital status information including status code, date,
    cancelation reason, and separation details.

    XML Schema: eCH-0011 maritalDataType
    """

    marital_status: MaritalStatus = Field(
        ...,
        description=(
            "Marital status (required):\n"
            "1=single, 2=married, 3=widowed, 4=divorced,\n"
            "5=unmarried, 6=registered partnership, 7=dissolved partnership,\n"
            "9=not specified"
        )
    )
    date_of_marital_status: Optional[date] = Field(
        None,
        description="Date when marital status became effective"
    )
    cancelation_reason: Optional[CancelationReason] = Field(
        None,
        description=(
            "Reason for partnership dissolution:\n"
            "1=death, 2=declared missing, 3=divorce/dissolution,\n"
            "4=annulment, 9=other"
        )
    )
    official_proof_of_marital_status_yes_no: Optional[bool] = Field(
        None,
        description="Whether official proof of marital status exists"
    )
    separation_data: Optional[ECH0011SeparationData] = Field(
        None,
        description="Separation information (if applicable)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}maritalData')
        else:
            elem = ET.Element(f'{{{namespace}}}maritalData')

        # Marital status (required)
        status_elem = ET.SubElement(elem, f'{{{namespace}}}maritalStatus')
        status_elem.text = self.marital_status

        # Date of marital status (optional)
        if self.date_of_marital_status:
            date_elem = ET.SubElement(elem, f'{{{namespace}}}dateOfMaritalStatus')
            date_elem.text = self.date_of_marital_status.isoformat()

        # Cancelation reason (optional)
        if self.cancelation_reason:
            cancel_elem = ET.SubElement(elem, f'{{{namespace}}}cancelationReason')
            cancel_elem.text = self.cancelation_reason

        # Official proof (optional)
        if self.official_proof_of_marital_status_yes_no is not None:
            proof_elem = ET.SubElement(elem, f'{{{namespace}}}officialProofOfMaritalStatusYesNo')
            proof_elem.text = 'true' if self.official_proof_of_marital_status_yes_no else 'false'

        # Separation data (optional)
        if self.separation_data:
            self.separation_data.to_xml(elem, namespace)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011MaritalData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (maritalData container)
            namespace: XML namespace URI

        Returns:
            Parsed marital data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Marital status (required)
        status_elem = elem.find('eCH-0011:maritalStatus', ns)
        if status_elem is None or not status_elem.text:
            raise ValueError("Missing required field: maritalStatus")

        # Date (optional)
        date_elem = elem.find('eCH-0011:dateOfMaritalStatus', ns)
        status_date = date.fromisoformat(date_elem.text.strip()) if date_elem is not None and date_elem.text else None

        # Cancelation reason (optional)
        cancel_elem = elem.find('eCH-0011:cancelationReason', ns)
        cancel = cancel_elem.text.strip() if cancel_elem is not None and cancel_elem.text else None

        # Official proof (optional)
        proof_elem = elem.find('eCH-0011:officialProofOfMaritalStatusYesNo', ns)
        proof = proof_elem.text.strip().lower() == 'true' if proof_elem is not None and proof_elem.text else None

        # Separation data (optional)
        sep_elem = elem.find('eCH-0011:separationData', ns)
        sep_data = ECH0011SeparationData.from_xml(sep_elem, namespace) if sep_elem is not None else None

        return cls(
            marital_status=status_elem.text.strip(),
            date_of_marital_status=status_date,
            cancelation_reason=cancel,
            official_proof_of_marital_status_yes_no=proof,
            separation_data=sep_data
        )


class ECH0011MaritalDataRestrictedMarriage(BaseModel):
    """eCH-0011 Marital data restricted for marriage events.

    Restriction of maritalDataType where maritalStatus is fixed to "2" (MARRIED).
    Used in specific marriage event contexts.

    XML Schema: eCH-0011 maritalDataRestrictedMarriageType
    XSD Lines: 123-139
    """

    date_of_marital_status: date = Field(..., description="Marriage date (required)")
    official_proof_of_marital_status_yes_no: bool = Field(
        ...,
        description="Official proof exists (required)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @property
    def marital_status(self) -> MaritalStatus:
        """Marital status is always MARRIED for this restricted type."""
        return MaritalStatus.MARRIED


class ECH0011MaritalDataRestrictedPartnership(BaseModel):
    """eCH-0011 Marital data restricted for registered partnership events.

    Restriction of maritalDataType where maritalStatus is fixed to "6" (REGISTERED_PARTNERSHIP).
    Used in specific partnership registration contexts.

    XML Schema: eCH-0011 maritalDataRestrictedPartnershipType
    XSD Lines: 140-156
    """

    date_of_marital_status: date = Field(..., description="Partnership registration date (required)")
    official_proof_of_marital_status_yes_no: bool = Field(
        ...,
        description="Official proof exists (required)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @property
    def marital_status(self) -> MaritalStatus:
        """Marital status is always REGISTERED_PARTNERSHIP for this restricted type."""
        return MaritalStatus.REGISTERED_PARTNERSHIP


class ECH0011MaritalDataRestrictedDivorce(BaseModel):
    """eCH-0011 Marital data restricted for divorce events.

    Restriction of maritalDataType where maritalStatus is fixed to "4" (DIVORCED).
    Used in specific divorce event contexts.

    XML Schema: eCH-0011 maritalDataRestrictedDivorceType
    XSD Lines: 157-172
    """

    date_of_marital_status: date = Field(..., description="Divorce date (required)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @property
    def marital_status(self) -> MaritalStatus:
        """Marital status is always DIVORCED for this restricted type."""
        return MaritalStatus.DIVORCED


class ECH0011MaritalDataRestrictedUndoMarried(BaseModel):
    """eCH-0011 Marital data restricted for marriage annulment events.

    Restriction of maritalDataType where maritalStatus is fixed to "5" (UNMARRIED/annulled).
    Used when a marriage is annulled (never legally valid).

    XML Schema: eCH-0011 maritalDataRestrictedUndoMarriedType
    XSD Lines: 173-188
    """

    date_of_marital_status: date = Field(..., description="Annulment date (required)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @property
    def marital_status(self) -> MaritalStatus:
        """Marital status is always UNMARRIED for this restricted type."""
        return MaritalStatus.UNMARRIED


class ECH0011MaritalDataRestrictedUndoPartnership(BaseModel):
    """eCH-0011 Marital data restricted for partnership dissolution events.

    Restriction of maritalDataType where maritalStatus is fixed to "7" (DISSOLVED_PARTNERSHIP).
    Used when a registered partnership is dissolved.

    XML Schema: eCH-0011 maritalDataRestrictedUndoPartnershipType
    XSD Lines: 189-205
    """

    date_of_marital_status: date = Field(..., description="Dissolution date (required)")
    cancelation_reason: CancelationReason = Field(..., description="Reason for dissolution (required)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False
    )

    @property
    def marital_status(self) -> MaritalStatus:
        """Marital status is always DISSOLVED_PARTNERSHIP for this restricted type."""
        return MaritalStatus.DISSOLVED_PARTNERSHIP


class ECH0011MaritalDataRestrictedMaritalStatusPartner(BaseModel):
    """eCH-0011 Marital data restricted for partner death/dissolution events.

    Restriction of maritalDataType where maritalStatus is one of:
    - "3" (WIDOWED)
    - "5" (UNMARRIED)
    - "7" (DISSOLVED_PARTNERSHIP)

    Used for events involving partner death or partnership dissolution.

    XML Schema: eCH-0011 maritalDataRestrictedMaritalStatusPartnerType
    XSD Lines: 206-224
    """

    marital_status: MaritalStatus = Field(
        ...,
        description="Marital status (must be WIDOWED, UNMARRIED, or DISSOLVED_PARTNERSHIP)"
    )
    date_of_marital_status: date = Field(..., description="Status change date (required)")
    cancelation_reason: Optional[CancelationReason] = Field(
        None,
        description="Reason for dissolution (optional)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False
    )

    @field_validator('marital_status')
    @classmethod
    def validate_marital_status(cls, v: MaritalStatus) -> MaritalStatus:
        """Validate that marital status is one of the allowed values."""
        allowed = {MaritalStatus.WIDOWED, MaritalStatus.UNMARRIED, MaritalStatus.DISSOLVED_PARTNERSHIP}
        if v not in allowed:
            raise ValueError(
                f"Marital status must be WIDOWED (3), UNMARRIED (5), or DISSOLVED_PARTNERSHIP (7), got: {v}"
            )
        return v


class ECH0011CountryInfo(BaseModel):
    """eCH-0011 Country info for nationality.

    Represents a single nationality with country and validity date.

    XML Schema: Part of eCH-0011 nationalityDataType
    """

    country: ECH0008Country = Field(
        ...,
        description="Country of nationality (required)"
    )
    nationality_valid_from: Optional[date] = Field(
        None,
        description="Date from which nationality is valid"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}countryInfo')
        else:
            elem = ET.Element(f'{{{namespace}}}countryInfo')

        # Country (required) - wrapper in eCH-0011, content from eCH-0008
        country_wrapper = ET.SubElement(elem, f'{{{namespace}}}country')
        # Add eCH-0008 country content to the wrapper
        for child in self.country.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0008/3'):
            country_wrapper.append(child)

        # Valid from date (optional)
        if self.nationality_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}nationalityValidFrom')
            valid_elem.text = self.nationality_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011CountryInfo':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (countryInfo container)
            namespace: XML namespace URI

        Returns:
            Parsed country info object

        Raises:
            ValueError: If required fields missing
        """
        ns = {
            'eCH-0011': namespace,
            'eCH-0008': 'http://www.ech.ch/xmlns/eCH-0008/3'
        }

        # Country (required) - wrapper in eCH-0011, content from eCH-0008
        country_elem = elem.find('eCH-0011:country', ns)
        if country_elem is None:
            raise ValueError("Missing required field: country")
        # Parse eCH-0008 country content from within the eCH-0011 wrapper
        country = ECH0008Country.from_xml(country_elem, 'http://www.ech.ch/xmlns/eCH-0008/3')

        # Valid from (optional)
        valid_elem = elem.find('eCH-0011:nationalityValidFrom', ns)
        valid_from = date.fromisoformat(valid_elem.text.strip()) if valid_elem is not None and valid_elem.text else None

        return cls(
            country=country,
            nationality_valid_from=valid_from
        )


class ECH0011NationalityData(BaseModel):
    """eCH-0011 Nationality data.

    Contains nationality status and list of nationalities.

    XML Schema: eCH-0011 nationalityDataType
    """

    nationality_status: NationalityStatus = Field(
        ...,
        description=(
            "Nationality status (required):\n"
            "0=unknown/not specified,\n"
            "1=Swiss citizen,\n"
            "2=foreign national"
        )
    )
    country_info: List[ECH0011CountryInfo] = Field(
        default_factory=list,
        description="List of nationalities (can be multiple)"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
        element_name: str = 'nationalityData',
        wrapper_namespace: Optional[str] = None
    ) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of the element to create
            wrapper_namespace: Optional wrapper namespace (for cross-schema composition)

        Returns:
            XML Element

        Note:
            When wrapper_namespace is provided, creates:
            <wrapper_namespace:element_name>
              <namespace:nationalityData>...</namespace:nationalityData>
            </wrapper_namespace:element_name>
        """
        # Handle wrapper namespace (for eCH-0020 cross-schema composition)
        # When wrapper_namespace is provided, create element in wrapper namespace
        # Content (children) will still use the original namespace
        if wrapper_namespace is not None and parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_namespace}}}{element_name}')
        else:
            # Standard behavior - create in own namespace
            if parent is not None:
                elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
            else:
                elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Nationality status (required)
        status_elem = ET.SubElement(elem, f'{{{namespace}}}nationalityStatus')
        status_elem.text = self.nationality_status

        # Country info list (optional, unbounded)
        for country_info in self.country_info:
            country_info.to_xml(elem, namespace)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011NationalityData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (nationalityData container)
            namespace: XML namespace URI

        Returns:
            Parsed nationality data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Nationality status (required)
        status_elem = elem.find('eCH-0011:nationalityStatus', ns)
        if status_elem is None or not status_elem.text:
            raise ValueError("Missing required field: nationalityStatus")

        # Country info list (optional, multiple)
        country_infos = []
        for country_elem in elem.findall('eCH-0011:countryInfo', ns):
            country_infos.append(ECH0011CountryInfo.from_xml(country_elem, namespace))

        return cls(
            nationality_status=status_elem.text.strip(),
            country_info=country_infos
        )


class ECH0011PlaceOfOrigin(BaseModel):
    """eCH-0011 Place of origin (Heimatort).

    Represents a Swiss place of origin (Bürgerort/Heimatort) for Swiss citizens.

    XML Schema: eCH-0011 placeOfOriginType
    """

    origin_name: str = Field(
        ...,
        max_length=50,
        description="Name of place of origin (required)"
    )
    canton: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Canton abbreviation (required)"
    )
    place_of_origin_id: Optional[int] = Field(
        None,
        description="BFS place of origin ID (optional)"
    )
    history_municipality_id: Optional[str] = Field(
        None,
        max_length=12,
        description="Historical municipality ID (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}placeOfOrigin')
        else:
            elem = ET.Element(f'{{{namespace}}}placeOfOrigin')

        # Origin name (required)
        name_elem = ET.SubElement(elem, f'{{{namespace}}}originName')
        name_elem.text = self.origin_name

        # Canton (required)
        canton_elem = ET.SubElement(elem, f'{{{namespace}}}canton')
        canton_elem.text = self.canton

        # Place of origin ID (optional)
        if self.place_of_origin_id:
            id_elem = ET.SubElement(elem, f'{{{namespace}}}placeOfOriginId')
            id_elem.text = str(self.place_of_origin_id)

        # History municipality ID (optional)
        if self.history_municipality_id:
            hist_elem = ET.SubElement(elem, f'{{{namespace}}}historyMunicipalityId')
            hist_elem.text = self.history_municipality_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011PlaceOfOrigin':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (placeOfOrigin container)
            namespace: XML namespace URI

        Returns:
            Parsed place of origin object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Origin name (required)
        name_elem = elem.find('eCH-0011:originName', ns)
        if name_elem is None or not name_elem.text:
            raise ValueError("Missing required field: originName")

        # Canton (required)
        canton_elem = elem.find('eCH-0011:canton', ns)
        if canton_elem is None or not canton_elem.text:
            raise ValueError("Missing required field: canton")

        # Place of origin ID (optional)
        id_elem = elem.find('eCH-0011:placeOfOriginId', ns)
        origin_id = int(id_elem.text.strip()) if id_elem is not None and id_elem.text else None

        # History municipality ID (optional)
        hist_elem = elem.find('eCH-0011:historyMunicipalityId', ns)
        hist_id = hist_elem.text.strip() if hist_elem is not None and hist_elem.text else None

        return cls(
            origin_name=name_elem.text.strip(),
            canton=canton_elem.text.strip(),
            place_of_origin_id=origin_id,
            history_municipality_id=hist_id
        )


class ECH0011ResidencePermitData(BaseModel):
    """eCH-0011 Residence permit data.

    Contains residence permit information for foreign nationals.

    XML Schema: eCH-0011 residencePermitDataType
    """

    residence_permit: ResidencePermitType = Field(
        ...,
        description="Residence permit type per eCH-0006 (e.g., L='01', B='02', C='03', F='06')"
    )
    residence_permit_valid_from: Optional[date] = Field(
        None,
        description="Permit valid from date"
    )
    residence_permit_valid_till: Optional[date] = Field(
        None,
        description="Permit valid until date"
    )
    entry_date: Optional[date] = Field(
        None,
        description="Date of entry to Switzerland"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
        element_name: str = 'residencePermit',
        wrapper_namespace: Optional[str] = None
    ) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of the element to create
            wrapper_namespace: Optional wrapper namespace (for cross-schema composition)

        Returns:
            XML Element

        Note:
            When wrapper_namespace is provided, creates:
            <wrapper_namespace:element_name>
              <namespace:residencePermit>...</namespace:residencePermit>
            </wrapper_namespace:element_name>
        """
        # Handle wrapper namespace (for eCH-0020 cross-schema composition)
        # When wrapper_namespace is provided, create element in wrapper namespace
        # Content (children) will still use the original namespace
        if wrapper_namespace is not None and parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_namespace}}}{element_name}')
        else:
            # Standard behavior - create in own namespace
            if parent is not None:
                elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
            else:
                elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Residence permit (required)
        permit_elem = ET.SubElement(elem, f'{{{namespace}}}residencePermit')
        permit_elem.text = self.residence_permit

        # Valid from (optional)
        if self.residence_permit_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}residencePermitValidFrom')
            from_elem.text = self.residence_permit_valid_from.isoformat()

        # Valid till (optional)
        if self.residence_permit_valid_till:
            till_elem = ET.SubElement(elem, f'{{{namespace}}}residencePermitValidTill')
            till_elem.text = self.residence_permit_valid_till.isoformat()

        # Entry date (optional)
        if self.entry_date:
            entry_elem = ET.SubElement(elem, f'{{{namespace}}}entryDate')
            entry_elem.text = self.entry_date.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011ResidencePermitData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (residencePermit container)
            namespace: XML namespace URI

        Returns:
            Parsed residence permit data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Residence permit (required)
        permit_elem = elem.find('eCH-0011:residencePermit', ns)
        if permit_elem is None or not permit_elem.text:
            raise ValueError("Missing required field: residencePermit")

        # Valid from (optional)
        from_elem = elem.find('eCH-0011:residencePermitValidFrom', ns)
        valid_from = date.fromisoformat(from_elem.text.strip()) if from_elem is not None and from_elem.text else None

        # Valid till (optional)
        till_elem = elem.find('eCH-0011:residencePermitValidTill', ns)
        valid_till = date.fromisoformat(till_elem.text.strip()) if till_elem is not None and till_elem.text else None

        # Entry date (optional)
        entry_elem = elem.find('eCH-0011:entryDate', ns)
        entry = date.fromisoformat(entry_elem.text.strip()) if entry_elem is not None and entry_elem.text else None

        return cls(
            residence_permit=permit_elem.text.strip(),
            residence_permit_valid_from=valid_from,
            residence_permit_valid_till=valid_till,
            entry_date=entry
        )


class ECH0011DeathPeriod(BaseModel):
    """eCH-0011 Death period.

    Represents the period of death (from date, optionally to date).

    XML Schema: eCH-0011 deathPeriodType
    """

    date_from: date = Field(
        ...,
        description="Death date or start of death period (required)"
    )
    date_to: Optional[date] = Field(
        None,
        description="End of death period (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI

        Returns:
            XML Element
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}deathPeriod')
        else:
            elem = ET.Element(f'{{{namespace}}}deathPeriod')

        # Date from (required)
        from_elem = ET.SubElement(elem, f'{{{namespace}}}dateFrom')
        from_elem.text = self.date_from.isoformat()

        # Date to (optional)
        if self.date_to:
            to_elem = ET.SubElement(elem, f'{{{namespace}}}dateTo')
            to_elem.text = self.date_to.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011DeathPeriod':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (deathPeriod container)
            namespace: XML namespace URI

        Returns:
            Parsed death period object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Date from (required)
        from_elem = elem.find('eCH-0011:dateFrom', ns)
        if from_elem is None or not from_elem.text:
            raise ValueError("Missing required field: dateFrom")
        date_from = date.fromisoformat(from_elem.text.strip())

        # Date to (optional)
        to_elem = elem.find('eCH-0011:dateTo', ns)
        date_to = date.fromisoformat(to_elem.text.strip()) if to_elem is not None and to_elem.text else None

        return cls(
            date_from=date_from,
            date_to=date_to
        )


class ECH0011DeathData(BaseModel):
    """eCH-0011 Death data.

    Contains death information including period and optional place.

    XML Schema: eCH-0011 deathDataType
    """

    death_period: ECH0011DeathPeriod = Field(
        ...,
        description="Death period (required)"
    )
    place_of_death: Optional[ECH0011GeneralPlace] = Field(
        None,
        description="Place of death (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'deathData',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace for content elements
            element_name: Name of wrapper element (default: 'deathData')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)

        Returns:
            XML Element
        """
        # Use wrapper_namespace for wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Death period (required)
        self.death_period.to_xml(elem, namespace)

        # Place of death (optional)
        if self.place_of_death:
            self.place_of_death.to_xml(elem, namespace, 'placeOfDeath')

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011DeathData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (deathData container)
            namespace: XML namespace URI

        Returns:
            Parsed death data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {'eCH-0011': namespace}

        # Death period (required)
        period_elem = elem.find('eCH-0011:deathPeriod', ns)
        if period_elem is None:
            raise ValueError("Missing required field: deathPeriod")
        death_period = ECH0011DeathPeriod.from_xml(period_elem, namespace)

        # Place of death (optional)
        place_elem = elem.find('eCH-0011:placeOfDeath', ns)
        place = ECH0011GeneralPlace.from_xml(place_elem, namespace) if place_elem is not None else None

        return cls(
            death_period=death_period,
            place_of_death=place
        )


class ECH0011PartnerIdOrganisation(BaseModel):
    """eCH-0011 Partner ID organization.

    Used in contactDataType as one of the choice options for representing
    an organization contact with local and optional other person IDs.

    XML Schema: eCH-0011 partnerIdOrganisationType
    XSD Lines: 438-443
    """

    local_person_id: ECH0044NamedPersonId = Field(
        ...,
        description="Local person ID (required)"
    )
    other_person_id: List[ECH0044NamedPersonId] = Field(
        default_factory=list,
        description="Other person IDs (optional, unbounded)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
        arbitrary_types_allowed=True
    )

    def to_xml(self, parent: ET.Element, tag: str = "partnerIdOrganisation",
               nsmap: Optional[Dict[str, str]] = None) -> ET.Element:
        """Convert to XML element.

        Args:
            parent: Parent XML element
            tag: Tag name for this element
            nsmap: Namespace map (optional)

        Returns:
            Created XML element
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0044": "http://www.ech.ch/xmlns/eCH-0044/4"
            }

        elem = ET.SubElement(parent, f"{{{nsmap[None]}}}{tag}")

        # Add local person ID (required)
        # The localPersonId element is in eCH-0011 namespace, but its children are in eCH-0044
        local_elem = ET.SubElement(elem, f"{{{nsmap[None]}}}localPersonId")
        category_elem = ET.SubElement(local_elem, f"{{{nsmap['eCH-0044']}}}personIdCategory")
        category_elem.text = self.local_person_id.person_id_category
        id_elem = ET.SubElement(local_elem, f"{{{nsmap['eCH-0044']}}}personId")
        id_elem.text = self.local_person_id.person_id

        # Add other person IDs (optional, multiple)
        # Same structure: otherPersonId element in eCH-0011, children in eCH-0044
        for other_id in self.other_person_id:
            other_elem = ET.SubElement(elem, f"{{{nsmap[None]}}}otherPersonId")
            other_category = ET.SubElement(other_elem, f"{{{nsmap['eCH-0044']}}}personIdCategory")
            other_category.text = other_id.person_id_category
            other_id_elem = ET.SubElement(other_elem, f"{{{nsmap['eCH-0044']}}}personId")
            other_id_elem.text = other_id.person_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, nsmap: Optional[Dict[str, str]] = None) -> 'ECH0011PartnerIdOrganisation':
        """Create instance from XML element.

        Args:
            elem: XML element (partnerIdOrganisation)
            nsmap: Namespace map (optional)

        Returns:
            ECH0011PartnerIdOrganisation instance
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0044": "http://www.ech.ch/xmlns/eCH-0044/4"
            }

        ns = nsmap[None]

        # Parse local person ID (required)
        # The localPersonId element is in eCH-0011 namespace, children in eCH-0044
        local_person_id_elem = elem.find(f"{{{ns}}}localPersonId")
        if local_person_id_elem is None:
            raise ValueError("Missing required localPersonId in partnerIdOrganisation")

        # Parse the namedPersonId structure manually
        ech0044_ns = {'eCH-0044': nsmap['eCH-0044']}
        category_elem = local_person_id_elem.find('eCH-0044:personIdCategory', ech0044_ns)
        id_elem = local_person_id_elem.find('eCH-0044:personId', ech0044_ns)

        if category_elem is None or id_elem is None:
            raise ValueError("Missing personIdCategory or personId in localPersonId")

        local_person_id = ECH0044NamedPersonId(
            person_id_category=category_elem.text,
            person_id=id_elem.text
        )

        # Parse other person IDs (optional, multiple)
        other_person_ids = []
        for other_id_elem in elem.findall(f"{{{ns}}}otherPersonId"):
            other_category = other_id_elem.find('eCH-0044:personIdCategory', ech0044_ns)
            other_id = other_id_elem.find('eCH-0044:personId', ech0044_ns)
            if other_category is not None and other_id is not None:
                other_person_ids.append(ECH0044NamedPersonId(
                    person_id_category=other_category.text,
                    person_id=other_id.text
                ))

        return cls(
            local_person_id=local_person_id,
            other_person_id=other_person_ids
        )


class ECH0011ContactData(BaseModel):
    """eCH-0011 Contact data.

    Represents contact information for a person, including optional contact
    person/organization and required contact address.

    The XSD defines a choice (minOccurs=0) of three identification variants:
    - personIdentification (full person identification)
    - personIdentificationPartner (light person identification)
    - partnerIdOrganisation (organization with person IDs)

    At most one of these can be set.

    XML Schema: eCH-0011 contactDataType
    XSD Lines: 262-272
    """

    # Optional choice: contact person OR partner OR organization (at most one)
    contact_person: Optional[ECH0044PersonIdentification] = Field(
        None,
        description="Contact person identification (full) - choice 1 of 3"
    )
    contact_person_partner: Optional[ECH0044PersonIdentificationLight] = Field(
        None,
        description="Contact person partner (light) - choice 2 of 3"
    )
    contact_organization: Optional[ECH0011PartnerIdOrganisation] = Field(
        None,
        description="Contact organization - choice 3 of 3"
    )

    # Required contact address
    contact_address: ECH0010MailAddress = Field(
        ...,
        description="Contact mailing address (required)"
    )

    # Optional validity dates
    contact_valid_from: Optional[date] = Field(
        None,
        description="Contact valid from date"
    )
    contact_valid_till: Optional[date] = Field(
        None,
        description="Contact valid until date"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
        arbitrary_types_allowed=True
    )

    @model_validator(mode='after')
    def validate_contact_choice(self) -> 'ECH0011ContactData':
        """Validate that at most one contact identification is set (XSD choice constraint)."""
        contact_fields = [
            self.contact_person,
            self.contact_person_partner,
            self.contact_organization
        ]
        set_count = sum(1 for field in contact_fields if field is not None)

        if set_count > 1:
            raise ValueError(
                f"contactDataType allows at most one contact identification, but {set_count} are set"
            )

        return self

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'contactData',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI for content elements
            element_name: Name of wrapper element (default: 'contactData')
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

        # Optional choice: at most one of three variants - wrapper in eCH-0011, content in eCH-0044
        if self.contact_person:
            self.contact_person.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0044/4',  # Content namespace
                element_name='personIdentification',
                wrapper_namespace=namespace  # Wrapper in eCH-0011
            )
        elif self.contact_person_partner:
            self.contact_person_partner.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0044/4',  # Content namespace
                element_name='personIdentificationPartner',
                wrapper_namespace=namespace  # Wrapper in eCH-0011
            )
        elif self.contact_organization:
            self.contact_organization.to_xml(
                parent=elem,
                tag='partnerIdOrganisation',
                nsmap={
                    None: namespace,
                    'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'
                }
            )

        # Contact address (required) - wrapper in eCH-0011, content in eCH-0010
        self.contact_address.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0010/5',  # Content namespace
            element_name='contactAddress',
            wrapper_namespace=namespace  # Wrapper in eCH-0011
        )

        # Valid from (optional)
        if self.contact_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}contactValidFrom')
            from_elem.text = self.contact_valid_from.isoformat()

        # Valid till (optional)
        if self.contact_valid_till:
            till_elem = ET.SubElement(elem, f'{{{namespace}}}contactValidTill')
            till_elem.text = self.contact_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011ContactData':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (contactData container)
            namespace: XML namespace URI

        Returns:
            Parsed contact data object

        Raises:
            ValueError: If required fields missing
        """
        ns = {
            'eCH-0011': namespace,
            'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4',
            'eCH-0010': 'http://www.ech.ch/xmlns/eCH-0010/5'
        }

        # Parse optional choice (at most one of three variants)
        contact_person = None
        contact_person_partner = None
        contact_organization = None

        # Variant 1: personIdentification (full) - wrapper in eCH-0011, content in eCH-0044
        person_elem = elem.find('eCH-0011:personIdentification', ns)
        if person_elem is not None:
            contact_person = ECH0044PersonIdentification.from_xml(
                person_elem,
                'http://www.ech.ch/xmlns/eCH-0044/4'
            )

        # Variant 2: personIdentificationPartner (light) - wrapper in eCH-0011, content in eCH-0044
        partner_elem = elem.find('eCH-0011:personIdentificationPartner', ns)
        if partner_elem is not None:
            contact_person_partner = ECH0044PersonIdentificationLight.from_xml(
                partner_elem,
                'http://www.ech.ch/xmlns/eCH-0044/4'
            )

        # Variant 3: partnerIdOrganisation
        org_elem = elem.find(f'{{{namespace}}}partnerIdOrganisation')
        if org_elem is not None:
            contact_organization = ECH0011PartnerIdOrganisation.from_xml(
                org_elem,
                nsmap={
                    None: namespace,
                    'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'
                }
            )

        # Contact address (required) - contactAddress element in eCH-0011, content in eCH-0010
        address_elem = elem.find('eCH-0011:contactAddress', ns)
        if address_elem is None:
            raise ValueError("Missing required field: contactAddress")
        contact_address = ECH0010MailAddress.from_xml(address_elem, 'http://www.ech.ch/xmlns/eCH-0010/5')

        # Valid from (optional)
        from_elem = elem.find('eCH-0011:contactValidFrom', ns)
        valid_from = date.fromisoformat(from_elem.text.strip()) if from_elem is not None and from_elem.text else None

        # Valid till (optional)
        till_elem = elem.find('eCH-0011:contactValidTill', ns)
        valid_till = date.fromisoformat(till_elem.text.strip()) if till_elem is not None and till_elem.text else None

        return cls(
            contact_person=contact_person,
            contact_person_partner=contact_person_partner,
            contact_organization=contact_organization,
            contact_address=contact_address,
            contact_valid_from=valid_from,
            contact_valid_till=valid_till
        )


class ECH0011DestinationType(BaseModel):
    """eCH-0011 Destination (arrival/departure location).

    Extension of generalPlaceType with optional mail address.
    Used for representing where a person comes from or goes to.

    XML Schema: eCH-0011 destinationType
    """

    # Inherits generalPlaceType fields (choice)
    unknown: Optional[bool] = Field(
        None,
        description="True if destination is unknown"
    )
    swiss_municipality: Optional[ECH0007Municipality] = Field(
        None,
        description="Swiss municipality (if applicable)"
    )
    foreign_country: Optional[ECH0008Country] = Field(
        None,
        description="Foreign country (if applicable)"
    )
    foreign_town: Optional[str] = Field(
        None,
        max_length=100,
        description="Town name in foreign country"
    )

    # Extension: optional mail address (addressInformationType per XSD line 330)
    mail_address: Optional[ECH0010AddressInformation] = Field(
        None,
        description="Mail address at destination (addressInformationType, not mailAddressType - just address fields, no person/org wrapper)"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
        element_name: str = 'comesFrom',
        wrapper_namespace: Optional[str] = None
    ) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element (comesFrom/goesTo)
            wrapper_namespace: Optional wrapper namespace (for cross-schema composition)

        Returns:
            XML Element

        Raises:
            ValueError: If multiple or no place types are set

        Note:
            When wrapper_namespace is provided, creates:
            <wrapper_namespace:element_name>
              <namespace:comesFrom/goesTo>...</namespace:comesFrom/goesTo>
            </wrapper_namespace:element_name>
        """
        # Handle wrapper namespace (for eCH-0020 cross-schema composition)
        # When wrapper_namespace is provided, create element in wrapper namespace
        # Content (children) will still use the original namespace
        if wrapper_namespace is not None and parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_namespace}}}{element_name}')
        else:
            # Standard behavior - create in own namespace
            if parent is not None:
                elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
            else:
                elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Validate choice (from generalPlaceType)
        place_count = sum([
            self.unknown is True,
            self.swiss_municipality is not None,
            self.foreign_country is not None
        ])

        if place_count == 0:
            raise ValueError("Must specify one of: unknown, swiss_municipality, or foreign_country")
        if place_count > 1:
            raise ValueError("Can only specify one of: unknown, swiss_municipality, or foreign_country")

        # Place type (same as generalPlaceType)
        if self.unknown:
            unknown_elem = ET.SubElement(elem, f'{{{namespace}}}unknown')
            unknown_elem.text = "0"
        elif self.swiss_municipality:
            # Swiss municipality - swissTown wrapper in eCH-0011, content in eCH-0007
            swiss_town_elem = ET.SubElement(elem, f'{{{namespace}}}swissTown')
            swiss_muni = self.swiss_municipality.swiss_municipality
            ech0007_ns = 'http://www.ech.ch/xmlns/eCH-0007/5'
            if swiss_muni.municipality_id:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}municipalityId').text = swiss_muni.municipality_id
            ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}municipalityName').text = swiss_muni.municipality_name
            if swiss_muni.canton_abbreviation:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}cantonAbbreviation').text = swiss_muni.canton_abbreviation.value
            if swiss_muni.history_municipality_id:
                ET.SubElement(swiss_town_elem, f'{{{ech0007_ns}}}historyMunicipalityId').text = swiss_muni.history_municipality_id
        elif self.foreign_country:
            # Foreign country - wrapper in eCH-0011, content in eCH-0008
            foreign_elem = ET.SubElement(elem, f'{{{namespace}}}foreignCountry')
            self.foreign_country.to_xml(
                parent=foreign_elem,
                namespace='http://www.ech.ch/xmlns/eCH-0008/3',  # Content namespace
                element_name='country',
                wrapper_namespace=namespace  # Wrapper in eCH-0011
            )
            if self.foreign_town:
                town_elem = ET.SubElement(foreign_elem, f'{{{namespace}}}town')
                town_elem.text = self.foreign_town

        # Mail address (extension, optional) - wrapper in eCH-0011, content in eCH-0010
        if self.mail_address:
            self.mail_address.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0010/5',  # Content namespace
                element_name='mailAddress',
                wrapper_namespace=namespace  # Wrapper in eCH-0011
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011DestinationType':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (destination container)
            namespace: XML namespace URI

        Returns:
            Parsed destination object
        """
        ns = {
            'eCH-0011': namespace,
            'eCH-0007': 'http://www.ech.ch/xmlns/eCH-0007/5',
            'eCH-0008': 'http://www.ech.ch/xmlns/eCH-0008/3',
            'eCH-0010': 'http://www.ech.ch/xmlns/eCH-0010/5'
        }

        # Check for unknown
        unknown_elem = elem.find('eCH-0011:unknown', ns)
        unknown = unknown_elem is not None

        # Check for Swiss municipality - swissTown element in eCH-0011 namespace
        # Parse swissMunicipalityType content directly (municipalityId, municipalityName, etc.)
        swiss_elem = elem.find('eCH-0011:swissTown', ns)
        swiss_mun = None
        if swiss_elem is not None:
            from openmun_ech.ech0007 import ECH0007SwissMunicipality
            mun_id_elem = swiss_elem.find('eCH-0007:municipalityId', ns)
            mun_name_elem = swiss_elem.find('eCH-0007:municipalityName', ns)
            canton_elem = swiss_elem.find('eCH-0007:cantonAbbreviation', ns)
            hist_id_elem = swiss_elem.find('eCH-0007:historyMunicipalityId', ns)

            if mun_name_elem is not None and mun_name_elem.text:
                swiss_municipality = ECH0007SwissMunicipality(
                    municipality_id=mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None,
                    municipality_name=mun_name_elem.text.strip(),
                    canton_abbreviation=canton_elem.text.strip() if canton_elem is not None and canton_elem.text else None,
                    history_municipality_id=hist_id_elem.text.strip() if hist_id_elem is not None and hist_id_elem.text else None
                )
                swiss_mun = ECH0007Municipality(swiss_municipality=swiss_municipality)

        # Check for foreign country
        foreign_container = elem.find('eCH-0011:foreignCountry', ns)
        foreign_country = None
        foreign_town = None

        if foreign_container is not None:
            # country element is in eCH-0011 namespace (wrapper), content is in eCH-0008
            country_elem = foreign_container.find('eCH-0011:country', ns)
            if country_elem is not None:
                foreign_country = ECH0008Country.from_xml(country_elem, 'http://www.ech.ch/xmlns/eCH-0008/3')

            town_elem = foreign_container.find('eCH-0011:town', ns)
            foreign_town = town_elem.text.strip() if town_elem is not None and town_elem.text else None

        # Mail address (optional) - wrapper in eCH-0011, content in eCH-0010
        mail_elem = elem.find('eCH-0011:mailAddress', ns)
        mail_address = None
        if mail_elem is not None:
            # Parse addressInformationType content (no wrapper inside mailAddress)
            mail_address = ECH0010AddressInformation.from_xml(mail_elem, 'http://www.ech.ch/xmlns/eCH-0010/5')

        return cls(
            unknown=unknown if unknown else None,
            swiss_municipality=swiss_mun,
            foreign_country=foreign_country,
            foreign_town=foreign_town,
            mail_address=mail_address
        )


class ECH0011DwellingAddress(BaseModel):
    """eCH-0011 Dwelling address.

    Represents a dwelling address with building/dwelling IDs, household info,
    and Swiss address.

    XML Schema: eCH-0011 dwellingAddressType
    XSD Lines: 371-380
    """

    # Building and dwelling identifiers (optional)
    egid: Optional[int] = Field(
        None,
        ge=1,
        le=999999999,
        description="Federal Building ID (Eidgenössischer Gebäudeidentifikator)"
    )
    ewid: Optional[int] = Field(
        None,
        ge=1,
        le=999,
        description="Federal Dwelling ID (Eidgenössischer Wohnungsidentifikator)"
    )
    household_id: Optional[str] = Field(
        None,
        description="Household identifier (token)"
    )

    # Address (required) - uses eCH-0010 swissAddressInformationType
    address: 'ECH0010SwissAddressInformation' = Field(
        ...,
        description="Swiss address information (required)"
    )

    # Household type (required)
    type_of_household: TypeOfHousehold = Field(
        ...,
        description="Type of household: 0=unknown, 1=single, 2=family, 3=non-family (required)"
    )

    # Moving date (optional)
    moving_date: Optional[date] = Field(
        None,
        description="Date of moving into dwelling"
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
        element_name: str = 'dwellingAddress',
        wrapper_namespace: Optional[str] = None
    ) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of the element to create
            wrapper_namespace: Optional wrapper namespace (for cross-schema composition)

        Returns:
            XML Element

        Note:
            When wrapper_namespace is provided, creates:
            <wrapper_namespace:element_name>
              <namespace:dwellingAddress>...</namespace:dwellingAddress>
            </wrapper_namespace:element_name>
        """
        # Handle wrapper namespace (for eCH-0020 cross-schema composition)
        if wrapper_namespace is not None and parent is not None:
            wrapper = ET.SubElement(parent, f'{{{wrapper_namespace}}}{element_name}')
            elem = ET.SubElement(wrapper, f'{{{namespace}}}dwellingAddress')
        else:
            # Standard behavior
            if parent is not None:
                elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
            else:
                elem = ET.Element(f'{{{namespace}}}{element_name}')

        # EGID (optional)
        if self.egid is not None:
            egid_elem = ET.SubElement(elem, f'{{{namespace}}}EGID')
            egid_elem.text = str(self.egid)

        # EWID (optional)
        if self.ewid is not None:
            ewid_elem = ET.SubElement(elem, f'{{{namespace}}}EWID')
            ewid_elem.text = str(self.ewid)

        # Household ID (optional)
        if self.household_id:
            hh_elem = ET.SubElement(elem, f'{{{namespace}}}householdID')
            hh_elem.text = self.household_id

        # Address (required) - eCH-0010 swissAddressInformationType
        address_elem = ET.SubElement(elem, f'{{{namespace}}}address')
        self.address.to_xml(
            parent=address_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0010/5'
        )

        # Type of household (required)
        type_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfHousehold')
        type_elem.text = self.type_of_household

        # Moving date (optional)
        if self.moving_date:
            date_elem = ET.SubElement(elem, f'{{{namespace}}}movingDate')
            date_elem.text = self.moving_date.isoformat()

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011DwellingAddress':
        """Import from eCH-0011 XML."""
        ns = {
            'eCH-0011': namespace,
            'eCH-0010': 'http://www.ech.ch/xmlns/eCH-0010/5'
        }

        # EGID (optional)
        egid_elem = elem.find('eCH-0011:EGID', ns)
        egid = int(egid_elem.text.strip()) if egid_elem is not None and egid_elem.text else None

        # EWID (optional)
        ewid_elem = elem.find('eCH-0011:EWID', ns)
        ewid = int(ewid_elem.text.strip()) if ewid_elem is not None and ewid_elem.text else None

        # Household ID (optional)
        hh_elem = elem.find('eCH-0011:householdID', ns)
        household_id = hh_elem.text.strip() if hh_elem is not None and hh_elem.text else None

        # Address (required) - address element in eCH-0011, content in eCH-0010
        from openmun_ech.ech0010 import ECH0010SwissAddressInformation
        address_elem = elem.find('eCH-0011:address', ns)
        if address_elem is None:
            raise ValueError("Missing required field: address")
        address = ECH0010SwissAddressInformation.from_xml(address_elem, 'http://www.ech.ch/xmlns/eCH-0010/5')

        # Type of household (required)
        type_elem = elem.find('eCH-0011:typeOfHousehold', ns)
        if type_elem is None or not type_elem.text:
            raise ValueError("Missing required field: typeOfHousehold")
        type_of_household = type_elem.text.strip()

        # Moving date (optional)
        date_elem = elem.find('eCH-0011:movingDate', ns)
        moving_date = date.fromisoformat(date_elem.text.strip()) if date_elem is not None and date_elem.text else None

        return cls(
            egid=egid,
            ewid=ewid,
            household_id=household_id,
            address=address,
            type_of_household=type_of_household,
            moving_date=moving_date
        )


class ECH0011ResidenceData(BaseModel):
    """eCH-0011 Residence data.

    Represents residence information including municipality, dates, origin,
    destination, and dwelling details.

    XML Schema: eCH-0011 residenceDataType
    XSD Lines: 381-390
    """

    # Reporting municipality (required)
    reporting_municipality: ECH0007Municipality = Field(
        ...,
        description="Municipality where person is registered (required)"
    )

    # Arrival date (required)
    arrival_date: date = Field(
        ...,
        description="Date of arrival in municipality (required)"
    )

    # Comes from (optional)
    comes_from: Optional[ECH0011DestinationType] = Field(
        None,
        description="Origin/previous location (optional)"
    )

    # Dwelling address (required)
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        description="Dwelling address information (required)"
    )

    # Departure date (optional)
    departure_date: Optional[date] = Field(
        None,
        description="Date of departure from municipality (optional)"
    )

    # Goes to (optional)
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        description="Destination/next location (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'mainResidence') -> ET.Element:
        """Export to eCH-0011 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Reporting municipality (required) - swissMunicipalityType per XSD
        # XSD: <xs:element name="reportingMunicipality" type="eCH-0007:swissMunicipalityType"/>
        # Content is direct children (municipalityId, municipalityName, cantonAbbreviation)
        reporting_muni_elem = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
        ech0007_ns = 'http://www.ech.ch/xmlns/eCH-0007/5'
        swiss_muni = self.reporting_municipality.swiss_municipality

        # Add swissMunicipalityType fields directly (no wrapper element)
        if swiss_muni.municipality_id:
            ET.SubElement(reporting_muni_elem, f'{{{ech0007_ns}}}municipalityId').text = swiss_muni.municipality_id
        ET.SubElement(reporting_muni_elem, f'{{{ech0007_ns}}}municipalityName').text = swiss_muni.municipality_name
        if swiss_muni.canton_abbreviation:
            ET.SubElement(reporting_muni_elem, f'{{{ech0007_ns}}}cantonAbbreviation').text = swiss_muni.canton_abbreviation.value
        if swiss_muni.history_municipality_id:
            ET.SubElement(reporting_muni_elem, f'{{{ech0007_ns}}}historyMunicipalityId').text = swiss_muni.history_municipality_id

        # Arrival date (required)
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Comes from (optional)
        if self.comes_from:
            self.comes_from.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='comesFrom'
            )

        # Dwelling address (required)
        self.dwelling_address.to_xml(parent=elem, namespace=namespace)

        # Departure date (optional)
        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        # Goes to (optional)
        if self.goes_to:
            self.goes_to.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='goesTo'
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011ResidenceData':
        """Import from eCH-0011 XML."""
        ns = {
            'eCH-0011': namespace,
            'eCH-0007': 'http://www.ech.ch/xmlns/eCH-0007/5'
        }

        # Reporting municipality (required) - reportingMunicipality element in eCH-0011 namespace
        mun_elem = elem.find('eCH-0011:reportingMunicipality', ns)
        if mun_elem is None:
            raise ValueError("Missing required field: reportingMunicipality")

        # Parse swissMunicipalityType content from within reportingMunicipality element
        from openmun_ech.ech0007 import ECH0007SwissMunicipality
        mun_id_elem = mun_elem.find('eCH-0007:municipalityId', ns)
        mun_name_elem = mun_elem.find('eCH-0007:municipalityName', ns)
        canton_elem = mun_elem.find('eCH-0007:cantonAbbreviation', ns)
        hist_id_elem = mun_elem.find('eCH-0007:historyMunicipalityId', ns)

        if mun_name_elem is None or not mun_name_elem.text:
            raise ValueError("Missing required field: municipalityName in reportingMunicipality")

        swiss_muni = ECH0007SwissMunicipality(
            municipality_id=mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None,
            municipality_name=mun_name_elem.text.strip(),
            canton_abbreviation=canton_elem.text.strip() if canton_elem is not None and canton_elem.text else None,
            history_municipality_id=hist_id_elem.text.strip() if hist_id_elem is not None and hist_id_elem.text else None
        )
        reporting_municipality = ECH0007Municipality(swiss_municipality=swiss_muni)

        # Arrival date (required)
        arrival_elem = elem.find('eCH-0011:arrivalDate', ns)
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("Missing required field: arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text.strip())

        # Comes from (optional)
        comes_elem = elem.find('eCH-0011:comesFrom', ns)
        comes_from = ECH0011DestinationType.from_xml(comes_elem, namespace) if comes_elem is not None else None

        # Dwelling address (required)
        dwelling_elem = elem.find('eCH-0011:dwellingAddress', ns)
        if dwelling_elem is None:
            raise ValueError("Missing required field: dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem, namespace)

        # Departure date (optional)
        departure_elem = elem.find('eCH-0011:departureDate', ns)
        departure_date = date.fromisoformat(departure_elem.text.strip()) if departure_elem is not None and departure_elem.text else None

        # Goes to (optional)
        goes_elem = elem.find('eCH-0011:goesTo', ns)
        goes_to = ECH0011DestinationType.from_xml(goes_elem, namespace) if goes_elem is not None else None

        return cls(
            reporting_municipality=reporting_municipality,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0011MainResidence(BaseModel):
    """eCH-0011 Main residence.

    Represents a person's main residence with optional secondary residences.

    XML Schema: eCH-0011 mainResidenceType
    XSD Lines: 391-396
    """

    # Main residence (required)
    main_residence: ECH0011ResidenceData = Field(
        ...,
        description="Main residence data (required)"
    )

    # Secondary residences (optional, unbounded)
    secondary_residence: List[ECH0007Municipality] = Field(
        default_factory=list,
        description="List of secondary residence municipalities (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'hasMainResidence',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace for content elements
            element_name: Name of wrapper element (default: 'hasMainResidence')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)
        """
        # Use wrapper_namespace for wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Main residence (required)
        self.main_residence.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='mainResidence'
        )

        # Secondary residences (optional, multiple) - wrapper in eCH-0011, content in eCH-0007
        for secondary in self.secondary_residence:
            sec_res_elem = ET.SubElement(elem, f'{{{namespace}}}secondaryResidence')
            # Serialize municipality content (municipalityId, municipalityName, etc.) in eCH-0007 namespace
            swiss_muni = secondary.swiss_municipality
            ech0007_ns = 'http://www.ech.ch/xmlns/eCH-0007/5'
            if swiss_muni.municipality_id:
                ET.SubElement(sec_res_elem, f'{{{ech0007_ns}}}municipalityId').text = swiss_muni.municipality_id
            ET.SubElement(sec_res_elem, f'{{{ech0007_ns}}}municipalityName').text = swiss_muni.municipality_name
            if swiss_muni.canton_abbreviation:
                ET.SubElement(sec_res_elem, f'{{{ech0007_ns}}}cantonAbbreviation').text = swiss_muni.canton_abbreviation.value
            if swiss_muni.history_municipality_id:
                ET.SubElement(sec_res_elem, f'{{{ech0007_ns}}}historyMunicipalityId').text = swiss_muni.history_municipality_id

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011MainResidence':
        """Import from eCH-0011 XML."""
        ns = {
            'eCH-0011': namespace,
            'eCH-0007': 'http://www.ech.ch/xmlns/eCH-0007/5'
        }

        # Main residence (required)
        main_elem = elem.find('eCH-0011:mainResidence', ns)
        if main_elem is None:
            raise ValueError("Missing required field: mainResidence")
        main_residence = ECH0011ResidenceData.from_xml(main_elem, namespace)

        # Secondary residences (optional, multiple) - wrapper in eCH-0011, content in eCH-0007
        secondary_list = []
        for secondary_elem in elem.findall('eCH-0011:secondaryResidence', ns):
            # Parse swissMunicipalityType content directly (municipalityId, municipalityName, etc.)
            from openmun_ech.ech0007 import ECH0007SwissMunicipality
            mun_id_elem = secondary_elem.find('eCH-0007:municipalityId', ns)
            mun_name_elem = secondary_elem.find('eCH-0007:municipalityName', ns)
            canton_elem = secondary_elem.find('eCH-0007:cantonAbbreviation', ns)
            hist_id_elem = secondary_elem.find('eCH-0007:historyMunicipalityId', ns)

            if mun_name_elem is not None and mun_name_elem.text:
                swiss_municipality = ECH0007SwissMunicipality(
                    municipality_id=mun_id_elem.text.strip() if mun_id_elem is not None and mun_id_elem.text else None,
                    municipality_name=mun_name_elem.text.strip(),
                    canton_abbreviation=canton_elem.text.strip() if canton_elem is not None and canton_elem.text else None,
                    history_municipality_id=hist_id_elem.text.strip() if hist_id_elem is not None and hist_id_elem.text else None
                )
                secondary_list.append(ECH0007Municipality(swiss_municipality=swiss_municipality))

        return cls(
            main_residence=main_residence,
            secondary_residence=secondary_list
        )


class ECH0011SecondaryResidence(BaseModel):
    """eCH-0011 Secondary residence.

    Represents a person's secondary residence with reference to main residence municipality.
    The secondaryResidence data is a restricted residenceDataType where comesFrom is required.

    XML Schema: eCH-0011 secondaryResidenceType
    XSD Lines: 397-417
    """

    # Main residence municipality reference (required)
    main_residence: ECH0007Municipality = Field(
        ...,
        description="Municipality where person has main residence (required)"
    )

    # Secondary residence data (required) - restricted residenceDataType
    # Note: comesFrom is REQUIRED (not optional like in base residenceDataType)
    reporting_municipality: ECH0007Municipality = Field(
        ...,
        description="Municipality where secondary residence is registered (required)"
    )
    arrival_date: date = Field(
        ...,
        description="Date of arrival at secondary residence (required)"
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        description="Origin/previous location (REQUIRED for secondary residence)"
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        description="Dwelling address at secondary residence (required)"
    )
    departure_date: Optional[date] = Field(
        None,
        description="Date of departure from secondary residence (optional)"
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        description="Destination/next location (optional)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'hasSecondaryResidence',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace for content elements
            element_name: Name of wrapper element (default: 'hasSecondaryResidence')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)
        """
        # Use wrapper_namespace for wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Main residence municipality (required)
        self.main_residence.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0007/5',
            element_name='mainResidence'
        )

        # Secondary residence (required) - inline complex type
        sec_elem = ET.SubElement(elem, f'{{{namespace}}}secondaryResidence')

        # Reporting municipality (required)
        self.reporting_municipality.to_xml(
            parent=sec_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0007/5',
            element_name='reportingMunicipality'
        )

        # Arrival date (required)
        arrival_elem = ET.SubElement(sec_elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Comes from (REQUIRED for secondary residence)
        self.comes_from.to_xml(
            parent=sec_elem,
            namespace=namespace,
            element_name='comesFrom'
        )

        # Dwelling address (required)
        self.dwelling_address.to_xml(parent=sec_elem, namespace=namespace)

        # Departure date (optional)
        if self.departure_date:
            departure_elem = ET.SubElement(sec_elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        # Goes to (optional)
        if self.goes_to:
            self.goes_to.to_xml(
                parent=sec_elem,
                namespace=namespace,
                element_name='goesTo'
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011SecondaryResidence':
        """Import from eCH-0011 XML."""
        ns = {
            'eCH-0011': namespace,
            'eCH-0007': 'http://www.ech.ch/xmlns/eCH-0007/5'
        }

        # Main residence municipality (required)
        main_elem = elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}mainResidence', ns)
        if main_elem is None:
            raise ValueError("Missing required field: mainResidence")
        main_residence = ECH0007Municipality.from_xml(main_elem, 'http://www.ech.ch/xmlns/eCH-0007/5')

        # Secondary residence element (required)
        sec_elem = elem.find('eCH-0011:secondaryResidence', ns)
        if sec_elem is None:
            raise ValueError("Missing required field: secondaryResidence")

        # Reporting municipality (required)
        mun_elem = sec_elem.find('{http://www.ech.ch/xmlns/eCH-0007/5}reportingMunicipality', ns)
        if mun_elem is None:
            raise ValueError("Missing required field: reportingMunicipality")
        reporting_municipality = ECH0007Municipality.from_xml(mun_elem, 'http://www.ech.ch/xmlns/eCH-0007/5')

        # Arrival date (required)
        arrival_elem = sec_elem.find('eCH-0011:arrivalDate', ns)
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("Missing required field: arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text.strip())

        # Comes from (REQUIRED for secondary residence)
        comes_elem = sec_elem.find('eCH-0011:comesFrom', ns)
        if comes_elem is None:
            raise ValueError("Missing required field: comesFrom (required for secondary residence)")
        comes_from = ECH0011DestinationType.from_xml(comes_elem, namespace)

        # Dwelling address (required)
        dwelling_elem = sec_elem.find('eCH-0011:dwellingAddress', ns)
        if dwelling_elem is None:
            raise ValueError("Missing required field: dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem, namespace)

        # Departure date (optional)
        departure_elem = sec_elem.find('eCH-0011:departureDate', ns)
        departure_date = date.fromisoformat(departure_elem.text.strip()) if departure_elem is not None and departure_elem.text else None

        # Goes to (optional)
        goes_elem = sec_elem.find('eCH-0011:goesTo', ns)
        goes_to = ECH0011DestinationType.from_xml(goes_elem, namespace) if goes_elem is not None else None

        return cls(
            main_residence=main_residence,
            reporting_municipality=reporting_municipality,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0011OtherResidence(BaseModel):
    """eCH-0011 Other residence.

    Represents a person's other type of residence (neither main nor secondary).
    This is a restricted residenceDataType where comesFrom is required.

    Note: The XSD element is named "secondaryResidence" even though this is
    within otherResidenceType. This follows the XSD schema exactly.

    XML Schema: eCH-0011 otherResidenceType
    XSD Lines: 418-437
    """

    # Other residence data (restricted residenceDataType)
    # Note: comesFrom is REQUIRED (not optional like base residenceDataType)
    reporting_municipality: ECH0007Municipality = Field(
        ...,
        description="Municipality where residence is registered"
    )
    arrival_date: date = Field(
        ...,
        description="Date of arrival at this residence"
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        description="Origin location (required for other residence)"
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        description="Dwelling address at this residence"
    )
    departure_date: Optional[date] = Field(
        None,
        description="Date of departure from this residence"
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        description="Destination location (if departed)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
        arbitrary_types_allowed=True
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'hasOtherResidence',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace for content elements
            element_name: Name of wrapper element (default: 'hasOtherResidence')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)
        """
        # Use wrapper_namespace for wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        # Create secondaryResidence wrapper (XSD naming)
        secondary_residence_elem = ET.SubElement(elem, f'{{{namespace}}}secondaryResidence')

        # Add reporting municipality
        self.reporting_municipality.to_xml(
            parent=secondary_residence_elem,
            namespace='http://www.ech.ch/xmlns/eCH-0007/5',
            element_name='reportingMunicipality'
        )

        # Add arrival date
        arrival_elem = ET.SubElement(secondary_residence_elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Add comes from (REQUIRED for other residence)
        self.comes_from.to_xml(
            parent=secondary_residence_elem,
            namespace=namespace,
            element_name='comesFrom'
        )

        # Add dwelling address
        self.dwelling_address.to_xml(parent=secondary_residence_elem, namespace=namespace)

        # Add optional departure date
        if self.departure_date is not None:
            departure_elem = ET.SubElement(secondary_residence_elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        # Add optional goes to
        if self.goes_to is not None:
            self.goes_to.to_xml(
                parent=secondary_residence_elem,
                namespace=namespace,
                element_name='goesTo'
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, nsmap: Optional[Dict[str, str]] = None) -> 'ECH0011OtherResidence':
        """Create instance from XML element.

        Args:
            elem: XML element (otherResidence)
            nsmap: Namespace map (optional)

        Returns:
            ECH0011OtherResidence instance
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0007": "http://www.ech.ch/xmlns/eCH-0007/6",
                "eCH-0010": "http://www.ech.ch/xmlns/eCH-0010/6"
            }

        ns = nsmap[None]

        # Get secondaryResidence wrapper element
        secondary_residence_elem = elem.find(f"{{{ns}}}secondaryResidence")
        if secondary_residence_elem is None:
            raise ValueError("Missing required secondaryResidence element in otherResidence")

        # Parse reporting municipality
        reporting_municipality_elem = secondary_residence_elem.find(f"{{{ns}}}reportingMunicipality")
        if reporting_municipality_elem is None:
            raise ValueError("Missing required reportingMunicipality in other residence")
        reporting_municipality = ECH0007Municipality.from_xml(reporting_municipality_elem, nsmap)

        # Parse arrival date
        arrival_date_elem = secondary_residence_elem.find(f"{{{ns}}}arrivalDate")
        if arrival_date_elem is None:
            raise ValueError("Missing required arrivalDate in other residence")
        arrival_date = date.fromisoformat(arrival_date_elem.text)

        # Parse comes from (REQUIRED for other residence)
        comes_from_elem = secondary_residence_elem.find(f"{{{ns}}}comesFrom")
        if comes_from_elem is None:
            raise ValueError("Missing required comesFrom in other residence")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem, nsmap)

        # Parse dwelling address
        dwelling_address_elem = secondary_residence_elem.find(f"{{{ns}}}dwellingAddress")
        if dwelling_address_elem is None:
            raise ValueError("Missing required dwellingAddress in other residence")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_address_elem, nsmap)

        # Parse optional departure date
        departure_date = None
        departure_date_elem = secondary_residence_elem.find(f"{{{ns}}}departureDate")
        if departure_date_elem is not None and departure_date_elem.text:
            departure_date = date.fromisoformat(departure_date_elem.text)

        # Parse optional goes to
        goes_to = None
        goes_to_elem = secondary_residence_elem.find(f"{{{ns}}}goesTo")
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem, nsmap)

        return cls(
            reporting_municipality=reporting_municipality,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0011Person(BaseModel):
    """eCH-0011 Complete person model (personType).

    Combines all person data components into a complete person record.
    This is the top-level model that validates against eCH-0011 personType.

    XML Schema: eCH-0011 personType
    """

    # Required fields
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        description="Person identification (eCH-0044, required)"
    )
    name_data: ECH0011NameData = Field(
        ...,
        description="Name data (required)"
    )
    birth_data: ECH0011BirthData = Field(
        ...,
        description="Birth data (required)"
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        description="Religion data (required)"
    )
    marital_data: ECH0011MaritalData = Field(
        ...,
        description="Marital data (required)"
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        description="Nationality data (required)"
    )

    # Optional fields
    death_data: Optional[ECH0011DeathData] = Field(
        None,
        description="Death data (optional)"
    )
    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        description="Contact data (optional)"
    )
    language_of_correspondance: Optional[str] = Field(
        None,
        max_length=2,
        description="Language of correspondence (ISO 639-1 code, optional)"
    )
    restricted_voting_and_election_right_federation: Optional[bool] = Field(
        None,
        description="Restricted voting/election rights (optional)"
    )

    # Choice: Swiss person has placeOfOrigin, foreigner has residencePermit
    place_of_origin: List[ECH0011PlaceOfOrigin] = Field(
        default_factory=list,
        description="Places of origin (for Swiss citizens)"
    )
    residence_permit: Optional[ECH0011ResidencePermitData] = Field(
        None,
        description="Residence permit (for foreign nationals)"
    )

    @field_validator('place_of_origin', 'residence_permit')
    @classmethod
    def validate_swiss_or_foreign(cls, v, info):
        """Validate that either placeOfOrigin OR residencePermit is set (not both)."""
        # This will be checked in to_xml() method
        return v

    @staticmethod
    def _populate_person_identification(elem: ET.Element,
                                       person_id: ECH0044PersonIdentification) -> None:
        """Populate person identification element with eCH-0044 content.

        The personIdentification element is in eCH-0011 namespace, but its content
        (child elements) are in eCH-0044 namespace as defined by eCH-0044:personIdentificationType.

        Args:
            elem: The personIdentification element (already created in eCH-0011 namespace)
            person_id: The person identification data to populate
        """
        ech0044_ns = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # VN (optional)
        if person_id.vn:
            vn_elem = ET.SubElement(elem, f'{{{ech0044_ns}}}vn')
            vn_elem.text = person_id.vn

        # Local person ID (required)
        person_id.local_person_id.to_xml(elem, ech0044_ns, 'localPersonId')

        # Other person IDs (optional, multiple)
        for other_id in person_id.other_person_id:
            other_id.to_xml(elem, ech0044_ns, 'otherPersonId')

        # EU person IDs (optional, multiple)
        for eu_id in person_id.eu_person_id:
            eu_id.to_xml(elem, ech0044_ns, 'euPersonId')

        # Official name (required)
        official_elem = ET.SubElement(elem, f'{{{ech0044_ns}}}officialName')
        official_elem.text = person_id.official_name

        # First name (required)
        first_elem = ET.SubElement(elem, f'{{{ech0044_ns}}}firstName')
        first_elem.text = person_id.first_name

        # Original name (optional)
        if person_id.original_name:
            original_elem = ET.SubElement(elem, f'{{{ech0044_ns}}}originalName')
            original_elem.text = person_id.original_name

        # Sex (required)
        sex_elem = ET.SubElement(elem, f'{{{ech0044_ns}}}sex')
        sex_elem.text = person_id.sex

        # Date of birth (required)
        person_id.date_of_birth.to_xml(elem, ech0044_ns, 'dateOfBirth')

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8',
               element_name: str = 'person') -> ET.Element:
        """Export to eCH-0011 XML.

        Args:
            parent: Parent element to attach to (if None, creates standalone)
            namespace: XML namespace URI
            element_name: Name of container element

        Returns:
            XML Element

        Raises:
            ValueError: If both or neither of placeOfOrigin/residencePermit are set
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Check Swiss/foreign choice
        has_origin = len(self.place_of_origin) > 0
        has_permit = self.residence_permit is not None

        if has_origin and has_permit:
            raise ValueError("Cannot have both placeOfOrigin and residencePermit")
        if not has_origin and not has_permit:
            raise ValueError("Must have either placeOfOrigin (Swiss) or residencePermit (foreign)")

        # Person identification (required, eCH-0044 type in eCH-0011 namespace)
        # Note: The element tag is in eCH-0011 namespace, but content is eCH-0044 namespace
        # XSD: <xs:element name="personIdentification" type="eCH-0044:personIdentificationType" />
        person_id_elem = ET.SubElement(elem, f'{{{namespace}}}personIdentification')
        # Now populate it with eCH-0044 content (but don't create wrapper element)
        self._populate_person_identification(person_id_elem, self.person_identification)

        # Name data (required)
        self.name_data.to_xml(elem, namespace)

        # Birth data (required)
        self.birth_data.to_xml(elem, namespace)

        # Religion data (required)
        self.religion_data.to_xml(elem, namespace)

        # Marital data (required)
        self.marital_data.to_xml(elem, namespace)

        # Nationality data (required)
        self.nationality_data.to_xml(elem, namespace)

        # Death data (optional)
        if self.death_data:
            self.death_data.to_xml(elem, namespace)

        # Contact data (optional)
        if self.contact_data:
            self.contact_data.to_xml(elem, namespace)

        # Language of correspondance (optional)
        if self.language_of_correspondance:
            lang_elem = ET.SubElement(elem, f'{{{namespace}}}languageOfCorrespondance')
            lang_elem.text = self.language_of_correspondance

        # Restricted voting rights (optional)
        if self.restricted_voting_and_election_right_federation is not None:
            vote_elem = ET.SubElement(elem, f'{{{namespace}}}restrictedVotingAndElectionRightFederation')
            vote_elem.text = 'true' if self.restricted_voting_and_election_right_federation else 'false'

        # Choice: placeOfOrigin OR residencePermit
        if has_origin:
            # Swiss person - places of origin
            for origin in self.place_of_origin:
                origin.to_xml(elem, namespace)
        else:
            # Foreign person - residence permit
            self.residence_permit.to_xml(elem, namespace)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element,
                 namespace: str = 'http://www.ech.ch/xmlns/eCH-0011/8') -> 'ECH0011Person':
        """Import from eCH-0011 XML.

        Args:
            elem: XML element (person container)
            namespace: XML namespace URI

        Returns:
            Parsed person object

        Raises:
            ValueError: If required fields missing or validation fails
        """
        ns = {
            'eCH-0011': namespace,
            'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'
        }

        # Person identification (required, eCH-0044 type in eCH-0011 namespace)
        # Note: The element is in eCH-0011 namespace, but uses eCH-0044:personIdentificationType
        person_id_elem = elem.find('eCH-0011:personIdentification', ns)
        if person_id_elem is None:
            raise ValueError("Missing required field: personIdentification")
        person_id = ECH0044PersonIdentification.from_xml(person_id_elem, 'http://www.ech.ch/xmlns/eCH-0044/4')

        # Name data (required)
        name_elem = elem.find('eCH-0011:nameData', ns)
        if name_elem is None:
            raise ValueError("Missing required field: nameData")
        name_data = ECH0011NameData.from_xml(name_elem, namespace)

        # Birth data (required)
        birth_elem = elem.find('eCH-0011:birthData', ns)
        if birth_elem is None:
            raise ValueError("Missing required field: birthData")
        birth_data = ECH0011BirthData.from_xml(birth_elem, namespace)

        # Religion data (required)
        religion_elem = elem.find('eCH-0011:religionData', ns)
        if religion_elem is None:
            raise ValueError("Missing required field: religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem, namespace)

        # Marital data (required)
        marital_elem = elem.find('eCH-0011:maritalData', ns)
        if marital_elem is None:
            raise ValueError("Missing required field: maritalData")
        marital_data = ECH0011MaritalData.from_xml(marital_elem, namespace)

        # Nationality data (required)
        nationality_elem = elem.find('eCH-0011:nationalityData', ns)
        if nationality_elem is None:
            raise ValueError("Missing required field: nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem, namespace)

        # Death data (optional)
        death_elem = elem.find('eCH-0011:deathData', ns)
        death_data = ECH0011DeathData.from_xml(death_elem, namespace) if death_elem is not None else None

        # Contact data (optional)
        contact_elem = elem.find('eCH-0011:contactData', ns)
        contact_data = ECH0011ContactData.from_xml(contact_elem, namespace) if contact_elem is not None else None

        # Language of correspondance (optional)
        lang_elem = elem.find('eCH-0011:languageOfCorrespondance', ns)
        language = lang_elem.text.strip() if lang_elem is not None and lang_elem.text else None

        # Restricted voting rights (optional)
        vote_elem = elem.find('eCH-0011:restrictedVotingAndElectionRightFederation', ns)
        restricted_voting = vote_elem.text.strip().lower() == 'true' if vote_elem is not None and vote_elem.text else None

        # Choice: placeOfOrigin OR residencePermit
        origins = []
        for origin_elem in elem.findall('eCH-0011:placeOfOrigin', ns):
            origins.append(ECH0011PlaceOfOrigin.from_xml(origin_elem, namespace))

        permit_elem = elem.find('eCH-0011:residencePermit', ns)
        permit = ECH0011ResidencePermitData.from_xml(permit_elem, namespace) if permit_elem is not None else None

        return cls(
            person_identification=person_id,
            name_data=name_data,
            birth_data=birth_data,
            religion_data=religion_data,
            marital_data=marital_data,
            nationality_data=nationality_data,
            death_data=death_data,
            contact_data=contact_data,
            language_of_correspondance=language,
            restricted_voting_and_election_right_federation=restricted_voting,
            place_of_origin=origins,
            residence_permit=permit
        )


class ECH0011ReportedPerson(BaseModel):
    """eCH-0011 Reported person (reportedPersonType).

    Combines a person with exactly one type of residence information.
    This is the type required by eCH-0099 v2.1 for baseData elements.

    The XSD defines this as a sequence containing:
    - person (personType)
    - choice of exactly one residence type:
      - hasMainResidence (mainResidenceType)
      - hasSecondaryResidence (secondaryResidenceType)
      - hasOtherResidence (otherResidenceType)

    XML Schema: eCH-0011 reportedPersonType
    XSD Lines: 22-31
    """

    # Required person data
    person: ECH0011Person = Field(
        ...,
        description="Complete person data (required)"
    )

    # Exactly one of these residence types must be set (XSD choice)
    has_main_residence: Optional[ECH0011MainResidence] = Field(
        None,
        description="Main residence data (choice 1 of 3)"
    )
    has_secondary_residence: Optional[ECH0011SecondaryResidence] = Field(
        None,
        description="Secondary residence data (choice 2 of 3)"
    )
    has_other_residence: Optional[ECH0011OtherResidence] = Field(
        None,
        description="Other residence data (choice 3 of 3)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
        arbitrary_types_allowed=True
    )

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0011ReportedPerson':
        """Validate that exactly one residence type is set (XSD choice constraint)."""
        residence_fields = [
            self.has_main_residence,
            self.has_secondary_residence,
            self.has_other_residence
        ]
        set_count = sum(1 for field in residence_fields if field is not None)

        if set_count == 0:
            raise ValueError(
                "reportedPersonType requires exactly one residence type: "
                "hasMainResidence, hasSecondaryResidence, or hasOtherResidence"
            )
        if set_count > 1:
            raise ValueError(
                f"reportedPersonType allows only one residence type, but {set_count} are set"
            )

        return self

    def to_xml(self, parent: ET.Element, tag: str = "reportedPerson",
               nsmap: Optional[Dict[str, str]] = None) -> ET.Element:
        """Convert to XML element.

        Args:
            parent: Parent XML element
            tag: Tag name for this element (default: "reportedPerson")
            nsmap: Namespace map (optional)

        Returns:
            Created XML element
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0007": "http://www.ech.ch/xmlns/eCH-0007/6",
                "eCH-0010": "http://www.ech.ch/xmlns/eCH-0010/6",
                "eCH-0044": "http://www.ech.ch/xmlns/eCH-0044/4"
            }

        # Create root reportedPerson element
        elem = ET.SubElement(parent, f"{{{nsmap[None]}}}{tag}")

        # Add person data
        self.person.to_xml(elem, tag="person", nsmap=nsmap)

        # Add whichever residence type is set (XSD choice)
        if self.has_main_residence is not None:
            self.has_main_residence.to_xml(elem, tag="hasMainResidence", nsmap=nsmap)
        elif self.has_secondary_residence is not None:
            self.has_secondary_residence.to_xml(elem, tag="hasSecondaryResidence", nsmap=nsmap)
        elif self.has_other_residence is not None:
            self.has_other_residence.to_xml(elem, tag="hasOtherResidence", nsmap=nsmap)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, nsmap: Optional[Dict[str, str]] = None) -> 'ECH0011ReportedPerson':
        """Create instance from XML element.

        Args:
            elem: XML element (reportedPerson)
            nsmap: Namespace map (optional)

        Returns:
            ECH0011ReportedPerson instance
        """
        if nsmap is None:
            nsmap = {
                None: "http://www.ech.ch/xmlns/eCH-0011/8",
                "eCH-0007": "http://www.ech.ch/xmlns/eCH-0007/6",
                "eCH-0010": "http://www.ech.ch/xmlns/eCH-0010/6",
                "eCH-0044": "http://www.ech.ch/xmlns/eCH-0044/4"
            }

        ns = nsmap[None]

        # Parse person (required)
        person_elem = elem.find(f"{{{ns}}}person")
        if person_elem is None:
            raise ValueError("Missing required person element in reportedPerson")
        person = ECH0011Person.from_xml(person_elem, nsmap)

        # Parse residence type (exactly one must be present - XSD choice)
        has_main_residence = None
        has_secondary_residence = None
        has_other_residence = None

        main_residence_elem = elem.find(f"{{{ns}}}hasMainResidence")
        if main_residence_elem is not None:
            has_main_residence = ECH0011MainResidence.from_xml(main_residence_elem, nsmap)

        secondary_residence_elem = elem.find(f"{{{ns}}}hasSecondaryResidence")
        if secondary_residence_elem is not None:
            has_secondary_residence = ECH0011SecondaryResidence.from_xml(secondary_residence_elem, nsmap)

        other_residence_elem = elem.find(f"{{{ns}}}hasOtherResidence")
        if other_residence_elem is not None:
            has_other_residence = ECH0011OtherResidence.from_xml(other_residence_elem, nsmap)

        # Validator will check that exactly one is set
        return cls(
            person=person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence
        )
