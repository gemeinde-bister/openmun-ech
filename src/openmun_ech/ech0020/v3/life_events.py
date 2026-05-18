"""eCH-0020 v3.0 — Life Events."""

import xml.etree.ElementTree as ET
from typing import Optional, List, Literal
from datetime import date
from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
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


# ============================================================================
# HELPER CLASSES (inline extension types for adoption/childRelationship)
# ============================================================================


class ECH0020AddParent(ECHModel):
    """Parent to add during adoption (inline complexType extension).

    Extends eCH-0021 parentalRelationshipType with optional nameOfParentAtEvent.
    Custom to_xml/from_xml: inline extension flattens children into parent element.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'addParent'

    parental_relationship: ECH0021ParentalRelationship = xml_field('parentalRelationship')
    name_of_parent_at_event: Optional[ECH0021NameOfParent] = xml_field(
        'nameOfParentAtEvent', default=None,
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
        **kwargs,
    ) -> ET.Element:
        ns = namespace or self.__xml_ns__
        name = element_name or self.__xml_element__
        ns_021 = NS.ECH0021_V7

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{name}')
        else:
            elem = ET.Element(f'{{{ns}}}{name}')

        self.parental_relationship.to_xml(
            parent=elem, namespace=ns_021, element_name='parentalRelationship',
        )
        if self.name_of_parent_at_event:
            self.name_of_parent_at_event.to_xml(
                parent=elem, namespace=ns_021, element_name='nameOfParentAtEvent',
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, **kwargs) -> 'ECH0020AddParent':
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7

        # Production XML may use either eCH-0020 or eCH-0021 namespace for child elements
        rel_elem = elem.find(f'{{{ns_020}}}parentalRelationship')
        if rel_elem is None:
            rel_elem = elem.find(f'{{{ns_021}}}parentalRelationship')
        if rel_elem is None:
            raise ValueError("addParent requires parentalRelationship")
        parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

        name_elem = elem.find(f'{{{ns_020}}}nameOfParentAtEvent')
        if name_elem is None:
            name_elem = elem.find(f'{{{ns_021}}}nameOfParentAtEvent')
        name_of_parent_at_event = (
            ECH0021NameOfParent.from_xml(name_elem) if name_elem is not None else None
        )

        return cls(
            parental_relationship=parental_relationship,
            name_of_parent_at_event=name_of_parent_at_event,
        )


class ECH0020RemoveParent(ECHModel):
    """Parent to remove during adoption (inline complexType extension).

    Same structure as ECH0020AddParent.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'removeParent'

    parental_relationship: ECH0021ParentalRelationship = xml_field('parentalRelationship')
    name_of_parent_at_event: Optional[ECH0021NameOfParent] = xml_field(
        'nameOfParentAtEvent', default=None,
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
        **kwargs,
    ) -> ET.Element:
        ns = namespace or self.__xml_ns__
        name = element_name or self.__xml_element__
        ns_021 = NS.ECH0021_V7

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{name}')
        else:
            elem = ET.Element(f'{{{ns}}}{name}')

        self.parental_relationship.to_xml(
            parent=elem, namespace=ns_021, element_name='parentalRelationship',
        )
        if self.name_of_parent_at_event:
            self.name_of_parent_at_event.to_xml(
                parent=elem, namespace=ns_021, element_name='nameOfParentAtEvent',
            )

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, **kwargs) -> 'ECH0020RemoveParent':
        ns_020 = NS.ECH0020_V3
        ns_021 = NS.ECH0021_V7

        rel_elem = elem.find(f'{{{ns_020}}}parentalRelationship')
        if rel_elem is None:
            rel_elem = elem.find(f'{{{ns_021}}}parentalRelationship')
        if rel_elem is None:
            raise ValueError("removeParent requires parentalRelationship")
        parental_relationship = ECH0021ParentalRelationship.from_xml(rel_elem)

        name_elem = elem.find(f'{{{ns_020}}}nameOfParentAtEvent')
        if name_elem is None:
            name_elem = elem.find(f'{{{ns_021}}}nameOfParentAtEvent')
        name_of_parent_at_event = (
            ECH0021NameOfParent.from_xml(name_elem) if name_elem is not None else None
        )

        return cls(
            parental_relationship=parental_relationship,
            name_of_parent_at_event=name_of_parent_at_event,
        )


# ============================================================================
# SWISS NATIONALITY (hardcoded XSD restriction)
# ============================================================================


class ECH0020SwissNationality(ECHModel):
    """Swiss nationality with hardcoded values per XSD restriction.

    nationalityStatus=2, countryId=8100, countryIdISO2=CH.
    Custom to_xml/from_xml: nested <nationality><nationalityStatus>...<country>...</country></nationality>.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'nationality'

    nationality_status: Literal["2"] = xml_field('nationalityStatus', default="2")
    country_id: Literal[8100] = xml_field('countryId', default=8100)
    country_id_iso2: Literal["CH"] = xml_field('countryIdISO2', default="CH")

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
        **kwargs,
    ) -> ET.Element:
        ns = namespace or self.__xml_ns__
        name = element_name or self.__xml_element__

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{ns}}}{name}')
        else:
            elem = ET.Element(f'{{{ns}}}{name}')

        ET.SubElement(elem, f'{{{ns}}}nationalityStatus').text = self.nationality_status
        country_elem = ET.SubElement(elem, f'{{{ns}}}country')
        ET.SubElement(country_elem, f'{{{ns}}}countryId').text = str(self.country_id)
        ET.SubElement(country_elem, f'{{{ns}}}countryIdISO2').text = self.country_id_iso2

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, **kwargs) -> 'ECH0020SwissNationality':
        ns = NS.ECH0020_V3

        status_elem = elem.find(f'{{{ns}}}nationalityStatus')
        if status_elem is None or not status_elem.text:
            raise ValueError("swissNationalityType requires nationalityStatus")
        if status_elem.text != "2":
            raise ValueError(
                f'swissNationalityType requires nationalityStatus="2", got "{status_elem.text}"'
            )

        country_elem = elem.find(f'{{{ns}}}country')
        if country_elem is None:
            raise ValueError("swissNationalityType requires country element")

        id_elem = country_elem.find(f'{{{ns}}}countryId')
        if id_elem is None or not id_elem.text:
            raise ValueError("swissNationalityType requires country/countryId")
        country_id = int(id_elem.text)
        if country_id != 8100:
            raise ValueError(f'swissNationalityType requires countryId=8100, got {country_id}')

        iso2_elem = country_elem.find(f'{{{ns}}}countryIdISO2')
        if iso2_elem is None or not iso2_elem.text:
            raise ValueError("swissNationalityType requires country/countryIdISO2")
        if iso2_elem.text != "CH":
            raise ValueError(
                f'swissNationalityType requires countryIdISO2="CH", got "{iso2_elem.text}"'
            )

        return cls()


# ============================================================================
# ADOPTION / CHILD RELATIONSHIP EVENTS
# ============================================================================


class ECH0020EventAdoption(ECHModel):
    """Adoption event — changes in parental relationships.

    AddParent/RemoveParent have custom to_xml/from_xml handling inline extension,
    so this class can be fully declarative (ECHModel calls their to_xml/from_xml).
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventAdoption'

    adoption_person: ECH0020InfostarPerson = xml_field('adoptionPerson')
    add_parent: Optional[List[ECH0020AddParent]] = xml_field(
        'addParent', default=None, is_list=True,
    )
    remove_parent: Optional[List[ECH0020RemoveParent]] = xml_field(
        'removeParent', default=None, is_list=True,
    )
    adoption_valid_from: Optional[date] = xml_field('adoptionValidFrom', default=None)


class ECH0020EventChildRelationship(ECHModel):
    """Child relationship event — register or correct parent-child relationships."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChildRelationship'

    child_relationship_person: ECH0020InfostarPerson = xml_field('childRelationshipPerson')
    add_parent: Optional[List[ECH0020AddParent]] = xml_field(
        'addParent', default=None, is_list=True,
    )
    remove_parent: Optional[List[ECH0020RemoveParent]] = xml_field(
        'removeParent', default=None, is_list=True,
    )
    child_relationship_valid_from: Optional[date] = xml_field(
        'childRelationshipValidFrom', default=None,
    )


# ============================================================================
# NATURALIZATION EVENTS
# ============================================================================


class ECH0020EventNaturalizeForeigner(ECHModel):
    """Naturalization event — foreigner acquires Swiss citizenship."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventNaturalizeForeigner'

    naturalize_foreigner_person: ECH0044PersonIdentification = xml_field(
        'naturalizeForeignerPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    place_of_origin_info: List[ECH0020PlaceOfOriginInfo] = xml_field(
        'placeOfOriginInfo', is_list=True,
    )
    nationality: ECH0020SwissNationality = xml_field('nationality')


class ECH0020EventNaturalizeSwiss(ECHModel):
    """Naturalization event — Swiss person acquires additional place of origin."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventNaturalizeSwiss'

    naturalize_swiss_person: ECH0044PersonIdentification = xml_field(
        'naturalizeSwissPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    place_of_origin_info: List[ECH0020PlaceOfOriginInfo] = xml_field(
        'placeOfOriginInfo', is_list=True,
    )


# ============================================================================
# UNDO CITIZENSHIP / SWISS
# ============================================================================


class ECH0020EventUndoCitizen(ECHModel):
    """Undo citizenship — remove a place of origin."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoCitizen'

    undo_citizen_person: ECH0044PersonIdentification = xml_field(
        'undoCitizenPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    place_of_origin: ECH0011PlaceOfOrigin = xml_field(
        'placeOfOrigin', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    place_of_origin_addon: Optional[ECH0021PlaceOfOriginAddonData] = xml_field(
        'placeOfOriginAddon', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventUndoSwiss(ECHModel):
    """Undo Swiss nationality — person loses ALL Swiss citizenship."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoSwiss'

    undo_swiss_person: ECH0044PersonIdentification = xml_field(
        'undoSwissPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = xml_field(
        'residencePermitData', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )
    undo_swiss_valid_from: Optional[date] = xml_field(
        'undoSwissValidFrom', default=None,
    )


# ============================================================================
# CHANGE ORIGIN
# ============================================================================


class ECH0020EventChangeOrigin(ECHModel):
    """Change/update place of origin event."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeOrigin'

    change_origin_person: ECH0044PersonIdentification = xml_field(
        'changeOriginPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    origin_info: List[ECH0020PlaceOfOriginInfo] = xml_field(
        'originInfo', is_list=True,
    )


# ============================================================================
# BIRTH PERSON TYPE
# ============================================================================


class ECH0020BirthPerson(ECHModel):
    """Person data structure for birth events.

    XSD CHOICE: placeOfOriginInfo (Swiss) XOR residencePermitData (foreign).
    Uses wrapper pattern for cross-namespace fields.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'birthPerson'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')
    birth_info: ECH0020BirthInfo = xml_field('birthInfo')
    religion_data: ECH0011ReligionData = xml_field(
        'religionData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    marital_data: ECH0011MaritalData = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    contact_data: Optional[ECH0011ContactData] = xml_field(
        'contactData', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = xml_field(
        'personAdditionalData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )
    # XSD CHOICE (validated below)
    place_of_origin_info: Optional[List[ECH0020PlaceOfOriginInfo]] = xml_field(
        'placeOfOriginInfo', default=None, is_list=True,
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = xml_field(
        'residencePermitData', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )
    lock_data: ECH0021LockData = xml_field(
        'lockData', wrapper=True, child_ns=NS.ECH0021_V7,
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = xml_field(
        'parentalRelationship', wrapper=True, child_ns=NS.ECH0021_V7,
        default=None, is_list=True,
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = xml_field(
        'healthInsuranceData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BirthPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData."""
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


# ============================================================================
# BIRTH EVENT
# ============================================================================


class ECH0020EventBirth(ECHModel):
    """Birth event — register a new person.

    XSD CHOICE (optional): at most ONE of hasMainResidence/hasSecondaryResidence/hasOtherResidence.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventBirth'

    birth_person: ECH0020BirthPerson = xml_field('birthPerson')
    has_main_residence: Optional[ECH0011MainResidence] = xml_field(
        'hasMainResidence', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )
    has_secondary_residence: Optional[ECH0011SecondaryResidence] = xml_field(
        'hasSecondaryResidence', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )
    has_other_residence: Optional[ECH0011OtherResidence] = xml_field(
        'hasOtherResidence', wrapper=True, child_ns=NS.ECH0011_V8, default=None,
    )

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventBirth':
        """Validate XSD CHOICE: at most ONE residence type."""
        residences = [
            self.has_main_residence,
            self.has_secondary_residence,
            self.has_other_residence,
        ]
        set_count = sum(1 for r in residences if r is not None)

        if set_count > 1:
            raise ValueError(
                f"eventBirth allows at most ONE residence type (main/secondary/other), "
                f"but {set_count} are set"
            )

        return self


# ============================================================================
# MARRIAGE / PARTNERSHIP
# ============================================================================


class ECH0020EventMarriage(ECHModel):
    """Marriage event — register a marriage.

    Uses wrapper pattern for marriagePerson (eCH-0044) and maritalRelationship (eCH-0021).
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMarriage'

    marriage_person: ECH0044PersonIdentification = xml_field(
        'marriagePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_info: ECH0020MaritalInfoRestrictedMarriage = xml_field('maritalInfo')
    marital_relationship: Optional[ECH0021MaritalRelationship] = xml_field(
        'maritalRelationship', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventPartnership(ECHModel):
    """Registered partnership event.

    Uses wrapper pattern for cross-namespace fields (eCH-0044, eCH-0021).
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventPartnership'

    partnership_person: ECH0044PersonIdentification = xml_field(
        'partnershipPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_info: ECH0020MaritalInfoRestrictedMarriage = xml_field('maritalInfo')
    partnership_relationship: Optional[ECH0021MaritalRelationship] = xml_field(
        'partnershipRelationship', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


# ============================================================================
# SEPARATION / UNDO SEPARATION
# ============================================================================


class ECH0020EventSeparation(ECHModel):
    """Separation event — register legal separation."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventSeparation'

    separation_person: ECH0044PersonIdentification = xml_field(
        'separationPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    separation_data: ECH0011SeparationData = xml_field(
        'separationData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventUndoSeparation(ECHModel):
    """Undo separation event — couple reconciles."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoSeparation'

    undo_separation_person: ECH0044PersonIdentification = xml_field(
        'undoSeparationPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    separation_valid_till: Optional[date] = xml_field(
        'separationValidTill', default=None,
    )


# ============================================================================
# DIVORCE
# ============================================================================


class ECH0020EventDivorce(ECHModel):
    """Divorce event — dissolution of marriage or partnership."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventDivorce'

    divorce_person: ECH0044PersonIdentification = xml_field(
        'divorcePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_data: ECH0011MaritalDataRestrictedDivorce = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


# ============================================================================
# UNDO MARRIAGE / PARTNERSHIP
# ============================================================================


class ECH0020EventUndoMarriage(ECHModel):
    """Undo marriage event — nullify/annul marriage."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoMarriage'

    undo_marriage_person: ECH0044PersonIdentification = xml_field(
        'undoMarriagePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_data: ECH0011MaritalDataRestrictedUndoMarried = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventUndoPartnership(ECHModel):
    """Undo partnership event — nullify/annul registered partnership."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoPartnership'

    undo_partnership_person: ECH0044PersonIdentification = xml_field(
        'undoPartnershipPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_data: ECH0011MaritalDataRestrictedUndoPartnership = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


# ============================================================================
# DEATH / MISSING
# ============================================================================


class ECH0020EventDeath(ECHModel):
    """Death event — register person death.

    Uses wrapper pattern for both deathPerson and deathData.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventDeath'

    death_person: ECH0044PersonIdentification = xml_field(
        'deathPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    death_data: ECH0011DeathData = xml_field(
        'deathData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventMissing(ECHModel):
    """Missing person event — register person as missing (presumed dead).

    Uses wrapper pattern for cross-namespace fields (eCH-0044, eCH-0011).
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMissing'

    missing_person: ECH0044PersonIdentification = xml_field(
        'missingPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    death_data: ECH0011DeathData = xml_field(
        'deathData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventUndoMissing(ECHModel):
    """Undo missing person event — person found alive."""

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoMissing'

    undo_missing_person: ECH0044PersonIdentification = xml_field(
        'undoMissingPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    undo_missing_valid_from: Optional[date] = xml_field(
        'undoMissingValidFrom', default=None,
    )
