```{toctree}
:hidden:

type_schemas/index
messages
circular_reference
exceptions
openapi
api
```

# Getting started

Uses simple, composable logic to validate data.

## Installation

```sh
pip install git+https://github.com/Dog-Egg/Zangar
```

## Usage

```py
>>> import zangar as z

```

Zangar's core validation logic for data consists of only two methods, defined as [`ensure`](#ensure) and [`transform`](#transform), which can be combined through chain-like calls.

For example:

```py
>>> name_to_greeting = (
...     z.ensure(lambda s: isinstance(s, str))
...     .transform(lambda s: s.title())
...     .transform(lambda s: f"Hello {s}")
...     .ensure(lambda s: "!" not in s)
... )

>>> name_to_greeting.parse('john')
'Hello John'

>>> name_to_greeting.parse('john!')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Invalid value']}]

```

All other validation methods provided by Zangar are implemented by combining `ensure` and `transform`.

## Schema

### `.ensure`

`ensure` is used to define custom data validation rules and should return a boolean value.

```py
>>> my_data = z.ensure(lambda s: len(s) > 5)

>>> my_data.parse('hello')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Invalid value']}]

>>> my_data.parse('hello world') # this is OK.
'hello world'

```

#### break_on_failure

When multiple `ensure` methods are adjacent, even if one `ensure` fails, the subsequent `ensure` methods will still be executed by default.

```py
>>> try:
...   (
...     z.ensure(lambda s: len(s) >= 6, message='Password must be at least 6 characters')
...      .ensure(lambda s: "!" not in s, message='Password must not contain !')
...   ).parse('ab12!')
... except z.ValidationError as e:
...   e.format_errors()
...
[{'msgs': ['Password must be at least 6 characters', 'Password must not contain !']}]

```

The `break_on_failure` parameter controls whether the validation should terminate upon failure, preventing further validation from being propagated.

```py
>>> try:
...   (
...     z.ensure(lambda s: len(s) >= 6, break_on_failure=True, message='Password must be at least 6 characters')
...      .ensure(lambda s: "!" not in s, message='Password must not contain !')
...   ).parse('ab12!')
... except z.ValidationError as e:
...   e.format_errors()
...
[{'msgs': ['Password must be at least 6 characters']}]

```

### `.transform`

To transform data during parsing, use the `transform` method.

```py
>>> to_int = z.transform(lambda s: int(s))

>>> to_int.parse('10')
10

```

### `.relay`

The `relay` method is simply a shortcut for invoking another schema for parsing using `transform`.
It is equivalent to the following code:

```py
>>> my_int = z.transform(int).relay(z.int())

# equivalent to
>>> my_int = z.transform(int).transform(z.int().parse)

```

### `.parse`

Given any schema, you can call its `.parse` method to check data is valid. If it is, a value is returned with full type information! Otherwise, an error is thrown.

```py
>>> string = z.str()

>>> string.parse("hello")
'hello'

>>> string.parse(123)
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Expected str, received int']}]

```

## Unions

Zangar provides a way to create a union schema using the `|` operator, where the data is parsed sequentially from left to right.

```py
>>> int_or_none = z.int() | z.none()

>>> assert int_or_none.parse(1) == 1
>>> assert int_or_none.parse(None) is None

>>> int_or_none.parse('a')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Expected int, received str', 'Expected NoneType, received str']}]

```

## Typing

`z.Schema` is an interface, you can use `z.Schema[T]` to specify the type of the data. This can be helpful for static type checking.

```py
from typing import TypeVar

T = TypeVar('T')

def your_function(schema: z.Schema[T]) -> T:
    # do something
    return schema.parse(...)
```
