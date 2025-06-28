Messages
========

Zangar provides a fully customizable message management system. You can write your own custom messages or modify Zangar's default messages.

Custom Messages
---------------

Functions like `zangar.ensure`, `zangar.transform`, `zangar.int`, `zangar.to.int`, etc., all accept a ``message`` keyword argument to customize messages.

For example:

.. doctest:: python

    >>> z.ensure(lambda x: len(x) > 5, message="Too short").parse("hello")
    Traceback (most recent call last):
    zangar.exceptions.ValidationError: [{'msgs': ['Too short']}]

You can also pass a function, which will receive the parsed value as its argument, allowing you to construct clearer messages.

.. doctest:: python

    >>> z.int(message=lambda x: f"I need an integer instead of {x!r}").parse("hello")
    Traceback (most recent call last):
    zangar.exceptions.ValidationError: [{'msgs': ["I need an integer instead of 'hello'"]}]

Required Field Messages
-----------------------

Required fields can also have custom messages as shown below.

.. doctest:: python

    >>> z.struct({
    ...     'username': z.field(z.str()).required(message='Username is required.'),
    ... }).parse({})
    Traceback (most recent call last):
    zangar.exceptions.ValidationError: [{'loc': ['username'], 'msgs': ['Username is required.']}]

.. warning::

    If the message for a required field is a function, since there is no corresponding parsed value, the function will receive `None` as its argument.

Not Just Strings
----------------

Messages can be any type you want (except `None`), not just strings.

.. doctest:: python

    >>> z.struct({
    ...     'username': z.field(z.str()).required(message={'code': 1001, 'description': 'This field is required.'}),
    ... }).parse({})
    Traceback (most recent call last):
    zangar.exceptions.ValidationError: [{'loc': ['username'], 'msgs': [{'code': 1001, 'description': 'This field is required.'}]}]

Modifying Default Messages
--------------------------

Zangar's built-in validation methods all have default messages, but they may not be what you want. Zangar provides a way to modify default messages via a context object, so you can change the default messages where needed.

.. code-block:: python

    class MyMessageContext(z.MessageContext):
        def process_message(self, message):
            if isinstance(message, z.DefaultMessage):
                if message.key == 'field_required':
                    return 'Required field'
            return super().process_message(message)

.. doctest:: python

    >>> with MyMessageContext():
    ...     z.struct({
    ...         'username': z.field(z.str()).required(),
    ...     }).parse({})
    Traceback (most recent call last):
    zangar.exceptions.ValidationError: [{'loc': ['username'], 'msgs': ['Required field']}]

Zangar's default messages are wrapped in a `zangar.DefaultMessage` object. It contains additional information that can be used to customize messages.

Below is a list of the built-in default messages:

.. default-messages-table::