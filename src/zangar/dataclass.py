from __future__ import annotations

import dataclasses
import sys
import types
import typing
from typing import TypeVar, get_args, get_origin

from . import _alias as z
from ._core import Schema, Union
from ._messages import IncompleteMessage

T = TypeVar("T")


def dataclass(cls: type[T], /) -> Schema[T]:
    return Converter().dataclass(cls)


class Proxy:
    def __init__(self, func):
        self.__func = func

    def __getattr__(self, name):
        return getattr(self.__func(), name)


class Converter:

    def __init__(self):
        self._cached: dict[type, Schema | None] = {}

    def dataclass(self, cls: type[T]) -> Schema[T]:
        if cls in self._cached:
            return typing.cast(Schema, Proxy(lambda: self._cached[cls]))
        self._cached[cls] = None

        fields = dataclasses.fields(cls)  # type: ignore
        object_fields = {}
        try:
            hints = typing.get_type_hints(cls)
        except KeyError:
            hints = {}
        for field in fields:
            if "zangar_schema" in field.metadata:
                schema = field.metadata["zangar_schema"]
            else:
                schema = self.resolve_type(hints.get(field.name, field.type))

            f = z.field(schema)
            if (
                field.default is not dataclasses.MISSING
                or field.default_factory is not dataclasses.MISSING
            ):
                f = f.optional()
            object_fields[field.name] = f
        object_schema = z.object(object_fields)
        schema = object_schema.transform(lambda d: cls(**d))
        self._cached[cls] = schema
        return schema

    def resolve_type(self, t) -> Schema:
        if dataclasses.is_dataclass(t):
            return self.dataclass(typing.cast(type, t))

        values = self.resolve_complex_type(t)
        if values is not None:
            schema_cls, args = values
            return schema_cls(*map(self.resolve_type, args))

        if not isinstance(t, type):
            raise NotImplementedError(t, type(t))
        return z.ensure(
            lambda x: isinstance(x, t),
            message=IncompleteMessage(name="type_check", ctx={"expected_type": t}),
        )

    def resolve_complex_type(self, tp):
        origin = get_origin(tp)
        if origin is None:
            return None
        if origin is list:
            return (z.list, get_args(tp))
        if sys.version_info >= (3, 10) and origin is types.UnionType:
            return (Union, get_args(tp))
        if origin is typing.Union:
            return (Union, get_args(tp))
        raise NotImplementedError(tp)
