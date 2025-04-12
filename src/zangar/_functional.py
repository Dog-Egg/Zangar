from __future__ import annotations

import builtins
import sys
import typing as t
from collections.abc import Callable

from ._core import Schema

__all__ = [
    "ensure",
    "transform",
    "ref",
]


def ref(name: str, /):
    frame = sys._getframe(1)

    def inner(value):
        schema: Schema = frame.f_locals[name]
        return schema.parse(value)

    return Schema().transform(inner)


T = t.TypeVar("T")


def ensure(func: Callable[[T], builtins.bool], /, **kwargs):
    return Schema().ensure(func, **kwargs)


def transform(func: Callable[[t.Any], T], /, **kwargs):
    return Schema().transform(func, **kwargs)
