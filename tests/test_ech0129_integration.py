"""Integration tests for eCH-0129 v6.0.0 — full object graph construction.

Tests that complex, nested object graphs can be built, serialized to XML,
and deserialized back. Each test builds a realistic scenario combining
multiple types across submodules.
"""

import xml.etree.ElementTree as ET
from datetime import date

from openmun_ech.ech0129 import (
    # Enums
    AreaDescriptionCode,
    AreaType,
    BuildingCategory,
    BuildingStatus,
    BuildingVolumeNorm,
    ChangeReason,
    DwellingStatus,
    DwellingUsageCode,
    EmailCategory,
    EnergySource,
    FiscalRelationship,
    HeatGeneratorHeating,
    HeatGeneratorHotWater,
    KindOfWork,
    LocationCode,
    OriginOfCoordinates,
    PhoneCategory,
    PlaceNameType,
    ProjectStatus,
    RealestateStatus,
    RealestateType,
    RemarkType,
    StreetKind,
    StreetLanguage,
    StreetStatus,
    TypeOfClient,
    TypeOfConstruction,
    TypeOfConstructionProject,
    TypeOfPermit,
    TypeOfValue,
    UsageCode,
    # Models
    ECH0129Area,
    ECH0129Building,
    ECH0129BuildingAddress,
    ECH0129BuildingAuthority,
    ECH0129BuildingAuthorityOnly,
    ECH0129BuildingDate,
    ECH0129BuildingEntrance,
    ECH0129BuildingEntranceIdentification,
    ECH0129BuildingEntranceOnly,
    ECH0129BuildingIdentification,
    ECH0129BuildingOnly,
    ECH0129BuildingVolume,
    ECH0129CadastralMap,
    ECH0129CadastralSurveyorRemark,
    ECH0129ConstructionLocalisation,
    ECH0129ConstructionProject,
    ECH0129ConstructionProjectIdentification,
    ECH0129Contact,
    ECH0129Coordinates,
    ECH0129CoveringAreaOfSDR,
    ECH0129DatePartiallyKnown,
    ECH0129Dwelling,
    ECH0129DwellingUsage,
    ECH0129Email,
    ECH0129EstimationObject,
    ECH0129EstimationValue,
    ECH0129FiscalOwnership,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129IdentificationChoice,
    ECH0129InsuranceObject,
    ECH0129InsuranceSum,
    ECH0129InsuranceValue,
    ECH0129InsuranceVolume,
    ECH0129KindOfConstructionWork,
    ECH0129Locality,
    ECH0129LocalityName,
    ECH0129NamedId,
    ECH0129NamedMetaData,
    ECH0129PartialAreaOfBuilding,
    ECH0129Person,
    ECH0129PersonOnly,
    ECH0129Phone,
    ECH0129PlaceName,
    ECH0129Realestate,
    ECH0129RealestateIdentification,
    ECH0129Right,
    ECH0129Street,
    ECH0129StreetDescription,
    ECH0129StreetDescriptionEntry,
    ECH0129StreetSection,
    ECH0129Value,
)
from openmun_ech.ech0007.v6 import ECH0007v6SwissMunicipality
from openmun_ech.ech0008.v3 import ECH0008Country
from openmun_ech.ech0010.v6 import ECH0010v6AddressInformation, ECH0010v6Country
from openmun_ech.ech0044 import ECH0044PersonIdentificationLight
from openmun_ech.ech0097 import (
    ECH0097NamedOrganisationId,
    ECH0097OrganisationIdentification,
)


# ---------------------------------------------------------------------------
# Shared helpers for building test data
# ---------------------------------------------------------------------------

def make_named_id(category: str = "MU.6172", id_value: str = "1") -> ECH0129NamedId:
    return ECH0129NamedId(id_category=category, id_value=id_value)


def make_coordinates() -> ECH0129Coordinates:
    return ECH0129Coordinates(
        east="2634000.000",
        north="1128000.000",
        origin_of_coordinates=OriginOfCoordinates.BUILDING_APPLICATION,
    )


def make_street_section() -> ECH0129StreetSection:
    return ECH0129StreetSection(
        esid=10000001,
        swiss_zip_code=3983,
        swiss_zip_code_add_on="00",
    )


def make_street_description() -> ECH0129StreetDescription:
    return ECH0129StreetDescription(
        entries=[
            ECH0129StreetDescriptionEntry(
                language=StreetLanguage.GERMAN,
                description_long="Dorfstrasse",
                description_short="Dorfs.",
                description_index="Dor",
            )
        ]
    )


def make_building_identification() -> ECH0129BuildingIdentification:
    return ECH0129BuildingIdentification(
        egid=123456789,
        local_id=[make_named_id()],
        municipality=6172,
    )


def make_org_id() -> ECH0097OrganisationIdentification:
    return ECH0097OrganisationIdentification(
        local_organisation_id=ECH0097NamedOrganisationId(
            organisation_id_category="MU.6172",
            organisation_id="1",
        ),
        organisation_name="Gemeinde Bister",
    )


def make_person_id() -> ECH0044PersonIdentificationLight:
    return ECH0044PersonIdentificationLight(
        vn="7561234567890",
        official_name="Muster",
        first_name="Hans",
        sex="1",
    )


def make_address() -> ECH0010v6AddressInformation:
    return ECH0010v6AddressInformation(
        street="Dorfstrasse",
        house_number="1",
        town="Bister",
        swiss_zip_code=3983,
        swiss_zip_code_add_on="00",
        country=ECH0010v6Country(
            country_id=8100,
            country_id_iso2="CH",
            country_name_short="Schweiz",
        ),
    )


def make_realestate_id() -> ECH0129RealestateIdentification:
    return ECH0129RealestateIdentification(
        egrid="CH123456789012",
        number="1234",
    )


# ---------------------------------------------------------------------------
# Test: Building with entrances + nested types
# ---------------------------------------------------------------------------

class TestBuildingWithEntrances:
    """Build a complete building with entrances, heating, volume."""

    def test_building_full_graph(self):
        """Full building with identification, entrances, heating, volume."""
        entrance = ECH0129BuildingEntrance(
            egaid=100000001,
            edid=0,
            building_entrance_no="A",
            coordinates=make_coordinates(),
            local_id=make_named_id("ENTRANCE", "1"),
            is_official_address=True,
            street_section=make_street_section(),
        )

        building = ECH0129Building(
            building_identification=make_building_identification(),
            egid=123456789,
            official_building_no="12A",
            name="Gemeindehaus",
            date_of_construction=ECH0129BuildingDate(
                year_month_day=date(1985, 6, 15)
            ),
            number_of_floors=3,
            number_of_separate_habitable_rooms=8,
            surface_area_of_building=450,
            building_category=BuildingCategory.RESIDENTIAL_ONLY,
            building_class=1121,
            status=BuildingStatus.EXISTING,
            coordinates=make_coordinates(),
            civil_defense_shelter=True,
            volume=ECH0129BuildingVolume(
                volume=1500,
                information_source="851",
                norm="961",
            ),
            heating=[
                ECH0129Heating(
                    heat_generator_heating=HeatGeneratorHeating.HEAT_PUMP_SINGLE,
                    energy_source_heating=EnergySource.AIR,
                    information_source_heating="852",
                    revision_date=date(2023, 1, 15),
                ),
            ],
            hot_water=[
                ECH0129HotWater(
                    heat_generator_hot_water=HeatGeneratorHotWater.HEAT_PUMP,
                    energy_source_heating=EnergySource.AIR,
                    information_source_heating="852",
                    revision_date=date(2023, 1, 15),
                ),
            ],
            building_entrance=[entrance],
            named_meta_data=[
                ECH0129NamedMetaData(
                    meta_data_name="MADD_IMPORT_DATE",
                    meta_data_value="2024-01-15",
                ),
            ],
            building_free_text=["Denkmalgeschuetzt"],
        )

        xml = building.to_xml()
        assert xml.tag.endswith('}building')

        # Roundtrip
        restored = ECH0129Building.from_xml(xml)
        assert restored.egid == 123456789
        assert restored.building_category == BuildingCategory.RESIDENTIAL_ONLY
        assert len(restored.building_entrance) == 1
        assert restored.building_entrance[0].egaid == 100000001
        assert restored.volume is not None
        assert restored.volume.volume == 1500
        assert len(restored.heating) == 1
        assert restored.heating[0].heat_generator_heating == HeatGeneratorHeating.HEAT_PUMP_SINGLE
        assert len(restored.named_meta_data) == 1

    def test_building_only_no_entrances(self):
        """BuildingOnly: same structure minus entrances."""
        building_only = ECH0129BuildingOnly(
            building_category=BuildingCategory.PARTIAL_RESIDENTIAL,
            building_class=1220,
            status=BuildingStatus.EXISTING,
            number_of_floors=5,
        )

        xml = building_only.to_xml()
        assert xml.tag.endswith('}buildingOnly')

        restored = ECH0129BuildingOnly.from_xml(xml)
        assert restored.building_category == BuildingCategory.PARTIAL_RESIDENTIAL
        assert restored.building_class == 1220

    def test_building_minimal(self):
        """Minimal building: only the required field."""
        building = ECH0129Building(
            building_category=BuildingCategory.PROVISIONAL,
        )
        xml = building.to_xml()
        restored = ECH0129Building.from_xml(xml)
        assert restored.building_category == BuildingCategory.PROVISIONAL
        assert restored.building_entrance == []


# ---------------------------------------------------------------------------
# Test: Construction project with localisation
# ---------------------------------------------------------------------------

class TestConstructionProject:
    """Build a complete construction project with all nested types."""

    def test_project_with_municipality_localisation(self):
        """Construction project localized to a municipality."""
        project = ECH0129ConstructionProject(
            construction_project_identification=ECH0129ConstructionProjectIdentification(
                local_id=[make_named_id("BAU", "2024-001")],
                eproid=500000001,
                official_construction_project_file_no="BP-2024/001",
            ),
            type_of_construction_project=TypeOfConstructionProject.BUILDING_CONSTRUCTION,
            construction_localisation=ECH0129ConstructionLocalisation(
                municipality=ECH0007v6SwissMunicipality(
                    municipality_id="6172",
                    municipality_name="Bister",
                ),
            ),
            type_of_permit=TypeOfPermit.BAUZONE,
            building_permit_issue_date=date(2024, 3, 15),
            project_start_date=date(2024, 6, 1),
            total_costs_of_project=500000,
            status=ProjectStatus.CONSTRUCTION_STARTED,
            type_of_client=TypeOfClient.PRIVATPERSONEN,
            type_of_construction=TypeOfConstruction.WOHNGEBAEUDE_MIT_NEBENNUTZUNG,
            description="Neubau Einfamilienhaus, 2 Geschosse",
            duration_of_construction_phase=18,
            number_of_concerned_buildings=1,
            number_of_concerned_dwellings=1,
            project_free_text=["Minergie-Standard"],
        )

        xml = project.to_xml()
        assert xml.tag.endswith('}constructionProject')

        restored = ECH0129ConstructionProject.from_xml(xml)
        assert restored.status == ProjectStatus.CONSTRUCTION_STARTED
        assert restored.description == "Neubau Einfamilienhaus, 2 Geschosse"
        assert restored.total_costs_of_project == 500000
        assert restored.construction_localisation is not None
        assert restored.construction_localisation.municipality is not None
        assert restored.construction_localisation.municipality.municipality_id == "6172"
        assert len(restored.project_free_text) == 1

    def test_project_canton_localisation(self):
        """Construction project localized to a canton."""
        from openmun_ech.ech0007.v5 import CantonAbbreviation

        project = ECH0129ConstructionProject(
            construction_localisation=ECH0129ConstructionLocalisation(
                canton=CantonAbbreviation.VS,
            ),
            status=ProjectStatus.PERMIT_GRANTED,
            description="Kantonales Bauprojekt",
        )

        xml = project.to_xml()
        restored = ECH0129ConstructionProject.from_xml(xml)
        assert restored.construction_localisation.canton == CantonAbbreviation.VS

    def test_project_country_localisation(self):
        """Construction project with country localisation."""
        project = ECH0129ConstructionProject(
            construction_localisation=ECH0129ConstructionLocalisation(
                country=ECH0008Country(
                    country_id="8100",
                    country_id_iso2="CH",
                    country_name_short="Schweiz",
                ),
            ),
            status=ProjectStatus.PERMIT_DENIED,
            description="Grenzueberschreitendes Projekt",
        )

        xml = project.to_xml()
        restored = ECH0129ConstructionProject.from_xml(xml)
        assert restored.construction_localisation.country is not None
        assert restored.construction_localisation.country.country_id_iso2 == "CH"

    def test_kind_of_construction_work(self):
        """Kind of construction work with boolean flags."""
        work = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
            energetic_restauration=True,
            renovation_heatingsystem=True,
            inner_conversion_renovation=False,
        )

        xml = work.to_xml()
        restored = ECH0129KindOfConstructionWork.from_xml(xml)
        assert restored.kind_of_work == KindOfWork.NEW_CONSTRUCTION
        assert restored.energetic_restauration is True
        assert restored.renovation_heatingsystem is True
        assert restored.inner_conversion_renovation is False


# ---------------------------------------------------------------------------
# Test: Person with address, phone, email
# ---------------------------------------------------------------------------

class TestPersonGraph:
    """Person + building authority with cross-standard types."""

    def test_person_with_all_contact_info(self):
        """Person with person identification + address + email + phone."""
        person = ECH0129Person(
            identification=ECH0129IdentificationChoice(
                person_identification=make_person_id(),
            ),
            address=make_address(),
            email=ECH0129Email(
                email_category=EmailCategory.PRIVATE,
                email_address="hans@example.ch",
            ),
            phone=ECH0129Phone(
                phone_category=PhoneCategory.PRIVATE_PHONE,
                phone_number="0279461234",
            ),
            protected=False,
        )

        xml = person.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert 'person' in xml.tag
        assert 'Muster' in xml_str

        restored = ECH0129Person.from_xml(xml)
        assert restored.identification.person_identification is not None
        assert restored.identification.person_identification.official_name == "Muster"
        assert restored.email is not None
        assert restored.email.email_address == "hans@example.ch"
        assert restored.phone is not None
        assert restored.phone.phone_number == "0279461234"
        assert restored.protected is False

    def test_person_with_org_identification(self):
        """Person using organisation identification branch."""
        person = ECH0129Person(
            identification=ECH0129IdentificationChoice(
                organisation_identification=make_org_id(),
            ),
        )

        xml = person.to_xml()
        restored = ECH0129Person.from_xml(xml)
        assert restored.identification.organisation_identification is not None
        assert restored.identification.organisation_identification.organisation_name == "Gemeinde Bister"

    def test_person_only_minimal(self):
        """PersonOnly: just identification, nothing else."""
        person_only = ECH0129PersonOnly(
            identification=ECH0129IdentificationChoice(
                person_identification=make_person_id(),
            ),
        )

        xml = person_only.to_xml()
        restored = ECH0129PersonOnly.from_xml(xml)
        assert restored.identification.person_identification is not None

    def test_building_authority_full(self):
        """Building authority with contact person + contact + address."""
        authority = ECH0129BuildingAuthority(
            building_authority_identification_type=make_org_id(),
            description="Bauamt Gemeinde Bister",
            short_description="Bauamt",
            contact_person=ECH0129IdentificationChoice(
                person_identification=make_person_id(),
            ),
            contact=ECH0129Contact(
                email_address="bauamt@bister.ch",
                phone_number="0279461000",
            ),
            address=make_address(),
        )

        xml = authority.to_xml()
        xml_str = ET.tostring(xml, encoding='unicode')
        assert 'buildingAuthority' in xml.tag
        assert 'Bauamt' in xml_str

        restored = ECH0129BuildingAuthority.from_xml(xml)
        assert restored.description == "Bauamt Gemeinde Bister"
        assert restored.contact_person is not None
        assert restored.contact is not None
        assert restored.contact.email_address == "bauamt@bister.ch"

    def test_building_authority_only(self):
        """BuildingAuthorityOnly: identification + descriptions only."""
        authority = ECH0129BuildingAuthorityOnly(
            building_authority_identification_type=make_org_id(),
            description="Bauamt",
        )

        xml = authority.to_xml()
        restored = ECH0129BuildingAuthorityOnly.from_xml(xml)
        assert restored.description == "Bauamt"


# ---------------------------------------------------------------------------
# Test: Insurance and Estimation objects
# ---------------------------------------------------------------------------

class TestInsuranceEstimation:
    """Insurance and estimation objects with nested value types."""

    def test_insurance_object_full(self):
        """Insurance object with value and volume."""
        obj = ECH0129InsuranceObject(
            local_id=make_named_id("GVA", "VS-1234"),
            start_date=date(2020, 1, 1),
            insurance_number="VS-1234-5678",
            usage_code=UsageCode.RESIDENTIAL,
            location_code=LocationCode.DETACHED,
            insurance_value=ECH0129InsuranceValue(
                local_id=make_named_id("VW", "2020-001"),
                valid_from=date(2020, 1, 1),
                change_reason=ChangeReason.NEW_VALUE,
                insurance_sum=ECH0129InsuranceSum(amount="850000.00"),
            ),
            volume=ECH0129InsuranceVolume(
                volume=1200,
                norm=BuildingVolumeNorm.SIA_416,
            ),
        )

        xml = obj.to_xml()
        assert xml.tag.endswith('}insuranceObject')

        restored = ECH0129InsuranceObject.from_xml(xml)
        assert restored.insurance_number == "VS-1234-5678"
        assert restored.insurance_value is not None
        assert restored.insurance_value.insurance_sum.amount == "850000.00"
        assert restored.volume is not None
        assert restored.volume.volume == 1200

    def test_estimation_object_with_values(self):
        """Estimation object with multiple estimation values."""
        obj = ECH0129EstimationObject(
            local_id=make_named_id("SCHT", "2024-001"),
            volume=500,
            year_of_construction="1985",
            description="Einfamilienhaus mit Garage",
            valid_from=date(2024, 1, 1),
            estimation_reason="Neuschaetzung",
            estimation_value=[
                ECH0129EstimationValue(
                    local_id=make_named_id("SW", "LAND-001"),
                    value=ECH0129Value(amount="250000.00"),
                    type_of_value=TypeOfValue.TAX_VALUE,
                ),
                ECH0129EstimationValue(
                    local_id=make_named_id("SW", "GEB-001"),
                    value=ECH0129Value(amount="600000.00"),
                    type_of_value=TypeOfValue.MARKET_VALUE,
                ),
            ],
        )

        xml = obj.to_xml()
        assert xml.tag.endswith('}estimationObject')

        restored = ECH0129EstimationObject.from_xml(xml)
        assert restored.year_of_construction == "1985"
        assert len(restored.estimation_value) == 2
        assert restored.estimation_value[0].type_of_value == TypeOfValue.TAX_VALUE
        assert restored.estimation_value[1].value.amount == "600000.00"


# ---------------------------------------------------------------------------
# Test: Realestate with area and fiscal ownership
# ---------------------------------------------------------------------------

class TestRealestateGraph:
    """Realestate, area, and fiscal ownership types."""

    def test_realestate_full(self):
        """Complete realestate with all optional fields."""
        realestate = ECH0129Realestate(
            realestate_identification=make_realestate_id(),
            authority="GB",
            date_val=date(2024, 1, 15),
            realestate_type=RealestateType.LIEGENSCHAFT,
            status=RealestateStatus.VALID,
            mutnumber="MUT-2024-001",
            ident_dn="DN-001",
            square_measure="12345.50",
            realestate_incomplete=False,
            coordinates=make_coordinates(),
            named_meta_data=[
                ECH0129NamedMetaData(
                    meta_data_name="VALREG_IMPORT",
                    meta_data_value="2024-01-15",
                ),
            ],
        )

        xml = realestate.to_xml()
        assert xml.tag.endswith('}realestate')

        restored = ECH0129Realestate.from_xml(xml)
        assert restored.realestate_type == RealestateType.LIEGENSCHAFT
        assert restored.square_measure == "12345.50"
        assert restored.realestate_identification.egrid == "CH123456789012"
        assert len(restored.named_meta_data) == 1

    def test_area(self):
        """Area type (all fields required)."""
        area = ECH0129Area(
            area_type=AreaType.GROUND_COVER,
            area_description_code=AreaDescriptionCode.GEBAEUDE,
            area_description="Wohngebaeude",
            area_value="450.00",
        )

        xml = area.to_xml()
        restored = ECH0129Area.from_xml(xml)
        assert restored.area_type == AreaType.GROUND_COVER
        assert restored.area_value == "450.00"

    def test_fiscal_ownership(self):
        """Fiscal ownership with denominator/numerator."""
        ownership = ECH0129FiscalOwnership(
            accession_date=date(2024, 1, 1),
            fiscal_relationship=FiscalRelationship.OWNER,
            denominator="1.000",
            numerator="1.000",
        )

        xml = ownership.to_xml()
        restored = ECH0129FiscalOwnership.from_xml(xml)
        assert restored.fiscal_relationship == FiscalRelationship.OWNER
        assert restored.denominator == "1.000"


# ---------------------------------------------------------------------------
# Test: Street and locality types
# ---------------------------------------------------------------------------

class TestStreetLocalityGraph:
    """Street, locality, and place name composite types."""

    def test_street_full(self):
        """Street with description entries, status, kind."""
        street = ECH0129Street(
            esid=10000001,
            is_official_description=True,
            official_street_number=12345,
            local_id=make_named_id("STR", "100"),
            street_kind=StreetKind.STREET,
            description=make_street_description(),
            street_status=StreetStatus.EXISTING,
        )

        xml = street.to_xml()
        assert xml.tag.endswith('}street')

        restored = ECH0129Street.from_xml(xml)
        assert restored.esid == 10000001
        assert restored.street_kind == StreetKind.STREET
        assert len(restored.description.entries) == 1
        assert restored.description.entries[0].description_long == "Dorfstrasse"

    def test_locality_full(self):
        """Locality with zip code and name."""
        locality = ECH0129Locality(
            swiss_zip_code=3983,
            swiss_zip_code_add_on="00",
            name=ECH0129LocalityName(
                name_long="Bister",
                name_short="Bister",
            ),
        )

        xml = locality.to_xml()
        assert xml.tag.endswith('}locality')

        restored = ECH0129Locality.from_xml(xml)
        assert restored.swiss_zip_code == 3983
        assert restored.name.name_long == "Bister"

    def test_place_name(self):
        """Place name with type and name."""
        place = ECH0129PlaceName(
            place_name_type=PlaceNameType.ORTSNAME,
            local_geographical_name="Bister",
        )

        xml = place.to_xml()
        restored = ECH0129PlaceName.from_xml(xml)
        assert restored.place_name_type == PlaceNameType.ORTSNAME
        assert restored.local_geographical_name == "Bister"


# ---------------------------------------------------------------------------
# Test: Cadastral types
# ---------------------------------------------------------------------------

class TestCadastralGraph:
    """Cadastral types: right, map, surveyor remark, SDR, partial area."""

    def test_right(self):
        right = ECH0129Right(ereid="EREID-001")
        xml = right.to_xml()
        restored = ECH0129Right.from_xml(xml)
        assert restored.ereid == "EREID-001"

    def test_cadastral_map(self):
        cm = ECH0129CadastralMap(
            map_number="1234",
            ident_dn="DN-001",
        )
        xml = cm.to_xml()
        restored = ECH0129CadastralMap.from_xml(xml)
        assert restored.map_number == "1234"

    def test_cadastral_surveyor_remark(self):
        remark = ECH0129CadastralSurveyorRemark(
            remark_type=RemarkType.OTHER,
            remark_text="Gartenhaus ohne EGID",
            object_id="OBJ-123",
        )
        xml = remark.to_xml()
        restored = ECH0129CadastralSurveyorRemark.from_xml(xml)
        assert restored.remark_type == RemarkType.OTHER
        assert restored.remark_text == "Gartenhaus ohne EGID"

    def test_covering_area_of_sdr(self):
        sdr = ECH0129CoveringAreaOfSDR(
            square_measure="500.00",
            realestate_identification=make_realestate_id(),
        )
        xml = sdr.to_xml()
        restored = ECH0129CoveringAreaOfSDR.from_xml(xml)
        assert restored.square_measure == "500.00"

    def test_partial_area_of_building(self):
        partial = ECH0129PartialAreaOfBuilding(
            square_measure="120.50",
        )
        xml = partial.to_xml()
        restored = ECH0129PartialAreaOfBuilding.from_xml(xml)
        assert restored.square_measure == "120.50"


# ---------------------------------------------------------------------------
# Test: Dwelling with usage
# ---------------------------------------------------------------------------

class TestDwellingGraph:
    """Dwelling with identification and usage types."""

    def test_dwelling_full(self):
        """Complete dwelling with all common fields."""
        dwelling = ECH0129Dwelling(
            local_id=[make_named_id("WHNG", "1")],
            administrative_dwelling_no="W001",
            ewid=1,
            physical_dwelling_no="1OG-links",
            date_of_construction=ECH0129DatePartiallyKnown(
                year_month_day=date(1985, 6, 15)
            ),
            no_of_habitable_rooms=4,
            floor=3101,  # 1. Stock
            location_of_dwelling_on_floor="lks",
            multiple_floor=False,
            kitchen=True,
            surface_area_of_dwelling=95,
            status=DwellingStatus.EXISTING,
            dwelling_usage=ECH0129DwellingUsage(
                usage_code=DwellingUsageCode.MAIN_RESIDENCE,
                revision_date=date(2024, 1, 1),
            ),
            dwelling_free_text=["Parkett"],
        )

        xml = dwelling.to_xml()
        assert xml.tag.endswith('}dwelling')

        restored = ECH0129Dwelling.from_xml(xml)
        assert restored.ewid == 1
        assert restored.no_of_habitable_rooms == 4
        assert restored.floor == 3101
        assert restored.kitchen is True
        assert restored.dwelling_usage is not None
        assert restored.dwelling_usage.usage_code == DwellingUsageCode.MAIN_RESIDENCE
        assert len(restored.dwelling_free_text) == 1


# ---------------------------------------------------------------------------
# Test: Entrance types with address
# ---------------------------------------------------------------------------

class TestEntranceGraph:
    """Building entrance + building address composition."""

    def test_building_address_full(self):
        """BuildingAddress with full address data."""
        from openmun_ech.ech0129.v6.entrance import (
            ECH0129AddressStreetDescription,
            ECH0129AddressStreetEntry,
        )

        address = ECH0129BuildingAddress(
            egaid=100000001,
            egid=123456789,
            edid=0,
            street_description=ECH0129AddressStreetDescription(
                entries=[
                    ECH0129AddressStreetEntry(
                        language=StreetLanguage.GERMAN,
                        description_long="Dorfstrasse",
                    )
                ]
            ),
            building_entrance_no="A",
            swiss_zip_code=3983,
            swiss_zip_code_add_on="00",
            locality="Bister",
            municipality_id=6172,
            municipality_name="Bister",
            status=BuildingStatus.EXISTING,
        )

        xml = address.to_xml()
        assert xml.tag.endswith('}buildingAddress')

        restored = ECH0129BuildingAddress.from_xml(xml)
        assert restored.municipality_name == "Bister"
        assert restored.building_entrance_no == "A"

    def test_entrance_identification_roundtrip(self):
        """BuildingEntranceIdentification roundtrip."""
        ident = ECH0129BuildingEntranceIdentification(
            egid=123456789,
            egaid=100000001,
            edid=0,
            local_id=make_named_id("EINGANG", "1"),
        )
        xml = ident.to_xml()
        restored = ECH0129BuildingEntranceIdentification.from_xml(xml)
        assert restored.egid == 123456789
        assert restored.egaid == 100000001


# ---------------------------------------------------------------------------
# Test: Package-level imports work correctly
# ---------------------------------------------------------------------------

class TestPackageImports:
    """Verify that all 98 exports are importable from the package."""

    def test_all_exports_importable(self):
        """All __all__ entries are importable."""
        import openmun_ech.ech0129 as pkg
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            assert obj is not None, f"{name} is None"

    def test_enum_count(self):
        """38 enum classes exported."""
        import openmun_ech.ech0129 as pkg
        from enum import EnumType
        enums = [name for name in pkg.__all__
                 if isinstance(getattr(pkg, name), EnumType)]
        assert len(enums) == 38

    def test_model_count(self):
        """60 model classes exported."""
        import openmun_ech.ech0129 as pkg
        from enum import EnumType
        models = [name for name in pkg.__all__
                  if not isinstance(getattr(pkg, name), EnumType)]
        assert len(models) == 60
