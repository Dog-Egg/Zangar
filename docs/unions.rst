Unions
======

Unions allow you to validate data that can be one of several different types. Zangar provides powerful union validation through the ``|`` operator, enabling flexible data validation while maintaining type safety.

Basic Unions
-----------------

The simplest way to create a union is using the ``|`` operator between two schemas:

.. code-block:: python

    import zangar as z

    # A value that can be either an integer or a string
    int_or_str = z.int() | z.str()

    # Parse different types
    assert int_or_str.parse(42) == 42
    assert int_or_str.parse("hello") == "hello"

    # Validation fails if neither type matches
    try:
        int_or_str.parse([1, 2, 3])  # list is neither int nor str
    except z.ValidationError as e:
        print(e.format_errors())
        # [
        #     {'msgs': ['Expected int, received list']},
        #     {'msgs': ['Expected str, received list']}
        # ]

Multiple Unions
---------------

You can chain multiple types together to create unions with more than two options:

.. code-block:: python

    # A value that can be int, str, or bool
    multi_type = z.int() | z.str() | z.bool()

    assert multi_type.parse(42) == 42
    assert multi_type.parse("hello") == "hello"
    assert multi_type.parse(True) == True

Union with None (Optional Values)
----------------------------------

A common pattern is to make a value optional by unioning it with ``None``:

.. code-block:: python

    # Optional integer
    optional_int = z.int() | z.none()

    assert optional_int.parse(42) == 42
    assert optional_int.parse(None) is None

    # Optional string with validation
    optional_name = z.str().min(2) | z.none()

    assert optional_name.parse("John") == "John"
    assert optional_name.parse(None) is None

    try:
        optional_name.parse("A")  # Too short
    except z.ValidationError:
        pass  # Validation fails

Complex Unions
--------------

Unions can include complex schemas like structures and lists:

.. code-block:: python

    # Union of different data structures
    user_data = z.struct({
        'name': z.str(),
        'age': z.int()
    }) | z.struct({
        'username': z.str(),
        'email': z.str()
    })

    # Can parse either structure
    user1 = user_data.parse({'name': 'John', 'age': 30})
    user2 = user_data.parse({'username': 'john_doe', 'email': 'john@example.com'})

    # Union with lists
    list_or_single = z.list(z.str()) | z.str()

    assert list_or_single.parse(['a', 'b', 'c']) == ['a', 'b', 'c']
    assert list_or_single.parse('single') == 'single'

Validation Order and Error Handling
------------------------------------

Zangar tries each schema in the union from left to right. If all schemas fail, it collects all validation errors:

.. code-block:: python

    schema = z.int().gt(0) | z.str().min(5)

    # First schema succeeds
    assert schema.parse(10) == 10

    # Second schema succeeds
    assert schema.parse("hello world") == "hello world"

    # Both schemas fail - shows all errors
    try:
        schema.parse(-5)  # Negative int fails first schema
    except z.ValidationError as e:
        print(e.format_errors())
        # [
        #     {'msgs': ['The value should be greater than 0']},
        #     {'msgs': ['Expected str, received int']}
        # ]

    try:
        schema.parse("hi")  # Short string fails both schemas
    except z.ValidationError as e:
        print(e.format_errors())
        # [
        #     {'msgs': ['Expected int, received str']},
        #     {'msgs': ['The value should be at least 5 characters long']}
        # ]

Transformations with Unions
--------------------------------

You can apply transformations to unions, which will be applied after successful validation:

.. code-block:: python

    # Transform the result regardless of which type matched
    schema = (z.int() | z.str()).transform(lambda x: f"Value: {x}")

    assert schema.parse(42) == "Value: 42"
    assert schema.parse("hello") == "Value: hello"

    # Transform only affects successful parsing
    number_or_default = (z.int() | z.transform(lambda _: 0))

    assert number_or_default.parse(42) == 42
    assert number_or_default.parse("anything") == 0
