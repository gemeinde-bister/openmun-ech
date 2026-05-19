"""eCH-0133 Objektwesen — Domäne Steuern v3.0.

Tax domain messages for Swiss property/building administration.
Defines 4 message types for exchanging tax-relevant property data:
- ownerOrBeneficiary: fiscal ownership changes
- estimation: property valuations
- realestateBaseDelivery: full parcel dump with ownership + valuations
- estimationBaseDelivery: full valuation dump with linked parcels

All types verified field-by-field against:
- XSD: eCH-0133-3-0.xsd (198 lines, 4 named types + 1 root element)
- PDF: STAN_d_DEF_2022-06-14_eCH-0133_V2.1.0_Objektwesen - Domäne Steuern.pdf

Dependencies (all already implemented):
- eCH-0129 v6.0.0: realestateType, fiscalOwnershipType, personIdentificationType,
  areaType, estimationObjectType, buildingOnlyType
- eCH-0007 v6: swissMunicipalityType
- eCH-0058 v5: headerType
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Union

from pydantic import Field, model_validator
from typing_extensions import Self

from openmun_ech.core import ECHModel, xml_field, NS
from openmun_ech.ech0129 import (
    ECH0129Realestate,
    ECH0129FiscalOwnership,
    ECH0129PersonIdentification,
    ECH0129Area,
    ECH0129EstimationObject,
    ECH0129BuildingOnly,
)
from openmun_ech.ech0007.v6 import ECH0007v6SwissMunicipality
from openmun_ech.ech0058.v5 import ECH0058Header


# ============================================================================
# Shared Helper Types
# ============================================================================

class ECH0133FiscalOwnershipInfo(ECHModel):
    """Fiscal ownership with person identification.

    Anonymous inline type appearing identically in 4 places:
    - ownerOrBeneficiaryType (XSD line 38)
    - realestateBaseDeliveryType > realestateInformation (XSD line 87)
    - estimationBaseDeliveryType > realestateInformation (XSD line 130)
    - estimationBaseDeliveryType > buildingInformation > realestateInformation (XSD line 159)

    Structure: fiscalOwnership + personIdentification
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'fiscalOwnershipInformation'

    fiscal_ownership: ECH0129FiscalOwnership = xml_field(
        'fiscalOwnership', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    person_identification: ECH0129PersonIdentification = xml_field(
        'personIdentification', wrapper=True, child_ns=NS.ECH0129_V6,
    )


class ECH0133BuildingInfo(ECHModel):
    """Building with estimation objects.

    Anonymous inline type shared between estimationType (XSD line 60)
    and realestateBaseDeliveryType (XSD line 98).

    Structure: building + estimationObject[0..N]
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'buildingInformation'

    building: ECH0129BuildingOnly = xml_field(
        'building', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    estimation_object: List[ECH0129EstimationObject] = xml_field(
        'estimationObject', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )


# ============================================================================
# §4.2 ownerOrBeneficiary
# ============================================================================

class ECH0133OwnerOrBeneficiary(ECHModel):
    """Steuerrechtliches Eigentum melden — ownerOrBeneficiaryType.

    XSD: ownerOrBeneficiaryType (line 33-48)
    PDF: §4.2, page 8-9

    Reports fiscal ownership changes. Sent by Steuern (ST) to
    Bauverwaltung (BV) and Gebäudeversicherung (GV).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'ownerOrBeneficiary'

    realestate: ECH0129Realestate = xml_field(
        'realestate', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    municipality: ECH0007v6SwissMunicipality = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6,
    )
    fiscal_ownership_information: List[ECH0133FiscalOwnershipInfo] = xml_field(
        'fiscalOwnershipInformation', is_list=True,
    )


# ============================================================================
# §4.3 estimation
# ============================================================================

class ECH0133EstimationRealestateInfo(ECHModel):
    """Realestate info within estimation message.

    Anonymous inline type within estimationType (XSD line 51-72).

    Structure: realestate + municipality + area[] + estimationObject? + buildingInformation[]
    Note: no fiscalOwnershipInformation (unlike RealestateInfo in baseDelivery).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'realestateInfo'

    realestate: ECH0129Realestate = xml_field(
        'realestate', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    municipality: ECH0007v6SwissMunicipality = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6,
    )
    area: List[ECH0129Area] = xml_field(
        'area', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )
    estimation_object: Optional[ECH0129EstimationObject] = xml_field(
        'estimationObject', wrapper=True, child_ns=NS.ECH0129_V6,
        default=None,
    )
    building_information: List[ECH0133BuildingInfo] = xml_field(
        'buildingInformation', is_list=True, default_factory=list,
    )


class ECH0133Estimation(ECHModel):
    """Schätzung — estimationType.

    XSD: estimationType (line 49-75)
    PDF: §4.3, page 10-11

    Reports property valuations. Sent by Schätzungsamt (SA) to
    Steuern (ST) and others.
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'estimation'

    realestate_info: List[ECH0133EstimationRealestateInfo] = xml_field(
        'realestateInfo', is_list=True,
    )


# ============================================================================
# §4.4.1.1 realestateBaseDelivery
# ============================================================================

class ECH0133RealestateInfo(ECHModel):
    """Realestate info within realestateBaseDelivery.

    Anonymous inline type within realestateBaseDeliveryType (XSD line 78-110).

    Structure: realestate + municipality + area[] + fiscalOwnershipInformation[]
               + estimationObject? + buildingInformation[]
    Superset of ECH0133EstimationRealestateInfo (adds fiscalOwnershipInformation).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'realestateInformation'

    realestate: ECH0129Realestate = xml_field(
        'realestate', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    municipality: ECH0007v6SwissMunicipality = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6,
    )
    area: List[ECH0129Area] = xml_field(
        'area', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )
    fiscal_ownership_information: List[ECH0133FiscalOwnershipInfo] = xml_field(
        'fiscalOwnershipInformation', is_list=True, default_factory=list,
    )
    estimation_object: Optional[ECH0129EstimationObject] = xml_field(
        'estimationObject', wrapper=True, child_ns=NS.ECH0129_V6,
        default=None,
    )
    building_information: List[ECH0133BuildingInfo] = xml_field(
        'buildingInformation', is_list=True, default_factory=list,
    )


class ECH0133RealestateBaseDelivery(ECHModel):
    """Gesamtdatenbestand Grundstücke — realestateBaseDeliveryType.

    XSD: realestateBaseDeliveryType (line 76-113)
    PDF: §4.4.1.1, page 12-13

    Full parcel dump with ownership and valuations.
    Sent by Schätzungsamt (SA) to Steuern (ST).

    Note: XSD defines xs:choice between realestateInformation[] and extensions.
    Extensions element skipped (vendor escape hatch, no known production use).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'realestateBaseDelivery'

    realestate_information: List[ECH0133RealestateInfo] = xml_field(
        'realestateInformation', is_list=True,
    )


# ============================================================================
# §4.4.1.2 estimationBaseDelivery
# ============================================================================

class ECH0133EstBaseBldgRealestateInfo(ECHModel):
    """Realestate info nested inside buildingInformation of estimationBaseDelivery.

    Anonymous inline type (XSD line 150-169).
    Leaf type: realestate + municipality + area[] + fiscalOwnershipInformation[]
    No building or estimationObject fields.
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'realestateInformation'

    realestate: ECH0129Realestate = xml_field(
        'realestate', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    municipality: ECH0007v6SwissMunicipality = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6,
    )
    area: List[ECH0129Area] = xml_field(
        'area', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )
    fiscal_ownership_information: List[ECH0133FiscalOwnershipInfo] = xml_field(
        'fiscalOwnershipInformation', is_list=True, default_factory=list,
    )


class ECH0133EstBaseRealestateInfo(ECHModel):
    """Realestate info in estimationBaseDelivery choice branch A.

    Anonymous inline type (XSD line 121-143).
    Like EstBaseBldgRealestateInfo but adds building[] directly
    (not wrapped in buildingInformation).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'realestateInformation'

    realestate: ECH0129Realestate = xml_field(
        'realestate', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    municipality: ECH0007v6SwissMunicipality = xml_field(
        'municipality', wrapper=True, child_ns=NS.ECH0007_V6,
    )
    area: List[ECH0129Area] = xml_field(
        'area', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )
    fiscal_ownership_information: List[ECH0133FiscalOwnershipInfo] = xml_field(
        'fiscalOwnershipInformation', is_list=True, default_factory=list,
    )
    building: List[ECH0129BuildingOnly] = xml_field(
        'building', wrapper=True, child_ns=NS.ECH0129_V6,
        is_list=True, default_factory=list,
    )


class ECH0133EstBaseBuildingInfo(ECHModel):
    """Building info in estimationBaseDelivery choice branch B.

    Anonymous inline type (XSD line 145-175).
    Different from ECH0133BuildingInfo: has realestateInformation[]
    instead of estimationObject[].
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'buildingInformation'

    building: ECH0129BuildingOnly = xml_field(
        'building', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    realestate_information: List[ECH0133EstBaseBldgRealestateInfo] = xml_field(
        'realestateInformation', is_list=True, default_factory=list,
    )


class ECH0133EstimationInfo(ECHModel):
    """Estimation information within estimationBaseDelivery.

    Anonymous inline type (XSD line 116-178).

    Contains an estimationObject (required) plus xs:choice:
    - Branch A: realestateInformation (single, with building[])
    - Branch B: buildingInformation[] (each with realestateInformation[])
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'estimationInformation'

    estimation_object: ECH0129EstimationObject = xml_field(
        'estimationObject', wrapper=True, child_ns=NS.ECH0129_V6,
    )
    realestate_information: Optional[ECH0133EstBaseRealestateInfo] = xml_field(
        'realestateInformation', default=None,
    )
    building_information: List[ECH0133EstBaseBuildingInfo] = xml_field(
        'buildingInformation', is_list=True, default_factory=list,
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one of realestateInformation or buildingInformation."""
        has_realestate = self.realestate_information is not None
        has_building = len(self.building_information) > 0
        if not has_realestate and not has_building:
            raise ValueError(
                "estimationInformation: must set one of "
                "realestateInformation or buildingInformation"
            )
        if has_realestate and has_building:
            raise ValueError(
                "estimationInformation: realestateInformation and "
                "buildingInformation are mutually exclusive (xs:choice)"
            )
        return self


class ECH0133EstimationBaseDelivery(ECHModel):
    """Gesamtdatenbestand Schätzungen — estimationBaseDeliveryType.

    XSD: estimationBaseDeliveryType (line 114-182)
    PDF: §4.4.1.2, page 14-15

    Full valuation dump with linked parcels/buildings.
    Sent by Schätzungsamt (SA) to Steuern (ST).

    Note: XSD defines xs:choice between estimationInformation[] and extensions.
    Extensions element skipped (vendor escape hatch, no known production use).
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'estimationBaseDelivery'

    estimation_information: List[ECH0133EstimationInfo] = xml_field(
        'estimationInformation', is_list=True,
    )


# ============================================================================
# Root Delivery Element
# ============================================================================

class ECH0133Delivery(ECHModel):
    """eCH-0133 Delivery root element.

    XSD: anonymous complexType on <delivery> element (line 183-197)
    PDF: §4, page 5

    Contains eCH-0058 header + xs:choice of 4 message types.
    Custom to_xml/from_xml for header wrapper + message type dispatch.
    """

    __xml_ns__ = NS.ECH0133_V3
    __xml_element__ = 'delivery'

    delivery_header: ECH0058Header = Field(
        ...,
        description="eCH-0058 v5 delivery header",
    )
    owner_or_beneficiary: Optional[ECH0133OwnerOrBeneficiary] = Field(
        default=None,
        description="§4.2 Fiscal ownership message",
    )
    estimation: Optional[ECH0133Estimation] = Field(
        default=None,
        description="§4.3 Valuation message",
    )
    realestate_base_delivery: Optional[ECH0133RealestateBaseDelivery] = Field(
        default=None,
        description="§4.4.1.1 Full parcel dump",
    )
    estimation_base_delivery: Optional[ECH0133EstimationBaseDelivery] = Field(
        default=None,
        description="§4.4.1.2 Full valuation dump",
    )

    @model_validator(mode='after')
    def validate_choice(self) -> Self:
        """Enforce xs:choice: exactly one of the 4 message types."""
        count = sum(v is not None for v in [
            self.owner_or_beneficiary,
            self.estimation,
            self.realestate_base_delivery,
            self.estimation_base_delivery,
        ])
        if count == 0:
            raise ValueError(
                "delivery: must set one of ownerOrBeneficiary, estimation, "
                "realestateBaseDelivery, or estimationBaseDelivery"
            )
        if count > 1:
            raise ValueError(
                "delivery: message types are mutually exclusive (xs:choice), "
                f"but {count} are set"
            )
        return self

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0133_V3,
        element_name: str = 'delivery',
        **_kw,
    ) -> ET.Element:
        """Export to eCH-0133 XML.

        Custom override: deliveryHeader wrapper + message type dispatch.
        """
        if parent is not None:
            root = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            root = ET.Element(f'{{{namespace}}}{element_name}')

        # deliveryHeader — wrapper in eCH-0133 ns, content from eCH-0058
        header_wrapper = ET.SubElement(root, f'{{{namespace}}}deliveryHeader')
        self.delivery_header.to_xml(
            parent=header_wrapper,
            namespace=NS.ECH0058_V5,
            skip_wrapper=True,
        )

        # Serialize whichever message type is set
        if self.owner_or_beneficiary is not None:
            self.owner_or_beneficiary.to_xml(parent=root, namespace=namespace)
        elif self.estimation is not None:
            self.estimation.to_xml(parent=root, namespace=namespace)
        elif self.realestate_base_delivery is not None:
            self.realestate_base_delivery.to_xml(parent=root, namespace=namespace)
        elif self.estimation_base_delivery is not None:
            self.estimation_base_delivery.to_xml(parent=root, namespace=namespace)

        return root

    @classmethod
    def from_xml(
        cls,
        elem: ET.Element,
        namespace: str = NS.ECH0133_V3,
    ) -> 'ECH0133Delivery':
        """Import from eCH-0133 XML."""
        # deliveryHeader (required)
        header_elem = elem.find(f'{{{namespace}}}deliveryHeader')
        if header_elem is None:
            raise ValueError("Missing required deliveryHeader element")
        delivery_header = ECH0058Header.from_xml(
            header_elem, namespace=NS.ECH0058_V5,
        )

        # Dispatch on which message type is present
        owner_or_beneficiary = None
        estimation = None
        realestate_base_delivery = None
        estimation_base_delivery = None

        oob_elem = elem.find(f'{{{namespace}}}ownerOrBeneficiary')
        if oob_elem is not None:
            owner_or_beneficiary = ECH0133OwnerOrBeneficiary.from_xml(
                oob_elem, namespace=namespace,
            )

        est_elem = elem.find(f'{{{namespace}}}estimation')
        if est_elem is not None:
            estimation = ECH0133Estimation.from_xml(
                est_elem, namespace=namespace,
            )

        rbd_elem = elem.find(f'{{{namespace}}}realestateBaseDelivery')
        if rbd_elem is not None:
            realestate_base_delivery = ECH0133RealestateBaseDelivery.from_xml(
                rbd_elem, namespace=namespace,
            )

        ebd_elem = elem.find(f'{{{namespace}}}estimationBaseDelivery')
        if ebd_elem is not None:
            estimation_base_delivery = ECH0133EstimationBaseDelivery.from_xml(
                ebd_elem, namespace=namespace,
            )

        return cls(
            delivery_header=delivery_header,
            owner_or_beneficiary=owner_or_beneficiary,
            estimation=estimation,
            realestate_base_delivery=realestate_base_delivery,
            estimation_base_delivery=estimation_base_delivery,
        )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'ECH0133Delivery':
        """Parse eCH-0133 delivery from XML file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        return cls.from_xml(root)

    def to_file(
        self,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        xml_declaration: bool = True,
        pretty_print: bool = True,
    ) -> None:
        """Write eCH-0133 delivery to XML file."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        root = self.to_xml()
        if pretty_print:
            ET.indent(root, space='  ')
        tree = ET.ElementTree(root)
        tree.write(
            path, encoding=encoding,
            xml_declaration=xml_declaration, method='xml',
        )
