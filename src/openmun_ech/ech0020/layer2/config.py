"""eCH-0020 Layer 2: Delivery Configuration."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# DELIVERY CONFIGURATION (Phase 2.3: Delivery Construction)
# ============================================================================

class DeliveryConfig(BaseModel):
    """Deployment configuration for creating complete eCH deliveries.

    This configuration contains deployment-level metadata that remains constant
    across all deliveries from a specific application deployment. Values should
    come from configuration files or environment variables, NEVER hardcoded.

    Usage Pattern:
        >>> # Load from config file (user implementation)
        >>> config = DeliveryConfig(
        ...     sender_id="1-6172-1",              # From sedex registration
        ...     manufacturer="OpenMun",            # From application config
        ...     product="Municipality System",    # From application config
        ...     product_version="1.0.0",         # From application version
        ...     test_delivery_flag=True           # From environment (test vs prod)
        ... )
        >>>
        >>> # Use with Layer 2 events to create complete deliveries
        >>> event = BaseDeliveryEvent(...)
        >>> delivery = event.finalize(config)
        >>> delivery.to_file("output.xml")

    Config File Example (YAML):
        deployment:
          sender_id: "1-6172-1"
          manufacturer: "OpenMun"
          product: "Municipality System"
          product_version: "1.0.0"
          test_delivery_flag: true

    Config File Example (TOML):
        [deployment]
        sender_id = "1-6172-1"
        manufacturer = "OpenMun"
        product = "Municipality System"
        product_version = "1.0.0"
        test_delivery_flag = true

    Homogeneous API:
        Same DeliveryConfig works for ALL eCH delivery types:
        - eCH-0020 (Event deliveries): BaseDeliveryEvent.finalize(config)
        - eCH-0099 (Statistics deliveries): StatisticsDelivery.finalize(config)
        - Future eCH types: Same pattern

    Zero-Tolerance Policy:
        Values MUST come from configuration, not hardcoded:
        - ❌ WRONG: DeliveryConfig(manufacturer="OpenMun")  # Hardcoded
        - ✅ RIGHT: DeliveryConfig(**yaml.safe_load(config_file))

    See Also:
        - BaseDeliveryEvent.finalize(): Uses this config to create ECH0020Delivery
        - docs/PHASE_2_3_DELIVERY_CONSTRUCTION_DECISION.md: Design rationale
    """

    # ========== Required Fields (Deployment-Level) ==========
    sender_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Sedex participant ID (format: type-bfs-instance, e.g., '1-6172-1'). "
            "Identifies the sender in the sedex network. Must come from sedex registration."
        )
    )
    manufacturer: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description=(
            "Software manufacturer name (1-30 characters). "
            "Identifies who developed the software. Must come from application configuration."
        )
    )
    product: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description=(
            "Product/software name (1-30 characters). "
            "Identifies the software product. Must come from application configuration."
        )
    )
    product_version: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description=(
            "Product version (1-10 characters, e.g., '1.0.0'). "
            "Identifies the software version. Must come from application version."
        )
    )
    test_delivery_flag: bool = Field(
        ...,
        description=(
            "Test vs production flag. True = test delivery, False = production delivery. "
            "Should come from environment configuration (test/staging/production)."
        )
    )

    # ========== Optional Fields (Deployment-Level) ==========
    message_type_override: Optional[str] = Field(
        None,
        description=(
            "Override message type URI. If None, auto-detected based on delivery type: "
            "eCH-0020 = 'http://www.ech.ch/xmlns/eCH-0020/3', "
            "eCH-0099 = 'http://www.ech.ch/xmlns/eCH-0099/2'. "
            "Only override if using non-standard message types."
        )
    )
    original_sender_id: Optional[str] = Field(
        None,
        description=(
            "Original sender ID for forwarded messages (optional). "
            "Only used if this deployment forwards messages from another system."
        )
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )
