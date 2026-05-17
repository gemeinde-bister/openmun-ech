"""eCH-0020 v3.0 — Correction Events."""

import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

from openmun_ech.core import NS
from openmun_ech.ech0011 import (
    ECH0011MaritalDataRestrictedMaritalStatusPartner,
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011ResidencePermitData,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011MainResidence,
    ECH0011SecondaryResidence,
    ECH0011OtherResidence,
)
from openmun_ech.ech0021.v7 import (
    ECH0021JobData,
    ECH0021GuardianRelationship,
    ECH0021ParentalRelationship,
    ECH0021MaritalRelationship,
)
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044NamedPersonId,
    Sex,
)

from .info_types import (
    ECH0020BirthInfo,
    ECH0020MaritalInfo,
    ECH0020NameInfo,
    ECH0020PlaceOfOriginInfo,
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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMaritalStatusPartner'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeName'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'changeSexPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
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
        ns_020 = NS.ECH0020_V3

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'personIdentificationAfter'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling.

        Pattern: Wrapper elements in eCH-0020, content from eCH-0044.
        Example: <vn> (eCH-0020) contains text, <localPersonId> (eCH-0020) contains eCH-0044 children
        """
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'correctIdentificationPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
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
        ns_020 = NS.ECH0020_V3

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'identificationConversionPerson'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
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
        ns_020 = NS.ECH0020_V3

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectName'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctNamePerson (required)
        # Element is in eCH-0020 namespace, but content type is eCH-0044:personIdentificationType
        self.correct_name_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctNamePerson',
            wrapper_namespace=ns_020  # Element wrapper in eCH-0020 namespace
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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectNationality'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectContact'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectReligion'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectPlaceOfOrigin'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectResidencePermit'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns_020}}}{element_name}')
        else:
            elem = ET.Element(f'{{{ns_020}}}{element_name}')

        # correctResidencePermitPerson (required)
        # Element is in eCH-0020 namespace, but content type is eCH-0044:personIdentificationType
        self.correct_residence_permit_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctResidencePermitPerson',
            wrapper_namespace=ns_020  # Element wrapper in eCH-0020 namespace
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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectMaritalInfo'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectBirthInfo'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectGuardianRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectParentalRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectReporting'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectOccupation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventCorrectDeathData'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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


