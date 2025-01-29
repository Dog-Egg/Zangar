from __future__ import annotations

import dataclasses
import datetime
import sys
import types
import typing
from collections.abc import Callable
from typing import TypeVar, get_args, get_origin

from zangar._types import Field

from . import _alias as z
from ._common import empty
from ._core import Schema, SchemaBase, Union
from ._messages import DefaultMessage, get_message
from .exceptions import ValidationError

T = TypeVar("T")


def dataclass(cls: type[T], /) -> SchemaBase[T]:
    return Converter().dataclass(cls)


class Proxy:
    def __init__(self, func):
        self.__func = func

    def __getattr__(self, name):
        return getattr(self.__func(), name)


def _process_ensure_fields(
    schema: SchemaBase[T],
    decorators: list[EnsureFieldsDecorator],
    name_to_alias: dict[str, str],
) -> SchemaBase[T]:
    for decorator in decorators:

        def ensure_func(decorator: EnsureFieldsDecorator):
            def _ensure_func(value):
                if getattr(value, decorator.method_name)():
                    return True
                error = ValidationError(empty)
                for fieldname in decorator.fieldnames:
                    error._set_child(
                        name_to_alias[fieldname],
                        ValidationError(
                            get_message(
                                (
                                    decorator.message
                                    if decorator.message is not None
                                    else DefaultMessage(name="ensure_failed")
                                ),
                                value=value,
                            )
                        ),
                    )
                raise error

            return _ensure_func

        schema = schema.ensure(ensure_func(decorator))
    return schema


TYPE_MAPPING = {
    int: z.int,
    str: z.str,
    float: z.float,
    bool: z.bool,
    datetime.datetime: z.datetime,
}


class Converter:

    def __init__(self):
        self._cached: dict[type, SchemaBase | None] = {}

    def dataclass(self, cls: type[T]) -> SchemaBase[T]:
        if cls in self._cached:
            return typing.cast(Schema, Proxy(lambda: self._cached[cls]))
        self._cached[cls] = None  # None is a placeholder

        dc_fields = dataclasses.fields(cls)  # type: ignore
        object_fields: dict[str, Field] = {}
        try:
            hints = typing.get_type_hints(cls)
        except KeyError:
            hints = {}

        decorators = DecoratorCollector(cls)

        for dc_field in dc_fields:
            if "zangar_schema" in dc_field.metadata:
                object_field = z.field(dc_field.metadata["zangar_schema"])
            else:
                schema = self.resolve_type(hints.get(dc_field.name, dc_field.type))
                if dc_field.name in decorators.field_decorators:
                    decorator = decorators.field_decorators[dc_field.name]
                    schema = getattr(cls, decorator.method_name)(schema)
                    object_field = z.field(schema, alias=decorator.alias)
                else:
                    object_field = z.field(schema)

            default: typing.Any = z.field._empty
            if dc_field.default is not dataclasses.MISSING:
                default = dc_field.default
            elif dc_field.default_factory is not dataclasses.MISSING:
                default = dc_field.default_factory
            if default is not z.field._empty:
                object_field = object_field.optional(default=default)
            object_fields[dc_field.name] = object_field
        object_schema = z.object(object_fields)
        schema = object_schema.transform(lambda d: cls(**d))
        schema = _process_ensure_fields(
            schema,
            decorators.ensure_fields_decorators,
            object_schema._name_to_alias,
        )
        self._cached[cls] = schema
        return schema

    def resolve_type(self, t) -> SchemaBase:
        if dataclasses.is_dataclass(t):
            return self.dataclass(typing.cast(type, t))

        values = self.resolve_complex_type(t)
        if values is not None:
            schema_cls, args = values
            return schema_cls(*map(self.resolve_type, args))

        if not isinstance(t, type):
            raise NotImplementedError(t, type(t))

        if t in TYPE_MAPPING:
            return TYPE_MAPPING[t]()
        return z.ensure(
            lambda x: isinstance(x, t),
            message=DefaultMessage(name="type_check", ctx={"expected_type": t}),
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


class DecoratorCollector:
    def __init__(self, cls):
        self.field_decorators: dict[str, FieldDecorator] = {}
        self.ensure_fields_decorators: list[EnsureFieldsDecorator] = []

        for obj in vars(cls).values():
            decorator = getattr(obj, _DECORATOR_KEY, None)
            if isinstance(decorator, FieldDecorator):
                self.field_decorators[decorator.fieldname] = decorator
            elif isinstance(decorator, EnsureFieldsDecorator):
                self.ensure_fields_decorators.append(decorator)


_DECORATOR_KEY = "zangar_decorator"


class DecoratorBase:
    method_name: str

    def __call__(self, method):
        setattr(method, _DECORATOR_KEY, self)
        try:
            self.method_name = method.__name__
        except AttributeError:
            self.method_name = method.__func__.__name__
        return method


class FieldDecorator(DecoratorBase):
    def __init__(self, fieldname, /, alias: str | None = None):
        self.fieldname = fieldname
        self.alias = alias

    def __call__(
        self,
        method: (
            Callable[[SchemaBase[T]], SchemaBase[T]]
            | Callable[[typing.Any, SchemaBase[T]], SchemaBase[T]]
        ),
    ):
        if not isinstance(method, (classmethod, staticmethod)):
            raise ValueError(
                "@dc.field must decorate a class method or a static method"
            )
        return super().__call__(method)


class EnsureFieldsDecorator(DecoratorBase):
    def __init__(self, fieldnames: list[str], /, message=None):
        self.fieldnames = fieldnames
        self.message = message

    def __call__(self, method: Callable[[T], bool]):
        if isinstance(method, (classmethod, staticmethod)):
            raise ValueError("@dc.ensire_fields must decorate a instance method")
        return super().__call__(method)


class DecoratorNamespace:
    field = FieldDecorator
    ensure_fields = EnsureFieldsDecorator


dc = DecoratorNamespace()
