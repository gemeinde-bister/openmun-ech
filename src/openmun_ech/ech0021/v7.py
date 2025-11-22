"""eCH-0021 Person Additional Data v7.0.

Standard: eCH-0021 v7.0 (Person additional data)
Version stability: Required for eCH-0020 v3.0 compatibility

This component provides additional person data structures including:
- Birth addon data (parent names)
- Marital data addon (place of marriage)
- Person additional data (salutation, language)
- Place of origin addon (naturalization dates)
- Lock data (data/paper/address locks)
- Relationships (marital, parental, guardian)
- Job data
- Military/civil service data

ARCHITECTURE: Pure Pydantic Model (Layer 1)
- NO database coupling
- NO from_db_fields() method
- Database mapping logic belongs in: openmun/mappers/
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Union
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# Import components we depend on
from openmun_ech.ech0044 import (
    ECH0044PersonIdentification,
    ECH0044PersonIdentificationLight,
)
from openmun_ech.ech0010 import (
    ECH0010MailAddress,
    ECH0010AddressInformation,
    ECH0010OrganisationMailAddressInfo,
    ECH0010OrganisationMailAddress,
)
from openmun_ech.ech0011.v8 import (
    ECH0011GeneralPlace,
    ECH0011PartnerIdOrganisation,
)
from openmun_ech.ech0011.enums import LanguageCode

# Import enums from this package
from .enums import (
    MrMrs,
    TypeOfRelationship,
    CareType,
    KindOfEmployment,
    YesNo,
    UIDOrganisationIdCategory,
)


# ============================================================================
# Person Additional Data
# ============================================================================

class ECH0021PersonAdditionalData(BaseModel):
    """eCH-0021 Person additional data.

    Contains salutation, title, and language of correspondence.

    XML Schema: eCH-0021 personAdditionalData
    """

    mr_mrs: Optional[MrMrs] = Field(
        None,
        description="Salutation: 1=Mrs/Frau, 2=Mr/Herr (eCH-0010 mrMrsType)"
    )
    title: Optional[str] = Field(
        None,
        max_length=50,
        description="Title (Dr., Prof., etc.) (eCH-0010 titleType)"
    )
    language_of_correspondance: Optional[LanguageCode] = Field(
        None,
        description="Language code: de, fr, it, rm, en (eCH-0011 languageType)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'personAdditionalData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.mr_mrs:
            mr_mrs_elem = ET.SubElement(elem, f'{{{namespace}}}mrMrs')
            mr_mrs_elem.text = self.mr_mrs.value

        if self.title:
            title_elem = ET.SubElement(elem, f'{{{namespace}}}title')
            title_elem.text = self.title

        if self.language_of_correspondance:
            lang_elem = ET.SubElement(elem, f'{{{namespace}}}languageOfCorrespondance')
            lang_elem.text = self.language_of_correspondance.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021PersonAdditionalData':
        """Import from eCH-0021 v7 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        mr_mrs_elem = element.find('eCH-0021:mrMrs', ns)
        title_elem = element.find('eCH-0021:title', ns)
        lang_elem = element.find('eCH-0021:languageOfCorrespondance', ns)

        return cls(
            mr_mrs=MrMrs(mr_mrs_elem.text) if mr_mrs_elem is not None else None,
            title=title_elem.text if title_elem is not None else None,
            language_of_correspondance=lang_elem.text if lang_elem is not None else None
        )


# ============================================================================
# Lock Data
# ============================================================================

class ECH0021LockData(BaseModel):
    """eCH-0021 v7 Lock data.

    Contains flags and validity dates for data and paper locks.
    NOTE: addressLock was added in v8 (not in v7).

    XML Schema: eCH-0021-7-0 lockDataType
    """

    data_lock: YesNo = Field(..., description="Data lock (required: yes/no)")
    data_lock_valid_from: Optional[date] = None
    data_lock_valid_till: Optional[date] = None

    paper_lock: YesNo = Field(..., description="Paper lock (required: yes/no)")
    paper_lock_valid_from: Optional[date] = None
    paper_lock_valid_till: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'lockData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Data lock (required)
        data_lock = ET.SubElement(elem, f'{{{namespace}}}dataLock')
        data_lock.text = self.data_lock.value

        if self.data_lock_valid_from:
            data_from = ET.SubElement(elem, f'{{{namespace}}}dataLockValidFrom')
            data_from.text = self.data_lock_valid_from.isoformat()

        if self.data_lock_valid_till:
            data_till = ET.SubElement(elem, f'{{{namespace}}}dataLockValidTill')
            data_till.text = self.data_lock_valid_till.isoformat()

        # Paper lock (required)
        paper_lock = ET.SubElement(elem, f'{{{namespace}}}paperLock')
        paper_lock.text = self.paper_lock.value

        if self.paper_lock_valid_from:
            paper_from = ET.SubElement(elem, f'{{{namespace}}}paperLockValidFrom')
            paper_from.text = self.paper_lock_valid_from.isoformat()

        if self.paper_lock_valid_till:
            paper_till = ET.SubElement(elem, f'{{{namespace}}}paperLockValidTill')
            paper_till.text = self.paper_lock_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021LockData':
        """Import from eCH-0021 v7 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        def get_text(path: str) -> Optional[str]:
            elem = element.find(path, ns)
            return elem.text if elem is not None else None

        def get_date(path: str) -> Optional[date]:
            text = get_text(path)
            return date.fromisoformat(text) if text else None

        return cls(
            data_lock=YesNo(get_text('eCH-0021:dataLock')),
            data_lock_valid_from=get_date('eCH-0021:dataLockValidFrom'),
            data_lock_valid_till=get_date('eCH-0021:dataLockValidTill'),
            paper_lock=YesNo(get_text('eCH-0021:paperLock')),
            paper_lock_valid_from=get_date('eCH-0021:paperLockValidFrom'),
            paper_lock_valid_till=get_date('eCH-0021:paperLockValidTill')
        )


# ============================================================================
# Place of Origin Addon
# ============================================================================

class ECH0021PlaceOfOriginAddonData(BaseModel):
    """eCH-0021 Place of origin addon data.

    Contains naturalization and expatriation dates.

    XML Schema: eCH-0021 placeOfOriginAddonDataType
    """

    naturalization_date: Optional[date] = Field(
        None,
        description="Date of naturalization"
    )
    expatriation_date: Optional[date] = Field(
        None,
        description="Date of expatriation"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'placeOfOriginAddonData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.naturalization_date:
            nat_elem = ET.SubElement(elem, f'{{{namespace}}}naturalizationDate')
            nat_elem.text = self.naturalization_date.isoformat()

        if self.expatriation_date:
            exp_elem = ET.SubElement(elem, f'{{{namespace}}}expatriationDate')
            exp_elem.text = self.expatriation_date.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021PlaceOfOriginAddonData':
        """Import from eCH-0021 v7 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        nat_elem = element.find('eCH-0021:naturalizationDate', ns)
        exp_elem = element.find('eCH-0021:expatriationDate', ns)

        return cls(
            naturalization_date=date.fromisoformat(nat_elem.text) if nat_elem is not None else None,
            expatriation_date=date.fromisoformat(exp_elem.text) if exp_elem is not None else None
        )


# ============================================================================
# Marital Data Addon
# ============================================================================

class ECH0021MaritalDataAddon(BaseModel):
    """eCH-0021 Marital data addon.

    Contains place of marriage information.

    XML Schema: eCH-0021 maritalDataAddonType
    """

    place_of_marriage: Optional[ECH0011GeneralPlace] = Field(
        None,
        description="Place where marriage occurred (Swiss municipality or foreign country)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'maritalDataAddon') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.place_of_marriage:
            # Create wrapper in eCH-0021 namespace
            place_wrapper = ET.SubElement(elem, f'{{{namespace}}}placeOfMarriage')
            # Generate eCH-0011 content
            place_content = self.place_of_marriage.to_xml(namespace='http://www.ech.ch/xmlns/eCH-0011/8')
            # Move children to wrapper
            for child in place_content:
                place_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021MaritalDataAddon':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # Look for wrapper in eCH-0021 namespace
        place_elem = element.find('eCH-0021:placeOfMarriage', ns)

        return cls(
            place_of_marriage=ECH0011GeneralPlace.from_xml(place_elem) if place_elem is not None else None
        )


# ============================================================================
# Birth Addon Data
# ============================================================================

class ECH0021NameOfParent(BaseModel):
    """eCH-0021 Name of parent.

    Contains parent name information with choice of:
    - Both first and official name
    - First name only
    - Official name only

    XML Schema: eCH-0021 nameOfParentType
    """

    # Choice: full name OR firstName only OR officialName only
    first_name: Optional[str] = Field(None, max_length=100)
    official_name: Optional[str] = Field(None, max_length=100)
    first_name_only: Optional[str] = Field(None, max_length=100)
    official_name_only: Optional[str] = Field(None, max_length=100)

    type_of_relationship: Optional[TypeOfRelationship] = Field(
        None,
        description="Type of relationship (3=mother, 4=father)"
    )
    official_proof_of_name_of_parents_yes_no: Optional[bool] = Field(
        None,
        description="Official proof of parent names exists"
    )

    @field_validator('type_of_relationship')
    @classmethod
    def validate_parent_relationship(cls, v):
        """Validate that relationship type is father or mother."""
        if v is not None and v not in [TypeOfRelationship.MOTHER, TypeOfRelationship.FATHER]:
            raise ValueError(f"Parent relationship must be mother (3) or father (4), got {v}")
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'nameOfParent') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # XSD CHOICE: exactly one of three options:
        # - firstName + officialName (both names known)
        # - firstNameOnly (only first name known)
        # - officialNameOnly (only official name known)
        if self.first_name and self.official_name:
            fn_elem = ET.SubElement(elem, f'{{{namespace}}}firstName')
            fn_elem.text = self.first_name
            on_elem = ET.SubElement(elem, f'{{{namespace}}}officialName')
            on_elem.text = self.official_name
        elif self.first_name_only:
            fno_elem = ET.SubElement(elem, f'{{{namespace}}}firstNameOnly')
            fno_elem.text = self.first_name_only
        elif self.official_name_only:
            ono_elem = ET.SubElement(elem, f'{{{namespace}}}officialNameOnly')
            ono_elem.text = self.official_name_only

        # Only export typeOfRelationship if using generic element_name
        # (nameOfFather/nameOfMother already encode the relationship type)
        if self.type_of_relationship and element_name not in ('nameOfFather', 'nameOfMother'):
            rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
            rel_elem.text = self.type_of_relationship.value

        if self.official_proof_of_name_of_parents_yes_no is not None:
            proof_elem = ET.SubElement(elem, f'{{{namespace}}}officialProofOfNameOfParentsYesNo')
            proof_elem.text = 'true' if self.official_proof_of_name_of_parents_yes_no else 'false'

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021NameOfParent':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        fn_elem = element.find('eCH-0021:firstName', ns)
        on_elem = element.find('eCH-0021:officialName', ns)
        fno_elem = element.find('eCH-0021:firstNameOnly', ns)
        ono_elem = element.find('eCH-0021:officialNameOnly', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        proof_elem = element.find('eCH-0021:officialProofOfNameOfParentsYesNo', ns)

        # Infer type_of_relationship from element name if not explicitly provided
        type_of_relationship = None
        if rel_elem is not None:
            type_of_relationship = TypeOfRelationship(rel_elem.text)
        else:
            # Check element name to infer relationship type
            element_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            if element_name == 'nameOfFather':
                type_of_relationship = TypeOfRelationship.FATHER
            elif element_name == 'nameOfMother':
                type_of_relationship = TypeOfRelationship.MOTHER

        return cls(
            first_name=fn_elem.text if fn_elem is not None else None,
            official_name=on_elem.text if on_elem is not None else None,
            first_name_only=fno_elem.text if fno_elem is not None else None,
            official_name_only=ono_elem.text if ono_elem is not None else None,
            type_of_relationship=type_of_relationship,
            official_proof_of_name_of_parents_yes_no=(proof_elem.text == 'true') if proof_elem is not None else None
        )


class ECH0021BirthAddonData(BaseModel):
    """eCH-0021 Birth addon data.

    Contains names of parents (up to 2: father and mother).

    XML Schema: eCH-0021 birthAddonDataType
    """

    name_of_parent: List[ECH0021NameOfParent] = Field(
        default_factory=list,
        max_length=2,
        description="Names of parents (max 2: father and mother)"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'birthAddonData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        for parent_name in self.name_of_parent:
            # Determine element name based on type_of_relationship
            if parent_name.type_of_relationship and parent_name.type_of_relationship.value == '3':
                elem_name = 'nameOfFather'
            elif parent_name.type_of_relationship and parent_name.type_of_relationship.value == '4':
                elem_name = 'nameOfMother'
            else:
                elem_name = 'nameOfParent'  # Fallback to generic
            parent_name.to_xml(parent=elem, namespace=namespace, element_name=elem_name)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021BirthAddonData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # Look for nameOfFather, nameOfMother, AND generic nameOfParent
        father_elems = element.findall('eCH-0021:nameOfFather', ns)
        mother_elems = element.findall('eCH-0021:nameOfMother', ns)
        parent_elems = element.findall('eCH-0021:nameOfParent', ns)

        all_parents = father_elems + mother_elems + parent_elems

        return cls(
            name_of_parent=[ECH0021NameOfParent.from_xml(elem) for elem in all_parents]
        )


# ============================================================================
# Job Data
# ============================================================================

class ECH0021UIDStructure(BaseModel):
    """eCH-0021 UID structure (Swiss business identifier).

    XML Schema: eCH-0021 uidStructureType
    """

    uid_organisation_id_categorie: UIDOrganisationIdCategory = Field(
        ...,
        description="UID category (CHE=enterprise, ADM=administration)"
    )
    uid_organisation_id: int = Field(
        ...,
        ge=1,
        le=999999999,
        description="9-digit UID organization ID"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'UID') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        cat_elem = ET.SubElement(elem, f'{{{namespace}}}uidOrganisationIdCategorie')
        cat_elem.text = self.uid_organisation_id_categorie.value  # Enum value: "CHE" or "ADM"

        id_elem = ET.SubElement(elem, f'{{{namespace}}}uidOrganisationId')
        id_elem.text = f"{self.uid_organisation_id:09d}"

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021UIDStructure':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        cat_elem = element.find('eCH-0021:uidOrganisationIdCategorie', ns)
        id_elem = element.find('eCH-0021:uidOrganisationId', ns)

        return cls(
            uid_organisation_id_categorie=cat_elem.text,
            uid_organisation_id=int(id_elem.text)
        )


class ECH0021OccupationData(BaseModel):
    """eCH-0021 Occupation data.

    XML Schema: eCH-0021 occupationDataType
    """

    uid: Optional[ECH0021UIDStructure] = None
    employer: Optional[str] = Field(None, max_length=100)
    place_of_work: Optional[ECH0010AddressInformation] = None
    place_of_employer: Optional[ECH0010AddressInformation] = None
    occupation_valid_from: Optional[date] = None
    occupation_valid_till: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'occupationData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.uid:
            self.uid.to_xml(parent=elem, namespace=namespace)

        if self.employer:
            emp_elem = ET.SubElement(elem, f'{{{namespace}}}employer')
            emp_elem.text = self.employer

        if self.place_of_work:
            # Wrapper element placeOfWork in eCH-0021/7 namespace, content in eCH-0010/5
            self.place_of_work.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0010/5',
                element_name='placeOfWork',
                wrapper_namespace=namespace
            )

        if self.place_of_employer:
            # Wrapper element placeOfEmployer in eCH-0021/7 namespace, content in eCH-0010/5
            self.place_of_employer.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0010/5',
                element_name='placeOfEmployer',
                wrapper_namespace=namespace
            )

        if self.occupation_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}occupationValidFrom')
            from_elem.text = self.occupation_valid_from.isoformat()

        if self.occupation_valid_till:
            till_elem = ET.SubElement(elem, f'{{{namespace}}}occupationValidTill')
            till_elem.text = self.occupation_valid_till.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021OccupationData':
        """Import from eCH-0021 XML."""
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        uid_elem = element.find('eCH-0021:UID', ns_0021)
        emp_elem = element.find('eCH-0021:employer', ns_0021)

        # placeOfWork and placeOfEmployer are wrappers in eCH-0021/7 namespace
        # containing eCH-0010/5 address data
        pow_wrapper = element.find('eCH-0021:placeOfWork', ns_0021)
        poe_wrapper = element.find('eCH-0021:placeOfEmployer', ns_0021)

        from_elem = element.find('eCH-0021:occupationValidFrom', ns_0021)
        till_elem = element.find('eCH-0021:occupationValidTill', ns_0021)

        return cls(
            uid=ECH0021UIDStructure.from_xml(uid_elem) if uid_elem is not None else None,
            employer=emp_elem.text if emp_elem is not None else None,
            place_of_work=ECH0010AddressInformation.from_xml(pow_wrapper) if pow_wrapper is not None else None,
            place_of_employer=ECH0010AddressInformation.from_xml(poe_wrapper) if poe_wrapper is not None else None,
            occupation_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None,
            occupation_valid_till=date.fromisoformat(till_elem.text) if till_elem is not None else None
        )


class ECH0021JobData(BaseModel):
    """eCH-0021 Job data.

    XML Schema: eCH-0021 jobDataType
    """

    kind_of_employment: KindOfEmployment = Field(
        ...,
        description="Kind of employment (employed, self-employed, unemployed, etc.)"
    )
    job_title: Optional[str] = Field(None, max_length=100)
    occupation_data: List[ECH0021OccupationData] = Field(default_factory=list)

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'jobData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        kind_elem = ET.SubElement(elem, f'{{{namespace}}}kindOfEmployment')
        kind_elem.text = self.kind_of_employment.value

        if self.job_title:
            title_elem = ET.SubElement(elem, f'{{{namespace}}}jobTitle')
            title_elem.text = self.job_title

        for occ in self.occupation_data:
            occ.to_xml(parent=elem, namespace=namespace)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021JobData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        kind_elem = element.find('eCH-0021:kindOfEmployment', ns)
        title_elem = element.find('eCH-0021:jobTitle', ns)
        occ_elems = element.findall('eCH-0021:occupationData', ns)

        return cls(
            kind_of_employment=KindOfEmployment(kind_elem.text),
            job_title=title_elem.text if title_elem is not None else None,
            occupation_data=[ECH0021OccupationData.from_xml(elem) for elem in occ_elems]
        )


# ============================================================================
# Relationships
# ============================================================================

class ECH0021Partner(BaseModel):
    """eCH-0021 Partner information.

    Contains person identification (full or light version) and optional address.
    Used in marital and parental relationships.

    XML Schema: Inline complexType in maritalRelationshipType and parentalRelationshipType
    """

    person_identification: Union[ECH0044PersonIdentification, ECH0044PersonIdentificationLight] = Field(
        ...,
        description="Person identification of partner (full or light version)"
    )

    address: Optional[ECH0010MailAddress] = Field(
        None,
        description="Partner's mail address"
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'partner') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # Person identification (full or light)
        if isinstance(self.person_identification, ECH0044PersonIdentificationLight):
            self.person_identification.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0044/4',
                element_name='personIdentificationPartner',
                wrapper_namespace=namespace
            )
        else:
            self.person_identification.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0044/4',
                element_name='personIdentification',
                wrapper_namespace=namespace
            )

        # Optional address
        if self.address:
            self.address.to_xml(
                parent=elem,
                namespace='http://www.ech.ch/xmlns/eCH-0010/5',
                element_name='address',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021Partner':
        """Import from eCH-0021 XML."""
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # Try full person identification first (wrapper in eCH-0021, content in eCH-0044)
        pers_elem = element.find('eCH-0021:personIdentification', ns_0021)
        if pers_elem is not None:
            person_id = ECH0044PersonIdentification.from_xml(pers_elem)
        else:
            # Try light person identification (wrapper in eCH-0021, content in eCH-0044)
            pers_light_elem = element.find('eCH-0021:personIdentificationPartner', ns_0021)
            if pers_light_elem is not None:
                person_id = ECH0044PersonIdentificationLight.from_xml(pers_light_elem)
            else:
                raise ValueError("Missing required field: personIdentification or personIdentificationPartner")

        # Address (wrapper in eCH-0021, content in eCH-0010)
        addr_elem = element.find('eCH-0021:address', ns_0021)

        return cls(
            person_identification=person_id,
            address=ECH0010MailAddress.from_xml(addr_elem) if addr_elem is not None else None
        )


class ECH0021MaritalRelationship(BaseModel):
    """eCH-0021 Marital relationship.

    Contains partner information and type of relationship (married/partnership).

    XML Schema: eCH-0021 maritalRelationshipType
    """

    partner: ECH0021Partner = Field(..., description="Partner information")
    type_of_relationship: TypeOfRelationship = Field(
        ...,
        description="Type of marital relationship (1=spouse, 2=registered partner)"
    )

    @field_validator('type_of_relationship')
    @classmethod
    def validate_marital_relationship_type(cls, v: TypeOfRelationship) -> TypeOfRelationship:
        """Validate that relationship type is married or registered partnership."""
        if v not in (TypeOfRelationship.SPOUSE, TypeOfRelationship.REGISTERED_PARTNER):
            raise ValueError(
                f"Marital relationship must be SPOUSE (1) or REGISTERED_PARTNER (2), got: {v}"
            )
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'maritalRelationship',
               wrapper_namespace: Optional[str] = None) -> ET.Element:
        """Export to eCH-0021 v7 XML.

        Args:
            parent: Parent element to attach to
            namespace: XML namespace for content elements
            element_name: Name of wrapper element (default: 'maritalRelationship')
            wrapper_namespace: Namespace for wrapper element (defaults to namespace if not specified)
        """
        # Use wrapper_namespace for wrapper element, namespace for content
        wrapper_ns = wrapper_namespace if wrapper_namespace is not None else namespace

        if parent is not None:
            elem = ET.SubElement(parent, f'{{{wrapper_ns}}}{element_name}')
        else:
            elem = ET.Element(f'{{{wrapper_ns}}}{element_name}')

        self.partner.to_xml(parent=elem, namespace=namespace)

        rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
        rel_elem.text = self.type_of_relationship.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021MaritalRelationship':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        partner_elem = element.find('eCH-0021:partner', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)

        return cls(
            partner=ECH0021Partner.from_xml(partner_elem),
            type_of_relationship=TypeOfRelationship(rel_elem.text)
        )


class ECH0021ParentalRelationship(BaseModel):
    """eCH-0021 Parental relationship.

    Contains partner (parent) information, relationship type, and care arrangement.

    XML Schema: eCH-0021 parentalRelationshipType
    """

    partner: ECH0021Partner = Field(..., description="Parent information")
    relationship_valid_from: Optional[date] = Field(
        None,
        alias='relationshipValidFrom',
        description="Date when parental relationship was established"
    )
    type_of_relationship: TypeOfRelationship = Field(
        ...,
        description="Type of parental relationship (3=mother, 4=father, 5=foster father, 6=foster mother)"
    )
    care: CareType = Field(
        ...,
        description="Care/custody arrangement"
    )

    @field_validator('type_of_relationship')
    @classmethod
    def validate_parental_relationship_type(cls, v: TypeOfRelationship) -> TypeOfRelationship:
        """Validate that relationship type is a parental one."""
        parental_types = (
            TypeOfRelationship.MOTHER,
            TypeOfRelationship.FATHER,
            TypeOfRelationship.FOSTER_FATHER,
            TypeOfRelationship.FOSTER_MOTHER
        )
        if v not in parental_types:
            raise ValueError(
                f"Parental relationship must be MOTHER (3), FATHER (4), FOSTER_FATHER (5), or FOSTER_MOTHER (6), got: {v}"
            )
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'parentalRelationship') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        self.partner.to_xml(parent=elem, namespace=namespace)

        if self.relationship_valid_from:
            rel_from_elem = ET.SubElement(elem, f'{{{namespace}}}relationshipValidFrom')
            rel_from_elem.text = self.relationship_valid_from.isoformat()

        rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
        rel_elem.text = self.type_of_relationship.value

        care_elem = ET.SubElement(elem, f'{{{namespace}}}care')
        care_elem.text = self.care.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021ParentalRelationship':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        partner_elem = element.find('eCH-0021:partner', ns)
        rel_from_elem = element.find('eCH-0021:relationshipValidFrom', ns)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        care_elem = element.find('eCH-0021:care', ns)

        return cls(
            partner=ECH0021Partner.from_xml(partner_elem),
            relationshipValidFrom=date.fromisoformat(rel_from_elem.text) if rel_from_elem is not None else None,
            type_of_relationship=TypeOfRelationship(rel_elem.text),
            care=CareType(care_elem.text)
        )


class ECH0021GuardianMeasureInfo(BaseModel):
    """eCH-0021 Guardian measure information.

    Contains legal basis (ZGB articles) and validity information for
    child and adult protection measures (KESR - Kindes- und Erwachsenenschutzrecht).

    XML Schema: eCH-0021 guardianMeasureInfoType
    XSD Lines: 126-145
    PDF: Section 3.1.9.5 (pages 20-22)
    """

    based_on_law: List[str] = Field(
        default_factory=list,
        description="ZGB article numbers for KESR measures (optional, unbounded)"
    )
    based_on_law_add_on: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Additional legal basis information (optional, 1-100 chars)"
    )
    guardian_measure_valid_from: date = Field(
        ...,
        description="Date when guardian measure becomes valid (required)"
    )

    @field_validator('based_on_law')
    @classmethod
    def validate_based_on_law(cls, v: List[str]) -> List[str]:
        """Validate ZGB article numbers against eCH-0021 basedOnLawType.

        XSD enumeration (lines 175-196): 18 valid ZGB article values.
        These are Swiss Civil Code articles for child and adult protection.
        """
        valid_articles = {
            "306", "310", "311", "312", "327-a", "363", "368", "369", "370",
            "371", "372", "393", "394", "395", "396", "397", "398", "399"
        }

        for article in v:
            if article not in valid_articles:
                raise ValueError(
                    f"Invalid ZGB article '{article}'. Must be one of: {sorted(valid_articles)}"
                )
        return v

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'guardianMeasureInfo') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # basedOnLaw (optional, multiple)
        for article in self.based_on_law:
            law_elem = ET.SubElement(elem, f'{{{namespace}}}basedOnLaw')
            law_elem.text = article

        # basedOnLawAddOn (optional)
        if self.based_on_law_add_on:
            addon_elem = ET.SubElement(elem, f'{{{namespace}}}basedOnLawAddOn')
            addon_elem.text = self.based_on_law_add_on

        # guardianMeasureValidFrom (required)
        valid_from_elem = ET.SubElement(elem, f'{{{namespace}}}guardianMeasureValidFrom')
        valid_from_elem.text = self.guardian_measure_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021GuardianMeasureInfo':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        # basedOnLaw (optional, multiple)
        law_elems = element.findall('eCH-0021:basedOnLaw', ns)
        based_on_law = [elem.text for elem in law_elems if elem.text]

        # basedOnLawAddOn (optional)
        addon_elem = element.find('eCH-0021:basedOnLawAddOn', ns)
        based_on_law_add_on = addon_elem.text if addon_elem is not None else None

        # guardianMeasureValidFrom (required)
        valid_from_elem = element.find('eCH-0021:guardianMeasureValidFrom', ns)
        guardian_measure_valid_from = date.fromisoformat(valid_from_elem.text)

        return cls(
            based_on_law=based_on_law,
            based_on_law_add_on=based_on_law_add_on,
            guardian_measure_valid_from=guardian_measure_valid_from
        )


class ECH0021GuardianRelationship(BaseModel):
    """eCH-0021 Guardian relationship.

    Contains guardian information for child and adult protection measures.
    Guardian can be a person OR an organization (e.g., KESB).

    XML Schema: eCH-0021 guardianRelationshipType
    XSD Lines: 146-174
    PDF: Section 3.1.9.3 (page 19)
    """

    guardian_relationship_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Guardian relationship identifier (required, 1-36 chars)"
    )

    # Partner (optional) - xs:choice: person OR organization
    person_identification: Optional[ECH0044PersonIdentification] = Field(
        None,
        description="Guardian as person (full identification)"
    )
    person_identification_partner: Optional[ECH0044PersonIdentificationLight] = Field(
        None,
        description="Guardian as person (light identification)"
    )
    partner_id_organisation: Optional[ECH0011PartnerIdOrganisation] = Field(
        None,
        description="Guardian as organization (e.g., KESB)"
    )

    # Partner address (optional, inside partner element)
    partner_address: Optional[ECH0010MailAddress] = Field(
        None,
        description="Guardian's mailing address (optional)"
    )

    type_of_relationship: TypeOfRelationship = Field(
        ...,
        description="Type of guardian relationship (7=legal assistant, 8=advisor, 9=guardian, 10=healthcare proxy)"
    )

    guardian_measure_info: ECH0021GuardianMeasureInfo = Field(
        ...,
        description="Guardian measure information (required)"
    )

    care: Optional[CareType] = Field(
        None,
        description="Care arrangement (optional)"
    )

    @field_validator('type_of_relationship')
    @classmethod
    def validate_guardian_relationship_type(cls, v: TypeOfRelationship) -> TypeOfRelationship:
        """Validate that relationship type is a guardian one.

        XSD restriction (lines 158-163): Only values 7, 8, 9, 10 allowed.
        """
        guardian_types = (
            TypeOfRelationship.LEGAL_ASSISTANT,           # 7
            TypeOfRelationship.ADVISOR,                   # 8
            TypeOfRelationship.GUARDIAN,                  # 9
            TypeOfRelationship.HEALTHCARE_PROXY           # 10
        )
        if v not in guardian_types:
            raise ValueError(
                f"Guardian relationship must be LEGAL_ASSISTANT (7), ADVISOR (8), "
                f"GUARDIAN (9), or HEALTHCARE_PROXY (10), got: {v}"
            )
        return v

    @model_validator(mode='after')
    def validate_partner_choice(self):
        """Validate xs:choice constraint: at most one partner type can be set."""
        # Count how many partner fields are set
        partner_count = sum([
            self.person_identification is not None,
            self.person_identification_partner is not None,
            self.partner_id_organisation is not None,
        ])

        # XSD allows 0 or 1 partner (minOccurs=0)
        # But if partner is present, exactly ONE type must be chosen
        if partner_count > 1:
            raise ValueError(
                "Guardian partner must be at most ONE of: person_identification, "
                "person_identification_partner, or partner_id_organisation. "
                f"Got {partner_count} partner types."
            )

        return self

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'guardianRelationship') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # guardianRelationshipId (required)
        id_elem = ET.SubElement(elem, f'{{{namespace}}}guardianRelationshipId')
        id_elem.text = self.guardian_relationship_id

        # partner (optional) - xs:choice + optional address
        if (self.person_identification or self.person_identification_partner or
            self.partner_id_organisation or self.partner_address):
            partner_elem = ET.SubElement(elem, f'{{{namespace}}}partner')

            # xs:choice: person OR organization
            if self.person_identification:
                self.person_identification.to_xml(
                    parent=partner_elem,
                    element_name='personIdentification',
                    wrapper_namespace=namespace
                )
            elif self.person_identification_partner:
                self.person_identification_partner.to_xml(
                    parent=partner_elem,
                    element_name='personIdentificationPartner',
                    wrapper_namespace=namespace
                )
            elif self.partner_id_organisation:
                # ECH0011PartnerIdOrganisation uses wrapper_namespace parameter
                # Wrapper element uses eCH-0021, content uses eCH-0011
                self.partner_id_organisation.to_xml(
                    parent=partner_elem,
                    tag='partnerIdOrganisation',
                    wrapper_namespace=namespace  # Use eCH-0021 for wrapper element
                )

            # address (optional, inside partner)
            if self.partner_address:
                # Element name must be 'address' per eCH-0021 XSD (line 151)
                # Wrapper element in eCH-0021 namespace, content in eCH-0010 v5
                self.partner_address.to_xml(
                    parent=partner_elem,
                    element_name='address',
                    wrapper_namespace=namespace  # eCH-0021 for wrapper
                    # namespace parameter defaults to eCH-0010 v5 for content
                )

        # typeOfRelationship (required)
        rel_elem = ET.SubElement(elem, f'{{{namespace}}}typeOfRelationship')
        rel_elem.text = self.type_of_relationship.value

        # guardianMeasureInfo (required)
        self.guardian_measure_info.to_xml(parent=elem, namespace=namespace)

        # care (optional)
        if self.care:
            care_elem = ET.SubElement(elem, f'{{{namespace}}}care')
            care_elem.text = self.care.value

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021GuardianRelationship':
        """Import from eCH-0021 XML."""
        ns = {
            'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7',
            'eCH-0044': 'http://www.ech.ch/xmlns/eCH-0044/4',
            'eCH-0011': 'http://www.ech.ch/xmlns/eCH-0011/8',
        }

        # guardianRelationshipId (required)
        id_elem = element.find('eCH-0021:guardianRelationshipId', ns)
        guardian_relationship_id = id_elem.text

        # partner (optional) - parse xs:choice
        partner_elem = element.find('eCH-0021:partner', ns)
        person_identification = None
        person_identification_partner = None
        partner_id_organisation = None
        partner_address = None

        if partner_elem is not None:
            # Try to find person identification (full)
            person_id_elem = partner_elem.find('eCH-0021:personIdentification', ns)
            if person_id_elem is not None:
                person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

            # Try to find person identification (light/partner)
            person_partner_elem = partner_elem.find('eCH-0021:personIdentificationPartner', ns)
            if person_partner_elem is not None:
                person_identification_partner = ECH0044PersonIdentificationLight.from_xml(person_partner_elem)

            # Try to find organization
            # Note: wrapper element is in eCH-0021 namespace, content in eCH-0011
            org_elem = partner_elem.find('eCH-0021:partnerIdOrganisation', ns)
            if org_elem is not None:
                partner_id_organisation = ECH0011PartnerIdOrganisation.from_xml(org_elem)

            # Try to find address (inside partner)
            # Note: wrapper element 'address' is in eCH-0021 namespace, content in eCH-0010 v5
            addr_elem = partner_elem.find('eCH-0021:address', ns)
            if addr_elem is not None:
                partner_address = ECH0010MailAddress.from_xml(addr_elem)

        # typeOfRelationship (required)
        rel_elem = element.find('eCH-0021:typeOfRelationship', ns)
        type_of_relationship = TypeOfRelationship(rel_elem.text)

        # guardianMeasureInfo (required)
        measure_elem = element.find('eCH-0021:guardianMeasureInfo', ns)
        guardian_measure_info = ECH0021GuardianMeasureInfo.from_xml(measure_elem)

        # care (optional)
        care_elem = element.find('eCH-0021:care', ns)
        care = CareType(care_elem.text) if care_elem is not None else None

        return cls(
            guardian_relationship_id=guardian_relationship_id,
            person_identification=person_identification,
            person_identification_partner=person_identification_partner,
            partner_id_organisation=partner_id_organisation,
            partner_address=partner_address,
            type_of_relationship=type_of_relationship,
            guardian_measure_info=guardian_measure_info,
            care=care
        )


# ============================================================================
# Optional/Low Priority Types (Military, Civil Defense, Health Insurance, etc.)
# ============================================================================

class ECH0021ArmedForcesData(BaseModel):
    """eCH-0021 Armed forces data.

    XML Schema: eCH-0021 armedForcesDataType
    """

    armed_forces_service: Optional[YesNo] = None
    armed_forces_liability: Optional[YesNo] = None
    armed_forces_valid_from: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'armedForcesData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.armed_forces_service:
            service_elem = ET.SubElement(elem, f'{{{namespace}}}armedForcesService')
            service_elem.text = self.armed_forces_service.value

        if self.armed_forces_liability:
            liability_elem = ET.SubElement(elem, f'{{{namespace}}}armedForcesLiability')
            liability_elem.text = self.armed_forces_liability.value

        if self.armed_forces_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}armedForcesValidFrom')
            from_elem.text = self.armed_forces_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021ArmedForcesData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        service_elem = element.find('eCH-0021:armedForcesService', ns)
        liability_elem = element.find('eCH-0021:armedForcesLiability', ns)
        from_elem = element.find('eCH-0021:armedForcesValidFrom', ns)

        return cls(
            armed_forces_service=YesNo(service_elem.text) if service_elem is not None else None,
            armed_forces_liability=YesNo(liability_elem.text) if liability_elem is not None else None,
            armed_forces_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None
        )


class ECH0021CivilDefenseData(BaseModel):
    """eCH-0021 Civil defense data.

    XML Schema: eCH-0021 civilDefenseDataType
    """

    civil_defense: Optional[YesNo] = None
    civil_defense_valid_from: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'civilDefenseData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.civil_defense:
            cd_elem = ET.SubElement(elem, f'{{{namespace}}}civilDefense')
            cd_elem.text = self.civil_defense.value

        if self.civil_defense_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}civilDefenseValidFrom')
            from_elem.text = self.civil_defense_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021CivilDefenseData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        cd_elem = element.find('eCH-0021:civilDefense', ns)
        from_elem = element.find('eCH-0021:civilDefenseValidFrom', ns)

        return cls(
            civil_defense=YesNo(cd_elem.text) if cd_elem is not None else None,
            civil_defense_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None
        )


class ECH0021FireServiceData(BaseModel):
    """eCH-0021 Fire service data.

    XML Schema: eCH-0021 fireServiceDataType
    """

    fire_service: Optional[YesNo] = None
    fire_service_liability: Optional[YesNo] = None
    fire_service_valid_from: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'fireServiceData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        if self.fire_service:
            fs_elem = ET.SubElement(elem, f'{{{namespace}}}fireService')
            fs_elem.text = self.fire_service.value

        if self.fire_service_liability:
            liability_elem = ET.SubElement(elem, f'{{{namespace}}}fireServiceLiability')
            liability_elem.text = self.fire_service_liability.value

        if self.fire_service_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}fireServiceValidFrom')
            from_elem.text = self.fire_service_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021FireServiceData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        fs_elem = element.find('eCH-0021:fireService', ns)
        liability_elem = element.find('eCH-0021:fireServiceLiability', ns)
        from_elem = element.find('eCH-0021:fireServiceValidFrom', ns)

        return cls(
            fire_service=YesNo(fs_elem.text) if fs_elem is not None else None,
            fire_service_liability=YesNo(liability_elem.text) if liability_elem is not None else None,
            fire_service_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None
        )


class ECH0021HealthInsuranceData(BaseModel):
    """eCH-0021 Health insurance data.

    Contains health insurance status and optional insurance information.
    Insurance can be specified either as a name (string) or as an
    organization address (full contact details).

    XML Schema: eCH-0021 healthInsuranceDataType
    """

    health_insured: YesNo = Field(..., description="Health insurance status")

    # Choice: insurance name OR insurance address
    insurance_name: Optional[str] = Field(None, max_length=100, description="Insurance company name")
    insurance_address: Optional['ECH0010OrganisationMailAddress'] = Field(
        None,
        description="Insurance company full address (organisation + address)"
    )

    health_insurance_valid_from: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'healthInsuranceData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        hi_elem = ET.SubElement(elem, f'{{{namespace}}}healthInsured')
        hi_elem.text = self.health_insured.value

        # Insurance: choice of name OR address
        if self.insurance_name or self.insurance_address:
            ins_elem = ET.SubElement(elem, f'{{{namespace}}}insurance')

            if self.insurance_name:
                name_elem = ET.SubElement(ins_elem, f'{{{namespace}}}insuranceName')
                name_elem.text = self.insurance_name
            elif self.insurance_address:
                # Create the insuranceAddress wrapper in eCH-0021 namespace
                addr_wrapper = ET.SubElement(ins_elem, f'{{{namespace}}}insuranceAddress')

                # Add organisation and addressInformation in eCH-0010 namespace
                ns_010 = 'http://www.ech.ch/xmlns/eCH-0010/5'

                # Serialize organisation
                self.insurance_address.organisation.to_xml(
                    parent=addr_wrapper,
                    namespace=ns_010,
                    element_name='organisation'
                )

                # Serialize address information
                self.insurance_address.address_information.to_xml(
                    parent=addr_wrapper,
                    namespace=ns_010,
                    element_name='addressInformation'
                )

        if self.health_insurance_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceValidFrom')
            from_elem.text = self.health_insurance_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021HealthInsuranceData':
        """Import from eCH-0021 XML."""
        ns_0021 = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}
        ns_0010 = {'eCH-0010': 'http://www.ech.ch/xmlns/eCH-0010/5'}

        hi_elem = element.find('eCH-0021:healthInsured', ns_0021)
        ins_elem = element.find('eCH-0021:insurance', ns_0021)

        # Try to find insurance name or address
        insurance_name = None
        insurance_address = None
        if ins_elem is not None:
            name_elem = ins_elem.find('eCH-0021:insuranceName', ns_0021)
            if name_elem is not None:
                insurance_name = name_elem.text
            else:
                # insuranceAddress wrapper is in eCH-0021 namespace
                # Content inside is from eCH-0010
                addr_elem = ins_elem.find('eCH-0021:insuranceAddress', ns_0021)
                if addr_elem is not None:
                    # The insuranceAddress contains organisation and addressInformation elements
                    org_elem = addr_elem.find('eCH-0010:organisation', ns_0010)
                    addr_info_elem = addr_elem.find('eCH-0010:addressInformation', ns_0010)

                    if org_elem is not None and addr_info_elem is not None:
                        # Parse organisation info
                        org_info = ECH0010OrganisationMailAddressInfo.from_xml(org_elem)
                        # Parse address information
                        addr_info = ECH0010AddressInformation.from_xml(addr_info_elem)
                        # Create the complete organisation mail address
                        insurance_address = ECH0010OrganisationMailAddress(
                            organisation=org_info,
                            address_information=addr_info
                        )

        from_elem = element.find('eCH-0021:healthInsuranceValidFrom', ns_0021)

        return cls(
            health_insured=YesNo(hi_elem.text),
            insurance_name=insurance_name,
            insurance_address=insurance_address,
            health_insurance_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None
        )


class ECH0021MatrimonialInheritanceArrangementData(BaseModel):
    """eCH-0021 Matrimonial inheritance arrangement data.

    XML Schema: eCH-0021 matrimonialInheritanceArrangementDataType
    """

    matrimonial_inheritance_arrangement: YesNo = Field(
        ...,
        description="Matrimonial inheritance arrangement exists"
    )
    matrimonial_inheritance_arrangement_valid_from: Optional[date] = None

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'matrimonialInheritanceArrangementData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        mia_elem = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangement')
        mia_elem.text = self.matrimonial_inheritance_arrangement.value

        if self.matrimonial_inheritance_arrangement_valid_from:
            from_elem = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangementValidFrom')
            from_elem.text = self.matrimonial_inheritance_arrangement_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021MatrimonialInheritanceArrangementData':
        """Import from eCH-0021 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        mia_elem = element.find('eCH-0021:matrimonialInheritanceArrangement', ns)
        from_elem = element.find('eCH-0021:matrimonialInheritanceArrangementValidFrom', ns)

        return cls(
            matrimonial_inheritance_arrangement=YesNo(mia_elem.text),
            matrimonial_inheritance_arrangement_valid_from=date.fromisoformat(from_elem.text) if from_elem is not None else None
        )


# ============================================================================
# Political Rights (v7 ONLY - removed in v8)
# ============================================================================

class ECH0021PoliticalRightData(BaseModel):
    """eCH-0021 v7 Political rights data.

    NOTE: This type was REMOVED in v8 (federal voting restrictions removed).
    Only exists in v7 for compatibility with eCH-0020 v3.0.

    XML Schema: eCH-0021-7-0 politicalRightDataType
    Namespace: http://www.ech.ch/xmlns/eCH-0021/7
    """

    model_config = ConfigDict(populate_by_name=True)

    restricted_voting_and_election_right_federation: Optional[bool] = Field(
        None,
        alias='restrictedVotingAndElectionRightFederation',
        description='Restriction of voting rights at federal level (deprecated in v8)'
    )

    def to_xml(self, parent: Optional[ET.Element] = None,
               namespace: str = 'http://www.ech.ch/xmlns/eCH-0021/7',
               element_name: str = 'politicalRightData') -> ET.Element:
        """Export to eCH-0021 v7 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # restrictedVotingAndElectionRightFederation (optional boolean)
        if self.restricted_voting_and_election_right_federation is not None:
            restriction_elem = ET.SubElement(
                elem,
                f'{{{namespace}}}restrictedVotingAndElectionRightFederation'
            )
            restriction_elem.text = 'true' if self.restricted_voting_and_election_right_federation else 'false'

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0021PoliticalRightData':
        """Import from eCH-0021 v7 XML."""
        ns = {'eCH-0021': 'http://www.ech.ch/xmlns/eCH-0021/7'}

        restriction_elem = element.find(
            'eCH-0021:restrictedVotingAndElectionRightFederation',
            ns
        )

        restricted = None
        if restriction_elem is not None and restriction_elem.text:
            restricted = restriction_elem.text.lower() == 'true'

        return cls(
            restricted_voting_and_election_right_federation=restricted
        )
