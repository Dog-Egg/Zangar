from __future__ import annotations

import typing as t
from collections.abc import Callable, Mapping
from operator import getitem

from ._common import Empty, empty
from .exceptions import ValidationError

T = t.TypeVar("T")
P = t.TypeVar("P")


class SchemaBase(t.Generic[T]):
    def parse(self, value, /) -> T:
        raise NotImplementedError

    def __or__(self, other: SchemaBase[P]):
        return Union(self, other)


class Union(t.Generic[T, P], SchemaBase[t.Union[T, P]]):
    def __init__(self, a: SchemaBase[T], b: SchemaBase[P], /):
        self.__unions = (a, b)

    def parse(self, value, /) -> T | P:
        error = ValidationError(empty)
        for item in self.__unions:
            try:
                return item.parse(t.cast(t.Any, value))
            except ValidationError as e:
                error._concat(e)
        raise error

    def __repr__(self) -> str:
        items: list[str] = []
        for item in self.__unions:
            if isinstance(item, Union):
                items.append(repr(item))
            else:
                items.append(item.__class__.__name__)
        return " | ".join(items)


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
        self._required_message: str = "This field is required"
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


class Schema(t.Generic[T], SchemaBase[T]):
    def __init__(self, prev: SchemaBase | None = None):
        self.__prev = prev
        self.__validators: list[Callable[[t.Any], None]] = []
        self.__transform: Callable[[T], t.Any] = lambda x: x

    def ensure(
        self,
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
    ):

        def validate(value):
            if not func(value):
                if callable(message):
                    msg = message(value)
                else:
                    msg = message
                raise ValidationError(msg or "Invalid value")

        self.__validators.append(validate)
        return self

    def transform(
        self,
        func: Callable[[T], P],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
    ):
        def decorator(value):
            try:
                return func(value)
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise e
                msg = message(value) if callable(message) else message
                raise ValidationError(msg or str(e)) from e

        self.__transform = decorator
        return Schema[P](self)

    def relay(self, other: SchemaBase[P], /):
        return self.transform(other.parse)

    def parse(self, value, /) -> T:
        if self.__prev:
            value = self.__prev.parse(value)
        error = ValidationError(empty)
        for validate in self.__validators:
            try:
                validate(value)
            except ValidationError as e:
                error._concat(e)
        if not error._empty():
            raise error
        return self.__transform(value)


class TypeSchema(Schema[T]):

    __type: type

    def __init_subclass__(cls, type: type) -> None:
        cls.__type = type
        return super().__init_subclass__()

    def __init__(self):
        super().__init__()

    def _transform(self, value):
        return value

    def parse(self, value, /) -> T:
        return (
            (
                Schema()
                .ensure(
                    lambda x: isinstance(x, self.__type),
                    message=f"Expected {self.__type.__name__}, received {type(value).__name__}",
                )
                .transform(self._transform)
            )
            .relay(super())
            .parse(value)
        )


class String(TypeSchema[str], type=str):
    pass


class Integer(TypeSchema[int], type=int):
    pass


class Float(TypeSchema[float], type=float):
    pass


class Boolean(TypeSchema[bool], type=bool):
    pass


_NoneType = type(None)


class NoneType(TypeSchema[_NoneType], type=_NoneType):
    pass


class Any(TypeSchema, type=object):
    pass


class Object(TypeSchema[dict], type=object):
    def __init__(self, fields: dict[str, Field], /):
        super().__init__()
        self.__fields = fields

    def extend(self, fields: dict[str, Field], /):
        _fields = self.__fields.copy()
        _fields.update(fields)
        return Object(_fields)

    def _transform(self, value):
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
                    raise ValidationError(field._required_message)
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


class List(TypeSchema[t.List[T]], type=list):
    def __init__(self, item: SchemaBase[T], /):
        super().__init__()
        self.__item = item

    def _transform(self, value):
        rv = []
        error = ValidationError(empty)
        for index, item in enumerate(value):
            try:
                rv.append(self.__item.parse(item))
            except ValidationError as exc:
                error._setitem(index, exc)
        if not error._empty():
            raise error
        return rv
