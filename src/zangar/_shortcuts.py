from __future__ import annotations

import builtins
import typing as t
from collections.abc import Callable

from zangar._core import Schema

__all__ = [
    "ensure",
    "transform",
]


T = t.TypeVar("T")


def ensure(func: Callable[[T], builtins.bool], /, **kwargs):
    return Schema().ensure(func, **kwargs)


def transform(func: Callable[[t.Any], T], /, **kwargs):
    return Schema().transform(func, **kwargs)
