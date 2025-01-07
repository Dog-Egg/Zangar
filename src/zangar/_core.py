from __future__ import annotations

import abc
import datetime
import sys
import typing as t
from collections.abc import Callable, Mapping
from operator import getitem

from ._common import Empty, empty
from ._messages import IncompleteMessage, get_message
from .exceptions import ValidationError

T = t.TypeVar("T")
P = t.TypeVar("P")


class SchemaBase(t.Generic[T], abc.ABC):
    @abc.abstractmethod
    def __or__(self, other: SchemaBase[P]) -> SchemaBase[T | P]: ...

    @abc.abstractmethod
    def parse(self, value, /) -> T: ...

    @abc.abstractmethod
    def ensure(
        self, func: Callable[[T], bool], /, *, message: t.Any = None
    ) -> SchemaBase[T]: ...

    @abc.abstractmethod
    def transform(
        self, func: Callable[[T], P], /, *, message: t.Any = None
    ) -> SchemaBase[P]: ...

    @abc.abstractmethod
    def relay(self, other: SchemaBase[P], /) -> SchemaBase[P]: ...


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


class TransformationValidator:
    def __init__(self, func) -> None:
        self.__func = func

    def __call__(self, value):
        return self.__func(value)


class EnsuranceValidator:
    def __init__(self, func, break_on_failure) -> None:
        self.__func = func
        self.break_on_failure = break_on_failure

    def __call__(self, value):
        return self.__func(value)


class Schema(SchemaBase[T]):

    def __init__(
        self,
        *,
        prev: Schema | None = None,
        validator: TransformationValidator | EnsuranceValidator | None = None,
    ):
        self.__prev = prev
        self._validator = validator

    def __or__(self, other: SchemaBase[P]) -> Union[T, P]:
        return Union(self, other)

    def ensure(
        self,
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
        break_on_failure: bool = False,
    ) -> Schema[T]:
        def validate(value):
            if not func(value):
                if isinstance(message, IncompleteMessage):
                    msg = get_message(
                        name=message.name,
                        message=None,
                        value=value,
                        ctx=message.ctx,
                    )
                else:
                    msg = get_message(
                        name="ensure_failed", message=message, value=value
                    )
                raise ValidationError(msg)

        return Schema(
            prev=self, validator=EnsuranceValidator(validate, break_on_failure)
        )

    def transform(
        self,
        func: Callable[[T], P],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
    ):
        def validate(value):
            try:
                return func(value)
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise e
                if isinstance(message, IncompleteMessage):
                    msg = get_message(
                        name=message.name,
                        message=None,
                        value=value,
                        ctx=message.ctx,
                    )
                else:
                    msg = get_message(
                        name="transform_failed",
                        message=message,
                        value=value,
                        ctx={"exc": e},
                    )
                raise ValidationError(msg) from e

        return Schema[P](prev=self, validator=TransformationValidator(validate))

    def relay(self, other: SchemaBase[P], /):
        return self.transform(other.parse)

    def __iterate_chain(self):
        if self.__prev is not None:
            yield from self.__prev.__iterate_chain()
        yield self

    def parse(self, value, /) -> T:
        error = ValidationError(empty)
        for n in self.__iterate_chain():
            validator = n._validator
            if isinstance(validator, EnsuranceValidator):
                try:
                    validator(value)
                except ValidationError as e:
                    error._concat(e)
                    if validator.break_on_failure:
                        break
            elif isinstance(validator, TransformationValidator):
                if not error._empty():
                    raise error
                value = validator(value)

        if not error._empty():
            raise error

        return value


class Union(t.Generic[T, P], Schema[t.Union[T, P]]):
    def __init__(self, a: SchemaBase[T], b: SchemaBase[P], /):
        self.__unions = (a, b)

        def transform(value):
            error = ValidationError(empty)
            for item in self.__unions:
                try:
                    return item.parse(t.cast(t.Any, value))
                except ValidationError as e:
                    error._concat(e)
            raise error

        super().__init__(prev=Schema().transform(transform))

    def __repr__(self) -> str:
        items: list[str] = []
        for item in self.__unions:
            if isinstance(item, Union):
                items.append(repr(item))
            else:
                items.append(item.__class__.__name__)
        return " | ".join(items)


S = t.TypeVar("S", bound=Schema)


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


def ref(name: str, /):
    frame = sys._getframe(1)

    def transform(value):
        schema: Schema = frame.f_locals[name]
        return schema.parse(value)

    return Schema().transform(transform)
