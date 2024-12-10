# Tutorial

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

### `ensure`

`ensure` is used to define custom data validation rules and should return a boolean value.

```py
>>> my_data = z.ensure(lambda s: len(s) > 5)

>>> my_data.parse('hello')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Invalid value']}]

>>> my_data.parse('hello world') # this is OK.
'hello world'

```

#### message

A `message` can be provided for a validation method, which will be used when validation fails. If the `message` is a callable object, its return value will be used as the `message`.

```py
>>> my_data = z.ensure(lambda s: len(s) > 5, message='Too short')

>>> my_data.parse('hello')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Too short']}]

```

Use a callable object as the message.

```py
>>> my_data = (
...   z.ensure(
...       lambda s: len(s) > 5,
...       message=lambda s: f"The {s!r} is too short"
...   )
... )

>>> my_data.parse('hello')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ["The 'hello' is too short"]}]

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

### `transform`

To transform data during parsing, use the `transform` method.

```py
>>> to_int = z.transform(lambda s: int(s))

>>> to_int.parse('10')
10

```

#### message

A `message` can be provided for a transformation method, which will be used when transformation fails. If the `message` is a callable object, its return value will be used as the `message`.

```py
>>> z.transform(lambda x: int(x), message='Invalid integer').parse('a')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['Invalid integer']}]

```

Use a callable object as the message.

```py
>>> z.transform(lambda x: int(x), message=lambda x: f'Invalid integer: {x!r}').parse('a')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ["Invalid integer: 'a'"]}]

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

## Types

The various type schemas defined below are implemented using [`transform`](#transform) and [`ensure`](#ensure), which means you can completely define your own type schemas. For example:

```py
>>> z.str().min(1).max(20).parse('Hello')
'Hello'

# equivalent to:
>>> (
...   z.ensure(lambda x: isinstance(x, str), break_on_failure=True)
...   .ensure(lambda x: len(x) >= 0)
...   .ensure(lambda x: len(x) <= 20)
... ).parse('Hello')
'Hello'

```

### String

```py
>>> z.str().parse('string')
'string'

```

#### methods

```py
>>> string = z.str().min(1) # Validate the minimum length of a string.
>>> string = z.str().max(20) # Validate the maximum length of a string.

```

### Number

```py
# Integer
>>> z.int().parse(1)
1

# Float
>>> z.float().parse(1.0)
1.0

```

#### methods

```py
>>> number = z.int().gt(0)  # Validate the number is greater than 0.
>>> number = z.int().gte(0) # Validate the number is greater than or equal to 0.
>>> number = z.int().lte(10) # Validate the number is less than or equal to 10.
>>> number = z.int().lt(10) # Validate the number is less than 10.

```

### Boolean

```py
>>> z.bool().parse(True)
True

```

### None

```py
>>> z.none().parse(None)

```

### Any

```py
>>> any = z.any()

```

### Object

```py
>>> dog = z.object({
...     'name': z.field(z.str()),
...     'breed': z.field(z.str()),
... })

```

#### Field

##### `alias`

You can assign alias to external data corresponding to field, which will be mapped to field name during parsing.

```py
>>> dog = z.object({
...   'name': z.field(z.str(), alias='nickname'),
... })

>>> dog.parse({'nickname': 'Fido'})
{'name': 'Fido'}

```

##### `.optional`

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

#### `.extend`

You can add additional fields to an object schema with the .extend method.

```py
>>> dog_with_age = dog.extend({
...   'age': z.field(z.int()),
... })

```

### List

```py
>>> z.list(z.transform(int)).parse(['1', 2, '3'])
[1, 2, 3]

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

## Exceptions

### ValidationError

#### `.format_errors`

```py
>>> name_schema = (
...     z.str()
...     .ensure(
...         lambda x: len(x) >= 5,
...         message="The name is at lease 5 characters long",
...     )
...     .ensure(
...         lambda s: "!" not in s,
...         message="The name cannot contain !",
...     )
... )

>>> try:
...     z.object(
...         {
...             "names": z.field(
...                 z.list(name_schema)
...             ),
...         }
...     ).parse(
...         {
...             "names": ["Isabella", "Olivia", "Ava!"],
...         }
...     )
... except z.ValidationError as e:
...     e.format_errors()
...
[{'loc': ['names', 2], 'msgs': ['The name is at lease 5 characters long', 'The name cannot contain !']}]

```

Return result type

```ts
type Errors = Array<{
  loc?: Array<string | number>;
  msgs: Array<any>;
}>;
```
