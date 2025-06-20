from __future__ import annotations

import dataclasses

import zangar as z


def check_transform() -> int:
    return z.transform(int).parse("1")


def check_transform_ensure() -> int:
    return z.str().transform(lambda x: len(x)).ensure(lambda x: x > 1).parse("1")


def check_none() -> None:
    return z.none().parse(1)


def check_struct() -> dict:
    return z.struct({}).ensure(lambda x: "a" in x).parse(object())


def check_union() -> int | str:
    int_or_str = z.int() | z.str()
    return int_or_str.parse(1)


def check_list() -> list[int]:
    return z.list(z.int()).parse([1, 2])


@dataclasses.dataclass
class Point:
    x: int
    y: int


def check_dataclass():
    return z.dataclass(Point).parse({"x": 1, "y": 2})


def check_dataclass_ensure():
    def ensure_fn(o: Point):
        return o.x > 0

    return z.dataclass(Point).ensure(ensure_fn).parse({"x": 1, "y": 2})
