# Structures

structures are used to parse complex objects and return a dictionary.

## Definitions

Its definition is as follows:

```python
dog = z.struct({
    'name': z.field(z.str()),
    'breed': z.field(z.str()),
})
```

If you do not need to make any changes to the field, you can omit [](#field). The above definition can be simplified to the following code:

```python
dog = z.struct({
    'name': z.str(),
    'breed': z.str(),
})
```

The structure field, when parsing an object, will use its field name to get the value of the key for [Mapping](#collections.abc.Mapping) objects, and the value of the attribute for other objects.

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

## Optional Fields

Fields are required by default, but this method allows them to be made optional.

```py
>>> dog = z.struct({
...     'name': z.str(),
...     'breed': z.field(z.str()).optional(),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido'}

```

It is also possible to provide a default value for the optional field.

```py
>>> dog = z.struct({
...     'name': z.str(),
...     'breed': z.field(z.str()).optional(default='unknown'),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido', 'breed': 'unknown'}

```

## Field Alias

You can assign alias to external data corresponding to field, which will be mapped to field name during parsing.

```py
>>> dog = z.struct({
...   'name': z.field(z.str(), alias='nickname'),
... })

>>> dog.parse({'nickname': 'Fido'})
{'name': 'Fido'}

```

## Extending Fields

You can expand the field in the following way.

```py
>>> dog_with_age = z.struct({
...   **dog.fields,
...   'age': z.int(),
... })

```

## [.ensure_fields](#ensure_fields)

🚧 TODO: Missing description...

```python
my_schema = z.struct({
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

## Change Optional Fields

Two opposite methods, [optional_fields](#zangar.optional_fields) and [required_fields](#zangar.required_fields), are provided to change optional fields.

`.optional_fields`

Based on the current structure schema fields, construct a new structure schema, setting all fields as optional; or set specified fields as optional and the other fields as required. The opposite of [`.required_fields`](#zangar.required_fields).

```python
z.struct(z.optional_fields({
    'username': z.field(z.str()),
    'email': z.field(z.str())
}))

# equivalent to:
z.struct({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
})
```

```python
z.struct(z.optional_fields({
    'username': z.field(z.str()),
    'email': z.field(z.str())
}, ['username']))

# equivalent to:
z.struct({
    'username': z.field(z.str()).optional(),
    'email': z.str()
})
```

`.required_fields`

Based on the current structure schema fields, construct a new structure schema, setting all fields as required; or set specified fields as required and the other fields as optional. The opposite of [`.optional_fields`](#zangar.optional_fields).

```python
z.struct(z.required_fields({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
}))

# equivalent to:
z.struct({
    'username': z.str(),
    'email': z.str()
})
```

```python
z.struct(z.required_fields({
    'username': z.field(z.str()).optional(),
    'email': z.field(z.str()).optional()
}, ['username']))

# equivalent to:
z.struct({
    'username': z.str(),
    'email': z.field(z.str()).optional()
})
```

## Pick or Omit Fields

`.pick_fields`

Construct a new structure schema by selecting the specified fields. The opposite of [`.omit_fields`](#zangar.omit_fields).

```python
z.struct(z.pick_fields({
    'username': z.str(),
    'email': z.str()
}, ['username']))

# equivalent to:
z.struct({
    'username': z.str()
})
```

`.omit_fields`

Construct a new structure schema by excluding the specified fields. The opposite of [`.pick_fields`](#zangar.pick_fields).

```python
z.struct(z.omit_fields({
    'username': z.str(),
    'email': z.str()
}, ['username']))

# equivalent to:
z.struct({
    'email': z.str()
})
```

## Unknown Fields

Only [](#mstruct) can access unknown fields.

Include unknown fields in the parsed result.

```py
>>> z.mstruct({
...     'username': z.str(),
...     'email': z.str()
... }, unknown='include').parse({
...     'username': 'john',
...     'email': 'john@example.com',
...     'age': 18
... })
{'username': 'john', 'email': 'john@example.com', 'age': 18}

```

Raise an error when encountering unknown fields.

```py
>>> z.mstruct({
...     'username': z.str(),
...     'email': z.str()
... }, unknown='raise').parse({
...     'username': 'john',
...     'email': 'john@example.com',
...     'age': 18
... })
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['age'], 'msgs': ['Unknown field']}]

```