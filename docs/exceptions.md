<!--
```py
>>> import zangar as z

```
-->

# Exceptions

## ValidationError

### `.format_errors`

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
...     z.struct(
...         {
...             "names": z.list(name_schema),
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
