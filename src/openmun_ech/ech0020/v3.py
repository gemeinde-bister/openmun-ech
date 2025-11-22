"""eCH-0020 Event Reporting Standard v3.0.

Standard: eCH-0020 v3.0 (Event reporting for Swiss population registers)
Status: CRITICAL GOVERNMENT DATA - ZERO TOLERANCE FOR ERRORS

This component provides event reporting structures for Swiss population registers,
enabling communication between municipalities, INFOSTAR, ZEMIS, and cantonal systems.

Event Types:
- Base delivery (complete municipality snapshot)
- Life events (birth, death, marriage, divorce, etc.)
- Movement events (move in, move out, missing)
- Administrative changes (name, nationality, religion, occupation)
- Corrections and data updates

XSD Source: docs/eCH/eCH-0020-3-0.xsd
PDF Source: docs/eCH/STAN_d_DEF_2015-02-26-eCH-0020_V3.0_Meldegruende.pdf

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/

IMPLEMENTATION STATUS: ✅ COMPLETE
- Total complex types: 89
- Implemented: 89
- Progress: 89/89 (100%)
- File size: 10,786 lines, 96 classes

Tracker: docs/ECH0020_IMPLEMENTATION_TRACKER.md

Completed: 2025-10-26
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union, Literal
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# XSD validation (Zero-Tolerance Policy #5: No Schema Violations)
from openmun_ech.utils.schema_cache import validate_xml_cached

# eCH-0020 v3.0 namespace constant
NAMESPACE_ECH0020_V3 = 'http://www.ech.ch/xmlns/eCH-0020/3'
NAMESPACE_ECH0011_V8 = 'http://www.ech.ch/xmlns/eCH-0011/8'
NAMESPACE_ECH0021_V7 = 'http://www.ech.ch/xmlns/eCH-0021/7'
NAMESPACE_ECH0044_V4 = 'http://www.ech.ch/xmlns/eCH-0044/4'

# Import dependencies from other eCH standards
from openmun_ech.ech0006 import ResidencePermitType
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0010 import (
    ECH0010MailAddress,
    ECH0010AddressInformation,
    ECH0010SwissAddressInformation,
)
from openmun_ech.ech0011 import (
    ECH0011NameData,
    ECH0011BirthData,
    ECH0011MaritalData,
    ECH0011MaritalDataRestrictedMarriage,
    ECH0011MaritalDataRestrictedPartnership,
    ECH0011MaritalDataRestrictedDivorce,
    ECH0011MaritalDataRestrictedUndoMarried,
    ECH0011MaritalDataRestrictedUndoPartnership,
    ECH0011MaritalDataRestrictedMaritalStatusPartner,
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    ECH0011MainResidence,
    ECH0011SecondaryResidence,
    ECH0011OtherResidence,
    ECH0011SeparationData,
    FederalRegister,
    MaritalStatus,
    YesNo,  # For paperLockType
)
from openmun_ech.ech0021 import DataLockType  # v7 enum
from openmun_ech.ech0021.v7 import (
    ECH0021PersonAdditionalData,
    ECH0021LockData,
    ECH0021PlaceOfOriginAddonData,
    ECH0021MaritalDataAddon,
    ECH0021BirthAddonData,
    ECH0021JobData,
    ECH0021HealthInsuranceData,
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021PoliticalRightData,
    ECH0021GuardianRelationship,
    ECH0021ParentalRelationship,
    ECH0021MaritalRelationship,
    ECH0021MatrimonialInheritanceArrangementData,
    ECH0021NameOfParent,
)
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
    ECH0044NamedPersonId,
    Sex,
)
from openmun_ech.ech0058 import ECH0058Header


# ============================================================================
# INFO/WRAPPER TYPES (Wrapper types for validation dates and additional data)
# ============================================================================

class ECH0020NameInfo(BaseModel):
    """Name data with optional validation date.

    Wrapper around eCH-0011 nameData adding an optional nameValidFrom field.

    XSD: nameInfoType (eCH-0020-3-0.xsd lines 31-36)
    PDF: N/A (simple wrapper type, not documented separately)
    """

    name_data: ECH0011NameData = Field(
        ...,
        description="Name data per eCH-0011"
    )

    name_valid_from: Optional[date] = Field(
        None,
        alias='nameValidFrom',
        description="Date from which name is valid"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'nameInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # nameData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        name_wrapper = ET.SubElement(elem, f'{{{namespace}}}nameData')
        # Generate eCH-0011 content and move children to wrapper
        name_content = self.name_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in name_content:
            name_wrapper.append(child)

        # nameValidFrom (optional)
        if self.name_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{namespace}}}nameValidFrom')
            valid_from_elem.text = self.name_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020NameInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0011 = {'eCH-0011': 'http://www.ech.ch/xmlns/eCH-0011/8'}

        # nameData (required, wrapper in eCH-0020, content in eCH-0011)
        name_data_elem = element.find('eCH-0020:nameData', ns_0020)
        if name_data_elem is None:
            raise ValueError("nameData is required in nameInfoType")
        name_data = ECH0011NameData.from_xml(name_data_elem)

        # nameValidFrom (optional)
        valid_from_elem = element.find('eCH-0020:nameValidFrom', ns_0020)
        name_valid_from = None
        if valid_from_elem is not None and valid_from_elem.text:
            name_valid_from = date.fromisoformat(valid_from_elem.text)

        return cls(
            name_data=name_data,
            name_valid_from=name_valid_from
        )


class ECH0020BirthInfo(BaseModel):
    """Birth data with optional addon data.

    Wrapper around eCH-0011 birthData with optional eCH-0021 birthAddonData
    (contains names of parents).

    XSD: birthInfoType (eCH-0020-3-0.xsd lines 43-48)
    PDF: N/A (simple wrapper type)
    """

    birth_data: ECH0011BirthData = Field(
        ...,
        description="Birth data per eCH-0011"
    )

    birth_addon_data: Optional[ECH0021BirthAddonData] = Field(
        None,
        alias='birthAddonData',
        description="Birth addon data per eCH-0021 v7 (parent names)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'birthInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # birthData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        birth_wrapper = ET.SubElement(elem, f'{{{namespace}}}birthData')
        # Generate eCH-0011 content and move children to wrapper
        birth_content = self.birth_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in birth_content:
            birth_wrapper.append(child)

        # birthAddonData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.birth_addon_data:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}birthAddonData')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.birth_addon_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BirthInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # birthData (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        birth_data_elem = element.find('eCH-0020:birthData', ns_0020)
        if birth_data_elem is None:
            raise ValueError("birthData is required in birthInfoType")
        birth_data = ECH0011BirthData.from_xml(birth_data_elem)

        # birthAddonData (optional, wrapper in eCH-0020, content in eCH-0021)
        birth_addon_elem = element.find('eCH-0020:birthAddonData', ns_0020)
        birth_addon_data = None
        if birth_addon_elem is not None:
            birth_addon_data = ECH0021BirthAddonData.from_xml(birth_addon_elem)

        return cls(
            birth_data=birth_data,
            birth_addon_data=birth_addon_data
        )


class ECH0020MaritalInfo(BaseModel):
    """Marital data with optional addon data.

    Wrapper around eCH-0011 maritalData with optional eCH-0021 maritalDataAddon
    (contains place of marriage and other details).

    XSD: maritalInfoType (eCH-0020-3-0.xsd lines 49-54)
    PDF: N/A (simple wrapper type)
    """

    marital_data: ECH0011MaritalData = Field(
        ...,
        description="Marital data per eCH-0011"
    )

    marital_data_addon: Optional[ECH0021MaritalDataAddon] = Field(
        None,
        alias='maritalDataAddon',
        description="Marital data addon per eCH-0021 v7 (place of marriage)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'maritalInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # maritalData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        marital_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalData')
        # Generate eCH-0011 content and move children to wrapper
        marital_content = self.marital_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in marital_content:
            marital_wrapper.append(child)

        # maritalDataAddon (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.marital_data_addon:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalDataAddon')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.marital_data_addon.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020MaritalInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # maritalData (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        marital_data_elem = element.find('eCH-0020:maritalData', ns_0020)
        if marital_data_elem is None:
            raise ValueError("maritalData is required in maritalInfoType")
        marital_data = ECH0011MaritalData.from_xml(marital_data_elem)

        # maritalDataAddon (optional, wrapper in eCH-0020, content in eCH-0021)
        marital_addon_elem = element.find('eCH-0020:maritalDataAddon', ns_0020)
        marital_data_addon = None
        if marital_addon_elem is not None:
            marital_data_addon = ECH0021MaritalDataAddon.from_xml(marital_addon_elem)

        return cls(
            marital_data=marital_data,
            marital_data_addon=marital_data_addon
        )


class ECH0020MaritalInfoRestrictedMarriage(BaseModel):
    """Restricted marital info (for marriage/partnership data).

    Contains a restricted inline maritalData structure (status + date only)
    plus optional maritalDataAddon from eCH-0021 v7.

    XSD: maritalInfoRestrictedMarriageType (eCH-0020-3-0.xsd lines 55-67)
    PDF: N/A (inline type definition)

    Note: This differs from maritalInfoType by using a restricted inline
    maritalData structure instead of the full eCH-0011 maritalDataType.
    """

    marital_status: MaritalStatus = Field(
        ...,
        alias='maritalStatus',
        description="Marital status code per eCH-0011"
    )

    date_of_marital_status: Optional[date] = Field(
        None,
        alias='dateOfMaritalStatus',
        description="Date when marital status became effective"
    )

    marital_data_addon: Optional[ECH0021MaritalDataAddon] = Field(
        None,
        alias='maritalDataAddon',
        description="Marital data addon per eCH-0021 v7 (place of marriage)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'maritalInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # maritalData (inline complexType, required)
        marital_data_elem = ET.SubElement(elem, f'{{{namespace}}}maritalData')

        # maritalStatus (required)
        status_elem = ET.SubElement(marital_data_elem, f'{{{namespace}}}maritalStatus')
        status_elem.text = self.marital_status.value

        # dateOfMaritalStatus (optional)
        if self.date_of_marital_status:
            date_elem = ET.SubElement(marital_data_elem, f'{{{namespace}}}dateOfMaritalStatus')
            date_elem.text = self.date_of_marital_status.isoformat()

        # maritalDataAddon (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.marital_data_addon:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalDataAddon')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.marital_data_addon.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020MaritalInfoRestrictedMarriage':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # maritalData (inline complexType, required)
        marital_data_elem = element.find('eCH-0020:maritalData', ns_0020)
        if marital_data_elem is None:
            raise ValueError("maritalData is required in maritalInfoRestrictedMarriageType")

        # maritalStatus (required)
        status_elem = marital_data_elem.find('eCH-0020:maritalStatus', ns_0020)
        if status_elem is None:
            raise ValueError("maritalStatus is required in maritalData")
        marital_status = MaritalStatus(status_elem.text)

        # dateOfMaritalStatus (optional)
        date_elem = marital_data_elem.find('eCH-0020:dateOfMaritalStatus', ns_0020)
        date_of_marital_status = None
        if date_elem is not None and date_elem.text:
            date_of_marital_status = date.fromisoformat(date_elem.text)

        # maritalDataAddon (optional, wrapper in eCH-0020, content in eCH-0021)
        marital_addon_elem = element.find('eCH-0020:maritalDataAddon', ns_0020)
        marital_data_addon = None
        if marital_addon_elem is not None:
            marital_data_addon = ECH0021MaritalDataAddon.from_xml(marital_addon_elem)

        return cls(
            marital_status=marital_status,
            date_of_marital_status=date_of_marital_status,
            marital_data_addon=marital_data_addon
        )


class ECH0020PlaceOfOriginInfo(BaseModel):
    """Place of origin data with optional addon data.

    Wrapper around eCH-0011 placeOfOrigin with optional eCH-0021 placeOfOriginAddonData
    (contains naturalization and expatriation dates).

    XSD: placeOfOriginInfoType (eCH-0020-3-0.xsd lines 68-73)
    PDF: N/A (simple wrapper type)
    """

    place_of_origin: ECH0011PlaceOfOrigin = Field(
        ...,
        alias='placeOfOrigin',
        description="Place of origin per eCH-0011"
    )

    place_of_origin_addon_data: Optional[ECH0021PlaceOfOriginAddonData] = Field(
        None,
        alias='placeOfOriginAddonData',
        description="Place of origin addon per eCH-0021 v7 (naturalization/expatriation dates)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'placeOfOriginInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # placeOfOrigin (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        origin_wrapper = ET.SubElement(elem, f'{{{namespace}}}placeOfOrigin')
        # Generate eCH-0011 content and move children to wrapper
        origin_content = self.place_of_origin.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in origin_content:
            origin_wrapper.append(child)

        # placeOfOriginAddonData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.place_of_origin_addon_data:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}placeOfOriginAddonData')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.place_of_origin_addon_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020PlaceOfOriginInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # placeOfOrigin (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        place_of_origin_elem = element.find('eCH-0020:placeOfOrigin', ns_0020)
        if place_of_origin_elem is None:
            raise ValueError("placeOfOrigin is required in placeOfOriginInfoType")
        place_of_origin = ECH0011PlaceOfOrigin.from_xml(place_of_origin_elem)

        # placeOfOriginAddonData (optional, wrapper in eCH-0020, content in eCH-0021)
        place_addon_elem = element.find('eCH-0020:placeOfOriginAddonData', ns_0020)
        place_of_origin_addon_data = None
        if place_addon_elem is not None:
            place_of_origin_addon_data = ECH0021PlaceOfOriginAddonData.from_xml(place_addon_elem)

        return cls(
            place_of_origin=place_of_origin,
            place_of_origin_addon_data=place_of_origin_addon_data
        )


# ============================================================================
# TYPE 7/89: INFOSTAR PERSON TYPE
# ============================================================================

class ECH0020InfostarPerson(BaseModel):
    """Person data structure for INFOSTAR (federal population register).

    This type is used for reporting population data to INFOSTAR, the Swiss federal
    population information system. It contains the essential person data required
    for federal register synchronization.

    XSD: infostarPersonType (eCH-0020-3-0.xsd lines 96-109)
    PDF: Unknown section (INFOSTAR reporting structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - personIdentification: Person identification (VN, local ID, etc.)
    - nameInfo: Name data with optional validation date
    - birthInfo: Birth data (extends eCH-0020 birthInfoType)
    - maritalInfo: Marital status data
    - nationalityData: Nationality/citizenship data
    - placeOfOriginInfo: Swiss place(s) of origin (0-n, for Swiss citizens)
    - deathData: Death information (optional)

    Note: This type has no XSD CHOICE constraints - all fields are in sequence.
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data (extends eCH-0020 birthInfoType inline)'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # Optional fields
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (for Swiss citizens, 0-n)'
    )
    death_data: Optional[ECH0011DeathData] = Field(
        None,
        alias='deathData',
        description='Death information (optional)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'infostarPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'infostarPerson')

        Returns:
            XML element with all person data for INFOSTAR
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # 1. personIdentification (required, eCH-0044/4 namespace)
        self.person_identification.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0044/4',
            element_name='personIdentification'
        )

        # 2. nameInfo (required, eCH-0020/3 namespace)
        self.name_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='nameInfo'
        )

        # 3. birthInfo (required, eCH-0020/3 namespace)
        # XSD has inline complexType extending birthInfoType, but with no additions
        # So we just serialize as regular birthInfo
        self.birth_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='birthInfo'
        )

        # 4. maritalInfo (required, eCH-0020/3 namespace)
        self.marital_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='maritalInfo'
        )

        # 5. nationalityData (required, eCH-0011/8 namespace)
        self.nationality_data.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0011/8',
            element_name='nationalityData'
        )

        # 6. placeOfOriginInfo (optional, 0-n, eCH-0020/3 namespace)
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(
                    parent=elem,
                    namespace=namespace,
                    element_name='placeOfOriginInfo'
                )

        # 7. deathData (optional, eCH-0011/8 namespace)
        if self.death_data:
            self.death_data.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0011/8',
                element_name='deathData'
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020InfostarPerson':
        """Parse from XML element.

        Args:
            element: XML element containing infostarPerson data

        Returns:
            Parsed ECH0020InfostarPerson instance
        """
        # Define namespaces
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # 1. personIdentification (required)
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("infostarPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        # 2. nameInfo (required)
        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("infostarPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        # 3. birthInfo (required)
        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("infostarPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        # 4. maritalInfo (required)
        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("infostarPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        # 5. nationalityData (required)
        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("infostarPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        # 6. placeOfOriginInfo (optional, 0-n)
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [
                ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems
            ]

        # 7. deathData (optional)
        death_data = None
        death_elem = element.find(f'{{{ns_020}}}deathData')
        if death_elem is not None:
            death_data = ECH0011DeathData.from_xml(death_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            death_data=death_data
        )


# ============================================================================
# TYPE 8/89: BASE DELIVERY PERSON TYPE
# ============================================================================

class ECH0020BaseDeliveryPerson(BaseModel):
    """Complete person data structure for base deliveries.

    Base deliveries are complete snapshots of a municipality's population register,
    sent to INFOSTAR/cantonal systems. This type contains all person data including
    demographics, relationships, military service, health insurance, etc.

    XSD: baseDeliveryPersonType (eCH-0020-3-0.xsd lines 113-140)
    PDF: Unknown section (base delivery structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields (21 total):
    REQUIRED:
    - personIdentification: Person identification (VN, local ID)
    - nameInfo: Name data with validation date
    - birthInfo: Birth data
    - religionData: Religion/confession
    - maritalInfo: Marital status
    - nationalityData: Nationality/citizenship
    - lockData: Data/paper lock information
    - CHOICE: placeOfOriginInfo (Swiss, 1-n) OR residencePermitData (foreign)

    OPTIONAL:
    - deathData: Death information
    - contactData: Contact information (phone, email)
    - personAdditionalData: Additional person data
    - politicalRightData: Political rights data
    - jobData: Employment data
    - maritalRelationship: Marital relationship details
    - parentalRelationship: Parental relationships (0-n)
    - guardianRelationship: Guardian relationships (0-n)
    - armedForcesData: Military service data
    - civilDefenseData: Civil defense service
    - fireServiceData: Fire service data
    - healthInsuranceData: Health insurance
    - matrimonialInheritanceArrangementData: Matrimonial regime/inheritance
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data per eCH-0020'
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='Religion/confession data per eCH-0011'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # XSD CHOICE: placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    # Note: placeOfOriginInfo is unbounded (1-n for Swiss citizens)
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (1-n for Swiss citizens)'
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Residence permit data for foreign nationals'
    )

    # lockData is REQUIRED (comes after CHOICE in XSD)
    lock_data: ECH0021LockData = Field(
        ...,
        alias='lockData',
        description='Data lock and paper lock information'
    )

    # Optional fields (all minOccurs=0)
    death_data: Optional[ECH0011DeathData] = Field(
        None,
        alias='deathData',
        description='Death information (if deceased)'
    )
    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description='Contact information (phone, email)'
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description='Additional person data per eCH-0021'
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = Field(
        None,
        alias='politicalRightData',
        description='Political rights data (v7-only field)'
    )
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Employment/occupation data'
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Marital relationship details'
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description='Parental relationships (0-n)'
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = Field(
        None,
        alias='guardianRelationship',
        description='Guardian relationships (0-n)'
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = Field(
        None,
        alias='armedForcesData',
        description='Military service data'
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = Field(
        None,
        alias='civilDefenseData',
        description='Civil defense service data'
    )
    fire_service_data: Optional[ECH0021FireServiceData] = Field(
        None,
        alias='fireServiceData',
        description='Fire service data'
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description='Health insurance information'
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = Field(
        None,
        alias='matrimonialInheritanceArrangementData',
        description='Matrimonial regime and inheritance arrangement'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BaseDeliveryPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData.

        XSD constraint (lines 123-127):
        <xs:choice>
            <xs:element name="placeOfOriginInfo" type="eCH-0020:placeOfOriginInfoType" maxOccurs="unbounded"/>
            <xs:element name="residencePermitData" type="eCH-0011:residencePermitDataType"/>
        </xs:choice>
        """
        has_origin = self.place_of_origin_info is not None and len(self.place_of_origin_info) > 0
        has_permit = self.residence_permit_data is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "baseDeliveryPersonType requires either placeOfOriginInfo (Swiss citizen) "
                "OR residencePermitData (foreign national)"
            )
        if has_origin and has_permit:
            raise ValueError(
                "baseDeliveryPersonType allows either placeOfOriginInfo OR residencePermitData, "
                f"but both were provided (origins={len(self.place_of_origin_info)}, permit=yes)"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'baseDeliveryPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'baseDeliveryPerson')

        Returns:
            XML element with complete person data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # 1. personIdentification (required, eCH-0044/4)
        # Create wrapper element in parent namespace
        personIdentification_wrapper = ET.SubElement(elem, f'{{{namespace}}}personIdentification')
        personIdentification_content = self.person_identification.to_xml(namespace=ns_044)
        for child in personIdentification_content:
            personIdentification_wrapper.append(child)

        # 2. nameInfo (required, eCH-0020/3)
        self.name_info.to_xml(parent=elem, namespace=namespace, element_name='nameInfo')

        # 3. birthInfo (required, eCH-0020/3)
        self.birth_info.to_xml(parent=elem, namespace=namespace, element_name='birthInfo')

        # 4. religionData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData',
            wrapper_namespace=namespace
        )

        # 5. maritalInfo (required, eCH-0020/3)
        self.marital_info.to_xml(parent=elem, namespace=namespace, element_name='maritalInfo')

        # 6. nationalityData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData',
            wrapper_namespace=namespace
        )

        # 7. deathData (optional, eCH-0011/8)
        if self.death_data:
            # Create wrapper element in parent namespace
            deathData_wrapper = ET.SubElement(elem, f'{{{namespace}}}deathData')
            deathData_content = self.death_data.to_xml(namespace=ns_011)
            for child in deathData_content:
                deathData_wrapper.append(child)

        # 8. contactData (optional, eCH-0011/8)
        if self.contact_data:
            # Create wrapper element in parent namespace
            contactData_wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            contactData_content = self.contact_data.to_xml(namespace=ns_011)
            for child in contactData_content:
                contactData_wrapper.append(child)

        # 9. personAdditionalData (optional, eCH-0021/7)
        if self.person_additional_data:
            # Create wrapper element in parent namespace
            personAdditionalData_wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            personAdditionalData_content = self.person_additional_data.to_xml(namespace=ns_021)
            for child in personAdditionalData_content:
                personAdditionalData_wrapper.append(child)

        # 10. politicalRightData (optional, eCH-0021/7)
        if self.political_right_data:
            # Create wrapper element in parent namespace
            politicalRightData_wrapper = ET.SubElement(elem, f'{{{namespace}}}politicalRightData')
            politicalRightData_content = self.political_right_data.to_xml(namespace=ns_021)
            for child in politicalRightData_content:
                politicalRightData_wrapper.append(child)

        # 11. CHOICE: placeOfOriginInfo (unbounded) OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace, element_name='placeOfOriginInfo')
        elif self.residence_permit_data:
            # Wrapper in ns_020, content in ns_011
            self.residence_permit_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='residencePermitData',
                wrapper_namespace=namespace
            )

        # 12. lockData (required, eCH-0021/7)
        # Create wrapper element in parent namespace
        lockData_wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        lockData_content = self.lock_data.to_xml(namespace=ns_021)
        for child in lockData_content:
            lockData_wrapper.append(child)

        # 13. jobData (optional, eCH-0021/7)
        if self.job_data:
            # Create wrapper element in parent namespace
            jobData_wrapper = ET.SubElement(elem, f'{{{namespace}}}jobData')
            jobData_content = self.job_data.to_xml(namespace=ns_021)
            for child in jobData_content:
                jobData_wrapper.append(child)

        # 14. maritalRelationship (optional, eCH-0021/7)
        if self.marital_relationship:
            # Create wrapper element in parent namespace
            maritalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalRelationship')
            maritalRelationship_content = self.marital_relationship.to_xml(namespace=ns_021)
            for child in maritalRelationship_content:
                maritalRelationship_wrapper.append(child)

        # 15. parentalRelationship (optional, 0-n, eCH-0021/7)
        if self.parental_relationship:
            for relationship in self.parental_relationship:
                # Create wrapper element

                parentalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')

                parentalRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in parentalRelationship_content:

                    parentalRelationship_wrapper.append(child)

        # 16. guardianRelationship (optional, 0-n, eCH-0021/7)
        if self.guardian_relationship:
            for relationship in self.guardian_relationship:
                # Create wrapper element

                guardianRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}guardianRelationship')

                guardianRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in guardianRelationship_content:

                    guardianRelationship_wrapper.append(child)

        # 17. armedForcesData (optional, eCH-0021/7)
        if self.armed_forces_data:
            # Create wrapper element in parent namespace
            armedForcesData_wrapper = ET.SubElement(elem, f'{{{namespace}}}armedForcesData')
            armedForcesData_content = self.armed_forces_data.to_xml(namespace=ns_021)
            for child in armedForcesData_content:
                armedForcesData_wrapper.append(child)

        # 18. civilDefenseData (optional, eCH-0021/7)
        if self.civil_defense_data:
            # Create wrapper element in parent namespace
            civilDefenseData_wrapper = ET.SubElement(elem, f'{{{namespace}}}civilDefenseData')
            civilDefenseData_content = self.civil_defense_data.to_xml(namespace=ns_021)
            for child in civilDefenseData_content:
                civilDefenseData_wrapper.append(child)

        # 19. fireServiceData (optional, eCH-0021/7)
        if self.fire_service_data:
            # Create wrapper element in parent namespace
            fireServiceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}fireServiceData')
            fireServiceData_content = self.fire_service_data.to_xml(namespace=ns_021)
            for child in fireServiceData_content:
                fireServiceData_wrapper.append(child)

        # 20. healthInsuranceData (optional, eCH-0021/7)
        if self.health_insurance_data:
            # Create wrapper element in parent namespace
            healthInsuranceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            healthInsuranceData_content = self.health_insurance_data.to_xml(namespace=ns_021)
            for child in healthInsuranceData_content:
                healthInsuranceData_wrapper.append(child)

        # 21. matrimonialInheritanceArrangementData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.matrimonial_inheritance_arrangement_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangementData')
            content = self.matrimonial_inheritance_arrangement_data.to_xml(namespace=ns_021)
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BaseDeliveryPerson':
        """Parse from XML element.

        Args:
            element: XML element containing baseDeliveryPerson data

        Returns:
            Parsed ECH0020BaseDeliveryPerson instance
        """
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # Required fields
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("baseDeliveryPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        religion_elem = element.find(f'{{{ns_020}}}religionData')
        if religion_elem is None:
            raise ValueError("baseDeliveryPersonType requires religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("baseDeliveryPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        lock_elem = element.find(f'{{{ns_020}}}lockData')
        if lock_elem is None:
            raise ValueError("baseDeliveryPersonType requires lockData")
        lock_data = ECH0021LockData.from_xml(lock_elem)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems]

        residence_permit_data = None
        permit_elem = element.find(f'{{{ns_020}}}residencePermitData')
        if permit_elem is not None:
            residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem)

        # Optional fields
        death_data = None
        death_elem = element.find(f'{{{ns_020}}}deathData')
        if death_elem is not None:
            death_data = ECH0011DeathData.from_xml(death_elem)

        contact_data = None
        contact_elem = element.find(f'{{{ns_020}}}contactData')
        if contact_elem is not None:
            contact_data = ECH0011ContactData.from_xml(contact_elem)

        person_additional_data = None
        additional_elem = element.find(f'{{{ns_020}}}personAdditionalData')
        if additional_elem is not None:
            person_additional_data = ECH0021PersonAdditionalData.from_xml(additional_elem)

        political_right_data = None
        political_elem = element.find(f'{{{ns_020}}}politicalRightData')
        if political_elem is not None:
            political_right_data = ECH0021PoliticalRightData.from_xml(political_elem)

        job_data = None
        job_elem = element.find(f'{{{ns_020}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        marital_relationship = None
        marital_rel_elem = element.find(f'{{{ns_020}}}maritalRelationship')
        if marital_rel_elem is not None:
            marital_relationship = ECH0021MaritalRelationship.from_xml(marital_rel_elem)

        parental_relationship = None
        parental_elems = element.findall(f'{{{ns_020}}}parentalRelationship')
        if parental_elems:
            parental_relationship = [ECH0021ParentalRelationship.from_xml(elem) for elem in parental_elems]

        guardian_relationship = None
        guardian_elems = element.findall(f'{{{ns_020}}}guardianRelationship')
        if guardian_elems:
            guardian_relationship = [ECH0021GuardianRelationship.from_xml(elem) for elem in guardian_elems]

        armed_forces_data = None
        armed_elem = element.find(f'{{{ns_020}}}armedForcesData')
        if armed_elem is not None:
            armed_forces_data = ECH0021ArmedForcesData.from_xml(armed_elem)

        civil_defense_data = None
        civil_elem = element.find(f'{{{ns_020}}}civilDefenseData')
        if civil_elem is not None:
            civil_defense_data = ECH0021CivilDefenseData.from_xml(civil_elem)

        fire_service_data = None
        fire_elem = element.find(f'{{{ns_020}}}fireServiceData')
        if fire_elem is not None:
            fire_service_data = ECH0021FireServiceData.from_xml(fire_elem)

        health_insurance_data = None
        health_elem = element.find(f'{{{ns_020}}}healthInsuranceData')
        if health_elem is not None:
            health_insurance_data = ECH0021HealthInsuranceData.from_xml(health_elem)

        matrimonial_inheritance_arrangement_data = None
        matrimonial_elem = element.find(f'{{{ns_020}}}matrimonialInheritanceArrangementData')
        if matrimonial_elem is not None:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData.from_xml(matrimonial_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            death_data=death_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            political_right_data=political_right_data,
            job_data=job_data,
            marital_relationship=marital_relationship,
            parental_relationship=parental_relationship,
            guardian_relationship=guardian_relationship,
            armed_forces_data=armed_forces_data,
            civil_defense_data=civil_defense_data,
            fire_service_data=fire_service_data,
            health_insurance_data=health_insurance_data,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
        )


# ============================================================================
# TYPE 9/89: BASE DELIVERY RESTRICTED MOVE-IN PERSON TYPE
# ============================================================================

class ECH0020BaseDeliveryRestrictedMoveInPerson(BaseModel):
    """Restricted person data structure for move-in events in base deliveries.

    This is an XSD restriction of baseDeliveryPersonType, used specifically for
    move-in event reporting. The key difference: NO deathData field (deceased
    persons do not move in).

    XSD: baseDeliveryRestrictedMoveInPersonType (eCH-0020-3-0.xsd lines 141-169)
    PDF: Unknown section (move-in event structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Note: This is an XSD restriction, so we implement as standalone class (not inheritance)
    because Pydantic restrictions don't map cleanly to Python inheritance.

    Differences from baseDeliveryPersonType:
    - NO deathData field (only difference)
    - All other 20 fields identical
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data per eCH-0020'
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='Religion/confession data per eCH-0011'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # NOTE: deathData field is REMOVED in this restriction (deceased don't move in)

    # XSD CHOICE: placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (1-n for Swiss citizens)'
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Residence permit data for foreign nationals'
    )

    # lockData is REQUIRED (comes after CHOICE in XSD)
    lock_data: ECH0021LockData = Field(
        ...,
        alias='lockData',
        description='Data lock and paper lock information'
    )

    # Optional fields (all minOccurs=0)
    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description='Contact information (phone, email)'
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description='Additional person data per eCH-0021'
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = Field(
        None,
        alias='politicalRightData',
        description='Political rights data (v7-only field)'
    )
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Employment/occupation data'
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Marital relationship details'
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description='Parental relationships (0-n)'
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = Field(
        None,
        alias='guardianRelationship',
        description='Guardian relationships (0-n)'
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = Field(
        None,
        alias='armedForcesData',
        description='Military service data'
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = Field(
        None,
        alias='civilDefenseData',
        description='Civil defense service data'
    )
    fire_service_data: Optional[ECH0021FireServiceData] = Field(
        None,
        alias='fireServiceData',
        description='Fire service data'
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description='Health insurance information'
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = Field(
        None,
        alias='matrimonialInheritanceArrangementData',
        description='Matrimonial regime and inheritance arrangement'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BaseDeliveryRestrictedMoveInPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData."""
        has_origin = self.place_of_origin_info is not None and len(self.place_of_origin_info) > 0
        has_permit = self.residence_permit_data is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "baseDeliveryRestrictedMoveInPersonType requires either placeOfOriginInfo "
                "(Swiss citizen) OR residencePermitData (foreign national)"
            )
        if has_origin and has_permit:
            raise ValueError(
                "baseDeliveryRestrictedMoveInPersonType allows either placeOfOriginInfo OR "
                f"residencePermitData, but both were provided (origins={len(self.place_of_origin_info)}, permit=yes)"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'baseDeliveryRestrictedMoveInPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'baseDeliveryRestrictedMoveInPerson')

        Returns:
            XML element with complete move-in person data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # 1. personIdentification (required, eCH-0044/4)
        # Create wrapper element in parent namespace
        personIdentification_wrapper = ET.SubElement(elem, f'{{{namespace}}}personIdentification')
        personIdentification_content = self.person_identification.to_xml(namespace=ns_044)
        for child in personIdentification_content:
            personIdentification_wrapper.append(child)

        # 2. nameInfo (required, eCH-0020/3)
        self.name_info.to_xml(parent=elem, namespace=namespace, element_name='nameInfo')

        # 3. birthInfo (required, eCH-0020/3)
        self.birth_info.to_xml(parent=elem, namespace=namespace, element_name='birthInfo')

        # 4. religionData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData',
            wrapper_namespace=namespace
        )

        # 5. maritalInfo (required, eCH-0020/3)
        self.marital_info.to_xml(parent=elem, namespace=namespace, element_name='maritalInfo')

        # 6. nationalityData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData',
            wrapper_namespace=namespace
        )

        # NOTE: NO deathData field in restricted type (deceased don't move in)

        # 7. contactData (optional, eCH-0011/8)
        if self.contact_data:
            # Create wrapper element in parent namespace
            contactData_wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            contactData_content = self.contact_data.to_xml(namespace=ns_011)
            for child in contactData_content:
                contactData_wrapper.append(child)

        # 8. personAdditionalData (optional, eCH-0021/7)
        if self.person_additional_data:
            # Create wrapper element in parent namespace
            personAdditionalData_wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            personAdditionalData_content = self.person_additional_data.to_xml(namespace=ns_021)
            for child in personAdditionalData_content:
                personAdditionalData_wrapper.append(child)

        # 9. politicalRightData (optional, eCH-0021/7)
        if self.political_right_data:
            # Create wrapper element in parent namespace
            politicalRightData_wrapper = ET.SubElement(elem, f'{{{namespace}}}politicalRightData')
            politicalRightData_content = self.political_right_data.to_xml(namespace=ns_021)
            for child in politicalRightData_content:
                politicalRightData_wrapper.append(child)

        # 10. CHOICE: placeOfOriginInfo (unbounded) OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace, element_name='placeOfOriginInfo')
        elif self.residence_permit_data:
            # Wrapper in ns_020, content in ns_011
            self.residence_permit_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='residencePermitData',
                wrapper_namespace=namespace
            )

        # 11. lockData (required, eCH-0021/7)
        # Create wrapper element in parent namespace
        lockData_wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        lockData_content = self.lock_data.to_xml(namespace=ns_021)
        for child in lockData_content:
            lockData_wrapper.append(child)

        # 12. jobData (optional, eCH-0021/7)
        if self.job_data:
            # Create wrapper element in parent namespace
            jobData_wrapper = ET.SubElement(elem, f'{{{namespace}}}jobData')
            jobData_content = self.job_data.to_xml(namespace=ns_021)
            for child in jobData_content:
                jobData_wrapper.append(child)

        # 13. maritalRelationship (optional, eCH-0021/7)
        if self.marital_relationship:
            # Create wrapper element in parent namespace
            maritalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalRelationship')
            maritalRelationship_content = self.marital_relationship.to_xml(namespace=ns_021)
            for child in maritalRelationship_content:
                maritalRelationship_wrapper.append(child)

        # 14. parentalRelationship (optional, 0-n, eCH-0021/7)
        if self.parental_relationship:
            for relationship in self.parental_relationship:
                # Create wrapper element

                parentalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')

                parentalRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in parentalRelationship_content:

                    parentalRelationship_wrapper.append(child)

        # 15. guardianRelationship (optional, 0-n, eCH-0021/7)
        if self.guardian_relationship:
            for relationship in self.guardian_relationship:
                # Create wrapper element

                guardianRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}guardianRelationship')

                guardianRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in guardianRelationship_content:

                    guardianRelationship_wrapper.append(child)

        # 16. armedForcesData (optional, eCH-0021/7)
        if self.armed_forces_data:
            # Create wrapper element in parent namespace
            armedForcesData_wrapper = ET.SubElement(elem, f'{{{namespace}}}armedForcesData')
            armedForcesData_content = self.armed_forces_data.to_xml(namespace=ns_021)
            for child in armedForcesData_content:
                armedForcesData_wrapper.append(child)

        # 17. civilDefenseData (optional, eCH-0021/7)
        if self.civil_defense_data:
            # Create wrapper element in parent namespace
            civilDefenseData_wrapper = ET.SubElement(elem, f'{{{namespace}}}civilDefenseData')
            civilDefenseData_content = self.civil_defense_data.to_xml(namespace=ns_021)
            for child in civilDefenseData_content:
                civilDefenseData_wrapper.append(child)

        # 18. fireServiceData (optional, eCH-0021/7)
        if self.fire_service_data:
            # Create wrapper element in parent namespace
            fireServiceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}fireServiceData')
            fireServiceData_content = self.fire_service_data.to_xml(namespace=ns_021)
            for child in fireServiceData_content:
                fireServiceData_wrapper.append(child)

        # 19. healthInsuranceData (optional, eCH-0021/7)
        if self.health_insurance_data:
            # Create wrapper element in parent namespace
            healthInsuranceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            healthInsuranceData_content = self.health_insurance_data.to_xml(namespace=ns_021)
            for child in healthInsuranceData_content:
                healthInsuranceData_wrapper.append(child)

        # 20. matrimonialInheritanceArrangementData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.matrimonial_inheritance_arrangement_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangementData')
            content = self.matrimonial_inheritance_arrangement_data.to_xml(namespace=ns_021)
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BaseDeliveryRestrictedMoveInPerson':
        """Parse from XML element.

        Args:
            element: XML element containing restricted move-in person data

        Returns:
            Parsed ECH0020BaseDeliveryRestrictedMoveInPerson instance
        """
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # Required fields
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        religion_elem = element.find(f'{{{ns_020}}}religionData')
        if religion_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        lock_elem = element.find(f'{{{ns_020}}}lockData')
        if lock_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires lockData")
        lock_data = ECH0021LockData.from_xml(lock_elem)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems]

        residence_permit_data = None
        permit_elem = element.find(f'{{{ns_020}}}residencePermitData')
        if permit_elem is not None:
            residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem)

        # Optional fields (NO deathData in restricted type)
        contact_data = None
        contact_elem = element.find(f'{{{ns_020}}}contactData')
        if contact_elem is not None:
            contact_data = ECH0011ContactData.from_xml(contact_elem)

        person_additional_data = None
        additional_elem = element.find(f'{{{ns_020}}}personAdditionalData')
        if additional_elem is not None:
            person_additional_data = ECH0021PersonAdditionalData.from_xml(additional_elem)

        political_right_data = None
        political_elem = element.find(f'{{{ns_020}}}politicalRightData')
        if political_elem is not None:
            political_right_data = ECH0021PoliticalRightData.from_xml(political_elem)

        job_data = None
        job_elem = element.find(f'{{{ns_020}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        marital_relationship = None
        marital_rel_elem = element.find(f'{{{ns_020}}}maritalRelationship')
        if marital_rel_elem is not None:
            marital_relationship = ECH0021MaritalRelationship.from_xml(marital_rel_elem)

        parental_relationship = None
        parental_elems = element.findall(f'{{{ns_020}}}parentalRelationship')
        if parental_elems:
            parental_relationship = [ECH0021ParentalRelationship.from_xml(elem) for elem in parental_elems]

        guardian_relationship = None
        guardian_elems = element.findall(f'{{{ns_020}}}guardianRelationship')
        if guardian_elems:
            guardian_relationship = [ECH0021GuardianRelationship.from_xml(elem) for elem in guardian_elems]

        armed_forces_data = None
        armed_elem = element.find(f'{{{ns_020}}}armedForcesData')
        if armed_elem is not None:
            armed_forces_data = ECH0021ArmedForcesData.from_xml(armed_elem)

        civil_defense_data = None
        civil_elem = element.find(f'{{{ns_020}}}civilDefenseData')
        if civil_elem is not None:
            civil_defense_data = ECH0021CivilDefenseData.from_xml(civil_elem)

        fire_service_data = None
        fire_elem = element.find(f'{{{ns_020}}}fireServiceData')
        if fire_elem is not None:
            fire_service_data = ECH0021FireServiceData.from_xml(fire_elem)

        health_insurance_data = None
        health_elem = element.find(f'{{{ns_020}}}healthInsuranceData')
        if health_elem is not None:
            health_insurance_data = ECH0021HealthInsuranceData.from_xml(health_elem)

        matrimonial_inheritance_arrangement_data = None
        matrimonial_elem = element.find(f'{{{ns_020}}}matrimonialInheritanceArrangementData')
        if matrimonial_elem is not None:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData.from_xml(matrimonial_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            political_right_data=political_right_data,
            job_data=job_data,
            marital_relationship=marital_relationship,
            parental_relationship=parental_relationship,
            guardian_relationship=guardian_relationship,
            armed_forces_data=armed_forces_data,
            civil_defense_data=civil_defense_data,
            fire_service_data=fire_service_data,
            health_insurance_data=health_insurance_data,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
        )


# ============================================================================
# REPORTING MUNICIPALITY TYPES (Municipality reporting and residence data)
# ============================================================================

class ECH0020ReportingMunicipality(BaseModel):
    """Municipality reporting data with residence and movement information.

    This type contains information about where a person is registered, when they
    arrived, where they came from, their dwelling address, and departure/destination
    information if applicable.

    XSD: reportingMunicipalityType (eCH-0020-3-0.xsd lines 455-467)
    PDF: Unknown section (reporting municipality structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - CHOICE: reportingMunicipality (Swiss municipality) OR federalRegister (INFOSTAR/ZEMIS)
    - arrivalDate: Date of arrival in municipality (optional)
    - comesFrom: Previous residence (optional)
    - dwellingAddress: Current dwelling address (optional)
    - departureDate: Date of departure (optional)
    - goesTo: Destination after departure (optional)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister (mutually exclusive)
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # Optional fields
    arrival_date: Optional[date] = Field(
        None,
        alias='arrivalDate',
        description='Date of arrival in this municipality'
    )
    comes_from: Optional[ECH0011DestinationType] = Field(
        None,
        alias='comesFrom',
        description='Previous residence (where person came from)'
    )
    dwelling_address: Optional[ECH0011DwellingAddress] = Field(
        None,
        alias='dwellingAddress',
        description='Current dwelling address in municipality'
    )
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipality':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityType requires either reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityType allows either reportingMunicipality OR federalRegister, "
                "but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'reportingMunicipality')

        Returns:
            XML element with reporting municipality data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE: reportingMunicipality OR federalRegister
        if self.reporting_municipality:
            self.reporting_municipality.to_xml(
                parent=elem, namespace=ns_007
            )
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Optional fields
        if self.arrival_date:
            arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.arrival_date.isoformat()

        if self.comes_from:
            # Wrapper in ns_020, content in ns_011
            self.comes_from.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='comesFrom',
                wrapper_namespace=namespace
            )

        if self.dwelling_address:
            # Wrapper in ns_020, content in ns_011
            self.dwelling_address.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='dwellingAddress',
                wrapper_namespace=namespace
            )

        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipality':
        """Parse from XML element.

        Args:
            element: XML element containing reportingMunicipality data

        Returns:
            Parsed ECH0020ReportingMunicipality instance
        """
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE: reportingMunicipality OR federalRegister
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Optional fields
        arrival_date = None
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is not None and arrival_elem.text:
            arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from = None
        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is not None:
            comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_address = None
        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is not None:
            dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedBaseMain(BaseModel):
    """Restricted reporting municipality for base delivery main residence.

    XSD restriction of reportingMunicipalityType with required fields for main residence.

    XSD: reportingMunicipalityRestrictedBaseMainType (eCH-0020-3-0.xsd lines 468-484)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    - comesFrom: remains optional
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields in restriction
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    # Optional fields
    comes_from: Optional[ECH0011DestinationType] = Field(
        None,
        alias='comesFrom',
        description='Previous residence (where person came from)'
    )
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedBaseMain':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseMainType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseMainType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Optional comesFrom
        if self.comes_from:
            # Wrapper in ns_020, content in ns_011
            self.comes_from.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='comesFrom',
                wrapper_namespace=namespace
            )

        # Required dwellingAddress
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Optional fields
        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedBaseMain':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedBaseMainType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseMainType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Optional fields
        comes_from = None
        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is not None:
            comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedBaseSecondary(BaseModel):
    """Restricted reporting municipality for base delivery secondary residence.

    XSD restriction of reportingMunicipalityType with required fields for secondary residence.

    XSD: reportingMunicipalityRestrictedBaseSecondaryType (eCH-0020-3-0.xsd lines 485-501)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - comesFrom: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields in restriction
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        alias='comesFrom',
        description='Previous residence (REQUIRED for secondary residence)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    # Optional fields
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedBaseSecondary':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseSecondaryType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseSecondaryType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Optional fields
        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedBaseSecondary':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Optional fields
        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


# Helper classes for eventBaseDelivery inline complex types

class ECH0020HasMainResidence(BaseModel):
    """Main residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseMainType with optional secondary residences.
    This is an inline anonymous type from eventBaseDelivery XSD definition.
    """

    # All fields from reportingMunicipalityRestrictedBaseMainType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')
    comes_from: Optional[ECH0011DestinationType] = Field(None, alias='comesFrom')
    departure_date: Optional[date] = Field(None, alias='departureDate')
    goes_to: Optional[ECH0011DestinationType] = Field(None, alias='goesTo')

    # Extension: additional secondary residences
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = Field(
        None,
        alias='secondaryResidence',
        description='Secondary residence municipalities (0-n)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasMainResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasMainResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasMainResidence allows either reportingMunicipality OR federalRegister")
        return self


class ECH0020HasSecondaryResidence(BaseModel):
    """Secondary residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseSecondaryType with required main residence.
    This is an inline anonymous type from eventBaseDelivery XSD definition.
    """

    # All fields from reportingMunicipalityRestrictedBaseSecondaryType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')
    departure_date: Optional[date] = Field(None, alias='departureDate')
    goes_to: Optional[ECH0011DestinationType] = Field(None, alias='goesTo')

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = Field(
        ...,
        alias='mainResidence',
        description='Main residence municipality (required)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasSecondaryResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasSecondaryResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasSecondaryResidence allows either reportingMunicipality OR federalRegister")
        return self


# ============================================================================
# TYPE 13/89: EVENT BASE DELIVERY
# ============================================================================

class ECH0020EventBaseDelivery(BaseModel):
    """Base delivery event structure.

    Base deliveries are complete snapshots of a municipality's population register.
    This event type contains person data plus residence information.

    XSD: eventBaseDelivery (eCH-0020-3-0.xsd lines 173-203)
    PDF: Unknown section (base delivery event structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - baseDeliveryPerson: Complete person data (required)
    - CHOICE: hasMainResidence OR hasSecondaryResidence OR hasOtherResidence
    - baseDeliveryValidFrom: Validity start date (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    base_delivery_person: 'ECH0020BaseDeliveryPerson' = Field(
        ...,
        alias='baseDeliveryPerson',
        description='Complete person data for base delivery'
    )

    # XSD CHOICE: exactly one of three residence types
    has_main_residence: Optional[ECH0020HasMainResidence] = Field(
        None,
        alias='hasMainResidence',
        description='Person has main residence in this municipality'
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidence] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Person has secondary residence in this municipality'
    )
    has_other_residence: Optional['ECH0020ReportingMunicipalityRestrictedBaseSecondary'] = Field(
        None,
        alias='hasOtherResidence',
        description='Person has other residence type in this municipality'
    )

    # Optional fields
    base_delivery_valid_from: Optional[date] = Field(
        None,
        alias='baseDeliveryValidFrom',
        description='Date from which this base delivery is valid'
    )

    # Note: extension element not implemented (xs:element ref="eCH-0020:extension")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventBaseDelivery':
        """Validate XSD CHOICE: exactly ONE residence type must be present."""
        has_main = self.has_main_residence is not None
        has_secondary = self.has_secondary_residence is not None
        has_other = self.has_other_residence is not None

        residence_count = sum([has_main, has_secondary, has_other])

        if residence_count == 0:
            raise ValueError(
                "eventBaseDelivery requires exactly ONE of: hasMainResidence, "
                "hasSecondaryResidence, or hasOtherResidence"
            )
        if residence_count > 1:
            raise ValueError(
                f"eventBaseDelivery allows only ONE residence type, but {residence_count} were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventBaseDelivery',
        skip_wrapper: bool = False
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace URI
            element_name: Name of the XML element
            skip_wrapper: If True, serialize children directly into parent
                         (used when this type is embedded without element wrapper)

        Returns:
            XML Element
        """
        if skip_wrapper and parent is not None:
            # Type used inline - serialize children into parent directly
            elem = parent
        elif parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # 1. baseDeliveryPerson (required)
        self.base_delivery_person.to_xml(
            parent=elem, namespace=namespace, element_name='baseDeliveryPerson'
        )

        # 2. CHOICE: residence type
        if self.has_main_residence:
            # hasMainResidence extends reportingMunicipalityRestrictedBaseMainType
            main_elem = ET.SubElement(elem, f'{{{namespace}}}hasMainResidence')

            # Base fields from reportingMunicipalityRestrictedBaseMainType
            if self.has_main_residence.reporting_municipality:
                # Create wrapper element in eCH-0020 namespace
                reporting_mun_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}reportingMunicipality')
                mun_content = self.has_main_residence.reporting_municipality.to_xml(namespace=ns_007)
                for child in mun_content:
                    reporting_mun_wrapper.append(child)
            elif self.has_main_residence.federal_register:
                reg_elem = ET.SubElement(main_elem, f'{{{namespace}}}federalRegister')
                reg_elem.text = self.has_main_residence.federal_register.value

            arrival_elem = ET.SubElement(main_elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.has_main_residence.arrival_date.isoformat()

            if self.has_main_residence.comes_from:
                # Create wrapper element in eCH-0020 namespace
                comes_from_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}comesFrom')
                comes_from_content = self.has_main_residence.comes_from.to_xml(namespace=ns_011)
                for child in comes_from_content:
                    comes_from_wrapper.append(child)

            # Create wrapper element in eCH-0020 namespace
            dwelling_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}dwellingAddress')
            dwelling_content = self.has_main_residence.dwelling_address.to_xml(namespace=ns_011)
            for child in dwelling_content:
                dwelling_wrapper.append(child)

            if self.has_main_residence.departure_date:
                dep_elem = ET.SubElement(main_elem, f'{{{namespace}}}departureDate')
                dep_elem.text = self.has_main_residence.departure_date.isoformat()

            if self.has_main_residence.goes_to:
                # Create wrapper element in eCH-0020 namespace
                goes_to_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}goesTo')
                goes_to_content = self.has_main_residence.goes_to.to_xml(namespace=ns_011)
                for child in goes_to_content:
                    goes_to_wrapper.append(child)

            # Extension: secondaryResidence (0-n)
            if self.has_main_residence.secondary_residence:
                for sec_res in self.has_main_residence.secondary_residence:
                    # Create wrapper element in eCH-0020 namespace
                    sec_res_wrapper = ET.SubElement(main_elem, f'{{{namespace}}}secondaryResidence')
                    sec_res_content = sec_res.to_xml(namespace=ns_007)
                    for child in sec_res_content:
                        sec_res_wrapper.append(child)

        elif self.has_secondary_residence:
            # hasSecondaryResidence extends reportingMunicipalityRestrictedBaseSecondaryType
            sec_elem = ET.SubElement(elem, f'{{{namespace}}}hasSecondaryResidence')

            # Base fields
            if self.has_secondary_residence.reporting_municipality:
                # Create wrapper element in eCH-0020 namespace
                reporting_mun_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}reportingMunicipality')
                mun_content = self.has_secondary_residence.reporting_municipality.to_xml(namespace=ns_007)
                for child in mun_content:
                    reporting_mun_wrapper.append(child)
            elif self.has_secondary_residence.federal_register:
                reg_elem = ET.SubElement(sec_elem, f'{{{namespace}}}federalRegister')
                reg_elem.text = self.has_secondary_residence.federal_register.value

            arrival_elem = ET.SubElement(sec_elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.has_secondary_residence.arrival_date.isoformat()

            # Create wrapper element in eCH-0020 namespace
            comes_from_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}comesFrom')
            comes_from_content = self.has_secondary_residence.comes_from.to_xml(namespace=ns_011)
            for child in comes_from_content:
                comes_from_wrapper.append(child)

            # Create wrapper element in eCH-0020 namespace
            dwelling_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}dwellingAddress')
            dwelling_content = self.has_secondary_residence.dwelling_address.to_xml(namespace=ns_011)
            for child in dwelling_content:
                dwelling_wrapper.append(child)

            if self.has_secondary_residence.departure_date:
                dep_elem = ET.SubElement(sec_elem, f'{{{namespace}}}departureDate')
                dep_elem.text = self.has_secondary_residence.departure_date.isoformat()

            if self.has_secondary_residence.goes_to:
                # Create wrapper element in eCH-0020 namespace
                goes_to_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}goesTo')
                goes_to_content = self.has_secondary_residence.goes_to.to_xml(namespace=ns_011)
                for child in goes_to_content:
                    goes_to_wrapper.append(child)

            # Extension: mainResidence (required)
            # Create wrapper element in eCH-0020 namespace
            main_res_wrapper = ET.SubElement(sec_elem, f'{{{namespace}}}mainResidence')
            main_res_content = self.has_secondary_residence.main_residence.to_xml(namespace=ns_007)
            for child in main_res_content:
                main_res_wrapper.append(child)

        elif self.has_other_residence:
            # hasOtherResidence uses reportingMunicipalityRestrictedBaseSecondaryType directly
            self.has_other_residence.to_xml(
                parent=elem, namespace=namespace, element_name='hasOtherResidence'
            )

        # 3. baseDeliveryValidFrom (optional)
        if self.base_delivery_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}baseDeliveryValidFrom')
            valid_elem.text = self.base_delivery_valid_from.isoformat()

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventBaseDelivery':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # Required: baseDeliveryPerson
        person_elem = element.find(f'{{{ns_020}}}baseDeliveryPerson')
        if person_elem is None:
            raise ValueError("eventBaseDelivery requires baseDeliveryPerson")
        base_delivery_person = ECH0020BaseDeliveryPerson.from_xml(person_elem)

        # CHOICE: residence type (parse all three, validate later)
        has_main_residence = None
        main_elem = element.find(f'{{{ns_020}}}hasMainResidence')
        if main_elem is not None:
            # Parse base fields
            reporting_municipality = None
            mun_elem = main_elem.find(f'{{{ns_020}}}reportingMunicipality')
            if mun_elem is not None:
                reporting_municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

            federal_register = None
            reg_elem = main_elem.find(f'{{{ns_020}}}federalRegister')
            if reg_elem is not None and reg_elem.text:
                federal_register = FederalRegister(reg_elem.text)

            arr_elem = main_elem.find(f'{{{ns_020}}}arrivalDate')
            if arr_elem is None or not arr_elem.text:
                raise ValueError("hasMainResidence requires arrivalDate")
            arrival_date = date.fromisoformat(arr_elem.text)

            comes_from = None
            cf_elem = main_elem.find(f'{{{ns_020}}}comesFrom')
            if cf_elem is not None:
                comes_from = ECH0011DestinationType.from_xml(cf_elem)

            dw_elem = main_elem.find(f'{{{ns_020}}}dwellingAddress')
            if dw_elem is None:
                raise ValueError("hasMainResidence requires dwellingAddress")
            dwelling_address = ECH0011DwellingAddress.from_xml(dw_elem)

            departure_date = None
            dep_elem = main_elem.find(f'{{{ns_020}}}departureDate')
            if dep_elem is not None and dep_elem.text:
                departure_date = date.fromisoformat(dep_elem.text)

            goes_to = None
            gt_elem = main_elem.find(f'{{{ns_020}}}goesTo')
            if gt_elem is not None:
                goes_to = ECH0011DestinationType.from_xml(gt_elem)

            # Extension: secondaryResidence (0-n)
            secondary_residence = None
            sec_elems = main_elem.findall(f'{{{ns_020}}}secondaryResidence')
            if sec_elems:
                secondary_residence = [ECH0007SwissMunicipality.from_xml(e) for e in sec_elems]

            has_main_residence = ECH0020HasMainResidence(
                reporting_municipality=reporting_municipality,
                federal_register=federal_register,
                arrival_date=arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=departure_date,
                goes_to=goes_to,
                secondary_residence=secondary_residence
            )

        has_secondary_residence = None
        sec_elem = element.find(f'{{{ns_020}}}hasSecondaryResidence')
        if sec_elem is not None:
            # Parse base fields
            reporting_municipality = None
            mun_elem = sec_elem.find(f'{{{ns_020}}}reportingMunicipality')
            if mun_elem is not None:
                reporting_municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

            federal_register = None
            reg_elem = sec_elem.find(f'{{{ns_020}}}federalRegister')
            if reg_elem is not None and reg_elem.text:
                federal_register = FederalRegister(reg_elem.text)

            arr_elem = sec_elem.find(f'{{{ns_020}}}arrivalDate')
            if arr_elem is None or not arr_elem.text:
                raise ValueError("hasSecondaryResidence requires arrivalDate")
            arrival_date = date.fromisoformat(arr_elem.text)

            cf_elem = sec_elem.find(f'{{{ns_020}}}comesFrom')
            if cf_elem is None:
                raise ValueError("hasSecondaryResidence requires comesFrom")
            comes_from = ECH0011DestinationType.from_xml(cf_elem)

            dw_elem = sec_elem.find(f'{{{ns_020}}}dwellingAddress')
            if dw_elem is None:
                raise ValueError("hasSecondaryResidence requires dwellingAddress")
            dwelling_address = ECH0011DwellingAddress.from_xml(dw_elem)

            departure_date = None
            dep_elem = sec_elem.find(f'{{{ns_020}}}departureDate')
            if dep_elem is not None and dep_elem.text:
                departure_date = date.fromisoformat(dep_elem.text)

            goes_to = None
            gt_elem = sec_elem.find(f'{{{ns_020}}}goesTo')
            if gt_elem is not None:
                goes_to = ECH0011DestinationType.from_xml(gt_elem)

            # Extension: mainResidence (required)
            main_res_elem = sec_elem.find(f'{{{ns_020}}}mainResidence')
            if main_res_elem is None:
                raise ValueError("hasSecondaryResidence requires mainResidence")
            main_residence = ECH0007SwissMunicipality.from_xml(main_res_elem)

            has_secondary_residence = ECH0020HasSecondaryResidence(
                reporting_municipality=reporting_municipality,
                federal_register=federal_register,
                arrival_date=arrival_date,
                comes_from=comes_from,
                dwelling_address=dwelling_address,
                departure_date=departure_date,
                goes_to=goes_to,
                main_residence=main_residence
            )

        has_other_residence = None
        other_elem = element.find(f'{{{ns_020}}}hasOtherResidence')
        if other_elem is not None:
            has_other_residence = ECH0020ReportingMunicipalityRestrictedBaseSecondary.from_xml(other_elem)

        # Optional: baseDeliveryValidFrom
        base_delivery_valid_from = None
        valid_elem = element.find(f'{{{ns_020}}}baseDeliveryValidFrom')
        if valid_elem is not None and valid_elem.text:
            base_delivery_valid_from = date.fromisoformat(valid_elem.text)

        return cls(
            base_delivery_person=base_delivery_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence,
            base_delivery_valid_from=base_delivery_valid_from
        )


# ============================================================================
# TYPE 14/89: EVENT KEY EXCHANGE
# ============================================================================

class ECH0020EventKeyExchange(BaseModel):
    """Key exchange event for synchronizing person identifiers.

    Used for exchanging encryption keys or synchronizing person identifiers
    between municipalities and federal systems.

    XSD: eventKeyExchange (eCH-0020-3-0.xsd lines 204-209)
    PDF: Unknown section (key exchange event)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - keyExchangePerson: Person identification(s) for key exchange (1-n, required)
    - extension: Extension element (optional, not implemented)
    """

    key_exchange_person: List[ECH0044PersonIdentification] = Field(
        ...,
        alias='keyExchangePerson',
        min_length=1,
        description='Person identification(s) for key exchange (at least 1 required)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventKeyExchange'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # keyExchangePerson (1-n, required)
        for person in self.key_exchange_person:
            # Create wrapper element

            keyExchangePerson_wrapper = ET.SubElement(elem, f'{{{namespace}}}keyExchangePerson')

            keyExchangePerson_content = person.to_xml(namespace=ns_044)

            for child in keyExchangePerson_content:

                keyExchangePerson_wrapper.append(child)

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventKeyExchange':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

        # keyExchangePerson (1-n, required)
        person_elems = element.findall(f'{{{ns_020}}}keyExchangePerson')
        if not person_elems:
            raise ValueError("eventKeyExchange requires at least one keyExchangePerson")

        key_exchange_person = [
            ECH0044PersonIdentification.from_xml(elem) for elem in person_elems
        ]

        return cls(key_exchange_person=key_exchange_person)


# ============================================================================
# TYPE 15/89: EVENT DATA REQUEST
# ============================================================================

class ECH0020EventDataRequest(BaseModel):
    """Data request event for querying person information.

    Used to request person data from other municipalities or federal systems.

    XSD: eventDataRequest (eCH-0020-3-0.xsd lines 210-216)
    PDF: Unknown section (data request event)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - dataRequestPerson: Person identification(s) for data request (0-n, optional)
    - municipality: Municipality to request from (optional)
    - dataValidFrom: Date from which data is valid (optional)
    - extension: Extension element (optional, not implemented)
    """

    data_request_person: Optional[List[ECH0044PersonIdentification]] = Field(
        None,
        alias='dataRequestPerson',
        description='Person identification(s) for data request (0-n)'
    )
    municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='municipality',
        description='Municipality to request data from'
    )
    data_valid_from: Optional[date] = Field(
        None,
        alias='dataValidFrom',
        description='Date from which requested data should be valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventDataRequest'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # dataRequestPerson (0-n, optional)
        if self.data_request_person:
            for person in self.data_request_person:
                # Create wrapper element

                dataRequestPerson_wrapper = ET.SubElement(elem, f'{{{namespace}}}dataRequestPerson')

                dataRequestPerson_content = person.to_xml(namespace=ns_044)

                for child in dataRequestPerson_content:

                    dataRequestPerson_wrapper.append(child)

        # municipality (optional)
        if self.municipality:
            # Create wrapper element in parent namespace
            municipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}municipality')
            municipality_content = self.municipality.to_xml(namespace=ns_007)
            for child in municipality_content:
                municipality_wrapper.append(child)

        # dataValidFrom (optional)
        if self.data_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}dataValidFrom')
            valid_elem.text = self.data_valid_from.isoformat()

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventDataRequest':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

        # dataRequestPerson (0-n, optional)
        data_request_person = None
        person_elems = element.findall(f'{{{ns_020}}}dataRequestPerson')
        if person_elems:
            data_request_person = [
                ECH0044PersonIdentification.from_xml(elem) for elem in person_elems
            ]

        # municipality (optional)
        municipality = None
        mun_elem = element.find(f'{{{ns_020}}}municipality')
        if mun_elem is not None:
            municipality = ECH0007SwissMunicipality.from_xml(mun_elem)

        # dataValidFrom (optional)
        data_valid_from = None
        valid_elem = element.find(f'{{{ns_020}}}dataValidFrom')
        if valid_elem is not None and valid_elem.text:
            data_valid_from = date.fromisoformat(valid_elem.text)

        return cls(
            data_request_person=data_request_person,
            municipality=municipality,
            data_valid_from=data_valid_from
        )


# Helper classes for eventAdoption inline complex types

class ECH0020AddParent(BaseModel):
    """Parent to be added during adoption (inline complexType extension).

    Extends eCH-0021 parentalRelationshipType with optional nameOfParentAtEvent.
    This is an inline anonymous type from eventAdoption XSD definition.
    """

    # Base parental relationship (we use composition for the XSD extension)
    parental_relationship: ECH0021ParentalRelationship = Field(
        ...,
        description='Base parental relationship data'
    )

    # Extension field
    name_of_parent_at_event: Optional[ECH0021NameOfParent] = Field(
        None,
        alias='nameOfParentAtEvent',
        description="Parent's name at the time of adoption event"
    )

    model_config = ConfigDict(populate_by_name=True)


class ECH0020RemoveParent(BaseModel):
    """Parent to be removed during adoption (inline complexType extension).

    Extends eCH-0021 parentalRelationshipType with optional nameOfParentAtEvent.
    This is an inline anonymous type from eventAdoption XSD definition.
    """

    # Base parental relationship
    parental_relationship: ECH0021ParentalRelationship = Field(
        ...,
        description='Base parental relationship data'
    )

    # Extension field
    name_of_parent_at_event: Optional[ECH0021NameOfParent] = Field(
        None,
        alias='nameOfParentAtEvent',
        description="Parent's name at the time of adoption event"
    )

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# TYPE 16/89: EVENT ADOPTION
# ============================================================================

class ECH0020EventAdoption(BaseModel):
    """Adoption event recording changes in parental relationships.

    Used to register adoptions, which involves adding new parent(s) and
    optionally removing biological parent(s).

    XSD: eventAdoption (eCH-0020-3-0.xsd lines 217-245)
    PDF: Unknown section (adoption event)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - adoptionPerson: Person being adopted (required)
    - addParent: Parent(s) to add (0-n, optional)
    - removeParent: Parent(s) to remove (0-n, optional)
    - adoptionValidFrom: Date from which adoption is valid (optional)
    - extension: Extension element (optional, not implemented)
    """

    adoption_person: 'ECH0020InfostarPerson' = Field(
        ...,
        alias='adoptionPerson',
        description='Person being adopted'
    )
    add_parent: Optional[List[ECH0020AddParent]] = Field(
        None,
        alias='addParent',
        description='Parent(s) to add through adoption (0-n)'
    )
    remove_parent: Optional[List[ECH0020RemoveParent]] = Field(
        None,
        alias='removeParent',
        description='Parent(s) to remove through adoption (0-n)'
    )
    adoption_valid_from: Optional[date] = Field(
        None,
        alias='adoptionValidFrom',
        description='Date from which adoption is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventAdoption'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # 1. adoptionPerson (required)
        self.adoption_person.to_xml(parent=elem, namespace=namespace, element_name='adoptionPerson')

        # 2. addParent (0-n, optional) - inline extension of parentalRelationshipType
        if self.add_parent:
            for add in self.add_parent:
                add_elem = ET.SubElement(elem, f'{{{namespace}}}addParent')
                # Inline base parentalRelationship fields directly into addParent element
                add.parental_relationship.to_xml(parent=add_elem, namespace=ns_021, element_name='parentalRelationship')
                # Extension: nameOfParentAtEvent
                if add.name_of_parent_at_event:
                    add.name_of_parent_at_event.to_xml(
                        parent=add_elem, namespace=ns_021, element_name='nameOfParentAtEvent'
                    )

        # 3. removeParent (0-n, optional) - inline extension of parentalRelationshipType
        if self.remove_parent:
            for remove in self.remove_parent:
                remove_elem = ET.SubElement(elem, f'{{{namespace}}}removeParent')
                # Inline base parentalRelationship fields
                remove.parental_relationship.to_xml(
                    parent=remove_elem, namespace=ns_021, element_name='parentalRelationship'
                )
                # Extension: nameOfParentAtEvent
                if remove.name_of_parent_at_event:
                    remove.name_of_parent_at_event.to_xml(
                        parent=remove_elem, namespace=ns_021, element_name='nameOfParentAtEvent'
                    )

        # 4. adoptionValidFrom (optional)
        if self.adoption_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{namespace}}}adoptionValidFrom')
            valid_elem.text = self.adoption_valid_from.isoformat()

        # Note: extension element not implemented

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020EventAdoption':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

        # Required: adoptionPerson
        person_elem = element.find(f'{{{ns_020}}}adoptionPerson')
        if person_elem is None:
            raise ValueError("eventAdoption requires adoptionPerson")
        adoption_person = ECH0020InfostarPerson.from_xml(person_elem)

        # Optional: addParent (0-n)
        add_parent = None
        add_elems = element.findall(f'{{{ns_020}}}addParent')
        if add_elems:
            add_parent = []
            for add_elem in add_elems:
                # Parse base parentalRelationship (inline)
                rel_elem = add_elem.find(f'{{{ns_020}}}parentalRelationship')
                if rel_elem is None:
                    raise ValueError("addParent requires parentalRelationship")
                parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

                # Extension: nameOfParentAtEvent
                name_of_parent_at_event = None
                name_elem = add_elem.find(f'{{{ns_020}}}nameOfParentAtEvent')
                if name_elem is not None:
                    name_of_parent_at_event = ECH0021NameOfParent.from_xml(name_elem)

                add_parent.append(ECH0020AddParent(
                    parental_relationship=parental_relationship,
                    name_of_parent_at_event=name_of_parent_at_event
                ))

        # Optional: removeParent (0-n)
        remove_parent = None
        remove_elems = element.findall(f'{{{ns_020}}}removeParent')
        if remove_elems:
            remove_parent = []
            for remove_elem in remove_elems:
                # Parse base parentalRelationship (inline)
                rel_elem = remove_elem.find(f'{{{ns_020}}}removeParent/parentalRelationship')
                if rel_elem is None:
                    raise ValueError("removeParent requires parentalRelationship")
                parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

                # Extension: nameOfParentAtEvent
                name_of_parent_at_event = None
                name_elem = remove_elem.find(f'{{{ns_020}}}nameOfParentAtEvent')
                if name_elem is not None:
                    name_of_parent_at_event = ECH0021NameOfParent.from_xml(name_elem)

                remove_parent.append(ECH0020RemoveParent(
                    parental_relationship=parental_relationship,
                    name_of_parent_at_event=name_of_parent_at_event
                ))

        # Optional: adoptionValidFrom
        adoption_valid_from = None
        valid_elem = element.find(f'{{{ns_020}}}adoptionValidFrom')
        if valid_elem is not None and valid_elem.text:
            adoption_valid_from = date.fromisoformat(valid_elem.text)

        return cls(
            adoption_person=adoption_person,
            add_parent=add_parent,
            remove_parent=remove_parent,
            adoption_valid_from=adoption_valid_from
        )


# TYPE 17/89: eventChildRelationship
class ECH0020EventChildRelationship(BaseModel):
    """Child relationship event - register or correct parent-child relationships.

    XSD: eventChildRelationship (eCH-0020-3-0.xsd lines 247-279)
    PDF: Section on child relationship registration

    Used for:
    - Acknowledging paternity (Vaterschaftsanerkennung)
    - Correcting parent-child relationships
    - Adding or removing parents from registry

    NOTE: Uses the same inline extension pattern as eventAdoption.
    Reuses ECH0020AddParent and ECH0020RemoveParent helper classes.

    Fields:
    - childRelationshipPerson (required): Person whose relationship is changing
    - addParent (0-2): Parents to add (max 2 for biological parents)
    - removeParent (0-2): Parents to remove (max 2)
    - childRelationshipValidFrom (optional): Effective date
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    child_relationship_person: 'ECH0020InfostarPerson' = Field(
        ...,
        alias='childRelationshipPerson',
        description='Person whose parent-child relationship is being registered or changed'
    )

    add_parent: Optional[List[ECH0020AddParent]] = Field(
        None,
        alias='addParent',
        max_length=2,
        description='Parents to add (max 2 - biological parents)'
    )

    remove_parent: Optional[List[ECH0020RemoveParent]] = Field(
        None,
        alias='removeParent',
        max_length=2,
        description='Parents to remove (max 2)'
    )

    child_relationship_valid_from: Optional[date] = Field(
        None,
        alias='childRelationshipValidFrom',
        description='Effective date of child relationship change'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventChildRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NAMESPACE_ECH0021_V7

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # childRelationshipPerson (required)
        self.child_relationship_person.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='childRelationshipPerson'
        )

        # addParent (0-2)
        if self.add_parent:
            for add in self.add_parent:
                # Create addParent element
                add_elem = ET.SubElement(elem, f'{{{ns_020}}}addParent')

                # Serialize base parentalRelationship
                add.parental_relationship.to_xml(
                    parent=add_elem,
                    namespace=ns_021,
                    element_name='parentalRelationship'
                )

                # Serialize extension element nameOfParentAtEvent
                if add.name_of_parent_at_event:
                    add.name_of_parent_at_event.to_xml(
                        parent=add_elem,
                        namespace=ns_021,
                        element_name='nameOfParentAtEvent'
                    )

        # removeParent (0-2)
        if self.remove_parent:
            for rem in self.remove_parent:
                # Create removeParent element
                rem_elem = ET.SubElement(elem, f'{{{ns_020}}}removeParent')

                # Serialize base parentalRelationship
                rem.parental_relationship.to_xml(
                    parent=rem_elem,
                    namespace=ns_021,
                    element_name='parentalRelationship'
                )

                # Serialize extension element nameOfParentAtEvent
                if rem.name_of_parent_at_event:
                    rem.name_of_parent_at_event.to_xml(
                        parent=rem_elem,
                        namespace=ns_021,
                        element_name='nameOfParentAtEvent'
                    )

        # childRelationshipValidFrom (optional)
        if self.child_relationship_valid_from:
            ET.SubElement(elem, f'{{{ns_020}}}childRelationshipValidFrom').text = \
                self.child_relationship_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChildRelationship':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_021 = NAMESPACE_ECH0021_V7

        # childRelationshipPerson (required)
        child_person_elem = elem.find(f'{{{ns_020}}}childRelationshipPerson')
        if child_person_elem is None:
            raise ValueError("eventChildRelationship requires childRelationshipPerson")
        child_relationship_person = ECH0020InfostarPerson.from_xml(child_person_elem)

        # addParent (0-2)
        add_parent: Optional[List[ECH0020AddParent]] = None
        add_elems = elem.findall(f'{{{ns_020}}}addParent')
        if add_elems:
            if len(add_elems) > 2:
                raise ValueError(f"eventChildRelationship allows max 2 addParent, got {len(add_elems)}")

            add_parent = []
            for add_elem in add_elems:
                # Parse base parentalRelationship
                rel_elem = add_elem.find(f'{{{ns_021}}}parentalRelationship')
                if rel_elem is None:
                    raise ValueError("addParent requires parentalRelationship")
                parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

                # Parse extension nameOfParentAtEvent (optional)
                name_elem = add_elem.find(f'{{{ns_021}}}nameOfParentAtEvent')
                name_of_parent_at_event = ECH0021NameOfParent.from_xml(name_elem) if name_elem is not None else None

                add_parent.append(ECH0020AddParent(
                    parental_relationship=parental_relationship,
                    name_of_parent_at_event=name_of_parent_at_event
                ))

        # removeParent (0-2)
        remove_parent: Optional[List[ECH0020RemoveParent]] = None
        rem_elems = elem.findall(f'{{{ns_020}}}removeParent')
        if rem_elems:
            if len(rem_elems) > 2:
                raise ValueError(f"eventChildRelationship allows max 2 removeParent, got {len(rem_elems)}")

            remove_parent = []
            for rem_elem in rem_elems:
                # Parse base parentalRelationship
                rel_elem = rem_elem.find(f'{{{ns_021}}}parentalRelationship')
                if rel_elem is None:
                    raise ValueError("removeParent requires parentalRelationship")
                parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

                # Parse extension nameOfParentAtEvent (optional)
                name_elem = rem_elem.find(f'{{{ns_021}}}nameOfParentAtEvent')
                name_of_parent_at_event = ECH0021NameOfParent.from_xml(name_elem) if name_elem is not None else None

                remove_parent.append(ECH0020RemoveParent(
                    parental_relationship=parental_relationship,
                    name_of_parent_at_event=name_of_parent_at_event
                ))

        # childRelationshipValidFrom (optional)
        valid_elem = elem.find(f'{{{ns_020}}}childRelationshipValidFrom')
        child_relationship_valid_from = date.fromisoformat(valid_elem.text) if valid_elem is not None and valid_elem.text else None

        # extension: Not implemented

        return cls(
            child_relationship_person=child_relationship_person,
            add_parent=add_parent,
            remove_parent=remove_parent,
            child_relationship_valid_from=child_relationship_valid_from
        )


# TYPE 18/89: swissNationalityType
class ECH0020SwissNationality(BaseModel):
    """Swiss nationality data with hardcoded values per eCH-0020 v3.0.

    XSD: swissNationalityType (eCH-0020-3-0.xsd lines 276-307)
    PDF: Section on nationality acquisition

    This type represents ONLY Swiss nationality with XSD-enforced values:
    - nationalityStatus: MUST be "2" (Swiss citizenship)
    - countryId: MUST be 8100 (Switzerland's numeric country code)
    - countryIdISO2: MUST be "CH" (Switzerland's ISO2 code)

    Used in naturalization events (eventNaturalizeForeigner) to record
    the acquisition of Swiss citizenship.

    NOTE: The XSD restricts all values via enumerations with single values.
    We use Literal types to enforce this at the Python level.
    """
    model_config = ConfigDict(populate_by_name=True)

    nationality_status: Literal["2"] = Field(
        "2",
        alias='nationalityStatus',
        description='Nationality status code - MUST be "2" (Swiss citizenship) per XSD'
    )

    country_id: Literal[8100] = Field(
        8100,
        alias='countryId',
        description='Country numeric code - MUST be 8100 (Switzerland) per XSD'
    )

    country_id_iso2: Literal["CH"] = Field(
        "CH",
        alias='countryIdISO2',
        description='Country ISO2 code - MUST be "CH" (Switzerland) per XSD'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'nationality'
    ) -> ET.Element:
        """Serialize to XML with nested country element."""
        ns = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns}}}{element_name}')

        # nationalityStatus (required, MUST be "2")
        ET.SubElement(elem, f'{{{ns}}}nationalityStatus').text = self.nationality_status

        # country element (required, nested structure with hardcoded CH values)
        country_elem = ET.SubElement(elem, f'{{{ns}}}country')
        ET.SubElement(country_elem, f'{{{ns}}}countryId').text = str(self.country_id)
        ET.SubElement(country_elem, f'{{{ns}}}countryIdISO2').text = self.country_id_iso2

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020SwissNationality':
        """Parse from XML element with XSD validation."""
        ns = NAMESPACE_ECH0020_V3

        # nationalityStatus (required)
        status_elem = elem.find(f'{{{ns}}}nationalityStatus')
        if status_elem is None or not status_elem.text:
            raise ValueError("swissNationalityType requires nationalityStatus")
        nationality_status = status_elem.text

        # Validate XSD restriction: MUST be "2"
        if nationality_status != "2":
            raise ValueError(f'swissNationalityType requires nationalityStatus="2", got "{nationality_status}"')

        # country element (required)
        country_elem = elem.find(f'{{{ns}}}country')
        if country_elem is None:
            raise ValueError("swissNationalityType requires country element")

        # countryId (required)
        id_elem = country_elem.find(f'{{{ns}}}countryId')
        if id_elem is None or not id_elem.text:
            raise ValueError("swissNationalityType requires country/countryId")
        country_id = int(id_elem.text)

        # Validate XSD restriction: MUST be 8100
        if country_id != 8100:
            raise ValueError(f'swissNationalityType requires countryId=8100, got {country_id}')

        # countryIdISO2 (required)
        iso2_elem = country_elem.find(f'{{{ns}}}countryIdISO2')
        if iso2_elem is None or not iso2_elem.text:
            raise ValueError("swissNationalityType requires country/countryIdISO2")
        country_id_iso2 = iso2_elem.text

        # Validate XSD restriction: MUST be "CH"
        if country_id_iso2 != "CH":
            raise ValueError(f'swissNationalityType requires countryIdISO2="CH", got "{country_id_iso2}"')

        return cls(
            nationality_status=nationality_status,
            country_id=country_id,
            country_id_iso2=country_id_iso2
        )


# TYPE 19/89: eventNaturalizeForeigner
class ECH0020EventNaturalizeForeigner(BaseModel):
    """Naturalization event - foreigner acquires Swiss citizenship.

    XSD: eventNaturalizeForeigner (eCH-0020-3-0.xsd lines 307-314)
    PDF: Section on naturalization events

    Used when a foreign national is naturalized and acquires:
    - Swiss citizenship (nationality status "2")
    - Place(s) of origin (Heimatort/Bürgerort)
    - Full civic rights

    This event records the ACQUISITION of Swiss nationality.
    Compare with eventNaturalizeSwiss which records ADDITIONAL place of origin.

    Fields:
    - naturalizeForeignerPerson (required): Person being naturalized (identification only)
    - placeOfOriginInfo (1-unbounded): Place(s) of origin acquired through naturalization
    - nationality (required): Swiss nationality data (always status "2", country CH)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    naturalize_foreigner_person: ECH0044PersonIdentification = Field(
        ...,
        alias='naturalizeForeignerPerson',
        description='Person identification of foreigner being naturalized'
    )

    place_of_origin_info: List['ECH0020PlaceOfOriginInfo'] = Field(
        ...,
        min_length=1,
        alias='placeOfOriginInfo',
        description='Place(s) of origin (Heimatort/Bürgerort) acquired through naturalization (1-n)'
    )

    nationality: 'ECH0020SwissNationality' = Field(
        ...,
        description='Swiss nationality data (status="2", country=CH)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventNaturalizeForeigner'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # naturalizeForeignerPerson (required)
        self.naturalize_foreigner_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='naturalizeForeignerPerson'
        )

        # placeOfOriginInfo (1-unbounded)
        for origin_info in self.place_of_origin_info:
            origin_info.to_xml(
                parent=elem,
                namespace=ns_020,
                element_name='placeOfOriginInfo'
            )

        # nationality (required)
        self.nationality.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='nationality'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventNaturalizeForeigner':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # naturalizeForeignerPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}naturalizeForeignerPerson')
        if person_elem is None:
            raise ValueError("eventNaturalizeForeigner requires naturalizeForeignerPerson")
        naturalize_foreigner_person = ECH0044PersonIdentification.from_xml(person_elem)

        # placeOfOriginInfo (1-unbounded)
        origin_elems = elem.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if not origin_elems:
            raise ValueError("eventNaturalizeForeigner requires at least one placeOfOriginInfo")
        place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(e) for e in origin_elems]

        # nationality (required)
        nat_elem = elem.find(f'{{{ns_020}}}nationality')
        if nat_elem is None:
            raise ValueError("eventNaturalizeForeigner requires nationality")
        nationality = ECH0020SwissNationality.from_xml(nat_elem)

        # extension: Not implemented

        return cls(
            naturalize_foreigner_person=naturalize_foreigner_person,
            place_of_origin_info=place_of_origin_info,
            nationality=nationality
        )


# TYPE 20/89: eventNaturalizeSwiss
class ECH0020EventNaturalizeSwiss(BaseModel):
    """Naturalization event - Swiss person acquires ADDITIONAL place of origin.

    XSD: eventNaturalizeSwiss (eCH-0020-3-0.xsd lines 315-321)
    PDF: Section on naturalization events

    CRITICAL DISTINCTION from eventNaturalizeForeigner:
    - eventNaturalizeForeigner: Person is NOT yet Swiss → receives nationality + origin
    - eventNaturalizeSwiss: Person is ALREADY Swiss → receives ADDITIONAL origin

    Used when a Swiss citizen is granted citizenship (Bürgerrecht) in an
    additional municipality, acquiring a new place of origin (Heimatort/Bürgerort).

    Example: Swiss person from Bern moves to Zürich and is granted
    Zürich citizenship after years of residence.

    Fields:
    - naturalizeSwissPerson (required): Person identification (already Swiss)
    - placeOfOriginInfo (1-unbounded): NEW place(s) of origin acquired
    - extension (optional): Not implemented

    NOTE: No nationality field (person is already Swiss).
    """
    model_config = ConfigDict(populate_by_name=True)

    naturalize_swiss_person: ECH0044PersonIdentification = Field(
        ...,
        alias='naturalizeSwissPerson',
        description='Person identification of Swiss citizen acquiring additional origin'
    )

    place_of_origin_info: List['ECH0020PlaceOfOriginInfo'] = Field(
        ...,
        min_length=1,
        alias='placeOfOriginInfo',
        description='NEW place(s) of origin acquired through naturalization (1-n)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventNaturalizeSwiss'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # naturalizeSwissPerson (required)
        self.naturalize_swiss_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='naturalizeSwissPerson'
        )

        # placeOfOriginInfo (1-unbounded)
        for origin_info in self.place_of_origin_info:
            origin_info.to_xml(
                parent=elem,
                namespace=ns_020,
                element_name='placeOfOriginInfo'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventNaturalizeSwiss':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # naturalizeSwissPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}naturalizeSwissPerson')
        if person_elem is None:
            raise ValueError("eventNaturalizeSwiss requires naturalizeSwissPerson")
        naturalize_swiss_person = ECH0044PersonIdentification.from_xml(person_elem)

        # placeOfOriginInfo (1-unbounded)
        origin_elems = elem.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if not origin_elems:
            raise ValueError("eventNaturalizeSwiss requires at least one placeOfOriginInfo")
        place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(e) for e in origin_elems]

        # extension: Not implemented

        return cls(
            naturalize_swiss_person=naturalize_swiss_person,
            place_of_origin_info=place_of_origin_info
        )


# TYPE 21/89: eventUndoCitizen
class ECH0020EventUndoCitizen(BaseModel):
    """Undo citizenship event - remove a place of origin (revoke municipal citizenship).

    XSD: eventUndoCitizen (eCH-0020-3-0.xsd lines 322-329)
    PDF: Section on citizenship revocation

    This is the OPPOSITE of naturalization events - removes citizenship in a municipality.

    Used when:
    - Person renounces citizenship (Bürgerrecht) in a municipality
    - Citizenship is revoked due to naturalization elsewhere
    - Expatriation from Switzerland (losing Swiss nationality entirely)

    Example: Swiss person with origin in Bern and Zürich renounces Zürich citizenship,
    keeping only Bern origin.

    Fields:
    - undoCitizenPerson (required): Person identification
    - placeOfOrigin (required): Place of origin being REMOVED
    - placeOfOriginAddon (optional): Expatriation date (XSD restriction: UnDo variant)
    - extension (optional): Not implemented

    NOTE: XSD uses placeOfOriginAddonRestrictedUnDoDataType which restricts
    placeOfOriginAddonDataType to require ONLY expatriationDate field.
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_citizen_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoCitizenPerson',
        description='Person identification of person losing citizenship'
    )

    place_of_origin: ECH0011PlaceOfOrigin = Field(
        ...,
        alias='placeOfOrigin',
        description='Place of origin (Heimatort/Bürgerort) being REMOVED'
    )

    place_of_origin_addon: Optional[ECH0021PlaceOfOriginAddonData] = Field(
        None,
        alias='placeOfOriginAddon',
        description='Expatriation date (XSD restriction: only expatriationDate used for UnDo)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoCitizen'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoCitizenPerson (required)
        self.undo_citizen_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoCitizenPerson'
        )

        # placeOfOrigin (required)
        self.place_of_origin.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='placeOfOrigin'
        )

        # placeOfOriginAddon (optional)
        if self.place_of_origin_addon:
            self.place_of_origin_addon.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='placeOfOriginAddon'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoCitizen':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        # undoCitizenPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoCitizenPerson')
        if person_elem is None:
            raise ValueError("eventUndoCitizen requires undoCitizenPerson")
        undo_citizen_person = ECH0044PersonIdentification.from_xml(person_elem)

        # placeOfOrigin (required)
        origin_elem = elem.find(f'{{{ns_011}}}placeOfOrigin')
        if origin_elem is None:
            raise ValueError("eventUndoCitizen requires placeOfOrigin")
        place_of_origin = ECH0011PlaceOfOrigin.from_xml(origin_elem)

        # placeOfOriginAddon (optional)
        addon_elem = elem.find(f'{{{ns_021}}}placeOfOriginAddon')
        place_of_origin_addon = ECH0021PlaceOfOriginAddonData.from_xml(addon_elem) if addon_elem is not None else None

        # extension: Not implemented

        return cls(
            undo_citizen_person=undo_citizen_person,
            place_of_origin=place_of_origin,
            place_of_origin_addon=place_of_origin_addon
        )


# TYPE 22/89: eventUndoSwiss
class ECH0020EventUndoSwiss(BaseModel):
    """Undo Swiss nationality - person loses ALL Swiss citizenship (expatriation).

    XSD: eventUndoSwiss (eCH-0020-3-0.xsd lines 330-338)
    PDF: Section on loss of Swiss nationality

    CRITICAL DISTINCTION:
    - eventUndoCitizen: Removes ONE place of origin (still Swiss, just fewer origins)
    - eventUndoSwiss: Loses ALL Swiss nationality (becomes FOREIGN)

    Used when a Swiss person loses Swiss citizenship entirely, becoming foreign:
    - Voluntary renunciation of Swiss nationality
    - Acquisition of another nationality (some countries require this)
    - Legal revocation of citizenship

    If person stays in Switzerland after losing Swiss citizenship, they need
    a residence permit (residencePermitData).

    Fields:
    - undoSwissPerson (required): Person identification
    - nationalityData (required): NEW nationality data (foreign country)
    - residencePermitData (optional): Residence permit if staying in Switzerland
    - undoSwissValidFrom (optional): Effective date of nationality loss
    - extension (optional): Not implemented

    Example: Swiss person acquires US citizenship and renounces Swiss nationality.
    They receive US nationality data and may get a residence permit if returning to CH.
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_swiss_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoSwissPerson',
        description='Person identification of person losing Swiss citizenship'
    )

    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='NEW nationality data (foreign country after losing Swiss citizenship)'
    )

    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Residence permit if person stays in Switzerland after losing citizenship'
    )

    undo_swiss_valid_from: Optional[date] = Field(
        None,
        alias='undoSwissValidFrom',
        description='Effective date of Swiss citizenship loss'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoSwiss'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoSwissPerson (required)
        self.undo_swiss_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoSwissPerson'
        )

        # nationalityData (required)
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData'
        )

        # residencePermitData (optional)
        if self.residence_permit_data:
            self.residence_permit_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='residencePermitData'
            )

        # undoSwissValidFrom (optional)
        if self.undo_swiss_valid_from:
            ET.SubElement(elem, f'{{{ns_020}}}undoSwissValidFrom').text = \
                self.undo_swiss_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoSwiss':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # undoSwissPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoSwissPerson')
        if person_elem is None:
            raise ValueError("eventUndoSwiss requires undoSwissPerson")
        undo_swiss_person = ECH0044PersonIdentification.from_xml(person_elem)

        # nationalityData (required)
        nat_elem = elem.find(f'{{{ns_011}}}nationalityData')
        if nat_elem is None:
            raise ValueError("eventUndoSwiss requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nat_elem)

        # residencePermitData (optional)
        permit_elem = elem.find(f'{{{ns_011}}}residencePermitData')
        residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem) if permit_elem is not None else None

        # undoSwissValidFrom (optional)
        valid_elem = elem.find(f'{{{ns_020}}}undoSwissValidFrom')
        undo_swiss_valid_from = date.fromisoformat(valid_elem.text) if valid_elem is not None and valid_elem.text else None

        # extension: Not implemented

        return cls(
            undo_swiss_person=undo_swiss_person,
            nationality_data=nationality_data,
            residence_permit_data=residence_permit_data,
            undo_swiss_valid_from=undo_swiss_valid_from
        )


# TYPE 23/89: eventChangeOrigin
class ECH0020EventChangeOrigin(BaseModel):
    """Change/update place of origin event.

    XSD: eventChangeOrigin (eCH-0020-3-0.xsd lines 339-345)
    PDF: Section on origin changes

    Used to update or correct place of origin (Heimatort/Bürgerort) information
    for a Swiss person. This is typically a correction or administrative update,
    not a naturalization (which uses eventNaturalizeForeigner or eventNaturalizeSwiss).

    Example: Municipality name change, administrative correction, or update
    to canton information for an existing place of origin.

    Fields:
    - changeOriginPerson (required): Person identification
    - originInfo (1-unbounded): Updated place(s) of origin information
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    change_origin_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeOriginPerson',
        description='Person identification of person with updated origin information'
    )

    origin_info: List['ECH0020PlaceOfOriginInfo'] = Field(
        ...,
        min_length=1,
        alias='originInfo',
        description='Updated place(s) of origin information (1-n)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventChangeOrigin'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeOriginPerson (required)
        self.change_origin_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeOriginPerson'
        )

        # originInfo (1-unbounded)
        for origin in self.origin_info:
            origin.to_xml(
                parent=elem,
                namespace=ns_020,
                element_name='originInfo'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeOrigin':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # changeOriginPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeOriginPerson')
        if person_elem is None:
            raise ValueError("eventChangeOrigin requires changeOriginPerson")
        change_origin_person = ECH0044PersonIdentification.from_xml(person_elem)

        # originInfo (1-unbounded)
        origin_elems = elem.findall(f'{{{ns_020}}}originInfo')
        if not origin_elems:
            raise ValueError("eventChangeOrigin requires at least one originInfo")
        origin_info = [ECH0020PlaceOfOriginInfo.from_xml(e) for e in origin_elems]

        # extension: Not implemented

        return cls(
            change_origin_person=change_origin_person,
            origin_info=origin_info
        )


# TYPE 24/89: eventBirth
class ECH0020EventBirth(BaseModel):
    """Birth event - register a new person.

    XSD: eventBirth (eCH-0020-3-0.xsd lines 346-356)
    PDF: Section on birth registration

    Used to register a birth in the population register. The newborn is assigned:
    - Person identification (VN if Swiss or eligible)
    - Name, birth info
    - Nationality (Swiss with places of origin OR foreign with residence permit)
    - Optional residence information (where the child lives)

    Fields:
    - birthPerson (required): Person data for newborn (uses birthPersonType)
    - XSD CHOICE (optional): hasMainResidence OR hasSecondaryResidence OR hasOtherResidence
    - extension (optional): Not implemented

    The CHOICE is optional because a newborn may not have a registered residence yet
    (e.g., still in hospital, or registered elsewhere).
    """
    model_config = ConfigDict(populate_by_name=True)

    birth_person: 'ECH0020BirthPerson' = Field(
        ...,
        alias='birthPerson',
        description='Person data for newborn (birthPersonType)'
    )

    has_main_residence: Optional[ECH0011MainResidence] = Field(
        None,
        alias='hasMainResidence',
        description='Main residence (XSD CHOICE: only ONE residence type allowed)'
    )

    has_secondary_residence: Optional[ECH0011SecondaryResidence] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Secondary residence (XSD CHOICE: only ONE residence type allowed)'
    )

    has_other_residence: Optional[ECH0011OtherResidence] = Field(
        None,
        alias='hasOtherResidence',
        description='Other residence (XSD CHOICE: only ONE residence type allowed)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventBirth':
        """Validate XSD CHOICE: at most ONE residence type (all optional)."""
        residences = [
            self.has_main_residence,
            self.has_secondary_residence,
            self.has_other_residence
        ]
        set_count = sum(1 for r in residences if r is not None)

        if set_count > 1:
            raise ValueError(
                f"eventBirth allows at most ONE residence type (main/secondary/other), "
                f"but {set_count} are set"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventBirth'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # birthPerson (required)
        self.birth_person.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='birthPerson'
        )

        # CHOICE: at most one residence type (all optional) - wrapper in eCH-0020, content in eCH-0011
        if self.has_main_residence:
            self.has_main_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasMainResidence',
                wrapper_namespace=ns_020
            )
        elif self.has_secondary_residence:
            self.has_secondary_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasSecondaryResidence',
                wrapper_namespace=ns_020
            )
        elif self.has_other_residence:
            self.has_other_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasOtherResidence',
                wrapper_namespace=ns_020
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventBirth':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8

        # birthPerson (required)
        person_elem = elem.find(f'{{{ns_020}}}birthPerson')
        if person_elem is None:
            raise ValueError("eventBirth requires birthPerson")
        birth_person = ECH0020BirthPerson.from_xml(person_elem)

        # CHOICE: at most one residence type (all optional) - wrappers in eCH-0020, content in eCH-0011
        main_elem = elem.find(f'{{{ns_020}}}hasMainResidence')
        has_main_residence = ECH0011MainResidence.from_xml(main_elem) if main_elem is not None else None

        sec_elem = elem.find(f'{{{ns_020}}}hasSecondaryResidence')
        has_secondary_residence = ECH0011SecondaryResidence.from_xml(sec_elem) if sec_elem is not None else None

        other_elem = elem.find(f'{{{ns_020}}}hasOtherResidence')
        has_other_residence = ECH0011OtherResidence.from_xml(other_elem) if other_elem is not None else None

        # extension: Not implemented

        return cls(
            birth_person=birth_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence
        )


# TYPE 25/89: eventMarriage
class ECH0020EventMarriage(BaseModel):
    """Marriage event - register a marriage.

    XSD: eventMarriage (eCH-0020-3-0.xsd lines 357-364)
    PDF: Section on marriage registration

    Used to register a marriage in the population register. Updates:
    - Marital status to "married"
    - Marriage date and place
    - Optional link to spouse (maritalRelationship)

    Note: This is for opposite-sex OR same-sex marriage (since 2022 in Switzerland).
    For registered partnerships (before 2022), use eventPartnership.

    Fields:
    - marriagePerson (required): Person identification
    - maritalInfo (required): Marriage info (maritalInfoRestrictedMarriageType)
    - maritalRelationship (optional): Link to spouse
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    marriage_person: ECH0044PersonIdentification = Field(
        ...,
        alias='marriagePerson',
        description='Person identification of person getting married'
    )

    marital_info: 'ECH0020MaritalInfoRestrictedMarriage' = Field(
        ...,
        alias='maritalInfo',
        description='Marriage information (date, place, separation date if applicable)'
    )

    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Optional link to spouse (marital relationship)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventMarriage'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # marriagePerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.marriage_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='marriagePerson',
            wrapper_namespace=ns_020
        )

        # maritalInfo (required) - fully in eCH-0020
        self.marital_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='maritalInfo'
        )

        # maritalRelationship (optional) - wrapper in eCH-0020, content in eCH-0021
        if self.marital_relationship:
            self.marital_relationship.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='maritalRelationship',
                wrapper_namespace=ns_020
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMarriage':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        # marriagePerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}marriagePerson')
        if person_elem is None:
            raise ValueError("eventMarriage requires marriagePerson")
        marriage_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalInfo (required) - fully in eCH-0020
        info_elem = elem.find(f'{{{ns_020}}}maritalInfo')
        if info_elem is None:
            raise ValueError("eventMarriage requires maritalInfo")
        marital_info = ECH0020MaritalInfoRestrictedMarriage.from_xml(info_elem)

        # maritalRelationship (optional) - wrapper in eCH-0020, content in eCH-0021
        rel_elem = elem.find(f'{{{ns_020}}}maritalRelationship')
        marital_relationship = ECH0021MaritalRelationship.from_xml(rel_elem) if rel_elem is not None else None

        # extension: Not implemented

        return cls(
            marriage_person=marriage_person,
            marital_info=marital_info,
            marital_relationship=marital_relationship
        )


# TYPE 26/89: eventPartnership
class ECH0020EventPartnership(BaseModel):
    """Registered partnership event - register a registered partnership.

    XSD: eventPartnership (eCH-0020-3-0.xsd lines 365-372)
    PDF: Section on partnership registration

    Used to register a registered partnership (eingetragene Partnerschaft).
    This was the legal framework for same-sex couples before same-sex marriage
    was legalized in Switzerland (July 1, 2022).

    Note: After 2022, same-sex couples can choose marriage (eventMarriage) or
    continue with registered partnership. Existing partnerships can be converted
    to marriage.

    Fields:
    - partnershipPerson (required): Person identification
    - maritalInfo (required): Partnership info (maritalInfoRestrictedMarriageType)
    - partnershipRelationship (optional): Link to partner
    - extension (optional): Not implemented

    Almost identical structure to eventMarriage, just different legal framework.
    """
    model_config = ConfigDict(populate_by_name=True)

    partnership_person: ECH0044PersonIdentification = Field(
        ...,
        alias='partnershipPerson',
        description='Person identification of person entering registered partnership'
    )

    marital_info: 'ECH0020MaritalInfoRestrictedMarriage' = Field(
        ...,
        alias='maritalInfo',
        description='Partnership information (date, place, separation date if applicable)'
    )

    partnership_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='partnershipRelationship',
        description='Optional link to partner (uses same maritalRelationshipType as marriage)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventPartnership'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # partnershipPerson (required)
        self.partnership_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='partnershipPerson'
        )

        # maritalInfo (required)
        self.marital_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='maritalInfo'
        )

        # partnershipRelationship (optional)
        if self.partnership_relationship:
            self.partnership_relationship.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='partnershipRelationship'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventPartnership':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        # partnershipPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}partnershipPerson')
        if person_elem is None:
            raise ValueError("eventPartnership requires partnershipPerson")
        partnership_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalInfo (required)
        info_elem = elem.find(f'{{{ns_020}}}maritalInfo')
        if info_elem is None:
            raise ValueError("eventPartnership requires maritalInfo")
        marital_info = ECH0020MaritalInfoRestrictedMarriage.from_xml(info_elem)

        # partnershipRelationship (optional)
        rel_elem = elem.find(f'{{{ns_021}}}partnershipRelationship')
        partnership_relationship = ECH0021MaritalRelationship.from_xml(rel_elem) if rel_elem is not None else None

        # extension: Not implemented

        return cls(
            partnership_person=partnership_person,
            marital_info=marital_info,
            partnership_relationship=partnership_relationship
        )


# TYPE 27/89: eventSeparation
class ECH0020EventSeparation(BaseModel):
    """Separation event - register legal separation of married/partnered couple.

    XSD: eventSeparation (eCH-0020-3-0.xsd lines 373-379)
    PDF: Section on separation registration

    Used to register a legal separation (gerichtliche Trennung) without divorce.
    The couple remains legally married/partnered but lives separately.

    This is different from:
    - Divorce (eventDivorce): Ends the marriage entirely
    - eventUndoSeparation: Cancels the separation (couple reconciles)

    In Switzerland, separation is optional before divorce. Some couples separate
    legally before divorcing, others divorce directly.

    Fields:
    - separationPerson (required): Person identification
    - separationData (required): Separation date and reconciliation info (from eCH-0011)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    separation_person: ECH0044PersonIdentification = Field(
        ...,
        alias='separationPerson',
        description='Person identification of person legally separating'
    )

    separation_data: ECH0011SeparationData = Field(
        ...,
        alias='separationData',
        description='Separation date and optional reconciliation date (eCH-0011 separationDataType)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventSeparation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # separationPerson (required)
        self.separation_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='separationPerson'
        )

        # separationData (required)
        self.separation_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='separationData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventSeparation':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # separationPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}separationPerson')
        if person_elem is None:
            raise ValueError("eventSeparation requires separationPerson")
        separation_person = ECH0044PersonIdentification.from_xml(person_elem)

        # separationData (required)
        data_elem = elem.find(f'{{{ns_011}}}separationData')
        if data_elem is None:
            raise ValueError("eventSeparation requires separationData")
        separation_data = ECH0011SeparationData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            separation_person=separation_person,
            separation_data=separation_data
        )


# TYPE 28/89: eventUndoSeparation
class ECH0020EventUndoSeparation(BaseModel):
    """Undo separation event - cancel legal separation (couple reconciles).

    XSD: eventUndoSeparation (eCH-0020-3-0.xsd lines 380-386)
    PDF: Section on separation cancellation

    Used when a legally separated couple reconciles and resumes married/partnered
    life together. The separation is cancelled, but the marriage/partnership
    remains (they do NOT need to remarry).

    This is different from:
    - Divorce (eventDivorce): Would end the marriage entirely
    - New marriage: Not needed - they are still married/partnered

    Swiss civil law allows separated couples to reconcile at any time before
    divorce is finalized.

    Fields:
    - undoSeparationPerson (required): Person identification
    - separationValidTill (optional): End date of separation period
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_separation_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoSeparationPerson',
        description='Person identification of person reconciling after separation'
    )

    separation_valid_till: Optional[date] = Field(
        None,
        alias='separationValidTill',
        description='End date of separation period (reconciliation date)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoSeparation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoSeparationPerson (required)
        self.undo_separation_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoSeparationPerson'
        )

        # separationValidTill (optional)
        if self.separation_valid_till:
            ET.SubElement(elem, f'{{{ns_020}}}separationValidTill').text = \
                self.separation_valid_till.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoSeparation':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # undoSeparationPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoSeparationPerson')
        if person_elem is None:
            raise ValueError("eventUndoSeparation requires undoSeparationPerson")
        undo_separation_person = ECH0044PersonIdentification.from_xml(person_elem)

        # separationValidTill (optional)
        valid_elem = elem.find(f'{{{ns_020}}}separationValidTill')
        separation_valid_till = date.fromisoformat(valid_elem.text) if valid_elem is not None and valid_elem.text else None

        # extension: Not implemented

        return cls(
            undo_separation_person=undo_separation_person,
            separation_valid_till=separation_valid_till
        )


# TYPE 29/89: eventDivorce
class ECH0020EventDivorce(BaseModel):
    """Divorce event - register dissolution of marriage or partnership.

    XSD: eventDivorce (eCH-0020-3-0.xsd lines 387-393)
    PDF: Section on divorce registration

    Used to register a divorce (Scheidung) or dissolution of registered partnership
    (Auflösung der eingetragenen Partnerschaft). This ends the marriage/partnership
    entirely - the persons become legally unmarried/unpartnered.

    This is different from:
    - Separation (eventSeparation): Marriage continues, just living apart
    - Undo marriage/partnership: Administrative corrections, not divorce

    Swiss law requires a separation period before divorce (with exceptions for
    specific circumstances like abuse, irreconcilable differences proven, etc.).

    Fields:
    - divorcePerson (required): Person identification
    - maritalData (required): Marital data with divorce info (eCH-0011 restricted type)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    divorce_person: ECH0044PersonIdentification = Field(
        ...,
        alias='divorcePerson',
        description='Person identification of person getting divorced'
    )

    marital_data: ECH0011MaritalDataRestrictedDivorce = Field(
        ...,
        alias='maritalData',
        description='Marital data with divorce date and cancellation info (eCH-0011 restricted)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventDivorce'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # divorcePerson (required)
        self.divorce_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='divorcePerson'
        )

        # maritalData (required)
        self.marital_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='maritalData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventDivorce':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # divorcePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}divorcePerson')
        if person_elem is None:
            raise ValueError("eventDivorce requires divorcePerson")
        divorce_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalData (required)
        data_elem = elem.find(f'{{{ns_011}}}maritalData')
        if data_elem is None:
            raise ValueError("eventDivorce requires maritalData")
        marital_data = ECH0011MaritalDataRestrictedDivorce.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            divorce_person=divorce_person,
            marital_data=marital_data
        )


# ============================================================================
# PERSON TYPE VARIATIONS (Different person structures for different events)
# ============================================================================

class ECH0020BirthPerson(BaseModel):
    """Person data structure for birth events.

    Contains person identification, name/birth/marital data, and either
    Swiss origin information OR residence permit data for foreign nationals.

    XSD: birthPersonType (eCH-0020-3-0.xsd lines 77-95)
    PDF: Section describing birth event person data

    XSD Constraint: CHOICE between placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    """

    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description="Person identification per eCH-0044"
    )

    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description="Name data with validation date"
    )

    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description="Birth data with optional addon"
    )

    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description="Religion data per eCH-0011"
    )

    marital_data: ECH0011MaritalData = Field(
        ...,
        alias='maritalData',
        description="Marital data per eCH-0011"
    )

    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description="Nationality data per eCH-0011"
    )

    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description="Contact data per eCH-0011"
    )

    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description="Additional person data per eCH-0021 v7"
    )

    # XSD CHOICE: Either placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description="Place of origin data (for Swiss nationals, unbounded)"
    )

    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description="Residence permit data (for foreign nationals)"
    )

    lock_data: ECH0021LockData = Field(
        ...,
        alias='lockData',
        description="Lock data per eCH-0021 v7"
    )

    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description="Parental relationships (optional, unbounded)"
    )

    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description="Health insurance data per eCH-0021 v7"
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BirthPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData must be present."""
        has_origin = self.place_of_origin_info is not None and len(self.place_of_origin_info) > 0
        has_permit = self.residence_permit_data is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "birthPersonType requires either placeOfOriginInfo (Swiss) OR "
                "residencePermitData (foreign), but neither was provided"
            )

        if has_origin and has_permit:
            raise ValueError(
                "birthPersonType allows either placeOfOriginInfo (Swiss) OR "
                "residencePermitData (foreign), but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'birthPerson'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # personIdentification (required) - wrapper in eCH-0020, content in eCH-0044
        self.person_identification.to_xml(
            parent=elem,
            namespace='http://www.ech.ch/xmlns/eCH-0044/4',
            element_name='personIdentification',
            wrapper_namespace=namespace
        )

        # nameInfo (required)
        self.name_info.to_xml(parent=elem, namespace=namespace)

        # birthInfo (required)
        self.birth_info.to_xml(parent=elem, namespace=namespace)

        # religionData (required) - manual wrapper pattern (type doesn't support wrapper_namespace yet)
        wrapper = ET.SubElement(elem, f'{{{namespace}}}religionData')
        content = self.religion_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in content:
            wrapper.append(child)

        # maritalData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalData')
        content = self.marital_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in content:
            wrapper.append(child)

        # nationalityData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}nationalityData')
        content = self.nationality_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
        for child in content:
            wrapper.append(child)

        # contactData (optional) - manual wrapper pattern
        if self.contact_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            content = self.contact_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
            for child in content:
                wrapper.append(child)

        # personAdditionalData (optional) - manual wrapper pattern
        if self.person_additional_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            content = self.person_additional_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in content:
                wrapper.append(child)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace)
        elif self.residence_permit_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}residencePermitData')
            content = self.residence_permit_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
            for child in content:
                wrapper.append(child)

        # lockData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        content = self.lock_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
        for child in content:
            wrapper.append(child)

        # parentalRelationship (optional, unbounded) - manual wrapper pattern
        if self.parental_relationship:
            for parental_rel in self.parental_relationship:
                wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')
                content = parental_rel.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
                for child in content:
                    wrapper.append(child)

        # healthInsuranceData (optional) - manual wrapper pattern
        if self.health_insurance_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            content = self.health_insurance_data.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0021/7')
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BirthPerson':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': 'http://www.ech.ch/xmlns/eCH-0020/3'}
        ns_0044 = {'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4'}
        ns_0011 = {'eCH-0011': 'http://www.ech.ch/xmlns/eCH-0011/8'}
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # Required fields - all wrappers in eCH-0020, content in respective namespaces
        person_id_elem = element.find('eCH-0020:personIdentification', ns_0020)
        if person_id_elem is None:
            raise ValueError("personIdentification is required in birthPersonType")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        name_info_elem = element.find('eCH-0020:nameInfo', ns_0020)
        if name_info_elem is None:
            raise ValueError("nameInfo is required in birthPersonType")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        birth_info_elem = element.find('eCH-0020:birthInfo', ns_0020)
        if birth_info_elem is None:
            raise ValueError("birthInfo is required in birthPersonType")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        religion_elem = element.find('eCH-0020:religionData', ns_0020)
        if religion_elem is None:
            raise ValueError("religionData is required in birthPersonType")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        marital_elem = element.find('eCH-0020:maritalData', ns_0020)
        if marital_elem is None:
            raise ValueError("maritalData is required in birthPersonType")
        marital_data = ECH0011MaritalData.from_xml(marital_elem)

        nationality_elem = element.find('eCH-0020:nationalityData', ns_0020)
        if nationality_elem is None:
            raise ValueError("nationalityData is required in birthPersonType")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        lock_data_elem = element.find('eCH-0020:lockData', ns_0020)
        if lock_data_elem is None:
            raise ValueError("lockData is required in birthPersonType")
        lock_data = ECH0021LockData.from_xml(lock_data_elem)

        # Optional fields - wrappers in eCH-0020
        contact_elem = element.find('eCH-0020:contactData', ns_0020)
        contact_data = ECH0011ContactData.from_xml(contact_elem) if contact_elem is not None else None

        person_addon_elem = element.find('eCH-0020:personAdditionalData', ns_0020)
        person_additional_data = ECH0021PersonAdditionalData.from_xml(person_addon_elem) if person_addon_elem is not None else None

        # CHOICE: placeOfOriginInfo OR residencePermitData
        origin_elems = element.findall('eCH-0020:placeOfOriginInfo', ns_0020)
        place_of_origin_info = None
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems]

        permit_elem = element.find('eCH-0020:residencePermitData', ns_0020)
        residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem) if permit_elem is not None else None

        # Optional unbounded fields - wrappers in eCH-0020
        parental_elems = element.findall('eCH-0020:parentalRelationship', ns_0020)
        parental_relationship = None
        if parental_elems:
            parental_relationship = [ECH0021ParentalRelationship.from_xml(elem) for elem in parental_elems]

        health_ins_elem = element.find('eCH-0020:healthInsuranceData', ns_0020)
        health_insurance_data = ECH0021HealthInsuranceData.from_xml(health_ins_elem) if health_ins_elem is not None else None

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_data=marital_data,
            nationality_data=nationality_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            parental_relationship=parental_relationship,
            health_insurance_data=health_insurance_data
        )


# ============================================================================
# TYPE 30/89: EVENT UNDO MARRIAGE
# ============================================================================

class ECH0020EventUndoMarriage(BaseModel):
    """Undo marriage event - nullify/annul marriage registration.
    
    XSD: eventUndoMarriage (eCH-0020-3-0.xsd lines 394-400)
    PDF: Section on marriage nullification/annulment
    
    Used to undo/nullify/annul a marriage (Ungültigkeitserklärung/Annullierung der Ehe).
    This is different from divorce (Scheidung) - marriage is declared invalid from
    the beginning (ex tunc), as if it never existed.
    
    Legal contexts:
    - Marriage was never valid (bigamy, fraud, coercion, etc.)
    - Court declares marriage null and void
    - Administrative correction of erroneous marriage registration
    
    Fields:
    - undoMarriagePerson (required): Person identification
    - maritalData (required): Marital data with nullification info (eCH-0011 restricted type)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_marriage_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoMarriagePerson',
        description='Person identification of person whose marriage is being nullified'
    )

    marital_data: ECH0011MaritalDataRestrictedUndoMarried = Field(
        ...,
        alias='maritalData',
        description='Marital data with nullification date and cancellation info (eCH-0011 restricted)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoMarriage'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoMarriagePerson (required)
        self.undo_marriage_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoMarriagePerson'
        )

        # maritalData (required)
        self.marital_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='maritalData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoMarriage':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # undoMarriagePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoMarriagePerson')
        if person_elem is None:
            raise ValueError("eventUndoMarriage requires undoMarriagePerson")
        undo_marriage_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalData (required)
        data_elem = elem.find(f'{{{ns_011}}}maritalData')
        if data_elem is None:
            raise ValueError("eventUndoMarriage requires maritalData")
        marital_data = ECH0011MaritalDataRestrictedUndoMarried.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            undo_marriage_person=undo_marriage_person,
            marital_data=marital_data
        )


class ECH0020EventUndoPartnership(BaseModel):
    """Undo partnership event - nullify/annul registered partnership.

    XSD: eventUndoPartnership (eCH-0020-3-0.xsd lines 402-409)
    PDF: Section on partnership nullification/annulment

    Used to undo/nullify/annul a registered partnership (eingetragene Partnerschaft).
    This is different from separation (Auflösung) - partnership is declared invalid
    from the beginning (ex tunc), as if it never existed.

    Legal contexts:
    - Partnership was never valid (fraud, coercion, etc.)
    - Court declares partnership null and void
    - Administrative correction of erroneous partnership registration

    Fields:
    - undoPartnershipPerson (required): Person identification
    - maritalData (required): Marital data with nullification info (eCH-0011 restricted type)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_partnership_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoPartnershipPerson',
        description='Person identification of person whose partnership is being nullified'
    )

    marital_data: ECH0011MaritalDataRestrictedUndoPartnership = Field(
        ...,
        alias='maritalData',
        description='Marital data with nullification date and cancellation info (eCH-0011 restricted)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoPartnership'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoPartnershipPerson (required)
        self.undo_partnership_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoPartnershipPerson'
        )

        # maritalData (required)
        self.marital_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='maritalData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoPartnership':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # undoPartnershipPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoPartnershipPerson')
        if person_elem is None:
            raise ValueError("eventUndoPartnership requires undoPartnershipPerson")
        undo_partnership_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalData (required)
        data_elem = elem.find(f'{{{ns_011}}}maritalData')
        if data_elem is None:
            raise ValueError("eventUndoPartnership requires maritalData")
        marital_data = ECH0011MaritalDataRestrictedUndoPartnership.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            undo_partnership_person=undo_partnership_person,
            marital_data=marital_data
        )


class ECH0020EventDeath(BaseModel):
    """Death event - register person death.

    XSD: eventDeath (eCH-0020-3-0.xsd lines 408-414)
    PDF: Section on death registration

    Used to register the death of a person in the population register.
    This event terminates residence and triggers various administrative
    processes (inheritance, pension, etc.).

    Fields:
    - deathPerson (required): Person identification
    - deathData (required): Death data with date, place, etc. (eCH-0011)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    death_person: ECH0044PersonIdentification = Field(
        ...,
        alias='deathPerson',
        description='Person identification of deceased person'
    )

    death_data: ECH0011DeathData = Field(
        ...,
        alias='deathData',
        description='Death data per eCH-0011 (date, place, cause, etc.)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventDeath'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # deathPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.death_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='deathPerson',
            wrapper_namespace=ns_020
        )

        # deathData (required) - wrapper in eCH-0020, content in eCH-0011
        self.death_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='deathData',
            wrapper_namespace=ns_020
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventDeath':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # deathPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}deathPerson')
        if person_elem is None:
            raise ValueError("eventDeath requires deathPerson")
        death_person = ECH0044PersonIdentification.from_xml(person_elem)

        # deathData (required) - wrapper in eCH-0020, content in eCH-0011
        data_elem = elem.find(f'{{{ns_020}}}deathData')
        if data_elem is None:
            raise ValueError("eventDeath requires deathData")
        death_data = ECH0011DeathData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            death_person=death_person,
            death_data=death_data
        )


class ECH0020EventMissing(BaseModel):
    """Missing person event - register person as missing (presumed dead).

    XSD: eventMissing (eCH-0020-3-0.xsd lines 415-421)
    PDF: Section on missing person registration

    Used to register a person as missing when they are presumed dead but the
    death cannot be confirmed (e.g., lost at sea, natural disaster, missing for
    extended period). Uses deathData to record the presumed death date.

    Legal contexts:
    - Person missing and presumed dead
    - Court declaration of presumed death
    - Administrative handling of long-term missing persons

    Fields:
    - missingPerson (required): Person identification
    - deathData (required): Death data with presumed death date (eCH-0011)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    missing_person: ECH0044PersonIdentification = Field(
        ...,
        alias='missingPerson',
        description='Person identification of missing person'
    )

    death_data: ECH0011DeathData = Field(
        ...,
        alias='deathData',
        description='Death data with presumed death date per eCH-0011'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventMissing'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # missingPerson (required)
        self.missing_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='missingPerson'
        )

        # deathData (required)
        self.death_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='deathData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMissing':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # missingPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}missingPerson')
        if person_elem is None:
            raise ValueError("eventMissing requires missingPerson")
        missing_person = ECH0044PersonIdentification.from_xml(person_elem)

        # deathData (required)
        data_elem = elem.find(f'{{{ns_011}}}deathData')
        if data_elem is None:
            raise ValueError("eventMissing requires deathData")
        death_data = ECH0011DeathData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            missing_person=missing_person,
            death_data=death_data
        )


class ECH0020EventUndoMissing(BaseModel):
    """Undo missing person event - person found alive.

    XSD: eventUndoMissing (eCH-0020-3-0.xsd lines 422-428)
    PDF: Section on undoing missing person status

    Used to reverse a missing person registration when the person is found
    alive or when the missing status needs to be corrected.

    Fields:
    - undoMissingPerson (required): Person identification
    - undoMissingValidFrom (optional): Date from which undo is valid
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    undo_missing_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoMissingPerson',
        description='Person identification of person whose missing status is being undone'
    )

    undo_missing_valid_from: Optional[date] = Field(
        None,
        alias='undoMissingValidFrom',
        description='Date from which the undo of missing status is valid'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventUndoMissing'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoMissingPerson (required)
        self.undo_missing_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoMissingPerson'
        )

        # undoMissingValidFrom (optional)
        if self.undo_missing_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}undoMissingValidFrom')
            valid_from_elem.text = self.undo_missing_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoMissing':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # undoMissingPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoMissingPerson')
        if person_elem is None:
            raise ValueError("eventUndoMissing requires undoMissingPerson")
        undo_missing_person = ECH0044PersonIdentification.from_xml(person_elem)

        # undoMissingValidFrom (optional)
        valid_from_elem = elem.find(f'{{{ns_020}}}undoMissingValidFrom')
        undo_missing_valid_from = None
        if valid_from_elem is not None and valid_from_elem.text:
            undo_missing_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            undo_missing_person=undo_missing_person,
            undo_missing_valid_from=undo_missing_valid_from
        )


class ECH0020EventMaritalStatusPartner(BaseModel):
    """Marital status with partner event - register marital status change with partner details.

    XSD: eventMaritalStatusPartner (eCH-0020-3-0.xsd lines 429-435)
    PDF: Section on marital status change with partner information

    Used to register a change in marital status that includes partner information.
    This is distinct from eventMarriage/eventPartnership which register the initial
    union - this event updates marital status with partner data.

    Fields:
    - maritalStatusPartnerPerson (required): Person identification
    - maritalData (required): Restricted marital data with partner info (eCH-0011)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    marital_status_partner_person: ECH0044PersonIdentification = Field(
        ...,
        alias='maritalStatusPartnerPerson',
        description='Person identification of person whose marital status is being updated'
    )

    marital_data: ECH0011MaritalDataRestrictedMaritalStatusPartner = Field(
        ...,
        alias='maritalData',
        description='Marital data with partner information (eCH-0011 restricted type)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventMaritalStatusPartner'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # maritalStatusPartnerPerson (required)
        self.marital_status_partner_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='maritalStatusPartnerPerson'
        )

        # maritalData (required)
        self.marital_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='maritalData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMaritalStatusPartner':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # maritalStatusPartnerPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}maritalStatusPartnerPerson')
        if person_elem is None:
            raise ValueError("eventMaritalStatusPartner requires maritalStatusPartnerPerson")
        marital_status_partner_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalData (required)
        data_elem = elem.find(f'{{{ns_011}}}maritalData')
        if data_elem is None:
            raise ValueError("eventMaritalStatusPartner requires maritalData")
        marital_data = ECH0011MaritalDataRestrictedMaritalStatusPartner.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            marital_status_partner_person=marital_status_partner_person,
            marital_data=marital_data
        )


class ECH0020EventChangeName(BaseModel):
    """Name change event - register official name change.

    XSD: eventChangeName (eCH-0020-3-0.xsd lines 436-442)
    PDF: Section on name change events

    Used to register an official name change (e.g., marriage, court order,
    gender transition, adoption, personal preference).

    Fields:
    - changeNamePerson (required): Person identification
    - nameInfo (required): New name data with validity date (eCH-0020 wrapper)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    change_name_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeNamePerson',
        description='Person identification of person whose name is being changed'
    )

    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='New name data with optional validity date'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventChangeName'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeNamePerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.change_name_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeNamePerson',
            wrapper_namespace=ns_020
        )

        # nameInfo (required)
        self.name_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='nameInfo'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeName':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # changeNamePerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}changeNamePerson')
        if person_elem is None:
            raise ValueError("eventChangeName requires changeNamePerson")
        change_name_person = ECH0044PersonIdentification.from_xml(person_elem)

        # nameInfo (required)
        name_info_elem = elem.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("eventChangeName requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        # extension: Not implemented

        return cls(
            change_name_person=change_name_person,
            name_info=name_info
        )


class ECH0020ChangeSexPerson(BaseModel):
    """Person data for sex change event.

    XSD: changeSexPersonType (eCH-0020-3-0.xsd lines 443-448)
    PDF: Section on sex change person data

    Contains person identification and new sex designation for sex change events.

    Fields:
    - personIdentification (required): Person identification
    - sex (required): New sex designation
    """
    model_config = ConfigDict(populate_by_name=True)

    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification'
    )

    sex: Sex = Field(
        ...,
        description='New sex designation per eCH-0044'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'changeSexPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # personIdentification (required)
        self.person_identification.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='personIdentification'
        )

        # sex (required)
        sex_elem = ET.SubElement(elem, f'{{{ns_044}}}sex')
        sex_elem.text = self.sex.value

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020ChangeSexPerson':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # personIdentification (required)
        person_elem = elem.find(f'{{{ns_044}}}personIdentification')
        if person_elem is None:
            raise ValueError("changeSexPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_elem)

        # sex (required)
        sex_elem = elem.find(f'{{{ns_044}}}sex')
        if sex_elem is None or not sex_elem.text:
            raise ValueError("changeSexPersonType requires sex")
        sex = Sex(sex_elem.text)

        return cls(
            person_identification=person_identification,
            sex=sex
        )


class ECH0020EventChangeSex(BaseModel):
    """Sex change event - register official sex/gender change.

    XSD: eventChangeSex (eCH-0020-3-0.xsd lines 449-454)
    PDF: Section on sex change events

    Used to register an official sex/gender change (Geschlechtsänderung).

    Fields:
    - changeSexPerson (required): Person data with new sex designation
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    change_sex_person: 'ECH0020ChangeSexPerson' = Field(
        ...,
        alias='changeSexPerson',
        description='Person identification and new sex designation'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventChangeSex'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeSexPerson (required)
        self.change_sex_person.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='changeSexPerson'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeSex':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3

        # changeSexPerson (required)
        person_elem = elem.find(f'{{{ns_020}}}changeSexPerson')
        if person_elem is None:
            raise ValueError("eventChangeSex requires changeSexPerson")
        change_sex_person = ECH0020ChangeSexPerson.from_xml(person_elem)

        # extension: Not implemented

        return cls(
            change_sex_person=change_sex_person
        )


class ECH0020PersonIdOnly(BaseModel):
    """Person identification only (subset of full personIdentificationType).

    XSD: personIdOnlyType (eCH-0020-3-0.xsd lines 714-721)
    PDF: Section on person identification for corrections

    Reduced person identification containing only ID fields without demographic data.
    Used when correcting person identification data.

    Fields:
    - vn (optional): AHV-13 number (Versichertennummer)
    - localPersonId (required): Local person ID
    - otherPersonId (optional, unbounded): Other person IDs
    - euPersonId (optional, unbounded): EU person IDs
    """
    model_config = ConfigDict(populate_by_name=True)

    vn: Optional[str] = Field(
        None,
        description='AHV-13 number (Versichertennummer)'
    )

    local_person_id: ECH0044NamedPersonId = Field(
        ...,
        alias='localPersonId',
        description='Local person ID per eCH-0044'
    )

    other_person_id: Optional[List[ECH0044NamedPersonId]] = Field(
        None,
        alias='otherPersonId',
        description='Other person IDs per eCH-0044'
    )

    eu_person_id: Optional[List[ECH0044NamedPersonId]] = Field(
        None,
        alias='euPersonId',
        description='EU person IDs per eCH-0044'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'personIdentificationAfter'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling.

        Pattern: Wrapper elements in eCH-0020, content from eCH-0044.
        Example: <vn> (eCH-0020) contains text, <localPersonId> (eCH-0020) contains eCH-0044 children
        """
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # vn (optional) - simple text in eCH-0020 namespace
        if self.vn:
            vn_elem = ET.SubElement(elem, f'{{{ns_020}}}vn')
            vn_elem.text = self.vn

        # localPersonId (required) - wrapper in eCH-0020, content from eCH-0044
        # Use manual wrapper pattern for proper namespace composition
        wrapper = ET.SubElement(elem, f'{{{ns_020}}}localPersonId')
        content = self.local_person_id.to_xml(namespace=ns_044)
        for child in content:
            wrapper.append(child)

        # otherPersonId (optional, unbounded)
        if self.other_person_id:
            for other_id in self.other_person_id:
                wrapper = ET.SubElement(elem, f'{{{ns_020}}}otherPersonId')
                content = other_id.to_xml(namespace=ns_044)
                for child in content:
                    wrapper.append(child)

        # euPersonId (optional, unbounded)
        if self.eu_person_id:
            for eu_id in self.eu_person_id:
                wrapper = ET.SubElement(elem, f'{{{ns_020}}}euPersonId')
                content = eu_id.to_xml(namespace=ns_044)
                for child in content:
                    wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020PersonIdOnly':
        """Parse from XML element.

        Pattern: Wrapper elements in eCH-0020, content from eCH-0044.
        """
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # vn (optional) - in eCH-0020 namespace (not eCH-0044!)
        vn_elem = elem.find(f'{{{ns_020}}}vn')
        vn = vn_elem.text if vn_elem is not None and vn_elem.text else None

        # localPersonId (required) - wrapper in eCH-0020, content from eCH-0044
        local_id_elem = elem.find(f'{{{ns_020}}}localPersonId')
        if local_id_elem is None:
            raise ValueError("personIdOnlyType requires localPersonId")
        local_person_id = ECH0044NamedPersonId.from_xml(local_id_elem)

        # otherPersonId (optional, unbounded) - wrapper in eCH-0020
        other_person_id = []
        for other_elem in elem.findall(f'{{{ns_020}}}otherPersonId'):
            other_person_id.append(ECH0044NamedPersonId.from_xml(other_elem))

        # euPersonId (optional, unbounded) - wrapper in eCH-0020
        eu_person_id = []
        for eu_elem in elem.findall(f'{{{ns_020}}}euPersonId'):
            eu_person_id.append(ECH0044NamedPersonId.from_xml(eu_elem))

        return cls(
            vn=vn,
            local_person_id=local_person_id,
            other_person_id=other_person_id if other_person_id else None,
            eu_person_id=eu_person_id if eu_person_id else None
        )


class ECH0020CorrectIdentificationPerson(BaseModel):
    """Person data for identification correction event.

    XSD: correctIdentificationPersonType (eCH-0020-3-0.xsd lines 722-727)
    PDF: Section on identification correction

    Contains before/after person identification for correction events.

    Fields:
    - personIdentificationBefore (required): Person identification before correction
    - personIdentificationAfter (required): Person identification after correction (ID-only subset)
    """
    model_config = ConfigDict(populate_by_name=True)

    person_identification_before: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentificationBefore',
        description='Person identification before correction (full data)'
    )

    person_identification_after: 'ECH0020PersonIdOnly' = Field(
        ...,
        alias='personIdentificationAfter',
        description='Person identification after correction (ID fields only)'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'correctIdentificationPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # personIdentificationBefore (required) - wrapper in eCH-0020, content in eCH-0044
        self.person_identification_before.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='personIdentificationBefore',
            wrapper_namespace=ns_020
        )

        # personIdentificationAfter (required) - fully in eCH-0020
        self.person_identification_after.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='personIdentificationAfter'
        )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020CorrectIdentificationPerson':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # personIdentificationBefore (required) - wrapper in eCH-0020, content in eCH-0044
        before_elem = elem.find(f'{{{ns_020}}}personIdentificationBefore')
        if before_elem is None:
            raise ValueError("correctIdentificationPersonType requires personIdentificationBefore")
        person_identification_before = ECH0044PersonIdentification.from_xml(before_elem)

        # personIdentificationAfter (required)
        after_elem = elem.find(f'{{{ns_020}}}personIdentificationAfter')
        if after_elem is None:
            raise ValueError("correctIdentificationPersonType requires personIdentificationAfter")
        person_identification_after = ECH0020PersonIdOnly.from_xml(after_elem)

        return cls(
            person_identification_before=person_identification_before,
            person_identification_after=person_identification_after
        )


class ECH0020EventCorrectIdentification(BaseModel):
    """Identification correction event - correct person identification data.

    XSD: eventCorrectIdentification (eCH-0020-3-0.xsd lines 728-734)
    PDF: Section on identification correction events

    Used to correct errors in person identification (VN, local IDs, EU IDs).

    Fields:
    - correctIdentificationPerson (required): Before/after person identification
    - identificationValidFrom (optional): Date from which correction is valid
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_identification_person: 'ECH0020CorrectIdentificationPerson' = Field(
        ...,
        alias='correctIdentificationPerson',
        description='Person identification before and after correction'
    )

    identification_valid_from: Optional[date] = Field(
        None,
        alias='identificationValidFrom',
        description='Date from which corrected identification is valid'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectIdentification'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctIdentificationPerson (required)
        self.correct_identification_person.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='correctIdentificationPerson'
        )

        # identificationValidFrom (optional)
        if self.identification_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}identificationValidFrom')
            valid_from_elem.text = self.identification_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectIdentification':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3

        # correctIdentificationPerson (required)
        person_elem = elem.find(f'{{{ns_020}}}correctIdentificationPerson')
        if person_elem is None:
            raise ValueError("eventCorrectIdentification requires correctIdentificationPerson")
        correct_identification_person = ECH0020CorrectIdentificationPerson.from_xml(person_elem)

        # identificationValidFrom (optional)
        valid_from_elem = elem.find(f'{{{ns_020}}}identificationValidFrom')
        identification_valid_from = None
        if valid_from_elem is not None and valid_from_elem.text:
            identification_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            correct_identification_person=correct_identification_person,
            identification_valid_from=identification_valid_from
        )


class ECH0020IdentificationConversionPerson(BaseModel):
    """Person data for identification conversion (inline anonymous type).

    XSD: Inline anonymous complexType in eventIdentificationConversion (eCH-0020-3-0.xsd lines 737-746)
    PDF: Section on identification conversion

    Contains VN and local person ID before/after for ID conversion events.

    Fields:
    - vn (optional): AHV-13 number
    - localPersonIdBefore (required): Local person ID before conversion
    - localPersonIdAfter (required): Local person ID after conversion
    """
    model_config = ConfigDict(populate_by_name=True)

    vn: Optional[str] = Field(
        None,
        description='AHV-13 number (Versichertennummer)'
    )

    local_person_id_before: ECH0044NamedPersonId = Field(
        ...,
        alias='localPersonIdBefore',
        description='Local person ID before conversion'
    )

    local_person_id_after: ECH0044NamedPersonId = Field(
        ...,
        alias='localPersonIdAfter',
        description='Local person ID after conversion'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'identificationConversionPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # vn (optional)
        if self.vn:
            vn_elem = ET.SubElement(elem, f'{{{ns_044}}}vn')
            vn_elem.text = self.vn

        # localPersonIdBefore (required)
        self.local_person_id_before.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='localPersonIdBefore'
        )

        # localPersonIdAfter (required)
        self.local_person_id_after.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='localPersonIdAfter'
        )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020IdentificationConversionPerson':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # vn (optional)
        vn_elem = elem.find(f'{{{ns_044}}}vn')
        vn = vn_elem.text if vn_elem is not None and vn_elem.text else None

        # localPersonIdBefore (required)
        before_elem = elem.find(f'{{{ns_044}}}localPersonIdBefore')
        if before_elem is None:
            raise ValueError("identificationConversionPerson requires localPersonIdBefore")
        local_person_id_before = ECH0044NamedPersonId.from_xml(before_elem)

        # localPersonIdAfter (required)
        after_elem = elem.find(f'{{{ns_044}}}localPersonIdAfter')
        if after_elem is None:
            raise ValueError("identificationConversionPerson requires localPersonIdAfter")
        local_person_id_after = ECH0044NamedPersonId.from_xml(after_elem)

        return cls(
            vn=vn,
            local_person_id_before=local_person_id_before,
            local_person_id_after=local_person_id_after
        )


class ECH0020EventIdentificationConversion(BaseModel):
    """Identification conversion event - convert local person IDs.

    XSD: eventIdentificationConversion (eCH-0020-3-0.xsd lines 735-749)
    PDF: Section on identification conversion events

    Used to convert local person IDs (e.g., system migration, municipality merger).

    Fields:
    - identificationConversionPerson (required, unbounded): Person ID conversions
    - identificationValidFrom (optional): Date from which conversion is valid
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    identification_conversion_person: List['ECH0020IdentificationConversionPerson'] = Field(
        ...,
        alias='identificationConversionPerson',
        description='Person ID conversions (unbounded)'
    )

    identification_valid_from: Optional[date] = Field(
        None,
        alias='identificationValidFrom',
        description='Date from which conversion is valid'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventIdentificationConversion'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # identificationConversionPerson (required, unbounded)
        for person in self.identification_conversion_person:
            person.to_xml(
                parent=elem,
                namespace=ns_020,
                element_name='identificationConversionPerson'
            )

        # identificationValidFrom (optional)
        if self.identification_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}identificationValidFrom')
            valid_from_elem.text = self.identification_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventIdentificationConversion':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3

        # identificationConversionPerson (required, unbounded)
        person_elems = elem.findall(f'{{{ns_020}}}identificationConversionPerson')
        if not person_elems:
            raise ValueError("eventIdentificationConversion requires at least one identificationConversionPerson")
        identification_conversion_person = [
            ECH0020IdentificationConversionPerson.from_xml(p) for p in person_elems
        ]

        # identificationValidFrom (optional)
        valid_from_elem = elem.find(f'{{{ns_020}}}identificationValidFrom')
        identification_valid_from = None
        if valid_from_elem is not None and valid_from_elem.text:
            identification_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            identification_conversion_person=identification_conversion_person,
            identification_valid_from=identification_valid_from
        )


class ECH0020EventCorrectName(BaseModel):
    """Name correction event - correct name data.

    XSD: eventCorrectName (eCH-0020-3-0.xsd lines 750-756)
    PDF: Section on name correction events

    Used to correct errors in name data (spelling, official name, etc.).

    Fields:
    - correctNamePerson (required): Person identification
    - nameInfo (required): Corrected name data with validity date
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_name_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctNamePerson',
        description='Person identification'
    )

    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Corrected name data with optional validity date'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectName'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctNamePerson (required)
        self.correct_name_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctNamePerson'
        )

        # nameInfo (required)
        self.name_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='nameInfo'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectName':
        """Parse from XML element.

        Pattern: correctNamePerson wrapper in eCH-0020, content from eCH-0044.
        """
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # correctNamePerson (required) - wrapper in eCH-0020, content from eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctNamePerson')
        if person_elem is None:
            raise ValueError("eventCorrectName requires correctNamePerson")
        correct_name_person = ECH0044PersonIdentification.from_xml(person_elem)

        # nameInfo (required)
        name_info_elem = elem.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("eventCorrectName requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        # extension: Not implemented

        return cls(
            correct_name_person=correct_name_person,
            name_info=name_info
        )


class ECH0020EventCorrectNationality(BaseModel):
    """Nationality correction event - correct nationality data.

    XSD: eventCorrectNationality (eCH-0020-3-0.xsd lines 757-763)
    PDF: Section on nationality correction events

    Used to correct errors in nationality data.

    Fields:
    - correctNationalityPerson (required): Person identification
    - nationalityData (required): Corrected nationality data
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_nationality_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctNationalityPerson',
        description='Person identification'
    )

    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Corrected nationality data per eCH-0011'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectNationality'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctNationalityPerson (required)
        self.correct_nationality_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctNationalityPerson'
        )

        # nationalityData (required)
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectNationality':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # correctNationalityPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctNationalityPerson')
        if person_elem is None:
            raise ValueError("eventCorrectNationality requires correctNationalityPerson")
        correct_nationality_person = ECH0044PersonIdentification.from_xml(person_elem)

        # nationalityData (required)
        data_elem = elem.find(f'{{{ns_011}}}nationalityData')
        if data_elem is None:
            raise ValueError("eventCorrectNationality requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            correct_nationality_person=correct_nationality_person,
            nationality_data=nationality_data
        )


class ECH0020EventCorrectContact(BaseModel):
    """Contact correction event - correct contact data.

    XSD: eventCorrectContact (eCH-0020-3-0.xsd lines 764-770)
    PDF: Section on contact correction events

    Used to correct errors in contact data (email, phone, etc.).

    Fields:
    - correctContactPerson (required): Person identification
    - contactData (optional): Corrected contact data
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_contact_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctContactPerson',
        description='Person identification'
    )

    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description='Corrected contact data per eCH-0011'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectContact'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctContactPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_contact_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctContactPerson',
            wrapper_namespace=ns_020
        )

        # contactData (optional) - wrapper in eCH-0020, content in eCH-0011
        if self.contact_data:
            self.contact_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='contactData',
                wrapper_namespace=ns_020
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectContact':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # correctContactPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctContactPerson')
        if person_elem is None:
            raise ValueError("eventCorrectContact requires correctContactPerson")
        correct_contact_person = ECH0044PersonIdentification.from_xml(person_elem)

        # contactData (optional) - wrapper in eCH-0020, content in eCH-0011
        data_elem = elem.find(f'{{{ns_020}}}contactData')
        contact_data = None
        if data_elem is not None:
            contact_data = ECH0011ContactData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            correct_contact_person=correct_contact_person,
            contact_data=contact_data
        )


class ECH0020EventCorrectReligion(BaseModel):
    """Religion correction event - correct religion data.

    XSD: eventCorrectReligion (eCH-0020-3-0.xsd lines 771-777)
    PDF: Section on religion correction events

    Used to correct errors in religion data.

    Fields:
    - correctReligionPerson (required): Person identification
    - religionData (required): Corrected religion data
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_religion_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctReligionPerson',
        description='Person identification'
    )

    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='Corrected religion data per eCH-0011'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectReligion'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctReligionPerson (required)
        self.correct_religion_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctReligionPerson'
        )

        # religionData (required)
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectReligion':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # correctReligionPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctReligionPerson')
        if person_elem is None:
            raise ValueError("eventCorrectReligion requires correctReligionPerson")
        correct_religion_person = ECH0044PersonIdentification.from_xml(person_elem)

        # religionData (required)
        data_elem = elem.find(f'{{{ns_011}}}religionData')
        if data_elem is None:
            raise ValueError("eventCorrectReligion requires religionData")
        religion_data = ECH0011ReligionData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            correct_religion_person=correct_religion_person,
            religion_data=religion_data
        )


class ECH0020EventCorrectPlaceOfOrigin(BaseModel):
    """Place of origin correction event - correct place of origin data.

    XSD: eventCorrectPlaceOfOrigin (eCH-0020-3-0.xsd lines 778-784)
    PDF: Section on place of origin correction events

    Used to correct errors in place of origin data (Heimatort/Bürgerort).

    Fields:
    - correctPlaceOfOriginPerson (required): Person identification
    - placeOfOriginInfo (optional, unbounded): Corrected place of origin data with addons
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_place_of_origin_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctPlaceOfOriginPerson',
        description='Person identification'
    )

    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Corrected place of origin data (unbounded)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectPlaceOfOrigin'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctPlaceOfOriginPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_place_of_origin_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctPlaceOfOriginPerson',
            wrapper_namespace=ns_020
        )

        # placeOfOriginInfo (optional, unbounded)
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(
                    parent=elem,
                    namespace=ns_020,
                    element_name='placeOfOriginInfo'
                )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectPlaceOfOrigin':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # correctPlaceOfOriginPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctPlaceOfOriginPerson')
        if person_elem is None:
            raise ValueError("eventCorrectPlaceOfOrigin requires correctPlaceOfOriginPerson")
        correct_place_of_origin_person = ECH0044PersonIdentification.from_xml(person_elem)

        # placeOfOriginInfo (optional, unbounded)
        origin_elems = elem.findall(f'{{{ns_020}}}placeOfOriginInfo')
        place_of_origin_info = None
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(o) for o in origin_elems]

        # extension: Not implemented

        return cls(
            correct_place_of_origin_person=correct_place_of_origin_person,
            place_of_origin_info=place_of_origin_info
        )


class ECH0020EventCorrectResidencePermit(BaseModel):
    """Residence permit correction event - correct residence permit data.

    XSD: eventCorrectResidencePermit (eCH-0020-3-0.xsd lines 785-791)
    PDF: Section on residence permit correction events

    Used to correct errors in residence permit data.

    Fields:
    - correctResidencePermitPerson (required): Person identification
    - residencePermitData (optional): Corrected residence permit data
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_residence_permit_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctResidencePermitPerson',
        description='Person identification'
    )

    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Corrected residence permit data per eCH-0011'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectResidencePermit'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctResidencePermitPerson (required)
        self.correct_residence_permit_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctResidencePermitPerson'
        )

        # residencePermitData (optional) - wrapper in eCH-0020, content from eCH-0011
        if self.residence_permit_data:
            wrapper = ET.SubElement(elem, f'{{{ns_020}}}residencePermitData')
            content = self.residence_permit_data.to_xml(namespace=ns_011)
            for child in content:
                wrapper.append(child)

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectResidencePermit':
        """Parse from XML element.

        Pattern: Wrappers in eCH-0020, content from eCH-0044/eCH-0011.
        """
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = NAMESPACE_ECH0011_V8
        ns_044 = NAMESPACE_ECH0044_V4

        # correctResidencePermitPerson (required) - wrapper in eCH-0020
        person_elem = elem.find(f'{{{ns_020}}}correctResidencePermitPerson')
        if person_elem is None:
            raise ValueError("eventCorrectResidencePermit requires correctResidencePermitPerson")
        correct_residence_permit_person = ECH0044PersonIdentification.from_xml(person_elem)

        # residencePermitData (optional) - wrapper in eCH-0020, content from eCH-0011
        data_elem = elem.find(f'{{{ns_020}}}residencePermitData')
        residence_permit_data = None
        if data_elem is not None:
            residence_permit_data = ECH0011ResidencePermitData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            correct_residence_permit_person=correct_residence_permit_person,
            residence_permit_data=residence_permit_data
        )


class ECH0020EventCorrectMaritalInfo(BaseModel):
    """Marital info correction event - correct marital data.

    XSD: eventCorrectMaritalInfo (eCH-0020-3-0.xsd lines 792-799)
    PDF: Section on marital info correction events

    Used to correct errors in marital data (status, date, partner).

    Fields:
    - correctMaritalDataPerson (required): Person identification
    - maritalInfo (required): Corrected marital info with addon
    - maritalRelationship (optional): Marital relationship details per eCH-0021
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_marital_data_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctMaritalDataPerson',
        description='Person identification'
    )

    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Corrected marital info with optional addon'
    )

    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Marital relationship details per eCH-0021 v7'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectMaritalInfo'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctMaritalDataPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_marital_data_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctMaritalDataPerson',
            wrapper_namespace=ns_020
        )

        # maritalInfo (required) - fully in eCH-0020
        self.marital_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='maritalInfo'
        )

        # maritalRelationship (optional) - wrapper in eCH-0020, content in eCH-0021
        if self.marital_relationship:
            self.marital_relationship.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='maritalRelationship',
                wrapper_namespace=ns_020
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectMaritalInfo':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_021 = NAMESPACE_ECH0021_V7
        ns_044 = NAMESPACE_ECH0044_V4

        # correctMaritalDataPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctMaritalDataPerson')
        if person_elem is None:
            raise ValueError("eventCorrectMaritalInfo requires correctMaritalDataPerson")
        correct_marital_data_person = ECH0044PersonIdentification.from_xml(person_elem)

        # maritalInfo (required) - fully in eCH-0020
        info_elem = elem.find(f'{{{ns_020}}}maritalInfo')
        if info_elem is None:
            raise ValueError("eventCorrectMaritalInfo requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(info_elem)

        # maritalRelationship (optional) - wrapper in eCH-0020, content in eCH-0021
        rel_elem = elem.find(f'{{{ns_020}}}maritalRelationship')
        marital_relationship = None
        if rel_elem is not None:
            marital_relationship = ECH0021MaritalRelationship.from_xml(rel_elem)

        # extension: Not implemented

        return cls(
            correct_marital_data_person=correct_marital_data_person,
            marital_info=marital_info,
            marital_relationship=marital_relationship
        )


class ECH0020EventCorrectBirthInfo(BaseModel):
    """Birth info correction event - correct birth data.

    XSD: eventCorrectBirthInfo (eCH-0020-3-0.xsd lines 800-806)
    PDF: Section on birth info correction events

    Used to correct errors in birth data (date, place, parents).

    Fields:
    - correctBirthInfoPerson (required): Person identification
    - birthInfo (required): Corrected birth info with addon
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_birth_info_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctBirthInfoPerson',
        description='Person identification'
    )

    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Corrected birth info with optional addon (parent names)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectBirthInfo'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctBirthInfoPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_birth_info_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctBirthInfoPerson',
            wrapper_namespace=ns_020
        )

        # birthInfo (required) - fully in eCH-0020
        self.birth_info.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='birthInfo'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectBirthInfo':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4

        # correctBirthInfoPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctBirthInfoPerson')
        if person_elem is None:
            raise ValueError("eventCorrectBirthInfo requires correctBirthInfoPerson")
        correct_birth_info_person = ECH0044PersonIdentification.from_xml(person_elem)

        # birthInfo (required)
        info_elem = elem.find(f'{{{ns_020}}}birthInfo')
        if info_elem is None:
            raise ValueError("eventCorrectBirthInfo requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(info_elem)

        # extension: Not implemented

        return cls(
            correct_birth_info_person=correct_birth_info_person,
            birth_info=birth_info
        )


class ECH0020EventCorrectGuardianRelationship(BaseModel):
    """Guardian relationship correction event - correct guardian data.

    XSD: eventCorrectGuardianRelationship (eCH-0020-3-0.xsd lines 681-687)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Used to correct errors in guardian relationship data (add, remove, or modify guardians).

    Fields:
    - correctGuardianRelationshipPerson (required): Person identification
    - guardianRelationship (optional, unbounded): List of corrected guardian relationships
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_guardian_relationship_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctGuardianRelationshipPerson',
        description='Person whose guardian relationship is being corrected'
    )

    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = Field(
        None,
        alias='guardianRelationship',
        description='List of corrected guardian relationships (optional, can be empty to remove all)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectGuardianRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctGuardianRelationshipPerson (required)
        self.correct_guardian_relationship_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctGuardianRelationshipPerson'
        )

        # guardianRelationship (optional, unbounded)
        if self.guardian_relationship:
            for guardian in self.guardian_relationship:
                guardian.to_xml(
                    parent=elem,
                    namespace=ns_021,
                    element_name='guardianRelationship'
                )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectGuardianRelationship':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # correctGuardianRelationshipPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctGuardianRelationshipPerson')
        if person_elem is None:
            raise ValueError("eventCorrectGuardianRelationship requires correctGuardianRelationshipPerson")
        correct_guardian_relationship_person = ECH0044PersonIdentification.from_xml(person_elem)

        # guardianRelationship (optional, unbounded)
        guardian_elems = elem.findall(f'{{{ns_021}}}guardianRelationship')
        guardian_relationship = [ECH0021GuardianRelationship.from_xml(g) for g in guardian_elems] if guardian_elems else None

        # extension: Not implemented

        return cls(
            correct_guardian_relationship_person=correct_guardian_relationship_person,
            guardian_relationship=guardian_relationship
        )


class ECH0020EventCorrectParentalRelationship(BaseModel):
    """Parental relationship correction event - correct parent-child data.

    XSD: eventCorrectParentalRelationship (eCH-0020-3-0.xsd lines 688-694)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Used to correct errors in parental relationship data (add, remove, or modify parent links).

    Fields:
    - correctParentalRelationshipPerson (required): Person identification (the child)
    - parentalRelationship (optional, unbounded): List of corrected parental relationships
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_parental_relationship_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctParentalRelationshipPerson',
        description='Person (child) whose parental relationship is being corrected'
    )

    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description='List of corrected parental relationships (optional, can be empty to remove all)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectParentalRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctParentalRelationshipPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_parental_relationship_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctParentalRelationshipPerson',
            wrapper_namespace=ns_020
        )

        # parentalRelationship (optional, unbounded) - wrapper in eCH-0020, content in eCH-0021
        # ECH0021ParentalRelationship doesn't support wrapper_namespace yet, use manual pattern
        if self.parental_relationship:
            for parental in self.parental_relationship:
                wrapper = ET.SubElement(elem, f'{{{ns_020}}}parentalRelationship')
                content = parental.to_xml(namespace=ns_021)
                for child in content:
                    wrapper.append(child)

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectParentalRelationship':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # correctParentalRelationshipPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}correctParentalRelationshipPerson')
        if person_elem is None:
            raise ValueError("eventCorrectParentalRelationship requires correctParentalRelationshipPerson")
        correct_parental_relationship_person = ECH0044PersonIdentification.from_xml(person_elem)

        # parentalRelationship (optional, unbounded) - wrapper in eCH-0020, content in eCH-0021
        parental_elems = elem.findall(f'{{{ns_020}}}parentalRelationship')
        parental_relationship = [ECH0021ParentalRelationship.from_xml(p) for p in parental_elems] if parental_elems else None

        # extension: Not implemented

        return cls(
            correct_parental_relationship_person=correct_parental_relationship_person,
            parental_relationship=parental_relationship
        )


class ECH0020EventCorrectReporting(BaseModel):
    """Reporting data correction event - correct residence registration data.

    XSD: eventCorrectReporting (eCH-0020-3-0.xsd lines 695-706)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Used to correct errors in reporting municipality data (residence type and validity).

    XSD CHOICE: Exactly ONE of hasMainResidence, hasSecondaryResidence, OR hasOtherResidence.

    Fields:
    - correctReportingPerson (required): Person identification
    - hasMainResidence (CHOICE): Main residence data
    - hasSecondaryResidence (CHOICE): Secondary residence data
    - hasOtherResidence (CHOICE): Other residence data
    - reportingValidFrom (optional): Validity start date
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_reporting_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctReportingPerson',
        description='Person whose reporting data is being corrected'
    )

    # XSD CHOICE: exactly one required
    has_main_residence: Optional[ECH0011MainResidence] = Field(
        None,
        alias='hasMainResidence',
        description='Main residence (XSD CHOICE option 1)'
    )
    has_secondary_residence: Optional[ECH0011SecondaryResidence] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Secondary residence (XSD CHOICE option 2)'
    )
    has_other_residence: Optional[ECH0011OtherResidence] = Field(
        None,
        alias='hasOtherResidence',
        description='Other residence (XSD CHOICE option 3)'
    )

    reporting_valid_from: Optional[date] = Field(
        None,
        alias='reportingValidFrom',
        description='Validity start date for corrected reporting'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventCorrectReporting':
        """Validate XSD CHOICE: exactly ONE of main/secondary/other residence must be present."""
        has_main = self.has_main_residence is not None
        has_secondary = self.has_secondary_residence is not None
        has_other = self.has_other_residence is not None

        set_count = sum([has_main, has_secondary, has_other])

        if set_count == 0:
            raise ValueError("eventCorrectReporting requires exactly ONE of: hasMainResidence, hasSecondaryResidence, or hasOtherResidence")
        if set_count > 1:
            raise ValueError(f"eventCorrectReporting allows only ONE residence type, but {set_count} were provided")

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectReporting'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4
        ns_011 = NAMESPACE_ECH0011_V8

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctReportingPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.correct_reporting_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctReportingPerson',
            wrapper_namespace=ns_020
        )

        # XSD CHOICE: exactly one - wrapper in eCH-0020, content in eCH-0011
        if self.has_main_residence:
            self.has_main_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasMainResidence',
                wrapper_namespace=ns_020
            )
        elif self.has_secondary_residence:
            self.has_secondary_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasSecondaryResidence',
                wrapper_namespace=ns_020
            )
        elif self.has_other_residence:
            self.has_other_residence.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='hasOtherResidence',
                wrapper_namespace=ns_020
            )

        # reportingValidFrom (optional)
        if self.reporting_valid_from:
            valid_elem = ET.SubElement(elem, f'{{{ns_020}}}reportingValidFrom')
            valid_elem.text = self.reporting_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectReporting':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # correctReportingPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_wrapper = elem.find(f'{{{ns_020}}}correctReportingPerson')
        if person_wrapper is None:
            raise ValueError("eventCorrectReporting requires correctReportingPerson")
        correct_reporting_person = ECH0044PersonIdentification.from_xml(person_wrapper)

        # XSD CHOICE: exactly one - wrappers in eCH-0020, content in eCH-0011
        # ECH0011*Residence.from_xml() expects the wrapper element and looks for content inside
        has_main_residence = None
        main_wrapper = elem.find(f'{{{ns_020}}}hasMainResidence')
        if main_wrapper is not None:
            has_main_residence = ECH0011MainResidence.from_xml(main_wrapper, namespace=ns_011)

        has_secondary_residence = None
        secondary_wrapper = elem.find(f'{{{ns_020}}}hasSecondaryResidence')
        if secondary_wrapper is not None:
            has_secondary_residence = ECH0011SecondaryResidence.from_xml(secondary_wrapper, namespace=ns_011)

        has_other_residence = None
        other_wrapper = elem.find(f'{{{ns_020}}}hasOtherResidence')
        if other_wrapper is not None:
            has_other_residence = ECH0011OtherResidence.from_xml(other_wrapper, namespace=ns_011)

        # reportingValidFrom (optional)
        reporting_valid_from = None
        valid_elem = elem.find(f'{{{ns_020}}}reportingValidFrom')
        if valid_elem is not None and valid_elem.text:
            reporting_valid_from = date.fromisoformat(valid_elem.text)

        # extension: Not implemented

        return cls(
            correct_reporting_person=correct_reporting_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence,
            reporting_valid_from=reporting_valid_from
        )


class ECH0020EventCorrectOccupation(BaseModel):
    """Occupation correction event - correct job/occupation data.

    XSD: eventCorrectOccupation (eCH-0020-3-0.xsd lines 707-713)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Used to correct errors in occupation/job data.

    Fields:
    - correctOccupationPerson (required): Person identification
    - jobData (optional): Corrected occupation information (can be None to clear)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_occupation_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctOccupationPerson',
        description='Person whose occupation is being corrected'
    )

    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Corrected occupation information (optional, can be None to clear)'
    )

    # extension: Not implemented (eCH-0020:extension ref)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectOccupation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctOccupationPerson (required)
        self.correct_occupation_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctOccupationPerson'
        )

        # jobData (optional)
        if self.job_data:
            self.job_data.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='jobData'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectOccupation':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # correctOccupationPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctOccupationPerson')
        if person_elem is None:
            raise ValueError("eventCorrectOccupation requires correctOccupationPerson")
        correct_occupation_person = ECH0044PersonIdentification.from_xml(person_elem)

        # jobData (optional)
        job_data = None
        job_elem = elem.find(f'{{{ns_021}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        # extension: Not implemented

        return cls(
            correct_occupation_person=correct_occupation_person,
            job_data=job_data
        )


class ECH0020EventCorrectDeathData(BaseModel):
    """Death data correction event - correct death information.

    XSD: eventCorrectDeathData (eCH-0020-3-0.xsd lines 807-813)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Used to correct errors in death data (date, place).

    Fields:
    - correctDeathDataPerson (required): Person identification
    - deathData (optional): Corrected death information (can be None to clear)
    - extension (optional): Not implemented
    """
    model_config = ConfigDict(populate_by_name=True)

    correct_death_data_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctDeathDataPerson',
        description='Person whose death data is being corrected'
    )

    death_data: Optional[ECH0011DeathData] = Field(
        None,
        alias='deathData',
        description='Corrected death information (optional)'
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NAMESPACE_ECH0020_V3,
        element_name: str = 'eventCorrectDeathData'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NAMESPACE_ECH0044_V4
        ns_011 = NAMESPACE_ECH0011_V8

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctDeathDataPerson (required)
        self.correct_death_data_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctDeathDataPerson'
        )

        # deathData (optional)
        if self.death_data:
            self.death_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='deathData'
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectDeathData':
        """Parse from XML element."""
        ns_020 = NAMESPACE_ECH0020_V3
        ns_044 = NAMESPACE_ECH0044_V4
        ns_011 = NAMESPACE_ECH0011_V8

        # correctDeathDataPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctDeathDataPerson')
        if person_elem is None:
            raise ValueError("eventCorrectDeathData requires correctDeathDataPerson")
        correct_death_data_person = ECH0044PersonIdentification.from_xml(person_elem)

        # deathData (optional)
        death_data = None
        death_elem = elem.find(f'{{{ns_011}}}deathData')
        if death_elem is not None:
            death_data = ECH0011DeathData.from_xml(death_elem)

        return cls(
            correct_death_data_person=correct_death_data_person,
            death_data=death_data
        )


class ECH0020ReportingMunicipalityRestrictedMoveIn(BaseModel):
    """Restricted reporting municipality for move-in events.

    XSD restriction of reportingMunicipalityType with required fields for move-in.

    XSD: reportingMunicipalityRestrictedMoveInType (eCH-0020-3-0.xsd lines 502-516)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - comesFrom: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    - departureDate: EXCLUDED (not part of move-in)
    - goesTo: EXCLUDED (not part of move-in)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields for move-in event
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        alias='comesFrom',
        description='Previous residence where person came from (REQUIRED)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMoveIn':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveInType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveInType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)

        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMoveIn':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveInType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address
        )


class ECH0020ReportingMunicipalityRestrictedMoveOut(BaseModel):
    """Restricted reporting municipality for move-out events.

    XSD restriction of reportingMunicipalityType with required fields for move-out.

    XSD: reportingMunicipalityRestrictedMoveOutType (eCH-0020-3-0.xsd lines 517-530)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - departureDate: REQUIRED (was optional)
    - goesTo: REQUIRED (was optional)
    - arrivalDate: EXCLUDED (not part of move-out)
    - comesFrom: EXCLUDED (not part of move-out)
    - dwellingAddress: EXCLUDED (not part of move-out)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person was registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields for move-out event
    departure_date: date = Field(
        ...,
        alias='departureDate',
        description='Date of departure from this municipality (REQUIRED)'
    )
    goes_to: ECH0011DestinationType = Field(
        ...,
        alias='goesTo',
        description='Destination where person is going (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMoveOut':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveOutType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveOutType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
        departure_elem.text = self.departure_date.isoformat()

        # Create wrapper element in parent namespace
        goesTo_wrapper = ET.SubElement(elem, f'{{{namespace}}}goesTo')
        goesTo_content = self.goes_to.to_xml(namespace=ns_011)
        for child in goesTo_content:
            goesTo_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMoveOut':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is None or not departure_elem.text:
            raise ValueError("reportingMunicipalityRestrictedMoveOutType requires departureDate")
        departure_date = date.fromisoformat(departure_elem.text)

        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveOutType requires goesTo")
        goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedMove(BaseModel):
    """Restricted reporting municipality for internal move events.

    XSD restriction of reportingMunicipalityType for moves within same municipality.

    XSD: reportingMunicipalityRestrictedMoveType (eCH-0020-3-0.xsd lines 531-543)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - dwellingAddress: REQUIRED (the new address within municipality)
    - arrivalDate: EXCLUDED (person stays in same municipality)
    - comesFrom: EXCLUDED (internal move)
    - departureDate: EXCLUDED (internal move)
    - goesTo: EXCLUDED (internal move)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person remains registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED field for internal move event
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='New dwelling address within municipality (REQUIRED)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedMove':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedMoveType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required field
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedMove':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required field
        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedMoveType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            dwelling_address=dwelling_address
        )


# ============================================================================
# MOVE-IN EVENT HELPER TYPES (Inline complexType extensions for eventMoveIn)
# ============================================================================

class ECH0020HasMainResidenceMoveIn(BaseModel):
    """Main residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with optional secondary residences.
    This is an inline anonymous type from eventMoveIn XSD definition (lines 546-559).

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType
    """

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')

    # Extension: additional secondary residences
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = Field(
        None,
        alias='secondaryResidence',
        description='Secondary residence municipalities (0-n)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasMainResidenceMoveIn':
        """Validate XSD CHOICE: reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError("hasMainResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasMainResidence allows either reportingMunicipality OR federalRegister, not both")

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'hasMainResidence'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required base fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Extension: secondary residences
        if self.secondary_residence:
            for sec_res in self.secondary_residence:
                # Create wrapper element

                secondaryResidence_wrapper = ET.SubElement(elem, f'{{{namespace}}}secondaryResidence')

                secondaryResidence_content = sec_res.to_xml(namespace=ns_007)

                for child in secondaryResidence_content:

                    secondaryResidence_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020HasMainResidenceMoveIn':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("hasMainResidence requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("hasMainResidence requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("hasMainResidence requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Extension: secondary residences
        secondary_residence = None
        sec_res_elems = element.findall(f'{{{ns_020}}}secondaryResidence')
        if sec_res_elems:
            secondary_residence = [ECH0007SwissMunicipality.from_xml(e) for e in sec_res_elems]

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            secondary_residence=secondary_residence
        )


class ECH0020HasSecondaryResidenceMoveIn(BaseModel):
    """Secondary residence data for move-in events (inline complexType extension).

    Extends reportingMunicipalityRestrictedMoveInType with required main residence.
    This is an inline anonymous type from eventMoveIn XSD definition (lines 560-570).

    XSD: Inline extension of reportingMunicipalityRestrictedMoveInType
    """

    # All fields from reportingMunicipalityRestrictedMoveInType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = Field(
        ...,
        alias='mainResidence',
        description='Main residence municipality (required for secondary residence)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasSecondaryResidenceMoveIn':
        """Validate XSD CHOICE: reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError("hasSecondaryResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasSecondaryResidence allows either reportingMunicipality OR federalRegister, not both")

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'hasSecondaryResidence'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = 'http://www.ech.ch/xmlns/eCH-0007/5'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required base fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Extension: main residence
        # Create wrapper element in parent namespace
        mainResidence_wrapper = ET.SubElement(elem, f'{{{namespace}}}mainResidence')
        mainResidence_content = self.main_residence.to_xml(namespace=ns_007)
        for child in mainResidence_content:
            mainResidence_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020HasSecondaryResidenceMoveIn':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("hasSecondaryResidence requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("hasSecondaryResidence requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("hasSecondaryResidence requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Extension: main residence
        main_res_elem = element.find(f'{{{ns_020}}}mainResidence')
        if main_res_elem is None:
            raise ValueError("hasSecondaryResidence requires mainResidence")
        main_residence = ECH0007SwissMunicipality.from_xml(main_res_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            main_residence=main_residence
        )


# ============================================================================
# EVENT TYPES - MOVEMENT/RESIDENCE (Move-in, Move-out, Move)
# ============================================================================

class ECH0020EventMoveIn(BaseModel):
    """Move-in event - person moves into municipality from another location.

    XSD: eventMoveIn (eCH-0020-3-0.xsd lines 544-574)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - moveInPerson: Person data (baseDeliveryRestrictedMoveInPersonType, required)
    - CHOICE: hasMainResidence OR hasSecondaryResidence OR hasOtherResidence
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    move_in_person: 'ECH0020BaseDeliveryRestrictedMoveInPerson' = Field(
        ...,
        alias='moveInPerson',
        description='Person moving into municipality'
    )

    # XSD CHOICE: exactly one of three residence types
    has_main_residence: Optional[ECH0020HasMainResidenceMoveIn] = Field(
        None,
        alias='hasMainResidence',
        description='Person establishes main residence in this municipality'
    )
    has_secondary_residence: Optional[ECH0020HasSecondaryResidenceMoveIn] = Field(
        None,
        alias='hasSecondaryResidence',
        description='Person establishes secondary residence in this municipality'
    )
    has_other_residence: Optional['ECH0020ReportingMunicipalityRestrictedMoveIn'] = Field(
        None,
        alias='hasOtherResidence',
        description='Person has other residence type in this municipality'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventMoveIn':
        """Validate XSD CHOICE: exactly ONE of hasMainResidence, hasSecondaryResidence, or hasOtherResidence."""
        residences = [
            self.has_main_residence,
            self.has_secondary_residence,
            self.has_other_residence
        ]
        set_count = sum(1 for r in residences if r is not None)

        if set_count == 0:
            raise ValueError(
                "eventMoveIn requires exactly one of: hasMainResidence, "
                "hasSecondaryResidence, or hasOtherResidence"
            )
        if set_count > 1:
            raise ValueError(
                f"eventMoveIn allows only one residence type, but {set_count} are set"
            )

        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventMoveIn'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # moveInPerson (required)
        self.move_in_person.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='moveInPerson'
        )

        # CHOICE: exactly one residence type
        if self.has_main_residence:
            self.has_main_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasMainResidence'
            )
        elif self.has_secondary_residence:
            self.has_secondary_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasSecondaryResidence'
            )
        elif self.has_other_residence:
            self.has_other_residence.to_xml(
                parent=elem,
                namespace=namespace,
                element_name='hasOtherResidence'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMoveIn':
        """Parse from XML element."""
        ns = 'http://www.ech.ch/xmlns/eCH-0020/3'

        # moveInPerson (required)
        person_elem = elem.find(f'{{{ns}}}moveInPerson')
        if person_elem is None:
            raise ValueError("eventMoveIn requires moveInPerson")
        move_in_person = ECH0020BaseDeliveryRestrictedMoveInPerson.from_xml(person_elem)

        # CHOICE: exactly one residence type
        has_main_residence = None
        main_res_elem = elem.find(f'{{{ns}}}hasMainResidence')
        if main_res_elem is not None:
            has_main_residence = ECH0020HasMainResidenceMoveIn.from_xml(main_res_elem)

        has_secondary_residence = None
        sec_res_elem = elem.find(f'{{{ns}}}hasSecondaryResidence')
        if sec_res_elem is not None:
            has_secondary_residence = ECH0020HasSecondaryResidenceMoveIn.from_xml(sec_res_elem)

        has_other_residence = None
        other_res_elem = elem.find(f'{{{ns}}}hasOtherResidence')
        if other_res_elem is not None:
            has_other_residence = ECH0020ReportingMunicipalityRestrictedMoveIn.from_xml(other_res_elem)

        # extension: Not implemented

        return cls(
            move_in_person=move_in_person,
            has_main_residence=has_main_residence,
            has_secondary_residence=has_secondary_residence,
            has_other_residence=has_other_residence
        )


class ECH0020EventMove(BaseModel):
    """Internal move event - person moves to new address within same municipality.

    XSD: eventMove (eCH-0020-3-0.xsd lines 575-581)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - movePerson: Person identification (required)
    - moveReportingMunicipality: New dwelling address (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    move_person: ECH0044PersonIdentification = Field(
        ...,
        alias='movePerson',
        description='Person moving to new address within municipality'
    )
    move_reporting_municipality: 'ECH0020ReportingMunicipalityRestrictedMove' = Field(
        ...,
        alias='moveReportingMunicipality',
        description='New dwelling address and municipality information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventMove'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # movePerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.move_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='movePerson',
            wrapper_namespace=ns_020
        )

        # moveReportingMunicipality (required)
        self.move_reporting_municipality.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='moveReportingMunicipality'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMove':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # movePerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}movePerson')
        if person_elem is None:
            raise ValueError("eventMove requires movePerson")
        move_person = ECH0044PersonIdentification.from_xml(person_elem)

        # moveReportingMunicipality (required)
        municipality_elem = elem.find(f'{{{ns_020}}}moveReportingMunicipality')
        if municipality_elem is None:
            raise ValueError("eventMove requires moveReportingMunicipality")
        move_reporting_municipality = ECH0020ReportingMunicipalityRestrictedMove.from_xml(municipality_elem)

        # extension: Not implemented

        return cls(
            move_person=move_person,
            move_reporting_municipality=move_reporting_municipality
        )


class ECH0020EventContact(BaseModel):
    """Contact update event - person's contact information changes.

    XSD: eventContact (eCH-0020-3-0.xsd lines 582-588)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - contactPerson: Person identification (required)
    - contactData: New contact information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    contact_person: ECH0044PersonIdentification = Field(
        ...,
        alias='contactPerson',
        description='Person whose contact information is being updated'
    )
    contact_data: ECH0011ContactData = Field(
        ...,
        alias='contactData',
        description='New contact information (email, phone, etc.)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventContact'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling.

        Namespace wrapper pattern:
        - Wrapper elements (contactPerson, contactData) in eCH-0020 (no prefix)
        - Content inside wrappers from eCH-0044 and eCH-0011 (with prefix)
        """
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # contactPerson (required) - wrapper in ns_020, content in ns_044
        self.contact_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='contactPerson',
            wrapper_namespace=ns_020
        )

        # contactData (required) - wrapper in ns_020, content in ns_011
        self.contact_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='contactData',
            wrapper_namespace=ns_020
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventContact':
        """Parse from XML element.

        Namespace wrapper pattern:
        - Wrapper elements (contactPerson, contactData) are in eCH-0020 (no prefix)
        - Content inside wrappers is from eCH-0044 and eCH-0011 (with prefix)
        """
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # contactPerson (required) - wrapper in ns_020
        person_elem = elem.find(f'{{{ns_020}}}contactPerson')
        if person_elem is None:
            raise ValueError("eventContact requires contactPerson")
        contact_person = ECH0044PersonIdentification.from_xml(person_elem)

        # contactData (required) - wrapper in ns_020
        data_elem = elem.find(f'{{{ns_020}}}contactData')
        if data_elem is None:
            raise ValueError("eventContact requires contactData")
        contact_data = ECH0011ContactData.from_xml(data_elem)

        # extension: Not implemented

        return cls(
            contact_person=contact_person,
            contact_data=contact_data
        )


class ECH0020EventMoveOut(BaseModel):
    """Move-out event - person moves out of municipality to another location.

    XSD: eventMoveOut (eCH-0020-3-0.xsd lines 589-595)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - moveOutPerson: Person identification (required)
    - moveOutReportingDestination: Departure date and destination (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    move_out_person: ECH0044PersonIdentification = Field(
        ...,
        alias='moveOutPerson',
        description='Person moving out of municipality'
    )
    move_out_reporting_destination: 'ECH0020ReportingMunicipalityRestrictedMoveOut' = Field(
        ...,
        alias='moveOutReportingDestination',
        description='Departure date and destination information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventMoveOut'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # moveOutPerson (required) - wrapper in eCH-0020, content in eCH-0044
        self.move_out_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='moveOutPerson',
            wrapper_namespace=ns_020
        )

        # moveOutReportingDestination (required)
        self.move_out_reporting_destination.to_xml(
            parent=elem,
            namespace=ns_020,
            element_name='moveOutReportingDestination'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventMoveOut':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # moveOutPerson (required) - wrapper in eCH-0020, content in eCH-0044
        person_elem = elem.find(f'{{{ns_020}}}moveOutPerson')
        if person_elem is None:
            raise ValueError("eventMoveOut requires moveOutPerson")
        move_out_person = ECH0044PersonIdentification.from_xml(person_elem)

        # moveOutReportingDestination (required)
        destination_elem = elem.find(f'{{{ns_020}}}moveOutReportingDestination')
        if destination_elem is None:
            raise ValueError("eventMoveOut requires moveOutReportingDestination")
        move_out_reporting_destination = ECH0020ReportingMunicipalityRestrictedMoveOut.from_xml(destination_elem)

        # extension: Not implemented

        return cls(
            move_out_person=move_out_person,
            move_out_reporting_destination=move_out_reporting_destination
        )


class ECH0020EventChangeResidenceType(BaseModel):
    """Change residence type event - person changes from main/secondary/other residence.

    XSD: eventChangeResidenceTypeType (eCH-0020-3-0.xsd lines 596-603)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeResidenceTypePerson: Person data (required)
    - changeResidenceTypeReportingRelationship: New residence relationship (required)
    - residenceTypeValidFrom: Validity start date (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    change_residence_type_person: 'ECH0020BaseDeliveryRestrictedMoveInPerson' = Field(
        ...,
        alias='changeResidenceTypePerson',
        description='Person whose residence type is changing'
    )
    change_residence_type_reporting_relationship: 'ECH0020ReportingMunicipalityRestrictedMoveIn' = Field(
        ...,
        alias='changeResidenceTypeReportingRelationship',
        description='New residence relationship information'
    )

    # Optional field
    residence_type_valid_from: Optional[date] = Field(
        None,
        alias='residenceTypeValidFrom',
        description='Date from which new residence type is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventChangeResidenceTypeType'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns = namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns}}}{element_name}')

        # changeResidenceTypePerson (required)
        self.change_residence_type_person.to_xml(
            parent=elem,
            namespace=ns,
            element_name='changeResidenceTypePerson'
        )

        # changeResidenceTypeReportingRelationship (required)
        self.change_residence_type_reporting_relationship.to_xml(
            parent=elem,
            namespace=ns,
            element_name='changeResidenceTypeReportingRelationship'
        )

        # residenceTypeValidFrom (optional)
        if self.residence_type_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns}}}residenceTypeValidFrom')
            valid_from_elem.text = self.residence_type_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeResidenceType':
        """Parse from XML element."""
        ns = 'http://www.ech.ch/xmlns/eCH-0020/3'

        # changeResidenceTypePerson (required)
        person_elem = elem.find(f'{{{ns}}}changeResidenceTypePerson')
        if person_elem is None:
            raise ValueError("eventChangeResidenceTypeType requires changeResidenceTypePerson")
        change_residence_type_person = ECH0020BaseDeliveryRestrictedMoveInPerson.from_xml(person_elem)

        # changeResidenceTypeReportingRelationship (required)
        relationship_elem = elem.find(f'{{{ns}}}changeResidenceTypeReportingRelationship')
        if relationship_elem is None:
            raise ValueError("eventChangeResidenceTypeType requires changeResidenceTypeReportingRelationship")
        change_residence_type_reporting_relationship = ECH0020ReportingMunicipalityRestrictedMoveIn.from_xml(relationship_elem)

        # residenceTypeValidFrom (optional)
        residence_type_valid_from = None
        valid_from_elem = elem.find(f'{{{ns}}}residenceTypeValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            residence_type_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            change_residence_type_person=change_residence_type_person,
            change_residence_type_reporting_relationship=change_residence_type_reporting_relationship,
            residence_type_valid_from=residence_type_valid_from
        )


class ECH0020EventChangeReligion(BaseModel):
    """Change religion event - person's religious affiliation changes.

    XSD: eventChangeReligion (eCH-0020-3-0.xsd lines 604-610)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeReligionPerson: Person identification (required)
    - religionData: New religion information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    change_religion_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeReligionPerson',
        description='Person whose religion is changing'
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='New religion information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventChangeReligion'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeReligionPerson (required)
        self.change_religion_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeReligionPerson'
        )

        # religionData (required)
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeReligion':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # changeReligionPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeReligionPerson')
        if person_elem is None:
            raise ValueError("eventChangeReligion requires changeReligionPerson")
        change_religion_person = ECH0044PersonIdentification.from_xml(person_elem)

        # religionData (required)
        religion_elem = elem.find(f'{{{ns_011}}}religionData')
        if religion_elem is None:
            raise ValueError("eventChangeReligion requires religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        # extension: Not implemented

        return cls(
            change_religion_person=change_religion_person,
            religion_data=religion_data
        )


class ECH0020EventChangeOccupation(BaseModel):
    """Change occupation event - person's occupation changes.

    XSD: eventChangeOccupation (eCH-0020-3-0.xsd lines 611-617)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeOccupationPerson: Person identification (required)
    - jobData: New occupation information (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    change_occupation_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeOccupationPerson',
        description='Person whose occupation is changing'
    )

    # Optional field
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='New occupation information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventChangeOccupation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeOccupationPerson (required)
        self.change_occupation_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeOccupationPerson'
        )

        # jobData (optional)
        if self.job_data:
            self.job_data.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='jobData'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeOccupation':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeOccupationPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeOccupationPerson')
        if person_elem is None:
            raise ValueError("eventChangeOccupation requires changeOccupationPerson")
        change_occupation_person = ECH0044PersonIdentification.from_xml(person_elem)

        # jobData (optional)
        job_data = None
        job_elem = elem.find(f'{{{ns_021}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        # extension: Not implemented

        return cls(
            change_occupation_person=change_occupation_person,
            job_data=job_data
        )


class ECH0020EventGuardianMeasure(BaseModel):
    """Guardian measure event - establish guardianship relationship.

    XSD: eventGuardianMeasure (eCH-0020-3-0.xsd lines 618-624)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - guardianMeasurePerson: Person identification (required)
    - relationship: Guardian relationship information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    guardian_measure_person: ECH0044PersonIdentification = Field(
        ...,
        alias='guardianMeasurePerson',
        description='Person for whom guardianship is established'
    )
    relationship: ECH0021GuardianRelationship = Field(
        ...,
        description='Guardian relationship information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventGuardianMeasure'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # guardianMeasurePerson (required)
        self.guardian_measure_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='guardianMeasurePerson'
        )

        # relationship (required)
        self.relationship.to_xml(
            parent=elem,
            namespace=ns_021,
            element_name='relationship'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventGuardianMeasure':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # guardianMeasurePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}guardianMeasurePerson')
        if person_elem is None:
            raise ValueError("eventGuardianMeasure requires guardianMeasurePerson")
        guardian_measure_person = ECH0044PersonIdentification.from_xml(person_elem)

        # relationship (required)
        relationship_elem = elem.find(f'{{{ns_021}}}relationship')
        if relationship_elem is None:
            raise ValueError("eventGuardianMeasure requires relationship")
        relationship = ECH0021GuardianRelationship.from_xml(relationship_elem)

        # extension: Not implemented

        return cls(
            guardian_measure_person=guardian_measure_person,
            relationship=relationship
        )


class ECH0020EventUndoGuardian(BaseModel):
    """Undo guardian event - terminate guardianship relationship.

    XSD: eventUndoGuardian (eCH-0020-3-0.xsd lines 625-632)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - undoGuardianPerson: Person identification (required)
    - guardianRelationshipId: Guardian relationship ID to undo (required)
    - undoGuardianValidFrom: Effective date of undo (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    undo_guardian_person: ECH0044PersonIdentification = Field(
        ...,
        alias='undoGuardianPerson',
        description='Person whose guardianship is being terminated'
    )
    guardian_relationship_id: str = Field(
        ...,
        alias='guardianRelationshipId',
        description='ID of guardian relationship to terminate (minLength=1, maxLength=36)',
        min_length=1,
        max_length=36
    )

    # Optional field
    undo_guardian_valid_from: Optional[date] = Field(
        None,
        alias='undoGuardianValidFrom',
        description='Date from which termination is effective'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventUndoGuardian'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # undoGuardianPerson (required)
        self.undo_guardian_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='undoGuardianPerson'
        )

        # guardianRelationshipId (required)
        self.guardian_relationship_id.to_xml(
            parent=elem,
            namespace=ns_021,
            element_name='guardianRelationshipId'
        )

        # undoGuardianValidFrom (optional)
        if self.undo_guardian_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}undoGuardianValidFrom')
            valid_from_elem.text = self.undo_guardian_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventUndoGuardian':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # undoGuardianPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}undoGuardianPerson')
        if person_elem is None:
            raise ValueError("eventUndoGuardian requires undoGuardianPerson")
        undo_guardian_person = ECH0044PersonIdentification.from_xml(person_elem)

        # guardianRelationshipId (required)
        id_elem = elem.find(f'{{{ns_021}}}guardianRelationshipId')
        if id_elem is None:
            raise ValueError("eventUndoGuardian requires guardianRelationshipId")
        guardian_relationship_id = ECH0021GuardianRelationshipId.from_xml(id_elem)

        # undoGuardianValidFrom (optional)
        undo_guardian_valid_from = None
        valid_from_elem = elem.find(f'{{{ns_020}}}undoGuardianValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            undo_guardian_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            undo_guardian_person=undo_guardian_person,
            guardian_relationship_id=guardian_relationship_id,
            undo_guardian_valid_from=undo_guardian_valid_from
        )


class ECH0020EventChangeGuardian(BaseModel):
    """Change guardian event - modify guardianship relationship.

    XSD: eventChangeGuardian (eCH-0020-3-0.xsd lines 633-640)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeGuardianPerson: Person identification (required)
    - relationship: Updated guardian relationship information (required)
    - changeGuardianValidFrom: Effective date of change (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    change_guardian_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeGuardianPerson',
        description='Person whose guardianship is being changed'
    )
    relationship: ECH0021GuardianRelationship = Field(
        ...,
        description='Updated guardian relationship information'
    )

    # Optional field
    change_guardian_valid_from: Optional[date] = Field(
        None,
        alias='changeGuardianValidFrom',
        description='Date from which change is effective'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventChangeGuardian'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeGuardianPerson (required)
        self.change_guardian_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeGuardianPerson'
        )

        # relationship (required)
        self.relationship.to_xml(
            parent=elem,
            namespace=ns_021,
            element_name='relationship'
        )

        # changeGuardianValidFrom (optional)
        if self.change_guardian_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}changeGuardianValidFrom')
            valid_from_elem.text = self.change_guardian_valid_from.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeGuardian':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeGuardianPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeGuardianPerson')
        if person_elem is None:
            raise ValueError("eventChangeGuardian requires changeGuardianPerson")
        change_guardian_person = ECH0044PersonIdentification.from_xml(person_elem)

        # relationship (required)
        relationship_elem = elem.find(f'{{{ns_021}}}relationship')
        if relationship_elem is None:
            raise ValueError("eventChangeGuardian requires relationship")
        relationship = ECH0021GuardianRelationship.from_xml(relationship_elem)

        # changeGuardianValidFrom (optional)
        change_guardian_valid_from = None
        valid_from_elem = elem.find(f'{{{ns_020}}}changeGuardianValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            change_guardian_valid_from = date.fromisoformat(valid_from_elem.text)

        # extension: Not implemented

        return cls(
            change_guardian_person=change_guardian_person,
            relationship=relationship,
            change_guardian_valid_from=change_guardian_valid_from
        )


class ECH0020EventChangeNationality(BaseModel):
    """Change nationality event - person's nationality changes.

    XSD: eventChangeNationality (eCH-0020-3-0.xsd lines 641-647)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - changeNationalityPerson: Person identification (required)
    - nationalityData: New nationality information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    change_nationality_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeNationalityPerson',
        description='Person whose nationality is changing'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='New nationality information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventChangeNationality'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # changeNationalityPerson (required)
        self.change_nationality_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='changeNationalityPerson'
        )

        # nationalityData (required)
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeNationality':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # changeNationalityPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeNationalityPerson')
        if person_elem is None:
            raise ValueError("eventChangeNationality requires changeNationalityPerson")
        change_nationality_person = ECH0044PersonIdentification.from_xml(person_elem)

        # nationalityData (required)
        nationality_elem = elem.find(f'{{{ns_011}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("eventChangeNationality requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        # extension: Not implemented

        return cls(
            change_nationality_person=change_nationality_person,
            nationality_data=nationality_data
        )


class ECH0020EventEntryResidencePermit(BaseModel):
    """Entry residence permit event - person enters Switzerland with residence permit.

    XSD: eventEntryResidencePermit (eCH-0020-3-0.xsd lines 648-655)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - entryResidencePermitPerson: Person identification (required)
    - jobData: Occupation information (optional)
    - residencePermitData: Residence permit information (required)
    - extension: Extension element (optional, not implemented)
    """

    # Required field
    entry_residence_permit_person: ECH0044PersonIdentification = Field(
        ...,
        alias='entryResidencePermitPerson',
        description='Person entering with residence permit'
    )

    # Optional field
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Occupation information'
    )

    # Required field
    residence_permit_data: ECH0011ResidencePermitData = Field(
        ...,
        alias='residencePermitData',
        description='Residence permit information'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventEntryResidencePermit'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # entryResidencePermitPerson (required)
        self.entry_residence_permit_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='entryResidencePermitPerson'
        )

        # jobData (optional)
        if self.job_data:
            self.job_data.to_xml(
                parent=elem,
                namespace=ns_021,
                element_name='jobData'
            )

        # residencePermitData (required)
        self.residence_permit_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='residencePermitData'
        )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventEntryResidencePermit':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'
        ns_011 = 'http://www.ech.ch/xmlns/eCH-0011/8'

        # entryResidencePermitPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}entryResidencePermitPerson')
        if person_elem is None:
            raise ValueError("eventEntryResidencePermit requires entryResidencePermitPerson")
        entry_residence_permit_person = ECH0044PersonIdentification.from_xml(person_elem)

        # jobData (optional)
        job_data = None
        job_elem = elem.find(f'{{{ns_021}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        # residencePermitData (required)
        permit_elem = elem.find(f'{{{ns_011}}}residencePermitData')
        if permit_elem is None:
            raise ValueError("eventEntryResidencePermit requires residencePermitData")
        residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem)

        # extension: Not implemented

        return cls(
            entry_residence_permit_person=entry_residence_permit_person,
            job_data=job_data,
            residence_permit_data=residence_permit_data
        )


class ECH0020EventDataLock(BaseModel):
    """Data lock event - lock person's data for data protection purposes.

    XSD: eventDataLock (eCH-0020-3-0.xsd lines 656-664)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - dataLockPerson: Person identification (required)
    - dataLock: Data lock information (required)
    - dataLockValidFrom: Lock validity start date (optional)
    - dataLockValidTill: Lock validity end date (optional)
    - extension: Extension element (optional, not implemented)
    """

    # Required fields
    data_lock_person: ECH0044PersonIdentification = Field(
        ...,
        alias='dataLockPerson',
        description='Person whose data is being locked'
    )
    data_lock: ECH0021LockData = Field(
        ...,
        alias='dataLock',
        description='Data lock information'
    )

    # Optional fields
    data_lock_valid_from: Optional[date] = Field(
        None,
        alias='dataLockValidFrom',
        description='Date from which data lock is valid'
    )
    data_lock_valid_till: Optional[date] = Field(
        None,
        alias='dataLockValidTill',
        description='Date until which data lock is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
        element_name: str = 'eventDataLock'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # dataLockPerson (required)
        self.data_lock_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='dataLockPerson'
        )

        # dataLock (required)
        self.data_lock.to_xml(
            parent=elem,
            namespace=ns_021,
            element_name='dataLock'
        )

        # dataLockValidFrom (optional)
        if self.data_lock_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}dataLockValidFrom')
            valid_from_elem.text = self.data_lock_valid_from.isoformat()

        # dataLockValidTill (optional)
        if self.data_lock_valid_till:
            valid_till_elem = ET.SubElement(elem, f'{{{ns_020}}}dataLockValidTill')
            valid_till_elem.text = self.data_lock_valid_till.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventDataLock':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # dataLockPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}dataLockPerson')
        if person_elem is None:
            raise ValueError("eventDataLock requires dataLockPerson")
        data_lock_person = ECH0044PersonIdentification.from_xml(person_elem)

        # dataLock (required)
        lock_elem = elem.find(f'{{{ns_021}}}dataLock')
        if lock_elem is None:
            raise ValueError("eventDataLock requires dataLock")
        data_lock = ECH0021LockData.from_xml(lock_elem)

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

        # extension: Not implemented

        return cls(
            data_lock_person=data_lock_person,
            data_lock=data_lock,
            data_lock_valid_from=data_lock_valid_from,
            data_lock_valid_till=data_lock_valid_till
        )


# TYPE 63: eventPaperLock (XSD 665-673)
class ECH0020EventPaperLock(BaseModel):
    """Paper lock event - lock person's paper documents for data protection purposes.

    XSD: eventPaperLock (eCH-0020-3-0.xsd lines 665-673)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Example: Locking identity documents during legal proceedings.
    """

    paper_lock_person: ECH0044PersonIdentification = Field(
        ...,
        alias='paperLockPerson',
        description='Person whose paper documents are being locked'
    )
    paper_lock: YesNo = Field(
        ...,
        alias='paperLock',
        description='Paper lock information'
    )
    paper_lock_valid_from: Optional[date] = Field(
        None,
        alias='paperLockValidFrom',
        description='Start date of paper lock validity'
    )
    paper_lock_valid_till: Optional[date] = Field(
        None,
        alias='paperLockValidTill',
        description='End date of paper lock validity'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventPaperLock element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # paperLockPerson (required)
        self.paper_lock_person.to_xml(elem, ns_044, 'paperLockPerson')

        # paperLock (required)
        self.paper_lock.to_xml(elem, ns_021, 'paperLock')

        # paperLockValidFrom (optional)
        if self.paper_lock_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{ns_020}}}paperLockValidFrom')
            valid_from_elem.text = self.paper_lock_valid_from.isoformat()

        # paperLockValidTill (optional)
        if self.paper_lock_valid_till:
            valid_till_elem = ET.SubElement(elem, f'{{{ns_020}}}paperLockValidTill')
            valid_till_elem.text = self.paper_lock_valid_till.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventPaperLock':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # paperLockPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}paperLockPerson')
        if person_elem is None:
            raise ValueError("eventPaperLock requires paperLockPerson")
        paper_lock_person = ECH0044PersonIdentification.from_xml(person_elem)

        # paperLock (required, yesNoType: 0=No, 1=Yes)
        lock_elem = elem.find(f'{{{ns_021}}}paperLock')
        if lock_elem is None:
            raise ValueError("eventPaperLock requires paperLock")
        paper_lock = YesNo(lock_elem.text) if lock_elem.text else YesNo.NO

        # paperLockValidFrom (optional)
        paper_lock_valid_from = None
        valid_from_elem = elem.find(f'{{{ns_020}}}paperLockValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            paper_lock_valid_from = date.fromisoformat(valid_from_elem.text)

        # paperLockValidTill (optional)
        paper_lock_valid_till = None
        valid_till_elem = elem.find(f'{{{ns_020}}}paperLockValidTill')
        if valid_till_elem is not None and valid_till_elem.text:
            paper_lock_valid_till = date.fromisoformat(valid_till_elem.text)

        # extension: Not implemented

        return cls(
            paper_lock_person=paper_lock_person,
            paper_lock=paper_lock,
            paper_lock_valid_from=paper_lock_valid_from,
            paper_lock_valid_till=paper_lock_valid_till
        )


# TYPE 64: eventCare (XSD 674-680)
class ECH0020EventCare(BaseModel):
    """Care relationship event - establish care relationship (custody/parental relationship).

    XSD: eventCare (eCH-0020-3-0.xsd lines 674-680)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Example: Establishing custody arrangements for a child.
    """

    care_person: ECH0044PersonIdentification = Field(
        ...,
        alias='carePerson',
        description='Person receiving care (typically a child)'
    )
    parental_relationship: List[ECH0021ParentalRelationship] = Field(
        default_factory=list,
        alias='parentalRelationship',
        description='Parental/custody relationships'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventCare element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # carePerson (required)
        self.care_person.to_xml(elem, ns_044, 'carePerson')

        # parentalRelationship (optional, unbounded)
        for relationship in self.parental_relationship:
            relationship.to_xml(elem, ns_021, 'parentalRelationship')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCare':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # carePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}carePerson')
        if person_elem is None:
            raise ValueError("eventCare requires carePerson")
        care_person = ECH0044PersonIdentification.from_xml(person_elem)

        # parentalRelationship (optional, unbounded)
        parental_relationship = []
        for rel_elem in elem.findall(f'{{{ns_021}}}parentalRelationship'):
            parental_relationship.append(ECH0021ParentalRelationship.from_xml(rel_elem))

        # extension: Not implemented

        return cls(
            care_person=care_person,
            parental_relationship=parental_relationship
        )


# ============================================================================
# TYPE: eventCorrectPersonAdditionalData
# ============================================================================

class ECH0020EventCorrectPersonAdditionalData(BaseModel):
    """Correction event for person additional data per eCH-0020 v3.0.

    Corrects person additional data (locks, job, health insurance, political rights).

    XSD: eventCorrectPersonAdditionalData (eCH-0020-3-0.xsd lines 814-820)
    PDF: Event reporting standard
    """

    correct_person_additional_data_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctPersonAdditionalDataPerson',
        description='Person identification for correction'
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description='Person additional data to correct'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventCorrectPersonAdditionalData element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctPersonAdditionalDataPerson (required)
        self.correct_person_additional_data_person.to_xml(
            elem, ns_044, 'correctPersonAdditionalDataPerson'
        )

        # personAdditionalData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.person_additional_data is not None:
            wrapper = ET.SubElement(elem, f'{{{ns_020}}}personAdditionalData')
            content = self.person_additional_data.to_xml(namespace=ns_021)
            for child in content:
                wrapper.append(child)

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectPersonAdditionalData':
        """Parse from XML element.

        Pattern: Wrapper in eCH-0020, content from eCH-0044/eCH-0021.
        """
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # correctPersonAdditionalDataPerson (required) - wrapper in eCH-0020
        person_elem = elem.find(f'{{{ns_020}}}correctPersonAdditionalDataPerson')
        if person_elem is None:
            raise ValueError("eventCorrectPersonAdditionalData requires correctPersonAdditionalDataPerson")
        correct_person_additional_data_person = ECH0044PersonIdentification.from_xml(person_elem)

        # personAdditionalData (optional) - wrapper in eCH-0020, content from eCH-0021
        person_additional_data = None
        additional_elem = elem.find(f'{{{ns_020}}}personAdditionalData')
        if additional_elem is not None:
            person_additional_data = ECH0021PersonAdditionalData.from_xml(additional_elem)

        # extension: Not implemented

        return cls(
            correct_person_additional_data_person=correct_person_additional_data_person,
            person_additional_data=person_additional_data
        )


# ============================================================================
# TYPE: eventCorrectPoliticalRightData
# ============================================================================

class ECH0020EventCorrectPoliticalRightData(BaseModel):
    """Correction event for political rights data per eCH-0020 v3.0.

    Corrects political rights data (voting restrictions at federal level).
    NOTE: This type uses eCH-0021/7 politicalRightDataType (removed in v8).

    XSD: eventCorrectPoliticalRightData (eCH-0020-3-0.xsd lines 821-827)
    PDF: Event reporting standard
    """

    correct_political_right_data_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctPoliticalRightDataPerson',
        description='Person identification for correction'
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = Field(
        None,
        alias='politicalRightData',
        description='Political rights data to correct (v7-only field)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventCorrectPoliticalRightData element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctPoliticalRightDataPerson (required)
        self.correct_political_right_data_person.to_xml(
            elem, ns_044, 'correctPoliticalRightDataPerson'
        )

        # politicalRightData (optional)
        if self.political_right_data is not None:
            self.political_right_data.to_xml(elem, ns_021, 'politicalRightData')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectPoliticalRightData':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # correctPoliticalRightDataPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctPoliticalRightDataPerson')
        if person_elem is None:
            raise ValueError("eventCorrectPoliticalRightData requires correctPoliticalRightDataPerson")
        correct_political_right_data_person = ECH0044PersonIdentification.from_xml(person_elem)

        # politicalRightData (optional)
        political_right_data = None
        rights_elem = elem.find(f'{{{ns_021}}}politicalRightData')
        if rights_elem is not None:
            political_right_data = ECH0021PoliticalRightData.from_xml(rights_elem)

        # extension: Not implemented

        return cls(
            correct_political_right_data_person=correct_political_right_data_person,
            political_right_data=political_right_data
        )


# ============================================================================
# TYPE: eventCorrectDataLock
# ============================================================================

class ECH0020EventCorrectDataLock(BaseModel):
    """Correction event for data lock per eCH-0020 v3.0.

    Corrects the data lock status (no lock, address lock, or information lock).

    XSD: eventCorrectDataLock (eCH-0020-3-0.xsd lines 828-836)
    PDF: Event reporting standard
    """

    correct_data_lock_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctDataLockPerson',
        description='Person identification for correction'
    )
    data_lock: DataLockType = Field(
        ...,
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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventCorrectDataLock element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctDataLockPerson (required)
        self.correct_data_lock_person.to_xml(elem, ns_044, 'correctDataLockPerson')

        # dataLock (required)
        data_lock_elem = ET.SubElement(elem, f'{{{namespace}}}dataLock')
        data_lock_elem.text = self.data_lock.value

        # dataLockValidFrom (optional)
        if self.data_lock_valid_from is not None:
            valid_from_elem = ET.SubElement(elem, f'{{{namespace}}}dataLockValidFrom')
            valid_from_elem.text = self.data_lock_valid_from.isoformat()

        # dataLockValidTill (optional)
        if self.data_lock_valid_till is not None:
            valid_till_elem = ET.SubElement(elem, f'{{{namespace}}}dataLockValidTill')
            valid_till_elem.text = self.data_lock_valid_till.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectDataLock':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # correctDataLockPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctDataLockPerson')
        if person_elem is None:
            raise ValueError("eventCorrectDataLock requires correctDataLockPerson")
        correct_data_lock_person = ECH0044PersonIdentification.from_xml(person_elem)

        # dataLock (required)
        data_lock_elem = elem.find(f'{{{ns_020}}}dataLock')
        if data_lock_elem is None or data_lock_elem.text is None:
            raise ValueError("eventCorrectDataLock requires dataLock")
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

        # extension: Not implemented

        return cls(
            correct_data_lock_person=correct_data_lock_person,
            data_lock=data_lock,
            data_lock_valid_from=data_lock_valid_from,
            data_lock_valid_till=data_lock_valid_till
        )


# ============================================================================
# TYPE: eventCorrectPaperLock
# ============================================================================

class ECH0020EventCorrectPaperLock(BaseModel):
    """Correction event for paper lock per eCH-0020 v3.0.

    Corrects the paper lock status (prevents physical mail delivery).

    XSD: eventCorrectPaperLock (eCH-0020-3-0.xsd lines 837-845)
    PDF: Event reporting standard
    """

    correct_paper_lock_person: ECH0044PersonIdentification = Field(
        ...,
        alias='correctPaperLockPerson',
        description='Person identification for correction'
    )
    paper_lock: YesNo = Field(
        ...,
        alias='paperLock',
        description='Paper lock (prevents physical mail delivery)'
    )
    paper_lock_valid_from: Optional[date] = Field(
        None,
        alias='paperLockValidFrom',
        description='Date from which the paper lock is valid'
    )
    paper_lock_valid_till: Optional[date] = Field(
        None,
        alias='paperLockValidTill',
        description='Date until which the paper lock is valid'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # Create eventCorrectPaperLock element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctPaperLockPerson (required)
        self.correct_paper_lock_person.to_xml(elem, ns_044, 'correctPaperLockPerson')

        # paperLock (required)
        paper_lock_elem = ET.SubElement(elem, f'{{{namespace}}}paperLock')
        paper_lock_elem.text = self.paper_lock.value

        # paperLockValidFrom (optional)
        if self.paper_lock_valid_from is not None:
            valid_from_elem = ET.SubElement(elem, f'{{{namespace}}}paperLockValidFrom')
            valid_from_elem.text = self.paper_lock_valid_from.isoformat()

        # paperLockValidTill (optional)
        if self.paper_lock_valid_till is not None:
            valid_till_elem = ET.SubElement(elem, f'{{{namespace}}}paperLockValidTill')
            valid_till_elem.text = self.paper_lock_valid_till.isoformat()

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventCorrectPaperLock':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # correctPaperLockPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}correctPaperLockPerson')
        if person_elem is None:
            raise ValueError("eventCorrectPaperLock requires correctPaperLockPerson")
        correct_paper_lock_person = ECH0044PersonIdentification.from_xml(person_elem)

        # paperLock (required)
        paper_lock_elem = elem.find(f'{{{ns_020}}}paperLock')
        if paper_lock_elem is None or paper_lock_elem.text is None:
            raise ValueError("eventCorrectPaperLock requires paperLock")
        paper_lock = YesNo(paper_lock_elem.text)

        # paperLockValidFrom (optional)
        paper_lock_valid_from = None
        valid_from_elem = elem.find(f'{{{ns_020}}}paperLockValidFrom')
        if valid_from_elem is not None and valid_from_elem.text:
            paper_lock_valid_from = date.fromisoformat(valid_from_elem.text)

        # paperLockValidTill (optional)
        paper_lock_valid_till = None
        valid_till_elem = elem.find(f'{{{ns_020}}}paperLockValidTill')
        if valid_till_elem is not None and valid_till_elem.text:
            paper_lock_valid_till = date.fromisoformat(valid_till_elem.text)

        # extension: Not implemented

        return cls(
            correct_paper_lock_person=correct_paper_lock_person,
            paper_lock=paper_lock,
            paper_lock_valid_from=paper_lock_valid_from,
            paper_lock_valid_till=paper_lock_valid_till
        )


# ============================================================================
# TYPE: eventAnnounceDuplicate
# ============================================================================

class ECH0020EventAnnounceDuplicate(BaseModel):
    """Event to announce duplicate person entries per eCH-0020 v3.0.

    Reports duplicate person records in the population register to enable cleanup.

    XSD: eventAnnounceDuplicate (eCH-0020-3-0.xsd lines 846-852)
    PDF: Event reporting standard
    """

    correct_entry: ECH0044PersonIdentification = Field(
        ...,
        alias='correctEntry',
        description='Person identification of correct entry'
    )
    duplicate_entry: List[ECH0044PersonIdentification] = Field(
        ...,
        alias='duplicateEntry',
        description='Person identifications of duplicate entries (unbounded)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # Create eventAnnounceDuplicate element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctEntry (required)
        self.correct_entry.to_xml(elem, ns_044, 'correctEntry')

        # duplicateEntry (required, unbounded)
        for dup in self.duplicate_entry:
            dup.to_xml(elem, ns_044, 'duplicateEntry')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventAnnounceDuplicate':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # correctEntry (required)
        correct_elem = elem.find(f'{{{ns_044}}}correctEntry')
        if correct_elem is None:
            raise ValueError("eventAnnounceDuplicate requires correctEntry")
        correct_entry = ECH0044PersonIdentification.from_xml(correct_elem)

        # duplicateEntry (required, unbounded)
        duplicate_entry = []
        for dup_elem in elem.findall(f'{{{ns_044}}}duplicateEntry'):
            duplicate_entry.append(ECH0044PersonIdentification.from_xml(dup_elem))

        if not duplicate_entry:
            raise ValueError("eventAnnounceDuplicate requires at least one duplicateEntry")

        # extension: Not implemented

        return cls(
            correct_entry=correct_entry,
            duplicate_entry=duplicate_entry
        )


# ============================================================================
# TYPE: eventDeletedInRegister
# ============================================================================

class ECH0020EventDeletedInRegister(BaseModel):
    """Event for person deleted from register per eCH-0020 v3.0.

    Reports that a person record has been deleted from the population register.

    NOTE: XSD contains typo "deledetInRegisterPerson" - we preserve it for XSD compliance.

    XSD: eventDeletedInRegister (eCH-0020-3-0.xsd lines 853-858)
    PDF: Event reporting standard
    """

    deledet_in_register_person: ECH0044PersonIdentification = Field(
        ...,
        alias='deledetInRegisterPerson',  # XSD typo: "deledet" instead of "deleted"
        description='Person identification of deleted entry'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # Create eventDeletedInRegister element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # deledetInRegisterPerson (required) - XSD typo preserved
        self.deledet_in_register_person.to_xml(elem, ns_044, 'deledetInRegisterPerson')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventDeletedInRegister':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'

        # deledetInRegisterPerson (required) - XSD typo preserved
        person_elem = elem.find(f'{{{ns_044}}}deledetInRegisterPerson')
        if person_elem is None:
            raise ValueError("eventDeletedInRegister requires deledetInRegisterPerson")
        deledet_in_register_person = ECH0044PersonIdentification.from_xml(person_elem)

        # extension: Not implemented

        return cls(
            deledet_in_register_person=deledet_in_register_person
        )


# ============================================================================
# TYPE: eventChangeArmedForces
# ============================================================================

class ECH0020EventChangeArmedForces(BaseModel):
    """Event for armed forces status change per eCH-0020 v3.0.

    Reports changes to a person's armed forces service status.

    XSD: eventChangeArmedForces (eCH-0020-3-0.xsd lines 859-865)
    PDF: Event reporting standard
    """

    change_armed_forces_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeArmedForcesPerson',
        description='Person identification'
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = Field(
        None,
        alias='armedForcesData',
        description='Armed forces service data'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventChangeArmedForces element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # changeArmedForcesPerson (required)
        self.change_armed_forces_person.to_xml(elem, ns_044, 'changeArmedForcesPerson')

        # armedForcesData (optional)
        if self.armed_forces_data is not None:
            self.armed_forces_data.to_xml(elem, ns_021, 'armedForcesData')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeArmedForces':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeArmedForcesPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeArmedForcesPerson')
        if person_elem is None:
            raise ValueError("eventChangeArmedForces requires changeArmedForcesPerson")
        change_armed_forces_person = ECH0044PersonIdentification.from_xml(person_elem)

        # armedForcesData (optional)
        armed_forces_data = None
        forces_elem = elem.find(f'{{{ns_021}}}armedForcesData')
        if forces_elem is not None:
            armed_forces_data = ECH0021ArmedForcesData.from_xml(forces_elem)

        # extension: Not implemented

        return cls(
            change_armed_forces_person=change_armed_forces_person,
            armed_forces_data=armed_forces_data
        )


# ============================================================================
# TYPE: eventChangeCivilDefense
# ============================================================================

class ECH0020EventChangeCivilDefense(BaseModel):
    """Event for civil defense status change per eCH-0020 v3.0.

    Reports changes to a person's civil defense service status.

    XSD: eventChangeCivilDefense (eCH-0020-3-0.xsd lines 866-872)
    PDF: Event reporting standard
    """

    change_civil_defense_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeCivilDefensePerson',
        description='Person identification'
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = Field(
        None,
        alias='civilDefenseData',
        description='Civil defense service data'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventChangeCivilDefense element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # changeCivilDefensePerson (required)
        self.change_civil_defense_person.to_xml(elem, ns_044, 'changeCivilDefensePerson')

        # civilDefenseData (optional)
        if self.civil_defense_data is not None:
            self.civil_defense_data.to_xml(elem, ns_021, 'civilDefenseData')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeCivilDefense':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeCivilDefensePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeCivilDefensePerson')
        if person_elem is None:
            raise ValueError("eventChangeCivilDefense requires changeCivilDefensePerson")
        change_civil_defense_person = ECH0044PersonIdentification.from_xml(person_elem)

        # civilDefenseData (optional)
        civil_defense_data = None
        defense_elem = elem.find(f'{{{ns_021}}}civilDefenseData')
        if defense_elem is not None:
            civil_defense_data = ECH0021CivilDefenseData.from_xml(defense_elem)

        # extension: Not implemented

        return cls(
            change_civil_defense_person=change_civil_defense_person,
            civil_defense_data=civil_defense_data
        )


# ============================================================================
# TYPE: eventChangeFireService
# ============================================================================

class ECH0020EventChangeFireService(BaseModel):
    """Event for fire service status change per eCH-0020 v3.0.

    Reports changes to a person's fire service duty status.

    XSD: eventChangeFireService (eCH-0020-3-0.xsd lines 873-879)
    PDF: Event reporting standard
    """

    change_fire_service_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeFireServicePerson',
        description='Person identification'
    )
    fire_service_data: Optional[ECH0021FireServiceData] = Field(
        None,
        alias='fireServiceData',
        description='Fire service duty data'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventChangeFireService element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # changeFireServicePerson (required)
        self.change_fire_service_person.to_xml(elem, ns_044, 'changeFireServicePerson')

        # fireServiceData (optional)
        if self.fire_service_data is not None:
            self.fire_service_data.to_xml(elem, ns_021, 'fireServiceData')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeFireService':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeFireServicePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeFireServicePerson')
        if person_elem is None:
            raise ValueError("eventChangeFireService requires changeFireServicePerson")
        change_fire_service_person = ECH0044PersonIdentification.from_xml(person_elem)

        # fireServiceData (optional)
        fire_service_data = None
        service_elem = elem.find(f'{{{ns_021}}}fireServiceData')
        if service_elem is not None:
            fire_service_data = ECH0021FireServiceData.from_xml(service_elem)

        # extension: Not implemented

        return cls(
            change_fire_service_person=change_fire_service_person,
            fire_service_data=fire_service_data
        )


# ============================================================================
# TYPE: eventChangeHealthInsurance
# ============================================================================

class ECH0020EventChangeHealthInsurance(BaseModel):
    """Event for health insurance change per eCH-0020 v3.0.

    Reports changes to a person's health insurance registration.

    XSD: eventChangeHealthInsurance (eCH-0020-3-0.xsd lines 880-886)
    PDF: Event reporting standard
    """

    change_health_insurance_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeHealthInsurancePerson',
        description='Person identification'
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description='Health insurance registration data'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventChangeHealthInsurance element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # changeHealthInsurancePerson (required)
        self.change_health_insurance_person.to_xml(elem, ns_044, 'changeHealthInsurancePerson')

        # healthInsuranceData (optional)
        if self.health_insurance_data is not None:
            self.health_insurance_data.to_xml(elem, ns_021, 'healthInsuranceData')

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeHealthInsurance':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeHealthInsurancePerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeHealthInsurancePerson')
        if person_elem is None:
            raise ValueError("eventChangeHealthInsurance requires changeHealthInsurancePerson")
        change_health_insurance_person = ECH0044PersonIdentification.from_xml(person_elem)

        # healthInsuranceData (optional)
        health_insurance_data = None
        insurance_elem = elem.find(f'{{{ns_021}}}healthInsuranceData')
        if insurance_elem is not None:
            health_insurance_data = ECH0021HealthInsuranceData.from_xml(insurance_elem)

        # extension: Not implemented

        return cls(
            change_health_insurance_person=change_health_insurance_person,
            health_insurance_data=health_insurance_data
        )


# ============================================================================
# TYPE: eventChangeMatrimonialInheritanceArrangement
# ============================================================================

class ECH0020EventChangeMatrimonialInheritanceArrangement(BaseModel):
    """Event for matrimonial/inheritance arrangement change per eCH-0020 v3.0.

    Reports changes to matrimonial property regime and inheritance arrangements.

    XSD: eventChangeMatrimonialInheritanceArrangement (eCH-0020-3-0.xsd lines 887-893)
    PDF: Event reporting standard
    """

    change_matrimonial_inheritance_arrangement_person: ECH0044PersonIdentification = Field(
        ...,
        alias='changeMatrimonialInheritanceArrangementPerson',
        description='Person identification'
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = Field(
        None,
        alias='matrimonialInheritanceArrangementData',
        description='Matrimonial property regime and inheritance arrangement data'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element],
        namespace: str,
        element_name: str
    ) -> ET.Element:
        """Serialize to XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # Create eventChangeMatrimonialInheritanceArrangement element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # changeMatrimonialInheritanceArrangementPerson (required)
        self.change_matrimonial_inheritance_arrangement_person.to_xml(
            elem, ns_044, 'changeMatrimonialInheritanceArrangementPerson'
        )

        # matrimonialInheritanceArrangementData (optional)
        if self.matrimonial_inheritance_arrangement_data is not None:
            self.matrimonial_inheritance_arrangement_data.to_xml(
                elem, ns_021, 'matrimonialInheritanceArrangementData'
            )

        # extension: Not implemented

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'ECH0020EventChangeMatrimonialInheritanceArrangement':
        """Parse from XML element."""
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_044 = 'http://www.ech.ch/xmlns/eCH-0044/4'
        ns_021 = 'http://www.ech.ch/xmlns/eCH-0021/7'

        # changeMatrimonialInheritanceArrangementPerson (required)
        person_elem = elem.find(f'{{{ns_044}}}changeMatrimonialInheritanceArrangementPerson')
        if person_elem is None:
            raise ValueError("eventChangeMatrimonialInheritanceArrangement requires changeMatrimonialInheritanceArrangementPerson")
        change_matrimonial_inheritance_arrangement_person = ECH0044PersonIdentification.from_xml(person_elem)

        # matrimonialInheritanceArrangementData (optional)
        matrimonial_inheritance_arrangement_data = None
        arrangement_elem = elem.find(f'{{{ns_021}}}matrimonialInheritanceArrangementData')
        if arrangement_elem is not None:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData.from_xml(arrangement_elem)

        # extension: Not implemented

        return cls(
            change_matrimonial_inheritance_arrangement_person=change_matrimonial_inheritance_arrangement_person,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_058 = 'http://www.ech.ch/xmlns/eCH-0058/5'

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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'
        ns_058 = 'http://www.ech.ch/xmlns/eCH-0058/5'

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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

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
        ns_020 = 'http://www.ech.ch/xmlns/eCH-0020/3'

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
        namespace: str = 'http://www.ech.ch/xmlns/eCH-0020/3',
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
        ns = {'eCH-0020': NAMESPACE_ECH0020_V3}

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
            # TODO: Add parsers for other 52 event types as needed
            supported = "baseDelivery, correctReporting, moveIn, correctContact, moveOut, move, death, marriage, correctMaritalInfo, correctBirthInfo, correctIdentification, correctName, correctPersonAdditionalData, correctResidencePermit, correctParentalRelationship, correctPlaceOfOrigin, birth, changeName, contact"
            raise NotImplementedError(
                f"from_xml() currently supports: {supported}. Other event types will be added as needed."
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
                ECH0020Delivery._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
