"""eCH-0129 v6.0.0 Datenstandard Objektwesen — Enumerations.

All simpleType enumerations from eCH-0129-6-0.xsd, verified field-by-field
against the PDF STAN_d_DEF_2022-02-06_eCH-0129_V6.0.0_Objektwesen.pdf.

XSD: http://www.ech.ch/xmlns/eCH-0129/6
Source: https://www.ech.ch/de/standards/39432
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Construction Project (§4.3)
# ---------------------------------------------------------------------------

class TypeOfConstructionProject(str, Enum):
    """Type of construction project per eCH-0129 typeOfConstructionProjectType.

    XSD: typeOfConstructionProjectType (restriction of xs:nonNegativeInteger)
    PDF: §4.3.1.5 Art der Bauwerke (page 24)
    """
    CIVIL_ENGINEERING = "6010"              # Tiefbau
    BUILDING_CONSTRUCTION = "6011"          # Hochbau
    SPECIAL_CONSTRUCTION = "6012"           # Sonderbauten


class TypeOfPermit(str, Enum):
    """Permit type (legal basis) per eCH-0129 typeOfPermitType.

    XSD: typeOfPermitType (restriction of xs:nonNegativeInteger)
    PDF: §4.3.1.7 Bewilligungsgrund (page 25, Tabelle 6)
    """
    BAUZONE = "5000"                        # Bauzone
    OEKONOMIEBAUTEN_LANDWIRTSCHAFT = "5001" # Ökonomiebauten für die bodenabhängige Landwirtschaft
    LANDW_AUFBEREITUNG_LAGERUNG = "5002"    # Landwirtschaftliche Bauten: Aufbereitung, Lagerung, Verkauf
    WOHNBAUTEN_LANDW_GEWERBE = "5003"       # Wohnbauten für landwirtschaftliche Gewerbe
    GEMEINSCHAFTLICHE_STALLBAUTEN = "5004"  # Gemeinschaftliche Stallbauten
    INNERE_AUFSTOCKUNG_TIERHALTUNG = "5005" # Innere Aufstockung Tierhaltung (Schweineställe, Geflügelhallen)
    INNERE_AUFSTOCKUNG_PFLANZENBAU = "5006" # Innere Aufstockung Gemüse- und Pflanzenbau (Gewächshäuser)
    SPEZIALLANDWIRTSCHAFTSZONEN = "5007"    # Bauten und Anlagen in Speziallandwirtschaftszonen
    ENERGIE_AUS_BIOMASSE = "5008"           # Gewinnung von Energie aus Biomasse
    SCHUTZZONEN = "5009"                    # Zonenkonforme Bauten und Anlagen in Schutzzonen
    SPEZIALZONEN = "5011"                   # Zonenkonforme Bauten/Anlagen in Spezialzonen (Deponie, Sport u.ä.)
    WEILER_ERHALTUNGSZONEN = "5012"         # Zonenkonforme Bauten in Weiler- oder Erhaltungszonen u.ä.
    SOLARANLAGEN = "5015"                   # Solaranlagen
    STANDORTGEBUNDENE = "5021"              # Standortgebundene Bauten und Anlagen
    ZWECKAENDERUNG_STREUSIEDLUNG = "5022"   # Vollst. Zweckänderung von Bauten in Streusiedlungsgebieten
    ZWECKAENDERUNG_LANDSCHAFTSPRAEGEND = "5023"  # Vollständige Zweckänderung landschaftsprägender Bauten
    ZWECKAENDERUNG_OHNE_BAULICH = "5031"    # Zweckänderungen ohne bauliche Massnahmen
    NEBENBETRIEBE_EXISTENZSICHERUNG = "5041"  # Nichtlandwirtschaftliche Nebenbetriebe zur Existenzsicherung
    NEBENBETRIEBE_LANDW_BEZUG = "5043"      # Nichtlandw. Nebenbetriebe mit engem Bezug zu landw. Gewerbe
    NEBENBETRIEBE_TEMPORAER = "5044"        # Nichtlandw. Nebenbetriebe in temporären Betriebszentren
    AENDERUNG_ZONENWIDRIG_GEWORDEN = "5051" # Änderung zonenwidrig gewordener Bauten und Anlagen
    AENDERUNG_LANDW_WOHNBAUTEN = "5061"     # Änderungen an ehem. landw. genutzten Wohnbauten
    ZWECKAENDERUNG_GESCHUETZT = "5062"      # Vollständige Zweckänderung geschützter Bauten
    HOBBYMÄSSIGE_TIERHALTUNG_NAH = "5064"   # Hobbymässige Tierhaltung in nahe gelegenen Gebäuden
    AUSSENANLAGEN_HOBBYMÄSSIG = "5063"      # Aussenanlagen zur hobbymässigen Tierhaltung
    AENDERUNG_ZONENWIDRIG_GEWERBLICH = "5071"  # Änderung zonenwidrig gewordener gewerblicher Bauten


class ProjectStatus(str, Enum):
    """Project status per eCH-0129 projectStatusType.

    XSD: projectStatusType (restriction of xs:nonNegativeInteger)
    PDF: §4.3.1.17 Projektstatus (page 27)
    """
    SUBMITTED = "6701"                      # Baugesuch eingereicht
    PERMIT_GRANTED = "6702"                 # Baubewilligung erteilt (rechtswirksam)
    CONSTRUCTION_STARTED = "6703"           # baubegonnen
    COMPLETED = "6704"                      # abgeschlossen
    SUSPENDED = "6706"                      # Projekt sistiert
    PERMIT_DENIED = "6707"                  # Baugesuch abgelehnt (rechtswirksam)
    NOT_REALIZED = "6708"                   # nicht realisiert
    WITHDRAWN = "6709"                      # zurückgezogen


class TypeOfClient(str, Enum):
    """Client type per eCH-0129 typeOfClientType.

    XSD: typeOfClientType (restriction of xs:nonNegativeInteger)
    PDF: §4.3.1.18 Typ der Auftraggeber (page 28-29)
    """
    SBB = "6101"                            # SBB (Schweizerische Bundesbahnen)
    VBS = "6103"                            # VBS (Eidg. Departement für Verteidigung, Bevölkerungsschutz und Sport)
    BBL = "6104"                            # BBL (Bundesamt für Bauten und Logistik)
    SWISSCOM = "6107"                       # SWISSCOM
    DIE_POST = "6108"                       # Die Post
    KANTONE = "6110"                        # Kantone (ohne öffentliche Unternehmen)
    OEFFENTL_UNTERNEHMEN_KANTON = "6111"    # Öffentliche Unternehmen eines Kantons (ohne KB/GV)
    GEMEINDEN = "6115"                      # Gemeinden inkl. Korporationen des öffentlichen Rechts
    OEFFENTL_UNTERNEHMEN_GEMEINDE = "6116"  # Öffentliche Unternehmen einer Gemeinde (Werke usw.)
    VERSICHERUNGEN = "6121"                 # Versicherungsgesellschaften ohne Pensionskassen und Krankenkassen
    PENSIONSKASSEN = "6122"                 # Personalfürsorgestiftungen (Pensionskassen)
    KRANKENKASSEN_SUVA = "6123"             # Krankenkassen, SUVA
    BANKEN = "6124"                         # Banken, Immobilienfonds oder Finanzholdings
    PRIVATE_ELEKTRIZITAETSWERKE = "6131"    # Private Elektrizitätswerke
    PRIVATE_GASWERKE = "6132"               # Private Gaswerke
    PRIVATBAHNEN = "6133"                   # Privatbahnen
    EINZELFIRMEN_IMMOBILIEN = "6141"        # Einzelfirmen oder Personengesellschaften der Immobilienbranche
    WOHNBAUGENOSSENSCHAFTEN = "6142"        # Wohnbaugenossenschaften
    KAPITALGESELLSCHAFTEN_IMMOBILIEN = "6143"  # Kapitalgesellschaften der Immobilienbranche
    PRIVATPERSONEN = "6161"                 # Privatpersonen, inkl. Erbengemeinschaften
    EINZELFIRMEN_NICHT_IMMOBILIEN = "6151"  # Einzelfirmen oder Personengesellschaften ohne Immobilienbranche
    KAPITALGESELLSCHAFTEN_NICHT_IMMOBILIEN = "6152"  # Kapitalgesellschaften ohne Immobilienbranche
    ANDERE_PRIVATE = "6162"                 # Andere private Auftraggeber (Kirche, Stiftung, Verein, etc.)
    INTERNATIONALE_ORGANISATIONEN = "6163"  # Internationale Organisationen, Botschaften


class TypeOfConstruction(str, Enum):
    """Construction type per eCH-0129 typeOfConstructionType.

    XSD: typeOfConstructionType (restriction of xs:nonNegativeInteger)
    PDF: §4.3.1.19 Typ der Bauwerke (page 29-30)
    """
    WASSERVERSORGUNGSANLAGEN = "6211"       # Wasserversorgungsanlagen
    ELEKTRIZITAETSWERKE = "6212"            # Elektrizitätswerke und -netze
    GASWERKE = "6213"                       # Gaswerke und -netze, chemische Anlagen
    FERNHEIZUNGSANLAGEN = "6214"            # Fernheizungsanlagen
    UEBRIGE_VERSORGUNGSANLAGEN = "6219"     # Übrige Versorgungsanlagen
    WASSERENTSORGUNGSANLAGEN = "6221"       # Wasserentsorgungsanlagen
    KEHRICHTENTSORGUNGSANLAGEN = "6222"     # Kehrichtentsorgungsanlagen
    UEBRIGE_ENTSORGUNGSANLAGEN = "6223"     # Übrige Entsorgungsanlagen
    NATIONALSTRASSEN = "6231"               # Nationalstrassen
    KANTONALSTRASSEN = "6232"               # Kantonalstrassen
    GEMEINDESTRASSEN = "6233"               # Gemeindestrassen
    UEBRIGER_STRASSENBAU = "6234"           # Übriger Strassenbau, Parkplätze
    PARKHAEUSER = "6235"                    # Parkhäuser
    BAHNANLAGEN = "6241"                    # Bahnanlagen
    BUS_TRAMANLAGEN = "6242"                # Bus- und Tramanlagen
    SCHIFFSVERKEHRSANLAGEN = "6243"         # Schiffsverkehrsanlagen
    FLUGVERKEHRSANLAGEN = "6244"            # Flugverkehrsanlagen
    KOMMUNIKATIONSANLAGEN = "6245"          # Kommunikationsanlagen
    UEBRIGE_VERKEHRSANLAGEN = "6249"        # Übrige Verkehrsanlagen
    SCHULEN = "6251"                        # Schulen, Bildungswesen (bis Maturstufe)
    HOEHERES_BILDUNGSWESEN = "6252"         # Höheres Bildungswesen und Forschung
    AKUTSPITAELER = "6253"                  # Akutspitäler, allgemeine Spitäler
    HEIME = "6254"                          # Heime mit Unterkunft, Pflegedienste und/oder Betreuung
    UEBRIGES_GESUNDHEITSWESEN = "6255"      # Übriges spezialisiertes Gesundheitswesen
    FREIZEIT_TOURISMUSANLAGEN = "6256"      # Freizeit-, Tourismusanlagen
    KIRCHEN_SAKRALBAUTEN = "6257"           # Kirchen und Sakralbauten
    KULTURBAUTEN = "6258"                   # Kulturbauten inkl. Museen, Bibliotheken und Denkmäler
    SPORTHALLEN_SPORTPLAETZE = "6259"       # Sporthallen und Sportplätze
    UFERVERBAUUNGEN = "6261"                # Uferverbauungen, Staudämme
    LANDESVERTEIDIGUNGSBAUTEN = "6262"       # Landesverteidigungsbauten
    UEBRIGE_INFRASTRUKTUR = "6269"          # Übrige Infrastruktur
    EINFAMILIENHAEUSER_FREISTEHEND = "6271" # Einfamilienhäuser freistehend
    EINFAMILIENHAEUSER_ANGEBAUT = "6272"    # Einfamilienhäuser angebaut
    MEHRFAMILIENHAEUSER = "6273"            # Mehrfamilienhäuser (reine Wohngebäude)
    WOHNGEBAEUDE_MIT_NEBENNUTZUNG = "6274"  # Wohngebäude mit Nebennutzung (inkl. Bauernhäuser)
    WOHNHEIME = "6276"                      # Wohnheime ohne Pflegedienste und/oder Betreuung
    GARAGEN_PARKPLAETZE = "6278"            # Garagen, Parkplätze, Einstellhallen mit Wohngebäuden
    UEBRIGE_BAUTEN_WOHNGEBAEUDE = "6279"    # Übrige Bauten im Zusammenhang mit Wohngebäuden
    LANDWIRTSCHAFTSBAUTEN = "6281"          # Landwirtschaftsbauten
    FORSTWIRTSCHAFTSBAUTEN = "6282"         # Forstwirtschaftsbauten
    MELIORATIONEN = "6283"                  # Meliorationen
    WERKSTAETTEN = "6291"                   # Werkstätten, Fabrikgebäude
    LAGERHALLEN = "6292"                    # Lagerhallen, Depots, Silos, Zisternen
    BUEROGEBAEUDE = "6293"                  # Bürogebäude, Verwaltungsgebäude
    KAUFHAEUSER = "6294"                    # Kaufhäuser, Geschäftsgebäude
    HOTELS = "6295"                         # Hotels, Restaurants
    ANDERE_BEHERBERGUNGEN = "6296"          # Andere Beherbergungen
    UEBRIGE_WIRTSCHAFTLICHE = "6299"        # Übrige Verwendung für wirtschaftliche Zwecke


class KindOfWork(str, Enum):
    """Kind of construction work per eCH-0129 kindOfWorkType.

    XSD: kindOfWorkType (restriction of xs:nonNegativeInteger)
    PDF: §4.4.1.1 Art der Arbeiten (page 32)
    """
    NEW_CONSTRUCTION = "6001"               # Neubau
    CONVERSION = "6002"                     # Umbau
    DEMOLITION = "6007"                     # Abbruch


# ---------------------------------------------------------------------------
# Building (§4.5)
# ---------------------------------------------------------------------------

class PeriodOfConstruction(str, Enum):
    """Construction period per eCH-0129 periodOfConstructionType.

    XSD: periodOfConstructionType (restriction of xs:nonNegativeInteger)
    PDF: §4.24.3.1 Bauperiode (page 99-100)
    """
    BEFORE_1919 = "8011"                    # Periode vor 1919
    P_1919_1945 = "8012"                    # Periode von 1919 bis 1945
    P_1946_1960 = "8013"                    # Periode von 1946 bis 1960
    P_1961_1970 = "8014"                    # Periode von 1961 bis 1970
    P_1971_1980 = "8015"                    # Periode von 1971 bis 1980
    P_1981_1985 = "8016"                    # Periode von 1981 bis 1985
    P_1986_1990 = "8017"                    # Periode von 1986 bis 1990
    P_1991_1995 = "8018"                    # Periode von 1991 bis 1995
    P_1996_2000 = "8019"                    # Periode von 1996 bis 2000
    P_2001_2005 = "8020"                    # Periode von 2001 bis 2005
    P_2006_2010 = "8021"                    # Periode von 2006 bis 2010
    P_2011_2015 = "8022"                    # Periode von 2011 bis 2015
    FROM_2016 = "8023"                      # Periode ab 2016


class BuildingCategory(str, Enum):
    """Building category per eCH-0129 buildingCategoryType.

    XSD: buildingCategoryType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.13 Gebäudekategorie (page 40)
    """
    PROVISIONAL = "1010"                    # Provisorische Unterkunft
    RESIDENTIAL_ONLY = "1020"               # Reine Wohngebäude (Wohnnutzung ausschliesslich)
    RESIDENTIAL_WITH_SECONDARY = "1030"     # Wohngebäude mit Nebennutzung
    PARTIAL_RESIDENTIAL = "1040"            # Gebäude mit teilweiser Wohnnutzung
    NON_RESIDENTIAL = "1060"                # Gebäude ohne Wohnnutzung
    SPECIAL = "1080"                        # Sonderbau


class BuildingStatus(str, Enum):
    """Building status per eCH-0129 buildingStatusType.

    XSD: buildingStatusType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.15 Gebäudestatus (page 40-41)
    """
    PROJECTED = "1001"                      # Projektiert
    APPROVED = "1002"                       # Bewilligt
    UNDER_CONSTRUCTION = "1003"             # Im Bau
    EXISTING = "1004"                       # Bestehend
    UNUSABLE = "1005"                       # Nicht nutzbar
    DEMOLISHED = "1007"                     # Abgebrochen
    NOT_REALIZED = "1008"                   # Nicht realisiert
    NOT_USABLE = "1009"                     # XSD value 1009 (not described in PDF §4.5.1.15)


class HeatGeneratorHeating(str, Enum):
    """Heat generator for heating per eCH-0129 heatGeneratorHeatingType.

    XSD: heatGeneratorHeatingType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.24.1 Wärmeerzeuger für Heizung (page 44)
    """
    NONE = "7400"                           # Kein Wärmeerzeuger
    HEAT_PUMP_SINGLE = "7410"              # Wärmepumpe für ein Gebäude
    HEAT_PUMP_MULTI = "7411"               # Wärmepumpe für mehrere Gebäude
    THERMAL_SOLAR_SINGLE = "7420"          # Thermische Solaranlage für ein Gebäude
    THERMAL_SOLAR_MULTI = "7421"           # Thermische Solaranlage für mehrere Gebäude
    BOILER_GENERIC_SINGLE = "7430"         # Heizkessel (generisch) für ein Gebäude
    BOILER_GENERIC_MULTI = "7431"          # Heizkessel (generisch) für mehrere Gebäude
    BOILER_NON_CONDENSING_SINGLE = "7432"  # Heizkessel nicht kondensierend für ein Gebäude
    BOILER_NON_CONDENSING_MULTI = "7433"   # Heizkessel nicht kondensierend für mehrere Gebäude
    BOILER_CONDENSING_SINGLE = "7434"      # Heizkessel kondensierend für ein Gebäude
    BOILER_CONDENSING_MULTI = "7435"       # Heizkessel kondensierend für mehrere Gebäude
    STOVE = "7436"                         # Ofen
    CHP_SINGLE = "7440"                    # Wärmekraftkopplungsanlage für ein Gebäude
    CHP_MULTI = "7441"                     # Wärmekraftkopplungsanlage für mehrere Gebäude
    ELECTRIC_STORAGE_SINGLE = "7450"       # Elektrospeicher-Zentralheizung für ein Gebäude
    ELECTRIC_STORAGE_MULTI = "7451"        # Elektrospeicher-Zentralheizung für mehrere Gebäude
    ELECTRIC_DIRECT = "7452"               # Elektro direkt
    HEAT_EXCHANGER_SINGLE = "7460"         # Wärmetauscher (einschl. Fernwärme) für ein Gebäude
    HEAT_EXCHANGER_MULTI = "7461"          # Wärmetauscher (einschl. Fernwärme) für mehrere Gebäude
    OTHER = "7499"                         # Andere


class HeatGeneratorHotWater(str, Enum):
    """Heat generator for hot water per eCH-0129 heatGeneratorHotWaterType.

    XSD: heatGeneratorHotWaterType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.25.1 Wärmeerzeuger für Warmwasser (page 46-47)
    """
    NONE = "7600"                          # Kein Wärmeerzeuger
    HEAT_PUMP = "7610"                     # Wärmepumpe
    THERMAL_SOLAR = "7620"                 # Thermische Solaranlage
    BOILER_GENERIC = "7630"                # Heizkessel (generisch)
    BOILER_NON_CONDENSING = "7632"         # Heizkessel nicht kondensierend
    BOILER_CONDENSING = "7634"             # Heizkessel kondensierend
    CHP = "7640"                           # Wärmekraftkopplungsanlage
    CENTRAL_BOILER = "7650"                # Zentraler Elektroboiler
    SMALL_BOILER = "7651"                  # Kleinboiler
    HEAT_EXCHANGER = "7660"                # Wärmetauscher (einschliesslich für Fernwärme)
    OTHER = "7699"                         # Andere


class EnergySource(str, Enum):
    """Energy source per eCH-0129 energySourceType.

    XSD: energySourceType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.24.2 Energieträger (page 45)
    """
    NONE = "7500"                          # Keine
    AIR = "7501"                           # Luft
    GEOTHERMAL_GENERIC = "7510"            # Erdwärme (generisch)
    GEOTHERMAL_PROBE = "7511"              # Erdwärmesonde
    GEOTHERMAL_REGISTER = "7512"           # Erdregister
    WATER = "7513"                         # Wasser (Grundwasser, Oberflächenwasser, Abwasser)
    GAS = "7520"                           # Gas
    HEATING_OIL = "7530"                   # Heizöl
    WOOD_GENERIC = "7540"                  # Holz (generisch)
    WOOD_LOG = "7541"                      # Holz (Stückholz)
    WOOD_PELLETS = "7542"                  # Holz (Pellets)
    WOOD_CHIPS = "7543"                    # Holz (Schnitzel)
    WASTE_HEAT = "7550"                    # Abwärme (innerhalb des Gebäudes)
    ELECTRICITY = "7560"                   # Elektrizität
    SUN_THERMAL = "7570"                   # Sonne (thermisch)
    DISTRICT_HEAT_GENERIC = "7580"         # Fernwärme (generisch)
    DISTRICT_HEAT_HIGH_TEMP = "7581"       # Fernwärme (Hochtemperatur)
    DISTRICT_HEAT_LOW_TEMP = "7582"        # Fernwärme (Niedertemperatur)
    UNDETERMINED = "7598"                  # Unbestimmt
    OTHER = "7599"                         # Andere


class InformationSource(str, Enum):
    """Information source for heating/hot water per eCH-0129 informationSourceType.

    XSD: informationSourceType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.24.3 Informationsquelle (page 45-46)
    """
    OFFICIAL_ESTIMATION = "852"            # Gemäss amtlicher Schätzung
    BUILDING_INSURANCE = "853"             # Gemäss Gebäudeversicherung
    CHIMNEY_INSPECTION = "855"             # Gemäss Feuerungskontrolle
    OWNER = "857"                          # Gemäss Eigentümer/in oder Verwaltung
    GEAK = "858"                           # Gemäss Gebäudeenergieausweis der Kantone (GEAK)
    OTHER = "859"                          # Andere Datenquelle
    CENSUS_2000 = "860"                    # Gemäss Volkszählung 2000
    CANTONAL_DATA = "864"                  # Gemäss Daten des Kantons
    MUNICIPAL_DATA = "865"                 # Gemäss Daten der Gemeinde
    BUILDING_PERMIT = "869"                # Gemäss Baubewilligung
    UTILITY = "870"                        # Gemäss Versorgungswerk (Gas, Fernwärme)
    MINERGIE = "871"                       # Gemäss Minergie


class BuildingVolumeInformationSource(str, Enum):
    """Information source for building volume per eCH-0129 buildingVolumeInformationSourceType.

    XSD: buildingVolumeInformationSourceType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.23.2 Informationsquelle zum Gebäudevolumen (page 43)
    """
    BUILDING_PERMIT = "869"                # Gemäss Baubewilligung
    GEAK = "858"                           # Gemäss Gebäudeenergieausweis der Kantone (GEAK)
    BUILDING_INSURANCE = "853"             # Gemäss Gebäudeversicherung
    OFFICIAL_ESTIMATION = "852"            # Gemäss amtlicher Schätzung
    OWNER = "857"                          # Gemäss Eigentümer / Immobilienverwaltung
    OFFICIAL_SURVEY = "851"                # Gemäss amtlicher Vermessung
    TLM = "870"                            # Gemäss topografisches Landschaft Modell (TLM)
    NOT_DETERMINABLE = "878"               # Nicht bestimmbares Volumen (Gebäude nicht geschlossen)
    OTHER = "859"                          # Andere


class BuildingVolumeNorm(str, Enum):
    """Volume norm per eCH-0129 buildingVolumeNormType.

    XSD: buildingVolumeNormType (restriction of xs:nonNegativeInteger)
    PDF: §4.5.1.23.3 Gebäudevolumen: Norm (page 43-44)
    """
    SIA_116 = "961"                        # Gemäss SIA-Norm 116
    SIA_416 = "962"                        # Gemäss SIA-Norm 416
    UNKNOWN = "969"                        # unbekannt


class ThermotechnicalDeviceHeatingType(str, Enum):
    """Thermotechnical device heating type per eCH-0129 thermotechnicalDeviceHeatingTypeType.

    XSD: thermotechnicalDeviceHeatingTypeType (restriction of xs:nonNegativeInteger)
    PDF: not individually described — XSD only
    """
    TYPE_7701 = "7701"
    TYPE_7702 = "7702"
    TYPE_7703 = "7703"


# ---------------------------------------------------------------------------
# Dwelling (§4.6)
# ---------------------------------------------------------------------------

class DwellingStatus(str, Enum):
    """Dwelling status per eCH-0129 dwellingStatusType.

    XSD: dwellingStatusType (restriction of xs:nonNegativeInteger)
    PDF: §4.6.1.14 Wohnungstatus (page 52)
    """
    PROJECTED = "3001"                     # Projektiert
    APPROVED = "3002"                      # Bewilligt
    UNDER_CONSTRUCTION = "3003"            # Im Bau
    EXISTING = "3004"                      # Bestehend
    UNUSABLE = "3005"                      # Nicht nutzbar
    CANCELLED = "3007"                     # Aufgehoben
    NOT_REALIZED = "3008"                  # Nicht realisiert
    NOT_USABLE = "3009"                    # XSD value 3009


class DwellingUsageCode(str, Enum):
    """Dwelling usage code per eCH-0129 dwellingUsageCodeType.

    XSD: dwellingUsageCodeType (restriction of xs:nonNegativeInteger)
    PDF: §4.6.1.15 Wohnungsnutzung (page 53)
    """
    MAIN_RESIDENCE = "3010"                # Bewohnt gemäss RHG Art. 3 Bst. b (Erstwohnung)
    SECONDARY_RESIDENCE = "3020"           # Zeitweise bewohnt (Zweitwohnung)
    MISUSED = "3030"                       # Zweckentfremdet
    WORK_EDUCATION = "3031"                # Zu Erwerbs- oder Ausbildungszwecken bewohnt
    SAME_HOUSEHOLD = "3032"                # Von Privathaushalt mit Erstwohnung im gleichen Gebäude bewohnt
    NON_REGISTERABLE = "3033"              # Bewohnt von nicht meldepflichtigen Personen
    VACANT_SHORT = "3034"                  # Leerstehend seit höchstens zwei Jahren
    ALPINE_USE = "3035"                    # Für alpwirtschaftliche Zwecke genutzt
    STAFF_ACCOMMODATION = "3036"           # Zur Unterbringung von Personal genutzt
    SERVICE_DWELLING = "3037"              # Dienstwohnungen
    COLLECTIVE_HOUSEHOLD = "3038"          # Von einem Kollektivhaushalt genutzt
    UNINHABITABLE = "3070"                 # Wohnung unbewohnbar


class DwellingInformationSource(str, Enum):
    """Information source for dwelling usage per eCH-0129 dwellingInformationSourceType.

    XSD: dwellingInformationSourceType (restriction of xs:nonNegativeInteger)
    PDF: §4.6.1.15.2 Informationsquelle zur Nutzungsart (page 54)
    """
    AUTOMATIC = "3090"                     # Automatische Aktualisierung (Art. 2 Abs. 1 ZWV)
    EWK = "3091"                           # Einwohnerkontrolle
    OWNER = "3092"                         # Eigentümer/in oder Verwaltung
    OTHER = "3093"                         # Andere Datenquelle


class UsageLimitation(str, Enum):
    """Usage limitation per ZWG per eCH-0129 usageLimitationType.

    XSD: usageLimitationType (restriction of xs:nonNegativeInteger)
    PDF: §4.6.1.11 Nutzungsbeschränkung gemäss ZWG (page 51-52)
    """
    NONE = "3401"                          # Keine Beschränkung (Art. 8, 9 und 10 ZWG)
    PRIMARY_RESIDENCE = "3402"             # Erstwohnung (Art. 7 Abs. 1 Bst. a ZWG)
    TOURIST_MANAGED_A = "3403"             # Tour. bewirtschaftete Wohnung (Art. 7 Abs. 2 Bst. a ZWG)
    TOURIST_MANAGED_B = "3404"             # Tour. bewirtschaftete Wohnung (Art. 7 Abs. 2 Bst. b ZWG)


# ---------------------------------------------------------------------------
# Realestate (§4.8)
# ---------------------------------------------------------------------------

class RealestateType(str, Enum):
    """Realestate type per eCH-0129 realestateTypeType.

    XSD: realestateTypeType (restriction of xs:nonNegativeInteger)
    PDF: §4.8.1.5 Grundstücktyp (page 62)
    """
    LIEGENSCHAFT = "1"                     # Liegenschaft
    STOCKWERKSEINHEIT = "2"                # StockwerksEinheit
    GEWOEHNLICHES_MITEIGENTUM = "3"        # Gewöhnliches Miteigentum
    KONZESSION = "4"                       # Konzession
    GEWOEHNLICHES_SDR = "5"                # Gewöhnliches SDR
    BERGWERK = "6"                         # Bergwerk
    QUELLENRECHT = "7"                     # Quellenrecht (Spezialform des gewöhnlichen SDR)
    WEITERE = "8"                          # weitere


class RealestateStatus(str, Enum):
    """Realestate status per eCH-0129 realestateStatusType.

    XSD: realestateStatusType (restriction of xs:nonNegativeInteger)
    PDF: §4.8.1.12 Status (page 64)
    """
    PROJECTED = "0"                        # projektiert
    VALID = "1"                            # gültig DM01:LSNachfuehrung.Gueltigkeit


# ---------------------------------------------------------------------------
# Area (§4.9)
# ---------------------------------------------------------------------------

class AreaType(str, Enum):
    """Area type per eCH-0129 areaTypeType.

    XSD: areaTypeType (restriction of xs:nonNegativeInteger, values 1-3)
    PDF: §4.9.1.1 Flächentyp (page 65-66)
    """
    GROUND_COVER = "1"                     # Bodenbedeckung (AV)
    USAGE_ZONES = "2"                      # Nutzungszonen (Raumplanung)
    OTHER = "3"                            # Weitere (future: Minimale Geodatenmodelle ARE)


class AreaDescriptionCode(str, Enum):
    """Area description code per eCH-0129 areaDescriptionCodeType.

    XSD: areaDescriptionCodeType (restriction of xs:nonNegativeInteger, 0-25)
    PDF: §4.9.1.2 Bezeichnungscode (page 66-67)
    """
    GEBAEUDE = "0"                         # Gebäude
    STRASSE_WEG = "1"                      # Strasse_Weg (befestigt)
    TROTTOIR = "2"                         # Trottoir (befestigt)
    VERKEHRSINSEL = "3"                    # Verkehrsinsel (befestigt)
    BAHN = "4"                             # Bahn (befestigt)
    FLUGPLATZ = "5"                        # Flugplatz (befestigt)
    WASSERBECKEN = "6"                     # Wasserbecken (befestigt)
    UEBRIGE_BEFESTIGTE = "7"               # uebrige_befestigte (befestigt)
    ACKER_WIESE_WEIDE = "8"                # Acker_Wiese_Weide (humusiert)
    REBEN = "9"                            # Reben (humusiert)
    UEBRIGE_INTENSIVKULTUR = "10"          # uebrige_Intensivkultur (humusiert)
    GARTENANLAGE = "11"                    # Gartenanlage (humusiert)
    HOCH_FLACHMOOR = "12"                  # Hoch_Flachmoor (humusiert)
    UEBRIGE_HUMUSIERTE = "13"              # uebrige_humusierte (humusiert)
    STEHENDES_GEWAESSER = "14"             # stehendes Gewaesser (Gewässer)
    FLIESSENDES_GEWAESSER = "15"           # fliessendes Gewaesser (Gewässer)
    SCHILFGUERTEL = "16"                   # Schilfguertel (Gewässer)
    GESCHLOSSENER_WALD = "17"              # geschlossener_Wald (bestockt)
    WYTWEIDE_DICHT = "18"                  # Wytweide_dicht (bestockt)
    WYTWEIDE_OFFEN = "19"                  # Wytweide_offen (bestockt)
    UEBRIGE_BESTOCKTE = "20"               # uebrige_bestockte (bestockt)
    FELS = "21"                            # Fels (vegetationslos)
    GLETSCHER_FIRN = "22"                  # Gletscher_Firn (vegetationslos)
    GEROELL_SAND = "23"                    # Geroell_Sand (vegetationslos)
    ABBAU_DEPONIE = "24"                   # Abbau_Deponie (vegetationslos)
    UEBRIGE_VEGETATIONSLOSE = "25"         # uebrige_vegetationslose (vegetationslos)


# ---------------------------------------------------------------------------
# Insurance / Estimation (§4.13-4.14)
# ---------------------------------------------------------------------------

class UsageCode(str, Enum):
    """Insurance object usage code per eCH-0129 usageCodeType.

    XSD: usageCodeType (restriction of xs:nonNegativeInteger)
    PDF: §4.13.1.6 Nutzungsart (page 73-74, Tabelle 17)
    """
    RESIDENTIAL = "1199"                   # Wohnen
    GASTRONOMY = "1219"                    # Gastronomie
    OFFICE = "1220"                        # Büro
    RETAIL = "1230"                        # Verkauf
    TRANSPORT = "1241"                     # Nachrichten + Verkehr
    GARAGE = "1242"                        # Garage
    STORAGE = "1252"                       # Lager
    INDUSTRY = "1259"                      # Gewerbe und Industrie
    EDUCATION = "1263"                     # Ausbildung
    HEALTH = "1264"                        # Gesundheit
    SPORTS = "1265"                        # Sport
    CULTURE_LEISURE = "1269"               # Kultur und Freizeit
    AGRICULTURE = "1271"                   # Landwirtschaft
    SACRED = "1272"                        # Sakral
    PUBLIC_SPECIAL = "1274"                # öffentliche Spezialbauten


class LocationCode(str, Enum):
    """Insurance location code per eCH-0129 locationCodeType.

    XSD: locationCodeType (restriction of xs:nonNegativeInteger)
    PDF: §4.13.1.8 Lagecode (page 75)
    """
    UNKNOWN = "0"                          # unbekannt
    ISOLATED_GT_25M = "1"                  # vereinzelt stehend > 25m
    DETACHED = "2"                         # freistehend
    DETACHED_LT_25M = "3"                  # freistehend < 25m
    ATTACHED = "4"                         # angebaut
    ATTACHED_WITH_FIREWALL = "5"           # angebaut mit Brandmauer
    ATTACHED_WITHOUT_FIREWALL = "6"        # angebaut ohne Brandmauer


class ChangeReason(str, Enum):
    """Insurance value change reason per eCH-0129 changeReasonType.

    XSD: changeReasonType (restriction of xs:nonNegativeInteger)
    PDF: §4.13.1.9.3 Mutationsgrund (page 76)
    """
    NEW_VALUE = "1001"                     # Festlegung / Änderung Neuwert
    TECHNICAL_DEPRECIATION = "1002"        # Festlegung / Änderung technische Entwertung in %
    TIME_VALUE = "1003"                    # Festlegung / Änderung Zeitwert
    CONSTRUCTION_INCREASE = "1004"         # Festlegung bauliche Wertvermehrung
    INSURANCE_VALUE = "1005"               # Festlegung / Änderung Versicherungswert
    CONSTRUCTION_INSURANCE_SUM = "1006"    # Festlegung / Änderung Bauversicherungssumme


class TypeOfValue(str, Enum):
    """Estimation value type per eCH-0129 typeOfvalueType.

    XSD: typeOfvalueType (restriction of xs:nonNegativeInteger)
    PDF: §4.14.1.7.6 WertTyp (page 80-81)

    Note: XSD element is 'typeOfvalue' (lowercase 'v') — this is the XSD spelling.
    """
    BASIS_VALUE = "1007"                   # Basiswert
    TAX_VALUE = "2001"                     # Steuerwert
    MARKET_VALUE = "2002"                  # Verkehrswert
    PURCHASE_VALUE = "2003"                # Kaufwert
    REAL_VALUE = "2004"                    # Realwert
    IMPUTED_RENTAL = "2005"                # Eigenmietwert
    AGRICULTURAL_RENTAL = "2006"           # Landwirtschaftlicher Mietwert
    CAPITALIZED_EARNINGS = "2007"          # Ertragswert
    RENTAL_THIRD_PARTY = "2008"            # Mietwert für fremdvermietetes Eigentum
    BGBB_ESTIMATION = "2009"               # Schätzungswert BGBB
    PROJECT_ESTIMATION = "2010"            # Projektschätzungswert
    ENCUMBRANCE_LIMIT = "2011"             # Belastungsgrenze
    NEW_VALUE = "2012"                     # Neuwert
    TIME_VALUE = "2013"                    # Zeitwert
    RENTAL_RESIDENTIAL_2008 = "2014"       # Mietertrag Wohnräume fremdvermietet -> Abgleichen 2008
    RENTAL_COMMERCIAL_IMPUTED = "2015"     # Mietertrag Geschäftsräume -> Abgleichen mit Eigenmietwert
    TECHNICAL_DEPRECIATION = "2016"        # technische Entwertung (Prozentsatz Neuwert→Zeitwert)
    RENTAL_SELF_USED_ELSEWHERE = "9000"    # Mietwert selbstgenutzt andernorts
    RENTAL_COMMERCIAL_TURNOVER = "9001"    # Mietertrag Geschäftsräume aus Umsatz
    RENTAL_COMMERCIAL_AREA = "9002"        # Mietertrag Geschäftsräume aus Fläche
    BUILDING_RIGHT_INTEREST = "9003"       # Baurechtszins vom Baurechtnehmer


# ---------------------------------------------------------------------------
# Street / Locality (§4.15-4.16)
# ---------------------------------------------------------------------------

class StreetKind(str, Enum):
    """Street kind per eCH-0129 streetKindType.

    XSD: streetKindType (restriction of xs:nonNegativeInteger)
    PDF: §4.15.1.5 Art der Strasse (page 83)
    """
    STREET = "9801"                        # Strasse (Linienobjekt)
    SQUARE = "9802"                        # Platz (Punktobjekt)
    NAMED_AREA = "9803"                    # Benanntes Gebiet (Flächenobjekt)


class StreetStatus(str, Enum):
    """Street status per eCH-0129 streetStatusType.

    XSD: streetStatusType (restriction of xs:nonNegativeInteger)
    PDF: §4.15.1.6 Realisierungsstand der Strasse (page 84)
    """
    PROJECTED = "9811"                     # projektiert
    CONSTRUCTION_STARTED = "9812"          # baubegonnen
    EXISTING = "9813"                      # bestehend
    CANCELLED = "9814"                     # aufgehoben


class StreetLanguage(str, Enum):
    """Street description language per eCH-0129 streetLanguageType.

    XSD: streetLanguageType (restriction of xs:nonNegativeInteger)
    PDF: §4.15.1.5.1 Sprache (page 83)
    """
    GERMAN = "9901"                        # Deutsch
    ROMANSH = "9902"                       # Rätoromanisch
    FRENCH = "9903"                        # Französisch
    ITALIAN = "9904"                       # Italienisch


class NumberingType(str, Enum):
    """Street numbering type per eCH-0129 numberingType.

    XSD: numberingType (restriction of xs:nonNegativeInteger)
    PDF: not individually described — XSD enum values only
    """
    TYPE_9830 = "9830"
    TYPE_9832 = "9832"
    TYPE_9835 = "9835"
    TYPE_9836 = "9836"
    TYPE_9837 = "9837"
    TYPE_9839 = "9839"


# ---------------------------------------------------------------------------
# Cadastral (§4.17-4.19)
# ---------------------------------------------------------------------------

class PlaceNameType(str, Enum):
    """Place name type per eCH-0129 placeNameTypeType.

    XSD: placeNameTypeType (restriction of xs:nonNegativeInteger)
    PDF: §4.19.1.1 Lagebezeichnungstyp (page 88)
    """
    FLURNAME = "0"                         # Flurname
    ORTSNAME = "1"                         # Ortsname
    LOKALISATIONSNAME = "2"                # Lokalisationsname
    OTHER = "3"                            # anderer Name


class RemarkType(str, Enum):
    """Cadastral surveyor remark type per eCH-0129 remarkTypeType.

    XSD: remarkTypeType (restriction of xs:nonNegativeInteger)
    PDF: §4.18.1.1 Art (page 87)
    """
    DISPUTED_BOUNDARY = "1"                # streitigeGrenze
    SURVEY_POINT = "2"                     # Lagefixpunkt
    CULVERTED_WATER = "3"                  # eingedoltesGewaesser
    NATURAL_MONUMENT = "4"                 # Naturdenkmal
    PERMANENT_GROUND_SHIFT = "5"           # dauernde Bodenverschiebung
    OTHER = "6"                            # andere


# ---------------------------------------------------------------------------
# Contact (§4.22-4.23)
# ---------------------------------------------------------------------------

class PhoneCategory(str, Enum):
    """Phone category per eCH-0129 phoneCategoryType.

    XSD: phoneCategoryType (restriction of xs:integer)
    PDF: §4.23.1.4.1 Kategorie der Telefonnummer (page 96)
    """
    PRIVATE_PHONE = "1"                    # PrivatePhone — private Telefonnummer
    PRIVATE_MOBILE = "2"                   # PrivateMobile — private Mobil-Nummer
    PRIVATE_FAX = "3"                      # PrivateFax — private Fax-Nummer
    PRIVATE_INTERNET_VOICE = "4"           # PrivateInternetVoice — private Internettelefonie-Nummer
    BUSINESS_CENTRAL = "5"                 # BusinessCentral — geschäftliche Nummer (Zentrale)
    BUSINESS_DIRECT = "6"                  # BusinessDirect — geschäftliche Nummer (Durchwahl)
    BUSINESS_MOBILE = "7"                  # BusinessMobile — geschäftliche Mobil-Nummer
    BUSINESS_FAX = "8"                     # BusinessFax — geschäftliche Fax-Nummer
    BUSINESS_INTERNET_VOICE = "9"          # BusinessInternetVoice — geschäftliche Internettelefonie-Nummer
    PAGER = "10"                           # Pager


class EmailCategory(str, Enum):
    """Email category per eCH-0129 emailCategoryType.

    XSD: emailCategoryType (restriction of xs:integer)
    PDF: §4.23.1.3.1 Kategorie der E-Mail-Adresse (page 95)
    """
    PRIVATE = "1"                          # private E-Mail-Adresse
    BUSINESS = "2"                         # geschäftliche E-Mail-Adresse


# ---------------------------------------------------------------------------
# Coordinates (§4.24)
# ---------------------------------------------------------------------------

class OriginOfCoordinates(str, Enum):
    """Origin of coordinates per eCH-0129 originOfCoordinatesType.

    XSD: originOfCoordinatesType (restriction of xs:nonNegativeInteger)
    PDF: §4.24.4.3 Angabe zur Herkunft der Koordinaten (page 100-101)
    """
    OFFICIAL_SURVEY = "901"                # Amtliche Vermessung, DM.01
    DERIVED_FROM_SURVEY = "902"            # Aus amtlicher Vermessung hergeleitet
    SURVEYOR = "903"                       # Angabe Nachführungsgeometer
    BUILDING_APPLICATION = "904"           # Angabe Baugesuch
    BFS = "905"                            # Bundesamt für Statistik (BFS)
    GEOPOST = "906"                        # Datensatz GeoPost
    OTHER = "909"                          # Andere Datenquelle


# ---------------------------------------------------------------------------
# Fiscal Ownership (§4.12) — inline enum, not a named simpleType
# ---------------------------------------------------------------------------

class FiscalRelationship(str, Enum):
    """Fiscal ownership relationship per eCH-0129 fiscalOwnershipType.fiscalRelationship.

    XSD: anonymous restriction inside fiscalOwnershipType (inline enum, values 1-3)
    PDF: §4.12.1.2 Beziehungstyp (page 71)
    """
    OWNER = "1"                            # Eigentümer
    USUFRUCTUARY = "2"                     # Nutzniesser
    RESIDENTIAL_RIGHT = "3"                # Wohnrecht
