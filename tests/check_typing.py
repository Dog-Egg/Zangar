from __future__ import annotations

import dataclasses
from typing import assert_type

import zangar as z

assert_type(z.transform(int).parse("1"), int)
assert_type(z.str().transform(lambda x: len(x)).ensure(lambda x: x > 1).parse("1"), int)
assert_type(z.none().parse(1), None)
assert_type(z.struct({}).ensure(lambda x: "a" in x).parse(object()), dict)
assert_type((z.int() | z.str()).parse(1), int | str)
assert_type(z.list(z.int()).parse([]), list[int])


@dataclasses.dataclass
class Point:
    x: int
    y: int


assert_type(z.dataclass(Point).ensure(lambda _: True).parse({}), Point)
