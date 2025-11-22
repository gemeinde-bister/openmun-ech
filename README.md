# OpenMun eCH Models Library

A Python implementation of Swiss e-government (eCH) standards for municipal administration systems.

## Overview

This library provides Pydantic-based models for eCH standards used in Swiss e-government communications, with a focus on municipal population registry (Einwohnerregister) data exchange.

The library offers two APIs:
- **Layer 2** (Simplified): For creating new eCH-0020 deliveries from application data
- **Layer 1** (XSD-compliant): For parsing and processing production XML files

## Implemented Standards

- **eCH-0006 v2** - Residence Permits (105 enums)
- **eCH-0007 v5** - Municipality (30 models + 13 XSD tests)
- **eCH-0008 v3** - Country (26 models + 17 XSD tests)
- **eCH-0010 v5** - Address (37 models + 17 XSD tests)
- **eCH-0011 v8** - Person Data (77 models + 20 XSD tests)
- **eCH-0020 v3** - Population Registry Events (89 types, 11,220+ lines)
- **eCH-0021 v7** - Person Additional Data (26 models + 32 XSD tests)
- **eCH-0044 v4** - Person Identification (32 models + 10 XSD tests)
- **eCH-0058 v4+v5** - Message Headers (65 models + 13 XSD tests)
- **eCH-0099 v2.1** - Statistics Delivery (33 tests + production roundtrip)

## Features

- **Two-Layer API**: Simplified Layer 2 for creating deliveries, XSD-compliant Layer 1 for parsing
- **Pydantic Validation**: Type-safe serialization and deserialization
- **Zero Data Loss**: Production-tested with real government XML files
- **XSD Compliance**: Full compliance with official eCH XSD schemas
- **Comprehensive Testing**: 700+ tests including production data roundtrip validation
- **Namespace Handling**: Proper cross-schema composition with namespace management
 - **Optional Swiss Data Validation (warnings-only)**: Postal code ↔ town, municipality BFS, canton code, street name, cross-field checks, and religion code audit

## Installation

```bash
pip install -e .
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
    nationality_status="1",              # Swiss
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

See `docs/QUICKSTART.md` for detailed examples and configuration management.

### Optional Swiss Data Validation (warnings-only)

You can request non-blocking validation against Swiss open data and standard code lists:

```python
ctx = person.validate_swiss_data()
if ctx.has_warnings():
    for w in ctx.warnings:
        print(w)
```

Included checks (no exceptions are raised):
- Postal code ↔ town consistency (Swiss postal database)
- Municipality BFS existence
- Canton code validity
- Street name lookup and suggestions (Swiss street directory)
- Cross-field checks (e.g., postal code vs municipality, street vs postal)
- Religion code audit (warns if value not in eCH-0011 code list)

Notes:
- Validation uses in-memory caches and is fast after first load.
- Works even if you pass strings for Layer 2 enum fields; models accept both strings and enum instances.

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
        if hasattr(event, 'base_delivery_person'):
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
- Simplifying integration with LLM-based data processing
- Reducing code complexity (1-2 nesting levels vs 7 levels)

**Use Layer 1 when:**
- Parsing production XML files from other systems
- Processing batch imports from canton/federal registries
- Implementing XML validators or inspection tools
- Accessing all XSD elements including rarely-used fields

Both layers maintain zero data loss and full XSD compliance.

## Testing

Run the complete test suite:

```bash
pytest tests/ -v
```

Test specific standards:

```bash
pytest tests/test_ech0020_*.py -v
pytest tests/test_ech0099_*.py -v
pytest tests/test_layer2*.py -v
```

## Production Validation

The library has been validated against 204 production XML files from Swiss government systems with:
- Zero data loss (perfect element count match)
- 100% roundtrip success rate
- All available 19 eCH-0020 event types validated

## Architecture

### Core Principles

1. **Never bypass Pydantic validation** - All XML operations go through models
2. **Zero tolerance for defaults** - Missing government data must fail, not use fallbacks
3. **Production-first testing** - All models tested with real government data

### Key Patterns

**skip_wrapper Pattern** (XSD TYPE usage):
```python
msg.to_xml(parent=msgs_elem, namespace=namespace, skip_wrapper=True)
```

**wrapper_namespace Pattern** (Cross-schema composition):
```python
self.has_main_residence.to_xml(
    parent=elem,
    namespace=ns_011,              # Content namespace
    element_name='hasMainResidence',
    wrapper_namespace=ns_020        # Wrapper namespace
)
```

## Documentation

- **Quick Start Guide**: `docs/QUICKSTART.md` - Complete walkthrough for Layer 2
- **API Reference**: `docs/API_REFERENCE.md` - Full API documentation
- **Architecture**: `docs/TWO_LAYER_ARCHITECTURE_ROADMAP.md` - Implementation details
- **Validation**: `docs/VALIDATION_LAYER_DESIGN.md` - Optional Swiss data validation

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
