"""XML field descriptor for ECHModel.

Provides xml_field() which creates Pydantic FieldInfo with XML serialization
metadata attached. The metadata controls how ECHModel's generic to_xml()/from_xml()
handle each field.

Usage:
    from openmun_ech.core import ECHModel, xml_field, NS

    class MyModel(ECHModel):
        __xml_ns__ = NS.ECH0008_V3
        __xml_element__ = 'country'

        country_name: str = xml_field('countryNameShort')
        country_id: Optional[str] = xml_field('countryId', default=None)
"""

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


@dataclass(frozen=True, slots=True)
class XmlMeta:
    """XML serialization metadata for a single field.

    Stored in FieldInfo.json_schema_extra['__xml_meta__'] and read by
    ECHModel's to_xml()/from_xml() to dispatch serialization.
    """

    xml_name: str
    """camelCase element name in XML output."""

    ns: str | None = None
    """Namespace override for this element. If None, uses parent model's namespace."""

    child_ns: str | None = None
    """Namespace the child model uses for its content. Only meaningful with wrapper=True."""

    wrapper: bool = False
    """Wrapper pattern: create element in parent namespace, call child.to_xml(namespace=child_ns),
    move resulting children into the wrapper element."""

    is_list: bool = False
    """Serialize as repeated elements (one per list item)."""


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase.

    Examples:
        country_name_short -> countryNameShort
        country_id_iso2 -> countryIdIso2
        name_valid_from -> nameValidFrom
    """
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def xml_field(
    xml_name: str | None = None,
    *,
    ns: str | None = None,
    child_ns: str | None = None,
    wrapper: bool = False,
    is_list: bool = False,
    # Pydantic Field pass-through
    default: Any = PydanticUndefined,
    default_factory: Callable | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    description: str | None = None,
    **field_kwargs: Any,
) -> FieldInfo:
    """Create a Pydantic Field with XML serialization metadata.

    Args:
        xml_name: camelCase element name in XML. If None, auto-derived from
                  Python field name via snake_to_camel conversion.
        ns: Namespace override for this element.
        child_ns: Namespace for child model content (only with wrapper=True).
        wrapper: Enable wrapper pattern for cross-namespace composition.
        is_list: Field is List[T], serialize each item separately.
        default: Default value (pass-through to Pydantic Field).
        default_factory: Default factory (pass-through to Pydantic Field).
        min_length: String min length constraint.
        max_length: String max length constraint.
        description: Field description.
        **field_kwargs: Additional Pydantic Field kwargs.

    Returns:
        Pydantic FieldInfo with __xml_meta__ in json_schema_extra.
    """
    # xml_name=None is a sentinel — actual resolution happens in ECHModel._xml_fields()
    # using the Python field name. We store None here and resolve later.
    meta = XmlMeta(
        xml_name=xml_name or '',  # empty string = needs resolution
        ns=ns,
        child_ns=child_ns,
        wrapper=wrapper,
        is_list=is_list,
    )

    # Build Pydantic Field kwargs
    kwargs: dict[str, Any] = {}
    if default is not PydanticUndefined:
        kwargs['default'] = default
    if default_factory is not None:
        kwargs['default_factory'] = default_factory
    if min_length is not None:
        kwargs['min_length'] = min_length
    if max_length is not None:
        kwargs['max_length'] = max_length
    if description is not None:
        kwargs['description'] = description
    kwargs.update(field_kwargs)

    # Store XmlMeta in json_schema_extra
    kwargs['json_schema_extra'] = {'__xml_meta__': meta}

    return Field(**kwargs)


def get_xml_meta(field_info: FieldInfo, field_name: str) -> XmlMeta | None:
    """Extract XmlMeta from a Pydantic FieldInfo.

    Args:
        field_info: The Pydantic field info object.
        field_name: Python attribute name (for auto-deriving xml_name).

    Returns:
        XmlMeta with resolved xml_name, or None if field has no XML metadata.
    """
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return None

    meta = extra.get('__xml_meta__')
    if not isinstance(meta, XmlMeta):
        return None

    # Resolve empty xml_name from Python field name
    if not meta.xml_name:
        return XmlMeta(
            xml_name=_snake_to_camel(field_name),
            ns=meta.ns,
            child_ns=meta.child_ns,
            wrapper=meta.wrapper,
            is_list=meta.is_list,
        )

    return meta
