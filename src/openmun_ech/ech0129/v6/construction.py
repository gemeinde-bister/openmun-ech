"""eCH-0129 v6.0.0 — Construction project types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 204-210, 407-414, 415-440, 1592-1606)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.3, §4.4)

Types in this module depend on:
- eCH-0129 base_types (ECH0129NamedId)
- eCH-0129 enums (KindOfWork, TypeOfConstructionProject, TypeOfPermit,
  ProjectStatus, TypeOfClient, TypeOfConstruction)
- eCH-0007 v6 (ECH0007v6SwissMunicipality, ECH0007v6SwissAndFLMunicipality)
- eCH-0007 v5 (CantonAbbreviation — simpleType reused in v6)
- eCH-0008 v3 (ECH0008Country)
"""

from datetime import date
from typing import Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0007.v5 import CantonAbbreviation
from openmun_ech.ech0007.v6 import (
    ECH0007v6SwissAndFLMunicipality,
    ECH0007v6SwissMunicipality,
)
from openmun_ech.ech0008.v3 import ECH0008Country
from openmun_ech.ech0129.enums import (
    KindOfWork,
    ProjectStatus,
    TypeOfClient,
    TypeOfConstruction,
    TypeOfConstructionProject,
    TypeOfPermit,
)
from openmun_ech.ech0129.v6.base_types import ECH0129NamedId


# ---------------------------------------------------------------------------
# constructionLocalisationType (§4.3.1.6)
# XSD lines 204-210
# ---------------------------------------------------------------------------

class ECH0129ConstructionLocalisation(ECHModel):
    """eCH-0129 construction project localisation.

    XSD: constructionLocalisationType — xs:choice of 3 branches.
    PDF: §4.3.1.6 (page 24)

    Exactly one must be set:
    - municipality: eCH-0007:swissMunicipalityType (complex, wrapper pattern)
    - canton: eCH-0007:cantonAbbreviationType (simpleType, plain text element)
    - country: eCH-0008:countryType (complex, wrapper pattern)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'constructionLocalisation'

    municipality: Optional[ECH0007v6SwissMunicipality] = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6, default=None
    )
    canton: Optional[CantonAbbreviation] = xml_field('canton', default=None)
    country: Optional[ECH0008Country] = xml_field(
        'country', wrapper=True, child_ns=NS.ECH0008_V3, default=None
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one branch must be set."""
        count = sum(v is not None for v in [
            self.municipality, self.canton, self.country
        ])
        if count == 0:
            raise ValueError(
                "constructionLocalisationType: must set one of "
                "municipality, canton, or country"
            )
        if count > 1:
            raise ValueError(
                "constructionLocalisationType: only one of "
                "municipality, canton, or country allowed"
            )
        return self


# ---------------------------------------------------------------------------
# constructionProjectIdentificationType (§4.3.1)
# XSD lines 407-414
# ---------------------------------------------------------------------------

class ECH0129ConstructionProjectIdentification(ECHModel):
    """eCH-0129 construction project identification.

    XSD: constructionProjectIdentificationType — xs:sequence.
    PDF: §4.3.1 (page 22-24, Abb. 3)

    Fields (in XSD order):
    - localID: namedIdType, maxOccurs="unbounded" (REQUIRED, min 1)
    - EPROID: EPROIDType (nonNegativeInteger, 1–900000000), minOccurs="0"
    - officialConstructionProjectFileNo: officialConstructionProjectFileNoType
      (xs:token 1-15), minOccurs="0"
    - extensionOfOfficialConstructionProjectFileNo:
      extensionOfOfficialConstructionProjectFileNoType
      (nonNegativeInteger 0-99), minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'constructionProjectIdentification'

    local_id: list[ECH0129NamedId] = xml_field(
        'localID', is_list=True, min_length=1
    )
    eproid: Optional[int] = xml_field(
        'EPROID', default=None, ge=1, le=900000000
    )
    official_construction_project_file_no: Optional[str] = xml_field(
        'officialConstructionProjectFileNo', default=None,
        min_length=1, max_length=15
    )
    extension_of_official_construction_project_file_no: Optional[int] = xml_field(
        'extensionOfOfficialConstructionProjectFileNo', default=None,
        ge=0, le=99
    )


# ---------------------------------------------------------------------------
# kindOfConstructionWorkType (§4.4)
# XSD lines 1592-1606
# ---------------------------------------------------------------------------

class ECH0129KindOfConstructionWork(ECHModel):
    """eCH-0129 kind of construction work.

    XSD: kindOfConstructionWorkType — xs:sequence.
    PDF: §4.4 (page 31-33, Abb. 5)

    Fields (in XSD order):
    - kindOfWork: kindOfWorkType enum (REQUIRED)
    - ARBID: ARBIDType (nonNegativeInteger, 1–999999999999), minOccurs="0"
    - energeticRestauration: xs:boolean, minOccurs="0"
    - renovationHeatingsystem: xs:boolean, minOccurs="0"
    - innerConversionRenovation: xs:boolean, minOccurs="0"
    - conversion: xs:boolean, minOccurs="0"
    - extensionHeighteningHeated: xs:boolean, minOccurs="0"
    - extensionHeighteningNotHeated: xs:boolean, minOccurs="0"
    - thermicSolarFacility: xs:boolean, minOccurs="0"
    - photovoltaicSolarFacility: xs:boolean, minOccurs="0"
    - otherWorks: xs:boolean, minOccurs="0"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'kindOfConstructionWork'

    kind_of_work: KindOfWork = xml_field('kindOfWork')
    arbid: Optional[int] = xml_field(
        'ARBID', default=None, ge=1, le=999999999999
    )
    energetic_restauration: Optional[bool] = xml_field(
        'energeticRestauration', default=None
    )
    renovation_heatingsystem: Optional[bool] = xml_field(
        'renovationHeatingsystem', default=None
    )
    inner_conversion_renovation: Optional[bool] = xml_field(
        'innerConversionRenovation', default=None
    )
    conversion: Optional[bool] = xml_field('conversion', default=None)
    extension_heightening_heated: Optional[bool] = xml_field(
        'extensionHeighteningHeated', default=None
    )
    extension_heightening_not_heated: Optional[bool] = xml_field(
        'extensionHeighteningNotHeated', default=None
    )
    thermic_solar_facility: Optional[bool] = xml_field(
        'thermicSolarFacility', default=None
    )
    photovoltaic_solar_facility: Optional[bool] = xml_field(
        'photovoltaicSolarFacility', default=None
    )
    other_works: Optional[bool] = xml_field('otherWorks', default=None)


# ---------------------------------------------------------------------------
# constructionProjectType (§4.3)
# XSD lines 415-440
# ---------------------------------------------------------------------------

_MIN_PROJECT_DATE = date(2000, 1, 1)


class ECH0129ConstructionProject(ECHModel):
    """eCH-0129 construction project.

    XSD: constructionProjectType — xs:sequence of 22 elements.
    PDF: §4.3 (page 22-31, Abb. 4)

    Largest single entity in eCH-0129. 2 required fields (status, description),
    20 optional. 8 date fields share minInclusive=2000-01-01 constraint.

    Fields (in XSD order):
    - constructionProjectIdentification: constructionProjectIdentificationType,
      minOccurs="0"
    - typeOfConstructionProject: typeOfConstructionProjectType enum, minOccurs="0"
    - constructionLocalisation: constructionLocalisationType, minOccurs="0"
    - typeOfPermit: typeOfPermitType enum, minOccurs="0"
    - buildingPermitIssueDate: buildingPermitIssueDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - projectAnnouncementDate: projectAnnouncementDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - constructionAuthorisationDeniedDate:
      constructionAuthorisationDeniedDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - projectStartDate: projectStartDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - projectCompletionDate: projectCompletionDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - projectSuspensionDate: projectSuspensionDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - withdrawalDate: withdrawalDateType (xs:date ≥2000-01-01), minOccurs="0"
    - nonRealisationDate: nonRealisationDateType (xs:date ≥2000-01-01),
      minOccurs="0"
    - totalCostsOfProject: totalCostsOfProjectType (nonNegativeInteger,
      1000–999999999000), minOccurs="0"
    - status: projectStatusType enum (REQUIRED)
    - typeOfClient: typeOfClientType enum, minOccurs="0"
    - typeOfConstruction: typeOfConstructionType enum, minOccurs="0"
    - description: constructionProjectDescriptionType (xs:token, 3–1000)
      (REQUIRED)
    - durationOfConstructionPhase: durationOfConstructionPhaseType
      (nonNegativeInteger, 1–999), minOccurs="0"
    - numberOfConcernedBuildings: numberOfConcernedBuildingsType
      (nonNegativeInteger, 1–999), minOccurs="0"
    - numberOfConcernedDwellings: numberOfConcernedDwellingsType
      (nonNegativeInteger, 1–999), minOccurs="0"
    - projectFreeText: freeTextType (xs:token, 1–32), minOccurs="0",
      maxOccurs="2"
    - municipality: eCH-0007:swissAndFlMunicipalityType, minOccurs="0",
      maxOccurs="unbounded" (wrapper pattern)
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'constructionProject'

    construction_project_identification: Optional[
        ECH0129ConstructionProjectIdentification
    ] = xml_field('constructionProjectIdentification', default=None)
    type_of_construction_project: Optional[TypeOfConstructionProject] = xml_field(
        'typeOfConstructionProject', default=None
    )
    construction_localisation: Optional[
        ECH0129ConstructionLocalisation
    ] = xml_field('constructionLocalisation', default=None)
    type_of_permit: Optional[TypeOfPermit] = xml_field(
        'typeOfPermit', default=None
    )
    building_permit_issue_date: Optional[date] = xml_field(
        'buildingPermitIssueDate', default=None
    )
    project_announcement_date: Optional[date] = xml_field(
        'projectAnnouncementDate', default=None
    )
    construction_authorisation_denied_date: Optional[date] = xml_field(
        'constructionAuthorisationDeniedDate', default=None
    )
    project_start_date: Optional[date] = xml_field(
        'projectStartDate', default=None
    )
    project_completion_date: Optional[date] = xml_field(
        'projectCompletionDate', default=None
    )
    project_suspension_date: Optional[date] = xml_field(
        'projectSuspensionDate', default=None
    )
    withdrawal_date: Optional[date] = xml_field(
        'withdrawalDate', default=None
    )
    non_realisation_date: Optional[date] = xml_field(
        'nonRealisationDate', default=None
    )
    total_costs_of_project: Optional[int] = xml_field(
        'totalCostsOfProject', default=None, ge=1000, le=999999999000
    )
    status: ProjectStatus = xml_field('status')
    type_of_client: Optional[TypeOfClient] = xml_field(
        'typeOfClient', default=None
    )
    type_of_construction: Optional[TypeOfConstruction] = xml_field(
        'typeOfConstruction', default=None
    )
    description: str = xml_field('description', min_length=3, max_length=1000)
    duration_of_construction_phase: Optional[int] = xml_field(
        'durationOfConstructionPhase', default=None, ge=1, le=999
    )
    number_of_concerned_buildings: Optional[int] = xml_field(
        'numberOfConcernedBuildings', default=None, ge=1, le=999
    )
    number_of_concerned_dwellings: Optional[int] = xml_field(
        'numberOfConcernedDwellings', default=None, ge=1, le=999
    )
    project_free_text: list[str] = xml_field(
        'projectFreeText', default_factory=list, is_list=True
    )
    municipality: list[ECH0007v6SwissAndFLMunicipality] = xml_field(
        'municipality', default_factory=list,
        wrapper=True, child_ns=NS.ECH0007_V6, is_list=True
    )

    @field_validator(
        'building_permit_issue_date', 'project_announcement_date',
        'construction_authorisation_denied_date', 'project_start_date',
        'project_completion_date', 'project_suspension_date',
        'withdrawal_date', 'non_realisation_date',
    )
    @classmethod
    def validate_project_date(cls, v: Optional[date]) -> Optional[date]:
        """All project date types have XSD minInclusive=2000-01-01."""
        if v is not None and v < _MIN_PROJECT_DATE:
            raise ValueError(
                f"Project date must be >= 2000-01-01, got: {v}"
            )
        return v

    @field_validator('project_free_text')
    @classmethod
    def validate_free_text_list(cls, v: list[str]) -> list[str]:
        """XSD: projectFreeText maxOccurs="2", freeTextType 1–32 chars."""
        if len(v) > 2:
            raise ValueError(
                f"projectFreeText maxOccurs=2, got {len(v)} entries"
            )
        for i, text in enumerate(v):
            if len(text) < 1 or len(text) > 32:
                raise ValueError(
                    f"projectFreeText[{i}] must be 1–32 chars, "
                    f"got {len(text)} chars"
                )
        return v
