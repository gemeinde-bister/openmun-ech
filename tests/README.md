# eCH Models Testing Suite

**Purpose:** Systematic validation of eCH Pydantic models with production data
**Policy:** ZERO TOLERANCE for defaults, fallbacks, or manual XML building

---

## ⚠️ CRITICAL: Zero Tolerance Policy

**This is Swiss government data. Every field affects real people's legal status.**

### Non-Negotiable Rules:

1. **NEVER bypass Pydantic validation**
   - All XML ↔ Pydantic conversion MUST go through model validation
   - NO manual XML building (no `ET.SubElement` without Pydantic)
   - NO "temporary fixes" or shortcuts

2. **NEVER use defaults or fallbacks**
   - Missing required data MUST fail tests
   - Wrong data = wrong legal status = harm to real people
   - Tests must expose data quality issues, not hide them

3. **ALWAYS use proper XSD patterns**
   - `skip_wrapper=True` when XSD uses TYPE instead of element
   - `wrapper_namespace` when wrapper differs from content namespace
   - XSD extension = flatten base type fields into parent

4. **ALWAYS validate roundtrip with zero data loss**
   - Original element count == Exported element count
   - Every field must be preserved exactly
   - Any data loss = FAILURE

5. **ZERO TECHNICAL DEBT: Fix the source, not the symptom**
   - If a type doesn't support `wrapper_namespace` → Fix the type to support it
   - If a type doesn't support `element_name` → Add the parameter
   - NO manual wrapper patterns, NO workarounds, NO TODOs
   - We own all code: Fix issues at root cause in the library
   - Example: ECH0011ContactData was fixed to support `wrapper_namespace` instead of using manual wrappers

### Real-World Impact:

- Wrong address → Legal notices don't reach person
- Wrong permit → Deportation risk
- Wrong birth data → Citizenship issues
- Wrong death data → Estate/pension problems

**When in doubt: STOP. DO NOT GUESS.**

---

## Test Structure

```
tests/
├── README.md                                  # This file
├── ECH0020_EVENT_COVERAGE.md                  # Event type coverage tracking
├── conftest.py                                # Shared fixtures (production data)
├── test_ech0020_base_delivery_roundtrip.py    # ✅ Base delivery tests
├── test_ech0099_roundtrip.py                  # ✅ Statistics delivery tests
├── test_ech0020_movement_events_roundtrip.py  # ✅ moveIn, moveOut, move
├── test_ech0020_correction_events_roundtrip.py # ✅ correctReporting, etc.
├── test_ech0020_life_events_roundtrip.py      # ✅ birth, death, marriage
└── test_ech0020_contact_events_roundtrip.py   # ✅ contact
```

---

## Configuration

### Production Data Path

Tests auto-discover production data from:
1. `OPENMUN_PRODUCTION_DATA` environment variable (if set)
2. `config.yaml` file (see `config.yaml.sample`)

Set custom path:
```bash
export OPENMUN_PRODUCTION_DATA=/path/to/sedex/data
pytest tests/
```

### Skip Behavior

Tests skip gracefully if production data not available (for CI/CD):
```python
def test_something(skip_if_no_production_data):
    # Test skipped if no production data
    pass
```

---

## Running Tests

### Quick Validation (Known-Good Files)

Test with single verified files for fast feedback:
```bash
# eCH-0020 base delivery
pytest tests/private/test_ech0020_base_delivery_roundtrip.py::TestECH0020BaseDeliverySingleFile -v

# eCH-0099 statistics
pytest tests/private/test_ech0099_roundtrip.py::TestECH0099SingleFile -v
```

### Full Validation (All Production Files)

Test with all available production files (requires production data):
```bash
# All base deliveries
pytest tests/private/test_ech0020_base_delivery_roundtrip.py -v

# All eCH-0099 files
pytest tests/private/test_ech0099_roundtrip.py -v
```

### Full Test Suite

```bash
# Public tests (synthetic data only)
pytest tests/ -v

# With coverage
pytest tests/ --cov=openmun_ech --cov-report=html
```

---

## Test Development Workflow

### For Each New Event Type:

**1. Check Production Coverage**
```bash
# See ECH0020_EVENT_COVERAGE.md for event type list
# We have 204 files across 19 event types!
```

**2. Implement from_xml() Method**
- Follow XSD specification exactly
- Use namespace constants
- Handle all optional/required fields
- NO defaults, NO fallbacks

**3. Create Roundtrip Test**
```python
class TestECH0020EventMoveIn:
    """Test moveIn event roundtrip."""

    def test_movein_files_roundtrip(self, ech0020_event_files):
        """Test all moveIn files (20 available)."""
        files = ech0020_event_files('moveIn')

        failures = []
        for xml_file in files:
            # 1. Parse XML
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # 2. Import to Pydantic
            delivery = ECH0020Delivery.from_xml(root)

            # 3. Export back to XML
            exported = delivery.to_xml()

            # 4. Compare (must match exactly)
            match, diffs = compare_element_counts(root, exported)
            if not match:
                failures.append({'file': xml_file.name, 'diffs': diffs})

        # Assert no failures
        assert not failures, f"{len(failures)} files failed"
```

**4. Run Tests & Fix Issues**
```bash
pytest tests/private/test_ech0020_movement_events_roundtrip.py -v
```

**5. Document Results**
Update `ECH0020_EVENT_COVERAGE.md` with status

---

## Common Issues & Solutions

### Issue: Element Count Mismatch

**Symptom:** `addressInformation: 33 → 34 (EXTRA 1)`

**Common Causes:**
1. Creating extra wrapper element (use `wrapper_namespace` parameter)
2. Wrong namespace in from_xml() lookup
3. Missing `skip_wrapper=True` for XSD TYPE usage

**How to Debug:**
```python
# Check wrapper pattern
# WRONG: Creates two wrappers
wrapper = ET.SubElement(parent, 'placeOfEmployer')
address.to_xml(parent=wrapper, ...)

# CORRECT: Use wrapper_namespace
address.to_xml(
    parent=parent,
    namespace='eCH-0010/5',
    element_name='placeOfEmployer',
    wrapper_namespace='eCH-0021/7'
)
```

### Issue: Missing Elements

**Symptom:** `placeOfEmployer: 1 → 0 (MISSING 1)`

**Common Causes:**
1. from_xml() looking in wrong namespace
2. Not importing optional fields
3. Field not being serialized in to_xml()

**How to Debug:**
```python
# Check production XML structure
for poe in root.findall('.//{{eCH-0021/7}}placeOfEmployer'):
    print('Wrapper namespace:', poe.tag)
    for child in poe:
        print('  Child:', child.tag)  # Should be eCH-0010/5
```

### Issue: Pydantic Validation Error

**Symptom:** `ValidationError: field required`

**This is CORRECT behavior!**
- Production data is missing required field
- Test should FAIL to expose data quality issue
- DO NOT add defaults or fallbacks
- Fix data at source or adjust XSD understanding

---

## Success Metrics

### Current Status (2025-10-26 - COMPLETE):

**✅ Validated:**
- eCH-0020 all event types: 100% (204 files, 19 event types)
- eCH-0099 statistics: 100% (production files)

**Progress:**
- 204/204 eCH-0020 files validated (100%)
- 19/19 event types validated (100%)
- Zero data loss across all production files

See `ECH0020_EVENT_COVERAGE.md` for detailed breakdown by event type.

---

## Key Achievements

### 1. Architecture Integrity Maintained

**NO manual XML building anywhere:**
- All serialization through Pydantic models
- skip_wrapper pattern for XSD compliance
- wrapper_namespace for cross-schema composition

### 2. Production Data Validated

**Real government data tested:**
- 39 persons, 4400 elements: Perfect match
- 24 base deliveries: All pass
- Zero defaults used, zero fallbacks applied

### 3. Systematic Approach Established

**Repeatable workflow:**
- Auto-discover production files
- Test all event types systematically
- Document patterns and issues
- Fix issues properly (no shortcuts)

---

## Documentation

**See Also:**
- `ECH0020_EVENT_COVERAGE.md` - Event type tracking and status
- `docs/ECH0020_IMPLEMENTATION_TRACKER.md` - Implementation progress
- `docs/ECH_IMPLEMENTATION_VERIFICATION_WORKFLOW.md` - Zero-tolerance workflow
- `docs/ECH0020_CRITICAL_ISSUE.md` - Architecture lessons learned

---

## Contributing

### When Adding Tests:

1. Follow zero-tolerance policy (no exceptions!)
2. Use shared fixtures from conftest.py
3. Test with ALL available production files
4. Document any XSD ambiguities found
5. Update ECH0020_EVENT_COVERAGE.md

### When Fixing Issues:

1. Understand XSD specification first
2. Fix in Pydantic model (never bypass)
3. Test with production data
4. Document pattern for future reference

---

**Last Updated:** 2025-12-08
**Status:** All 19 eCH-0020 event types validated (100%)
