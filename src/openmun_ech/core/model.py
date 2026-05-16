"""ECHModel base class with declarative XML serialization.

Provides auto-generated to_xml()/from_xml() based on xml_field() metadata.
Eliminates handwritten XML boilerplate while preserving the existing interface
contract used by all Layer 1 classes.

Usage:
    from openmun_ech.core import ECHModel, xml_field, NS

    class ECH0008Country(ECHModel):
        __xml_ns__ = NS.ECH0008_V3
        __xml_element__ = 'country'

        country_id: Optional[str] = xml_field('countryId', default=None)
        country_name_short: str = xml_field('countryNameShort')
"""

import xml.etree.ElementTree as ET
from datetime import date
from enum import Enum
from typing import Any, ClassVar, Optional, Self, get_args, get_origin

from pydantic import BaseModel, ConfigDict

from openmun_ech.core.fields import XmlMeta, get_xml_meta


class ECHModel(BaseModel):
    """Base class for eCH XML models with declarative serialization.

    Subclasses declare:
        __xml_ns__: Default namespace URI for this model's content elements.
        __xml_element__: Default root element name (e.g. 'country', 'nameInfo').

    Fields declared with xml_field() get automatic to_xml()/from_xml() handling.
    """

    __xml_ns__: ClassVar[str]
    __xml_element__: ClassVar[str]

    model_config = ConfigDict(populate_by_name=True)

    def to_xml(
        self,
        parent: Optional[ET.Element] = None,
        namespace: str | None = None,
        element_name: str | None = None,
        wrapper_namespace: str | None = None,
    ) -> ET.Element:
        """Serialize this model to an XML Element.

        Preserves the interface contract of existing Layer 1 classes.

        Args:
            parent: Parent element to attach to. If None, creates standalone element.
            namespace: Namespace for content elements. Defaults to __xml_ns__.
            element_name: Root element name. Defaults to __xml_element__.
            wrapper_namespace: Namespace override for the root element itself
                             (content children still use `namespace`).

        Returns:
            The created XML Element.
        """
        ns = namespace or self.__xml_ns__
        el_name = element_name or self.__xml_element__
        root_ns = wrapper_namespace or ns

        # Create root element
        tag = f'{{{root_ns}}}{el_name}'
        if parent is not None:
            elem = ET.SubElement(parent, tag)
        else:
            elem = ET.Element(tag)

        # Serialize each xml_field in declaration order
        for field_name, field_info in type(self).model_fields.items():
            meta = get_xml_meta(field_info, field_name)
            if meta is None:
                continue

            value = getattr(self, field_name)
            if value is None:
                continue

            if meta.is_list:
                for item in value:
                    _serialize_value(elem, ns, meta, item)
            else:
                _serialize_value(elem, ns, meta, value)

        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element, namespace: str | None = None) -> Self:
        """Deserialize an XML Element into this model.

        Args:
            elem: XML element to parse (the root element of this model).
            namespace: Namespace for element lookups. Defaults to __xml_ns__.

        Returns:
            Instance of this model.

        Raises:
            ValueError: If a required field is missing.
        """
        ns = namespace or cls.__xml_ns__
        kwargs: dict[str, Any] = {}

        for field_name, field_info in cls.model_fields.items():
            meta = get_xml_meta(field_info, field_name)
            if meta is None:
                continue

            field_ns = meta.ns or ns
            field_type = _resolve_field_type(cls, field_name)
            is_required = field_info.is_required()

            if meta.is_list:
                found = elem.findall(f'{{{field_ns}}}{meta.xml_name}')
                if found:
                    kwargs[field_name] = [
                        _deserialize_value(child_elem, meta, field_type, ns)
                        for child_elem in found
                    ]
                elif is_required:
                    raise ValueError(f"Missing required field: {meta.xml_name}")
            else:
                found = elem.find(f'{{{field_ns}}}{meta.xml_name}')
                if found is not None:
                    kwargs[field_name] = _deserialize_value(found, meta, field_type, ns)
                elif is_required:
                    raise ValueError(f"Missing required field: {meta.xml_name}")

        return cls(**kwargs)


def _serialize_value(parent_elem: ET.Element, parent_ns: str, meta: XmlMeta, value: Any) -> None:
    """Serialize a single field value into the parent element."""
    field_ns = meta.ns or parent_ns

    if meta.wrapper:
        # Wrapper pattern: create element in parent namespace,
        # call child.to_xml(namespace=child_ns), move children
        wrapper_elem = ET.SubElement(parent_elem, f'{{{parent_ns}}}{meta.xml_name}')
        assert meta.child_ns is not None, f"wrapper=True requires child_ns for {meta.xml_name}"
        child_content = value.to_xml(namespace=meta.child_ns)
        for child in list(child_content):
            wrapper_elem.append(child)

    elif _is_model_instance(value):
        # Nested model: delegate to its to_xml()
        value.to_xml(parent=parent_elem, namespace=field_ns, element_name=meta.xml_name)

    elif isinstance(value, date):
        sub = ET.SubElement(parent_elem, f'{{{field_ns}}}{meta.xml_name}')
        sub.text = value.isoformat()

    elif isinstance(value, Enum):
        # Enum before str/int — (str, Enum) passes isinstance(v, str) but
        # str() gives "EnumClass.MEMBER" in Python 3.11+, not the value.
        sub = ET.SubElement(parent_elem, f'{{{field_ns}}}{meta.xml_name}')
        sub.text = str(value.value)

    elif isinstance(value, bool):
        sub = ET.SubElement(parent_elem, f'{{{field_ns}}}{meta.xml_name}')
        sub.text = 'true' if value else 'false'

    elif isinstance(value, (str, int, float)):
        sub = ET.SubElement(parent_elem, f'{{{field_ns}}}{meta.xml_name}')
        sub.text = str(value)

    else:
        raise TypeError(
            f"Cannot serialize field {meta.xml_name}: unsupported type {type(value).__name__}"
        )


def _deserialize_value(elem: ET.Element, meta: XmlMeta, field_type: type, parent_ns: str) -> Any:
    """Deserialize a single XML element into a Python value."""
    if meta.wrapper:
        # Wrapper pattern: pass wrapper element to child's from_xml()
        assert meta.child_ns is not None, f"wrapper=True requires child_ns for {meta.xml_name}"
        return field_type.from_xml(elem, namespace=meta.child_ns)

    elif _is_model_type(field_type):
        # Nested model
        field_ns = meta.ns or parent_ns
        return field_type.from_xml(elem, namespace=field_ns)

    elif field_type is date:
        text = elem.text
        if not text:
            raise ValueError(f"Empty text for date field: {meta.xml_name}")
        return date.fromisoformat(text.strip())

    elif isinstance(field_type, type) and issubclass(field_type, Enum):
        text = elem.text
        if not text:
            raise ValueError(f"Empty text for enum field: {meta.xml_name}")
        return field_type(text.strip())

    elif field_type is bool:
        text = elem.text
        if not text:
            raise ValueError(f"Empty text for bool field: {meta.xml_name}")
        return text.strip().lower() in ('true', '1')

    elif field_type is int:
        text = elem.text
        if not text:
            raise ValueError(f"Empty text for int field: {meta.xml_name}")
        return int(text.strip())

    elif field_type is str:
        return elem.text.strip() if elem.text else ''

    else:
        raise TypeError(
            f"Cannot deserialize field {meta.xml_name}: unsupported type {field_type.__name__}"
        )


def _is_model_instance(value: Any) -> bool:
    """Check if value is a Pydantic BaseModel instance with to_xml()."""
    return isinstance(value, BaseModel) and hasattr(value, 'to_xml')


def _is_model_type(typ: type) -> bool:
    """Check if type is a Pydantic BaseModel subclass with from_xml()."""
    try:
        return isinstance(typ, type) and issubclass(typ, BaseModel) and hasattr(typ, 'from_xml')
    except TypeError:
        return False


def _resolve_field_type(cls: type, field_name: str) -> type:
    """Resolve the concrete type of a field, unwrapping Optional[T] and List[T].

    For Optional[str], returns str.
    For List[ECH0011NameData], returns ECH0011NameData.
    For plain str, returns str.
    """
    annotation = cls.__annotations__.get(field_name)
    if annotation is None:
        # Check parent classes
        for parent in cls.__mro__[1:]:
            if field_name in getattr(parent, '__annotations__', {}):
                annotation = parent.__annotations__[field_name]
                break

    if annotation is None:
        raise TypeError(f"Cannot resolve type for field {field_name}")

    return _unwrap_type(annotation)


def _unwrap_type(annotation: Any) -> type:
    """Unwrap Optional[T], list[T], List[T] to get the inner type."""
    origin = get_origin(annotation)

    # Optional[T] = Union[T, None]
    if origin is type(None):
        return type(None)

    args = get_args(annotation)

    # Union types (Optional[T] = Union[T, None])
    if origin is not None and _is_union(origin):
        # Filter out NoneType
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _unwrap_type(non_none[0])
        # Multi-type union — return first non-None (caller handles dispatch)
        return non_none[0] if non_none else type(None)

    # list[T] or List[T]
    if origin is list:
        if args:
            return _unwrap_type(args[0])
        return str  # bare list, shouldn't happen

    # Plain type
    if isinstance(annotation, type):
        return annotation

    # Annotated[T, ...] — unwrap
    if hasattr(annotation, '__metadata__'):
        return _unwrap_type(get_args(annotation)[0])

    return annotation


def _is_union(origin: Any) -> bool:
    """Check if an origin type is a Union."""
    import types
    # Python 3.10+ UnionType (X | Y)
    if isinstance(origin, type) and origin.__name__ == 'UnionType':
        return True
    # typing.Union
    import typing
    try:
        return origin is typing.Union
    except AttributeError:
        return False
