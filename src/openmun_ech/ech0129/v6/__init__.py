"""eCH-0129 v6.0.0 Objektwesen — all ECHModel classes.

60 classes across 11 submodules:
  authority_person (7), base_types (11), building (3), cadastral (5),
  construction (4), dwelling (3), entrance (7), estimation (4),
  insurance (5), realestate (4), street_locality (7).

20 root element types (matching XSD xs:element declarations):
  building, buildingOnly, buildingEntrance, buildingEntranceOnly,
  constructionProject, dwelling, realestate, locality, fiscalOwnership,
  area, insuranceObject, estimationObject, street, right, cadastralMap,
  cadastralSurveyorRemark, placeName, coveringAreaOfSDR,
  partialAreaOfBuilding, kindOfConstructionWork.
"""

from .authority_person import (
    ECH0129BuildingAuthority,
    ECH0129BuildingAuthorityOnly,
    ECH0129Email,
    ECH0129IdentificationChoice,
    ECH0129Person,
    ECH0129PersonOnly,
    ECH0129Phone,
)
from .base_types import (
    ECH0129BuildingDate,
    ECH0129BuildingVolume,
    ECH0129Contact,
    ECH0129Coordinates,
    ECH0129DatePartiallyKnown,
    ECH0129DateRange,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129NamedId,
    ECH0129NamedMetaData,
    ECH0129PersonIdentification,
)
from .construction import (
    ECH0129ConstructionLocalisation,
    ECH0129ConstructionProject,
    ECH0129ConstructionProjectIdentification,
    ECH0129KindOfConstructionWork,
)
from .dwelling import (
    ECH0129Dwelling,
    ECH0129DwellingIdentification,
    ECH0129DwellingUsage,
)
from .building import (
    ECH0129Building,
    ECH0129BuildingIdentification,
    ECH0129BuildingOnly,
)
from .entrance import (
    ECH0129AddressStreetDescription,
    ECH0129AddressStreetEntry,
    ECH0129BuildingAddress,
    ECH0129BuildingAddressLight,
    ECH0129BuildingEntrance,
    ECH0129BuildingEntranceIdentification,
    ECH0129BuildingEntranceOnly,
)
from .cadastral import (
    ECH0129CadastralMap,
    ECH0129CadastralSurveyorRemark,
    ECH0129CoveringAreaOfSDR,
    ECH0129PartialAreaOfBuilding,
    ECH0129Right,
)
from .estimation import (
    ECH0129EstimationObject,
    ECH0129EstimationObjectOnly,
    ECH0129EstimationValue,
    ECH0129Value,
)
from .insurance import (
    ECH0129InsuranceObject,
    ECH0129InsuranceObjectOnly,
    ECH0129InsuranceSum,
    ECH0129InsuranceValue,
    ECH0129InsuranceVolume,
)
from .realestate import (
    ECH0129Area,
    ECH0129FiscalOwnership,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
)
from .street_locality import (
    ECH0129Locality,
    ECH0129LocalityName,
    ECH0129PlaceName,
    ECH0129Street,
    ECH0129StreetDescription,
    ECH0129StreetDescriptionEntry,
    ECH0129StreetSection,
)

__all__ = [
    'ECH0129AddressStreetDescription',
    'ECH0129AddressStreetEntry',
    'ECH0129Area',
    'ECH0129Building',
    'ECH0129BuildingAuthority',
    'ECH0129BuildingAuthorityOnly',
    'ECH0129BuildingAddress',
    'ECH0129BuildingAddressLight',
    'ECH0129BuildingDate',
    'ECH0129BuildingEntrance',
    'ECH0129BuildingEntranceIdentification',
    'ECH0129BuildingEntranceOnly',
    'ECH0129BuildingIdentification',
    'ECH0129BuildingOnly',
    'ECH0129BuildingVolume',
    'ECH0129CadastralMap',
    'ECH0129CadastralSurveyorRemark',
    'ECH0129ConstructionLocalisation',
    'ECH0129ConstructionProject',
    'ECH0129ConstructionProjectIdentification',
    'ECH0129Contact',
    'ECH0129Coordinates',
    'ECH0129CoveringAreaOfSDR',
    'ECH0129DatePartiallyKnown',
    'ECH0129DateRange',
    'ECH0129Dwelling',
    'ECH0129DwellingIdentification',
    'ECH0129DwellingUsage',
    'ECH0129Email',
    'ECH0129EstimationObject',
    'ECH0129EstimationObjectOnly',
    'ECH0129EstimationValue',
    'ECH0129FiscalOwnership',
    'ECH0129Heating',
    'ECH0129HotWater',
    'ECH0129IdentificationChoice',
    'ECH0129InsuranceObject',
    'ECH0129InsuranceObjectOnly',
    'ECH0129InsuranceSum',
    'ECH0129InsuranceValue',
    'ECH0129InsuranceVolume',
    'ECH0129KindOfConstructionWork',
    'ECH0129Locality',
    'ECH0129LocalityName',
    'ECH0129NamedId',
    'ECH0129NamedMetaData',
    'ECH0129PartialAreaOfBuilding',
    'ECH0129Person',
    'ECH0129PersonIdentification',
    'ECH0129PersonOnly',
    'ECH0129Phone',
    'ECH0129PlaceName',
    'ECH0129Realestate',
    'ECH0129RealestateIdentification',
    'ECH0129Right',
    'ECH0129Street',
    'ECH0129StreetDescription',
    'ECH0129StreetDescriptionEntry',
    'ECH0129StreetSection',
    'ECH0129Value',
]
