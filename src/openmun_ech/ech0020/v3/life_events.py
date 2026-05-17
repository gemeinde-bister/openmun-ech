"""eCH-0020 v3.0 — Life Events."""

import xml.etree.ElementTree as ET
from typing import Optional, List, Literal
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

from openmun_ech.core import NS
from openmun_ech.ech0011 import (
    ECH0011MaritalData,
    ECH0011MaritalDataRestrictedDivorce,
    ECH0011MaritalDataRestrictedUndoMarried,
    ECH0011MaritalDataRestrictedUndoPartnership,
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011MainResidence,
    ECH0011SecondaryResidence,
    ECH0011OtherResidence,
    ECH0011SeparationData,
)
from openmun_ech.ech0021.v7 import (
    ECH0021PersonAdditionalData,
    ECH0021LockData,
    ECH0021PlaceOfOriginAddonData,
    ECH0021HealthInsuranceData,
    ECH0021ParentalRelationship,
    ECH0021MaritalRelationship,
    ECH0021NameOfParent,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .info_types import (
    ECH0020BirthInfo,
    ECH0020MaritalInfoRestrictedMarriage,
    ECH0020NameInfo,
    ECH0020PlaceOfOriginInfo,
)
from .person_types import ECH0020InfostarPerson


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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventAdoption'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChildRelationship'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
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
        ns = NS.ECH0020_V3

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventNaturalizeForeigner'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventNaturalizeSwiss'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoCitizen'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoSwiss'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeOrigin'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventBirth'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMarriage'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventPartnership'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventSeparation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoSeparation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventDivorce'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
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
            namespace=NS.ECH0044_V4,
            element_name='personIdentification',
            wrapper_namespace=namespace
        )

        # nameInfo (required)
        self.name_info.to_xml(parent=elem, namespace=namespace)

        # birthInfo (required)
        self.birth_info.to_xml(parent=elem, namespace=namespace)

        # religionData (required) - manual wrapper pattern (type doesn't support wrapper_namespace yet)
        wrapper = ET.SubElement(elem, f'{{{namespace}}}religionData')
        content = self.religion_data.to_xml(namespace=NS.ECH0011_V8)
        for child in content:
            wrapper.append(child)

        # maritalData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalData')
        content = self.marital_data.to_xml(namespace=NS.ECH0011_V8)
        for child in content:
            wrapper.append(child)

        # nationalityData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}nationalityData')
        content = self.nationality_data.to_xml(namespace=NS.ECH0011_V8)
        for child in content:
            wrapper.append(child)

        # contactData (optional) - manual wrapper pattern
        if self.contact_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            content = self.contact_data.to_xml(namespace=NS.ECH0011_V8)
            for child in content:
                wrapper.append(child)

        # personAdditionalData (optional) - manual wrapper pattern
        if self.person_additional_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            content = self.person_additional_data.to_xml(namespace=NS.ECH0021_V7)
            for child in content:
                wrapper.append(child)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace)
        elif self.residence_permit_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}residencePermitData')
            content = self.residence_permit_data.to_xml(namespace=NS.ECH0011_V8)
            for child in content:
                wrapper.append(child)

        # lockData (required) - manual wrapper pattern
        wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        content = self.lock_data.to_xml(namespace=NS.ECH0021_V7)
        for child in content:
            wrapper.append(child)

        # parentalRelationship (optional, unbounded) - manual wrapper pattern
        if self.parental_relationship:
            for parental_rel in self.parental_relationship:
                wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')
                content = parental_rel.to_xml(namespace=NS.ECH0021_V7)
                for child in content:
                    wrapper.append(child)

        # healthInsuranceData (optional) - manual wrapper pattern
        if self.health_insurance_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            content = self.health_insurance_data.to_xml(namespace=NS.ECH0021_V7)
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BirthPerson':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0044 = {'eCH-0044': NS.ECH0044_V4}
        ns_0011 = {'eCH-0011': NS.ECH0011_V8}
        ns_0021 = {'eCH-0021': NS.ECH0021_V7}

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoMarriage'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoPartnership'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventDeath'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventMissing'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoMissing'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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


