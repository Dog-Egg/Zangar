<!--
```py
>>> import zangar as z

```
-->

## Primitives

```
>>> my_str = z.str()             # Validate that the data is of type `str`.
>>> my_int = z.int()             # Validate that the data is of type `int`.
>>> my_float = z.float()         # Validate that the data is of type `float`.
>>> my_bool = z.bool()           # Validate that the data is of type `bool`.
>>> my_none = z.none()           # Validate that the data is of type `None`.
>>> my_datatime = z.datetime()   # Validate that the data is of type `datetime`.
>>> my_any = z.any()             # Validate that the data is of any type.

```

These schemas are simple type validations and do not provide type conversion. Here's an equivalent example:

```py
>>> string = z.str()

# equivalent to:
>>> string = z.ensure(lambda x: isinstance(x, str))

```

## List

```py
>>> z.list(z.transform(int)).parse(['1', 2, '3'])
[1, 2, 3]

# equivalent to:
>>> z.ensure(lambda x: isinstance(x, list)).transform(lambda x: [z.transform(int).parse(i) for i in x]).parse(['1', 2, '3'])
[1, 2, 3]

```

## Object

`object` is a schema with fields, it can parse any object and return a dict.

```py
>>> dog = z.object({
...     'name': z.field(z.str()),
...     'breed': z.field(z.str()),
... })

```

The `object` field, when parsing an object, will use its field name to get the value of the key for [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) objects, and the value of the attribute for other objects.

```py
# Parsing a Mapping object

>>> dog.parse({
...     'name': 'Fido',
...     'breed': 'bulldog'
... })
{'name': 'Fido', 'breed': 'bulldog'}

```

```py
# Parsing other objects

>>> from types import SimpleNamespace

>>> obj = SimpleNamespace(name='Fido', breed='bulldog')
>>> dog.parse(obj)
{'name': 'Fido', 'breed': 'bulldog'}

```

### Field

#### `alias`

You can assign alias to external data corresponding to field, which will be mapped to field name during parsing.

```py
>>> dog = z.object({
...   'name': z.field(z.str(), alias='nickname'),
... })

>>> dog.parse({'nickname': 'Fido'})
{'name': 'Fido'}

```

#### `.optional`

Fields are required by default, but this method allows them to be made optional.

```py
>>> dog = z.object({
...     'name': z.field(z.str()),
...     'breed': z.field(z.str()).optional(),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido'}

```

It is also possible to provide a default value for the optional field.

```py
>>> dog = z.object({
...     'name': z.field(z.str()),
...     'breed': z.field(z.str()).optional(default='unknown'),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido', 'breed': 'unknown'}

```

### `.extend`

You can add additional fields to an object schema with the .extend method.

```py
>>> dog_with_age = dog.extend({
...   'age': z.field(z.int()),
... })

```

## Conversions

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

### `list`

```py
>>> assert z.to.list().parse((1, 2, 3)) == [1, 2, 3]

# equivalent to:
>>> assert z.transform(list).parse((1, 2, 3)) == [1, 2, 3]

```
