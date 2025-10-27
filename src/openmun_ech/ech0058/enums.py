"""eCH-0058 v4/v5 Standard Code Enumerations.

Official codes defined in eCH-0058 XSD for message headers.
These enums are shared between v4 and v5.

Standard: eCH-0058 v4.0 / v5.0
XSD: eCH-0058-4-0.xsd / eCH-0058-5-0.xsd
Namespace: http://www.ech.ch/xmlns/eCH-0058/4 (v4)
           http://www.ech.ch/xmlns/eCH-0058/5 (v5)
Source: https://www.ech.ch/de/standards/60030
"""

from enum import Enum


class ActionType(str, Enum):
    """Message action type codes per eCH-0058.

    Specifies the action to be performed with the message.
    This enum is identical in both v4 and v5 of eCH-0058.

    XSD: actionType (restriction of xs:string with enumeration)

    Values:
    - 1: Create/Insert (Erstellen/Einfügen)
    - 3: Modify/Update (Ändern/Aktualisieren)
    - 4: Cancel (Annulieren)
    - 5: Close (Schliessen)
    - 6: Reactivate (Reaktivieren)
    - 8: Send (Senden)
    - 9: Change (Wechseln)
    - 10: Confirm (Bestätigen)
    - 12: Request (Anfragen)
    """
    CREATE = "1"              # Erstellen/Einfügen
    MODIFY = "3"              # Ändern/Aktualisieren
    CANCEL = "4"              # Annulieren
    CLOSE = "5"               # Schliessen
    REACTIVATE = "6"          # Reaktivieren
    SEND = "8"                # Senden
    CHANGE = "9"              # Wechseln
    CONFIRM = "10"            # Bestätigen
    REQUEST = "12"            # Anfragen


# Backward compatibility constants
ACTION_CREATE = ActionType.CREATE.value
ACTION_MODIFY = ActionType.MODIFY.value
ACTION_SEND = ActionType.SEND.value
