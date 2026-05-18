"""eCH-0020 v3.0 — Correction Events."""

from typing import Optional, List
from datetime import date
from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
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


class ECH0020EventMaritalStatusPartner(ECHModel):
    """Marital status with partner event.

    XSD: eventMaritalStatusPartner (eCH-0020-3-0.xsd lines 429-435)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventMaritalStatusPartner'

    marital_status_partner_person: ECH0044PersonIdentification = xml_field(
        'maritalStatusPartnerPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_data: ECH0011MaritalDataRestrictedMaritalStatusPartner = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventChangeName(ECHModel):
    """Change name event.

    XSD: eventChangeName (eCH-0020-3-0.xsd lines 436-442)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeName'

    change_name_person: ECH0044PersonIdentification = xml_field(
        'changeNamePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')


class ECH0020ChangeSexPerson(ECHModel):
    """Person data for sex change event.

    XSD: changeSexPersonType (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'changeSexPerson'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    sex: Sex = xml_field('sex')


class ECH0020EventChangeSex(ECHModel):
    """Change sex event.

    XSD: eventChangeSex (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventChangeSex'

    change_sex_person: ECH0020ChangeSexPerson = xml_field('changeSexPerson')


class ECH0020PersonIdOnly(ECHModel):
    """Person identification subset (ID fields only).

    XSD: personIdOnlyType (eCH-0020-3-0.xsd lines 714-721)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'personIdentificationAfter'

    vn: Optional[str] = xml_field('vn', default=None)
    local_person_id: ECH0044NamedPersonId = xml_field(
        'localPersonId', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    other_person_id: Optional[List[ECH0044NamedPersonId]] = xml_field(
        'otherPersonId', default=None,
        wrapper=True, child_ns=NS.ECH0044_V4, is_list=True,
    )
    eu_person_id: Optional[List[ECH0044NamedPersonId]] = xml_field(
        'euPersonId', default=None,
        wrapper=True, child_ns=NS.ECH0044_V4, is_list=True,
    )


class ECH0020CorrectIdentificationPerson(ECHModel):
    """Before/after person identification for correction.

    XSD: correctIdentificationPersonType (eCH-0020-3-0.xsd lines 722-727)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'correctIdentificationPerson'

    person_identification_before: ECH0044PersonIdentification = xml_field(
        'personIdentificationBefore', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    person_identification_after: ECH0020PersonIdOnly = xml_field(
        'personIdentificationAfter',
    )


class ECH0020EventCorrectIdentification(ECHModel):
    """Identification correction event.

    XSD: eventCorrectIdentification (eCH-0020-3-0.xsd lines 728-734)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectIdentification'

    correct_identification_person: ECH0020CorrectIdentificationPerson = xml_field(
        'correctIdentificationPerson',
    )
    identification_valid_from: Optional[date] = xml_field(
        'identificationValidFrom', default=None,
    )


class ECH0020IdentificationConversionPerson(ECHModel):
    """Person data for identification conversion.

    XSD: identificationConversionPersonType (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'identificationConversionPerson'

    vn: Optional[str] = xml_field('vn', default=None)
    local_person_id_before: ECH0044NamedPersonId = xml_field(
        'localPersonIdBefore', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    local_person_id_after: ECH0044NamedPersonId = xml_field(
        'localPersonIdAfter', wrapper=True, child_ns=NS.ECH0044_V4,
    )


class ECH0020EventIdentificationConversion(ECHModel):
    """Identification conversion event.

    XSD: eventIdentificationConversion (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventIdentificationConversion'

    identification_conversion_person: List[ECH0020IdentificationConversionPerson] = xml_field(
        'identificationConversionPerson', is_list=True, min_length=1,
    )
    identification_valid_from: Optional[date] = xml_field(
        'identificationValidFrom', default=None,
    )


class ECH0020EventCorrectName(ECHModel):
    """Name correction event.

    XSD: eventCorrectName (eCH-0020-3-0.xsd lines 757-763)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectName'

    correct_name_person: ECH0044PersonIdentification = xml_field(
        'correctNamePerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')


class ECH0020EventCorrectNationality(ECHModel):
    """Nationality correction event.

    XSD: eventCorrectNationality (eCH-0020-3-0.xsd lines 764-770)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectNationality'

    correct_nationality_person: ECH0044PersonIdentification = xml_field(
        'correctNationalityPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventCorrectContact(ECHModel):
    """Contact correction event.

    XSD: eventCorrectContact (eCH-0020-3-0.xsd lines 771-777)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectContact'

    correct_contact_person: ECH0044PersonIdentification = xml_field(
        'correctContactPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    contact_data: Optional[ECH0011ContactData] = xml_field(
        'contactData', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventCorrectReligion(ECHModel):
    """Religion correction event.

    XSD: eventCorrectReligion (eCH-0020-3-0.xsd lines 771-777)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectReligion'

    correct_religion_person: ECH0044PersonIdentification = xml_field(
        'correctReligionPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    religion_data: ECH0011ReligionData = xml_field(
        'religionData', wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventCorrectPlaceOfOrigin(ECHModel):
    """Place of origin correction event.

    XSD: eventCorrectPlaceOfOrigin (eCH-0020-3-0.xsd lines 778-784)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectPlaceOfOrigin'

    correct_place_of_origin_person: ECH0044PersonIdentification = xml_field(
        'correctPlaceOfOriginPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    place_of_origin_info: Optional[List[ECH0020PlaceOfOriginInfo]] = xml_field(
        'placeOfOriginInfo', default=None, is_list=True,
    )


class ECH0020EventCorrectResidencePermit(ECHModel):
    """Residence permit correction event.

    XSD: eventCorrectResidencePermit (eCH-0020-3-0.xsd lines 785-791)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectResidencePermit'

    correct_residence_permit_person: ECH0044PersonIdentification = xml_field(
        'correctResidencePermitPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = xml_field(
        'residencePermitData', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )


class ECH0020EventCorrectMaritalInfo(ECHModel):
    """Marital info correction event.

    XSD: eventCorrectMaritalInfo (eCH-0020-3-0.xsd lines 792-799)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectMaritalInfo'

    correct_marital_data_person: ECH0044PersonIdentification = xml_field(
        'correctMaritalDataPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    marital_info: ECH0020MaritalInfo = xml_field('maritalInfo')
    marital_relationship: Optional[ECH0021MaritalRelationship] = xml_field(
        'maritalRelationship', default=None,
        wrapper=True, child_ns=NS.ECH0021_V7,
    )


class ECH0020EventCorrectBirthInfo(ECHModel):
    """Birth info correction event.

    XSD: eventCorrectBirthInfo (eCH-0020-3-0.xsd lines 800-806)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectBirthInfo'

    correct_birth_info_person: ECH0044PersonIdentification = xml_field(
        'correctBirthInfoPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    birth_info: ECH0020BirthInfo = xml_field('birthInfo')


class ECH0020EventCorrectGuardianRelationship(ECHModel):
    """Guardian relationship correction event.

    XSD: eventCorrectGuardianRelationship (eCH-0020-3-0.xsd lines 807-813)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectGuardianRelationship'

    correct_guardian_relationship_person: ECH0044PersonIdentification = xml_field(
        'correctGuardianRelationshipPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = xml_field(
        'guardianRelationship', default=None,
        wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )


class ECH0020EventCorrectParentalRelationship(ECHModel):
    """Parental relationship correction event.

    XSD: eventCorrectParentalRelationship (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectParentalRelationship'

    correct_parental_relationship_person: ECH0044PersonIdentification = xml_field(
        'correctParentalRelationshipPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = xml_field(
        'parentalRelationship', default=None,
        wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )


class ECH0020EventCorrectReporting(ECHModel):
    """Reporting data correction event.

    XSD: eventCorrectReporting (eCH-0020-3-0.xsd lines 695-706)
    XSD CHOICE: exactly ONE of hasMainResidence/hasSecondaryResidence/hasOtherResidence.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectReporting'

    correct_reporting_person: ECH0044PersonIdentification = xml_field(
        'correctReportingPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    has_main_residence: Optional[ECH0011MainResidence] = xml_field(
        'hasMainResidence', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )
    has_secondary_residence: Optional[ECH0011SecondaryResidence] = xml_field(
        'hasSecondaryResidence', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )
    has_other_residence: Optional[ECH0011OtherResidence] = xml_field(
        'hasOtherResidence', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )
    reporting_valid_from: Optional[date] = xml_field(
        'reportingValidFrom', default=None,
    )

    @model_validator(mode='after')
    def validate_residence_choice(self) -> 'ECH0020EventCorrectReporting':
        """Validate XSD CHOICE: exactly ONE of main/secondary/other residence."""
        set_count = sum([
            self.has_main_residence is not None,
            self.has_secondary_residence is not None,
            self.has_other_residence is not None,
        ])
        if set_count == 0:
            raise ValueError(
                "eventCorrectReporting requires exactly ONE of: "
                "hasMainResidence, hasSecondaryResidence, or hasOtherResidence"
            )
        if set_count > 1:
            raise ValueError(
                f"eventCorrectReporting allows only ONE residence type, "
                f"but {set_count} were provided"
            )
        return self


class ECH0020EventCorrectOccupation(ECHModel):
    """Occupation correction event.

    XSD: eventCorrectOccupation (eCH-0020-3-0.xsd lines 707-713)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectOccupation'

    correct_occupation_person: ECH0044PersonIdentification = xml_field(
        'correctOccupationPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    job_data: Optional[ECH0021JobData] = xml_field(
        'jobData', default=None,
        wrapper=True, child_ns=NS.ECH0021_V7,
    )


class ECH0020EventCorrectDeathData(ECHModel):
    """Death data correction event.

    XSD: eventCorrectDeathData (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'eventCorrectDeathData'

    correct_death_data_person: ECH0044PersonIdentification = xml_field(
        'correctDeathDataPerson', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    death_data: Optional[ECH0011DeathData] = xml_field(
        'deathData', default=None,
        wrapper=True, child_ns=NS.ECH0011_V8,
    )
