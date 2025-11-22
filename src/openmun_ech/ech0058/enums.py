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

    Specifies the action/purpose of the message exchange.
    This enum is identical in both v4 and v5 of eCH-0058.

    Source: eCH-0058 v5.1.0, Kapitel 2.4.1 (pages 11-12)
    XSD: actionType (restriction of xs:string with enumeration)

    Values:
    - 1: New (neu) - First time delivery of data
    - 3: Recall (Widerruf) - Revoke incorrectly delivered message
    - 4: Correction (Korrektur) - Correct already sent but incorrect data
    - 5: Request (Anfrage) - Explicitly request data from sender
    - 6: Response (Antwort) - Send data requested via "5"
    - 8: Negative Report (negative Quittung) - Error response message
    - 9: Positive Report (positive Quittung) - Success/acknowledgment response
    - 10: Forward (Weiterleitung) - Forward data to another recipient
    - 12: Reminder (Mahnung) - Reminder for outstanding deliveries
    """
    NEW = "1"                 # neu (new) - First delivery
    RECALL = "3"              # Widerruf (recall) - Revoke incorrect message
    CORRECTION = "4"          # Korrektur (correction) - Correct sent data
    REQUEST = "5"             # Anfrage (request) - Request data
    RESPONSE = "6"            # Antwort (response) - Response to request
    NEGATIVE_REPORT = "8"     # negative Quittung (negative report) - Error
    POSITIVE_REPORT = "9"     # positive Quittung (positive report) - Success
    FORWARD = "10"            # Weiterleitung (forward) - Forward data
    REMINDER = "12"           # Mahnung (reminder) - Reminder


# Backward compatibility constants
ACTION_CREATE = ActionType.NEW.value  # Old name was CREATE, now NEW
ACTION_NEW = ActionType.NEW.value
