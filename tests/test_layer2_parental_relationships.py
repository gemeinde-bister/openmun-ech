"""Tests 20-22: Parental Relationships

Tests Layer 2 handling of parental relationships:
- Test 20: Single parent (biological mother, no VN)
- Test 21: Two parents (biological mother + father, typical case)
- Test 22: Four parents (2 biological + 2 adoptive, edge case)

These tests validate complex family structures including adoption scenarios.

Tests verify:
1. Layer 2 construction with parents list
2. to_ech0020() conversion (Layer 2 → Layer 1 parental_relationship list)
3. from_ech0020() conversion (Layer 1 → Layer 2 parents list)
4. Full roundtrip with zero data loss
5. Rule #5: Preserve lists even for "typical" cases

Data policy:
- Fake personal data (names, dates, IDs)
- Real BFS fixtures (municipality codes)
"""

from datetime import date

import pytest

from openmun_ech.ech0020.models import BaseDeliveryPerson, PlaceType, PersonIdentification, ParentInfo


class TestParentalRelationships:
    """Test Layer 2 parental relationship fields."""

    def test_single_parent_biological_mother(self):
        """Test 20: Single parent - biological mother.

        Tests:
        - parents list with 1 entry (ParentInfo model)
        - Parent without VN (testing optional field)
        - relationship_type="4" (biological mother)
        - care="0" (unknown custody - required field per eCH-0021)
        - No relationship_valid_from (testing optional field)
        - Use case: Single mother, father unknown or not registered
        - Stored in ECH0021ParentalRelationship list
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (child) with single parent
        person_with_parent = BaseDeliveryPerson(
            local_person_id="12000",
            local_person_id_category="MU.6172",
            official_name="Schmidt",
            first_name="Lisa",
            sex="2",
            date_of_birth=date(2010, 6, 15),  # Child born 2010
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",  # single (child)
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Single parent: biological mother
            parents=[
                ParentInfo(
                    person=PersonIdentification(
                        # No VN (testing optional case)
                        local_person_id="12001",
                        local_person_id_category="MU.6172",
                        official_name="Schmidt",
                        first_name="Maria",
                        original_name="Müller",  # Maiden name
                        sex="2",  # Female
                        date_of_birth=date(1985, 3, 20)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="0",  # 0 = unknown custody (required field per eCH-0021)
                    # No relationship_valid_from (testing optional case)
                )
            ]
        )

        # Convert to Layer 1
        layer1_with_parent = person_with_parent.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_with_parent.parental_relationship is not None, "parental_relationship should be present"
        assert len(layer1_with_parent.parental_relationship) == 1, \
            f"Expected 1 parent, got {len(layer1_with_parent.parental_relationship)}"

        # Verify parent data
        parent_rel = layer1_with_parent.parental_relationship[0]
        assert parent_rel.partner is not None, "partner should be present"
        assert parent_rel.partner.person_identification is not None, "person_identification should be present"

        parent_id = parent_rel.partner.person_identification
        assert parent_id.official_name == "Schmidt", \
            f"Expected official_name='Schmidt', got {parent_id.official_name}"
        assert parent_id.first_name == "Maria", \
            f"Expected first_name='Maria', got {parent_id.first_name}"
        assert parent_id.original_name == "Müller", \
            f"Expected original_name='Müller', got {parent_id.original_name}"

        # Verify sex
        parent_sex = parent_id.sex.value if hasattr(parent_id.sex, 'value') else str(parent_id.sex)
        assert parent_sex == "2", f"Expected sex='2', got {parent_sex}"

        # Verify date_of_birth
        parent_dob = parent_id.date_of_birth
        if hasattr(parent_dob, 'year_month_day'):
            assert parent_dob.year_month_day == date(1985, 3, 20), \
                f"Expected DOB=1985-03-20, got {parent_dob.year_month_day}"
        else:
            assert parent_dob == date(1985, 3, 20), \
                f"Expected DOB=1985-03-20, got {parent_dob}"

        # Verify relationship type
        assert parent_rel.type_of_relationship == "4", \
            f"Expected type_of_relationship='4', got {parent_rel.type_of_relationship}"

        # Verify care field
        assert parent_rel.care == "0", \
            f"Expected care='0' (unknown), got {parent_rel.care}"

        # Verify optional field is None
        assert parent_rel.relationship_valid_from is None, \
            f"Expected relationship_valid_from=None, got {parent_rel.relationship_valid_from}"

        # Roundtrip: Layer 1 → Layer 2
        parent_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_with_parent)

        # Verify parents list preserved
        assert parent_roundtrip.parents is not None, "parents should be preserved"
        assert len(parent_roundtrip.parents) == 1, \
            f"Expected 1 parent in roundtrip, got {len(parent_roundtrip.parents)}"

        # Verify parent data preserved
        parent_info = parent_roundtrip.parents[0]
        assert parent_info.person.official_name == "Schmidt", \
            f"Expected parent official_name='Schmidt', got {parent_info.person.official_name}"
        assert parent_info.person.first_name == "Maria", \
            f"Expected parent first_name='Maria', got {parent_info.person.first_name}"
        assert parent_info.person.original_name == "Müller", \
            f"Expected parent original_name='Müller', got {parent_info.person.original_name}"
        assert parent_info.person.sex == "2", \
            f"Expected parent sex='2', got {parent_info.person.sex}"
        assert parent_info.person.date_of_birth == date(1985, 3, 20), \
            f"Expected parent DOB=1985-03-20, got {parent_info.person.date_of_birth}"
        assert parent_info.person.local_person_id == "12001", \
            f"Expected parent local_person_id='12001', got {parent_info.person.local_person_id}"
        assert parent_info.person.local_person_id_category == "MU.6172", \
            f"Expected parent local_person_id_category='MU.6172', got {parent_info.person.local_person_id_category}"

        # Verify relationship fields preserved
        assert parent_info.relationship_type == "4", \
            f"Expected relationship_type='4', got {parent_info.relationship_type}"
        assert parent_info.care == "0", \
            f"Expected care='0' in roundtrip, got {parent_info.care}"
        assert parent_info.relationship_valid_from is None, \
            f"Expected relationship_valid_from=None in roundtrip, got {parent_info.relationship_valid_from}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = parent_roundtrip.to_ech0020()
        assert layer1_roundtrip.parental_relationship is not None
        assert len(layer1_roundtrip.parental_relationship) == 1
        assert layer1_roundtrip.parental_relationship[0].type_of_relationship == "4"

    def test_two_parents_biological_mother_and_father(self):
        """Test 21: Two parents - biological mother and father (typical case).

        Tests:
        - parents list with 2 entries
        - Mother: has VN, original_name, relationship_type="4", care="1" (joint custody)
        - Father: no VN, no original_name, relationship_type="3", care="1" (joint custody)
        - Both have relationship_valid_from (child's birth date)
        - Use case: Standard two-parent family with joint custody
        - Validates Rule #5: Preserve lists even for "typical" cases
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (child) with two parents
        person_with_two_parents = BaseDeliveryPerson(
            local_person_id="13000",
            local_person_id_category="MU.6172",
            official_name="Fischer",
            first_name="Emma",
            sex="2",
            date_of_birth=date(2015, 9, 10),  # Child born 2015
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",  # single (child)
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Two parents: biological mother and father (typical case)
            parents=[
                # Biological mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569877777777",  # AHV-13 - mother has VN
                        local_person_id="13001",
                        local_person_id_category="MU.6172",
                        official_name="Fischer",
                        first_name="Anna",
                        original_name="Meier",  # Maiden name
                        sex="2",  # Female
                        date_of_birth=date(1988, 5, 15)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="1",  # 1 = joint custody (typical case)
                    relationship_valid_from=date(2015, 9, 10)  # Since child's birth
                ),
                # Biological father
                ParentInfo(
                    person=PersonIdentification(
                        # No VN for father (testing optional VN)
                        local_person_id="13002",
                        local_person_id_category="MU.6172",
                        official_name="Fischer",
                        first_name="Thomas",
                        # No original_name (testing optional field)
                        sex="1",  # Male
                        date_of_birth=date(1986, 11, 22)
                    ),
                    relationship_type="3",  # 3 = biological father
                    care="1",  # 1 = joint custody (same as mother)
                    relationship_valid_from=date(2015, 9, 10)  # Since child's birth
                )
            ]
        )

        # Convert to Layer 1
        layer1_two_parents = person_with_two_parents.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_two_parents.parental_relationship is not None, "parental_relationship should be present"
        assert len(layer1_two_parents.parental_relationship) == 2, \
            f"Expected 2 parents, got {len(layer1_two_parents.parental_relationship)}"

        # Verify mother data (first parent)
        mother_rel = layer1_two_parents.parental_relationship[0]
        assert mother_rel.partner is not None, "mother partner should be present"
        assert mother_rel.partner.person_identification is not None, "mother person_identification should be present"

        mother_id = mother_rel.partner.person_identification
        assert mother_id.official_name == "Fischer", \
            f"Expected mother official_name='Fischer', got {mother_id.official_name}"
        assert mother_id.first_name == "Anna", \
            f"Expected mother first_name='Anna', got {mother_id.first_name}"
        assert mother_id.original_name == "Meier", \
            f"Expected mother original_name='Meier', got {mother_id.original_name}"

        # Verify mother sex
        mother_sex = mother_id.sex.value if hasattr(mother_id.sex, 'value') else str(mother_id.sex)
        assert mother_sex == "2", f"Expected mother sex='2', got {mother_sex}"

        # Verify mother VN
        if hasattr(mother_id, 'vn') and mother_id.vn:
            assert str(mother_id.vn) == "7569877777777", \
                f"Expected mother vn='7569877777777', got {mother_id.vn}"

        # Verify mother relationship
        assert mother_rel.type_of_relationship == "4", \
            f"Expected mother type_of_relationship='4', got {mother_rel.type_of_relationship}"
        assert mother_rel.care == "1", \
            f"Expected mother care='1' (joint custody), got {mother_rel.care}"
        assert mother_rel.relationship_valid_from == date(2015, 9, 10), \
            f"Expected mother relationship_valid_from=2015-09-10, got {mother_rel.relationship_valid_from}"

        # Verify father data (second parent)
        father_rel = layer1_two_parents.parental_relationship[1]
        assert father_rel.partner is not None, "father partner should be present"
        assert father_rel.partner.person_identification is not None, "father person_identification should be present"

        father_id = father_rel.partner.person_identification
        assert father_id.official_name == "Fischer", \
            f"Expected father official_name='Fischer', got {father_id.official_name}"
        assert father_id.first_name == "Thomas", \
            f"Expected father first_name='Thomas', got {father_id.first_name}"

        # Verify father sex
        father_sex = father_id.sex.value if hasattr(father_id.sex, 'value') else str(father_id.sex)
        assert father_sex == "1", f"Expected father sex='1', got {father_sex}"

        # Verify father relationship
        assert father_rel.type_of_relationship == "3", \
            f"Expected father type_of_relationship='3', got {father_rel.type_of_relationship}"
        assert father_rel.care == "1", \
            f"Expected father care='1' (joint custody), got {father_rel.care}"
        assert father_rel.relationship_valid_from == date(2015, 9, 10), \
            f"Expected father relationship_valid_from=2015-09-10, got {father_rel.relationship_valid_from}"

        # Roundtrip: Layer 1 → Layer 2
        two_parents_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_two_parents)

        # Verify parents list preserved
        assert two_parents_roundtrip.parents is not None, "parents should be preserved"
        assert len(two_parents_roundtrip.parents) == 2, \
            f"Expected 2 parents in roundtrip, got {len(two_parents_roundtrip.parents)}"

        # Verify mother data preserved (first parent)
        mother_info = two_parents_roundtrip.parents[0]
        assert mother_info.person.official_name == "Fischer", \
            f"Expected mother official_name='Fischer', got {mother_info.person.official_name}"
        assert mother_info.person.first_name == "Anna", \
            f"Expected mother first_name='Anna', got {mother_info.person.first_name}"
        assert mother_info.person.original_name == "Meier", \
            f"Expected mother original_name='Meier', got {mother_info.person.original_name}"
        assert mother_info.person.sex == "2", \
            f"Expected mother sex='2', got {mother_info.person.sex}"
        assert mother_info.person.date_of_birth == date(1988, 5, 15), \
            f"Expected mother DOB=1988-05-15, got {mother_info.person.date_of_birth}"
        assert mother_info.person.vn == "7569877777777", \
            f"Expected mother vn='7569877777777', got {mother_info.person.vn}"
        assert mother_info.relationship_type == "4", \
            f"Expected mother relationship_type='4', got {mother_info.relationship_type}"
        assert mother_info.care == "1", \
            f"Expected mother care='1', got {mother_info.care}"
        assert mother_info.relationship_valid_from == date(2015, 9, 10), \
            f"Expected mother relationship_valid_from=2015-09-10, got {mother_info.relationship_valid_from}"

        # Verify father data preserved (second parent)
        father_info = two_parents_roundtrip.parents[1]
        assert father_info.person.official_name == "Fischer", \
            f"Expected father official_name='Fischer', got {father_info.person.official_name}"
        assert father_info.person.first_name == "Thomas", \
            f"Expected father first_name='Thomas', got {father_info.person.first_name}"
        assert father_info.person.original_name is None, \
            f"Expected father original_name=None, got {father_info.person.original_name}"
        assert father_info.person.sex == "1", \
            f"Expected father sex='1', got {father_info.person.sex}"
        assert father_info.person.date_of_birth == date(1986, 11, 22), \
            f"Expected father DOB=1986-11-22, got {father_info.person.date_of_birth}"
        assert father_info.person.vn is None, \
            f"Expected father vn=None, got {father_info.person.vn}"
        assert father_info.relationship_type == "3", \
            f"Expected father relationship_type='3', got {father_info.relationship_type}"
        assert father_info.care == "1", \
            f"Expected father care='1', got {father_info.care}"
        assert father_info.relationship_valid_from == date(2015, 9, 10), \
            f"Expected father relationship_valid_from=2015-09-10, got {father_info.relationship_valid_from}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = two_parents_roundtrip.to_ech0020()
        assert layer1_roundtrip.parental_relationship is not None
        assert len(layer1_roundtrip.parental_relationship) == 2

    def test_four_parents_biological_and_adoptive(self):
        """Test 22: Four parents - 2 biological + 2 adoptive (edge case).

        Tests:
        - parents list with 4 entries (validates Rule #5)
        - 2 biological parents: relationship_type "3"/"4", care="0", valid_from=birth
        - 2 adoptive parents: relationship_type "5"/"6", care="1", valid_from=adoption date
        - Use case: Adopted child with both biological and adoptive parents registered
        - Validates Rule #5: Preserve lists even for "typical" cases
        - Full Layer 2 → Layer 1 → Layer 2 roundtrip
        - Zero data loss verification
        """
        # Create Layer 2 person (child) with four parents
        person_with_four_parents = BaseDeliveryPerson(
            local_person_id="14000",
            local_person_id_category="MU.6172",
            official_name="Bernasconi",
            first_name="Marco",
            sex="1",
            date_of_birth=date(2010, 3, 25),  # Child born 2010
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            religion="111",
            marital_status="1",
            nationality_status="1",
            nationalities=[
                {
                    'country_id': '8100',
                    'country_iso': 'CH',
                    'country_name_short': 'Schweiz'
                }
            ],
            places_of_origin=[
                {
                    'bfs_code': '261',
                    'name': 'Zürich',
                    'canton': 'ZH'
                }
            ],
            data_lock="0",
            paper_lock=False,

            # Four parents: 2 biological + 2 adoptive (edge case for adopted children)
            parents=[
                # Biological mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888888",
                        local_person_id="14001",
                        local_person_id_category="MU.6172",
                        official_name="Rossi",
                        first_name="Elena",
                        sex="2",
                        date_of_birth=date(1992, 7, 10)
                    ),
                    relationship_type="4",  # 4 = biological mother
                    care="0",  # 0 = unknown (biological parents may not have custody after adoption)
                    relationship_valid_from=date(2010, 3, 25)  # Birth date
                ),
                # Biological father
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888889",
                        local_person_id="14002",
                        local_person_id_category="MU.6172",
                        official_name="Rossi",
                        first_name="Marco",
                        sex="1",
                        date_of_birth=date(1990, 4, 5)
                    ),
                    relationship_type="3",  # 3 = biological father
                    care="0",  # 0 = unknown
                    relationship_valid_from=date(2010, 3, 25)  # Birth date
                ),
                # Adoptive mother
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888890",
                        local_person_id="14003",
                        local_person_id_category="MU.6172",
                        official_name="Bernasconi",
                        first_name="Laura",
                        sex="2",
                        date_of_birth=date(1985, 11, 15)
                    ),
                    relationship_type="6",  # 6 = adoptive mother
                    care="1",  # 1 = joint custody (with adoptive father)
                    relationship_valid_from=date(2012, 6, 1)  # Adoption date
                ),
                # Adoptive father
                ParentInfo(
                    person=PersonIdentification(
                        vn="7569878888891",
                        local_person_id="14004",
                        local_person_id_category="MU.6172",
                        official_name="Bernasconi",
                        first_name="Roberto",
                        sex="1",
                        date_of_birth=date(1983, 9, 20)
                    ),
                    relationship_type="5",  # 5 = adoptive father
                    care="1",  # 1 = joint custody (with adoptive mother)
                    relationship_valid_from=date(2012, 6, 1)  # Adoption date
                )
            ]
        )

        # Convert to Layer 1
        layer1_four_parents = person_with_four_parents.to_ech0020()

        # Verify Layer 1 structure
        assert layer1_four_parents.parental_relationship is not None, "parental_relationship should be present"
        assert len(layer1_four_parents.parental_relationship) == 4, \
            f"Expected 4 parents, got {len(layer1_four_parents.parental_relationship)}"

        # Verify each parent (biological mother, biological father, adoptive mother, adoptive father)
        parent_checks = [
            ("biological mother", 0, "4", "Rossi", "Elena", "2", date(1992, 7, 10), "0", date(2010, 3, 25)),
            ("biological father", 1, "3", "Rossi", "Marco", "1", date(1990, 4, 5), "0", date(2010, 3, 25)),
            ("adoptive mother", 2, "6", "Bernasconi", "Laura", "2", date(1985, 11, 15), "1", date(2012, 6, 1)),
            ("adoptive father", 3, "5", "Bernasconi", "Roberto", "1", date(1983, 9, 20), "1", date(2012, 6, 1)),
        ]

        for label, idx, exp_rel_type, exp_official_name, exp_first_name, exp_sex, exp_dob, exp_care, exp_valid_from in parent_checks:
            parent_rel = layer1_four_parents.parental_relationship[idx]
            assert parent_rel.partner is not None, f"{label} partner should be present"
            assert parent_rel.partner.person_identification is not None, \
                f"{label} person_identification should be present"

            parent_id = parent_rel.partner.person_identification
            assert parent_id.official_name == exp_official_name, \
                f"Expected {label} official_name='{exp_official_name}', got {parent_id.official_name}"
            assert parent_id.first_name == exp_first_name, \
                f"Expected {label} first_name='{exp_first_name}', got {parent_id.first_name}"

            # Verify sex
            parent_sex = parent_id.sex.value if hasattr(parent_id.sex, 'value') else str(parent_id.sex)
            assert parent_sex == exp_sex, f"Expected {label} sex='{exp_sex}', got {parent_sex}"

            # Verify date_of_birth
            parent_dob = parent_id.date_of_birth
            if hasattr(parent_dob, 'year_month_day'):
                actual_dob = parent_dob.year_month_day
            else:
                actual_dob = parent_dob
            assert actual_dob == exp_dob, \
                f"Expected {label} DOB={exp_dob}, got {actual_dob}"

            # Verify relationship type
            assert parent_rel.type_of_relationship == exp_rel_type, \
                f"Expected {label} type_of_relationship='{exp_rel_type}', got {parent_rel.type_of_relationship}"

            # Verify care
            assert parent_rel.care == exp_care, \
                f"Expected {label} care='{exp_care}', got {parent_rel.care}"

            # Verify relationship_valid_from
            assert parent_rel.relationship_valid_from == exp_valid_from, \
                f"Expected {label} relationship_valid_from={exp_valid_from}, got {parent_rel.relationship_valid_from}"

        # Roundtrip: Layer 1 → Layer 2
        four_parents_roundtrip = BaseDeliveryPerson.from_ech0020(layer1_four_parents)

        # Verify parents list preserved
        assert four_parents_roundtrip.parents is not None, "parents should be preserved"
        assert len(four_parents_roundtrip.parents) == 4, \
            f"Expected 4 parents in roundtrip, got {len(four_parents_roundtrip.parents)}"

        # Verify each parent in roundtrip
        roundtrip_checks = [
            ("biological mother", 0, "4", "Rossi", "Elena", "2", date(1992, 7, 10), "7569878888888", "0", date(2010, 3, 25)),
            ("biological father", 1, "3", "Rossi", "Marco", "1", date(1990, 4, 5), "7569878888889", "0", date(2010, 3, 25)),
            ("adoptive mother", 2, "6", "Bernasconi", "Laura", "2", date(1985, 11, 15), "7569878888890", "1", date(2012, 6, 1)),
            ("adoptive father", 3, "5", "Bernasconi", "Roberto", "1", date(1983, 9, 20), "7569878888891", "1", date(2012, 6, 1)),
        ]

        for label, idx, exp_rel_type, exp_official_name, exp_first_name, exp_sex, exp_dob, exp_vn, exp_care, exp_valid_from in roundtrip_checks:
            parent_info = four_parents_roundtrip.parents[idx]
            assert parent_info.person.official_name == exp_official_name, \
                f"Expected {label} official_name='{exp_official_name}', got {parent_info.person.official_name}"
            assert parent_info.person.first_name == exp_first_name, \
                f"Expected {label} first_name='{exp_first_name}', got {parent_info.person.first_name}"
            assert parent_info.person.sex == exp_sex, \
                f"Expected {label} sex='{exp_sex}', got {parent_info.person.sex}"
            assert parent_info.person.date_of_birth == exp_dob, \
                f"Expected {label} DOB={exp_dob}, got {parent_info.person.date_of_birth}"
            assert parent_info.person.vn == exp_vn, \
                f"Expected {label} vn='{exp_vn}', got {parent_info.person.vn}"
            assert parent_info.relationship_type == exp_rel_type, \
                f"Expected {label} relationship_type='{exp_rel_type}', got {parent_info.relationship_type}"
            assert parent_info.care == exp_care, \
                f"Expected {label} care='{exp_care}', got {parent_info.care}"
            assert parent_info.relationship_valid_from == exp_valid_from, \
                f"Expected {label} relationship_valid_from={exp_valid_from}, got {parent_info.relationship_valid_from}"

        # Full roundtrip: Layer 2 → Layer 1 → Layer 2 → Layer 1
        layer1_roundtrip = four_parents_roundtrip.to_ech0020()
        assert layer1_roundtrip.parental_relationship is not None
        assert len(layer1_roundtrip.parental_relationship) == 4
