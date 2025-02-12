## Primitives

```python
z.str()        # Validate that the data is of type `str`.
z.int()        # Validate that the data is of type `int`.
z.float()      # Validate that the data is of type `float`.
z.bool()       # Validate that the data is of type `bool`.
z.none()       # Validate that the data is of type `None`.
z.datetime()   # Validate that the data is of type `datetime.datetime`.
z.any()        # Validate that the data is of any type.
```

These schemas are simple type validations and do not provide type conversion. Here's an equivalent example:

```python
# z.str() is equivalent to:
z.ensure(lambda x: isinstance(x, str))
```

### `list`

```py
>>> z.list(z.transform(int)).parse(['1', 2, '3'])
[1, 2, 3]

# equivalent to:
>>> z.ensure(lambda x: isinstance(x, list)).transform(lambda x: [z.transform(int).parse(i) for i in x]).parse(['1', 2, '3'])
[1, 2, 3]

```

## Conversions

The available type conversions are located in the namespace named `to`.

### `str`

```py
>>> assert z.to.str().parse(1) == '1'

# equivalent to:
>>> assert z.transform(str).parse(1) == '1'

```

### `int`

```py
>>> assert z.to.int().parse('1') == 1
>>> assert z.to.int().parse('1.0') == 1

>>> z.to.int().parse(1.2)
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['1.2 is not a valid integer']}]

```

This is the conversion function for `int`.

```py
{{ source_code('zangar._conversions.int_convert') }}

```

### `float`

```py
>>> assert z.to.float().parse('1.0') == 1.0

# equivalent to:
>>> assert z.transform(float).parse('1.0') == 1.0

```

### `list`

```py
>>> assert z.to.list().parse((1, 2, 3)) == [1, 2, 3]

# equivalent to:
>>> assert z.transform(list).parse((1, 2, 3)) == [1, 2, 3]

```

### `datetime`

It can parse a [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) datetime string.

```py
>>> z.to.datetime().parse('20040503T173008+08')
datetime.datetime(2004, 5, 3, 17, 30, 8, tzinfo=tzoffset(None, 28800))

>>> z.to.datetime().parse('2004-W19')
datetime.datetime(2004, 5, 3, 0, 0)

```
