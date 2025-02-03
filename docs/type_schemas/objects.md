## `object`

`object` is a schema with fields, it can parse any object and return a dict.

```python
dog = z.object({
    'name': z.field(z.str()),
    'breed': z.field(z.str()),
})
```

If you do not need to make any changes to the field, you can omit `field`. The above definition can be simplified to the following code:

```python
dog = z.object({
    'name': z.str(),
    'breed': z.str(),
})
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

### `.extend`

You can add additional fields to an object schema with the `.extend` method.

```py
>>> dog_with_age = dog.extend({
...   'age': z.int(),
... })

```

### `.ensure_fields`

```python
my_schema = z.object({
    'start_time': z.field(z.datetime()),
    'end_time': z.field(z.datetime()),
})
```

```py
>>> from datetime import datetime

>>> my_schema.ensure(lambda data: data['end_time'] > data['start_time'], message='The end time cannot be later than the start time').parse({
...     'start_time': datetime(2000, 1, 2),
...     'end_time': datetime(2000, 1, 1),
... })
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['The end time cannot be later than the start time']}]

```

```py
>>> my_schema.ensure_fields(['end_time'], lambda data: data['end_time'] > data['start_time'], message='The end time cannot be later than the start time').parse({
...     'start_time': datetime(2000, 1, 2),
...     'end_time': datetime(2000, 1, 1),
... })
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['end_time'], 'msgs': ['The end time cannot be later than the start time']}]

```

### `.optional_fields`

Based on the current object schema fields, construct a new object schema, setting all fields as optional; or set specified fields as optional and the other fields as required. The opposite of [`.required_fields`](#required_fields).

```python
z.object({
    'username': z.str(),
    'email': z.str()
}).optional_fields()

# equivalent to:
z.object({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
})
```

```python
z.object({
    'username': z.str(),
    'email': z.str()
}).optional_fields(['username'])

# equivalent to:
z.object({
    'username': z.field(z.str()).optional(),
    'email': z.str()
})
```

### `.required_fields`

Based on the current object schema fields, construct a new object schema, setting all fields as required; or set specified fields as required and the other fields as optional. The opposite of [`.optional_fields`](#optional_fields).

```python
z.object({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
}).required_fields()

# equivalent to:
z.object({
    'username': z.str(),
    'email': z.str()
})
```

```python
z.object({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
}).required_fields(['username'])

# equivalent to:
z.object({
    'username': z.str(),
    'email': z.field(z.str()).optional()
})
```

### `.pick_fields`

Construct a new object schema by selecting the specified fields. The opposite of [`.omit_fields`](#omit_fields).

```python
z.object({
    'username': z.str(),
    'email': z.str()
}).pick_fields(['username'])

# equivalent to:
z.object({
    'username': z.str()
})
```

### `.omit_fields`

Construct a new object schema by excluding the specified fields. The opposite of [`.pick_fields`](#pick_fields).

```python
z.object({
    'username': z.str(),
    'email': z.str()
}).omit_fields(['username'])

# equivalent to:
z.object({
    'email': z.str()
})
```

## `field`

### alias

You can assign alias to external data corresponding to field, which will be mapped to field name during parsing.

```py
>>> dog = z.object({
...   'name': z.field(z.str(), alias='nickname'),
... })

>>> dog.parse({'nickname': 'Fido'})
{'name': 'Fido'}

```

### `.optional`

Fields are required by default, but this method allows them to be made optional.

```py
>>> dog = z.object({
...     'name': z.str(),
...     'breed': z.field(z.str()).optional(),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido'}

```

It is also possible to provide a default value for the optional field.

```py
>>> dog = z.object({
...     'name': z.str(),
...     'breed': z.field(z.str()).optional(default='unknown'),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido', 'breed': 'unknown'}

```
