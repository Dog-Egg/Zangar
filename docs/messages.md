## Basic

### Ensurance Messages

Passby a string.

```py
>>> z.ensure(lambda x: len(x) > 5 , message='Too short').parse("hello")
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Too short']}]

```

Passby a function.

```py
>>> z.ensure(lambda x: len(x) > 5 , message=lambda x: f'The ${x} is too short').parse("hello")
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['The $hello is too short']}]

```

### Transformation Messages

Passby a string.

```py
>>> z.transform(int, message='Invalid integer').parse('a')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Invalid integer']}]

```

Passby a function.

```py
>>> z.transform(int, message=lambda x: f'Invalid integer: {x!r}').parse('a')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ["Invalid integer: 'a'"]}]

```

## Type Messages

API like `z.int` and `z.to.int` are implemented based on `ensure` and `transform`, and they also support the above-mentioned custom message mechanism.

```python
z.str(message='Invalid string')
z.int(message='Invalid integer')
z.float(message='Invalid float')
z.to.str(message='Invalid string')
z.to.int(message='Invalid integer')
...
```

## Required field message

```py
>>> z.object({
...     'username': z.field(z.str()).required(message='Username is required.'),
... }).parse({})
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'loc': ['username'], 'msgs': ['Username is required.']}]

```

!!! warning

    Required field message does not accept a function as its argument.

## Different Messages

Message can be in any form you need, not just a string.

```python
import enum
import json


class ErrorCode(enum.Enum):
    REQUIRED = 1001, 'This field is required.'
    IS_EMAIL = 1002, 'Must provide a valid email address.'

def custom_default(o):
    if isinstance(o, enum.Enum):
        return {'code': o.value[0], 'description': o.value[1]}
    raise TypeError(f'Cannot serialize object of {type(obj)}')

schema = z.object({
    'username': z.field(z.str()).required(message=ErrorCode.REQUIRED)
})
```

```py
>>> try:
...     schema.parse({})
... except z.ValidationError as e:
...     print(json.dumps(e.format_errors(), default=custom_default, indent=2))
[
  {
    "loc": [
      "username"
    ],
    "msgs": [
      {
        "code": 1001,
        "description": "This field is required."
      }
    ]
  }
]

```
