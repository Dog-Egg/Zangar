from __future__ import annotations

from dataclasses import dataclass

import zangar as z


@dataclass
class Point:
    x: int
    y: int


@dataclass
class C:
    my_list: list[Point]


def test():
    assert z.dataclass(C).parse({"my_list": [{"x": 0, "y": 0}]}) == C([Point(0, 0)])
