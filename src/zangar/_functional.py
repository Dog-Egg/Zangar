from __future__ import annotations

import builtins
import sys
import typing as t
from collections.abc import Callable

from ._core import Schema
from ._messages import DefaultMessage

__all__ = [
    "ensure",
    "transform",
    "ref",
    "isinstance",
]


def ref(name: str, /):
    """Create a reference to a schema.

    Args:
        name: The name of the schema.

    Returns:
        A schema that can parse the value using the referenced schema.
    """
    frame = sys._getframe(1)

    def inner(value):
        schema: Schema = frame.f_locals[name]
        return schema.parse(value)

    return Schema().transform(inner)


T = t.TypeVar("T")


def ensure(func: Callable[[T], builtins.bool], /, **kwargs):
    """Ensure that the value satisfies the condition.

    Args:
        func: The function to validate the value.
        message: The error message to display when the validation fails.
    """
    return Schema().ensure(func, **kwargs)


def transform(func: Callable[[t.Any], T], /, **kwargs) -> Schema[T]:
    """Transform the value.

    Args:
        func: The function to transform the value.
        message: The error message to display when the transformation fails.
    """
    return Schema().transform(func, **kwargs)


def isinstance(cls: type[T], /, **kwargs) -> Schema[T]:
    """Validate that the value is an instance of the given class.

    This is equivalent to ``z.ensure(lambda obj: isinstance(obj, cls))``,
        but this function provides more effective type hints.

    Args:
        cls: The class to check.
        message: The error message to display when the validation fails.
    """
    if "message" not in kwargs:
        kwargs.update(
            message=DefaultMessage(name="type_check", ctx={"expected_type": cls})
        )
    return ensure(lambda obj: builtins.isinstance(obj, cls), **kwargs)
