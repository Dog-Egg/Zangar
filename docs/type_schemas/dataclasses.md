## `dataclass`

The `dataclass` method converts a [`dataclasses.dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass) into a Zangar schema for data validation, and the resulting output is an instance of that dataclass.

## Create a dataclass

```python
from dataclasses import dataclass

import zangar as z

@dataclass
class InventoryItem:
    """Class for keeping track of an item in inventory."""
    name: str
    unit_price: float
    quantity_on_hand: int = 0
```

```py
# It's good!
>>> z.dataclass(InventoryItem).parse({'name': "necklace", 'unit_price': 12.50})
InventoryItem(name='necklace', unit_price=12.5, quantity_on_hand=0)

```

```py
# It's bad! because unit_price is not a float.
>>> z.dataclass(InventoryItem).parse({'name': "necklace", 'unit_price': '12.50'})
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['unit_price'], 'msgs': ['Expected float, received str']}]

```

## Nested dataclasses

```py
>>> from typing import List

>>> @dataclass
... class Point:
...      x: int
...      y: int

>>> @dataclass
... class C:
...      mylist: List[Point]

>>> z.dataclass(C).parse({'mylist': [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]})
C(mylist=[Point(x=1, y=2), Point(x=3, y=4)])

>>> z.dataclass(C).parse({'mylist': [{'x': 1, 'y': 2}, {'x': 3, 'y': '4'}]})
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['mylist', 1, 'y'], 'msgs': ['Expected int, received str']}]

```

## Customize the field schema

```python
from typing import List
from dataclasses import dataclass, field

@dataclass
class C:
    my_list: List[int] = field(metadata={'zangar': {'schema': z.to.list(z.to.int())}})

assert z.dataclass(C).parse(
        {"my_list": (1, '2', 3)}
    ) == C(my_list=[1, 2, 3])
```

## As a struct

`zangar.dataclass` is implemented using `struct`, so you only need to call `.struct` to get the internal struct schema.

```python
@dataclass
class C:
    a: int
    b: int
    c: int

assert z.dataclass(C).struct.pick_fields(['a', 'b']).parse(
        {'a': 1, 'b': 2, 'c': 3}
    ) == {'a': 1, 'b': 2}
```