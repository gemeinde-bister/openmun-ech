"""eCH-0020 v3.0 — Info Types."""

import xml.etree.ElementTree as ET
from typing import Optional, Self
from datetime import date

from openmun_ech.core import ECHModel, NS, xml_field
from openmun_ech.ech0011 import (
    ECH0011NameData,
    ECH0011BirthData,
    ECH0011MaritalData,
    ECH0011PlaceOfOrigin,
    MaritalStatus,
)
from openmun_ech.ech0021.v7 import (
    ECH0021PlaceOfOriginAddonData,
    ECH0021MaritalDataAddon,
    ECH0021BirthAddonData,
)


# ============================================================================
# INFO/WRAPPER TYPES (Wrapper types for validation dates and additional data)
# ============================================================================

class ECH0020NameInfo(ECHModel):
    """Name data with optional validation date.

    XSD: nameInfoType (eCH-0020-3-0.xsd lines 31-36)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'nameInfo'

    name_data: ECH0011NameData = xml_field(
        'nameData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    name_valid_from: Optional[date] = xml_field(
        'nameValidFrom', default=None,
    )


class ECH0020BirthInfo(ECHModel):
    """Birth data with optional addon data.

    XSD: birthInfoType (eCH-0020-3-0.xsd lines 43-48)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'birthInfo'

    birth_data: ECH0011BirthData = xml_field(
        'birthData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    birth_addon_data: Optional[ECH0021BirthAddonData] = xml_field(
        'birthAddonData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020MaritalInfo(ECHModel):
    """Marital data with optional addon data.

    XSD: maritalInfoType (eCH-0020-3-0.xsd lines 49-54)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'maritalInfo'

    marital_data: ECH0011MaritalData = xml_field(
        'maritalData', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    marital_data_addon: Optional[ECH0021MaritalDataAddon] = xml_field(
        'maritalDataAddon', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


class ECH0020MaritalInfoRestrictedMarriage(ECHModel):
    """Restricted marital info (for marriage/partnership events).

    Contains a restricted inline maritalData structure (status + date only)
    plus optional maritalDataAddon from eCH-0021 v7.

    XSD: maritalInfoRestrictedMarriageType (eCH-0020-3-0.xsd lines 55-67)

    Note: Custom to_xml/from_xml because maritalData is an inline anonymous
    complexType wrapping two scalar fields — not a separate model.
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'maritalInfo'

    marital_status: MaritalStatus = xml_field('maritalStatus')
    date_of_marital_status: Optional[date] = xml_field(
        'dateOfMaritalStatus', default=None,
    )
    marital_data_addon: Optional[ECH0021MaritalDataAddon] = xml_field(
        'maritalDataAddon', default=None,
    )

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
    ) -> ET.Element:
        """Custom: inline maritalData sub-element wrapping two scalars."""
        ns = namespace or self.__xml_ns__
        el_name = element_name or self.__xml_element__
        root_ns = wrapper_namespace or ns

        tag = f'{{{root_ns}}}{el_name}'
        elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

        # maritalData (inline complexType)
        marital_data_elem = ET.SubElement(elem, f'{{{ns}}}maritalData')
        status_elem = ET.SubElement(marital_data_elem, f'{{{ns}}}maritalStatus')
        status_elem.text = str(self.marital_status.value)
        if self.date_of_marital_status:
            date_elem = ET.SubElement(marital_data_elem, f'{{{ns}}}dateOfMaritalStatus')
            date_elem.text = self.date_of_marital_status.isoformat()

        # maritalDataAddon (wrapper in eCH-0020, content from eCH-0021)
        if self.marital_data_addon:
            addon_wrapper = ET.SubElement(elem, f'{{{ns}}}maritalDataAddon')
            addon_content = self.marital_data_addon.to_xml(namespace=NS.ECH0021_V7)
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
        """Custom: inline maritalData sub-element wrapping two scalars."""
        ns = namespace or cls.__xml_ns__

        # maritalData (inline complexType)
        marital_data_elem = elem.find(f'{{{ns}}}maritalData')
        if marital_data_elem is None:
            raise ValueError("maritalData is required in maritalInfoRestrictedMarriageType")

        status_elem = marital_data_elem.find(f'{{{ns}}}maritalStatus')
        if status_elem is None:
            raise ValueError("maritalStatus is required in maritalData")
        marital_status = MaritalStatus(status_elem.text)

        date_of_marital_status = None
        date_elem = marital_data_elem.find(f'{{{ns}}}dateOfMaritalStatus')
        if date_elem is not None and date_elem.text:
            date_of_marital_status = date.fromisoformat(date_elem.text)

        # maritalDataAddon (wrapper in eCH-0020, content in eCH-0021)
        marital_data_addon = None
        addon_elem = elem.find(f'{{{ns}}}maritalDataAddon')
        if addon_elem is not None:
            marital_data_addon = ECH0021MaritalDataAddon.from_xml(addon_elem)

        return cls(
            marital_status=marital_status,
            date_of_marital_status=date_of_marital_status,
            marital_data_addon=marital_data_addon,
        )


class ECH0020PlaceOfOriginInfo(ECHModel):
    """Place of origin data with optional addon data.

    XSD: placeOfOriginInfoType (eCH-0020-3-0.xsd lines 68-73)
    """

    __xml_ns__ = NS.ECH0020_V3
    __xml_element__ = 'placeOfOriginInfo'

    place_of_origin: ECH0011PlaceOfOrigin = xml_field(
        'placeOfOrigin', wrapper=True, child_ns=NS.ECH0011_V8,
    )
    place_of_origin_addon_data: Optional[ECH0021PlaceOfOriginAddonData] = xml_field(
        'placeOfOriginAddonData', wrapper=True, child_ns=NS.ECH0021_V7, default=None,
    )


# ============================================================================
