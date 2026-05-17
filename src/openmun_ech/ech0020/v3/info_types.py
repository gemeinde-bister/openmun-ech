"""eCH-0020 v3.0 — Info Types."""

import xml.etree.ElementTree as ET
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from openmun_ech.core import NS
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

class ECH0020NameInfo(BaseModel):
    """Name data with optional validation date.

    Wrapper around eCH-0011 nameData adding an optional nameValidFrom field.

    XSD: nameInfoType (eCH-0020-3-0.xsd lines 31-36)
    PDF: N/A (simple wrapper type, not documented separately)
    """

    name_data: ECH0011NameData = Field(
        ...,
        description="Name data per eCH-0011"
    )

    name_valid_from: Optional[date] = Field(
        None,
        alias='nameValidFrom',
        description="Date from which name is valid"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'nameInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # nameData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        name_wrapper = ET.SubElement(elem, f'{{{namespace}}}nameData')
        # Generate eCH-0011 content and move children to wrapper
        name_content = self.name_data.to_xml(namespace=NS.ECH0011_V8)
        for child in name_content:
            name_wrapper.append(child)

        # nameValidFrom (optional)
        if self.name_valid_from:
            valid_from_elem = ET.SubElement(elem, f'{{{namespace}}}nameValidFrom')
            valid_from_elem.text = self.name_valid_from.isoformat()

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020NameInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0011 = {'eCH-0011': NS.ECH0011_V8}

        # nameData (required, wrapper in eCH-0020, content in eCH-0011)
        name_data_elem = element.find('eCH-0020:nameData', ns_0020)
        if name_data_elem is None:
            raise ValueError("nameData is required in nameInfoType")
        name_data = ECH0011NameData.from_xml(name_data_elem)

        # nameValidFrom (optional)
        valid_from_elem = element.find('eCH-0020:nameValidFrom', ns_0020)
        name_valid_from = None
        if valid_from_elem is not None and valid_from_elem.text:
            name_valid_from = date.fromisoformat(valid_from_elem.text)

        return cls(
            name_data=name_data,
            name_valid_from=name_valid_from
        )


class ECH0020BirthInfo(BaseModel):
    """Birth data with optional addon data.

    Wrapper around eCH-0011 birthData with optional eCH-0021 birthAddonData
    (contains names of parents).

    XSD: birthInfoType (eCH-0020-3-0.xsd lines 43-48)
    PDF: N/A (simple wrapper type)
    """

    birth_data: ECH0011BirthData = Field(
        ...,
        description="Birth data per eCH-0011"
    )

    birth_addon_data: Optional[ECH0021BirthAddonData] = Field(
        None,
        alias='birthAddonData',
        description="Birth addon data per eCH-0021 v7 (parent names)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'birthInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # birthData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        birth_wrapper = ET.SubElement(elem, f'{{{namespace}}}birthData')
        # Generate eCH-0011 content and move children to wrapper
        birth_content = self.birth_data.to_xml(namespace=NS.ECH0011_V8)
        for child in birth_content:
            birth_wrapper.append(child)

        # birthAddonData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.birth_addon_data:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}birthAddonData')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.birth_addon_data.to_xml(namespace=NS.ECH0021_V7)
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020BirthInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0021 = {'eCH-0021': NS.ECH0021_V7}

        # birthData (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        birth_data_elem = element.find('eCH-0020:birthData', ns_0020)
        if birth_data_elem is None:
            raise ValueError("birthData is required in birthInfoType")
        birth_data = ECH0011BirthData.from_xml(birth_data_elem)

        # birthAddonData (optional, wrapper in eCH-0020, content in eCH-0021)
        birth_addon_elem = element.find('eCH-0020:birthAddonData', ns_0020)
        birth_addon_data = None
        if birth_addon_elem is not None:
            birth_addon_data = ECH0021BirthAddonData.from_xml(birth_addon_elem)

        return cls(
            birth_data=birth_data,
            birth_addon_data=birth_addon_data
        )


class ECH0020MaritalInfo(BaseModel):
    """Marital data with optional addon data.

    Wrapper around eCH-0011 maritalData with optional eCH-0021 maritalDataAddon
    (contains place of marriage and other details).

    XSD: maritalInfoType (eCH-0020-3-0.xsd lines 49-54)
    PDF: N/A (simple wrapper type)
    """

    marital_data: ECH0011MaritalData = Field(
        ...,
        description="Marital data per eCH-0011"
    )

    marital_data_addon: Optional[ECH0021MaritalDataAddon] = Field(
        None,
        alias='maritalDataAddon',
        description="Marital data addon per eCH-0021 v7 (place of marriage)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'maritalInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # maritalData (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        marital_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalData')
        # Generate eCH-0011 content and move children to wrapper
        marital_content = self.marital_data.to_xml(namespace=NS.ECH0011_V8)
        for child in marital_content:
            marital_wrapper.append(child)

        # maritalDataAddon (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.marital_data_addon:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalDataAddon')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.marital_data_addon.to_xml(namespace=NS.ECH0021_V7)
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020MaritalInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0021 = {'eCH-0021': NS.ECH0021_V7}

        # maritalData (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        marital_data_elem = element.find('eCH-0020:maritalData', ns_0020)
        if marital_data_elem is None:
            raise ValueError("maritalData is required in maritalInfoType")
        marital_data = ECH0011MaritalData.from_xml(marital_data_elem)

        # maritalDataAddon (optional, wrapper in eCH-0020, content in eCH-0021)
        marital_addon_elem = element.find('eCH-0020:maritalDataAddon', ns_0020)
        marital_data_addon = None
        if marital_addon_elem is not None:
            marital_data_addon = ECH0021MaritalDataAddon.from_xml(marital_addon_elem)

        return cls(
            marital_data=marital_data,
            marital_data_addon=marital_data_addon
        )


class ECH0020MaritalInfoRestrictedMarriage(BaseModel):
    """Restricted marital info (for marriage/partnership data).

    Contains a restricted inline maritalData structure (status + date only)
    plus optional maritalDataAddon from eCH-0021 v7.

    XSD: maritalInfoRestrictedMarriageType (eCH-0020-3-0.xsd lines 55-67)
    PDF: N/A (inline type definition)

    Note: This differs from maritalInfoType by using a restricted inline
    maritalData structure instead of the full eCH-0011 maritalDataType.
    """

    marital_status: MaritalStatus = Field(
        ...,
        alias='maritalStatus',
        description="Marital status code per eCH-0011"
    )

    date_of_marital_status: Optional[date] = Field(
        None,
        alias='dateOfMaritalStatus',
        description="Date when marital status became effective"
    )

    marital_data_addon: Optional[ECH0021MaritalDataAddon] = Field(
        None,
        alias='maritalDataAddon',
        description="Marital data addon per eCH-0021 v7 (place of marriage)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'maritalInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # maritalData (inline complexType, required)
        marital_data_elem = ET.SubElement(elem, f'{{{namespace}}}maritalData')

        # maritalStatus (required)
        status_elem = ET.SubElement(marital_data_elem, f'{{{namespace}}}maritalStatus')
        status_elem.text = self.marital_status.value

        # dateOfMaritalStatus (optional)
        if self.date_of_marital_status:
            date_elem = ET.SubElement(marital_data_elem, f'{{{namespace}}}dateOfMaritalStatus')
            date_elem.text = self.date_of_marital_status.isoformat()

        # maritalDataAddon (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.marital_data_addon:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}maritalDataAddon')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.marital_data_addon.to_xml(namespace=NS.ECH0021_V7)
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020MaritalInfoRestrictedMarriage':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0021 = {'eCH-0021': NS.ECH0021_V7}

        # maritalData (inline complexType, required)
        marital_data_elem = element.find('eCH-0020:maritalData', ns_0020)
        if marital_data_elem is None:
            raise ValueError("maritalData is required in maritalInfoRestrictedMarriageType")

        # maritalStatus (required)
        status_elem = marital_data_elem.find('eCH-0020:maritalStatus', ns_0020)
        if status_elem is None:
            raise ValueError("maritalStatus is required in maritalData")
        marital_status = MaritalStatus(status_elem.text)

        # dateOfMaritalStatus (optional)
        date_elem = marital_data_elem.find('eCH-0020:dateOfMaritalStatus', ns_0020)
        date_of_marital_status = None
        if date_elem is not None and date_elem.text:
            date_of_marital_status = date.fromisoformat(date_elem.text)

        # maritalDataAddon (optional, wrapper in eCH-0020, content in eCH-0021)
        marital_addon_elem = element.find('eCH-0020:maritalDataAddon', ns_0020)
        marital_data_addon = None
        if marital_addon_elem is not None:
            marital_data_addon = ECH0021MaritalDataAddon.from_xml(marital_addon_elem)

        return cls(
            marital_status=marital_status,
            date_of_marital_status=date_of_marital_status,
            marital_data_addon=marital_data_addon
        )


class ECH0020PlaceOfOriginInfo(BaseModel):
    """Place of origin data with optional addon data.

    Wrapper around eCH-0011 placeOfOrigin with optional eCH-0021 placeOfOriginAddonData
    (contains naturalization and expatriation dates).

    XSD: placeOfOriginInfoType (eCH-0020-3-0.xsd lines 68-73)
    PDF: N/A (simple wrapper type)
    """

    place_of_origin: ECH0011PlaceOfOrigin = Field(
        ...,
        alias='placeOfOrigin',
        description="Place of origin per eCH-0011"
    )

    place_of_origin_addon_data: Optional[ECH0021PlaceOfOriginAddonData] = Field(
        None,
        alias='placeOfOriginAddonData',
        description="Place of origin addon per eCH-0021 v7 (naturalization/expatriation dates)"
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str = NS.ECH0020_V3,
        element_name: str = 'placeOfOriginInfo'
    ) -> ET.Element:
        """Export to eCH-0020 v3 XML."""
        if parent is not None:
            elem = ET.SubElement(parent, f'{{{namespace}}}{element_name}')
        else:
            elem = ET.Element(f'{{{namespace}}}{element_name}')

        # placeOfOrigin (required) - wrapper in eCH-0020, content from eCH-0011
        # Create wrapper element in eCH-0020 namespace
        origin_wrapper = ET.SubElement(elem, f'{{{namespace}}}placeOfOrigin')
        # Generate eCH-0011 content and move children to wrapper
        origin_content = self.place_of_origin.to_xml(namespace=NS.ECH0011_V8)
        for child in origin_content:
            origin_wrapper.append(child)

        # placeOfOriginAddonData (optional) - wrapper in eCH-0020, content from eCH-0021
        if self.place_of_origin_addon_data:
            # Create wrapper element in eCH-0020 namespace
            addon_wrapper = ET.SubElement(elem, f'{{{namespace}}}placeOfOriginAddonData')
            # Generate eCH-0021 content and move children to wrapper
            addon_content = self.place_of_origin_addon_data.to_xml(namespace=NS.ECH0021_V7)
            for child in addon_content:
                addon_wrapper.append(child)

        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'ECH0020PlaceOfOriginInfo':
        """Import from eCH-0020 v3 XML."""
        ns_0020 = {'eCH-0020': NS.ECH0020_V3}
        ns_0021 = {'eCH-0021': NS.ECH0021_V7}

        # placeOfOrigin (required, wrapper element in eCH-0020 namespace, content in eCH-0011)
        place_of_origin_elem = element.find('eCH-0020:placeOfOrigin', ns_0020)
        if place_of_origin_elem is None:
            raise ValueError("placeOfOrigin is required in placeOfOriginInfoType")
        place_of_origin = ECH0011PlaceOfOrigin.from_xml(place_of_origin_elem)

        # placeOfOriginAddonData (optional, wrapper in eCH-0020, content in eCH-0021)
        place_addon_elem = element.find('eCH-0020:placeOfOriginAddonData', ns_0020)
        place_of_origin_addon_data = None
        if place_addon_elem is not None:
            place_of_origin_addon_data = ECH0021PlaceOfOriginAddonData.from_xml(place_addon_elem)

        return cls(
            place_of_origin=place_of_origin,
            place_of_origin_addon_data=place_of_origin_addon_data
        )


# ============================================================================
