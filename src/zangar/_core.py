from __future__ import annotations

import abc
import datetime
import typing as t
from collections.abc import Callable, Mapping
from operator import getitem

from ._common import Empty, empty
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
        schema: Schema[T],
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
                if callable(message):
                    msg = message(value)
                else:
                    msg = message
                raise ValidationError(msg or "Invalid value")

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
                msg = message(value) if callable(message) else message
                raise ValidationError(msg or str(e)) from e

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


class TypeSchema(Schema[T]):

    __type: type

    def __init_subclass__(cls, type: type) -> None:
        cls.__type = type
        return super().__init_subclass__()

    def __init__(self):
        super().__init__(
            prev=Schema()
            .ensure(
                lambda x: isinstance(x, self.__type),
                message=lambda x: f"Expected {self.__type.__name__}, received {type(x).__name__}",
            )
            .transform(self._pretransform)
        )

    def _pretransform(self, value):
        return value


class StringMethods(Schema):
    def min(self, value: int, /, **kwargs):
        kwargs.setdefault("message", f"The minimum length of the string is {value}")
        return StringMethods(prev=self.ensure(lambda x: len(x) >= value, **kwargs))

    def max(self, value: int, /, **kwargs):
        kwargs.setdefault("message", f"The maximum length of the string is {value}")
        return StringMethods(prev=self.ensure(lambda x: len(x) <= value, **kwargs))

    def strip(self, *args, **kwargs):
        return StringMethods(prev=self.transform((lambda s: s.strip(*args, **kwargs))))


class String(TypeSchema[str], StringMethods, type=str):
    pass


class NumberMethods(Schema):
    def gte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", f"The value should be greater than or equal to {value}"
        )
        return NumberMethods(prev=self.ensure(lambda x: x >= value, **kwargs))

    def gt(self, value: int | float, /, **kwargs):
        kwargs.setdefault("message", f"The value should be greater than {value}")
        return NumberMethods(prev=self.ensure(lambda x: x > value, **kwargs))

    def lte(self, value: int | float, /, **kwargs):
        kwargs.setdefault(
            "message", f"The value should be less than or equal to {value}"
        )
        return NumberMethods(prev=self.ensure(lambda x: x <= value, **kwargs))

    def lt(self, value: int | float, /, **kwargs):
        kwargs.setdefault("message", f"The value should be less than {value}")
        return NumberMethods(prev=self.ensure(lambda x: x < value, **kwargs))


class Integer(TypeSchema[int], NumberMethods, type=int):
    pass


class Float(TypeSchema[float], NumberMethods, type=float):
    pass


class Boolean(TypeSchema[bool], type=bool):
    pass


_NoneType = type(None)


class NoneType(TypeSchema[_NoneType], type=_NoneType):
    pass


class Any(TypeSchema, type=object):
    pass


class Datetime(TypeSchema[datetime.datetime], type=datetime.datetime):
    pass


class Object(TypeSchema[dict], type=object):
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
                    error._setitem(alias, ValidationError(field._required_message))
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


class List(TypeSchema[t.List[T]], type=list):
    def __init__(self, item: Schema[T], /):
        super().__init__()
        self.__item = item

    def _pretransform(self, value):
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
