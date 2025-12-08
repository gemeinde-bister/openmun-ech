"""eCH-0020 Population Registry Events - Layer 2 Simplified API.

This module provides a simplified API for creating eCH-0020 deliveries from
application data. Layer 2 flattens the complex XSD structure (7 nesting levels)
into a user-friendly interface while maintaining 100% XSD compliance and zero
data loss.

Architecture:
    Layer 1 (v3.py): XSD-faithful models for parsing production XML
    Layer 2 (models.py): Simplified models for creating deliveries

    Layer 2 → Layer 1 → XML + XSD validation → sedex transmission

When to Use:
    Use Layer 2 when creating new eCH-0020 deliveries from your application
    data (database records, user forms, etc.). Use Layer 1 when parsing
    existing production XML files.

Quick Start:
    Configuration lives in YOUR application, not this library. Create a
    configuration file (YAML, TOML, etc.) with your deployment metadata:

    Example config/production.yaml (in your application):
        deployment:
          sender_id: "1-6172-1"              # Your municipality sedex ID
          manufacturer: "Municipality IT"     # Your organization
          product: "Population Registry"      # Your software name
          product_version: "2.1.5"           # Your software version
          test_delivery_flag: false          # Production environment

    Example usage (in your application):
        import yaml
        from datetime import date
        from openmun_ech.ech0020 import (
            BaseDeliveryPerson,
            BaseDeliveryEvent,
            DeliveryConfig,
            DwellingAddressInfo,
            PlaceType,
            ResidenceType,
        )

        # Load YOUR configuration
        with open("config/production.yaml") as f:
            config_data = yaml.safe_load(f)

        config = DeliveryConfig(**config_data['deployment'])

        # Create person from YOUR database/forms
        person = BaseDeliveryPerson(
            local_person_id="12345",
            local_person_id_category="MU.6172",  # YOUR municipality
            vn="7561234567890",
            official_name="Müller",
            first_name="Hans",
            sex="1",
            date_of_birth=date(1980, 5, 15),
            religion="111",
            marital_status="1",
            nationality_status="1",
            places_of_origin=[{
                'bfs_code': '261',
                'name': 'Zürich',
                'canton': 'ZH'
            }],
            birth_place_type=PlaceType.SWISS,
            birth_municipality_bfs="261",
            birth_municipality_name="Zürich",
            data_lock="0",
            paper_lock="0"
        )

        # Create event
        dwelling = DwellingAddressInfo(
            street="Bahnhofstrasse",
            house_number="1",
            town="Zürich",
            swiss_zip_code=8001,
            type_of_household="1"
        )

        event = BaseDeliveryEvent(
            person=person,
            residence_type=ResidenceType.MAIN,
            reporting_municipality_bfs="261",
            reporting_municipality_name="Zürich",
            arrival_date=date(2024, 1, 1),
            dwelling_address=dwelling
        )

        # Finalize and export with automatic XSD validation
        delivery = event.finalize(config)
        delivery.to_file("output.xml")

Optional Swiss Data Validation:
    The validation module provides warnings for data quality issues using
    official Swiss open data (postal codes, municipalities, streets):

        from openmun_ech.validation import ValidationContext

        # Validate person data (warnings only, never blocks)
        ctx = person.validate_swiss_data()
        if ctx.has_warnings():
            for warning in ctx.warnings:
                print(f"Warning: {warning.message}")
                # Your application decides how to handle warnings

See Also:
    docs/QUICKSTART.md: Complete getting started guide
    docs/API_REFERENCE.md: Full API documentation
    docs/LAYER2_PUBLIC_API_AUDIT.md: API design rationale
    docs/TWO_LAYER_ARCHITECTURE_ROADMAP.md: Implementation status
"""

# Import all Layer 2 models from models.py
from .models import (
    # Main API
    BaseDeliveryPerson,
    BaseDeliveryEvent,
    DeliveryConfig,

    # Supporting models
    PersonIdentification,
    ParentInfo,
    GuardianInfo,
    SecondaryResidenceInfo,
    DwellingAddressInfo,
    DestinationInfo,

    # Enums
    ResidenceType,
    ReportingType,
    PlaceType,
    GuardianType,
    DatePrecision,
)

# Import Layer 1 for advanced users (production XML parsing)
from .v3 import ECH0020Delivery

__all__ = [
    # Main API - Start here for creating deliveries
    "BaseDeliveryPerson",
    "BaseDeliveryEvent",
    "DeliveryConfig",

    # Supporting models - Used by main API
    "PersonIdentification",
    "ParentInfo",
    "GuardianInfo",
    "SecondaryResidenceInfo",
    "DwellingAddressInfo",
    "DestinationInfo",

    # Enums - Type-safe constants
    "ResidenceType",
    "ReportingType",
    "PlaceType",
    "GuardianType",
    "DatePrecision",

    # Layer 1 - For parsing production XML (advanced)
    "ECH0020Delivery",
]
