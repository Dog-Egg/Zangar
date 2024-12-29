# pylint: disable=invalid-name
from __future__ import annotations

import builtins
import typing as t
from collections.abc import Callable

from . import _core as z

__all__ = [
    "ensure",
    "transform",
    "str",
    "int",
    "float",
    "bool",
    "none",
    "any",
    "datetime",
    "object",
    "field",
    "list",
]

str = z.String
int = z.Integer
float = z.Float
bool = z.Boolean
none = z.NoneType
any = z.Any
object = z.Object
field = z.Field
list = z.List
datetime = z.Datetime


T = t.TypeVar("T")


def ensure(func: Callable[[T], builtins.bool], /, **kwargs):
    return z.Schema().ensure(func, **kwargs)


def transform(func: Callable[[t.Any], T], /, **kwargs):
    return z.Schema().transform(func, **kwargs)
