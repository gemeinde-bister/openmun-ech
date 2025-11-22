"""eCH-0021 v8 Standard Code Enumerations.

Official codes defined in eCH-0021-8-0.xsd for person additional data,
relationships, and employment information.

Standard: eCH-0021 v8.0
XSD: eCH-0021-8-0.xsd
Namespace: http://www.ech.ch/xmlns/eCH-0021/8
Source: https://www.ech.ch/de/standards/60022
"""

from enum import Enum


class MrMrs(str, Enum):
    """Salutation codes per eCH-0010 mrMrsType (used in eCH-0021).

    XSD: mrMrsType (restriction of xs:string)

    Note: This type is defined in eCH-0010 but commonly used in eCH-0021
    personAdditionalData for salutation.
    """
    MRS = "1"          # Frau (Mrs)
    MR = "2"           # Herr (Mr)


class TypeOfRelationship(str, Enum):
    """Type of relationship codes per eCH-0021.

    Used in marital relationships (codes 1-2) and parental relationships
    (codes 3-6) and guardian relationships (codes 7-10) to specify the nature of the relationship.

    Source: eCH-0021 v8.1.0, Kapitel 3.1.9.4 (page 20)
    XSD: typeOfRelationshipType (restriction of xs:string)

    Note: Code 8 (Beirat) is deprecated after 2013-01-01.
    """
    # Marital relationships (used in maritalRelationship)
    SPOUSE = "1"                           # ist Ehepartner (is spouse)
    REGISTERED_PARTNER = "2"               # ist Partner in Eingetragener Partnerschaft (is registered partner)

    # Parental relationships (used in parentalRelationship)
    MOTHER = "3"                           # ist Mutter (is mother)
    FATHER = "4"                           # ist Vater (is father)
    FOSTER_FATHER = "5"                    # ist Pflegevater (is foster father)
    FOSTER_MOTHER = "6"                    # ist Pflegemutter (is foster mother)

    # Guardian relationships (used in guardianRelationship)
    LEGAL_ASSISTANT = "7"                  # ist Beistand (is legal assistant/guardian)
    ADVISOR = "8"                          # ist Beirat (is advisor - deprecated after 2013)
    GUARDIAN = "9"                         # ist Vormund (is guardian of minor)
    HEALTHCARE_PROXY = "10"                # ist Vorsorgebeauftragter (is healthcare proxy)


class CareType(str, Enum):
    """Parental authority codes per eCH-0021.

    Used in parental relationships to specify parental authority arrangements.

    Source: eCH-0021 v8.1.0, Kapitel 3.1.9.7 (page 24)
    XSD: careType (restriction of xs:string)

    Note: Code 1 is a legacy code for cases under old law where the distinction
    between joint and sole custody had not yet been made.
    """
    UNKNOWN = "0"                          # Nicht abgeklärt / unbekannt
    LEGACY_PARENTAL_AUTHORITY = "1"        # Elterliche Sorge (legacy code for old law)
    JOINT_PARENTAL_AUTHORITY = "2"         # Gemeinsame elterliche Sorge
    SOLE_PARENTAL_AUTHORITY = "3"          # Alleinige elterliche Sorge
    NO_PARENTAL_AUTHORITY = "4"            # Keine elterliche Sorge


class KindOfEmployment(str, Enum):
    """Employment type codes per eCH-0021.

    Used in jobData to specify the kind of employment.

    Source: eCH-0021 v8.1.0, Kapitel 3.1.8.1 (page 14)
    XSD: kindOfEmploymentType (restriction of xs:string)
    """
    UNEMPLOYED = "0"                       # Erwerbslos
    SELF_EMPLOYED = "1"                    # Selbstständig
    EMPLOYED = "2"                         # Unselbstständig
    PENSION_RECIPIENT = "3"                # AHV/IV-Bezüger (pension/disability recipient)
    NOT_IN_LABOR_FORCE = "4"               # Nichterwerbsperson (housewife/-husband, students, etc.)


class YesNo(str, Enum):
    """Yes/No codes per eCH-0011 v9 yesNoType (used in eCH-0021).

    Generic yes/no type used throughout eCH standards.

    XSD: yesNoType (eCH-0011 v9, lines for yesNoType)
    PDF: eCH-0011 v9 specification
    Values: 0=No, 1=Yes (no "unknown" value exists in XSD)
    """
    NO = "0"                               # Nein (No)
    YES = "1"                              # Ja (Yes)


class UIDOrganisationIdCategory(str, Enum):
    """Swiss UID organization ID category per eCH-0021.

    The UID (Unternehmens-Identifikationsnummer) is Switzerland's unique
    business identifier. Categories distinguish enterprises from administrative
    units.

    XSD: uidOrganisationIdCategorie (restriction of xs:string)
    """
    ENTERPRISE = "CHE"                     # Commercial enterprise / Unternehmung
    ADMINISTRATION = "ADM"                 # Public administration / Verwaltung


class DataLockType(str, Enum):
    """Data lock codes per eCH-0021 v7 dataLockType.

    Specifies the level of data protection/blocking for person records.

    NOTE: This type was changed in v8 to use eCH-0011:yesNoType (only 0/1).
    The v7 definition with three values is preserved here for eCH-0020 v3 compatibility.

    XSD: dataLockType (eCH-0021-7-0.xsd lines 267-273)
    PDF: eCH-0020 v3.0 page 101 - "Der Codewert Datensperre kann folgende Werte annehmen"
    """
    NO_LOCK = "0"                          # Datensperre nicht gesetzt
    ADDRESS_LOCK = "1"                     # Adresssperre
    INFORMATION_LOCK = "2"                 # Auskunftssperre (removed in v8)


# Backward compatibility constants
RELATIONSHIP_MARRIED = TypeOfRelationship.SPOUSE.value
RELATIONSHIP_PARTNERSHIP = TypeOfRelationship.REGISTERED_PARTNER.value
RELATIONSHIP_FATHER = TypeOfRelationship.FATHER.value
RELATIONSHIP_MOTHER = TypeOfRelationship.MOTHER.value
