from __future__ import annotations

import datetime
import typing as t

from zangar._core import Schema, SchemaBase
from zangar._messages import DefaultMessage
from zangar._types.base import TypeSchema
from zangar.exceptions import ValidationError

T = t.TypeVar("T")


class StringMethods(Schema):
    def min(self, value: int, /, **kwargs):
        """Validate the minimum length of a string.

        Args:
            value: The minimum length of the string.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="str_min", value=value, ctx={"min": value})
        )
        return StringMethods(
            prev=self.ensure(lambda x: len(x) >= value, **kwargs),
            meta={"$min": value},
        )

    def max(self, value: int, /, **kwargs):
        """Validate the maximum length of a string.

        Args:
            value: The maximum length of the string.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="str_max", value=value, ctx={"max": value})
        )
        return StringMethods(
            prev=self.ensure(lambda x: len(x) <= value, **kwargs),
            meta={"$max": value},
        )

    def strip(self, *args, **kwargs):
        """Trim whitespace from both ends."""
        return StringMethods(prev=self.transform((lambda s: s.strip(*args, **kwargs))))


class ZangarStr(TypeSchema[str], StringMethods):
    """Validate that the data is of type `str`."""

    def _expected_type(self) -> type:
        return str


class NumberMethods(Schema):
    def gte(self, value: int | float, /, **kwargs):
        """Validate the number is greater than or equal to a given value.

        Args:
            value: The minimum value of the number.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="number_gte", value=value, ctx={"gte": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x >= value, **kwargs), meta={"$gte": value}
        )

    def gt(self, value: int | float, /, **kwargs):
        """Validate the number is greater than a given value.

        Args:
            value: The minimum value of the number.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="number_gt", value=value, ctx={"gt": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x > value, **kwargs), meta={"$gt": value}
        )

    def lte(self, value: int | float, /, **kwargs):
        """Validate the number is less than or equal to a given value.

        Args:
            value: The maximum value of the number.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="number_lte", value=value, ctx={"lte": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x <= value, **kwargs), meta={"$lte": value}
        )

    def lt(self, value: int | float, /, **kwargs):
        """Validate the number is less than a given value.

        Args:
            value: The maximum value of the number.
            message: The error message to display when the validation fails.
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="number_lt", value=value, ctx={"lt": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x < value, **kwargs), meta={"$lt": value}
        )


class ZangarInt(TypeSchema[int], NumberMethods):
    def _expected_type(self) -> type:
        return int


class ZangarFloat(TypeSchema[float], NumberMethods):
    def _expected_type(self) -> type:
        return float


class ZangarBool(TypeSchema[bool]):
    def _expected_type(self) -> type:
        return bool


_NoneType = type(None)


class ZangarNone(TypeSchema[_NoneType]):
    def _expected_type(self) -> type:
        return _NoneType


class ZangarAny(TypeSchema):
    def _expected_type(self) -> type:
        return object


class DatetimeMethods(Schema[datetime.datetime]):
    def __is_aware(self, d):
        return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None

    def is_aware(self, **kwargs):
        kwargs.setdefault(
            "message",
            lambda value: DefaultMessage(key="datetime_is_aware", value=value),
        )
        return DatetimeMethods(prev=self.ensure(self.__is_aware, **kwargs))

    def is_naive(self, **kwargs):
        kwargs.setdefault(
            "message",
            lambda value: DefaultMessage(key="datetime_is_naive", value=value),
        )
        return DatetimeMethods(
            prev=self.ensure(lambda x: not self.__is_aware(x), **kwargs)
        )


class ZangarDatetime(TypeSchema[datetime.datetime], DatetimeMethods):
    def _expected_type(self) -> type:
        return datetime.datetime


class ZangarList(TypeSchema[t.List[T]]):
    """Validate that the data is of type `list`.

    Args:
        item: The schema to validate the items in the list.
    """

    def _expected_type(self) -> type:
        return list

    def __init__(self, item: SchemaBase[T] | None = None, /, **kwargs):
        super().__init__(**kwargs)
        self._item = item or ZangarAny()

    def _pretransform(self, value):
        rv = []
        error = ValidationError()
        for index, item in enumerate(value):
            try:
                item = self._item.parse(item)
            except ValidationError as exc:
                error._set_child_err(index, exc)
            rv.append(item)
        if not error._empty():
            raise error
        return rv
