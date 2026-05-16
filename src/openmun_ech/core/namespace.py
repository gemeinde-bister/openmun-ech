"""Namespace constants for all eCH standards.

Single source of truth for XML namespace URIs used across the library.
Eliminates inconsistency between literal strings scattered across modules.

Usage:
    from openmun_ech.core import NS

    root = etree.Element(f'{{{NS.ECH0020_V3}}}delivery')
    elem.find('eCH-0011:officialName', NS.PREFIXES)
"""

from xml.etree import ElementTree as ET


class NS:
    """XML namespace URIs for eCH standards.

    Naming: ECH{standard}_{version}, e.g. ECH0020_V3.
    Where a standard has sub-versions in the URI (e.g. eCH-0020-3/3),
    use the ALT_ prefix.
    """

    # eCH-0006: Residence permit codes
    ECH0006_V2 = 'http://www.ech.ch/xmlns/eCH-0006/2'

    # eCH-0007: Municipalities and cantons
    ECH0007_V5 = 'http://www.ech.ch/xmlns/eCH-0007/5'
    ECH0007_V6 = 'http://www.ech.ch/xmlns/eCH-0007/6'

    # eCH-0008: Countries
    ECH0008_V3 = 'http://www.ech.ch/xmlns/eCH-0008/3'

    # eCH-0010: Postal addresses
    ECH0010_V5 = 'http://www.ech.ch/xmlns/eCH-0010/5'
    ECH0010_V6 = 'http://www.ech.ch/xmlns/eCH-0010/6'
    ECH0010_V8 = 'http://www.ech.ch/xmlns/eCH-0010/8'

    # eCH-0011: Person data
    ECH0011_V8 = 'http://www.ech.ch/xmlns/eCH-0011/8'

    # eCH-0020: Population delivery
    ECH0020_V3 = 'http://www.ech.ch/xmlns/eCH-0020/3'
    ECH0020_V5 = 'http://www.ech.ch/xmlns/eCH-0020/5'
    # Alternative namespace forms (found in some schema locations)
    ALT_ECH0020_V3 = 'http://www.ech.ch/xmlns/eCH-0020-3/3'
    ALT_ECH0020_V5 = 'http://www.ech.ch/xmlns/eCH-0020-5/5'

    # eCH-0021: Additional person data
    ECH0021_V7 = 'http://www.ech.ch/xmlns/eCH-0021/7'
    ECH0021_V8 = 'http://www.ech.ch/xmlns/eCH-0021/8'

    # eCH-0044: Person identification
    ECH0044_V4 = 'http://www.ech.ch/xmlns/eCH-0044/4'

    # eCH-0058: Delivery header
    ECH0058_V4 = 'http://www.ech.ch/xmlns/eCH-0058/4'
    ECH0058_V5 = 'http://www.ech.ch/xmlns/eCH-0058/5'

    # eCH-0099: Statistics
    ECH0099_V2 = 'http://www.ech.ch/xmlns/eCH-0099/2'

    # W3C
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'

    # Prefix map for human-readable XML output and find() calls.
    # Keys are the conventional prefixes used in eCH documentation.
    PREFIXES: dict[str, str] = {
        'eCH-0006': ECH0006_V2,
        'eCH-0007': ECH0007_V6,  # Default to latest used version
        'eCH-0008': ECH0008_V3,
        'eCH-0010': ECH0010_V5,  # Default; v6/v8 used explicitly where needed
        'eCH-0011': ECH0011_V8,
        'eCH-0020': ECH0020_V3,
        'eCH-0021': ECH0021_V8,  # Default to latest used version
        'eCH-0044': ECH0044_V4,
        'eCH-0058': ECH0058_V5,  # Default to latest used version
        'eCH-0099': ECH0099_V2,
        'xsi': XSI,
    }


# Register human-readable prefixes for ElementTree output.
# This makes ET.tostring() produce eCH-0020:delivery instead of ns0:delivery.
# Only affects stdlib xml.etree — lxml uses nsmap= per element.
def _register_prefixes() -> None:
    for prefix, uri in NS.PREFIXES.items():
        ET.register_namespace(prefix, uri)
    # Also register versioned variants not in PREFIXES
    ET.register_namespace('eCH-0007-v5', NS.ECH0007_V5)
    ET.register_namespace('eCH-0010-v6', NS.ECH0010_V6)
    ET.register_namespace('eCH-0010-v8', NS.ECH0010_V8)
    ET.register_namespace('eCH-0021-v7', NS.ECH0021_V7)
    ET.register_namespace('eCH-0058-v4', NS.ECH0058_V4)


_register_prefixes()
