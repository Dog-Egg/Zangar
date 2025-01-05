from __future__ import annotations

import typing

import zangar as z
from zangar._core import Union
from zangar.dataclass import Converter


class C:
    simple: str
    a: typing.Union[str, None]
    b: typing.Optional[str]
    c: typing.Union[str, int]
    d: typing.List[str]
    e: typing.List[typing.Union[str, int]]
    f: typing.List


def test_complex_type():
    hints = typing.get_type_hints(C)
    assert Converter().resolve_complex_type(hints["simple"]) == None
    assert Converter().resolve_complex_type(hints["a"]) == (Union, (str, type(None)))
    assert Converter().resolve_complex_type(hints["b"]) == (Union, (str, type(None)))
    assert Converter().resolve_complex_type(hints["c"]) == (Union, (str, int))
    assert Converter().resolve_complex_type(hints["d"]) == (z.list, (str,))
    assert Converter().resolve_complex_type(hints["e"]) == (
        z.list,
        (typing.Union[str, int],),
    )
    assert Converter().resolve_complex_type(hints["f"]) == (z.list, ())
