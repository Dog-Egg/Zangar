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

## Type messages

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

    If the required field message is a function, the function's argument will be a `None`.

## Different messages

Message can be in any form you need, not just a string.

!!! note

    In practical scenarios, the frontend often needs the backend to provide an error code rather than an exact error message. This is because the frontend may have its own multilingual settings or custom text requirements.

```python
import enum
import json


class ErrorCode(enum.Enum):
    INVALID = 1000, 'Invalid value.'
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

## Modify default messages

The default messages in Zangar's validation methods are all string types. Overriding these default messages one by one can be costly. Therefore, Zangar offers a context object that allows modifying default messages wherever needed.

```python
import zangar as z

class MyDefaultMessages(z.DefaultMessages):
    def default(self, name: str, value, ctx: dict):
        if name == 'field_required':
            return {
                'error': 1001,
                'reason': 'This field is required.'
            }
        return {
            'error': 1000,
            'reason': super().default(name, value, ctx),
        }
```

```py
>>> with MyDefaultMessages():
...     try:
...         z.object({
...             'username': z.field(z.str().min(6)),
...             'password': z.field(z.str())
...         }).parse({'username': 'user'})
...     except z.ValidationError as e:
...         print(json.dumps(e.format_errors(), indent=2))
[
  {
    "loc": [
      "username"
    ],
    "msgs": [
      {
        "error": 1000,
        "reason": "The minimum length of the string is 6"
      }
    ]
  },
  {
    "loc": [
      "password"
    ],
    "msgs": [
      {
        "error": 1001,
        "reason": "This field is required."
      }
    ]
  }
]

```

This is the source code for Zangar `DefaultMessages.default`.

```py
{{ source_code('zangar._messages:DefaultMessages.default') }}
```
