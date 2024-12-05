# Tutorial

## Installation

```sh
pip install git+https://github.com/Dog-Egg/Zangar
```

## Usage

```py
>>> import zangar as z

```

## Schemas

### Schema

#### `.nullable`

A schema is not allowed to be `None` by default, you need to use `Nullable` to make it accept `None`.

```py
>>> nullable_str = z.Nullable(z.String())
>>> nullable_str.parse(None)

# equivalent to
>>> nullable_str = z.String().nullable()

```

#### `.refine`

`refine` is used to define custom data validation rules and should return a boolean value.

```py
>>> my_string = z.String().refine(lambda s: len(s) > 5, message='too short')

>>> my_string.parse('hello')
Traceback (most recent call last):
zangar.exceptions.ValidationError: [{'msgs': ['too short']}]

>>> my_string.parse('hello world') # this is OK.
'hello world'

```

#### `.transform`

To transform data after parsing, use the `transform` method.

```py
>>> str_to_len = z.String().transform(lambda s: len(s))

>>> str_to_len.parse('string')
6

```

#### Relationship to refinements

Transforms and refinements can be interleaved. These will be executed in the order they are declared.

```py
>>> name_to_greeting = (
...     z.String()
...     .transform(lambda s: s.title())
...     .refine(lambda s: len(s) > 3)
...     .transform(lambda s: f"Hello {s}")
...     .refine(lambda s: "!" not in s)
... )

>>> name_to_greeting.parse('john')
'Hello John'

```

### Object

```py
>>> dog = z.Object({
...     'name': z.Field(z.String()),
...     'breed': z.Field(z.String()),
... })

```

#### Field

##### `alias`

You can assign alias to external data corresponding to field, which will be mapped to field name during parsing.

```py
>>> pagination = z.Object({
...   'page_size': z.Field(z.Integer(), alias='pageSize'),
... })

>>> pagination.parse({'pageSize': 10})
{'page_size': 10}

```

##### `.optional`

Fields are required by default, but this method allows them to be made optional.

```py
>>> dog = z.Object({
...     'name': z.Field(z.String()),
...     'breed': z.Field(z.String()).optional(),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido'}

```

It is also possible to provide a default value for the optional field.

```py
>>> dog = z.Object({
...     'name': z.Field(z.String()),
...     'breed': z.Field(z.String()).optional(default='unknown'),
... })

>>> dog.parse({'name': 'Fido'})
{'name': 'Fido', 'breed': 'unknown'}

```

#### `.extend`

You can add additional fields to an object schema with the .extend method.

```py
>>> dog_with_age = dog.extend({
...   'age': z.Field(z.Integer()),
... })

```

### List

```py
>>> z.List(z.Integer()).parse(['1', 2, '3'])
[1, 2, 3]

```

### String

```py
>>> z.String().parse('string')
'string'

```

### Integer

```py
>>> z.Integer().parse('1.0')
1

```

## Exceptions

### ValidationError

#### `.format_errors`

```py
>>> name_schema = (
...     z.String()
...     .refine(
...         lambda x: len(x) >= 5,
...         message="The name is at lease 5 characters long",
...     )
...     .refine(
...         lambda s: "!" not in s,
...         message="The name cannot contain !",
...     )
... )

>>> try:
...     z.Object(
...         {
...             "names": z.Field(
...                 z.List(name_schema)
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
