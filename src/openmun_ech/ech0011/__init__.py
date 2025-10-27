"""eCH-0011 Person Basic Data component.

Exports versioned person data models and enumerations.
"""

from openmun_ech.ech0011.v8 import (
    ECH0011SwissMunicipalityWithoutBFS,
    ECH0011ForeignerName,
    ECH0011NameData,
    ECH0011GeneralPlace,
    ECH0011BirthData,
    ECH0011ReligionData,
    ECH0011SeparationData,
    ECH0011MaritalData,
    ECH0011MaritalDataRestrictedMarriage,
    ECH0011MaritalDataRestrictedPartnership,
    ECH0011MaritalDataRestrictedDivorce,
    ECH0011MaritalDataRestrictedUndoMarried,
    ECH0011MaritalDataRestrictedUndoPartnership,
    ECH0011MaritalDataRestrictedMaritalStatusPartner,
    ECH0011CountryInfo,
    ECH0011NationalityData,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathPeriod,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011PartnerIdOrganisation,
    ECH0011DestinationType,
    ECH0011DwellingAddress,
    ECH0011ResidenceData,
    ECH0011MainResidence,
    ECH0011SecondaryResidence,
    ECH0011OtherResidence,
    ECH0011Person,
    ECH0011ReportedPerson,
)

from openmun_ech.ech0011.enums import (
    Sex,
    ReligionCode,
    MaritalStatus,
    SeparationType,
    CancelationReason,
    PartnershipAbolition,
    NationalityStatus,
    LanguageCode,
    TypeOfResidence,
    TypeOfHousehold,
    FederalRegister,
    YesNo,
)

# Import dependencies needed for forward references
from openmun_ech.ech0010 import ECH0010SwissAddressInformation  # noqa: F401

# Rebuild models to resolve forward references
ECH0011DwellingAddress.model_rebuild()
ECH0011MainResidence.model_rebuild()
ECH0011SecondaryResidence.model_rebuild()
ECH0011OtherResidence.model_rebuild()
ECH0011Person.model_rebuild()
ECH0011ReportedPerson.model_rebuild()

__all__ = [
    # Models
    'ECH0011SwissMunicipalityWithoutBFS',
    'ECH0011ForeignerName',
    'ECH0011NameData',
    'ECH0011GeneralPlace',
    'ECH0011BirthData',
    'ECH0011ReligionData',
    'ECH0011SeparationData',
    'ECH0011MaritalData',
    'ECH0011MaritalDataRestrictedMarriage',
    'ECH0011MaritalDataRestrictedPartnership',
    'ECH0011MaritalDataRestrictedDivorce',
    'ECH0011MaritalDataRestrictedUndoMarried',
    'ECH0011MaritalDataRestrictedUndoPartnership',
    'ECH0011MaritalDataRestrictedMaritalStatusPartner',
    'ECH0011CountryInfo',
    'ECH0011NationalityData',
    'ECH0011PlaceOfOrigin',
    'ECH0011ResidencePermitData',
    'ECH0011DeathPeriod',
    'ECH0011DeathData',
    'ECH0011ContactData',
    'ECH0011PartnerIdOrganisation',
    'ECH0011DestinationType',
    'ECH0011DwellingAddress',
    'ECH0011ResidenceData',
    'ECH0011MainResidence',
    'ECH0011SecondaryResidence',
    'ECH0011OtherResidence',
    'ECH0011Person',
    'ECH0011ReportedPerson',
    # Enums
    'Sex',
    'ReligionCode',
    'MaritalStatus',
    'SeparationType',
    'CancelationReason',
    'PartnershipAbolition',
    'NationalityStatus',
    'LanguageCode',
    'TypeOfResidence',
    'TypeOfHousehold',
    'FederalRegister',
    'YesNo',
]
