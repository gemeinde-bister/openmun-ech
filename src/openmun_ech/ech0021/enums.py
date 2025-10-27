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
    MR = "1"           # Herr (Mr)
    MRS = "2"          # Frau (Mrs)


class TypeOfRelationship(str, Enum):
    """Type of relationship codes per eCH-0021.

    Used in marital relationships (codes 1-2) and parental relationships
    (codes 3-10) to specify the nature of the relationship.

    XSD: typeOfRelationshipType (restriction of xs:string)
    """
    # Marital relationships (used in maritalRelationship)
    MARRIED = "1"                          # Verheiratet
    REGISTERED_PARTNERSHIP = "2"           # Eingetragene Partnerschaft

    # Parental relationships (used in parentalRelationship)
    FATHER = "3"                           # Vater
    MOTHER = "4"                           # Mutter
    ADOPTIVE_FATHER = "5"                  # Adoptivvater
    ADOPTIVE_MOTHER = "6"                  # Adoptivmutter

    # Guardian relationships (used in guardianRelationship)
    GUARDIAN_PERSON = "7"                  # Vormund (Person)
    GUARDIAN_ORGANIZATION = "8"            # Vormund (Organisation)
    LEGAL_REPRESENTATIVE = "9"             # Beistand
    CURATOR = "10"                         # Kurator


class CareType(str, Enum):
    """Custody/care arrangement codes per eCH-0021.

    Used in parental relationships to specify custody arrangements.

    XSD: careType (restriction of xs:string)
    """
    UNKNOWN = "0"                          # Unbekannt
    JOINT_CUSTODY = "1"                    # Gemeinsame elterliche Sorge
    SOLE_CUSTODY_MOTHER = "2"              # Obhut Mutter
    SOLE_CUSTODY_FATHER = "3"              # Obhut Vater
    OTHER = "4"                            # Andere


class KindOfEmployment(str, Enum):
    """Employment type codes per eCH-0021.

    Used in jobData to specify the kind of employment.

    XSD: kindOfEmploymentType (restriction of xs:string)
    """
    UNKNOWN = "0"                          # Unbekannt
    EMPLOYED = "1"                         # Unselbständig erwerbstätig
    SELF_EMPLOYED = "2"                    # Selbständig erwerbstätig
    UNEMPLOYED = "3"                       # Arbeitslos
    NOT_IN_LABOR_FORCE = "4"               # Nichterwerbspersonen


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
RELATIONSHIP_MARRIED = TypeOfRelationship.MARRIED.value
RELATIONSHIP_PARTNERSHIP = TypeOfRelationship.REGISTERED_PARTNERSHIP.value
RELATIONSHIP_FATHER = TypeOfRelationship.FATHER.value
RELATIONSHIP_MOTHER = TypeOfRelationship.MOTHER.value
