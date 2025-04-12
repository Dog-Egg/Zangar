from __future__ import annotations

import dataclasses
import datetime
import inspect
import sys
import types
import typing
import warnings
from collections.abc import Callable
from functools import partial
from typing import TypeVar, get_args, get_origin

from zangar._types import Field

from . import _types
from ._common import empty
from ._core import Schema, SchemaBase, Union
from ._functional import ensure
from ._messages import DefaultMessage, get_message
from .exceptions import ValidationError

T = TypeVar("T")


# pylint: disable=invalid-name
class dataclass(Schema):

    def __init__(self, cls: type[dataclasses._DataclassT], /):
        self.__wrapper = _dataclass(cls, {})
        super().__init__(prev=self.__wrapper)

    @property
    def struct(self) -> _types.Struct:
        return self.__wrapper.struct


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
    int: _types.Integer,
    str: _types.String,
    float: _types.Float,
    bool: _types.Boolean,
    datetime.datetime: _types.Datetime,
}


def _dataclass(
    cls: type[dataclasses._DataclassT], cache: dict
) -> _DataclassWrapper[dataclasses._DataclassT]:
    if cls in cache:
        return typing.cast(_DataclassWrapper, Proxy(lambda: cache[cls]))
    cache[cls] = None  # None is a placeholder

    dc_fields = dataclasses.fields(cls)  # type: ignore
    struct_fields: dict[str, Field] = {}
    try:
        hints = typing.get_type_hints(cls)
    except KeyError:
        hints = {}

    decorators = DecoratorCollector(cls)

    for dc_field in dc_fields:
        get_schema = partial(
            resolve_type, hints.get(dc_field.name, dc_field.type), cache
        )

        if "zangar" in dc_field.metadata:
            metadata: dict = dc_field.metadata["zangar"].copy()
            if "schema" not in metadata:
                metadata["schema"] = get_schema()
            struct_field = _types.Field(**metadata)
        else:
            if dc_field.name in decorators.field_decorators:
                decorator = decorators.field_decorators[dc_field.name]
                if isinstance(decorator, FieldAssistedDecorator):
                    schema = getattr(cls, decorator.method_name)(get_schema())
                else:
                    schema = getattr(cls, decorator.method_name)()
                struct_field = _types.Field(schema, alias=decorator.alias)
            else:
                struct_field = _types.Field(get_schema())

        default: typing.Any = _types.Field._empty
        if dc_field.default is not dataclasses.MISSING:
            default = dc_field.default
        elif dc_field.default_factory is not dataclasses.MISSING:
            default = dc_field.default_factory
        if default is not _types.Field._empty:
            struct_field = struct_field.optional(default=default)
        struct_fields[dc_field.name] = struct_field
    struct = _types.Struct(struct_fields)
    schema = struct.transform(lambda d: cls(**d))
    schema = _process_ensure_fields(
        schema,
        decorators.ensure_fields_decorators,
        struct._name_to_alias,
    )
    cache[cls] = schema
    return _DataclassWrapper(struct, prev=schema)


class _DataclassWrapper(Schema["dataclasses._DataclassT"]):
    def __init__(self, struct: _types.Struct, prev):
        super().__init__(prev=prev)
        self.__struct = struct

    @property
    def struct(self):
        return self.__struct


def resolve_type(t, cache: dict) -> SchemaBase:
    if dataclasses.is_dataclass(t):
        return _dataclass(typing.cast(type, t), cache)

    values = resolve_complex_type(t)
    if values is not None:
        schema_cls, args = values
        return schema_cls(*map(partial(resolve_type, cache=cache), args))

    if not isinstance(t, type):
        raise NotImplementedError(t, type(t))

    if t in TYPE_MAPPING:
        return TYPE_MAPPING[t]()
    return ensure(
        lambda x: isinstance(x, t),
        message=DefaultMessage(name="type_check", ctx={"expected_type": t}),
    )


def resolve_complex_type(tp):
    origin = get_origin(tp)
    if origin is None:
        return None
    if origin is list:
        return (_types.List, get_args(tp))
    if sys.version_info >= (3, 10) and origin is types.UnionType:
        return (Union, get_args(tp))
    if origin is typing.Union:
        return (Union, get_args(tp))
    raise NotImplementedError(tp)


class DecoratorCollector:
    def __init__(self, cls):
        self.field_decorators: dict[str, FieldDecorator] = {}
        self.ensure_fields_decorators: list[EnsureFieldsDecorator] = []

        for c in inspect.getmro(cls):
            if dataclasses.is_dataclass(c):
                fieldnames = {f.name for f in dataclasses.fields(c)}
                for obj in vars(c).values():
                    decorator = getattr(obj, _DECORATOR_KEY, None)
                    if isinstance(decorator, FieldDecorator):
                        if decorator.fieldname not in fieldnames:
                            raise RuntimeError(
                                f"Field {decorator.fieldname!r} is not found"
                            )
                        if decorator.fieldname in self.field_decorators:
                            raise RuntimeError(
                                f"Field {decorator.fieldname!r} is already decorated"
                            )
                        self.field_decorators[decorator.fieldname] = decorator
                    elif isinstance(decorator, EnsureFieldsDecorator):
                        self.ensure_fields_decorators.append(decorator)


_DECORATOR_KEY = "zangar_decorator"


class DecoratorBase:
    method_name: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            "Decorators are deprecated",
            DeprecationWarning,
            stacklevel=3,
        )

    def __call__(self, method):
        setattr(method, _DECORATOR_KEY, self)
        try:
            self.method_name = method.__name__
        except AttributeError:
            self.method_name = method.__func__.__name__
        return method


class FieldDecorator(DecoratorBase):
    __name: str

    def __init_subclass__(cls, name):
        cls.__name = name

    def __init__(self, fieldname: str, /, *, alias: str | None = None):
        super().__init__()
        self.fieldname = fieldname
        self.alias = alias

    def __call__(self, method):
        if not isinstance(method, (classmethod, staticmethod)):
            raise ValueError(
                f"@dc.{self.__name} must decorate a class method or a static method"
            )
        return super().__call__(method)


class FieldAssistedDecorator(FieldDecorator, name="field_assisted"):
    def __call__(
        self,
        method: (
            Callable[[SchemaBase[T]], SchemaBase[T]]
            | Callable[[typing.Any, SchemaBase[T]], SchemaBase[T]]
        ),
    ):
        return super().__call__(method)


class _DeprecatedFieldDecorator(FieldAssistedDecorator, name="field"):
    pass


class FieldManualDecorator(FieldDecorator, name="field_manual"):
    def __call__(
        self,
        method: Callable[[], SchemaBase[T]] | Callable[[typing.Any], SchemaBase[T]],
    ):
        return super().__call__(method)


class EnsureFieldsDecorator(DecoratorBase):
    def __init__(self, fieldnames: list[str], /, *, message=None):
        super().__init__()
        self.fieldnames = fieldnames
        self.message = message

    def __call__(self, method: Callable[[T], bool]):
        if isinstance(method, (classmethod, staticmethod)):
            raise ValueError("@dc.ensire_fields must decorate a instance method")
        return super().__call__(method)


class DecoratorNamespace:
    @property
    def field(self):
        warnings.warn(
            "@dc.field is deprecated, use @dc.field_assisted instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return _DeprecatedFieldDecorator

    field_assisted = FieldAssistedDecorator
    field_manual = FieldManualDecorator
    ensure_fields = EnsureFieldsDecorator


dc = DecoratorNamespace()
