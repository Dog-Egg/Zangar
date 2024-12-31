from __future__ import annotations

import dataclasses
from typing import TypeVar, get_args, get_origin

from . import _alias as z
from ._core import Schema

T = TypeVar("T")


def dataclass(cls: type[T], /) -> Schema[T]:
    fields = dataclasses.fields(cls)  # type: ignore
    object_fields = {}
    for field in fields:
        if "zangar_schema" in field.metadata:
            schema = field.metadata["zangar_schema"]
        else:
            schema = _resolve_type(field.type)  # type: ignore

        f = z.field(schema)
        if (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING
        ):
            f = f.optional()
        object_fields[field.name] = f
    object_schema = z.object(object_fields)
    return object_schema.transform(lambda d: cls(**d))


def _resolve_type(t: type) -> Schema:
    if dataclasses.is_dataclass(t):
        return dataclass(t)

    origin = get_origin(t)
    if origin is not None:
        if origin is list:
            return z.list(_resolve_type(get_args(t)[0]))

    return z.ensure(
        lambda x: isinstance(x, t),
        message=lambda x: f"Expected {t.__name__}, received {type(x).__name__}",
    )
