from __future__ import annotations

import zangar as z

r1: int = z.transform(int).parse("1")

r2: int = z.str().transform(lambda x: len(x)).ensure(lambda x: x > 1).parse("1")

r3: None = z.none().parse(None)

r4: dict = z.object({}).ensure(lambda x: "a" in x).parse(object())

int_or_str = z.int() | z.str()
r5: int | str = int_or_str.parse(1)
r5 = int_or_str.parse("1")

str_or_none = z.str() | z.none()
r6: str | None = str_or_none.parse("1")
r6 = str_or_none.parse(None)

r7: list[int] = z.list(z.int()).parse([1, 2])
