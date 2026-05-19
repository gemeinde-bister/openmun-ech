"""eCH-0129 v6.0.0 — Building identification and entity types.

All types verified field-by-field against:
- XSD: eCH-0129-6-0.xsd (lines 442-474, 749-779, 781-815)
- PDF: STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf (§4.5, pages 34-47)

Types in this module depend on:
- eCH-0129 base_types (ECH0129BuildingDate, ECH0129BuildingVolume,
  ECH0129Coordinates, ECH0129DatePartiallyKnown, ECH0129Heating,
  ECH0129HotWater, ECH0129NamedId, ECH0129NamedMetaData)
- eCH-0129 entrance (ECH0129BuildingEntrance)
- eCH-0129 enums (BuildingCategory, BuildingStatus, RealestateType)

buildingIdentificationType — most complex xs:choice in the XSD:
  3 outer branches, one of which contains a nested xs:choice with
  2 sub-branches.
  Branch 1: EGID
  Branch 2: street + houseNumber + zipCode [+ nameOfBuilding]
  Branch 3: (EGRID | (cadasterAreaNumber + number [+ realestateType]))
            + officialBuildingNo

  Generic ECHModel serialization handles this without custom
  to_xml()/from_xml() because all element names are unique and field
  declaration order matches the XSD element order for every branch.
  Model validator enforces choice constraints.

buildingType vs buildingOnlyType:
  buildingOnlyType is an xs:restriction of buildingType that removes
  buildingEntrance. Implemented as standalone class per design decision.
"""

from typing import Optional, Self

from pydantic import field_validator, model_validator

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0129.enums import (
    BuildingCategory,
    BuildingStatus,
    RealestateType,
)
from openmun_ech.ech0129.v6.base_types import (
    ECH0129BuildingDate,
    ECH0129BuildingVolume,
    ECH0129Coordinates,
    ECH0129DatePartiallyKnown,
    ECH0129Heating,
    ECH0129HotWater,
    ECH0129NamedId,
    ECH0129NamedMetaData,
)
from openmun_ech.ech0129.v6.entrance import ECH0129BuildingEntrance


# ---------------------------------------------------------------------------
# buildingIdentificationType (§4.5.1, XSD lines 442-474)
# ---------------------------------------------------------------------------

class ECH0129BuildingIdentification(ECHModel):
    """eCH-0129 building identification.

    XSD: buildingIdentificationType — xs:sequence containing a complex
    xs:choice with 3 outer branches.
    PDF: §4.5.1 (pages 34-39, Abb. 7)

    Outer xs:choice:
      Branch 1: EGID alone
      Branch 2: street + houseNumber + zipCode [+ nameOfBuilding]
      Branch 3: inner xs:choice (EGRID | (cadasterAreaNumber + number
                [+ realestateType])) + officialBuildingNo

    After choice (required):
      localID: namedIdType (maxOccurs="unbounded", min 1)
      municipality: eCH-0007:municipalityIdType (int 1-9999)

    Element types from external namespaces (eCH-0010, eCH-0007) provide
    constraints only — all elements are in eCH-0129 namespace.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingIdentification'

    # --- Outer choice branch 1 ---
    egid: Optional[int] = xml_field(
        'EGID', default=None, ge=1, le=900000000
    )

    # --- Outer choice branch 2 (address) ---
    # eCH-0010:streetType — xs:token maxLength=60
    street: Optional[str] = xml_field(
        'street', default=None, max_length=60
    )
    # eCH-0010:houseNumberType — xs:token maxLength=12
    house_number: Optional[str] = xml_field(
        'houseNumber', default=None, max_length=12
    )
    # eCH-0010:swissZipCodeType — unsignedInt 1000-9999
    zip_code: Optional[int] = xml_field(
        'zipCode', default=None, ge=1000, le=9999
    )
    # nameOfBuildingType — xs:token 3-40, minOccurs="0"
    name_of_building: Optional[str] = xml_field(
        'nameOfBuilding', default=None, min_length=3, max_length=40
    )

    # --- Outer choice branch 3, inner choice branch a ---
    # EGRIDType — xs:token maxLength=14
    egrid: Optional[str] = xml_field(
        'EGRID', default=None, max_length=14
    )

    # --- Outer choice branch 3, inner choice branch b ---
    # cadasterAreaNumberType — xs:token (no constraints)
    cadaster_area_number: Optional[str] = xml_field(
        'cadasterAreaNumber', default=None
    )
    # Anonymous inline: xs:token 1-12
    number: Optional[str] = xml_field(
        'number', default=None, min_length=1, max_length=12
    )
    # realestateTypeType enum, minOccurs="0"
    realestate_type: Optional[RealestateType] = xml_field(
        'realestateType', default=None
    )

    # --- Outer choice branch 3, shared (required in branch 3) ---
    # officialBuildingNoType — xs:token 1-12
    official_building_no: Optional[str] = xml_field(
        'officialBuildingNo', default=None, min_length=1, max_length=12
    )

    # --- After choice (always required) ---
    local_id: list[ECH0129NamedId] = xml_field(
        'localID', is_list=True, min_length=1
    )
    municipality: int = xml_field('municipality', ge=1, le=9999)

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce nested xs:choice constraints.

        Outer choice: exactly one of
          1. EGID
          2. street + houseNumber + zipCode [+ nameOfBuilding]
          3. (EGRID | (cadasterAreaNumber + number [+ realestateType]))
             + officialBuildingNo
        """
        has_b1 = self.egid is not None
        has_b2 = any(f is not None for f in [
            self.street, self.house_number, self.zip_code,
        ])
        has_b3 = any(f is not None for f in [
            self.egrid, self.cadaster_area_number, self.number,
            self.official_building_no,
        ])

        # nameOfBuilding only valid in branch 2
        if self.name_of_building is not None and not has_b2:
            raise ValueError(
                "buildingIdentificationType: nameOfBuilding only valid "
                "with address branch (street/houseNumber/zipCode)"
            )

        # realestateType only valid in branch 3
        if self.realestate_type is not None and not has_b3:
            raise ValueError(
                "buildingIdentificationType: realestateType only valid "
                "with realestate branch"
            )

        count = sum([has_b1, has_b2, has_b3])
        if count == 0:
            raise ValueError(
                "buildingIdentificationType: must set one of EGID, "
                "address (street/houseNumber/zipCode), or realestate "
                "identification (EGRID/cadaster + officialBuildingNo)"
            )
        if count > 1:
            raise ValueError(
                "buildingIdentificationType: EGID, address, and "
                "realestate identification are mutually exclusive"
            )

        # Branch 2: street, houseNumber, zipCode all required
        if has_b2:
            missing = []
            if self.street is None:
                missing.append('street')
            if self.house_number is None:
                missing.append('houseNumber')
            if self.zip_code is None:
                missing.append('zipCode')
            if missing:
                raise ValueError(
                    f"buildingIdentificationType: address branch "
                    f"requires: {', '.join(missing)}"
                )

        # Branch 3: officialBuildingNo required, inner choice validation
        if has_b3:
            if self.official_building_no is None:
                raise ValueError(
                    "buildingIdentificationType: realestate branch "
                    "requires officialBuildingNo"
                )
            has_egrid = self.egrid is not None
            has_cadaster = self.cadaster_area_number is not None

            if has_egrid and has_cadaster:
                raise ValueError(
                    "buildingIdentificationType: EGRID and "
                    "cadasterAreaNumber are mutually exclusive"
                )
            if not has_egrid and not has_cadaster:
                raise ValueError(
                    "buildingIdentificationType: must set either "
                    "EGRID or (cadasterAreaNumber + number)"
                )
            if has_cadaster and self.number is None:
                raise ValueError(
                    "buildingIdentificationType: cadasterAreaNumber "
                    "requires number"
                )
            if has_egrid and self.number is not None:
                raise ValueError(
                    "buildingIdentificationType: number only valid "
                    "with cadasterAreaNumber, not EGRID"
                )
            if has_egrid and self.realestate_type is not None:
                raise ValueError(
                    "buildingIdentificationType: realestateType only "
                    "valid with cadasterAreaNumber, not EGRID"
                )

        return self


# ---------------------------------------------------------------------------
# buildingType (§4.5, XSD lines 749-779)
# ---------------------------------------------------------------------------

class ECH0129Building(ECHModel):
    """eCH-0129 building entity.

    XSD: buildingType — xs:sequence of 27 elements.
    PDF: §4.5 Gebäude (pages 34-47, Abb. 6)

    1 required field (buildingCategory), 26 optional.

    Fields (in XSD order):
    - buildingIdentification: buildingIdentificationType, minOccurs="0"
    - EGID: EGIDType (1-900000000), minOccurs="0"
    - officialBuildingNo: officialBuildingNoType (xs:token 1-12), minOccurs="0"
    - name: nameOfBuildingType (xs:token 3-40), minOccurs="0"
    - dateOfConstruction: buildingDateType, minOccurs="0"
    - dateOfRenovation: buildingDateType, minOccurs="0"
    - dateOfDemolition: datePartiallyKnownType, minOccurs="0"
    - numberOfFloors: numberOfFloorsType (1-99), minOccurs="0"
    - numberOfSeparateHabitableRooms: (0-999), minOccurs="0"
    - surfaceAreaOfBuilding: (1-99999), minOccurs="0"
    - subSurfaceAreaOfBuilding: (1-99999), minOccurs="0"
    - surfaceAreaOfBuildingSignaleObject: (1-99999), minOccurs="0"
      Note: XSD element name has typo "Signale" (not "Single") — preserved.
    - buildingCategory: buildingCategoryType enum (REQUIRED)
    - buildingClass: buildingClassType (1110-1278), minOccurs="0"
    - status: buildingStatusType enum, minOccurs="0"
    - coordinates: coordinatesType, minOccurs="0"
    - otherID: namedIdType, minOccurs="0", maxOccurs="unbounded"
    - civilDefenseShelter: xs:boolean, minOccurs="0"
    - neighbourhood: neighbourhoodType (1000-9999999), minOccurs="0"
    - localCode: localCodeType (xs:token 1-8), minOccurs="0", maxOccurs="4"
    - energyRelevantSurface: (5-900000), minOccurs="0"
    - volume: buildingVolumeType, minOccurs="0"
    - heating: heatingType, minOccurs="0", maxOccurs="2"
    - hotWater: hotWaterType, minOccurs="0", maxOccurs="2"
    - buildingEntrance: buildingEntranceType, minOccurs="0",
      maxOccurs="unbounded"
    - namedMetaData: namedMetaDataType, minOccurs="0", maxOccurs="unbounded"
    - buildingFreeText: freeTextType (xs:token 1-32), minOccurs="0",
      maxOccurs="2"
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'building'

    building_identification: Optional[ECH0129BuildingIdentification] = xml_field(
        'buildingIdentification', default=None
    )
    egid: Optional[int] = xml_field(
        'EGID', default=None, ge=1, le=900000000
    )
    official_building_no: Optional[str] = xml_field(
        'officialBuildingNo', default=None, min_length=1, max_length=12
    )
    name: Optional[str] = xml_field(
        'name', default=None, min_length=3, max_length=40
    )
    date_of_construction: Optional[ECH0129BuildingDate] = xml_field(
        'dateOfConstruction', default=None
    )
    date_of_renovation: Optional[ECH0129BuildingDate] = xml_field(
        'dateOfRenovation', default=None
    )
    date_of_demolition: Optional[ECH0129DatePartiallyKnown] = xml_field(
        'dateOfDemolition', default=None
    )
    number_of_floors: Optional[int] = xml_field(
        'numberOfFloors', default=None, ge=1, le=99
    )
    number_of_separate_habitable_rooms: Optional[int] = xml_field(
        'numberOfSeparateHabitableRooms', default=None, ge=0, le=999
    )
    surface_area_of_building: Optional[int] = xml_field(
        'surfaceAreaOfBuilding', default=None, ge=1, le=99999
    )
    sub_surface_area_of_building: Optional[int] = xml_field(
        'subSurfaceAreaOfBuilding', default=None, ge=1, le=99999
    )
    # Note: XSD element name has typo "Signale" instead of "Single"
    surface_area_of_building_signale_object: Optional[int] = xml_field(
        'surfaceAreaOfBuildingSignaleObject', default=None, ge=1, le=99999
    )
    building_category: BuildingCategory = xml_field('buildingCategory')
    building_class: Optional[int] = xml_field(
        'buildingClass', default=None, ge=1110, le=1278
    )
    status: Optional[BuildingStatus] = xml_field('status', default=None)
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    other_id: list[ECH0129NamedId] = xml_field(
        'otherID', default_factory=list, is_list=True
    )
    civil_defense_shelter: Optional[bool] = xml_field(
        'civilDefenseShelter', default=None
    )
    neighbourhood: Optional[int] = xml_field(
        'neighbourhood', default=None, ge=1000, le=9999999
    )
    local_code: list[str] = xml_field(
        'localCode', default_factory=list, is_list=True
    )
    energy_relevant_surface: Optional[int] = xml_field(
        'energyRelevantSurface', default=None, ge=5, le=900000
    )
    volume: Optional[ECH0129BuildingVolume] = xml_field(
        'volume', default=None
    )
    heating: list[ECH0129Heating] = xml_field(
        'heating', default_factory=list, is_list=True
    )
    hot_water: list[ECH0129HotWater] = xml_field(
        'hotWater', default_factory=list, is_list=True
    )
    building_entrance: list[ECH0129BuildingEntrance] = xml_field(
        'buildingEntrance', default_factory=list, is_list=True
    )
    named_meta_data: list[ECH0129NamedMetaData] = xml_field(
        'namedMetaData', default_factory=list, is_list=True
    )
    building_free_text: list[str] = xml_field(
        'buildingFreeText', default_factory=list, is_list=True
    )

    @field_validator('local_code')
    @classmethod
    def validate_local_code_list(cls, v: list[str]) -> list[str]:
        """XSD: localCode maxOccurs="4", localCodeType xs:token 1-8."""
        if len(v) > 4:
            raise ValueError(
                f"localCode maxOccurs=4, got {len(v)} entries"
            )
        for i, code in enumerate(v):
            if len(code) < 1 or len(code) > 8:
                raise ValueError(
                    f"localCode[{i}] must be 1-8 chars, "
                    f"got {len(code)} chars"
                )
        return v

    @field_validator('heating')
    @classmethod
    def validate_heating_list(
        cls, v: list[ECH0129Heating],
    ) -> list[ECH0129Heating]:
        """XSD: heating maxOccurs="2"."""
        if len(v) > 2:
            raise ValueError(
                f"heating maxOccurs=2, got {len(v)} entries"
            )
        return v

    @field_validator('hot_water')
    @classmethod
    def validate_hot_water_list(
        cls, v: list[ECH0129HotWater],
    ) -> list[ECH0129HotWater]:
        """XSD: hotWater maxOccurs="2"."""
        if len(v) > 2:
            raise ValueError(
                f"hotWater maxOccurs=2, got {len(v)} entries"
            )
        return v

    @field_validator('building_free_text')
    @classmethod
    def validate_building_free_text_list(cls, v: list[str]) -> list[str]:
        """XSD: buildingFreeText maxOccurs="2", freeTextType 1-32 chars."""
        if len(v) > 2:
            raise ValueError(
                f"buildingFreeText maxOccurs=2, got {len(v)} entries"
            )
        for i, text in enumerate(v):
            if len(text) < 1 or len(text) > 32:
                raise ValueError(
                    f"buildingFreeText[{i}] must be 1-32 chars, "
                    f"got {len(text)} chars"
                )
        return v


# ---------------------------------------------------------------------------
# buildingOnlyType (§4.5, XSD lines 781-815)
# ---------------------------------------------------------------------------

class ECH0129BuildingOnly(ECHModel):
    """eCH-0129 building entity (without building entrances).

    XSD: buildingOnlyType — xs:restriction of buildingType.
    PDF: §4.5 (same as buildingType)

    Identical to buildingType but without the buildingEntrance element.
    All other fields preserved with same cardinality.
    """

    __xml_ns__ = NS.ECH0129_V6
    __xml_element__ = 'buildingOnly'

    building_identification: Optional[ECH0129BuildingIdentification] = xml_field(
        'buildingIdentification', default=None
    )
    egid: Optional[int] = xml_field(
        'EGID', default=None, ge=1, le=900000000
    )
    official_building_no: Optional[str] = xml_field(
        'officialBuildingNo', default=None, min_length=1, max_length=12
    )
    name: Optional[str] = xml_field(
        'name', default=None, min_length=3, max_length=40
    )
    date_of_construction: Optional[ECH0129BuildingDate] = xml_field(
        'dateOfConstruction', default=None
    )
    date_of_renovation: Optional[ECH0129BuildingDate] = xml_field(
        'dateOfRenovation', default=None
    )
    date_of_demolition: Optional[ECH0129DatePartiallyKnown] = xml_field(
        'dateOfDemolition', default=None
    )
    number_of_floors: Optional[int] = xml_field(
        'numberOfFloors', default=None, ge=1, le=99
    )
    number_of_separate_habitable_rooms: Optional[int] = xml_field(
        'numberOfSeparateHabitableRooms', default=None, ge=0, le=999
    )
    surface_area_of_building: Optional[int] = xml_field(
        'surfaceAreaOfBuilding', default=None, ge=1, le=99999
    )
    sub_surface_area_of_building: Optional[int] = xml_field(
        'subSurfaceAreaOfBuilding', default=None, ge=1, le=99999
    )
    surface_area_of_building_signale_object: Optional[int] = xml_field(
        'surfaceAreaOfBuildingSignaleObject', default=None, ge=1, le=99999
    )
    building_category: BuildingCategory = xml_field('buildingCategory')
    building_class: Optional[int] = xml_field(
        'buildingClass', default=None, ge=1110, le=1278
    )
    status: Optional[BuildingStatus] = xml_field('status', default=None)
    coordinates: Optional[ECH0129Coordinates] = xml_field(
        'coordinates', default=None
    )
    other_id: list[ECH0129NamedId] = xml_field(
        'otherID', default_factory=list, is_list=True
    )
    civil_defense_shelter: Optional[bool] = xml_field(
        'civilDefenseShelter', default=None
    )
    neighbourhood: Optional[int] = xml_field(
        'neighbourhood', default=None, ge=1000, le=9999999
    )
    local_code: list[str] = xml_field(
        'localCode', default_factory=list, is_list=True
    )
    energy_relevant_surface: Optional[int] = xml_field(
        'energyRelevantSurface', default=None, ge=5, le=900000
    )
    volume: Optional[ECH0129BuildingVolume] = xml_field(
        'volume', default=None
    )
    heating: list[ECH0129Heating] = xml_field(
        'heating', default_factory=list, is_list=True
    )
    hot_water: list[ECH0129HotWater] = xml_field(
        'hotWater', default_factory=list, is_list=True
    )
    # buildingEntrance REMOVED (the only difference from buildingType)
    named_meta_data: list[ECH0129NamedMetaData] = xml_field(
        'namedMetaData', default_factory=list, is_list=True
    )
    building_free_text: list[str] = xml_field(
        'buildingFreeText', default_factory=list, is_list=True
    )

    @field_validator('local_code')
    @classmethod
    def validate_local_code_list(cls, v: list[str]) -> list[str]:
        """XSD: localCode maxOccurs="4", localCodeType xs:token 1-8."""
        if len(v) > 4:
            raise ValueError(
                f"localCode maxOccurs=4, got {len(v)} entries"
            )
        for i, code in enumerate(v):
            if len(code) < 1 or len(code) > 8:
                raise ValueError(
                    f"localCode[{i}] must be 1-8 chars, "
                    f"got {len(code)} chars"
                )
        return v

    @field_validator('heating')
    @classmethod
    def validate_heating_list(
        cls, v: list[ECH0129Heating],
    ) -> list[ECH0129Heating]:
        """XSD: heating maxOccurs="2"."""
        if len(v) > 2:
            raise ValueError(
                f"heating maxOccurs=2, got {len(v)} entries"
            )
        return v

    @field_validator('hot_water')
    @classmethod
    def validate_hot_water_list(
        cls, v: list[ECH0129HotWater],
    ) -> list[ECH0129HotWater]:
        """XSD: hotWater maxOccurs="2"."""
        if len(v) > 2:
            raise ValueError(
                f"hotWater maxOccurs=2, got {len(v)} entries"
            )
        return v

    @field_validator('building_free_text')
    @classmethod
    def validate_building_free_text_list(cls, v: list[str]) -> list[str]:
        """XSD: buildingFreeText maxOccurs="2", freeTextType 1-32 chars."""
        if len(v) > 2:
            raise ValueError(
                f"buildingFreeText maxOccurs=2, got {len(v)} entries"
            )
        for i, text in enumerate(v):
            if len(text) < 1 or len(text) > 32:
                raise ValueError(
                    f"buildingFreeText[{i}] must be 1-32 chars, "
                    f"got {len(text)} chars"
                )
        return v
