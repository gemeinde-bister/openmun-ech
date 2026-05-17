"""eCH-0020 v3.0 — Person Types."""

from typing import Optional, List
from datetime import date
from pydantic import model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0007 import ECH0007SwissMunicipality
from openmun_ech.ech0011 import (
    ECH0011ReligionData,
    ECH0011NationalityData,
    ECH0011ResidencePermitData,
    ECH0011DeathData,
    ECH0011ContactData,
    ECH0011DwellingAddress,
    ECH0011DestinationType,
    FederalRegister,
)
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
    ECH0021MaritalRelationship,
    ECH0021MatrimonialInheritanceArrangementData,
)
from openmun_ech.ech0044 import ECH0044PersonIdentification

from .info_types import (
    ECH0020NameInfo,
    ECH0020BirthInfo,
    ECH0020MaritalInfo,
    ECH0020PlaceOfOriginInfo,
)


# ============================================================================
# INFOSTAR PERSON TYPE
# ============================================================================

class ECH0020InfostarPerson(ECHModel):
    """Person data for INFOSTAR (federal population register).

    XSD: infostarPersonType (eCH-0020-3-0.xsd lines 96-109)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'infostarPerson'

    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')
    birth_info: ECH0020BirthInfo = xml_field('birthInfo')
    marital_info: ECH0020MaritalInfo = xml_field('maritalInfo')
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    place_of_origin_info: Optional[List[ECH0020PlaceOfOriginInfo]] = xml_field(
        'placeOfOriginInfo', default=None, is_list=True,
    )
    death_data: Optional[ECH0011DeathData] = xml_field(
        'deathData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )


# ============================================================================
# BASE DELIVERY PERSON TYPE (21 fields)
# ============================================================================

class ECH0020BaseDeliveryPerson(ECHModel):
    """Complete person data for base deliveries.

    XSD: baseDeliveryPersonType (eCH-0020-3-0.xsd lines 113-140)
    Field order follows XSD xs:sequence (serialization order).
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'baseDeliveryPerson'

    # Required fields
    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')
    birth_info: ECH0020BirthInfo = xml_field('birthInfo')
    religion_data: ECH0011ReligionData = xml_field(
        'religionData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    marital_info: ECH0020MaritalInfo = xml_field('maritalInfo')
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # Optional fields (XSD sequence order from production to_xml)
    death_data: Optional[ECH0011DeathData] = xml_field(
        'deathData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    contact_data: Optional[ECH0011ContactData] = xml_field(
        'contactData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = xml_field(
        'personAdditionalData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = xml_field(
        'politicalRightData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )

    # XSD CHOICE: placeOfOriginInfo (Swiss, 1-n) OR residencePermitData (foreign)
    place_of_origin_info: Optional[List[ECH0020PlaceOfOriginInfo]] = xml_field(
        'placeOfOriginInfo', default=None, is_list=True,
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = xml_field(
        'residencePermitData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # lockData required, after CHOICE in XSD
    lock_data: ECH0021LockData = xml_field(
        'lockData', wrapper=True, child_ns=NS.ECH0021_V7,
    )

    # Remaining optional fields
    job_data: Optional[ECH0021JobData] = xml_field(
        'jobData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = xml_field(
        'maritalRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = xml_field(
        'parentalRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = xml_field(
        'guardianRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = xml_field(
        'armedForcesData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = xml_field(
        'civilDefenseData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    fire_service_data: Optional[ECH0021FireServiceData] = xml_field(
        'fireServiceData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = xml_field(
        'healthInsuranceData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = xml_field(
        'matrimonialInheritanceArrangementData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BaseDeliveryPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData."""
        has_origin = self.place_of_origin_info is not None and len(self.place_of_origin_info) > 0
        has_permit = self.residence_permit_data is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "baseDeliveryPersonType requires either placeOfOriginInfo (Swiss citizen) "
                "OR residencePermitData (foreign national)"
            )
        if has_origin and has_permit:
            raise ValueError(
                "baseDeliveryPersonType allows either placeOfOriginInfo OR residencePermitData, "
                f"but both were provided (origins={len(self.place_of_origin_info)}, permit=yes)"
            )

        return self


# ============================================================================
# BASE DELIVERY RESTRICTED MOVE-IN PERSON TYPE (20 fields, no deathData)
# ============================================================================

class ECH0020BaseDeliveryRestrictedMoveInPerson(ECHModel):
    """Restricted person data for move-in events (no deathData).

    XSD restriction of baseDeliveryPersonType — deceased persons do not move in.
    XSD: baseDeliveryRestrictedMoveInPersonType (eCH-0020-3-0.xsd lines 141-169)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'baseDeliveryRestrictedMoveInPerson'

    # Required fields
    person_identification: ECH0044PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0044_V4,
    )
    name_info: ECH0020NameInfo = xml_field('nameInfo')
    birth_info: ECH0020BirthInfo = xml_field('birthInfo')
    religion_data: ECH0011ReligionData = xml_field(
        'religionData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    marital_info: ECH0020MaritalInfo = xml_field('maritalInfo')
    nationality_data: ECH0011NationalityData = xml_field(
        'nationalityData', wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # NOTE: NO deathData field (deceased don't move in)

    # Optional fields (XSD sequence order)
    contact_data: Optional[ECH0011ContactData] = xml_field(
        'contactData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = xml_field(
        'personAdditionalData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = xml_field(
        'politicalRightData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )

    # XSD CHOICE
    place_of_origin_info: Optional[List[ECH0020PlaceOfOriginInfo]] = xml_field(
        'placeOfOriginInfo', default=None, is_list=True,
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = xml_field(
        'residencePermitData', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # lockData required
    lock_data: ECH0021LockData = xml_field(
        'lockData', wrapper=True, child_ns=NS.ECH0021_V7,
    )

    # Remaining optional fields
    job_data: Optional[ECH0021JobData] = xml_field(
        'jobData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = xml_field(
        'maritalRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = xml_field(
        'parentalRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = xml_field(
        'guardianRelationship', default=None, wrapper=True, child_ns=NS.ECH0021_V7, is_list=True,
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = xml_field(
        'armedForcesData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = xml_field(
        'civilDefenseData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    fire_service_data: Optional[ECH0021FireServiceData] = xml_field(
        'fireServiceData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = xml_field(
        'healthInsuranceData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = xml_field(
        'matrimonialInheritanceArrangementData', default=None, wrapper=True, child_ns=NS.ECH0021_V7,
    )

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BaseDeliveryRestrictedMoveInPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData."""
        has_origin = self.place_of_origin_info is not None and len(self.place_of_origin_info) > 0
        has_permit = self.residence_permit_data is not None

        if not has_origin and not has_permit:
            raise ValueError(
                "baseDeliveryRestrictedMoveInPersonType requires either placeOfOriginInfo "
                "(Swiss citizen) OR residencePermitData (foreign national)"
            )
        if has_origin and has_permit:
            raise ValueError(
                "baseDeliveryRestrictedMoveInPersonType allows either placeOfOriginInfo OR "
                f"residencePermitData, but both were provided (origins={len(self.place_of_origin_info)}, permit=yes)"
            )

        return self


# ============================================================================
# REPORTING MUNICIPALITY TYPES
# ============================================================================

class ECH0020ReportingMunicipality(ECHModel):
    """Municipality reporting data with residence and movement information.

    XSD: reportingMunicipalityType (eCH-0020-3-0.xsd lines 455-467)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # Optional fields
    arrival_date: Optional[date] = xml_field('arrivalDate', default=None)
    comes_from: Optional[ECH0011DestinationType] = xml_field(
        'comesFrom', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: Optional[ECH0011DwellingAddress] = xml_field(
        'dwellingAddress', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    departure_date: Optional[date] = xml_field('departureDate', default=None)
    goes_to: Optional[ECH0011DestinationType] = xml_field(
        'goesTo', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipality':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityType requires either reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityType allows either reportingMunicipality OR federalRegister, "
                "but both were provided"
            )

        return self


class ECH0020ReportingMunicipalityRestrictedBaseMain(ECHModel):
    """Restricted reporting municipality for base delivery main residence.

    XSD: reportingMunicipalityRestrictedBaseMainType (eCH-0020-3-0.xsd lines 468-484)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # Required fields
    arrival_date: date = xml_field('arrivalDate')
    comes_from: Optional[ECH0011DestinationType] = xml_field(
        'comesFrom', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    departure_date: Optional[date] = xml_field('departureDate', default=None)
    goes_to: Optional[ECH0011DestinationType] = xml_field(
        'goesTo', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedBaseMain':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseMainType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseMainType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self


class ECH0020ReportingMunicipalityRestrictedBaseSecondary(ECHModel):
    """Restricted reporting municipality for base delivery secondary residence.

    XSD: reportingMunicipalityRestrictedBaseSecondaryType (eCH-0020-3-0.xsd lines 485-501)
    Differences: arrivalDate, comesFrom, dwellingAddress all REQUIRED.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'reportingMunicipality'

    # XSD CHOICE
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )

    # Required fields (all required in this restriction)
    arrival_date: date = xml_field('arrivalDate')
    comes_from: ECH0011DestinationType = xml_field(
        'comesFrom', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    departure_date: Optional[date] = xml_field('departureDate', default=None)
    goes_to: Optional[ECH0011DestinationType] = xml_field(
        'goesTo', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    @model_validator(mode='after')
    def validate_municipality_or_register_choice(self) -> 'ECH0020ReportingMunicipalityRestrictedBaseSecondary':
        """Validate XSD CHOICE: exactly ONE of reportingMunicipality OR federalRegister."""
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None

        if not has_municipality and not has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseSecondaryType requires either "
                "reportingMunicipality OR federalRegister"
            )
        if has_municipality and has_register:
            raise ValueError(
                "reportingMunicipalityRestrictedBaseSecondaryType allows either "
                "reportingMunicipality OR federalRegister, but both were provided"
            )

        return self


# ============================================================================
# RESIDENCE DATA TYPES (inline complexType extensions for eventBaseDelivery)
# ============================================================================

class ECH0020HasMainResidence(ECHModel):
    """Main residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseMainType with optional secondary residences.
    XSD: Inline extension in eventBaseDelivery (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'hasMainResidence'

    # Base fields from reportingMunicipalityRestrictedBaseMainType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )
    arrival_date: date = xml_field('arrivalDate')
    comes_from: Optional[ECH0011DestinationType] = xml_field(
        'comesFrom', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    departure_date: Optional[date] = xml_field('departureDate', default=None)
    goes_to: Optional[ECH0011DestinationType] = xml_field(
        'goesTo', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # Extension: secondary residences (0-n)
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = xml_field(
        'secondaryResidence', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5, is_list=True,
    )

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasMainResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasMainResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasMainResidence allows either reportingMunicipality OR federalRegister")
        return self


class ECH0020HasSecondaryResidence(ECHModel):
    """Secondary residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseSecondaryType with required main residence.
    XSD: Inline extension in eventBaseDelivery (eCH-0020-3-0.xsd)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'hasSecondaryResidence'

    # Base fields from reportingMunicipalityRestrictedBaseSecondaryType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = xml_field(
        'reportingMunicipality', default=None,
        wrapper=True, child_ns=NS.ECH0007_V5,
    )
    federal_register: Optional[FederalRegister] = xml_field(
        'federalRegister', default=None,
    )
    arrival_date: date = xml_field('arrivalDate')
    comes_from: ECH0011DestinationType = xml_field(
        'comesFrom', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    dwelling_address: ECH0011DwellingAddress = xml_field(
        'dwellingAddress', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    departure_date: Optional[date] = xml_field('departureDate', default=None)
    goes_to: Optional[ECH0011DestinationType] = xml_field(
        'goesTo', default=None, wrapper=True, child_ns=NS.ECH0011_V8,
    )

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = xml_field(
        'mainResidence', wrapper=True, child_ns=NS.ECH0007_V5,
    )

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasSecondaryResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasSecondaryResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasSecondaryResidence allows either reportingMunicipality OR federalRegister")
        return self
