# pylint: disable=invalid-name
from __future__ import annotations

import builtins
import typing as t
from collections.abc import Callable

from zangar._core import Schema

from . import _types

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
    "struct",
    "field",
    "list",
]

str = _types.String
int = _types.Integer
float = _types.Float
bool = _types.Boolean
none = _types.NoneType
any = _types.Any
object = _types.Object
struct = _types.Struct
field = _types.Field
list = _types.List
datetime = _types.Datetime


T = t.TypeVar("T")


def ensure(func: Callable[[T], builtins.bool], /, **kwargs):
    return Schema().ensure(func, **kwargs)


def transform(func: Callable[[t.Any], T], /, **kwargs):
    return Schema().transform(func, **kwargs)
