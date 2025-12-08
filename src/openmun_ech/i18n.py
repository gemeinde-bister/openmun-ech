"""Minimal labels for eCH enums (German, from official PDFs).

Default language is 'de'. If a label is missing, falls back to 'de', then
returns the input code.
"""

from enum import Enum
from typing import Any, Dict


_LABELS: Dict[str, Dict[str, Dict[str, str]]] = {
    # eCH-0011
    'TypeOfHousehold': {
        'de': {
            '0': 'Haushaltsart noch nicht zugeteilt',
            '1': 'Privathaushalt',
            '2': 'Kollektivhaushalt',
            '3': 'Sammelhaushalt',
        }
    },
    'TypeOfResidence': {
        'de': {
            '1': 'Hauptwohnsitz',
            '2': 'Nebenwohnsitz',
            '3': 'anderes Meldeverhältnis',
        }
    },
    'FederalRegister': {
        'de': {
            '1': 'INFOSTAR',
            '2': 'Ordipro',
            '3': 'ZEMIS',
        }
    },
    'MaritalStatus': {
        'de': {
            '1': 'ledig',
            '2': 'verheiratet',
            '3': 'verwitwet',
            '4': 'geschieden',
            '5': 'unverheiratet',
            '6': 'in eingetragener Partnerschaft',
            '7': 'aufgelöste Partnerschaft',
            '9': 'unbekannt',
        }
    },
    'SeparationType': {
        'de': {
            '1': 'freiwillig getrennt',
            '2': 'gerichtlich getrennt',
        }
    },
    'PartnershipAbolition': {
        'de': {
            '1': 'Gerichtlich aufgelöste Partnerschaft',
            '2': 'Ungültigerklärung',
            '3': 'Durch Verschollenerklärung',
            '4': 'Durch Tod aufgelöste Partnerschaft',
            '9': 'Unbekannt / Andere Gründe',
        }
    },
    'CancelationReason': {  # alias
        'de': {
            '1': 'Gerichtlich aufgelöste Partnerschaft',
            '2': 'Ungültigerklärung',
            '3': 'Durch Verschollenerklärung',
            '4': 'Durch Tod aufgelöste Partnerschaft',
            '9': 'Unbekannt / Andere Gründe',
        }
    },
    'NationalityStatus': {
        'de': {
            '0': 'Staatsangehörigkeit unbekannt',
            '1': 'Staatenlos',
            '2': 'Staatsangehörigkeit bekannt',
        }
    },
    'Sex': {
        'de': {
            '1': 'männlich',
            '2': 'weiblich',
            '3': 'unbestimmt',
        }
    },
    'ReligionCode': {
        'de': {
            '111': 'evangelisch-reformierte (protestantische) Kirche',
            '121': 'römisch-katholische Kirche',
            '1221': 'christkatholische / altkatholische Kirche',
            '2112': 'israelitische Gemeinschaft / jüdische Glaubensgemeinschaft',
            '2112013': 'Israelitische Cultusgemeinde',
            '2113014': 'Jüdisch Liberale Gemeinde',
            '000': 'Unbekannt',
        }
    },
    # eCH-0021
    'MrMrs': {
        'de': {
            '1': 'Frau',
            '2': 'Herr',
        }
    },
    'CareType': {
        'de': {
            '0': 'Nicht abgeklärt / unbekannt',
            '1': 'Elterliche Sorge',
            '2': 'Gemeinsame elterliche Sorge',
            '3': 'Alleinige elterliche Sorge',
            '4': 'Keine elterliche Sorge',
        }
    },
    'KindOfEmployment': {
        'de': {
            '0': 'Erwerbslos',
            '1': 'Selbstständig',
            '2': 'Unselbstständig',
            '3': 'AHV/IV-Bezüger',
            '4': 'Nichterwerbsperson (Bsp. „Hausfrau“, „Hausmann“, „Studierende“)',
        }
    },
    'TypeOfRelationship': {
        'de': {
            '1': 'ist Ehepartner',
            '2': 'ist Partner in Eingetragener Partnerschaft',
            '3': 'ist Mutter',
            '4': 'ist Vater',
            '5': 'ist Pflegevater',
            '6': 'ist Pflegemutter',
            '7': 'ist Beistand (von verbeiständeter Person)',
            '8': 'ist Beirat (von verbeirateter Person)',
            '9': 'ist Vormund (von bevormundeter minderjähriger Person)',
            '10': 'ist Vorsorgebeauftragter (von Person)',
        }
    },
    # eCH-0058
    'ActionType': {
        'de': {
            '1': 'neu',
            '3': 'Widerruf',
            '4': 'Korrektur',
            '5': 'Anfrage',
            '6': 'Antwort',
            '8': 'negative Quittung',
            '9': 'positive Quittung',
            '10': 'Weiterleitung',
            '12': 'Mahnung',
        }
    },
}


def _normalize_enum_name(enum_or_name: Any) -> str:
    if isinstance(enum_or_name, str):
        return enum_or_name
    if isinstance(enum_or_name, type) and issubclass(enum_or_name, Enum):
        return enum_or_name.__name__
    return type(enum_or_name).__name__


def _normalize_code(code: Any) -> str:
    if isinstance(code, Enum):
        return str(code.value)
    return str(code)


def get_label(enum_or_name: Any, code: Any, lang: str = 'de') -> str:
    """Return the PDF wording for an enum code in the requested language.

    Falls back to German, then returns the code if no label is found.
    """
    enum_name = _normalize_enum_name(enum_or_name)
    code_str = _normalize_code(code)

    per_enum = _LABELS.get(enum_name)
    if not per_enum:
        return code_str

    per_lang = per_enum.get(lang) or per_enum.get('de')
    if not per_lang:
        return code_str

    return per_lang.get(code_str, code_str)


__all__ = ['get_label']


