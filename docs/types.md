<!--
```py
>>> import zangar as z

```
-->

## Primitives

```
>>> my_str = z.str()       # Validate that the data is of type `str`.
>>> my_int = z.int()       # Validate that the data is of type `int`.
>>> my_float = z.float()   # Validate that the data is of type `float`.
>>> my_bool = z.bool()     # Validate that the data is of type `bool`.
>>> my_none = z.none()     # Validate that the data is of type `None`.
>>> my_any = z.any()       # Validate that the data is of any type.

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

```py
>>> dog = z.object({
...     'name': z.field(z.str()),
...     'breed': z.field(z.str()),
... })

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

## Unions

Zangar provides a way to create a union schema using the `|` operator, where the data is parsed sequentially from left to right.

```py
>>> int_or_str = z.int() | z.str()

>>> int_or_str.parse(1)
1

>>> int_or_str.parse('1')
'1'

>>> int_or_str.parse(None)
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Expected int, received NoneType', 'Expected str, received NoneType']}]

```
