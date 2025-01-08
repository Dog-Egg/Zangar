from __future__ import annotations

import abc
import typing as t
from collections.abc import Callable

from ._common import empty
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
