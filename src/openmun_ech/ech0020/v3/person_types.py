"""eCH-0020 v3.0 — Person Types."""

import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

from openmun_ech.core import NS
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


# TYPE 7/89: INFOSTAR PERSON TYPE
# ============================================================================

class ECH0020InfostarPerson(BaseModel):
    """Person data structure for INFOSTAR (federal population register).

    This type is used for reporting population data to INFOSTAR, the Swiss federal
    population information system. It contains the essential person data required
    for federal register synchronization.

    XSD: infostarPersonType (eCH-0020-3-0.xsd lines 96-109)
    PDF: Unknown section (INFOSTAR reporting structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - personIdentification: Person identification (VN, local ID, etc.)
    - nameInfo: Name data with optional validation date
    - birthInfo: Birth data (extends eCH-0020 birthInfoType)
    - maritalInfo: Marital status data
    - nationalityData: Nationality/citizenship data
    - placeOfOriginInfo: Swiss place(s) of origin (0-n, for Swiss citizens)
    - deathData: Death information (optional)

    Note: This type has no XSD CHOICE constraints - all fields are in sequence.
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data (extends eCH-0020 birthInfoType inline)'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # Optional fields
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (for Swiss citizens, 0-n)'
    )
    death_data: Optional[ECH0011DeathData] = Field(
        None,
        alias='deathData',
        description='Death information (optional)'
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'infostarPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'infostarPerson')

        Returns:
            XML element with all person data for INFOSTAR
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # 1. personIdentification (required, eCH-0044/4 namespace)
        self.person_identification.to_xml(
            parent=elem,
            namespace=NS.ECH0044_V4,
            element_name='personIdentification'
        )

        # 2. nameInfo (required, eCH-0020/3 namespace)
        self.name_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='nameInfo'
        )

        # 3. birthInfo (required, eCH-0020/3 namespace)
        # XSD has inline complexType extending birthInfoType, but with no additions
        # So we just serialize as regular birthInfo
        self.birth_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='birthInfo'
        )

        # 4. maritalInfo (required, eCH-0020/3 namespace)
        self.marital_info.to_xml(
            parent=elem,
            namespace=namespace,
            element_name='maritalInfo'
        )

        # 5. nationalityData (required, eCH-0011/8 namespace)
        self.nationality_data.to_xml(
            parent=elem,
            namespace=NS.ECH0011_V8,
            element_name='nationalityData'
        )

        # 6. placeOfOriginInfo (optional, 0-n, eCH-0020/3 namespace)
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(
                    parent=elem,
                    namespace=namespace,
                    element_name='placeOfOriginInfo'
                )

        # 7. deathData (optional, eCH-0011/8 namespace)
        if self.death_data:
            self.death_data.to_xml(
                parent=elem,
                namespace=NS.ECH0011_V8,
                element_name='deathData'
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020InfostarPerson':
        """Parse from XML element.

        Args:
            element: XML element containing infostarPerson data

        Returns:
            Parsed ECH0020InfostarPerson instance
        """
        # Define namespaces
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_044 = NS.ECH0044_V4

        # 1. personIdentification (required)
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("infostarPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        # 2. nameInfo (required)
        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("infostarPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        # 3. birthInfo (required)
        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("infostarPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        # 4. maritalInfo (required)
        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("infostarPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        # 5. nationalityData (required)
        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("infostarPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        # 6. placeOfOriginInfo (optional, 0-n)
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [
                ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems
            ]

        # 7. deathData (optional)
        death_data = None
        death_elem = element.find(f'{{{ns_020}}}deathData')
        if death_elem is not None:
            death_data = ECH0011DeathData.from_xml(death_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            death_data=death_data
        )


# ============================================================================
# TYPE 8/89: BASE DELIVERY PERSON TYPE
# ============================================================================

class ECH0020BaseDeliveryPerson(BaseModel):
    """Complete person data structure for base deliveries.

    Base deliveries are complete snapshots of a municipality's population register,
    sent to INFOSTAR/cantonal systems. This type contains all person data including
    demographics, relationships, military service, health insurance, etc.

    XSD: baseDeliveryPersonType (eCH-0020-3-0.xsd lines 113-140)
    PDF: Unknown section (base delivery structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields (21 total):
    REQUIRED:
    - personIdentification: Person identification (VN, local ID)
    - nameInfo: Name data with validation date
    - birthInfo: Birth data
    - religionData: Religion/confession
    - maritalInfo: Marital status
    - nationalityData: Nationality/citizenship
    - lockData: Data/paper lock information
    - CHOICE: placeOfOriginInfo (Swiss, 1-n) OR residencePermitData (foreign)

    OPTIONAL:
    - deathData: Death information
    - contactData: Contact information (phone, email)
    - personAdditionalData: Additional person data
    - politicalRightData: Political rights data
    - jobData: Employment data
    - maritalRelationship: Marital relationship details
    - parentalRelationship: Parental relationships (0-n)
    - guardianRelationship: Guardian relationships (0-n)
    - armedForcesData: Military service data
    - civilDefenseData: Civil defense service
    - fireServiceData: Fire service data
    - healthInsuranceData: Health insurance
    - matrimonialInheritanceArrangementData: Matrimonial regime/inheritance
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data per eCH-0020'
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='Religion/confession data per eCH-0011'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # XSD CHOICE: placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    # Note: placeOfOriginInfo is unbounded (1-n for Swiss citizens)
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (1-n for Swiss citizens)'
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Residence permit data for foreign nationals'
    )

    # lockData is REQUIRED (comes after CHOICE in XSD)
    lock_data: ECH0021LockData = Field(
        ...,
        alias='lockData',
        description='Data lock and paper lock information'
    )

    # Optional fields (all minOccurs=0)
    death_data: Optional[ECH0011DeathData] = Field(
        None,
        alias='deathData',
        description='Death information (if deceased)'
    )
    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description='Contact information (phone, email)'
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description='Additional person data per eCH-0021'
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = Field(
        None,
        alias='politicalRightData',
        description='Political rights data (v7-only field)'
    )
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Employment/occupation data'
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Marital relationship details'
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description='Parental relationships (0-n)'
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = Field(
        None,
        alias='guardianRelationship',
        description='Guardian relationships (0-n)'
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = Field(
        None,
        alias='armedForcesData',
        description='Military service data'
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = Field(
        None,
        alias='civilDefenseData',
        description='Civil defense service data'
    )
    fire_service_data: Optional[ECH0021FireServiceData] = Field(
        None,
        alias='fireServiceData',
        description='Fire service data'
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description='Health insurance information'
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = Field(
        None,
        alias='matrimonialInheritanceArrangementData',
        description='Matrimonial regime and inheritance arrangement'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_origin_or_permit_choice(self) -> 'ECH0020BaseDeliveryPerson':
        """Validate XSD CHOICE: exactly ONE of placeOfOriginInfo OR residencePermitData.

        XSD constraint (lines 123-127):
        <xs:choice>
            <xs:element name="placeOfOriginInfo" type="eCH-0020:placeOfOriginInfoType" maxOccurs="unbounded"/>
            <xs:element name="residencePermitData" type="eCH-0011:residencePermitDataType"/>
        </xs:choice>
        """
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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'baseDeliveryPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'baseDeliveryPerson')

        Returns:
            XML element with complete person data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

        # 1. personIdentification (required, eCH-0044/4)
        # Create wrapper element in parent namespace
        personIdentification_wrapper = ET.SubElement(elem, f'{{{namespace}}}personIdentification')
        personIdentification_content = self.person_identification.to_xml(namespace=ns_044)
        for child in personIdentification_content:
            personIdentification_wrapper.append(child)

        # 2. nameInfo (required, eCH-0020/3)
        self.name_info.to_xml(parent=elem, namespace=namespace, element_name='nameInfo')

        # 3. birthInfo (required, eCH-0020/3)
        self.birth_info.to_xml(parent=elem, namespace=namespace, element_name='birthInfo')

        # 4. religionData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData',
            wrapper_namespace=namespace
        )

        # 5. maritalInfo (required, eCH-0020/3)
        self.marital_info.to_xml(parent=elem, namespace=namespace, element_name='maritalInfo')

        # 6. nationalityData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData',
            wrapper_namespace=namespace
        )

        # 7. deathData (optional, eCH-0011/8)
        if self.death_data:
            # Create wrapper element in parent namespace
            deathData_wrapper = ET.SubElement(elem, f'{{{namespace}}}deathData')
            deathData_content = self.death_data.to_xml(namespace=ns_011)
            for child in deathData_content:
                deathData_wrapper.append(child)

        # 8. contactData (optional, eCH-0011/8)
        if self.contact_data:
            # Create wrapper element in parent namespace
            contactData_wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            contactData_content = self.contact_data.to_xml(namespace=ns_011)
            for child in contactData_content:
                contactData_wrapper.append(child)

        # 9. personAdditionalData (optional, eCH-0021/7)
        if self.person_additional_data:
            # Create wrapper element in parent namespace
            personAdditionalData_wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            personAdditionalData_content = self.person_additional_data.to_xml(namespace=ns_021)
            for child in personAdditionalData_content:
                personAdditionalData_wrapper.append(child)

        # 10. politicalRightData (optional, eCH-0021/7)
        if self.political_right_data:
            # Create wrapper element in parent namespace
            politicalRightData_wrapper = ET.SubElement(elem, f'{{{namespace}}}politicalRightData')
            politicalRightData_content = self.political_right_data.to_xml(namespace=ns_021)
            for child in politicalRightData_content:
                politicalRightData_wrapper.append(child)

        # 11. CHOICE: placeOfOriginInfo (unbounded) OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace, element_name='placeOfOriginInfo')
        elif self.residence_permit_data:
            # Wrapper in ns_020, content in ns_011
            self.residence_permit_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='residencePermitData',
                wrapper_namespace=namespace
            )

        # 12. lockData (required, eCH-0021/7)
        # Create wrapper element in parent namespace
        lockData_wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        lockData_content = self.lock_data.to_xml(namespace=ns_021)
        for child in lockData_content:
            lockData_wrapper.append(child)

        # 13. jobData (optional, eCH-0021/7)
        if self.job_data:
            # Create wrapper element in parent namespace
            jobData_wrapper = ET.SubElement(elem, f'{{{namespace}}}jobData')
            jobData_content = self.job_data.to_xml(namespace=ns_021)
            for child in jobData_content:
                jobData_wrapper.append(child)

        # 14. maritalRelationship (optional, eCH-0021/7)
        if self.marital_relationship:
            # Create wrapper element in parent namespace
            maritalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalRelationship')
            maritalRelationship_content = self.marital_relationship.to_xml(namespace=ns_021)
            for child in maritalRelationship_content:
                maritalRelationship_wrapper.append(child)

        # 15. parentalRelationship (optional, 0-n, eCH-0021/7)
        if self.parental_relationship:
            for relationship in self.parental_relationship:
                # Create wrapper element

                parentalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')

                parentalRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in parentalRelationship_content:

                    parentalRelationship_wrapper.append(child)

        # 16. guardianRelationship (optional, 0-n, eCH-0021/7)
        if self.guardian_relationship:
            for relationship in self.guardian_relationship:
                # Create wrapper element

                guardianRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}guardianRelationship')

                guardianRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in guardianRelationship_content:

                    guardianRelationship_wrapper.append(child)

        # 17. armedForcesData (optional, eCH-0021/7)
        if self.armed_forces_data:
            # Create wrapper element in parent namespace
            armedForcesData_wrapper = ET.SubElement(elem, f'{{{namespace}}}armedForcesData')
            armedForcesData_content = self.armed_forces_data.to_xml(namespace=ns_021)
            for child in armedForcesData_content:
                armedForcesData_wrapper.append(child)

        # 18. civilDefenseData (optional, eCH-0021/7)
        if self.civil_defense_data:
            # Create wrapper element in parent namespace
            civilDefenseData_wrapper = ET.SubElement(elem, f'{{{namespace}}}civilDefenseData')
            civilDefenseData_content = self.civil_defense_data.to_xml(namespace=ns_021)
            for child in civilDefenseData_content:
                civilDefenseData_wrapper.append(child)

        # 19. fireServiceData (optional, eCH-0021/7)
        if self.fire_service_data:
            # Create wrapper element in parent namespace
            fireServiceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}fireServiceData')
            fireServiceData_content = self.fire_service_data.to_xml(namespace=ns_021)
            for child in fireServiceData_content:
                fireServiceData_wrapper.append(child)

        # 20. healthInsuranceData (optional, eCH-0021/7)
        if self.health_insurance_data:
            # Create wrapper element in parent namespace
            healthInsuranceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            healthInsuranceData_content = self.health_insurance_data.to_xml(namespace=ns_021)
            for child in healthInsuranceData_content:
                healthInsuranceData_wrapper.append(child)

        # 21. matrimonialInheritanceArrangementData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.matrimonial_inheritance_arrangement_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangementData')
            content = self.matrimonial_inheritance_arrangement_data.to_xml(namespace=ns_021)
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BaseDeliveryPerson':
        """Parse from XML element.

        Args:
            element: XML element containing baseDeliveryPerson data

        Returns:
            Parsed ECH0020BaseDeliveryPerson instance
        """
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

        # Required fields
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("baseDeliveryPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        religion_elem = element.find(f'{{{ns_020}}}religionData')
        if religion_elem is None:
            raise ValueError("baseDeliveryPersonType requires religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("baseDeliveryPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("baseDeliveryPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        lock_elem = element.find(f'{{{ns_020}}}lockData')
        if lock_elem is None:
            raise ValueError("baseDeliveryPersonType requires lockData")
        lock_data = ECH0021LockData.from_xml(lock_elem)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems]

        residence_permit_data = None
        permit_elem = element.find(f'{{{ns_020}}}residencePermitData')
        if permit_elem is not None:
            residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem)

        # Optional fields
        death_data = None
        death_elem = element.find(f'{{{ns_020}}}deathData')
        if death_elem is not None:
            death_data = ECH0011DeathData.from_xml(death_elem)

        contact_data = None
        contact_elem = element.find(f'{{{ns_020}}}contactData')
        if contact_elem is not None:
            contact_data = ECH0011ContactData.from_xml(contact_elem)

        person_additional_data = None
        additional_elem = element.find(f'{{{ns_020}}}personAdditionalData')
        if additional_elem is not None:
            person_additional_data = ECH0021PersonAdditionalData.from_xml(additional_elem)

        political_right_data = None
        political_elem = element.find(f'{{{ns_020}}}politicalRightData')
        if political_elem is not None:
            political_right_data = ECH0021PoliticalRightData.from_xml(political_elem)

        job_data = None
        job_elem = element.find(f'{{{ns_020}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        marital_relationship = None
        marital_rel_elem = element.find(f'{{{ns_020}}}maritalRelationship')
        if marital_rel_elem is not None:
            marital_relationship = ECH0021MaritalRelationship.from_xml(marital_rel_elem)

        parental_relationship = None
        parental_elems = element.findall(f'{{{ns_020}}}parentalRelationship')
        if parental_elems:
            parental_relationship = [ECH0021ParentalRelationship.from_xml(elem) for elem in parental_elems]

        guardian_relationship = None
        guardian_elems = element.findall(f'{{{ns_020}}}guardianRelationship')
        if guardian_elems:
            guardian_relationship = [ECH0021GuardianRelationship.from_xml(elem) for elem in guardian_elems]

        armed_forces_data = None
        armed_elem = element.find(f'{{{ns_020}}}armedForcesData')
        if armed_elem is not None:
            armed_forces_data = ECH0021ArmedForcesData.from_xml(armed_elem)

        civil_defense_data = None
        civil_elem = element.find(f'{{{ns_020}}}civilDefenseData')
        if civil_elem is not None:
            civil_defense_data = ECH0021CivilDefenseData.from_xml(civil_elem)

        fire_service_data = None
        fire_elem = element.find(f'{{{ns_020}}}fireServiceData')
        if fire_elem is not None:
            fire_service_data = ECH0021FireServiceData.from_xml(fire_elem)

        health_insurance_data = None
        health_elem = element.find(f'{{{ns_020}}}healthInsuranceData')
        if health_elem is not None:
            health_insurance_data = ECH0021HealthInsuranceData.from_xml(health_elem)

        matrimonial_inheritance_arrangement_data = None
        matrimonial_elem = element.find(f'{{{ns_020}}}matrimonialInheritanceArrangementData')
        if matrimonial_elem is not None:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData.from_xml(matrimonial_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            death_data=death_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            political_right_data=political_right_data,
            job_data=job_data,
            marital_relationship=marital_relationship,
            parental_relationship=parental_relationship,
            guardian_relationship=guardian_relationship,
            armed_forces_data=armed_forces_data,
            civil_defense_data=civil_defense_data,
            fire_service_data=fire_service_data,
            health_insurance_data=health_insurance_data,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
        )


# ============================================================================
# TYPE 9/89: BASE DELIVERY RESTRICTED MOVE-IN PERSON TYPE
# ============================================================================

class ECH0020BaseDeliveryRestrictedMoveInPerson(BaseModel):
    """Restricted person data structure for move-in events in base deliveries.

    This is an XSD restriction of baseDeliveryPersonType, used specifically for
    move-in event reporting. The key difference: NO deathData field (deceased
    persons do not move in).

    XSD: baseDeliveryRestrictedMoveInPersonType (eCH-0020-3-0.xsd lines 141-169)
    PDF: Unknown section (move-in event structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Note: This is an XSD restriction, so we implement as standalone class (not inheritance)
    because Pydantic restrictions don't map cleanly to Python inheritance.

    Differences from baseDeliveryPersonType:
    - NO deathData field (only difference)
    - All other 20 fields identical
    """

    # Required fields (minOccurs=1, maxOccurs=1)
    person_identification: ECH0044PersonIdentification = Field(
        ...,
        alias='personIdentification',
        description='Person identification per eCH-0044'
    )
    name_info: 'ECH0020NameInfo' = Field(
        ...,
        alias='nameInfo',
        description='Name data with optional validation date'
    )
    birth_info: 'ECH0020BirthInfo' = Field(
        ...,
        alias='birthInfo',
        description='Birth data per eCH-0020'
    )
    religion_data: ECH0011ReligionData = Field(
        ...,
        alias='religionData',
        description='Religion/confession data per eCH-0011'
    )
    marital_info: 'ECH0020MaritalInfo' = Field(
        ...,
        alias='maritalInfo',
        description='Marital status data'
    )
    nationality_data: ECH0011NationalityData = Field(
        ...,
        alias='nationalityData',
        description='Nationality/citizenship data per eCH-0011'
    )

    # NOTE: deathData field is REMOVED in this restriction (deceased don't move in)

    # XSD CHOICE: placeOfOriginInfo (Swiss) OR residencePermitData (foreign)
    place_of_origin_info: Optional[List['ECH0020PlaceOfOriginInfo']] = Field(
        None,
        alias='placeOfOriginInfo',
        description='Swiss place(s) of origin (1-n for Swiss citizens)'
    )
    residence_permit_data: Optional[ECH0011ResidencePermitData] = Field(
        None,
        alias='residencePermitData',
        description='Residence permit data for foreign nationals'
    )

    # lockData is REQUIRED (comes after CHOICE in XSD)
    lock_data: ECH0021LockData = Field(
        ...,
        alias='lockData',
        description='Data lock and paper lock information'
    )

    # Optional fields (all minOccurs=0)
    contact_data: Optional[ECH0011ContactData] = Field(
        None,
        alias='contactData',
        description='Contact information (phone, email)'
    )
    person_additional_data: Optional[ECH0021PersonAdditionalData] = Field(
        None,
        alias='personAdditionalData',
        description='Additional person data per eCH-0021'
    )
    political_right_data: Optional[ECH0021PoliticalRightData] = Field(
        None,
        alias='politicalRightData',
        description='Political rights data (v7-only field)'
    )
    job_data: Optional[ECH0021JobData] = Field(
        None,
        alias='jobData',
        description='Employment/occupation data'
    )
    marital_relationship: Optional[ECH0021MaritalRelationship] = Field(
        None,
        alias='maritalRelationship',
        description='Marital relationship details'
    )
    parental_relationship: Optional[List[ECH0021ParentalRelationship]] = Field(
        None,
        alias='parentalRelationship',
        description='Parental relationships (0-n)'
    )
    guardian_relationship: Optional[List[ECH0021GuardianRelationship]] = Field(
        None,
        alias='guardianRelationship',
        description='Guardian relationships (0-n)'
    )
    armed_forces_data: Optional[ECH0021ArmedForcesData] = Field(
        None,
        alias='armedForcesData',
        description='Military service data'
    )
    civil_defense_data: Optional[ECH0021CivilDefenseData] = Field(
        None,
        alias='civilDefenseData',
        description='Civil defense service data'
    )
    fire_service_data: Optional[ECH0021FireServiceData] = Field(
        None,
        alias='fireServiceData',
        description='Fire service data'
    )
    health_insurance_data: Optional[ECH0021HealthInsuranceData] = Field(
        None,
        alias='healthInsuranceData',
        description='Health insurance information'
    )
    matrimonial_inheritance_arrangement_data: Optional[ECH0021MatrimonialInheritanceArrangementData] = Field(
        None,
        alias='matrimonialInheritanceArrangementData',
        description='Matrimonial regime and inheritance arrangement'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'baseDeliveryRestrictedMoveInPerson'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'baseDeliveryRestrictedMoveInPerson')

        Returns:
            XML element with complete move-in person data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

        # 1. personIdentification (required, eCH-0044/4)
        # Create wrapper element in parent namespace
        personIdentification_wrapper = ET.SubElement(elem, f'{{{namespace}}}personIdentification')
        personIdentification_content = self.person_identification.to_xml(namespace=ns_044)
        for child in personIdentification_content:
            personIdentification_wrapper.append(child)

        # 2. nameInfo (required, eCH-0020/3)
        self.name_info.to_xml(parent=elem, namespace=namespace, element_name='nameInfo')

        # 3. birthInfo (required, eCH-0020/3)
        self.birth_info.to_xml(parent=elem, namespace=namespace, element_name='birthInfo')

        # 4. religionData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.religion_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='religionData',
            wrapper_namespace=namespace
        )

        # 5. maritalInfo (required, eCH-0020/3)
        self.marital_info.to_xml(parent=elem, namespace=namespace, element_name='maritalInfo')

        # 6. nationalityData (required, eCH-0011/8)
        # Wrapper in ns_020, content in ns_011
        self.nationality_data.to_xml(
            parent=elem,
            namespace=ns_011,
            element_name='nationalityData',
            wrapper_namespace=namespace
        )

        # NOTE: NO deathData field in restricted type (deceased don't move in)

        # 7. contactData (optional, eCH-0011/8)
        if self.contact_data:
            # Create wrapper element in parent namespace
            contactData_wrapper = ET.SubElement(elem, f'{{{namespace}}}contactData')
            contactData_content = self.contact_data.to_xml(namespace=ns_011)
            for child in contactData_content:
                contactData_wrapper.append(child)

        # 8. personAdditionalData (optional, eCH-0021/7)
        if self.person_additional_data:
            # Create wrapper element in parent namespace
            personAdditionalData_wrapper = ET.SubElement(elem, f'{{{namespace}}}personAdditionalData')
            personAdditionalData_content = self.person_additional_data.to_xml(namespace=ns_021)
            for child in personAdditionalData_content:
                personAdditionalData_wrapper.append(child)

        # 9. politicalRightData (optional, eCH-0021/7)
        if self.political_right_data:
            # Create wrapper element in parent namespace
            politicalRightData_wrapper = ET.SubElement(elem, f'{{{namespace}}}politicalRightData')
            politicalRightData_content = self.political_right_data.to_xml(namespace=ns_021)
            for child in politicalRightData_content:
                politicalRightData_wrapper.append(child)

        # 10. CHOICE: placeOfOriginInfo (unbounded) OR residencePermitData
        if self.place_of_origin_info:
            for origin_info in self.place_of_origin_info:
                origin_info.to_xml(parent=elem, namespace=namespace, element_name='placeOfOriginInfo')
        elif self.residence_permit_data:
            # Wrapper in ns_020, content in ns_011
            self.residence_permit_data.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='residencePermitData',
                wrapper_namespace=namespace
            )

        # 11. lockData (required, eCH-0021/7)
        # Create wrapper element in parent namespace
        lockData_wrapper = ET.SubElement(elem, f'{{{namespace}}}lockData')
        lockData_content = self.lock_data.to_xml(namespace=ns_021)
        for child in lockData_content:
            lockData_wrapper.append(child)

        # 12. jobData (optional, eCH-0021/7)
        if self.job_data:
            # Create wrapper element in parent namespace
            jobData_wrapper = ET.SubElement(elem, f'{{{namespace}}}jobData')
            jobData_content = self.job_data.to_xml(namespace=ns_021)
            for child in jobData_content:
                jobData_wrapper.append(child)

        # 13. maritalRelationship (optional, eCH-0021/7)
        if self.marital_relationship:
            # Create wrapper element in parent namespace
            maritalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalRelationship')
            maritalRelationship_content = self.marital_relationship.to_xml(namespace=ns_021)
            for child in maritalRelationship_content:
                maritalRelationship_wrapper.append(child)

        # 14. parentalRelationship (optional, 0-n, eCH-0021/7)
        if self.parental_relationship:
            for relationship in self.parental_relationship:
                # Create wrapper element

                parentalRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}parentalRelationship')

                parentalRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in parentalRelationship_content:

                    parentalRelationship_wrapper.append(child)

        # 15. guardianRelationship (optional, 0-n, eCH-0021/7)
        if self.guardian_relationship:
            for relationship in self.guardian_relationship:
                # Create wrapper element

                guardianRelationship_wrapper = ET.SubElement(elem, f'{{{namespace}}}guardianRelationship')

                guardianRelationship_content = relationship.to_xml(namespace=ns_021)

                for child in guardianRelationship_content:

                    guardianRelationship_wrapper.append(child)

        # 16. armedForcesData (optional, eCH-0021/7)
        if self.armed_forces_data:
            # Create wrapper element in parent namespace
            armedForcesData_wrapper = ET.SubElement(elem, f'{{{namespace}}}armedForcesData')
            armedForcesData_content = self.armed_forces_data.to_xml(namespace=ns_021)
            for child in armedForcesData_content:
                armedForcesData_wrapper.append(child)

        # 17. civilDefenseData (optional, eCH-0021/7)
        if self.civil_defense_data:
            # Create wrapper element in parent namespace
            civilDefenseData_wrapper = ET.SubElement(elem, f'{{{namespace}}}civilDefenseData')
            civilDefenseData_content = self.civil_defense_data.to_xml(namespace=ns_021)
            for child in civilDefenseData_content:
                civilDefenseData_wrapper.append(child)

        # 18. fireServiceData (optional, eCH-0021/7)
        if self.fire_service_data:
            # Create wrapper element in parent namespace
            fireServiceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}fireServiceData')
            fireServiceData_content = self.fire_service_data.to_xml(namespace=ns_021)
            for child in fireServiceData_content:
                fireServiceData_wrapper.append(child)

        # 19. healthInsuranceData (optional, eCH-0021/7)
        if self.health_insurance_data:
            # Create wrapper element in parent namespace
            healthInsuranceData_wrapper = ET.SubElement(elem, f'{{{namespace}}}healthInsuranceData')
            healthInsuranceData_content = self.health_insurance_data.to_xml(namespace=ns_021)
            for child in healthInsuranceData_content:
                healthInsuranceData_wrapper.append(child)

        # 20. matrimonialInheritanceArrangementData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.matrimonial_inheritance_arrangement_data:
            wrapper = ET.SubElement(elem, f'{{{namespace}}}matrimonialInheritanceArrangementData')
            content = self.matrimonial_inheritance_arrangement_data.to_xml(namespace=ns_021)
            for child in content:
                wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BaseDeliveryRestrictedMoveInPerson':
        """Parse from XML element.

        Args:
            element: XML element containing restricted move-in person data

        Returns:
            Parsed ECH0020BaseDeliveryRestrictedMoveInPerson instance
        """
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8
        ns_021 = NS.ECH0021_V7
        ns_044 = NS.ECH0044_V4

        # Required fields
        person_id_elem = element.find(f'{{{ns_020}}}personIdentification')
        if person_id_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires personIdentification")
        person_identification = ECH0044PersonIdentification.from_xml(person_id_elem)

        name_info_elem = element.find(f'{{{ns_020}}}nameInfo')
        if name_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires nameInfo")
        name_info = ECH0020NameInfo.from_xml(name_info_elem)

        birth_info_elem = element.find(f'{{{ns_020}}}birthInfo')
        if birth_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires birthInfo")
        birth_info = ECH0020BirthInfo.from_xml(birth_info_elem)

        religion_elem = element.find(f'{{{ns_020}}}religionData')
        if religion_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires religionData")
        religion_data = ECH0011ReligionData.from_xml(religion_elem)

        marital_info_elem = element.find(f'{{{ns_020}}}maritalInfo')
        if marital_info_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires maritalInfo")
        marital_info = ECH0020MaritalInfo.from_xml(marital_info_elem)

        nationality_elem = element.find(f'{{{ns_020}}}nationalityData')
        if nationality_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires nationalityData")
        nationality_data = ECH0011NationalityData.from_xml(nationality_elem)

        lock_elem = element.find(f'{{{ns_020}}}lockData')
        if lock_elem is None:
            raise ValueError("baseDeliveryRestrictedMoveInPersonType requires lockData")
        lock_data = ECH0021LockData.from_xml(lock_elem)

        # CHOICE: placeOfOriginInfo OR residencePermitData
        place_of_origin_info = None
        origin_elems = element.findall(f'{{{ns_020}}}placeOfOriginInfo')
        if origin_elems:
            place_of_origin_info = [ECH0020PlaceOfOriginInfo.from_xml(elem) for elem in origin_elems]

        residence_permit_data = None
        permit_elem = element.find(f'{{{ns_020}}}residencePermitData')
        if permit_elem is not None:
            residence_permit_data = ECH0011ResidencePermitData.from_xml(permit_elem)

        # Optional fields (NO deathData in restricted type)
        contact_data = None
        contact_elem = element.find(f'{{{ns_020}}}contactData')
        if contact_elem is not None:
            contact_data = ECH0011ContactData.from_xml(contact_elem)

        person_additional_data = None
        additional_elem = element.find(f'{{{ns_020}}}personAdditionalData')
        if additional_elem is not None:
            person_additional_data = ECH0021PersonAdditionalData.from_xml(additional_elem)

        political_right_data = None
        political_elem = element.find(f'{{{ns_020}}}politicalRightData')
        if political_elem is not None:
            political_right_data = ECH0021PoliticalRightData.from_xml(political_elem)

        job_data = None
        job_elem = element.find(f'{{{ns_020}}}jobData')
        if job_elem is not None:
            job_data = ECH0021JobData.from_xml(job_elem)

        marital_relationship = None
        marital_rel_elem = element.find(f'{{{ns_020}}}maritalRelationship')
        if marital_rel_elem is not None:
            marital_relationship = ECH0021MaritalRelationship.from_xml(marital_rel_elem)

        parental_relationship = None
        parental_elems = element.findall(f'{{{ns_020}}}parentalRelationship')
        if parental_elems:
            parental_relationship = [ECH0021ParentalRelationship.from_xml(elem) for elem in parental_elems]

        guardian_relationship = None
        guardian_elems = element.findall(f'{{{ns_020}}}guardianRelationship')
        if guardian_elems:
            guardian_relationship = [ECH0021GuardianRelationship.from_xml(elem) for elem in guardian_elems]

        armed_forces_data = None
        armed_elem = element.find(f'{{{ns_020}}}armedForcesData')
        if armed_elem is not None:
            armed_forces_data = ECH0021ArmedForcesData.from_xml(armed_elem)

        civil_defense_data = None
        civil_elem = element.find(f'{{{ns_020}}}civilDefenseData')
        if civil_elem is not None:
            civil_defense_data = ECH0021CivilDefenseData.from_xml(civil_elem)

        fire_service_data = None
        fire_elem = element.find(f'{{{ns_020}}}fireServiceData')
        if fire_elem is not None:
            fire_service_data = ECH0021FireServiceData.from_xml(fire_elem)

        health_insurance_data = None
        health_elem = element.find(f'{{{ns_020}}}healthInsuranceData')
        if health_elem is not None:
            health_insurance_data = ECH0021HealthInsuranceData.from_xml(health_elem)

        matrimonial_inheritance_arrangement_data = None
        matrimonial_elem = element.find(f'{{{ns_020}}}matrimonialInheritanceArrangementData')
        if matrimonial_elem is not None:
            matrimonial_inheritance_arrangement_data = ECH0021MatrimonialInheritanceArrangementData.from_xml(matrimonial_elem)

        return cls(
            person_identification=person_identification,
            name_info=name_info,
            birth_info=birth_info,
            religion_data=religion_data,
            marital_info=marital_info,
            nationality_data=nationality_data,
            place_of_origin_info=place_of_origin_info,
            residence_permit_data=residence_permit_data,
            lock_data=lock_data,
            contact_data=contact_data,
            person_additional_data=person_additional_data,
            political_right_data=political_right_data,
            job_data=job_data,
            marital_relationship=marital_relationship,
            parental_relationship=parental_relationship,
            guardian_relationship=guardian_relationship,
            armed_forces_data=armed_forces_data,
            civil_defense_data=civil_defense_data,
            fire_service_data=fire_service_data,
            health_insurance_data=health_insurance_data,
            matrimonial_inheritance_arrangement_data=matrimonial_inheritance_arrangement_data
        )


# ============================================================================
# REPORTING MUNICIPALITY TYPES (Municipality reporting and residence data)
# ============================================================================

class ECH0020ReportingMunicipality(BaseModel):
    """Municipality reporting data with residence and movement information.

    This type contains information about where a person is registered, when they
    arrived, where they came from, their dwelling address, and departure/destination
    information if applicable.

    XSD: reportingMunicipalityType (eCH-0020-3-0.xsd lines 455-467)
    PDF: Unknown section (reporting municipality structure)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Fields:
    - CHOICE: reportingMunicipality (Swiss municipality) OR federalRegister (INFOSTAR/ZEMIS)
    - arrivalDate: Date of arrival in municipality (optional)
    - comesFrom: Previous residence (optional)
    - dwellingAddress: Current dwelling address (optional)
    - departureDate: Date of departure (optional)
    - goesTo: Destination after departure (optional)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister (mutually exclusive)
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # Optional fields
    arrival_date: Optional[date] = Field(
        None,
        alias='arrivalDate',
        description='Date of arrival in this municipality'
    )
    comes_from: Optional[ECH0011DestinationType] = Field(
        None,
        alias='comesFrom',
        description='Previous residence (where person came from)'
    )
    dwelling_address: Optional[ECH0011DwellingAddress] = Field(
        None,
        alias='dwellingAddress',
        description='Current dwelling address in municipality'
    )
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element.

        Args:
            parent: Optional parent element
            namespace: XML namespace (default eCH-0020/3)
            element_name: Element name (default 'reportingMunicipality')

        Returns:
            XML element with reporting municipality data
        """
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE: reportingMunicipality OR federalRegister
        if self.reporting_municipality:
            self.reporting_municipality.to_xml(
                parent=elem, namespace=ns_007
            )
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Optional fields
        if self.arrival_date:
            arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
            arrival_elem.text = self.arrival_date.isoformat()

        if self.comes_from:
            # Wrapper in ns_020, content in ns_011
            self.comes_from.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='comesFrom',
                wrapper_namespace=namespace
            )

        if self.dwelling_address:
            # Wrapper in ns_020, content in ns_011
            self.dwelling_address.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='dwellingAddress',
                wrapper_namespace=namespace
            )

        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipality':
        """Parse from XML element.

        Args:
            element: XML element containing reportingMunicipality data

        Returns:
            Parsed ECH0020ReportingMunicipality instance
        """
        ns_020 = NS.ECH0020_V3
        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE: reportingMunicipality OR federalRegister
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Optional fields
        arrival_date = None
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is not None and arrival_elem.text:
            arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from = None
        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is not None:
            comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_address = None
        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is not None:
            dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedBaseMain(BaseModel):
    """Restricted reporting municipality for base delivery main residence.

    XSD restriction of reportingMunicipalityType with required fields for main residence.

    XSD: reportingMunicipalityRestrictedBaseMainType (eCH-0020-3-0.xsd lines 468-484)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    - comesFrom: remains optional
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields in restriction
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    # Optional fields
    comes_from: Optional[ECH0011DestinationType] = Field(
        None,
        alias='comesFrom',
        description='Previous residence (where person came from)'
    )
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Optional comesFrom
        if self.comes_from:
            # Wrapper in ns_020, content in ns_011
            self.comes_from.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='comesFrom',
                wrapper_namespace=namespace
            )

        # Required dwellingAddress
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Optional fields
        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedBaseMain':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedBaseMainType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseMainType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Optional fields
        comes_from = None
        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is not None:
            comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


class ECH0020ReportingMunicipalityRestrictedBaseSecondary(BaseModel):
    """Restricted reporting municipality for base delivery secondary residence.

    XSD restriction of reportingMunicipalityType with required fields for secondary residence.

    XSD: reportingMunicipalityRestrictedBaseSecondaryType (eCH-0020-3-0.xsd lines 485-501)
    Namespace: http://www.ech.ch/xmlns/eCH-0020/3

    Differences from base reportingMunicipalityType:
    - arrivalDate: REQUIRED (was optional)
    - comesFrom: REQUIRED (was optional)
    - dwellingAddress: REQUIRED (was optional)
    """

    # XSD CHOICE: reportingMunicipality OR federalRegister
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None,
        alias='reportingMunicipality',
        description='Municipality where person is registered'
    )
    federal_register: Optional[FederalRegister] = Field(
        None,
        alias='federalRegister',
        description='Federal register (INFOSTAR=1, ORDIPRO=2, ZEMIS=3)'
    )

    # REQUIRED fields in restriction
    arrival_date: date = Field(
        ...,
        alias='arrivalDate',
        description='Date of arrival in this municipality (REQUIRED)'
    )
    comes_from: ECH0011DestinationType = Field(
        ...,
        alias='comesFrom',
        description='Previous residence (REQUIRED for secondary residence)'
    )
    dwelling_address: ECH0011DwellingAddress = Field(
        ...,
        alias='dwellingAddress',
        description='Current dwelling address in municipality (REQUIRED)'
    )

    # Optional fields
    departure_date: Optional[date] = Field(
        None,
        alias='departureDate',
        description='Date of departure from municipality'
    )
    goes_to: Optional[ECH0011DestinationType] = Field(
        None,
        alias='goesTo',
        description='Destination (where person is going)'
    )

    model_config = ConfigDict(populate_by_name=True)

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

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'reportingMunicipality'
    ) -> ET.Element:
        """Serialize to XML element."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        ns_007 = NS.ECH0007_V5
        ns_011 = NS.ECH0011_V8

        # CHOICE
        if self.reporting_municipality:
            # Create wrapper element in parent namespace
            reportingMunicipality_wrapper = ET.SubElement(elem, f'{{{namespace}}}reportingMunicipality')
            reportingMunicipality_content = self.reporting_municipality.to_xml(namespace=ns_007)
            for child in reportingMunicipality_content:
                reportingMunicipality_wrapper.append(child)
        elif self.federal_register:
            register_elem = ET.SubElement(elem, f'{{{namespace}}}federalRegister')
            register_elem.text = self.federal_register.value

        # Required fields
        arrival_elem = ET.SubElement(elem, f'{{{namespace}}}arrivalDate')
        arrival_elem.text = self.arrival_date.isoformat()

        # Create wrapper element in parent namespace
        comesFrom_wrapper = ET.SubElement(elem, f'{{{namespace}}}comesFrom')
        comesFrom_content = self.comes_from.to_xml(namespace=ns_011)
        for child in comesFrom_content:
            comesFrom_wrapper.append(child)
        # Create wrapper element in parent namespace
        dwellingAddress_wrapper = ET.SubElement(elem, f'{{{namespace}}}dwellingAddress')
        dwellingAddress_content = self.dwelling_address.to_xml(namespace=ns_011)
        for child in dwellingAddress_content:
            dwellingAddress_wrapper.append(child)

        # Optional fields
        if self.departure_date:
            departure_elem = ET.SubElement(elem, f'{{{namespace}}}departureDate')
            departure_elem.text = self.departure_date.isoformat()

        if self.goes_to:
            # Wrapper in ns_020, content in ns_011
            self.goes_to.to_xml(
                parent=elem,
                namespace=ns_011,
                element_name='goesTo',
                wrapper_namespace=namespace
            )

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020ReportingMunicipalityRestrictedBaseSecondary':
        """Parse from XML element."""
        ns_020 = NS.ECH0020_V3
        ns_011 = NS.ECH0011_V8

        # CHOICE
        reporting_municipality = None
        municipality_elem = element.find(f'{{{ns_020}}}reportingMunicipality')
        if municipality_elem is not None:
            reporting_municipality = ECH0007SwissMunicipality.from_xml(municipality_elem)

        federal_register = None
        register_elem = element.find(f'{{{ns_020}}}federalRegister')
        if register_elem is not None and register_elem.text:
            federal_register = FederalRegister(register_elem.text)

        # Required fields
        arrival_elem = element.find(f'{{{ns_020}}}arrivalDate')
        if arrival_elem is None or not arrival_elem.text:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires arrivalDate")
        arrival_date = date.fromisoformat(arrival_elem.text)

        comes_from_elem = element.find(f'{{{ns_020}}}comesFrom')
        if comes_from_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires comesFrom")
        comes_from = ECH0011DestinationType.from_xml(comes_from_elem)

        dwelling_elem = element.find(f'{{{ns_020}}}dwellingAddress')
        if dwelling_elem is None:
            raise ValueError("reportingMunicipalityRestrictedBaseSecondaryType requires dwellingAddress")
        dwelling_address = ECH0011DwellingAddress.from_xml(dwelling_elem)

        # Optional fields
        departure_date = None
        departure_elem = element.find(f'{{{ns_020}}}departureDate')
        if departure_elem is not None and departure_elem.text:
            departure_date = date.fromisoformat(departure_elem.text)

        goes_to = None
        goes_to_elem = element.find(f'{{{ns_020}}}goesTo')
        if goes_to_elem is not None:
            goes_to = ECH0011DestinationType.from_xml(goes_to_elem)

        return cls(
            reporting_municipality=reporting_municipality,
            federal_register=federal_register,
            arrival_date=arrival_date,
            comes_from=comes_from,
            dwelling_address=dwelling_address,
            departure_date=departure_date,
            goes_to=goes_to
        )


# Helper classes for eventBaseDelivery inline complex types

class ECH0020HasMainResidence(BaseModel):
    """Main residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseMainType with optional secondary residences.
    This is an inline anonymous type from eventBaseDelivery XSD definition.
    """

    # All fields from reportingMunicipalityRestrictedBaseMainType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')
    comes_from: Optional[ECH0011DestinationType] = Field(None, alias='comesFrom')
    departure_date: Optional[date] = Field(None, alias='departureDate')
    goes_to: Optional[ECH0011DestinationType] = Field(None, alias='goesTo')

    # Extension: additional secondary residences
    secondary_residence: Optional[List[ECH0007SwissMunicipality]] = Field(
        None,
        alias='secondaryResidence',
        description='Secondary residence municipalities (0-n)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasMainResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasMainResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasMainResidence allows either reportingMunicipality OR federalRegister")
        return self


class ECH0020HasSecondaryResidence(BaseModel):
    """Secondary residence data for base delivery (inline complexType extension).

    Extends reportingMunicipalityRestrictedBaseSecondaryType with required main residence.
    This is an inline anonymous type from eventBaseDelivery XSD definition.
    """

    # All fields from reportingMunicipalityRestrictedBaseSecondaryType
    reporting_municipality: Optional[ECH0007SwissMunicipality] = Field(
        None, alias='reportingMunicipality'
    )
    federal_register: Optional[FederalRegister] = Field(
        None, alias='federalRegister'
    )
    arrival_date: date = Field(..., alias='arrivalDate')
    comes_from: ECH0011DestinationType = Field(..., alias='comesFrom')
    dwelling_address: ECH0011DwellingAddress = Field(..., alias='dwellingAddress')
    departure_date: Optional[date] = Field(None, alias='departureDate')
    goes_to: Optional[ECH0011DestinationType] = Field(None, alias='goesTo')

    # Extension: required main residence
    main_residence: ECH0007SwissMunicipality = Field(
        ...,
        alias='mainResidence',
        description='Main residence municipality (required)'
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def validate_choice(self) -> 'ECH0020HasSecondaryResidence':
        has_municipality = self.reporting_municipality is not None
        has_register = self.federal_register is not None
        if not has_municipality and not has_register:
            raise ValueError("hasSecondaryResidence requires either reportingMunicipality OR federalRegister")
        if has_municipality and has_register:
            raise ValueError("hasSecondaryResidence allows either reportingMunicipality OR federalRegister")
        return self


# ============================================================================
