from __future__ import annotations

import typing

import zangar as z
from zangar._core import Union
from zangar.dataclass import resolve_complex_type


def test_complex_type():
    assert resolve_complex_type(str) == None
    assert resolve_complex_type(typing.Union[str, None]) == (Union, (str, type(None)))
    assert resolve_complex_type(typing.Optional[str]) == (Union, (str, type(None)))
    assert resolve_complex_type(typing.Union[str, int]) == (Union, (str, int))
    assert resolve_complex_type(typing.List[str]) == (z.list, (str,))
    assert resolve_complex_type(typing.List[typing.Union[str, int]]) == (
        z.list,
        (typing.Union[str, int],),
    )
    assert resolve_complex_type(typing.List) == (z.list, ())
