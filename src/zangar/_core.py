from __future__ import annotations

import abc
import typing as t
from collections.abc import Callable

from ._common import empty
from ._messages import DefaultMessage, get_message
from .exceptions import ValidationError

T = t.TypeVar("T")
P = t.TypeVar("P")


class SchemaBase(t.Generic[T], abc.ABC):
    _meta: dict

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

    @abc.abstractmethod
    def _iter(self) -> t.Generator[SchemaBase[t.Any], None, None]: ...


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


_USER_META_KEYS = {
    "oas",
}


class Schema(SchemaBase[T]):

    def __init__(
        self,
        *,
        prev: Schema | None = None,
        validator: TransformationValidator | EnsuranceValidator | None = None,
        meta: dict | None = None,
    ):
        self.__prev = prev
        self._validator = validator

        # check meta
        if meta is not None:
            for key in meta:
                if isinstance(key, str) and key.startswith("$"):
                    continue
                if key not in _USER_META_KEYS:
                    raise ValueError(f"Invalid meta key: {key}")
        self._meta: dict = meta or {}

    def __or__(self, other: SchemaBase[P]) -> Union[T, P]:
        return Union(self, other)

    def ensure(
        self,
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
        break_on_failure: bool = False,
        meta: dict | None = None,
    ) -> Schema[T]:
        def validate(value):
            if not func(value):
                raise ValidationError(
                    get_message(
                        message=(
                            message
                            if message is not None
                            else DefaultMessage(name="ensure_failed")
                        ),
                        value=value,
                    )
                )

        return Schema(
            prev=self,
            validator=EnsuranceValidator(validate, break_on_failure),
            meta=meta,
        )

    def transform(
        self,
        func: Callable[[T], P],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
        meta: dict | None = None,
    ):
        def validate(value):
            try:
                return func(value)
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise e
                raise ValidationError(
                    get_message(
                        message=(
                            message
                            if message is not None
                            else DefaultMessage(name="transform_failed", ctx={"exc": e})
                        ),
                        value=value,
                    )
                ) from e

        return Schema[P](
            prev=self, validator=TransformationValidator(validate), meta=meta
        )

    def relay(self, other: SchemaBase[P], /):
        return self.transform(other.parse)

    def _iter(self):
        if self.__prev is not None:
            yield from self.__prev._iter()
        yield self

    def parse(self, value, /) -> T:
        error = ValidationError(empty)
        for n in self._iter():
            validator = n._validator
            if isinstance(validator, EnsuranceValidator):
                try:
                    validator(value)
                except ValidationError as e:
                    error._set_peer(e)
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
        self._schemas = (a, b)

        def transform(value):
            error = ValidationError(empty)
            for item in self._schemas:
                try:
                    return item.parse(t.cast(t.Any, value))
                except ValidationError as e:
                    error._set_peer(e)
            raise error

        super().__init__(
            prev=Schema().transform(transform),
        )

    def __repr__(self) -> str:
        items: list[str] = []
        for item in self._schemas:
            if isinstance(item, Union):
                items.append(repr(item))
            else:
                items.append(item.__class__.__name__)
        return " | ".join(items)


class JoinSchema(Schema):
    def __init__(self, *schemas: SchemaBase):
        self.__schemas = schemas
        super().__init__()

    def _iter(self):
        for schema in self.__schemas:
            yield from schema._iter()
        yield from super()._iter()
