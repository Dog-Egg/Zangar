from __future__ import annotations

import abc
import datetime
import typing as t
from collections.abc import Callable, Mapping
from operator import getitem

from ._common import Empty, empty
from ._core import Schema, SchemaBase
from ._messages import IncompleteMessage, get_message
from .exceptions import ValidationError

T = t.TypeVar("T")


class Field(t.Generic[T]):
    def __init__(
        self,
        schema: SchemaBase[T],
        /,
        *,
        alias: str | None = None,
    ) -> None:
        self.__schema = schema
        self.__alias = alias
        self._required = True
        self._required_message = None
        self.__default: Callable[[], T] | T | Empty = empty

    def _get_default(self):
        if callable(self.__default):
            return self.__default()
        return self.__default

    @property
    def _alias(self):
        return self.__alias

    def parse(self, value, /):
        return self.__schema.parse(value)

    def optional(self, *, default: T | Callable[[], T] | Empty = empty):
        self._required = False
        self.__default = default
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

    def __init__(self, *, message=None):
        expected_type = self._expected_type()
        super().__init__(
            prev=Schema()
            .transform(
                self._convert,
                message=message
                or IncompleteMessage(
                    name="type_convertion", ctx={"expected_type": expected_type}
                ),
            )
            .ensure(
                lambda x: isinstance(x, expected_type),
                message=message
                or IncompleteMessage(
                    name="type_check", ctx={"expected_type": expected_type}
                ),
            )
            .transform(self._pretransform)
        )

    def _pretransform(self, value):
        return value


class StringMethods(Schema):
    def min(self, value: int, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="str_min", ctx={"min": value})
        )
        return StringMethods(prev=self.ensure(lambda x: len(x) >= value, **kwargs))

    def max(self, value: int, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="str_max", ctx={"max": value})
        )
        return StringMethods(prev=self.ensure(lambda x: len(x) <= value, **kwargs))

    def strip(self, *args, **kwargs):
        return StringMethods(prev=self.transform((lambda s: s.strip(*args, **kwargs))))


class String(TypeSchema[str], StringMethods):
    def _expected_type(self) -> type:
        return str


class NumberMethods(Schema):
    def gte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="number_gte", ctx={"gte": value})
        )
        return NumberMethods(prev=self.ensure(lambda x: x >= value, **kwargs))

    def gt(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="number_gt", ctx={"gt": value})
        )
        return NumberMethods(prev=self.ensure(lambda x: x > value, **kwargs))

    def lte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="number_lte", ctx={"lte": value})
        )
        return NumberMethods(prev=self.ensure(lambda x: x <= value, **kwargs))

    def lt(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", IncompleteMessage(name="number_lt", ctx={"lt": value})
        )
        return NumberMethods(prev=self.ensure(lambda x: x < value, **kwargs))


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


class Datetime(TypeSchema[datetime.datetime]):
    def _expected_type(self) -> type:
        return datetime.datetime


class Object(TypeSchema[dict]):
    def _expected_type(self) -> type:
        return object

    def __init__(self, fields: dict[str, Field], /):
        super().__init__()
        self.__fields = fields

    def extend(self, fields: dict[str, Field], /):
        _fields = self.__fields.copy()
        _fields.update(fields)
        return Object(_fields)

    def _pretransform(self, value):
        rv = {}
        error = ValidationError(empty)

        for fieldname, field in self.__fields.items():
            alias = fieldname if field._alias is None else field._alias
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
                    message = get_message(
                        name="field_required",
                        message=field._required_message,
                        value=None,
                    )
                    error._setitem(alias, ValidationError(message))
                    continue

                default = field._get_default()
                if default is not empty:
                    rv[fieldname] = default
            else:
                try:
                    field_value = field.parse(field_value)
                except ValidationError as e:
                    error._setitem(alias, e)
                else:
                    rv[fieldname] = field_value

        if not error._empty():
            raise error

        return rv


class List(TypeSchema[t.List[T]]):
    def _expected_type(self) -> type:
        return list

    def __init__(self, item: SchemaBase[T] | None = None, /):
        super().__init__()
        self.__item = item

    def _pretransform(self, value):
        rv = []
        error = ValidationError(empty)
        for index, item in enumerate(value):
            if self.__item is not None:
                try:
                    item = self.__item.parse(item)
                except ValidationError as exc:
                    error._setitem(index, exc)
            rv.append(item)
        if not error._empty():
            raise error
        return rv
