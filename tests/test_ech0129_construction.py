"""Tests for eCH-0129 v6.0.0 construction types (Session 6).

Verifies:
1. Model creation — required/optional fields, default values
2. Validation — field constraints, xs:choice enforcement, date ranges
3. Serialization roundtrip — to_xml() → from_xml() → compare
4. XML element names and ordering (xs:sequence)
5. Cross-namespace serialization (wrapper pattern for municipality/country)
"""

import xml.etree.ElementTree as ET
from datetime import date

import pytest

from openmun_ech.core import NS
from openmun_ech.ech0007.v5 import CantonAbbreviation, CantonFLAbbreviation
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
from openmun_ech.ech0129.v6.construction import (
    ECH0129ConstructionLocalisation,
    ECH0129ConstructionProject,
    ECH0129ConstructionProjectIdentification,
    ECH0129KindOfConstructionWork,
)

NS_0129 = NS.ECH0129_V6
NS_0007 = NS.ECH0007_V6
NS_0008 = NS.ECH0008_V3


# ===========================================================================
# Helpers
# ===========================================================================

def _make_named_id(category='IDBBP', value='12345'):
    return ECH0129NamedId(id_category=category, id_value=value)


def _make_municipality():
    return ECH0007v6SwissMunicipality(
        municipality_id='6196',
        municipality_name='Bister',
        canton_abbreviation=CantonAbbreviation.VS,
    )


def _make_country():
    return ECH0008Country(
        country_id='8100',
        country_id_iso2='CH',
        country_name_short='Schweiz',
    )


def _make_fl_municipality():
    return ECH0007v6SwissAndFLMunicipality(
        municipality_id='6196',
        municipality_name='Bister',
        canton_fl_abbreviation=CantonFLAbbreviation.VS,
    )


def _make_identification():
    return ECH0129ConstructionProjectIdentification(
        local_id=[_make_named_id()],
    )


def _make_localisation():
    return ECH0129ConstructionLocalisation(
        municipality=_make_municipality(),
    )


def _make_minimal_project():
    return ECH0129ConstructionProject(
        status=ProjectStatus.SUBMITTED,
        description='Neubau Einfamilienhaus',
    )


# ===========================================================================
# ECH0129ConstructionLocalisation
# ===========================================================================

class TestConstructionLocalisation:
    def test_municipality_branch(self):
        loc = ECH0129ConstructionLocalisation(
            municipality=_make_municipality(),
        )
        assert loc.municipality is not None
        assert loc.canton is None
        assert loc.country is None

    def test_canton_branch(self):
        loc = ECH0129ConstructionLocalisation(
            canton=CantonAbbreviation.VS,
        )
        assert loc.municipality is None
        assert loc.canton == CantonAbbreviation.VS
        assert loc.country is None

    def test_country_branch(self):
        loc = ECH0129ConstructionLocalisation(
            country=_make_country(),
        )
        assert loc.municipality is None
        assert loc.canton is None
        assert loc.country is not None

    def test_choice_none_rejected(self):
        """xs:choice — at least one must be set."""
        with pytest.raises(ValueError, match='must set one of'):
            ECH0129ConstructionLocalisation()

    def test_choice_multiple_rejected(self):
        """xs:choice — at most one allowed."""
        with pytest.raises(ValueError, match='only one of'):
            ECH0129ConstructionLocalisation(
                municipality=_make_municipality(),
                canton=CantonAbbreviation.VS,
            )

    def test_roundtrip_municipality(self):
        loc = ECH0129ConstructionLocalisation(
            municipality=_make_municipality(),
        )
        xml = loc.to_xml()
        parsed = ECH0129ConstructionLocalisation.from_xml(xml)
        assert parsed.municipality is not None
        assert parsed.municipality.municipality_id == '6196'
        assert parsed.municipality.municipality_name == 'Bister'
        assert parsed.canton is None
        assert parsed.country is None

    def test_roundtrip_canton(self):
        loc = ECH0129ConstructionLocalisation(
            canton=CantonAbbreviation.BE,
        )
        xml = loc.to_xml()
        parsed = ECH0129ConstructionLocalisation.from_xml(xml)
        assert parsed.canton == CantonAbbreviation.BE
        assert parsed.municipality is None
        assert parsed.country is None

    def test_roundtrip_country(self):
        loc = ECH0129ConstructionLocalisation(
            country=_make_country(),
        )
        xml = loc.to_xml()
        parsed = ECH0129ConstructionLocalisation.from_xml(xml)
        assert parsed.country is not None
        assert parsed.country.country_name_short == 'Schweiz'
        assert parsed.municipality is None
        assert parsed.canton is None

    def test_xml_municipality_wrapper(self):
        """Municipality uses wrapper pattern: eCH-0129 wrapper, eCH-0007 children."""
        loc = ECH0129ConstructionLocalisation(
            municipality=_make_municipality(),
        )
        xml = loc.to_xml()
        muni_elem = xml.find(f'{{{NS_0129}}}municipality')
        assert muni_elem is not None
        # Children are in eCH-0007 namespace
        assert muni_elem.find(f'{{{NS_0007}}}municipalityId') is not None
        assert muni_elem.find(f'{{{NS_0007}}}municipalityName') is not None

    def test_xml_canton_plain_text(self):
        """Canton is a simple text element in eCH-0129 namespace."""
        loc = ECH0129ConstructionLocalisation(
            canton=CantonAbbreviation.VS,
        )
        xml = loc.to_xml()
        canton_elem = xml.find(f'{{{NS_0129}}}canton')
        assert canton_elem is not None
        assert canton_elem.text == 'VS'

    def test_xml_country_wrapper(self):
        """Country uses wrapper pattern: eCH-0129 wrapper, eCH-0008 children."""
        loc = ECH0129ConstructionLocalisation(
            country=_make_country(),
        )
        xml = loc.to_xml()
        country_elem = xml.find(f'{{{NS_0129}}}country')
        assert country_elem is not None
        assert country_elem.find(f'{{{NS_0008}}}countryNameShort') is not None


# ===========================================================================
# ECH0129ConstructionProjectIdentification
# ===========================================================================

class TestConstructionProjectIdentification:
    def test_minimal(self):
        """Only required field: localID (min 1 entry)."""
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
        )
        assert len(cpi.local_id) == 1
        assert cpi.eproid is None
        assert cpi.official_construction_project_file_no is None
        assert cpi.extension_of_official_construction_project_file_no is None

    def test_all_fields(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id(), _make_named_id('CANTON', '99')],
            eproid=123456,
            official_construction_project_file_no='BP-2024-001',
            extension_of_official_construction_project_file_no=1,
        )
        assert len(cpi.local_id) == 2
        assert cpi.eproid == 123456
        assert cpi.official_construction_project_file_no == 'BP-2024-001'
        assert cpi.extension_of_official_construction_project_file_no == 1

    def test_local_id_required(self):
        """localID must have at least 1 entry."""
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(local_id=[])

    def test_local_id_missing(self):
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification()

    def test_eproid_range(self):
        """EPROIDType: 1–900000000."""
        ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()], eproid=1
        )
        ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()], eproid=900000000
        )
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(
                local_id=[_make_named_id()], eproid=0
            )
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(
                local_id=[_make_named_id()], eproid=900000001
            )

    def test_file_no_constraints(self):
        """officialConstructionProjectFileNo: 1–15 chars."""
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(
                local_id=[_make_named_id()],
                official_construction_project_file_no='',
            )
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(
                local_id=[_make_named_id()],
                official_construction_project_file_no='1234567890123456',  # 16
            )

    def test_extension_range(self):
        """extensionOfOfficialConstructionProjectFileNo: 0–99."""
        ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
            extension_of_official_construction_project_file_no=0,
        )
        ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
            extension_of_official_construction_project_file_no=99,
        )
        with pytest.raises(Exception):
            ECH0129ConstructionProjectIdentification(
                local_id=[_make_named_id()],
                extension_of_official_construction_project_file_no=100,
            )

    def test_roundtrip(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id('IDBBP', '12345')],
            eproid=42,
            official_construction_project_file_no='BP-2024',
            extension_of_official_construction_project_file_no=3,
        )
        xml = cpi.to_xml()
        parsed = ECH0129ConstructionProjectIdentification.from_xml(xml)
        assert len(parsed.local_id) == 1
        assert parsed.local_id[0].id_category == 'IDBBP'
        assert parsed.local_id[0].id_value == '12345'
        assert parsed.eproid == 42
        assert parsed.official_construction_project_file_no == 'BP-2024'
        assert parsed.extension_of_official_construction_project_file_no == 3

    def test_roundtrip_minimal(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
        )
        xml = cpi.to_xml()
        parsed = ECH0129ConstructionProjectIdentification.from_xml(xml)
        assert len(parsed.local_id) == 1
        assert parsed.eproid is None

    def test_roundtrip_multiple_local_ids(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[
                _make_named_id('IDBBP', '1'),
                _make_named_id('CANTON', '2'),
                _make_named_id('FEDERAL', '3'),
            ],
        )
        xml = cpi.to_xml()
        parsed = ECH0129ConstructionProjectIdentification.from_xml(xml)
        assert len(parsed.local_id) == 3
        assert parsed.local_id[0].id_category == 'IDBBP'
        assert parsed.local_id[1].id_category == 'CANTON'
        assert parsed.local_id[2].id_category == 'FEDERAL'

    def test_xml_element_names(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
            eproid=100,
            official_construction_project_file_no='BP-1',
            extension_of_official_construction_project_file_no=5,
        )
        xml = cpi.to_xml()
        assert xml.find(f'{{{NS_0129}}}localID') is not None
        assert xml.find(f'{{{NS_0129}}}EPROID') is not None
        assert xml.find(f'{{{NS_0129}}}officialConstructionProjectFileNo') is not None
        assert xml.find(
            f'{{{NS_0129}}}extensionOfOfficialConstructionProjectFileNo'
        ) is not None

    def test_xml_element_order(self):
        cpi = ECH0129ConstructionProjectIdentification(
            local_id=[_make_named_id()],
            eproid=1,
            official_construction_project_file_no='X',
            extension_of_official_construction_project_file_no=0,
        )
        xml = cpi.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'localID', 'EPROID',
            'officialConstructionProjectFileNo',
            'extensionOfOfficialConstructionProjectFileNo',
        ]


# ===========================================================================
# ECH0129KindOfConstructionWork
# ===========================================================================

class TestKindOfConstructionWork:
    def test_minimal(self):
        """Only required field: kindOfWork."""
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
        )
        assert kcw.kind_of_work == KindOfWork.NEW_CONSTRUCTION
        assert kcw.arbid is None
        assert kcw.energetic_restauration is None
        assert kcw.renovation_heatingsystem is None
        assert kcw.inner_conversion_renovation is None
        assert kcw.conversion is None
        assert kcw.extension_heightening_heated is None
        assert kcw.extension_heightening_not_heated is None
        assert kcw.thermic_solar_facility is None
        assert kcw.photovoltaic_solar_facility is None
        assert kcw.other_works is None

    def test_all_fields(self):
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.CONVERSION,
            arbid=999999999999,
            energetic_restauration=True,
            renovation_heatingsystem=True,
            inner_conversion_renovation=False,
            conversion=True,
            extension_heightening_heated=False,
            extension_heightening_not_heated=False,
            thermic_solar_facility=True,
            photovoltaic_solar_facility=True,
            other_works=False,
        )
        assert kcw.kind_of_work == KindOfWork.CONVERSION
        assert kcw.arbid == 999999999999
        assert kcw.energetic_restauration is True
        assert kcw.other_works is False

    def test_kind_of_work_required(self):
        with pytest.raises(Exception):
            ECH0129KindOfConstructionWork()

    def test_arbid_range(self):
        """ARBIDType: 1–999999999999."""
        ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION, arbid=1
        )
        ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION, arbid=999999999999
        )
        with pytest.raises(Exception):
            ECH0129KindOfConstructionWork(
                kind_of_work=KindOfWork.NEW_CONSTRUCTION, arbid=0
            )
        with pytest.raises(Exception):
            ECH0129KindOfConstructionWork(
                kind_of_work=KindOfWork.NEW_CONSTRUCTION,
                arbid=1000000000000,
            )

    def test_roundtrip_minimal(self):
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
        )
        xml = kcw.to_xml()
        parsed = ECH0129KindOfConstructionWork.from_xml(xml)
        assert parsed.kind_of_work == KindOfWork.NEW_CONSTRUCTION
        assert parsed.arbid is None
        assert parsed.energetic_restauration is None

    def test_roundtrip_full(self):
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.CONVERSION,
            arbid=42,
            energetic_restauration=True,
            renovation_heatingsystem=False,
            inner_conversion_renovation=True,
            conversion=True,
            extension_heightening_heated=False,
            extension_heightening_not_heated=True,
            thermic_solar_facility=False,
            photovoltaic_solar_facility=True,
            other_works=False,
        )
        xml = kcw.to_xml()
        parsed = ECH0129KindOfConstructionWork.from_xml(xml)
        assert parsed.kind_of_work == KindOfWork.CONVERSION
        assert parsed.arbid == 42
        assert parsed.energetic_restauration is True
        assert parsed.renovation_heatingsystem is False
        assert parsed.inner_conversion_renovation is True
        assert parsed.conversion is True
        assert parsed.extension_heightening_heated is False
        assert parsed.extension_heightening_not_heated is True
        assert parsed.thermic_solar_facility is False
        assert parsed.photovoltaic_solar_facility is True
        assert parsed.other_works is False

    def test_xml_element_names(self):
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
            arbid=1,
            energetic_restauration=True,
            photovoltaic_solar_facility=False,
        )
        xml = kcw.to_xml()
        assert xml.find(f'{{{NS_0129}}}kindOfWork') is not None
        assert xml.find(f'{{{NS_0129}}}ARBID') is not None
        assert xml.find(f'{{{NS_0129}}}energeticRestauration') is not None
        assert xml.find(f'{{{NS_0129}}}photovoltaicSolarFacility') is not None

    def test_xml_element_order(self):
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
            arbid=1,
            energetic_restauration=True,
            renovation_heatingsystem=False,
            inner_conversion_renovation=True,
            conversion=False,
            extension_heightening_heated=True,
            extension_heightening_not_heated=False,
            thermic_solar_facility=True,
            photovoltaic_solar_facility=False,
            other_works=True,
        )
        xml = kcw.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'kindOfWork', 'ARBID',
            'energeticRestauration', 'renovationHeatingsystem',
            'innerConversionRenovation', 'conversion',
            'extensionHeighteningHeated', 'extensionHeighteningNotHeated',
            'thermicSolarFacility', 'photovoltaicSolarFacility',
            'otherWorks',
        ]

    def test_boolean_serialization(self):
        """Boolean values serialize as 'true'/'false' in XML."""
        kcw = ECH0129KindOfConstructionWork(
            kind_of_work=KindOfWork.NEW_CONSTRUCTION,
            energetic_restauration=True,
            renovation_heatingsystem=False,
        )
        xml = kcw.to_xml()
        assert xml.find(f'{{{NS_0129}}}energeticRestauration').text == 'true'
        assert xml.find(f'{{{NS_0129}}}renovationHeatingsystem').text == 'false'


# ===========================================================================
# ECH0129ConstructionProject
# ===========================================================================

class TestConstructionProject:
    def test_minimal(self):
        """Only required fields: status + description."""
        cp = _make_minimal_project()
        assert cp.status == ProjectStatus.SUBMITTED
        assert cp.description == 'Neubau Einfamilienhaus'
        assert cp.construction_project_identification is None
        assert cp.type_of_construction_project is None
        assert cp.construction_localisation is None
        assert cp.type_of_permit is None
        assert cp.building_permit_issue_date is None
        assert cp.project_announcement_date is None
        assert cp.construction_authorisation_denied_date is None
        assert cp.project_start_date is None
        assert cp.project_completion_date is None
        assert cp.project_suspension_date is None
        assert cp.withdrawal_date is None
        assert cp.non_realisation_date is None
        assert cp.total_costs_of_project is None
        assert cp.type_of_client is None
        assert cp.type_of_construction is None
        assert cp.duration_of_construction_phase is None
        assert cp.number_of_concerned_buildings is None
        assert cp.number_of_concerned_dwellings is None
        assert cp.project_free_text == []
        assert cp.municipality == []

    def test_all_fields(self):
        cp = ECH0129ConstructionProject(
            construction_project_identification=_make_identification(),
            type_of_construction_project=TypeOfConstructionProject.BUILDING_CONSTRUCTION,
            construction_localisation=_make_localisation(),
            type_of_permit=TypeOfPermit.BAUZONE,
            building_permit_issue_date=date(2024, 3, 15),
            project_announcement_date=date(2024, 1, 10),
            construction_authorisation_denied_date=None,
            project_start_date=date(2024, 6, 1),
            project_completion_date=date(2025, 12, 31),
            project_suspension_date=None,
            withdrawal_date=None,
            non_realisation_date=None,
            total_costs_of_project=500000,
            status=ProjectStatus.CONSTRUCTION_STARTED,
            type_of_client=TypeOfClient.PRIVATPERSONEN,
            type_of_construction=TypeOfConstruction.EINFAMILIENHAEUSER_FREISTEHEND,
            description='Neubau Einfamilienhaus mit Garage',
            duration_of_construction_phase=18,
            number_of_concerned_buildings=1,
            number_of_concerned_dwellings=1,
            project_free_text=['Parzelle 1234', 'Zone W2'],
            municipality=[_make_fl_municipality()],
        )
        assert cp.type_of_construction_project == TypeOfConstructionProject.BUILDING_CONSTRUCTION
        assert cp.type_of_permit == TypeOfPermit.BAUZONE
        assert cp.building_permit_issue_date == date(2024, 3, 15)
        assert cp.total_costs_of_project == 500000
        assert cp.type_of_client == TypeOfClient.PRIVATPERSONEN
        assert cp.duration_of_construction_phase == 18
        assert len(cp.project_free_text) == 2
        assert len(cp.municipality) == 1

    def test_status_required(self):
        with pytest.raises(Exception):
            ECH0129ConstructionProject(description='Test project')

    def test_description_required(self):
        with pytest.raises(Exception):
            ECH0129ConstructionProject(status=ProjectStatus.SUBMITTED)

    def test_description_min_length(self):
        """constructionProjectDescriptionType: minLength=3."""
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED, description='AB',
            )

    def test_description_max_length(self):
        """constructionProjectDescriptionType: maxLength=1000."""
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED, description='X' * 1001,
            )

    def test_date_min_2000(self):
        """All 8 date fields require >= 2000-01-01."""
        date_fields = [
            'building_permit_issue_date',
            'project_announcement_date',
            'construction_authorisation_denied_date',
            'project_start_date',
            'project_completion_date',
            'project_suspension_date',
            'withdrawal_date',
            'non_realisation_date',
        ]
        for field_name in date_fields:
            with pytest.raises(ValueError, match='2000-01-01'):
                ECH0129ConstructionProject(
                    status=ProjectStatus.SUBMITTED,
                    description='Test project',
                    **{field_name: date(1999, 12, 31)},
                )

    def test_date_at_boundary(self):
        """2000-01-01 is the minimum — should be accepted."""
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test project',
            building_permit_issue_date=date(2000, 1, 1),
        )
        assert cp.building_permit_issue_date == date(2000, 1, 1)

    def test_total_costs_range(self):
        """totalCostsOfProjectType: 1000–999999999000."""
        ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Min cost',
            total_costs_of_project=1000,
        )
        ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Max cost',
            total_costs_of_project=999999999000,
        )
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Too cheap',
                total_costs_of_project=999,
            )
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Too expensive',
                total_costs_of_project=999999999001,
            )

    def test_duration_range(self):
        """durationOfConstructionPhaseType: 1–999."""
        ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test',
            duration_of_construction_phase=1,
        )
        ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test',
            duration_of_construction_phase=999,
        )
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                duration_of_construction_phase=0,
            )
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                duration_of_construction_phase=1000,
            )

    def test_number_of_buildings_range(self):
        """numberOfConcernedBuildingsType: 1–999."""
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                number_of_concerned_buildings=0,
            )
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                number_of_concerned_buildings=1000,
            )

    def test_number_of_dwellings_range(self):
        """numberOfConcernedDwellingsType: 1–999."""
        with pytest.raises(Exception):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                number_of_concerned_dwellings=0,
            )

    def test_free_text_max_occurrences(self):
        """projectFreeText: maxOccurs="2"."""
        with pytest.raises(ValueError, match='maxOccurs=2'):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                project_free_text=['a', 'b', 'c'],
            )

    def test_free_text_item_length(self):
        """freeTextType: 1–32 chars per item."""
        with pytest.raises(ValueError, match='1–32 chars'):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                project_free_text=[''],
            )
        with pytest.raises(ValueError, match='1–32 chars'):
            ECH0129ConstructionProject(
                status=ProjectStatus.SUBMITTED,
                description='Test',
                project_free_text=['X' * 33],
            )

    def test_free_text_valid(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test project',
            project_free_text=['Note 1', 'Note 2'],
        )
        assert len(cp.project_free_text) == 2

    def test_roundtrip_minimal(self):
        cp = _make_minimal_project()
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.status == ProjectStatus.SUBMITTED
        assert parsed.description == 'Neubau Einfamilienhaus'
        assert parsed.construction_project_identification is None
        assert parsed.project_free_text == []
        assert parsed.municipality == []

    def test_roundtrip_with_dates(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.PERMIT_GRANTED,
            description='Umbau Scheune',
            building_permit_issue_date=date(2024, 3, 15),
            project_start_date=date(2024, 6, 1),
            project_completion_date=date(2025, 3, 31),
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.building_permit_issue_date == date(2024, 3, 15)
        assert parsed.project_start_date == date(2024, 6, 1)
        assert parsed.project_completion_date == date(2025, 3, 31)
        assert parsed.project_announcement_date is None

    def test_roundtrip_with_nested_types(self):
        cp = ECH0129ConstructionProject(
            construction_project_identification=_make_identification(),
            construction_localisation=_make_localisation(),
            status=ProjectStatus.SUBMITTED,
            description='Neubau mit Identifikation',
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.construction_project_identification is not None
        assert len(parsed.construction_project_identification.local_id) == 1
        assert parsed.construction_localisation is not None
        assert parsed.construction_localisation.municipality is not None

    def test_roundtrip_with_enums(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.COMPLETED,
            description='Fertiggestelltes Projekt',
            type_of_construction_project=TypeOfConstructionProject.BUILDING_CONSTRUCTION,
            type_of_permit=TypeOfPermit.BAUZONE,
            type_of_client=TypeOfClient.PRIVATPERSONEN,
            type_of_construction=TypeOfConstruction.MEHRFAMILIENHAEUSER,
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.type_of_construction_project == TypeOfConstructionProject.BUILDING_CONSTRUCTION
        assert parsed.type_of_permit == TypeOfPermit.BAUZONE
        assert parsed.type_of_client == TypeOfClient.PRIVATPERSONEN
        assert parsed.type_of_construction == TypeOfConstruction.MEHRFAMILIENHAEUSER

    def test_roundtrip_with_integers(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Grosses Projekt',
            total_costs_of_project=5000000,
            duration_of_construction_phase=24,
            number_of_concerned_buildings=3,
            number_of_concerned_dwellings=12,
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.total_costs_of_project == 5000000
        assert parsed.duration_of_construction_phase == 24
        assert parsed.number_of_concerned_buildings == 3
        assert parsed.number_of_concerned_dwellings == 12

    def test_roundtrip_with_free_text(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Mit Freitext',
            project_free_text=['Bemerkung 1', 'Bemerkung 2'],
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert parsed.project_free_text == ['Bemerkung 1', 'Bemerkung 2']

    def test_roundtrip_with_municipalities(self):
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Gemeindeueberschreitend',
            municipality=[
                _make_fl_municipality(),
                ECH0007v6SwissAndFLMunicipality(
                    municipality_id='6197',
                    municipality_name='Ried-Moerel',
                    canton_fl_abbreviation=CantonFLAbbreviation.VS,
                ),
            ],
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        assert len(parsed.municipality) == 2
        assert parsed.municipality[0].municipality_name == 'Bister'
        assert parsed.municipality[1].municipality_name == 'Ried-Moerel'

    def test_roundtrip_full(self):
        """Full roundtrip with all 22 fields populated."""
        cp = ECH0129ConstructionProject(
            construction_project_identification=_make_identification(),
            type_of_construction_project=TypeOfConstructionProject.BUILDING_CONSTRUCTION,
            construction_localisation=_make_localisation(),
            type_of_permit=TypeOfPermit.BAUZONE,
            building_permit_issue_date=date(2024, 3, 15),
            project_announcement_date=date(2024, 1, 10),
            construction_authorisation_denied_date=date(2024, 2, 1),
            project_start_date=date(2024, 6, 1),
            project_completion_date=date(2025, 12, 31),
            project_suspension_date=date(2025, 3, 1),
            withdrawal_date=date(2025, 6, 15),
            non_realisation_date=date(2025, 9, 1),
            total_costs_of_project=500000,
            status=ProjectStatus.CONSTRUCTION_STARTED,
            type_of_client=TypeOfClient.PRIVATPERSONEN,
            type_of_construction=TypeOfConstruction.EINFAMILIENHAEUSER_FREISTEHEND,
            description='Neubau Einfamilienhaus mit Garage',
            duration_of_construction_phase=18,
            number_of_concerned_buildings=1,
            number_of_concerned_dwellings=1,
            project_free_text=['Parzelle 1234'],
            municipality=[_make_fl_municipality()],
        )
        xml = cp.to_xml()
        parsed = ECH0129ConstructionProject.from_xml(xml)
        # Spot-check key fields across all categories
        assert parsed.status == ProjectStatus.CONSTRUCTION_STARTED
        assert parsed.description == 'Neubau Einfamilienhaus mit Garage'
        assert parsed.building_permit_issue_date == date(2024, 3, 15)
        assert parsed.withdrawal_date == date(2025, 6, 15)
        assert parsed.total_costs_of_project == 500000
        assert parsed.duration_of_construction_phase == 18
        assert len(parsed.project_free_text) == 1
        assert len(parsed.municipality) == 1
        assert parsed.construction_project_identification is not None
        assert parsed.construction_localisation is not None

    def test_xml_element_order_minimal(self):
        """Required elements appear in correct XSD order."""
        cp = _make_minimal_project()
        xml = cp.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == ['status', 'description']

    def test_xml_element_order_full(self):
        """All 22 elements in correct XSD sequence order."""
        cp = ECH0129ConstructionProject(
            construction_project_identification=_make_identification(),
            type_of_construction_project=TypeOfConstructionProject.CIVIL_ENGINEERING,
            construction_localisation=_make_localisation(),
            type_of_permit=TypeOfPermit.BAUZONE,
            building_permit_issue_date=date(2024, 1, 1),
            project_announcement_date=date(2024, 1, 2),
            construction_authorisation_denied_date=date(2024, 1, 3),
            project_start_date=date(2024, 1, 4),
            project_completion_date=date(2024, 1, 5),
            project_suspension_date=date(2024, 1, 6),
            withdrawal_date=date(2024, 1, 7),
            non_realisation_date=date(2024, 1, 8),
            total_costs_of_project=100000,
            status=ProjectStatus.SUBMITTED,
            type_of_client=TypeOfClient.PRIVATPERSONEN,
            type_of_construction=TypeOfConstruction.BUEROGEBAEUDE,
            description='Element order test',
            duration_of_construction_phase=12,
            number_of_concerned_buildings=2,
            number_of_concerned_dwellings=5,
            project_free_text=['Note'],
            municipality=[_make_fl_municipality()],
        )
        xml = cp.to_xml()
        children = [child.tag.split('}')[1] for child in xml]
        assert children == [
            'constructionProjectIdentification',
            'typeOfConstructionProject',
            'constructionLocalisation',
            'typeOfPermit',
            'buildingPermitIssueDate',
            'projectAnnouncementDate',
            'constructionAuthorisationDeniedDate',
            'projectStartDate',
            'projectCompletionDate',
            'projectSuspensionDate',
            'withdrawalDate',
            'nonRealisationDate',
            'totalCostsOfProject',
            'status',
            'typeOfClient',
            'typeOfConstruction',
            'description',
            'durationOfConstructionPhase',
            'numberOfConcernedBuildings',
            'numberOfConcernedDwellings',
            'projectFreeText',
            'municipality',
        ]

    def test_xml_municipality_wrapper(self):
        """Municipality list uses wrapper pattern with eCH-0007 v6 children."""
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test',
            municipality=[_make_fl_municipality()],
        )
        xml = cp.to_xml()
        muni_elem = xml.find(f'{{{NS_0129}}}municipality')
        assert muni_elem is not None
        # Children in eCH-0007 namespace
        assert muni_elem.find(f'{{{NS_0007}}}municipalityId') is not None
        assert muni_elem.find(f'{{{NS_0007}}}municipalityName') is not None

    def test_xml_free_text_repeated(self):
        """projectFreeText creates repeated elements."""
        cp = ECH0129ConstructionProject(
            status=ProjectStatus.SUBMITTED,
            description='Test',
            project_free_text=['First', 'Second'],
        )
        xml = cp.to_xml()
        texts = xml.findall(f'{{{NS_0129}}}projectFreeText')
        assert len(texts) == 2
        assert texts[0].text == 'First'
        assert texts[1].text == 'Second'

    def test_double_roundtrip_stability(self):
        """Serialize → parse → serialize → parse must produce identical result."""
        cp = ECH0129ConstructionProject(
            construction_project_identification=_make_identification(),
            construction_localisation=ECH0129ConstructionLocalisation(
                canton=CantonAbbreviation.VS,
            ),
            status=ProjectStatus.PERMIT_GRANTED,
            description='Stability test',
            building_permit_issue_date=date(2024, 5, 20),
            total_costs_of_project=250000,
            project_free_text=['Remark'],
            municipality=[_make_fl_municipality()],
        )
        xml1 = cp.to_xml()
        parsed1 = ECH0129ConstructionProject.from_xml(xml1)
        xml2 = parsed1.to_xml()
        parsed2 = ECH0129ConstructionProject.from_xml(xml2)

        assert parsed2.status == parsed1.status
        assert parsed2.description == parsed1.description
        assert parsed2.building_permit_issue_date == parsed1.building_permit_issue_date
        assert parsed2.total_costs_of_project == parsed1.total_costs_of_project
        assert parsed2.project_free_text == parsed1.project_free_text
        assert len(parsed2.municipality) == len(parsed1.municipality)
        assert parsed2.construction_localisation.canton == parsed1.construction_localisation.canton

    def test_all_project_status_values(self):
        """Every ProjectStatus enum value accepted."""
        for status in ProjectStatus:
            cp = ECH0129ConstructionProject(
                status=status, description='Status test'
            )
            assert cp.status == status

    def test_all_kind_of_work_values(self):
        """Every KindOfWork enum value accepted in kindOfConstructionWork."""
        for kind in KindOfWork:
            kcw = ECH0129KindOfConstructionWork(kind_of_work=kind)
            assert kcw.kind_of_work == kind
