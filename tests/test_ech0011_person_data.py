"""Tests for eCH-0011 Person Data Pydantic models."""

import xml.etree.ElementTree as ET
import pytest
from datetime import date
from pydantic import ValidationError

from openmun_ech.ech0011 import (
    ECH0011ForeignerName,
    ECH0011NameData,
    ECH0011GeneralPlace,
    ECH0011BirthData,
    ECH0011ReligionData,
    ECH0011SeparationData,
    ECH0011MaritalData,
    ECH0011CountryInfo,
    ECH0011NationalityData,
    ECH0011PlaceOfOrigin,
    ECH0011ResidencePermitData,
    ECH0011DeathPeriod,
    ECH0011DeathData,
    ECH0011Person,
)
from openmun_ech.ech0007 import ECH0007Municipality, CantonAbbreviation
from openmun_ech.ech0008 import ECH0008Country
from openmun_ech.ech0044 import ECH0044PersonIdentification, ECH0044NamedPersonId, ECH0044DatePartiallyKnown


class TestECH0011ForeignerName:
    """Test eCH-0011 foreigner name model."""

    def test_create_minimal(self):
        """Test creating foreigner name with minimal data."""
        name = ECH0011ForeignerName()
        assert name.name is None
        assert name.first_name is None

    def test_create_full(self):
        """Test creating foreigner name with all fields."""
        name = ECH0011ForeignerName(
            name="Müller",
            first_name="Hans"
        )
        assert name.name == "Müller"
        assert name.first_name == "Hans"

    def test_to_xml(self):
        """Test XML export."""
        name = ECH0011ForeignerName(
            name="Schmidt",
            first_name="Maria"
        )
        xml = name.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}nameOnForeignPassport'

        name_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}name')
        assert name_elem is not None
        assert name_elem.text == "Schmidt"

        first_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}firstName')
        assert first_elem is not None
        assert first_elem.text == "Maria"

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011ForeignerName(
            name="Müller",
            first_name="Hans"
        )
        xml = original.to_xml()
        parsed = ECH0011ForeignerName.from_xml(xml)

        assert parsed.name == original.name
        assert parsed.first_name == original.first_name


class TestECH0011NameData:
    """Test eCH-0011 name data model."""

    def test_create_minimal(self):
        """Test creating name data with minimal required fields."""
        name = ECH0011NameData(
            official_name="Meier",
            first_name="Anna"
        )
        assert name.official_name == "Meier"
        assert name.first_name == "Anna"
        assert name.original_name is None
        assert name.alliance_name is None

    def test_create_full(self):
        """Test creating name data with all fields."""
        name = ECH0011NameData(
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            alliance_name="Meier",
            alias_name="Anna M.",
            other_name="Marie",
            call_name="Anna",
            name_on_foreign_passport=ECH0011ForeignerName(
                name="Smith",
                first_name="Anna"
            )
        )
        assert name.official_name == "Meier-Schmidt"
        assert name.original_name == "Schmidt"
        assert name.alliance_name == "Meier"
        assert name.name_on_foreign_passport is not None

    def test_validate_required_fields(self):
        """Test that official_name and first_name are required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011NameData(official_name="Meier")

        with pytest.raises(ValidationError, match="Field required"):
            ECH0011NameData(first_name="Anna")

    def test_to_xml_minimal(self):
        """Test XML export with minimal data."""
        name = ECH0011NameData(
            official_name="Meier",
            first_name="Anna"
        )
        xml = name.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}nameData'

        official_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}officialName')
        assert official_elem is not None
        assert official_elem.text == "Meier"

        first_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}firstName')
        assert first_elem is not None
        assert first_elem.text == "Anna"

    def test_to_xml_full(self):
        """Test XML export with all fields."""
        name = ECH0011NameData(
            official_name="Meier-Schmidt",
            first_name="Anna Maria",
            original_name="Schmidt",
            alliance_name="Meier",
            call_name="Anna"
        )
        xml = name.to_xml()

        # Check all fields present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}officialName') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}firstName') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}originalName') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}allianceName') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}callName') is not None

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011NameData(
            official_name="Meier",
            first_name="Anna",
            original_name="Schmidt",
            alliance_name="Meier"
        )
        xml = original.to_xml()
        parsed = ECH0011NameData.from_xml(xml)

        assert parsed.official_name == original.official_name
        assert parsed.first_name == original.first_name
        assert parsed.original_name == original.original_name
        assert parsed.alliance_name == original.alliance_name


class TestECH0011GeneralPlace:
    """Test eCH-0011 general place model."""

    def test_create_unknown(self):
        """Test creating unknown place."""
        place = ECH0011GeneralPlace(unknown=True)
        assert place.unknown is True
        assert place.swiss_municipality is None
        assert place.foreign_country is None

    def test_create_swiss_municipality(self):
        """Test creating Swiss municipality place."""
        mun = ECH0007Municipality.from_swiss(
            municipality_id="6172",
            municipality_name="Bister",
            canton=CantonAbbreviation.VS
        )
        place = ECH0011GeneralPlace(swiss_municipality=mun)
        assert place.swiss_municipality is not None
        assert place.swiss_municipality.swiss_municipality.municipality_name == "Bister"
        assert place.unknown is None
        assert place.foreign_country is None

    def test_create_foreign_country(self):
        """Test creating foreign country place."""
        country = ECH0008Country(
            country_id="8207",
            country_id_iso2="DE",
            country_name_short="Deutschland"
        )
        place = ECH0011GeneralPlace(
            foreign_country=country,
            foreign_town="Berlin"
        )
        assert place.foreign_country is not None
        assert place.foreign_town == "Berlin"
        assert place.unknown is None
        assert place.swiss_municipality is None

    def test_to_xml_unknown(self):
        """Test XML export for unknown place."""
        place = ECH0011GeneralPlace(unknown=True)
        xml = place.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}placeOfBirth'

        unknown_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}unknown')
        assert unknown_elem is not None
        assert unknown_elem.text == "0"  # XSD unknownType is xs:token with value "0"

    def test_to_xml_swiss_municipality(self):
        """Test XML export for Swiss municipality."""
        mun = ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
        place = ECH0011GeneralPlace(swiss_municipality=mun)
        xml = place.to_xml()

        # swissTown element is in eCH-0011 namespace (element defined in eCH-0011, type from eCH-0007)
        swiss_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}swissTown')
        assert swiss_elem is not None

    def test_to_xml_foreign_country(self):
        """Test XML export for foreign country."""
        country = ECH0008Country(
            country_id="8207",
            country_id_iso2="DE",
            country_name_short="Deutschland"
        )
        place = ECH0011GeneralPlace(
            foreign_country=country,
            foreign_town="Berlin"
        )
        xml = place.to_xml()

        foreign_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}foreignCountry')
        assert foreign_elem is not None

        town_elem = foreign_elem.find('{http://www.ech.ch/xmlns/eCH-0011/8}town')
        assert town_elem is not None
        assert town_elem.text == "Berlin"

    def test_validate_mutually_exclusive(self):
        """Test that multiple place types cannot be set."""
        mun = ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
        country = ECH0008Country(
            country_id="8207",
            country_id_iso2="DE",
            country_name_short="Deutschland"
        )

        # Both swiss and foreign - should fail on export
        place = ECH0011GeneralPlace(
            swiss_municipality=mun,
            foreign_country=country
        )
        with pytest.raises(ValueError, match="Can only specify one of"):
            place.to_xml()

    def test_roundtrip_swiss_municipality(self):
        """Test XML roundtrip for Swiss municipality."""
        original = ECH0011GeneralPlace(
            swiss_municipality=ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
        )
        xml = original.to_xml()
        parsed = ECH0011GeneralPlace.from_xml(xml)

        assert parsed.swiss_municipality is not None
        assert parsed.swiss_municipality.swiss_municipality.municipality_name == "Bister"
        assert parsed.unknown is None


class TestECH0011BirthData:
    """Test eCH-0011 birth data model."""

    def test_create_minimal(self):
        """Test creating birth data with minimal fields."""
        birth = ECH0011BirthData(
            date_of_birth=date(1990, 5, 15),
            place_of_birth=ECH0011GeneralPlace(unknown=True),
            sex="1"
        )
        assert birth.date_of_birth == date(1990, 5, 15)
        assert birth.sex == "1"

    def test_create_full(self):
        """Test creating birth data with all fields."""
        birth = ECH0011BirthData(
            date_of_birth=date(1990, 5, 15),
            place_of_birth=ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
            ),
            sex="2"
        )
        assert birth.date_of_birth == date(1990, 5, 15)
        assert birth.place_of_birth.swiss_municipality is not None
        assert birth.sex == "2"

    def test_validate_required_fields(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                sex="1"
            )

    def test_validate_sex_values(self):
        """Test that sex accepts only 1, 2, or 3."""
        # Valid values
        for sex_value in ["1", "2", "3"]:
            birth = ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex=sex_value
            )
            assert birth.sex == sex_value

        # Invalid value
        with pytest.raises(ValidationError, match="Input should be '1', '2' or '3'"):
            ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="4"
            )

    def test_to_xml(self):
        """Test XML export."""
        birth = ECH0011BirthData(
            date_of_birth=date(1990, 5, 15),
            place_of_birth=ECH0011GeneralPlace(unknown=True),
            sex="1"
        )
        xml = birth.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}birthData'

        dob_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}dateOfBirth')
        assert dob_elem is not None
        # dateOfBirth contains eCH-0044 datePartiallyKnown type with yearMonthDay child
        ymd_elem = dob_elem.find('{http://www.ech.ch/xmlns/eCH-0044/4}yearMonthDay')
        assert ymd_elem is not None
        assert ymd_elem.text == "1990-05-15"

        sex_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}sex')
        assert sex_elem is not None
        assert sex_elem.text == "1"

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011BirthData(
            date_of_birth=date(1990, 5, 15),
            place_of_birth=ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
            ),
            sex="2"
        )
        xml = original.to_xml()
        parsed = ECH0011BirthData.from_xml(xml)

        assert parsed.date_of_birth == original.date_of_birth
        assert parsed.sex == original.sex
        assert parsed.place_of_birth.swiss_municipality is not None


class TestECH0011ReligionData:
    """Test eCH-0011 religion data model."""

    def test_create_minimal(self):
        """Test creating religion data with minimal fields."""
        religion = ECH0011ReligionData(religion="111")
        assert religion.religion == "111"
        assert religion.religion_valid_from is None

    def test_create_full(self):
        """Test creating religion data with all fields."""
        religion = ECH0011ReligionData(
            religion="111",
            religion_valid_from=date(2020, 1, 1)
        )
        assert religion.religion == "111"
        assert religion.religion_valid_from == date(2020, 1, 1)

    def test_validate_religion_pattern(self):
        """Test religion code validation (3-6 digits)."""
        # Valid codes
        for code in ["111", "1111", "11111", "111111"]:
            religion = ECH0011ReligionData(religion=code)
            assert religion.religion == code

        # Invalid codes (too short)
        with pytest.raises(ValidationError, match="String should have at least 3 characters"):
            ECH0011ReligionData(religion="11")

        # Invalid codes (too long)
        with pytest.raises(ValidationError, match="String should have at most 6 characters"):
            ECH0011ReligionData(religion="1111111")

        # Invalid codes (non-digits)
        with pytest.raises(ValidationError, match="String should match pattern"):
            ECH0011ReligionData(religion="ABC")

    def test_to_xml(self):
        """Test XML export."""
        religion = ECH0011ReligionData(
            religion="111",
            religion_valid_from=date(2020, 1, 1)
        )
        xml = religion.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}religionData'

        religion_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}religion')
        assert religion_elem is not None
        assert religion_elem.text == "111"

        valid_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}religionValidFrom')
        assert valid_elem is not None
        assert valid_elem.text == "2020-01-01"

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011ReligionData(
            religion="111",
            religion_valid_from=date(2020, 1, 1)
        )
        xml = original.to_xml()
        parsed = ECH0011ReligionData.from_xml(xml)

        assert parsed.religion == original.religion
        assert parsed.religion_valid_from == original.religion_valid_from


class TestECH0011MaritalData:
    """Test eCH-0011 marital data model."""

    def test_create_minimal(self):
        """Test creating marital data with minimal fields."""
        marital = ECH0011MaritalData(marital_status="1")
        assert marital.marital_status == "1"
        assert marital.date_of_marital_status is None

    def test_create_full(self):
        """Test creating marital data with all fields."""
        marital = ECH0011MaritalData(
            marital_status="2",
            date_of_marital_status=date(2015, 6, 20),
            official_proof_of_marital_status_yes_no=True,
            separation_data=ECH0011SeparationData(
                separation="1",
                separation_valid_from=date(2020, 1, 1)
            )
        )
        assert marital.marital_status == "2"
        assert marital.date_of_marital_status == date(2015, 6, 20)
        assert marital.official_proof_of_marital_status_yes_no is True
        assert marital.separation_data is not None

    def test_validate_marital_status_values(self):
        """Test marital status accepts valid values."""
        # Valid values
        for status in ["1", "2", "3", "4", "5", "6", "7", "9"]:
            marital = ECH0011MaritalData(marital_status=status)
            assert marital.marital_status == status

        # Invalid value
        with pytest.raises(ValidationError):
            ECH0011MaritalData(marital_status="8")

    def test_to_xml(self):
        """Test XML export."""
        marital = ECH0011MaritalData(
            marital_status="2",
            date_of_marital_status=date(2015, 6, 20),
            official_proof_of_marital_status_yes_no=True
        )
        xml = marital.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}maritalData'

        status_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}maritalStatus')
        assert status_elem is not None
        assert status_elem.text == "2"

        date_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}dateOfMaritalStatus')
        assert date_elem is not None
        assert date_elem.text == "2015-06-20"

        proof_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}officialProofOfMaritalStatusYesNo')
        assert proof_elem is not None
        assert proof_elem.text == 'true'

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011MaritalData(
            marital_status="2",
            date_of_marital_status=date(2015, 6, 20),
            cancelation_reason="3"
        )
        xml = original.to_xml()
        parsed = ECH0011MaritalData.from_xml(xml)

        assert parsed.marital_status == original.marital_status
        assert parsed.date_of_marital_status == original.date_of_marital_status
        assert parsed.cancelation_reason == original.cancelation_reason


class TestECH0011NationalityData:
    """Test eCH-0011 nationality data model."""

    def test_create_minimal(self):
        """Test creating nationality data with minimal fields."""
        nationality = ECH0011NationalityData(nationality_status="1")
        assert nationality.nationality_status == "1"
        assert len(nationality.country_info) == 0

    def test_create_with_countries(self):
        """Test creating nationality data with countries."""
        swiss = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        nationality = ECH0011NationalityData(
            nationality_status="1",
            country_info=[
                ECH0011CountryInfo(
                    country=swiss,
                    nationality_valid_from=date(1990, 5, 15)
                )
            ]
        )
        assert nationality.nationality_status == "1"
        assert len(nationality.country_info) == 1
        assert nationality.country_info[0].country.country_name_short == "Schweiz"

    def test_validate_nationality_status(self):
        """Test nationality status accepts valid values."""
        # Valid values
        for status in ["0", "1", "2"]:
            nationality = ECH0011NationalityData(nationality_status=status)
            assert nationality.nationality_status == status

        # Invalid value
        with pytest.raises(ValidationError):
            ECH0011NationalityData(nationality_status="3")

    def test_to_xml(self):
        """Test XML export."""
        swiss = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        nationality = ECH0011NationalityData(
            nationality_status="1",
            country_info=[
                ECH0011CountryInfo(
                    country=swiss,
                    nationality_valid_from=date(1990, 5, 15)
                )
            ]
        )
        xml = nationality.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}nationalityData'

        status_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}nationalityStatus')
        assert status_elem is not None
        assert status_elem.text == "1"

        country_info_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}countryInfo')
        assert country_info_elem is not None

    def test_roundtrip(self):
        """Test XML roundtrip."""
        swiss = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        original = ECH0011NationalityData(
            nationality_status="1",
            country_info=[
                ECH0011CountryInfo(
                    country=swiss,
                    nationality_valid_from=date(1990, 5, 15)
                )
            ]
        )
        xml = original.to_xml()
        parsed = ECH0011NationalityData.from_xml(xml)

        assert parsed.nationality_status == original.nationality_status
        assert len(parsed.country_info) == 1
        assert parsed.country_info[0].nationality_valid_from == date(1990, 5, 15)


class TestRealWorldScenarios:
    """Test real-world person data scenarios."""

    def test_swiss_person_minimal(self):
        """Test minimal Swiss person data."""
        # Name data
        name = ECH0011NameData(
            official_name="Meier",
            first_name="Anna"
        )

        # Birth data
        birth = ECH0011BirthData(
            date_of_birth=date(1990, 5, 15),
            place_of_birth=ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality.from_swiss(
                municipality_id="6172",
                municipality_name="Bister",
                canton=CantonAbbreviation.VS
            )
            ),
            sex="2"
        )

        # Religion
        religion = ECH0011ReligionData(religion="111")

        # Marital status
        marital = ECH0011MaritalData(marital_status="1")

        # Nationality
        nationality = ECH0011NationalityData(
            nationality_status="1",
            country_info=[
                ECH0011CountryInfo(
                    country=ECH0008Country(
                        country_id="8100",
                        country_id_iso2="CH",
                        country_name_short="Schweiz"
                    ),
                    nationality_valid_from=date(1990, 5, 15)
                )
            ]
        )

        # All components should work together
        assert name.official_name == "Meier"
        assert birth.sex == "2"
        assert religion.religion == "111"
        assert marital.marital_status == "1"
        assert nationality.nationality_status == "1"

    def test_married_person_with_maiden_name(self):
        """Test married person with maiden name."""
        name = ECH0011NameData(
            official_name="Meier-Schmidt",
            first_name="Anna",
            original_name="Schmidt",
            alliance_name="Meier"
        )

        marital = ECH0011MaritalData(
            marital_status="2",
            date_of_marital_status=date(2015, 6, 20),
            official_proof_of_marital_status_yes_no=True
        )

        # Should roundtrip through XML
        name_xml = name.to_xml()
        name_parsed = ECH0011NameData.from_xml(name_xml)
        assert name_parsed.original_name == "Schmidt"
        assert name_parsed.alliance_name == "Meier"

        marital_xml = marital.to_xml()
        marital_parsed = ECH0011MaritalData.from_xml(marital_xml)
        assert marital_parsed.marital_status == "2"
        assert marital_parsed.date_of_marital_status == date(2015, 6, 20)

    def test_foreign_born_person(self):
        """Test person born in foreign country."""
        birth = ECH0011BirthData(
            date_of_birth=date(1985, 3, 10),
            place_of_birth=ECH0011GeneralPlace(
                foreign_country=ECH0008Country(
                    country_id="8207",
                    country_id_iso2="DE",
                    country_name_short="Deutschland"
                ),
                foreign_town="Berlin"
            ),
            sex="1"
        )

        # Should roundtrip
        xml = birth.to_xml()
        parsed = ECH0011BirthData.from_xml(xml)
        assert parsed.place_of_birth.foreign_country is not None
        assert parsed.place_of_birth.foreign_town == "Berlin"

    def test_dual_nationality(self):
        """Test person with dual nationality."""
        swiss = ECH0008Country(
            country_id="8100",
            country_id_iso2="CH",
            country_name_short="Schweiz"
        )
        german = ECH0008Country(
            country_id="8207",
            country_id_iso2="DE",
            country_name_short="Deutschland"
        )

        nationality = ECH0011NationalityData(
            nationality_status="1",
            country_info=[
                ECH0011CountryInfo(
                    country=swiss,
                    nationality_valid_from=date(1990, 5, 15)
                ),
                ECH0011CountryInfo(
                    country=german,
                    nationality_valid_from=date(1990, 5, 15)
                )
            ]
        )

        assert len(nationality.country_info) == 2

        # Should roundtrip
        xml = nationality.to_xml()
        parsed = ECH0011NationalityData.from_xml(xml)
        assert len(parsed.country_info) == 2


class TestECH0011PlaceOfOrigin:
    """Test eCH-0011 place of origin model."""

    def test_create_minimal(self):
        """Test creating place of origin with minimal fields."""
        origin = ECH0011PlaceOfOrigin(
            origin_name="Bister",
            canton="VS"
        )
        assert origin.origin_name == "Bister"
        assert origin.canton == "VS"
        assert origin.place_of_origin_id is None
        assert origin.history_municipality_id is None

    def test_create_full(self):
        """Test creating place of origin with all fields."""
        origin = ECH0011PlaceOfOrigin(
            origin_name="Bister",
            canton="VS",
            place_of_origin_id=6172,
            history_municipality_id="6172"
        )
        assert origin.origin_name == "Bister"
        assert origin.canton == "VS"
        assert origin.place_of_origin_id == 6172
        assert origin.history_municipality_id == "6172"

    def test_validate_required_fields(self):
        """Test that origin_name and canton are required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011PlaceOfOrigin(origin_name="Bister")

        with pytest.raises(ValidationError, match="Field required"):
            ECH0011PlaceOfOrigin(canton="VS")

    def test_validate_canton_length(self):
        """Test that canton must be exactly 2 characters."""
        # Valid canton
        origin = ECH0011PlaceOfOrigin(origin_name="Bister", canton="VS")
        assert origin.canton == "VS"

        # Too short
        with pytest.raises(ValidationError, match="String should have at least 2 characters"):
            ECH0011PlaceOfOrigin(origin_name="Bister", canton="V")

        # Too long
        with pytest.raises(ValidationError, match="String should have at most 2 characters"):
            ECH0011PlaceOfOrigin(origin_name="Bister", canton="VSX")

    def test_validate_origin_name_max_length(self):
        """Test that origin_name has max length 50."""
        # Valid name
        origin = ECH0011PlaceOfOrigin(
            origin_name="A" * 50,
            canton="VS"
        )
        assert len(origin.origin_name) == 50

        # Too long
        with pytest.raises(ValidationError, match="String should have at most 50 characters"):
            ECH0011PlaceOfOrigin(
                origin_name="A" * 51,
                canton="VS"
            )

    def test_to_xml_minimal(self):
        """Test XML export with minimal fields."""
        origin = ECH0011PlaceOfOrigin(
            origin_name="Bister",
            canton="VS"
        )
        xml = origin.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}placeOfOrigin'

        name_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}originName')
        assert name_elem is not None
        assert name_elem.text == "Bister"

        canton_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}canton')
        assert canton_elem is not None
        assert canton_elem.text == "VS"

    def test_to_xml_full(self):
        """Test XML export with all fields."""
        origin = ECH0011PlaceOfOrigin(
            origin_name="Bister",
            canton="VS",
            place_of_origin_id=6172,
            history_municipality_id="6172"
        )
        xml = origin.to_xml()

        # Check all fields present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}originName') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}canton') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}placeOfOriginId') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}historyMunicipalityId') is not None

        # Check values
        id_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}placeOfOriginId')
        assert id_elem.text == "6172"

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011PlaceOfOrigin(
            origin_name="Bister",
            canton="VS",
            place_of_origin_id=6172
        )
        xml = original.to_xml()
        parsed = ECH0011PlaceOfOrigin.from_xml(xml)

        assert parsed.origin_name == original.origin_name
        assert parsed.canton == original.canton
        assert parsed.place_of_origin_id == original.place_of_origin_id


class TestECH0011ResidencePermitData:
    """Test eCH-0011 residence permit data model."""

    def test_create_minimal(self):
        """Test creating residence permit with minimal fields."""
        permit = ECH0011ResidencePermitData(residence_permit="02")
        assert permit.residence_permit == "02"
        assert permit.residence_permit_valid_from is None
        assert permit.residence_permit_valid_till is None
        assert permit.entry_date is None

    def test_create_full(self):
        """Test creating residence permit with all fields."""
        permit = ECH0011ResidencePermitData(
            residence_permit="02",
            residence_permit_valid_from=date(2020, 1, 1),
            residence_permit_valid_till=date(2025, 12, 31),
            entry_date=date(2019, 12, 15)
        )
        assert permit.residence_permit == "02"
        assert permit.residence_permit_valid_from == date(2020, 1, 1)
        assert permit.residence_permit_valid_till == date(2025, 12, 31)
        assert permit.entry_date == date(2019, 12, 15)

    def test_validate_required_field(self):
        """Test that residence_permit is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011ResidencePermitData()

    def test_validate_permit_max_length(self):
        """Test that residence_permit has max length 2."""
        # Valid permit
        permit = ECH0011ResidencePermitData(residence_permit="02")
        assert permit.residence_permit == "02"

        # Invalid permit type (not in eCH-0006 enum)
        with pytest.raises(ValidationError, match="type=enum"):
            ECH0011ResidencePermitData(residence_permit="ABC")

    def test_to_xml_minimal(self):
        """Test XML export with minimal fields."""
        permit = ECH0011ResidencePermitData(residence_permit="02")
        xml = permit.to_xml()

        # Element name is 'residencePermit', type is 'residencePermitDataType'
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}residencePermit'

        permit_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermit')
        assert permit_elem is not None
        assert permit_elem.text == "02"

    def test_to_xml_full(self):
        """Test XML export with all fields."""
        permit = ECH0011ResidencePermitData(
            residence_permit="02",
            residence_permit_valid_from=date(2020, 1, 1),
            residence_permit_valid_till=date(2025, 12, 31),
            entry_date=date(2019, 12, 15)
        )
        xml = permit.to_xml()

        # Check all fields present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermit') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermitValidFrom') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermitValidTill') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}entryDate') is not None

        # Check date values
        valid_from = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermitValidFrom')
        assert valid_from.text == "2020-01-01"

    def test_roundtrip(self):
        """Test XML roundtrip."""
        original = ECH0011ResidencePermitData(
            residence_permit="02",
            residence_permit_valid_from=date(2020, 1, 1),
            entry_date=date(2019, 12, 15)
        )
        xml = original.to_xml()
        parsed = ECH0011ResidencePermitData.from_xml(xml)

        assert parsed.residence_permit == original.residence_permit
        assert parsed.residence_permit_valid_from == original.residence_permit_valid_from
        assert parsed.entry_date == original.entry_date


class TestECH0011DeathData:
    """Test eCH-0011 death data models."""

    def test_create_death_period_minimal(self):
        """Test creating death period with date_from only."""
        period = ECH0011DeathPeriod(date_from=date(2024, 10, 15))
        assert period.date_from == date(2024, 10, 15)
        assert period.date_to is None

    def test_create_death_period_full(self):
        """Test creating death period with date range."""
        period = ECH0011DeathPeriod(
            date_from=date(2024, 10, 15),
            date_to=date(2024, 10, 20)
        )
        assert period.date_from == date(2024, 10, 15)
        assert period.date_to == date(2024, 10, 20)

    def test_validate_death_period_required(self):
        """Test that date_from is required for death period."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011DeathPeriod()

    def test_create_death_data_minimal(self):
        """Test creating death data with period only."""
        death = ECH0011DeathData(
            death_period=ECH0011DeathPeriod(date_from=date(2024, 10, 15))
        )
        assert death.death_period.date_from == date(2024, 10, 15)
        assert death.place_of_death is None

    def test_create_death_data_full(self):
        """Test creating death data with period and place."""
        death = ECH0011DeathData(
            death_period=ECH0011DeathPeriod(
                date_from=date(2024, 10, 15),
                date_to=date(2024, 10, 20)
            ),
            place_of_death=ECH0011GeneralPlace(
                swiss_municipality=ECH0007Municipality.from_swiss(
                    municipality_id="6172",
                    municipality_name="Bister",
                    canton=CantonAbbreviation.VS
                )
            )
        )
        assert death.death_period.date_from == date(2024, 10, 15)
        assert death.place_of_death is not None
        assert death.place_of_death.swiss_municipality.swiss_municipality.municipality_name == "Bister"

    def test_validate_death_data_required(self):
        """Test that death_period is required."""
        with pytest.raises(ValidationError, match="Field required"):
            ECH0011DeathData()

    def test_to_xml_death_period(self):
        """Test XML export for death period."""
        period = ECH0011DeathPeriod(
            date_from=date(2024, 10, 15),
            date_to=date(2024, 10, 20)
        )
        xml = period.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}deathPeriod'

        from_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}dateFrom')
        assert from_elem is not None
        assert from_elem.text == "2024-10-15"

        to_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}dateTo')
        assert to_elem is not None
        assert to_elem.text == "2024-10-20"

    def test_to_xml_death_data_minimal(self):
        """Test XML export for death data with period only."""
        death = ECH0011DeathData(
            death_period=ECH0011DeathPeriod(date_from=date(2024, 10, 15))
        )
        xml = death.to_xml()

        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}deathData'

        period_elem = xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}deathPeriod')
        assert period_elem is not None

    def test_to_xml_death_data_full(self):
        """Test XML export for death data with all fields."""
        death = ECH0011DeathData(
            death_period=ECH0011DeathPeriod(date_from=date(2024, 10, 15)),
            place_of_death=ECH0011GeneralPlace(unknown=True)
        )
        xml = death.to_xml()

        # Check both fields present
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}deathPeriod') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}placeOfDeath') is not None

    def test_roundtrip_death_period(self):
        """Test XML roundtrip for death period."""
        original = ECH0011DeathPeriod(
            date_from=date(2024, 10, 15),
            date_to=date(2024, 10, 20)
        )
        xml = original.to_xml()
        parsed = ECH0011DeathPeriod.from_xml(xml)

        assert parsed.date_from == original.date_from
        assert parsed.date_to == original.date_to

    def test_roundtrip_death_data(self):
        """Test XML roundtrip for death data."""
        original = ECH0011DeathData(
            death_period=ECH0011DeathPeriod(date_from=date(2024, 10, 15)),
            place_of_death=ECH0011GeneralPlace(unknown=True)
        )
        xml = original.to_xml()
        parsed = ECH0011DeathData.from_xml(xml)

        assert parsed.death_period.date_from == original.death_period.date_from
        assert parsed.place_of_death.unknown is True


class TestECH0011Person:
    """Test eCH-0011 complete person model."""

    def test_create_swiss_citizen_minimal(self):
        """Test creating Swiss citizen with minimal required fields."""
        person = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8100",
                            country_id_iso2="CH",
                            country_name_short="Schweiz"
                        ),
                        nationality_valid_from=date(1990, 5, 15)
                    )
                ]
            ),
            place_of_origin=[
                ECH0011PlaceOfOrigin(
                    origin_name="Bister",
                    canton="VS"
                )
            ]
        )

        assert person.person_identification.official_name == "Meier"
        assert len(person.place_of_origin) == 1
        assert person.place_of_origin[0].origin_name == "Bister"
        assert person.residence_permit is None

    def test_create_foreign_national_minimal(self):
        """Test creating foreign national with minimal required fields."""
        person = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.2"
                ),
                official_name="Schmidt",
                first_name="Hans",
                sex="1",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1985, 3, 10))
            ),
            name_data=ECH0011NameData(
                official_name="Schmidt",
                first_name="Hans"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1985, 3, 10),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="1"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8207",
                            country_id_iso2="DE",
                            country_name_short="Deutschland"
                        ),
                        nationality_valid_from=date(1985, 3, 10)
                    )
                ]
            ),
            residence_permit=ECH0011ResidencePermitData(
                residence_permit="02",
                residence_permit_valid_from=date(2020, 1, 1)
            )
        )

        assert person.person_identification.official_name == "Schmidt"
        assert person.residence_permit is not None
        assert person.residence_permit.residence_permit == "02"
        assert len(person.place_of_origin) == 0

    def test_create_swiss_citizen_with_all_optional_fields(self):
        """Test creating Swiss citizen with all optional fields."""
        person = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                vn="7560123456789",
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(
                    swiss_municipality=ECH0007Municipality.from_swiss(
                        municipality_id="6172",
                        municipality_name="Bister",
                        canton=CantonAbbreviation.VS
                    )
                ),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(
                religion="111",
                religion_valid_from=date(2020, 1, 1)
            ),
            marital_data=ECH0011MaritalData(
                marital_status="2",
                date_of_marital_status=date(2015, 6, 20)
            ),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8100",
                            country_id_iso2="CH",
                            country_name_short="Schweiz"
                        ),
                        nationality_valid_from=date(1990, 5, 15)
                    )
                ]
            ),
            place_of_origin=[
                ECH0011PlaceOfOrigin(
                    origin_name="Bister",
                    canton="VS",
                    place_of_origin_id=6172
                )
            ],
            death_data=ECH0011DeathData(
                death_period=ECH0011DeathPeriod(date_from=date(2024, 10, 15)),
                place_of_death=ECH0011GeneralPlace(unknown=True)
            ),
            language_of_correspondance="de",
            restricted_voting_and_election_right_federation=False
        )

        assert person.person_identification.vn == "7560123456789"
        assert person.death_data is not None
        assert person.language_of_correspondance == "de"
        assert person.restricted_voting_and_election_right_federation is False

    def test_validate_swiss_or_foreign_choice(self):
        """Test that person must have either place_of_origin OR residence_permit."""
        # Both specified - should fail on to_xml()
        person_both = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(nationality_status="1"),
            place_of_origin=[ECH0011PlaceOfOrigin(origin_name="Bister", canton="VS")],
            residence_permit=ECH0011ResidencePermitData(residence_permit="02")
        )

        with pytest.raises(ValueError, match="Cannot have both placeOfOrigin and residencePermit"):
            person_both.to_xml()

        # Neither specified - should fail on to_xml()
        person_neither = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(nationality_status="1")
        )

        with pytest.raises(ValueError, match="Must have either placeOfOrigin"):
            person_neither.to_xml()

    def test_to_xml_swiss_citizen(self):
        """Test XML export for Swiss citizen."""
        person = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8100",
                            country_id_iso2="CH",
                            country_name_short="Schweiz"
                        )
                    )
                ]
            ),
            place_of_origin=[
                ECH0011PlaceOfOrigin(
                    origin_name="Bister",
                    canton="VS"
                )
            ]
        )

        xml = person.to_xml()
        assert xml.tag == '{http://www.ech.ch/xmlns/eCH-0011/8}person'

        # Check required elements present
        # personIdentification element is in eCH-0011 namespace (type is eCH-0044:personIdentificationType)
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}personIdentification') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}nameData') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}birthData') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}religionData') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}maritalData') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}nationalityData') is not None
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}placeOfOrigin') is not None

        # Check residence permit NOT present (Swiss citizen has places of origin, not residence permit)
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermit') is None

    def test_to_xml_foreign_national(self):
        """Test XML export for foreign national."""
        person = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.2"
                ),
                official_name="Schmidt",
                first_name="Hans",
                sex="1",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1985, 3, 10))
            ),
            name_data=ECH0011NameData(
                official_name="Schmidt",
                first_name="Hans"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1985, 3, 10),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="1"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8207",
                            country_id_iso2="DE",
                            country_name_short="Deutschland"
                        )
                    )
                ]
            ),
            residence_permit=ECH0011ResidencePermitData(
                residence_permit="02"
            )
        )

        xml = person.to_xml()

        # Check residence permit present (element name is 'residencePermit')
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}residencePermit') is not None

        # Check place of origin NOT present (foreign national has residence permit, not place of origin)
        assert xml.find('{http://www.ech.ch/xmlns/eCH-0011/8}placeOfOrigin') is None

    def test_roundtrip_swiss_citizen(self):
        """Test XML roundtrip for Swiss citizen."""
        original = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                vn="7560123456789",
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.1"
                ),
                official_name="Meier",
                first_name="Anna",
                sex="2",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1990, 5, 15))
            ),
            name_data=ECH0011NameData(
                official_name="Meier",
                first_name="Anna"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1990, 5, 15),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="2"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8100",
                            country_id_iso2="CH",
                            country_name_short="Schweiz"
                        )
                    )
                ]
            ),
            place_of_origin=[
                ECH0011PlaceOfOrigin(
                    origin_name="Bister",
                    canton="VS",
                    place_of_origin_id=6172
                )
            ]
        )

        xml = original.to_xml()
        parsed = ECH0011Person.from_xml(xml)

        assert parsed.person_identification.vn == original.person_identification.vn
        assert parsed.person_identification.official_name == original.person_identification.official_name
        assert parsed.name_data.official_name == original.name_data.official_name
        assert len(parsed.place_of_origin) == 1
        assert parsed.place_of_origin[0].origin_name == "Bister"
        assert parsed.residence_permit is None

    def test_roundtrip_foreign_national(self):
        """Test XML roundtrip for foreign national."""
        original = ECH0011Person(
            person_identification=ECH0044PersonIdentification(
                local_person_id=ECH0044NamedPersonId(
                    person_id_category="veka.id",
                    person_id="MU.6172.2"
                ),
                official_name="Schmidt",
                first_name="Hans",
                sex="1",
                date_of_birth=ECH0044DatePartiallyKnown.from_date(date(1985, 3, 10))
            ),
            name_data=ECH0011NameData(
                official_name="Schmidt",
                first_name="Hans"
            ),
            birth_data=ECH0011BirthData(
                date_of_birth=date(1985, 3, 10),
                place_of_birth=ECH0011GeneralPlace(unknown=True),
                sex="1"
            ),
            religion_data=ECH0011ReligionData(religion="111"),
            marital_data=ECH0011MaritalData(marital_status="1"),
            nationality_data=ECH0011NationalityData(
                nationality_status="1",
                country_info=[
                    ECH0011CountryInfo(
                        country=ECH0008Country(
                            country_id="8207",
                            country_id_iso2="DE",
                            country_name_short="Deutschland"
                        )
                    )
                ]
            ),
            residence_permit=ECH0011ResidencePermitData(
                residence_permit="02",
                residence_permit_valid_from=date(2020, 1, 1)
            )
        )

        xml = original.to_xml()
        parsed = ECH0011Person.from_xml(xml)

        assert parsed.person_identification.official_name == original.person_identification.official_name
        assert parsed.residence_permit is not None
        assert parsed.residence_permit.residence_permit == "02"
        assert len(parsed.place_of_origin) == 0
