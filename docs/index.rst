.. toctree::
    :hidden:

    getting_started
    structures
    messages
    circular_reference
    exceptions
    openapi
    api

Design Philosophy
=================

Zangar is built around a simple yet powerful philosophy: **composable validation through explicit ordering**. This document outlines the core design principles that make Zangar both intuitive and powerful for data validation and transformation.

Core Principles
---------------

Simple Building Blocks
~~~~~~~~~~~~~~~~~~~~~~~

Zangar's entire validation system is built on just two fundamental operations:

- **ensure**: Validates data without changing it (returns boolean)
- **transform**: Modifies data during parsing

All other validation methods are implemented by combining these two primitives. This design keeps the API surface small while providing unlimited flexibility.

.. code-block:: python

    # All string methods are built on these primitives
    z.str().min(5)        # equivalent to: z.str().ensure(lambda x: len(x) >= 5)
    z.str().strip()       # equivalent to: z.str().transform(lambda x: x.strip())

Explicit Ordering Matters
~~~~~~~~~~~~~~~~~~~~~~~~~~

One of Zangar's most important design decisions is that **the order of operations is explicit and meaningful**. This eliminates ambiguity and gives developers precise control over validation logic.

Consider these two schemas:

.. code-block:: python

    # Validate length BEFORE stripping
    schema1 = z.str().min(1).strip()
    
    # Strip BEFORE validating length  
    schema2 = z.str().strip().min(1)

These behave differently with whitespace-only input:

.. code-block::

    input_value = " "  # single space
    
    # schema1: checks len(" ") >= 1 (✓), then strips to ""
    schema1.parse(" ")  # Returns: ""
    
    # schema2: strips to "", then checks len("") >= 1 (✗)
    schema2.parse(" ")  # Raises: ValidationError

This explicit ordering prevents common bugs and makes validation logic predictable.

Chainable Composition
~~~~~~~~~~~~~~~~~~~~~

Zangar uses method chaining to build complex validation pipelines from simple components. Each method returns a new schema, allowing for functional composition:

.. code-block:: python

    user_name = (
        z.str()
        .transform(lambda s: s.strip())           # Remove whitespace
        .ensure(lambda s: len(s) >= 2)            # Minimum length
        .transform(lambda s: s.title())           # Capitalize
        .ensure(lambda s: s.isalpha())            # Only letters
    )

Type Safety Through Composition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Zangar maintains type information throughout the validation chain. When you transform data, the type signature updates accordingly:

.. code-block:: python

    # str -> int transformation updates types
    string_to_length = z.str().transform(lambda s: len(s))
    # Type: Schema[int]
    
    # Chaining preserves type information
    validated_length = string_to_length.ensure(lambda x: x > 0)
    # Type: Schema[int]

Design Patterns
---------------

Transform-Then-Validate
~~~~~~~~~~~~~~~~~~~~~~~

A common pattern is to clean/normalize data before validation:

.. code-block:: python

    email = (
        z.str()
        .transform(lambda s: s.strip().lower())   # Normalize
        .ensure(lambda s: "@" in s)               # Validate
        .ensure(lambda s: "." in s.split("@")[1]) # Domain has dot
    )

Validate-Then-Transform
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need to ensure data meets criteria before transformation:

.. code-block:: python

    safe_division = (
        z.float()
        .ensure(lambda x: x != 0, message="Cannot divide by zero")  # Safety check
        .transform(lambda x: 1 / x)                                 # Transform
    )
