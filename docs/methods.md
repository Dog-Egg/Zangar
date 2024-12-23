<!--
```py
>>> import zangar as z

```
-->

Zangar provides convenient validation methods for some types.

For example:

```py
>>> z.str().strip().min(1).max(20).parse(' hello ')
'hello'

# equivalent to:
>>> z.str().transform(str.strip).ensure(lambda x: len(x) >= 1).ensure(lambda x: len(x) <= 20).parse(' hello ')
'hello'

```

## String

### `.max`

Validate the maximum length of a string.

```py
>>> string = z.str().max(20)

# equivalent to:
>>> string = z.str().ensure(lambda x: len(x) <= 20)

```

### `.min`

Validate the minimum length of a string.

```py
>>> string = z.str().min(1)

# equivalent to:
>>> string = z.str().ensure(lambda x: len(x) >= 1)

```

### `.strip`

Trim whitespace from both ends.

```py
>>> z.str().strip().parse(' string ')
'string'

# equivalent to:
>>> z.str().transform(str.strip).parse(' string ')
'string'

```

## Number

### `.gt`

Validate the number is greater than a given value.

```py
>>> number = z.int().gt(0)

# equivalent to:
>>> number = z.int().ensure(lambda x: x > 0)

```

### `.gte`

Validate the number is greater than or equal to a given value.

```py
>>> number = z.int().gte(0)

# equivalent to:
>>> number = z.int().ensure(lambda x: x >= 0)

```

### `.lt`

Validate the number is less than a given value.

```py
>>> number = z.int().lt(10)

# equivalent to:
>>> number = z.int().ensure(lambda x: x < 10)

```

### `.lte`

Validate the number is less than or equal to a given value.

```py
>>> number = z.int().lte(10)

# equivalent to:
>>> number = z.int().ensure(lambda x: x <= 10)

```
