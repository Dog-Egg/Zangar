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

    def __init__(self, prev: Schema | None = None):
        self._prev = prev
        self._validator: tuple[Callable[[T], None], bool] | None = None
        self._transform_func: Callable[[T], t.Any] = lambda x: x

    def ensure(
        self,
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
        break_on_failure: bool = False,
    ) -> Schema[T]:
        return self._ensure(
            func,
            message=message,
            break_on_failure=break_on_failure,
            return_class=Schema[T],
        )

    def _ensure(
        self,
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
        break_on_failure: bool = False,
        return_class: type[S],
    ) -> S:
        def validate(value):
            if not func(value):
                if callable(message):
                    msg = message(value)
                else:
                    msg = message
                raise ValidationError(msg or "Invalid value")

        self._validator = (validate, break_on_failure)
        return return_class(self)

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

        self._transform_func = decorator
        return Schema[P](self)

    def relay(self, other: SchemaBase[P], /):
        return self.transform(other.parse)

    def parse(self, value, /) -> T:
        node: Schema = self
        nodes: list[Schema] = [node]
        while node._prev:
            nodes.append(node._prev)
            node = node._prev

        error = ValidationError(empty)
        for n in reversed(nodes):
            if n._validator:
                validate, break_on_failure = n._validator
                try:
                    validate(value)
                except ValidationError as e:
                    error._concat(e)
                if not error._empty() and break_on_failure:
                    raise error
            else:
                if not error._empty():
                    raise error
                value = n._transform_func(value)
        return value


S = t.TypeVar("S", bound=Schema)


class TypeSchema(Schema[T]):

    __type: type

    def __init_subclass__(cls, type: type) -> None:
        cls.__type = type
        return super().__init_subclass__()

    def __init__(self):
        super().__init__(
            Schema()
            .ensure(
                lambda x: isinstance(x, self.__type),
                message=lambda x: f"Expected {self.__type.__name__}, received {type(x).__name__}",
            )
            .transform(self._transform)
        )

    def _transform(self, value):
        return value


class StringMixin(Schema):
    def min(self, value: int, /, **kwargs):
        kwargs.setdefault("message", f"The minimum length of the string is {value}")
        return self._ensure(
            lambda x: len(x) >= value, return_class=StringMixin, **kwargs
        )

    def max(self, value: int, /, **kwargs):
        kwargs.setdefault("message", f"The maximum length of the string is {value}")
        return self._ensure(
            lambda x: len(x) <= value, return_class=StringMixin, **kwargs
        )


class String(TypeSchema[str], StringMixin, type=str):
    pass


class NumberMixin(Schema):
    def gte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", f"The value should be greater than or equal to {value}"
        )
        return self._ensure(lambda x: x >= value, return_class=NumberMixin, **kwargs)

    def gt(self, value: int | float, /, **kwargs):
        kwargs.setdefault("message", f"The value should be greater than {value}")
        return self._ensure(lambda x: x > value, return_class=NumberMixin, **kwargs)

    def lte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", f"The value should be less than or equal to {value}"
        )
        return self._ensure(lambda x: x <= value, return_class=NumberMixin, **kwargs)

    def lt(self, value: int | float, /, **kwargs):
        kwargs.setdefault("message", f"The value should be less than {value}")
        return self._ensure(lambda x: x < value, return_class=NumberMixin, **kwargs)


class Integer(TypeSchema[int], NumberMixin, type=int):
    pass


class Float(TypeSchema[float], NumberMixin, type=float):
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
