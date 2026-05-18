"""eCH-0020 v3.0 — Admin Events."""

from typing import Optional, List
from datetime import date

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0011 import (
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011ResidencePermitData,
    YesNo,
)
from openmun_ech.ech0021 import DataLockType
from openmun_ech.ech0021.v7 import (
    ECH0021PersonAdditionalData,
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


class ECH0020EventChangeReligion(ECHModel):
    """Change religion event.

    XSD: eventChangeReligion (eCH-0020-3-0.xsd lines 604-610)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeReligion'

    change_religion_person: ECH0044PersonIdentification = xml_field(
        'changeReligionPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    religion_data: ECH0011ReligionData = xml_field(
        'religionData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventChangeOccupation(ECHModel):
    """Change occupation event.

    XSD: eventChangeOccupation (eCH-0020-3-0.xsd lines 611-617)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeOccupation'

    change_occupation_person: ECH0044PersonIdentification = xml_field(
        'changeOccupationPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    job_data: Optional[ECH0021JobData] = xml_field(
        'jobData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventGuardianMeasure(ECHModel):
    """Guardian measure event — establish guardianship.

    XSD: eventGuardianMeasure (eCH-0020-3-0.xsd lines 618-624)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventGuardianMeasure'

    guardian_measure_person: ECH0044PersonIdentification = xml_field(
        'guardianMeasurePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    relationship: ECH0021GuardianRelationship = xml_field(
        'relationship', wrapper=True, child_ns=NS.ECH0021_V7,
    )


class ECH0020EventUndoGuardian(ECHModel):
    """Undo guardian event — terminate guardianship.

    XSD: eventUndoGuardian (eCH-0020-3-0.xsd lines 625-632)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventUndoGuardian'

    undo_guardian_person: ECH0044PersonIdentification = xml_field(
        'undoGuardianPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    guardian_relationship_id: str = xml_field(
        'guardianRelationshipId',
        min_length=1, max_length=36,
    )
    undo_guardian_valid_from: Optional[date] = xml_field(
        'undoGuardianValidFrom', default=None,
    )


class ECH0020EventChangeGuardian(ECHModel):
    """Change guardian event — modify guardianship.

    XSD: eventChangeGuardian (eCH-0020-3-0.xsd lines 633-640)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeGuardian'

    change_guardian_person: ECH0044PersonIdentification = xml_field(
        'changeGuardianPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    relationship: ECH0021GuardianRelationship = xml_field(
        'relationship', wrapper=True, child_ns=NS.ECH0021_V7,
    )
    change_guardian_valid_from: Optional[date] = xml_field(
        'changeGuardianValidFrom', default=None,
    )


class ECH0020EventChangeNationality(ECHModel):
    """Change nationality event.

    XSD: eventChangeNationality (eCH-0020-3-0.xsd lines 641-647)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeNationality'

    change_nationality_person: ECH0044PersonIdentification = xml_field(
        'changeNationalityPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventEntryResidencePermit(ECHModel):
    """Entry residence permit event.

    XSD: eventEntryResidencePermit (eCH-0020-3-0.xsd lines 648-655)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventEntryResidencePermit'

    entry_residence_permit_person: ECH0044PersonIdentification = xml_field(
        'entryResidencePermitPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    job_data: Optional[ECH0021JobData] = xml_field(
        'jobData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )
    residence_permit_data: ECH0011ResidencePermitData = xml_field(
        'residencePermitData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventDataLock(ECHModel):
    """Data lock event.

    XSD: eventDataLock (eCH-0020-3-0.xsd lines 656-664)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventDataLock'

    data_lock_person: ECH0044PersonIdentification = xml_field(
        'dataLockPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    data_lock: DataLockType = xml_field('dataLock')
    data_lock_valid_from: Optional[date] = xml_field(
        'dataLockValidFrom', default=None,
    )
    data_lock_valid_till: Optional[date] = xml_field(
        'dataLockValidTill', default=None,
    )


class ECH0020EventPaperLock(ECHModel):
    """Paper lock event.

    XSD: eventPaperLock (eCH-0020-3-0.xsd lines 665-673)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventPaperLock'

    paper_lock_person: ECH0044PersonIdentification = xml_field(
        'paperLockPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    paper_lock: YesNo = xml_field('paperLock')
    paper_lock_valid_from: Optional[date] = xml_field(
        'paperLockValidFrom', default=None,
    )
    paper_lock_valid_till: Optional[date] = xml_field(
        'paperLockValidTill', default=None,
    )


class ECH0020EventCare(ECHModel):
    """Care relationship event.

    XSD: eventCare (eCH-0020-3-0.xsd lines 674-680)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCare'

    care_person: ECH0044PersonIdentification = xml_field(
        'carePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    parental_relationship: List[ECH0021ParentalRelationship] = xml_field(
        'parentalRelationship', wrapper=True, child_ns=NS.ECH0021_V7, is_list=True, default_factory=list,
    )


class ECH0020EventCorrectPersonAdditionalData(ECHModel):
    """Correction event for person additional data.

    XSD: eventCorrectPersonAdditionalData (eCH-0020-3-0.xsd lines 814-820)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectPersonAdditionalData'

    correct_person_additional_data_person: ECH0044PersonIdentification = xml_field(
        'correctPersonAdditionalDataPerson',
        wrapper=True, child_ns=NS.ECH0044_V4,
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = xml_field(
        'personAdditionalData', default=None,
        wrapper=True, child_ns=NS.ECH0021_V7,
    )


class ECH0020EventCorrectPoliticalRightData(ECHModel):
    """Correction event for political rights data (v7-only).

    XSD: eventCorrectPoliticalRightData (eCH-0020-3-0.xsd lines 821-827)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectPoliticalRightData'

    correct_political_right_data_person: ECH0044PersonIdentification = xml_field(
        'correctPoliticalRightDataPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = xml_field(
        'politicalRightData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventCorrectDataLock(ECHModel):
    """Correction event for data lock.

    XSD: eventCorrectDataLock (eCH-0020-3-0.xsd lines 828-836)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectDataLock'

    correct_data_lock_person: ECH0044PersonIdentification = xml_field(
        'correctDataLockPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    data_lock: DataLockType = xml_field('dataLock')
    data_lock_valid_from: Optional[date] = xml_field(
        'dataLockValidFrom', default=None,
    )
    data_lock_valid_till: Optional[date] = xml_field(
        'dataLockValidTill', default=None,
    )


class ECH0020EventCorrectPaperLock(ECHModel):
    """Correction event for paper lock.

    XSD: eventCorrectPaperLock (eCH-0020-3-0.xsd lines 837-845)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectPaperLock'

    correct_paper_lock_person: ECH0044PersonIdentification = xml_field(
        'correctPaperLockPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    paper_lock: YesNo = xml_field('paperLock')
    paper_lock_valid_from: Optional[date] = xml_field(
        'paperLockValidFrom', default=None,
    )
    paper_lock_valid_till: Optional[date] = xml_field(
        'paperLockValidTill', default=None,
    )


class ECH0020EventAnnounceDuplicate(ECHModel):
    """Announce duplicate person entries.

    XSD: eventAnnounceDuplicate (eCH-0020-3-0.xsd lines 846-852)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventAnnounceDuplicate'

    correct_entry: ECH0044PersonIdentification = xml_field(
        'correctEntry', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    duplicate_entry: List[ECH0044PersonIdentification] = xml_field(
        'duplicateEntry', wrapper=True, child_ns=NS.ECH0044_V4, is_list=True,
    )


class ECH0020EventDeletedInRegister(ECHModel):
    """Person deleted from register.

    XSD: eventDeletedInRegister (eCH-0020-3-0.xsd lines 853-858)
    NOTE: XSD typo "deledetInRegisterPerson" preserved for compliance.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventDeletedInRegister'

    deledet_in_register_person: ECH0044PersonIdentification = xml_field(
        'deledetInRegisterPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )


class ECH0020EventChangeArmedForces(ECHModel):
    """Armed forces status change.

    XSD: eventChangeArmedForces (eCH-0020-3-0.xsd lines 859-865)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeArmedForces'

    change_armed_forces_person: ECH0044PersonIdentification = xml_field(
        'changeArmedForcesPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = xml_field(
        'armedForcesData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventChangeCivilDefense(ECHModel):
    """Civil defense status change.

    XSD: eventChangeCivilDefense (eCH-0020-3-0.xsd lines 866-872)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeCivilDefense'

    change_civil_defense_person: ECH0044PersonIdentification = xml_field(
        'changeCivilDefensePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = xml_field(
        'civilDefenseData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventChangeFireService(ECHModel):
    """Fire service status change.

    XSD: eventChangeFireService (eCH-0020-3-0.xsd lines 873-879)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeFireService'

    change_fire_service_person: ECH0044PersonIdentification = xml_field(
        'changeFireServicePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    fire_service_data: Optional[ECH0021FireServiceData] = xml_field(
        'fireServiceData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventChangeHealthInsurance(ECHModel):
    """Health insurance change.

    XSD: eventChangeHealthInsurance (eCH-0020-3-0.xsd lines 880-886)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeHealthInsurance'

    change_health_insurance_person: ECH0044PersonIdentification = xml_field(
        'changeHealthInsurancePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = xml_field(
        'healthInsuranceData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020EventChangeMatrimonialInheritanceArrangement(ECHModel):
    """Matrimonial/inheritance arrangement change.

    XSD: eventChangeMatrimonialInheritanceArrangement (eCH-0020-3-0.xsd lines 887-893)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeMatrimonialInheritanceArrangement'

    change_matrimonial_inheritance_arrangement_person: ECH0044PersonIdentification = xml_field(
        'changeMatrimonialInheritanceArrangementPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = xml_field(
        'matrimonialInheritanceArrangementData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )
