"""eCH-0020 v3.0 — Admin Events."""

import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from openmun_ech.core import NS
from openmun_ech.ech0011 import (
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011ResidencePermitData,
    YesNo,
)
from openmun_ech.ech0021 import DataLockType
from openmun_ech.ech0021.v7 import (
    ECH0021PersonAdditionalData,
    ECH0021LockData,
    ECH0021JobData,
    ECH0021HealthInsuranceData,
    ECH0021ArmedForcesData,
    ECH0021CivilDefenseData,
    ECH0021FireServiceData,
    ECH0021PoliticalRightData,
    ECH0021GuardianRelationship,
    ECH0021ParentalRelationship,
    ECH0021MatrimonialInheritanceArrangementData,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification


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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeReligion'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeOccupation'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventGuardianMeasure'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventUndoGuardian'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeGuardian'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventChangeNationality'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_011 = NS.ECH0011_V8

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventEntryResidencePermit'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7
        ns_011 = NS.ECH0011_V8

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7
        ns_011 = NS.ECH0011_V8

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
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'eventDataLock'
    ) -> ET.Element:
        """Serialize to XML with proper namespace handling."""
        ns_020 = namespace
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

        # Create eventCorrectPersonAdditionalData element
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # correctPersonAdditionalDataPerson (required)
        # Element is in eCH-0020 namespace, but content type is eCH-0044:personIdentificationType
        self.correct_person_additional_data_person.to_xml(
            parent=elem,
            namespace=ns_044,
            element_name='correctPersonAdditionalDataPerson',
            wrapper_namespace=ns_020  # Element wrapper in eCH-0020 namespace
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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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
        ns_020 = NS.ECH0020_V3
        ns_044 = NS.ECH0044_V4
        ns_021 = NS.ECH0021_V7

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


