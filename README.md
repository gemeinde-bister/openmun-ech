# OpenMun eCH Models Library

A comprehensive Python implementation of Swiss e-government (eCH) standards for municipal administration systems.

## Overview

This library provides Pydantic-based models for various eCH standards used in Swiss e-government communications, with a focus on municipal population registry (Einwohnerregister) data exchange.

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

- **100% Pydantic Validation**: All XML serialization/deserialization through type-safe Pydantic models
- **Zero Data Loss**: Production-tested with real government XML files
- **XSD Compliance**: Full compliance with official eCH XSD schemas
- **Comprehensive Testing**: 456+ passing tests including production data roundtrip validation
- **Namespace Handling**: Proper cross-schema composition with namespace management

## Installation

```bash
pip install -e .
```

## Usage

```python
from openmun_ech.ech0020.v3 import ECH0020Delivery
from openmun_ech.ech0011.v8 import ECH0011Person
import xml.etree.ElementTree as ET

# Parse eCH-0020 delivery
tree = ET.parse('delivery.xml')
root = tree.getroot()
delivery = ECH0020Delivery.from_xml(root)

# Access person data
if hasattr(delivery.event, 'base_delivery'):
    for person in delivery.event.base_delivery.person:
        print(f"Name: {person.name_data.official_name}")
        print(f"VN: {person.identity_card.vn}")

# Export back to XML
exported = delivery.to_xml()
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/ -v
```

Test specific standards:

```bash
pytest tests/test_ech0020_*.py -v
pytest tests/test_ech0099_roundtrip.py -v
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

## License

This library is part of the OpenMun project for Swiss municipal administration.

## Contributing

### Most Needed: Production XML Data

We have validated this library against **19 eCH-0020 event types**, **eCH-0020 and eCH-0099 base deliveries** using 204 production files. However, **many event types remain untested** due to limited access to production data.

**We urgently need:**
- **Validation** using our roundtrip scripts against your live government data
- **Temporary access to production XML files** from your municipality/canton
- **Testing reports** from your environment with error details
- **Bug reports** with anonymized XML samples

### Development Guidelines

When adding new event types or fixing issues:
1. **Always test with production data** - No synthetic test data for government systems
2. **Maintain zero data loss principle** - Perfect roundtrip or fail
3. **Follow existing patterns** for namespace handling (see Architecture section)
4. **Update documentation and test coverage**
5. **Report validation results** - Even successful tests help us track coverage