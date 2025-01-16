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

## `@dc.field`

Used to customize the field.

```python
@dataclass
class InventoryItem:
    """Class for keeping track of an item in inventory."""
    name: str
    unit_price: float
    quantity_on_hand: int = 0

    @z.dc.field('unit_price')
    @classmethod
    def customize_unit_price(cls, schema):
        return z.transform(float)

assert z.dataclass(InventoryItem).parse(
        {"name": "necklace", "unit_price": "12.50"}
    ) == InventoryItem(name="necklace", unit_price=12.5, quantity_on_hand=0)
```

## `@dc.ensure_fields`

```python
from datetime import datetime

@dataclass
class TimeRange:
    start: datetime
    end: datetime

    @z.dc.ensure_fields(['end'], message='The end must be after the start')
    def check_range(self):
        return self.end > self.start
```

```py
>>> z.dataclass(TimeRange).parse({'start': datetime(2000, 1, 2), 'end': datetime(2000, 1, 1)})
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['end'], 'msgs': ['The end must be after the start']}]

```
