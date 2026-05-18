# OpenMun eCH Models Library

A Python implementation of Swiss e-government (eCH) standards for municipal administration systems.

## Overview

This library provides Pydantic-based models for eCH standards used in Swiss e-government communications, with a focus on municipal population registry (Einwohnerregister) data exchange.

The library offers two APIs:
- **Layer 2** (Simplified): For creating new eCH-0020 deliveries from application data
- **Layer 1** (XSD-compliant): For parsing and processing production XML files

All Layer 1 models use a declarative `ECHModel` base class that derives XML serialization from field metadata, eliminating handwritten `to_xml()`/`from_xml()` boilerplate.

## Implemented Standards

- **eCH-0006 v2** - Residence Permits
- **eCH-0007 v5** - Municipality
- **eCH-0008 v3** - Country
- **eCH-0010 v5** - Postal Address
- **eCH-0011 v8** - Person Data
- **eCH-0020 v3** - Population Registry Events (96 classes)
- **eCH-0021 v7+v8** - Person Additional Data (deduplicated via shared base)
- **eCH-0044 v4** - Person Identification
- **eCH-0058 v4+v5** - Message Headers (deduplicated via shared base)
- **eCH-0099 v2** - Statistics Delivery

824 tests, including production data roundtrip validation.

## Features

- **Declarative XML Framework**: `ECHModel` base class with `xml_field()` metadata — field declarations drive serialization
- **Two-Layer API**: Simplified Layer 2 for creating deliveries, XSD-compliant Layer 1 for parsing
- **Pydantic Validation**: Type-safe models with constraints from XSD and PDF specifications
- **Zero Data Invention**: Missing government data fails with actionable errors, never defaults
- **XSD Compliance**: Verified against official eCH XSD schemas and PDF specifications
- **Multi-Version Support**: eCH-0021 v7/v8 and eCH-0058 v4/v5 share common code via `_shared.py`
- **Namespace Management**: Centralized `NS` constants, human-readable prefixes (`eCH-0011:` not `ns1:`)
- **Optional Swiss Data Validation**: Postal code, municipality BFS, canton, street name checks (warnings-only)

## Installation

```bash
pip install openmun-ech
```

## Quick Start (Layer 2)

For creating new eCH-0020 deliveries from application data:

```python
from datetime import date
from openmun_ech.ech0020 import (
    BaseDeliveryPerson,
    BaseDeliveryEvent,
    DeliveryConfig,
    ResidenceType,
    PlaceType,
)

# 1. Load your deployment configuration (from YAML, environment, etc.)
config = DeliveryConfig(
    sender_id="1-6172-1",              # Your sedex sender ID
    manufacturer="Your Company",
    product="Your Application",
    product_version="1.0.0",
    test_delivery_flag=True,           # Test vs production
)

# 2. Create person data from your database/forms
person = BaseDeliveryPerson(
    local_person_id="12345",
    local_person_id_category="MU.6172",  # Format: MU.{your_bfs_number}
    official_name="Müller",
    first_name="Anna",
    sex="2",
    date_of_birth=date(1985, 3, 15),
    birth_place_type=PlaceType.SWISS,
    birth_municipality_bfs="261",        # Zürich
    birth_municipality_name="Zürich",
    religion="111",                      # Roman Catholic
    marital_status="1",                  # Unmarried
    nationality_status="2",              # Known (Swiss citizenship indicated by places_of_origin)
    data_lock="0",                       # No lock
    places_of_origin=[{"bfs_code": "6172", "name": "Bister", "canton": "VS"}],
)

# 3. Create delivery event
event = BaseDeliveryEvent(
    person=person,
    residence_type=ResidenceType.MAIN,
    reporting_municipality_bfs="6172",       # Your municipality
    reporting_municipality_name="Bister",
    arrival_date=date(2025, 1, 15),
    dwelling_address={"town": "Bister", "swiss_zip_code": 3983, "type_of_household": "1"},
)

# 4. Finalize and export
delivery = event.finalize(config)
delivery.to_file("output.xml")
```

### Batch finalize (multi-person exports)

- eCH-0020 baseDelivery (many persons in one message):

```python
from openmun_ech.finalize import finalize_0020_base

events = [event1, event2, event3]
delivery = finalize_0020_base(events, config)
delivery.to_file("base_delivery.xml")
```

Note: For eCH-0020 you cannot mix different single event kinds (e.g., moveIn + moveOut) in one delivery; multi-message is only for baseDelivery.

- eCH-0099 statistics (many reported persons in one message):

```python
from openmun_ech.finalize import finalize_0099

delivery = finalize_0099([rp1, rp2], config)
delivery.to_file("statpop.xml")
```

### Optional Swiss Data Validation (warnings-only)

```python
ctx = person.validate_swiss_data()
if ctx.has_warnings():
    for w in ctx.warnings:
        print(w)
```

Included checks (no exceptions are raised):
- Postal code / town consistency (Swiss postal database)
- Municipality BFS existence
- Canton code validity
- Street name lookup and suggestions (Swiss street directory)
- Cross-field checks (e.g., postal code vs municipality, street vs postal)
- Religion code audit (warns if value not in eCH-0011 code list)

## Production XML Parsing (Layer 1)

For parsing and processing existing XML files from production systems:

```python
from openmun_ech.ech0020.v3 import ECH0020Delivery

# Parse XML file
delivery = ECH0020Delivery.from_file("delivery.xml")

# Access delivery metadata
print(f"Sender: {delivery.delivery_header.sender_id}")
print(f"Message Type: {delivery.delivery_header.message_type}")

# Handle different event types
if isinstance(delivery.event, list):
    # baseDelivery or keyExchange (list of events)
    for event in delivery.event:
        person = event.base_delivery_person
        if person.person_identification:
            print(f"Name: {person.person_identification.official_name}")
            print(f"VN: {person.person_identification.vn}")
else:
    # Other event types (single event)
    print(f"Event type: {type(delivery.event).__name__}")

# Export back to XML
delivery.to_file("output.xml")
```

## When to Use Layer 2 vs Layer 1

**Use Layer 2 when:**
- Creating new eCH deliveries from application data
- Constructing events from database records or user input
- Reducing code complexity (1-2 nesting levels vs 7 levels)

**Use Layer 1 when:**
- Parsing production XML files from other systems
- Processing batch imports from canton/federal registries
- Implementing XML validators or inspection tools
- Accessing all XSD elements including rarely-used fields

Both layers maintain zero data loss and full XSD compliance.

## Architecture

### Core Framework (`openmun_ech.core`)

The library uses a declarative XML framework where field metadata drives serialization:

```python
from openmun_ech.core import ECHModel, xml_field, NS

class ECH0008Country(ECHModel):
    __xml_ns__ = NS.ECH0008_V3
    __xml_element__ = 'country'

    country_id: Optional[str] = xml_field('countryId', default=None)
    country_name_short: str = xml_field('countryNameShort')
```

`ECHModel` provides generic `to_xml()` and `from_xml()` derived from field declarations. Classes only override these for complex patterns (choice types, cross-namespace wrappers).

Key components:
- **`NS`** — centralized namespace URI constants for all standards and versions
- **`xml_field()`** — Pydantic Field with XML metadata (element name, namespace, wrapper pattern)
- **`ECHModel`** — base class with declarative serialization/deserialization

### Multi-Version Deduplication

Standards with multiple versions (eCH-0021 v7/v8, eCH-0058 v4/v5) use a `_shared.py` module containing factory functions for structurally identical classes. Version-specific files define only the deltas.

### Design Principles

1. **Zero tolerance for defaults** — Missing government data must fail with actionable errors, never use fallbacks
2. **Serialization purity** — `to_xml()` is a pure function: no I/O, no XSD validation, no side effects
3. **PDF is authoritative** — The PDF specification defines the standard; the XSD is a technical aide

## Testing

Run the complete test suite:

```bash
pytest tests/ -v
```

Test specific standards:

```bash
pytest tests/test_ech0010_*.py -v   # Address models
pytest tests/test_ech0020_*.py -v   # Population registry
pytest tests/test_layer2*.py -v     # Layer 2 API
```

## Production Validation

The library has been validated against 204 production XML files from Swiss government systems with:
- Zero data loss (perfect element count match)
- 100% roundtrip success rate
- All available 19 eCH-0020 event types validated

## License

This library is part of the OpenMun project for Swiss municipal administration.

## Contributing

### Most Needed: Production XML Data

We have validated this library against 19 eCH-0020 event types using 204 production files. However, many event types remain untested due to limited access to production data.

**We need:**
- Validation using our roundtrip scripts against your live government data
- Temporary access to production XML files from your municipality/canton
- Testing reports from your environment with error details
- Bug reports with anonymized XML samples

### Development Guidelines

When adding new event types or fixing issues:
1. **Always test with production data** - No synthetic test data for government systems
2. **Maintain zero data loss principle** - Perfect roundtrip or fail
3. **Follow existing patterns** for namespace handling (see Architecture section)
4. **Update documentation and test coverage**
5. **Report validation results** - Even successful tests help us track coverage
