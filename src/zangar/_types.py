from __future__ import annotations

import abc
import copy
import datetime
import typing as t
import warnings
from collections.abc import Callable, Iterable, Mapping
from operator import getitem

from ._common import Empty, empty
from ._core import Schema, SchemaBase
from ._messages import DefaultMessage, get_message
from .exceptions import ValidationError

T = t.TypeVar("T")


class Field(t.Generic[T]):
    _empty = empty

    def __init__(
        self,
        schema: SchemaBase[T],
        *,
        alias: str | None = None,
    ) -> None:
        self._schema = schema
        self.__alias = alias
        self._required = True
        self._required_message = None
        self._default: Callable[[], T] | T | Empty = empty

    def _get_default(self):
        if callable(self._default):
            return self._default()
        return self._default

    @property
    def _alias(self):
        return self.__alias

    def parse(self, value, /):
        return self._schema.parse(value)

    def optional(self, *, default: T | Callable[[], T] | Empty = empty):
        self._required = False
        self._default = default
        return self

    def required(self, /, *, message=None):
        self._required = True
        if message is not None:
            self._required_message = message
        return self


class TypeSchema(Schema[T], abc.ABC):

    @abc.abstractmethod
    def _expected_type(self) -> type: ...

    def _convert(self, value):
        return value

    def __init__(self, *, message=None, **kwargs):
        expected_type = self._expected_type()
        super().__init__(
            **kwargs,
            prev=Schema()
            .transform(
                self._convert,
                message=(
                    message
                    if message is not None
                    else DefaultMessage(
                        name="type_convertion", ctx={"expected_type": expected_type}
                    )
                ),
            )
            .ensure(
                lambda x: isinstance(x, expected_type),
                message=(
                    message
                    if message is not None
                    else DefaultMessage(
                        name="type_check", ctx={"expected_type": expected_type}
                    )
                ),
            )
            .transform(self._pretransform),
        )

    def _pretransform(self, value):
        return value


class StringMethods(Schema):
    def min(self, value: int, /, **kwargs):
        kwargs.setdefault("message", DefaultMessage(name="str_min", ctx={"min": value}))
        return StringMethods(
            prev=self.ensure(lambda x: len(x) >= value, **kwargs),
            meta={"$min": value},
        )

    def max(self, value: int, /, **kwargs):
        kwargs.setdefault("message", DefaultMessage(name="str_max", ctx={"max": value}))
        return StringMethods(
            prev=self.ensure(lambda x: len(x) <= value, **kwargs),
            meta={"$max": value},
        )

    def strip(self, *args, **kwargs):
        return StringMethods(prev=self.transform((lambda s: s.strip(*args, **kwargs))))


class String(TypeSchema[str], StringMethods):
    def _expected_type(self) -> type:
        return str


class NumberMethods(Schema):
    def gte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", DefaultMessage(name="number_gte", ctx={"gte": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x >= value, **kwargs), meta={"$gte": value}
        )

    def gt(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", DefaultMessage(name="number_gt", ctx={"gt": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x > value, **kwargs), meta={"$gt": value}
        )

    def lte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", DefaultMessage(name="number_lte", ctx={"lte": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x <= value, **kwargs), meta={"$lte": value}
        )

    def lt(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", DefaultMessage(name="number_lt", ctx={"lt": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x < value, **kwargs), meta={"$lt": value}
        )


class Integer(TypeSchema[int], NumberMethods):
    def _expected_type(self) -> type:
        return int


class Float(TypeSchema[float], NumberMethods):
    def _expected_type(self) -> type:
        return float


class Boolean(TypeSchema[bool]):
    def _expected_type(self) -> type:
        return bool


_NoneType = type(None)


class NoneType(TypeSchema[_NoneType]):
    def _expected_type(self) -> type:
        return _NoneType


class Any(TypeSchema):
    def _expected_type(self) -> type:
        return object


class DatetimeMethods(Schema[datetime.datetime]):
    def __is_aware(self, d):
        return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None

    def is_aware(self, **kwargs):
        kwargs.setdefault("message", DefaultMessage(name="datetime_is_aware"))
        return DatetimeMethods(prev=self.ensure(self.__is_aware, **kwargs))

    def is_naive(self, **kwargs):
        kwargs.setdefault("message", DefaultMessage(name="datetime_is_naive"))
        return DatetimeMethods(
            prev=self.ensure(lambda x: not self.__is_aware(x), **kwargs)
        )


class Datetime(TypeSchema[datetime.datetime], DatetimeMethods):
    def _expected_type(self) -> type:
        return datetime.datetime


class StructMethod(Schema[T]):
    def __init__(
        self,
        *args,
        name_to_alias: dict[str, str],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.__name_to_alias = name_to_alias

    def ensure_fields(
        self,
        fieldnames: list[str],
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
    ):
        def inner_func(value):
            if func(value):
                return True
            error = ValidationError(empty)
            for fieldname in fieldnames:
                error._set_child(
                    self.__name_to_alias[fieldname],
                    ValidationError(
                        get_message(
                            (
                                message
                                if message is not None
                                else DefaultMessage(name="ensure_failed")
                            ),
                            value=value,
                        )
                    ),
                )
            raise error

        return StructMethod(
            prev=self.ensure(inner_func), name_to_alias=self.__name_to_alias
        )


class Struct(TypeSchema[dict], StructMethod[dict]):
    def _expected_type(self) -> type:
        return object

    def __init__(
        self,
        fields: (
            dict[str, Field] | dict[str, SchemaBase] | dict[str, Field | SchemaBase]
        ),
        /,
    ):
        self._fields: dict[str, Field] = {}
        for name, field in fields.items():
            if not isinstance(field, Field):
                self._fields[name] = Field(field)
            else:
                self._fields[name] = field

        self._name_to_alias, self._alias_to_name = {}, {}
        for name, field in self._fields.items():
            alias = field._alias or name
            self._name_to_alias[name] = alias
            self._alias_to_name[alias] = name

        super().__init__(name_to_alias=self._name_to_alias)

    def extend(self, fields: dict[str, Field | SchemaBase], /):
        new_fields: dict[str, Field | SchemaBase] = {}
        new_fields.update(self._fields)
        new_fields.update(fields)
        return Struct(fields)

    def __check_fieldnames(self, fieldnames: Iterable[str], /):
        for name in fieldnames:
            if name not in self._fields:
                raise ValueError(f"Field {name!r} not found in the struct schema")

    def required_fields(self, fieldnames: Iterable[str] | None = None, /) -> Struct:
        if fieldnames is not None:
            self.__check_fieldnames(fieldnames)

        copy_fields: dict[str, Field] = {}
        for name, field in self._fields.items():
            copy_field = copy.copy(field)
            if fieldnames is None or name in fieldnames:
                copy_field.required()
            else:
                copy_field.optional()
            copy_fields[name] = copy_field
        return self.__class__(copy_fields)

    def optional_fields(self, fieldnames: Iterable[str] | None = None, /) -> Struct:
        if fieldnames is not None:
            self.__check_fieldnames(fieldnames)
        if fieldnames is None:
            return self.required_fields([])
        return self.required_fields(set(self._fields) - set(fieldnames))

    def pick_fields(self, fieldnames: Iterable[str], /) -> Struct:
        self.__check_fieldnames(fieldnames)
        copy_fields = {}
        for name in fieldnames:
            copy_fields[name] = copy.copy(self._fields[name])
        return self.__class__(copy_fields)

    def omit_fields(self, fieldnames: Iterable[str], /) -> Struct:
        self.__check_fieldnames(fieldnames)
        return self.pick_fields(set(self._fields) - set(fieldnames))

    def _pretransform(self, value):
        rv = {}
        error = ValidationError(empty)

        for fieldname, field in self._fields.items():
            alias = self._name_to_alias[fieldname]
            if isinstance(value, Mapping):
                try:
                    field_value = getitem(value, alias)
                except KeyError:
                    field_value = empty
            else:
                try:
                    field_value = getattr(value, alias)
                except AttributeError:
                    field_value = empty

            if field_value is empty:
                if field._required:
                    error._set_child(
                        alias,
                        ValidationError(
                            get_message(
                                message=(
                                    field._required_message
                                    if field._required_message is not None
                                    else DefaultMessage(name="field_required")
                                ),
                                value=None,
                            )
                        ),
                    )
                    continue

                default = field._get_default()
                if default is not empty:
                    rv[fieldname] = default
            else:
                try:
                    field_value = field.parse(field_value)
                except ValidationError as e:
                    error._set_child(alias, e)
                else:
                    rv[fieldname] = field_value

        if not error._empty():
            raise error

        return rv


class Object(Struct):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            "Object is deprecated, use Struct instead",
            DeprecationWarning,
            stacklevel=2,
        )


class List(TypeSchema[t.List[T]]):
    def _expected_type(self) -> type:
        return list

    def __init__(self, item: SchemaBase[T] | None = None, /, **kwargs):
        super().__init__(**kwargs)
        self._item = item or Any()

    def _pretransform(self, value):
        rv = []
        error = ValidationError(empty)
        for index, item in enumerate(value):
            try:
                item = self._item.parse(item)
            except ValidationError as exc:
                error._set_child(index, exc)
            rv.append(item)
        if not error._empty():
            raise error
        return rv
