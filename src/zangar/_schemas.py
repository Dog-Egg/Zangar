from __future__ import annotations

import abc
import copy
import typing as t
from collections.abc import Callable, Mapping
from operator import getitem

from ._common import Empty, empty
from .exceptions import ValidationError

__all__ = [
    "Schema",
    "String",
    "Integer",
    "Object",
    "Field",
    "List",
    "Nullable",
]


T = t.TypeVar("T")
P = t.TypeVar("P")


class RefineMixin(t.Generic[T], abc.ABC):

    @abc.abstractmethod
    def refine(self, func: Callable[[T], bool], /, *, message=None) -> RefineMixin: ...


class TransformMixin(t.Generic[T], abc.ABC):
    @abc.abstractmethod
    def transform(self, func: Callable[[T], P]) -> TransformMixin: ...


class SchemaBase(t.Generic[T]):
    def parse(self, value, /) -> T:
        raise NotImplementedError


class Nullable(SchemaBase[t.Union[T, None]]):
    def __init__(self, schema: SchemaBase[T], /) -> None:
        self.__schema = schema

    def parse(self, value, /) -> T | None:
        if value is None:
            return None
        return self.__schema.parse(value)


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


class Schema(t.Generic[T], RefineMixin[T], TransformMixin[T], SchemaBase[T], abc.ABC):
    def __init__(self):
        super().__init__()
        self.__processors: list[Callable[[T], T]] = []
        self.__nonnullable_message: str = "This value is not nullable"

    @abc.abstractmethod
    def _parse(self, value) -> T: ...

    def parse(self, value, /) -> T:
        if value is None:
            raise ValidationError(self.__nonnullable_message)

        value = self._parse(value)

        error = ValidationError(empty)
        for processor in self.__processors:
            try:
                value = processor(value)
            except ValidationError as exc:
                error._concat(exc)

        if not error._empty():
            raise error

        return value

    def refine(self, func: Callable[[T], bool], /, *, message=None):
        self.__processors.append(ValidationProcessor(func, message))
        return self

    def nullable(self, /):
        return Nullable(self)

    def nonnullable(self, /, *, message=None):
        if message is not None:
            self.__nonnullable_message = message
        return self

    def transform(self, func: Callable[[T], P]):
        return Transformer[P](func, schema=self)


class ValidationProcessor(t.Generic[T]):
    def __init__(self, func: Callable[[T], bool], message=None) -> None:
        self.__func = func
        self.__message = message

    def __call__(self, value: T) -> T:
        if self.__func(value):
            return value
        raise ValidationError(message=self.__message or "Invalid value")


class Transformer(t.Generic[T], RefineMixin[T], TransformMixin[T], SchemaBase):
    def __init__(
        self, transform: Callable[[t.Any], T], schema, pretransformer=None
    ) -> None:
        self.__validators: list[tuple[Callable[[T], bool], t.Any]] = []
        self.__transform = transform

        self.__schema: Schema = schema
        self.__pretransformer: Transformer | None = pretransformer

        super().__init__()

    def refine(self, func: Callable[[T], bool], /, *, message=None):
        self.__validators.append((func, message))
        return self

    def transform(self, func: Callable[[T], P]):
        return Transformer[P](
            transform=func,
            schema=self.__schema,
            pretransformer=self,
        )

    def parse(self, value, /):
        if self.__pretransformer:
            value = self.__pretransformer.parse(value)
        else:
            value = self.__schema.parse(value)
        value = self.__transform(value)
        for validator, message in self.__validators:
            if not validator(value):
                raise ValidationError(message)
        return value


class Object(Schema[dict]):
    def __init__(self, fields: dict[str, Field], /):
        super().__init__()

        self.__fields: dict[str, Field] = fields

    def _parse(self, value):
        value = copy.copy(value)

        rv = {}
        error = ValidationError(empty)

        get: Callable[[t.Any, str], t.Any]
        if isinstance(value, Mapping):
            get = getitem
        else:
            get = getattr

        for fieldname, field in self.__fields.items():
            alias = fieldname if field._alias is None else field._alias

            try:
                field_value = get(value, alias)
            except (KeyError, AttributeError) as exc:
                if field._required:
                    raise ValidationError(field._required_message) from exc
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

    def extend(self, fields: dict[str, Field], /):
        _fields = self.__fields.copy()
        _fields.update(fields)
        return Object(_fields)


class String(Schema[str]):
    def __init__(self):
        super().__init__()
        self._min = None
        self._max = None
        self._pattern = None

    def _parse(self, value):
        return str(value)


class Integer(Schema[int]):

    def _parse(self, value):
        try:
            f = float(value)
            i = int(f)
            if i != f:
                raise ValueError
        except ValueError as exc:
            raise ValidationError("Invalid integer") from exc
        return i


class List(Schema[t.List[T]]):
    def __init__(self, schema: SchemaBase, /):
        super().__init__()
        self.__schema = schema

    def _parse(self, value):
        rv = []
        error = ValidationError(empty)
        for index, item in enumerate(value):
            try:
                rv.append(self.__schema.parse(item))
            except ValidationError as exc:
                error._setitem(index, exc)
        if not error._empty():
            raise error
        return rv
