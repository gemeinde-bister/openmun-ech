"""Minimal field descriptions from official eCH PDFs (German).

Default language is 'de'. If a description is missing, falls back to 'de',
then returns the field key.
"""

from typing import Dict


_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    # eCH-0011
    'typeOfHousehold': {
        'de': 'Haushaltsart',
    },
    'typeOfResidence': {
        'de': 'Art des Meldeverhältnisses.',
    },
    'federalRegister': {
        'de': 'Bundesregister',
    },
    'maritalStatus': {
        'de': 'Zivilstand',
    },
    'separation': {
        'de': 'Trennung',
    },
    'cancelationReason': {
        'de': 'Im Falle der Auflösung einer eingetragenen Partnerschaft ist der Grund für die Auflösung zu führen.',
    },
    'nationalityStatus': {
        'de': 'Status Staatsangehörigkeit',
    },
    'religion': {
        'de': 'Konfessionszugehörigkeit',
    },

    # eCH-0021
    'mrMrs': {
        'de': 'Code, der angibt, welche Anrede in der Adresse zu verwenden ist.',
    },
    'care': {
        'de': 'Angabe ob die Eltern die elterliche Sorge besitzen.',
    },
    'careType': {
        'de': 'Angabe ob die Eltern die elterliche Sorge besitzen.',
    },
    'kindOfEmployment': {
        'de': 'Erwerbsart.',
    },
    'typeOfRelationship': {
        'de': 'Angabe, in welcher Rolle die/der Partnerin/Partner zur Person steht.',
    },

    # eCH-0058
    'action': {
        'de': 'Der Aktionscode gibt den Zweck des Meldungsaustausches für diese spezifische Meldung an (ungeachtet ob die Meldung Bestandteil einer Transaktion ist oder nicht).',
    },
    'actionType': {
        'de': 'Der Aktionscode gibt den Zweck des Meldungsaustausches für diese spezifische Meldung an (ungeachtet ob die Meldung Bestandteil einer Transaktion ist oder nicht).',
    },
}


def get_desc(field: str, lang: str = 'de') -> str:
    per_field = _DESCRIPTIONS.get(field)
    if not per_field:
        return field
    return per_field.get(lang, per_field.get('de', field))


__all__ = ['get_desc']


