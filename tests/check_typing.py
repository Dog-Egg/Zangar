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
assert_type(z.isinstance(int).parse(""), int)
assert_type(z.str().strip().parse(""), str)
assert_type(z.str().min(0).parse(""), str)
assert_type(z.str().max(0).parse(""), str)
assert_type(z.int().gte(0).parse(1), int)
assert_type(z.int().gt(0).parse(1), int)
assert_type(z.int().lte(0).parse(1), int)
assert_type(z.int().lt(0).parse(1), int)
assert_type(z.float().gte(0.0).parse(1.0), float)
assert_type(z.float().gt(0.0).parse(1.0), float)
assert_type(z.float().lte(0.0).parse(1.0), float)
assert_type(z.float().lt(0.0).parse(1.0), float)


@dataclasses.dataclass
class Point:
    x: int
    y: int


assert_type(z.dataclass(Point).ensure(lambda _: True).parse({}), Point)
