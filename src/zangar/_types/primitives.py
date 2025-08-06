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

        .. code-block::

            >>> z.str().min(1).parse('hello')
            'hello'

            # equivalent to:
            >>> z.str().ensure(lambda x: len(x) >= 1).parse('hello')
            'hello'
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

        .. code-block::

            >>> z.str().max(10).parse('hello')
            'hello'

            # equivalent to:
            >>> z.str().ensure(lambda x: len(x) <= 10).parse('hello')
            'hello'
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="str_max", value=value, ctx={"max": value})
        )
        return StringMethods(
            prev=self.ensure(lambda x: len(x) <= value, **kwargs),
            meta={"$max": value},
        )

    def strip(self, *args, **kwargs):
        """Trim whitespace from both ends.

        .. code-block::

            >>> z.str().strip().parse(' hello ')
            'hello'

            # equivalent to:
            >>> z.str().transform(lambda x: x.strip()).parse(' hello ')
            'hello'
        """
        return StringMethods(prev=self.transform((lambda s: s.strip(*args, **kwargs))))


class ZangarStr(TypeSchema[str], StringMethods):
    """Validate that the data is of type `str`.

    .. code-block::

        >>> z.str().parse('hello')
        'hello'

        # equivalent to:
        >>> z.ensure(lambda x: isinstance(x, str)).parse('hello')
        'hello'
    """

    def _expected_type(self) -> type:
        return str


class NumberMethods(Schema):
    def gte(self, value: int | float, /, **kwargs):
        """Validate the number is greater than or equal to a given value.

        Args:
            value: The minimum value of the number.
            message: The error message to display when the validation fails.

        .. code-block::

            >>> z.int().gte(0).parse(1)
            1

            # equivalent to:
            >>> z.int().ensure(lambda x: x >= 0).parse(1)
            1
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

        .. code-block::

            >>> z.int().gt(0).parse(1)
            1

            # equivalent to:
            >>> z.int().ensure(lambda x: x > 0).parse(1)
            1
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

        .. code-block::

            >>> z.int().lte(10).parse(1)
            1

            # equivalent to:
            >>> z.int().ensure(lambda x: x <= 10).parse(1)
            1
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

        .. code-block::

            >>> z.int().lt(10).parse(1)
            1

            # equivalent to:
            >>> z.int().ensure(lambda x: x < 10).parse(1)
            1
        """
        kwargs.setdefault(
            "message", DefaultMessage(key="number_lt", value=value, ctx={"lt": value})
        )
        return NumberMethods(
            prev=self.ensure(lambda x: x < value, **kwargs), meta={"$lt": value}
        )


class ZangarInt(TypeSchema[int], NumberMethods):
    """Validate that the data is of type `int`.

    .. code-block::

        >>> z.int().parse(1)
        1

        # equivalent to:
        >>> z.ensure(lambda x: isinstance(x, int)).parse(1)
        1
    """

    def _expected_type(self) -> type:
        return int


class ZangarFloat(TypeSchema[float], NumberMethods):
    """Validate that the data is of type `float`.

    .. code-block::

        >>> z.float().parse(1.0)
        1.0

        # equivalent to:
        >>> z.ensure(lambda x: isinstance(x, float)).parse(1.0)
        1.0
    """

    def _expected_type(self) -> type:
        return float


class ZangarBool(TypeSchema[bool]):
    """Validate that the data is of type `bool`.

    .. code-block::

        >>> z.bool().parse(True)
        True

        # equivalent to:
        >>> z.ensure(lambda x: isinstance(x, bool)).parse(True)
        True
    """

    def _expected_type(self) -> type:
        return bool


_NoneType = type(None)


class ZangarNone(TypeSchema[_NoneType]):
    """Validate that the data is `None`.

    .. code-block::

        >>> z.none().parse(None)

        # equivalent to:
        >>> z.ensure(lambda x: x is None).parse(None)
    """

    def _expected_type(self) -> type:
        return _NoneType


class ZangarAny(TypeSchema):
    """Validate that the data is of any type."""

    def _expected_type(self) -> type:
        return object


class DatetimeMethods(Schema[datetime.datetime]):
    def __is_aware(self, d):
        return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None

    def is_aware(self, **kwargs):
        """Validate the datetime is aware."""
        kwargs.setdefault(
            "message",
            lambda value: DefaultMessage(key="datetime_is_aware", value=value),
        )
        return DatetimeMethods(prev=self.ensure(self.__is_aware, **kwargs))

    def is_naive(self, **kwargs):
        """Validate the datetime is naive."""
        kwargs.setdefault(
            "message",
            lambda value: DefaultMessage(key="datetime_is_naive", value=value),
        )
        return DatetimeMethods(
            prev=self.ensure(lambda x: not self.__is_aware(x), **kwargs)
        )


class ZangarDatetime(TypeSchema[datetime.datetime], DatetimeMethods):
    """Validate that the data is of type `datetime.datetime`.

    equivalent to:

    .. code-block::

        >>> z.datetime().parse(datetime.datetime(2000, 1, 1))
        datetime.datetime(2000, 1, 1, 0, 0)

        # equivalent to:
        >>> (
        ...    z.ensure(lambda x: isinstance(x, datetime.datetime))
        ...     .parse(datetime.datetime(2000, 1, 1))
        ... )
        datetime.datetime(2000, 1, 1, 0, 0)
    """

    def _expected_type(self) -> type:
        return datetime.datetime


class ZangarList(TypeSchema[t.List[T]]):
    """Validate that the data is of type `list`.

    Args:
        item: The schema to validate the items in the list.

    .. code-block::

        >>> z.list(z.transform(int)).parse(['1', 2])
        [1, 2]

        # equivalent to:
        >>> (
        ...    z.ensure(lambda x: isinstance(x, list))
        ...     .transform(lambda x: [z.transform(int).parse(i) for i in x])
        ...     .parse(['1', 2])
        ... )
        [1, 2]
    """

    def _expected_type(self) -> type:
        return list

    def __init__(self, item: SchemaBase[T] | None = None, /, **kwargs):
        super().__init__(**kwargs)
        self.__item = item or ZangarAny()

    @property
    def item(self):
        return self.__item

    def _pretransform(self, value):
        rv = []
        error = ValidationError()
        for index, item in enumerate(value):
            try:
                item = self.__item.parse(item)
            except ValidationError as exc:
                error._set_child_err(index, exc)
            rv.append(item)
        if not error._empty():
            raise error
        return rv
