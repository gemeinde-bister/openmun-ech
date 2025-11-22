"""eCH-0006 v2.0 Swiss Residence Permit Type Codes.

Official Swiss residence permit classifications (Aufenthaltsbewilligungen).

Standard: eCH-0006 v2.0
XSD: eCH-0006-2-0.xsd
Namespace: http://www.ech.ch/xmlns/eCH-0006/2
Source: https://www.ech.ch/de/standards/39487

Common Swiss residence permits:
- L: Short stay (Kurzaufenthalt) - < 1 year
- B: Residence (Aufenthalt) - 1-5 years, renewable
- C: Settlement (Niederlassung) - permanent
- Ci: Family of international officials
- G: Cross-border commuter (Grenzgänger)
- F: Provisionally admitted (vorläufig aufgenommen)
- N: Asylum seeker (Asylsuchende)
- S: Protection (Schutzbedürftige)
"""

from enum import Enum
from typing import Optional

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field


class ResidencePermitCategoryType(str, Enum):
    """Residence permit base category codes per eCH-0006 v2.0.

    XSD: residencePermitCategoryType (lines 8-24)
    PDF Table 1 (page 5): Basiskategorien für Ausländer
    """
    A_SEASONAL_WORKER = "01"  # Saisonarbeiterin / Saisonarbeiter
    B_RESIDENCE = "02"  # Aufenthalterin / Aufenthalter
    C_SETTLEMENT = "03"  # Niedergelassene / Niedergelassener (permanent)
    CI_FAMILY_INTL_ORG = "04"  # Working spouse/children of foreign representatives
    F_PROVISIONALLY_ADMITTED = "05"  # Vorläufig Aufgenommene
    G_CROSS_BORDER_COMMUTER = "06"  # Grenzgängerin / Grenzgänger
    L_SHORT_TERM = "07"  # Kurzaufenthalterin / Kurzaufenthalter
    N_ASYLUM_SEEKER = "08"  # Asylsuchende
    S_PROTECTION_NEEDED = "09"  # Schutzbedürftige
    MANDATORY_REGISTRATION = "10"  # Meldepflichtige bei ZEMIS
    DIPLOMAT_WITH_IMMUNITY = "11"  # Diplomat with diplomatic immunity
    INTL_OFFICIAL_NO_IMMUNITY = "12"  # International official without immunity
    NOT_ASSIGNED = "13"  # Nicht zugeteilt


class ResidencePermitRulingType(str, Enum):
    """Residence permit regulation/ruling type codes per eCH-0006 v2.0.

    XSD: residencePermitRulingType (lines 25-37)
    PDF Table 2 (page 6): Regelungstypen (legal regulation basis)
    """
    EU_EFTA_REGULATION = "01"  # Regelung nach EU/EFTA-Abkommen
    NON_EU_EFTA_REGULATION = "02"  # Regelung nicht EU/EFTA-Abkommen
    PROVISIONALLY_ADMITTED_REG = "03"  # Regelung für vorläufig Aufgenommene
    ASYLUM_SEEKER_REG = "04"  # Regelung für Asylsuchende
    PROTECTION_NEEDED_REG = "05"  # Regelung für Schutzbedürftige
    MANDATORY_REGISTRATION_REG = "06"  # Regelung für Meldepflichtige
    DIPLOMAT_WITH_IMMUNITY_REG = "07"  # Vienna Convention (diplomatic immunity)
    INTL_OFFICIAL_NO_IMMUNITY_REG = "08"  # International officials without immunity
    TRAINEE_REGULATION = "09"  # Stagiaires-Abkommen (trainee agreements)


class ResidencePermitBorderType(str, Enum):
    """Cross-border commuter (G permit) duration codes per eCH-0006 v2.0.

    XSD: residencePermitBorderType (lines 38-43)
    PDF Table 3 (page 7): Grenzgängerin / Grenzgänger subcategories
    """
    STAY_LESS_12_MONTHS = "01"  # Aufenthalt <12 Monate
    STAY_12_MONTHS_OR_MORE = "02"  # Aufenthalt >=12 Monate


class ResidencePermitShortType(str, Enum):
    """Short-term residence (L permit) duration/type codes per eCH-0006 v2.0.

    XSD: residencePermitShortType (lines 44-54)
    PDF Table 4 (page 8): Kurzaufenthalterin / Kurzaufenthalter subcategories
    """
    SHORT_TERM_12_MONTHS_OR_MORE = "01"  # >=12 Monate
    SHORT_TERM_4_TO_12_MONTHS = "02"  # >4 bis <12 Monate
    SERVICE_PROVIDER_4_MONTHS_OR_LESS = "03"  # Dienstleistungserbringer <=4 Monate
    SHORT_TERM_4_MONTHS_OR_LESS = "04"  # <=4 Monate
    MUSICIAN_ARTIST_8_MONTHS_OR_LESS = "05"  # Musiker und Künstler <=8 Monate
    DANCER_8_MONTHS_OR_LESS = "06"  # Tänzer/Tänzerin <=8 Monate
    TRAINEE_18_MONTHS_OR_LESS = "07"  # Stagiaires <=18 Monate


class InhabitantControlType(str, Enum):
    """Inhabitant control codes per eCH-0006 v2.0.

    Base categories with regulation (4-digit codes = category + ruling).

    XSD: inhabitantControlType (lines 107-128)
    PDF page 12: Basiskategorien inkl. Regelung

    NOTE: These are combinations of ResidencePermitCategoryType + ResidencePermitRulingType.
    For semantic meaning, see ResidencePermitType enum values.
    """
    A_SEASONAL_NON_EU = "0102"  # 01 + 02
    B_RESIDENCE_EU_EFTA = "0201"  # 02 + 01
    B_RESIDENCE_NON_EU = "0202"  # 02 + 02
    C_SETTLEMENT_EU_EFTA = "0301"  # 03 + 01
    C_SETTLEMENT_NON_EU = "0302"  # 03 + 02
    CI_FAMILY_INTL_EU_EFTA = "0401"  # 04 + 01
    CI_FAMILY_INTL_NON_EU = "0402"  # 04 + 02
    F_PROV_ADMITTED = "0503"  # 05 + 03
    G_BORDER_EU_EFTA = "0601"  # 06 + 01
    G_BORDER_NON_EU = "0602"  # 06 + 02
    L_SHORT_TERM_EU_EFTA = "0701"  # 07 + 01
    L_SHORT_TERM_NON_EU = "0702"  # 07 + 02
    N_ASYLUM = "0804"  # 08 + 04
    S_PROTECTION = "0905"  # 09 + 05
    MANDATORY_REG = "1006"  # 10 + 06
    DIPLOMAT_IMMUNITY = "1107"  # 11 + 07 per eCH-0006 v1.0.1 (1108 replaced by 1107)
    INTL_NO_IMMUNITY = "1208"  # 12 + 08
    NOT_ASSIGNED = "1300"  # 13 + 00


class ResidencePermitDetailedType(str, Enum):
    """Most detailed permit codes per eCH-0006 v2.0 (leaf nodes only).

    XSD: residencePermitDetailedType (lines 129-168)
    PDF page 12-13: Detailed codes without parent categories

    NOTE: Subset of ResidencePermitType with only the most specific codes.
    Use ResidencePermitType enum for semantic names and documentation.
    """
    # Base categories with regulation (4-digit)
    A_SEASONAL_NON_EU = "0102"
    B_RESIDENCE_EU_EFTA = "0201"
    B_RESIDENCE_NON_EU = "0202"
    C_SETTLEMENT_EU_EFTA = "0301"
    C_SETTLEMENT_NON_EU = "0302"
    CI_FAMILY_INTL_EU_EFTA = "0401"
    CI_FAMILY_INTL_NON_EU = "0402"
    F_PROV_ADMITTED = "0503"
    G_BORDER_EU_EFTA = "0601"
    G_BORDER_NON_EU = "0602"
    # Cross-border subcategories (6-digit)
    G_BORDER_EU_EFTA_LESS_12M = "060101"
    G_BORDER_NON_EU_LESS_12M = "060201"
    G_BORDER_EU_EFTA_12M_OR_MORE = "060102"
    G_BORDER_NON_EU_12M_OR_MORE = "060202"
    # Short-term base (4-digit)
    L_SHORT_TERM_EU_EFTA = "0701"
    L_SHORT_TERM_NON_EU = "0702"
    # Short-term subcategories (6-digit)
    L_SHORT_EU_12M_OR_MORE = "070101"
    L_SHORT_NON_EU_12M_OR_MORE = "070201"
    L_SHORT_EU_4_TO_12M = "070102"
    L_SHORT_NON_EU_4_TO_12M = "070202"
    L_SERVICE_EU_4M_OR_LESS = "070103"
    L_SHORT_EU_4M_OR_LESS = "070104"
    L_SHORT_NON_EU_4M_OR_LESS = "070204"
    L_MUSICIAN_EU_8M_OR_LESS = "070105"
    L_MUSICIAN_NON_EU_8M_OR_LESS = "070205"
    L_DANCER_8M_OR_LESS = "070206"
    L_TRAINEE_18M_OR_LESS = "070907"
    # Other categories
    N_ASYLUM = "0804"
    S_PROTECTION = "0905"
    MANDATORY_REG = "1006"
    MANDATORY_REG_SWISS_EMPLOYER = "100601"
    MANDATORY_REG_SELF_EMPLOYED = "100602"
    MANDATORY_REG_POSTED_WORKER = "100603"
    DIPLOMAT_IMMUNITY = "1107"
    INTL_NO_IMMUNITY = "1208"
    NOT_ASSIGNED = "1300"


class ResidencePermitToBeRegisteredType(str, Enum):
    """Mandatory registration (Meldepflichtige) type codes per eCH-0006 v2.0.

    XSD: residencePermitToBeRegisteredType (lines 169-175)
    PDF Table 5 (page 8): Meldepflichtige subcategories
    """
    EMPLOYEE_SWISS_EMPLOYER = "01"  # Arbeitnehmer bei Schweizer Arbeitgeber
    SELF_EMPLOYED_SERVICE_PROVIDER = "02"  # Selbständige Dienstleistungserbringer
    POSTED_WORKER = "03"  # Entsandte Arbeitnehmer


class ResidencePermitType(str, Enum):
    """Swiss residence permit types per eCH-0006 v2.0.

    XSD: residencePermitType (lines 55-106) - 45 enumeration values
    PDF: Table 6 (pages 9-10) - Complete list with descriptions

    CRITICAL: These codes determine legal residence status in Switzerland.
    Wrong codes can affect voting rights, social services, and deportation risk.

    Code structure (PDF page 4):
    - 2 digits (01-13): Base category only
    - 4 digits (0201): Base + regulation
    - 6 digits (070204): Base + regulation + subcategory
    """

    # ========================================================================
    # A permit (01) - Seasonal worker (DEPRECATED 2002)
    # Saisonarbeiterin / Saisonarbeiter (Ausweis A)
    # ========================================================================
    A = "01"
    A_NON_EU_EFTA = "0102"  # Until 5.2002

    # ========================================================================
    # B permit (02) - Residence (1-5 years, renewable)
    # Aufenthalterin / Aufenthalter (Ausweis B)
    # ========================================================================
    B = "02"
    B_EU_EFTA = "0201"        # From 06.2002
    B_NON_EU_EFTA = "0202"    # From 11.1986

    # ========================================================================
    # C permit (03) - Settlement (permanent residence)
    # Niedergelassene / Niedergelassener (Ausweis C)
    # ========================================================================
    C = "03"
    C_EU_EFTA = "0301"        # From 06.2002
    C_NON_EU_EFTA = "0302"    # From 11.1986

    # ========================================================================
    # Ci permit (04) - Working family of international officials
    # Erwerbstätige Ehepartnerin/Kinder (Ausweis Ci)
    # ========================================================================
    CI = "04"
    CI_EU_EFTA = "0401"       # From 06.2002
    CI_NON_EU_EFTA = "0402"   # From 11.1986

    # ========================================================================
    # F permit (05) - Provisionally admitted foreigners
    # Vorläufig Aufgenommene (Ausweis F)
    # ========================================================================
    F = "05"
    F_PROVISIONALLY_ADMITTED = "0503"  # From 06.1986

    # ========================================================================
    # G permit (06) - Cross-border commuter
    # Grenzgängerin / Grenzgänger (Ausweis G)
    # ========================================================================
    G = "06"
    G_EU_EFTA = "0601"                 # From 06.2002
    G_NON_EU_EFTA = "0602"             # From 11.1986
    G_EU_EFTA_LESS_12M = "060101"      # From 06.2002, <12 months
    G_NON_EU_EFTA_LESS_12M = "060201"  # From 11.1986, <12 months
    G_EU_EFTA_12M_OR_MORE = "060102"   # From 06.2002, >=12 months
    G_NON_EU_EFTA_12M_OR_MORE = "060202"  # From 11.1986, >=12 months

    # ========================================================================
    # L permit (07) - Short-term residence
    # Kurzaufenthalterin / Kurzaufenthalter (Ausweis L)
    # ========================================================================
    L = "07"
    L_EU_EFTA = "0701"                        # From 06.2002
    L_NON_EU_EFTA = "0702"                    # From 11.1986
    L_EU_EFTA_12M_OR_MORE = "070101"          # >=12 months cumulative
    L_NON_EU_EFTA_12M_OR_MORE = "070201"      # >=12 months cumulative
    L_EU_EFTA_4_TO_12M = "070102"             # >4 to <12 months
    L_NON_EU_EFTA_4_TO_12M = "070202"         # >4 to <12 months
    L_SERVICE_PROVIDER_EU_4M_OR_LESS = "070103"  # Service provider <=4 months
    L_EU_EFTA_4M_OR_LESS = "070104"           # <=4 months
    L_NON_EU_EFTA_4M_OR_LESS = "070204"       # <=4 months
    L_MUSICIAN_ARTIST_EU_8M_OR_LESS = "070105"  # Musicians/artists <=8 months
    L_MUSICIAN_ARTIST_NON_EU_8M_OR_LESS = "070205"  # Musicians/artists <=8 months
    L_DANCER_8M_OR_LESS = "070206"            # Dancers <=8 months
    L_TRAINEE_18M_OR_LESS = "070907"          # Stagiaires <=18 months

    # ========================================================================
    # N permit (08) - Asylum seeker
    # Asylsuchende (Ausweis N)
    # ========================================================================
    N = "08"
    N_ASYLUM_SEEKER = "0804"  # From 01.1981

    # ========================================================================
    # S permit (09) - Protection (temporary)
    # Schutzbedürftige (Ausweis S)
    # ========================================================================
    S = "09"
    S_PROTECTION = "0905"  # From 10.1999

    # ========================================================================
    # Category 10 - Mandatory registration (Meldepflichtige)
    # No physical permit card - registration only
    # ========================================================================
    MANDATORY_REGISTRATION = "10"
    MANDATORY_REGISTRATION_DETAILED = "1006"              # From 06.2004
    MANDATORY_REG_SWISS_EMPLOYER = "100601"               # Employee with Swiss employer
    MANDATORY_REG_SELF_EMPLOYED = "100602"                # Self-employed service provider
    MANDATORY_REG_POSTED_WORKER = "100603"                # Posted worker

    # ========================================================================
    # Category 11 - Diplomat with immunity
    # Diplomatic ID card (not residence permit)
    # ========================================================================
    DIPLOMAT_WITH_IMMUNITY = "11"
    DIPLOMAT_WITH_IMMUNITY_DETAILED = "1107"  # From 06.1963

    # ========================================================================
    # Category 12 - International official without immunity
    # Special ID card
    # ========================================================================
    INTL_OFFICIAL_NO_IMMUNITY = "12"
    INTL_OFFICIAL_NO_IMMUNITY_DETAILED = "1208"  # From 07.1946

    # ========================================================================
    # Category 13 - Not assigned
    # ========================================================================
    NOT_ASSIGNED = "1300"


class PermitRoot(BaseModel):
    """Root element for permit data per eCH-0006 v2.0.

    XSD: permitRoot element (lines 176-189)

    Contains all permit-related fields (all optional).
    This is the main container for residence permit information.
    """

    residence_permit_category: Optional[ResidencePermitCategoryType] = None
    residence_permit_ruling: Optional[ResidencePermitRulingType] = None
    residence_permit_border: Optional[ResidencePermitBorderType] = None
    residence_permit_short_type: Optional[ResidencePermitShortType] = None
    residence_permit: Optional[ResidencePermitType] = None
    inhabitant_control: Optional[InhabitantControlType] = None
    residence_permit_detailed_type: Optional[ResidencePermitDetailedType] = None
    residence_permit_to_be_registered_type: Optional[ResidencePermitToBeRegisteredType] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,  # Keep enum objects, not string values
    )

    def to_xml(self, nsmap: Optional[dict] = None) -> etree.Element:
        """Convert to XML element.

        Args:
            nsmap: Optional namespace map. Defaults to eCH-0006 namespace.

        Returns:
            lxml Element for permitRoot
        """
        if nsmap is None:
            nsmap = {None: "http://www.ech.ch/xmlns/eCH-0006/2"}

        root = etree.Element("{http://www.ech.ch/xmlns/eCH-0006/2}permitRoot", nsmap=nsmap)

        if self.residence_permit_category is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitCategory")
            elem.text = self.residence_permit_category.value

        if self.residence_permit_ruling is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitRuling")
            elem.text = self.residence_permit_ruling.value

        if self.residence_permit_border is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitBorder")
            elem.text = self.residence_permit_border.value

        if self.residence_permit_short_type is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitShortType")
            elem.text = self.residence_permit_short_type.value

        if self.residence_permit is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermit")
            elem.text = self.residence_permit.value

        if self.inhabitant_control is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}inhabitantControl")
            elem.text = self.inhabitant_control.value

        if self.residence_permit_detailed_type is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitDetailedType")
            elem.text = self.residence_permit_detailed_type.value

        if self.residence_permit_to_be_registered_type is not None:
            elem = etree.SubElement(root, "{http://www.ech.ch/xmlns/eCH-0006/2}residencePermitToBeRegisteredType")
            elem.text = self.residence_permit_to_be_registered_type.value

        return root

    @classmethod
    def from_xml(cls, elem: etree.Element) -> 'PermitRoot':
        """Parse from XML element.

        Args:
            elem: lxml Element for permitRoot

        Returns:
            PermitRoot instance
        """
        ns = {"ech": "http://www.ech.ch/xmlns/eCH-0006/2"}

        # Extract all optional fields
        category_elem = elem.find("ech:residencePermitCategory", ns)
        ruling_elem = elem.find("ech:residencePermitRuling", ns)
        border_elem = elem.find("ech:residencePermitBorder", ns)
        short_type_elem = elem.find("ech:residencePermitShortType", ns)
        permit_elem = elem.find("ech:residencePermit", ns)
        control_elem = elem.find("ech:inhabitantControl", ns)
        detailed_elem = elem.find("ech:residencePermitDetailedType", ns)
        to_register_elem = elem.find("ech:residencePermitToBeRegisteredType", ns)

        return cls(
            residence_permit_category=ResidencePermitCategoryType(category_elem.text) if category_elem is not None else None,
            residence_permit_ruling=ResidencePermitRulingType(ruling_elem.text) if ruling_elem is not None else None,
            residence_permit_border=ResidencePermitBorderType(border_elem.text) if border_elem is not None else None,
            residence_permit_short_type=ResidencePermitShortType(short_type_elem.text) if short_type_elem is not None else None,
            residence_permit=ResidencePermitType(permit_elem.text) if permit_elem is not None else None,
            inhabitant_control=InhabitantControlType(control_elem.text) if control_elem is not None else None,
            residence_permit_detailed_type=ResidencePermitDetailedType(detailed_elem.text) if detailed_elem is not None else None,
            residence_permit_to_be_registered_type=ResidencePermitToBeRegisteredType(to_register_elem.text) if to_register_elem is not None else None,
        )


# Helper function for display
def get_permit_description(permit_code: str) -> str:
    """Get human-readable description of permit type.

    Args:
        permit_code: Permit code (e.g., "02", "0201", "06")

    Returns:
        Human-readable description

    Examples:
        >>> get_permit_description("02")
        'B'
        >>> get_permit_description("0601")
        'F Eu Efta'
        >>> get_permit_description("99")
        'Unknown permit: 99'
    """
    try:
        permit = ResidencePermitType(permit_code)
        return permit.name.replace('_', ' ').title()
    except ValueError:
        return f"Unknown permit: {permit_code}"
