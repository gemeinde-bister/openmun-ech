"""eCH-0011 Standard Code Enumerations (aligned with v9.0.0 PDF).

Official codes used throughout the Swiss e-government person data standard.

Primary reference: eCH-0011 v9.0.0 PDF for code lists (e.g., religion).
Namespace (models in v8 module): http://www.ech.ch/xmlns/eCH-0011/8
Source: https://www.ech.ch/de/standards/60021
"""

from enum import Enum


class Sex(str, Enum):
    """Sex codes per eCH-0011 sexType.

    XSD: sexType (restriction of xs:string with pattern [1-3])
    """
    MALE = "1"
    FEMALE = "2"
    UNKNOWN = "3"


class ReligionCode(str, Enum):
    """Religion codes per eCH-0011 religionType (v9.0.0 PDF list).

    Source: eCH-0011 v9.0.0, 3.3.4.1 "religion – Konfessionszugehörigkeit" (Seite 21)
    For deliveries to BFS, only these codes are permitted. Other contexts
    may exchange additional BFS codes, but they are not listed here.

    XSD: religionType (restriction of xs:string)
    """
    PROTESTANT_REFORMED = "111"                   # evangelisch-reformierte (protestantische) Kirche
    ROMAN_CATHOLIC = "121"                        # römisch-katholische Kirche
    CHRIST_CATHOLIC = "1221"                      # christkatholische / altkatholische Kirche
    JEWISH_COMMUNITY = "2112"                     # israelitische Gemeinschaft / jüdische Glaubensgemeinschaft
    ISRAELITISCHE_CULTUSGEMEINDE = "2112013"     # Israelitische Cultusgemeinde
    JEWISH_LIBERAL_COMMUNITY = "2113014"         # Jüdisch Liberale Gemeinde
    UNKNOWN = "000"                               # Unbekannt


class MaritalStatus(str, Enum):
    """Marital status codes per eCH-0011 maritalStatusType.

    XSD: maritalStatusType (lines 102-113)
    PDF: Section 3.3.5.1 (page 22)

    Note: Code "8" does NOT exist in XSD or PDF (skipped in standard).
    For separation status, use the separate separationType field.
    """
    SINGLE = "1"                          # Ledig (never married)
    MARRIED = "2"                         # Verheiratet
    WIDOWED = "3"                         # Verwitwet
    DIVORCED = "4"                        # Geschieden
    UNMARRIED = "5"                       # Unverheiratet (legacy code)
    REGISTERED_PARTNERSHIP = "6"          # In eingetragener Partnerschaft
    DISSOLVED_PARTNERSHIP = "7"           # Aufgelöste Partnerschaft (dissolved)
    UNKNOWN = "9"                         # Unbekannt (unknown marital status)


class SeparationType(str, Enum):
    """Separation type codes per eCH-0011 separationType.

    Used as a separate field in marital data when a person is separated.
    Note: Separation is NOT a marital status code, it's a separate attribute.

    XSD: separationType (lines 213-218)
    PDF: Section 3.3.5.5 (page 23)
    """
    FACTUAL_SEPARATION = "1"              # Freiwillig getrennt (voluntarily separated)
    JUDICIAL_SEPARATION = "2"             # Gerichtlich getrennt (judicially separated)


class PartnershipAbolition(str, Enum):
    """Partnership abolition reason codes per eCH-0011.

    Used when registered partnership is dissolved (maritalStatus = 7).

    XSD: partnershipAbolitionType (lines 114-122)
    PDF: Section 3.3.5.3 cancelationReason - Auflösungsgrund (page 23)
    """
    JUDICIAL_DISSOLUTION = "1"            # Gerichtlich aufgelöste Partnerschaft
    ANNULMENT = "2"                       # Ungültigerklärung
    DECLARED_MISSING = "3"                # Durch Verschollenerklärung
    DEATH = "4"                           # Durch Tod aufgelöste Partnerschaft
    UNKNOWN = "9"                         # Unbekannt / Andere Gründe


# Backward compatibility alias (deprecated, use PartnershipAbolition)
CancelationReason = PartnershipAbolition


class NationalityStatus(str, Enum):
    """Nationality status codes per eCH-0011 v9.0.0.

    Indicates whether nationality is known, NOT whether person is Swiss or foreign.
    Actual citizenship is determined by presence of placeOfOriginInfo (Swiss) vs residencePermitData (foreign).

    Source: eCH-0011 v9.0.0, Kapitel 3.3.6.1
    XSD: nationalityStatusType (restriction of xs:string)
    """
    UNKNOWN = "0"                         # Staatsangehörigkeit unbekannt (Nationality unknown)
    STATELESS = "1"                       # Staatenlos (Stateless)
    KNOWN = "2"                           # Staatsangehörigkeit bekannt (Nationality known)


class LanguageCode(str, Enum):
    """Language codes for correspondence per eCH-0011 languageType.

    Swiss official languages plus English for international contexts.
    The XSD allows any 2-character language code, but these are the
    commonly used values in Swiss municipalities.

    XSD: languageType (xs:token with maxLength=2)
    Source: ISO 639-1 language codes
    """
    GERMAN = "de"                         # Deutsch (German)
    FRENCH = "fr"                         # Français (French)
    ITALIAN = "it"                        # Italiano (Italian)
    ROMANSH = "rm"                        # Rumantsch (Romansh)
    ENGLISH = "en"                        # English (for international contexts)


class TypeOfResidence(str, Enum):
    """Type of residence codes per eCH-0011 typeOfResidenceType.

    Indicates whether residence is main, secondary, or other.

    XSD: typeOfResidenceType (restriction of xs:nonNegativeInteger)
    """
    MAIN = "1"                            # Hauptwohnsitz
    SECONDARY = "2"                       # Nebenwohnsitz
    OTHER = "3"                           # Weitere Wohnsitzart


class TypeOfHousehold(str, Enum):
    """Type of household codes per eCH-0011 typeOfHouseholdType.

    Indicates the household structure type.

    Source: eCH-0011 v9.0.0, Kapitel 3.4.5.5 (page 35)
    XSD: typeOfHouseholdType (restriction of xs:string)
    """
    NOT_YET_ASSIGNED = "0"                # Haushaltsart noch nicht zugeteilt
    PRIVATE_HOUSEHOLD = "1"               # Privathaushalt
    COLLECTIVE_HOUSEHOLD = "2"            # Kollektivhaushalt
    GROUP_HOUSEHOLD = "3"                 # Sammelhaushalt


class FederalRegister(str, Enum):
    """Federal register codes per eCH-0011 federalRegisterType.

    Used to identify Swiss federal registers in residence data.
    Alternative to reportingMunicipality in some use cases.

    XSD: federalRegisterType (lines 18-24)
    PDF: Section 3.4.1.1 federalRegister - Bundesregister (page 36)
    """
    INFOSTAR = "1"                        # INFOSTAR (civil status registry)
    ORDIPRO = "2"                         # Ordipro (criminal records registry)
    ZEMIS = "3"                           # ZEMIS (immigration/asylum registry)


class YesNo(str, Enum):
    """Yes/No codes per eCH-0011 yesNoType.

    Binary indicator type defined in XSD but not actively used.
    Included for 100% XSD compliance.

    XSD: yesNoType (lines 343-348)
    PDF: Not documented (type defined but not used in v9.0)
    """
    NO = "0"                              # No / Nein
    YES = "1"                             # Yes / Ja


# Backward compatibility constants
SEX_MALE = Sex.MALE.value
SEX_FEMALE = Sex.FEMALE.value
SEX_UNKNOWN = Sex.UNKNOWN.value

MARITAL_SINGLE = MaritalStatus.SINGLE.value
MARITAL_MARRIED = MaritalStatus.MARRIED.value
MARITAL_WIDOWED = MaritalStatus.WIDOWED.value
MARITAL_DIVORCED = MaritalStatus.DIVORCED.value
MARITAL_UNKNOWN = MaritalStatus.UNKNOWN.value  # Replaced MARITAL_SEPARATED
