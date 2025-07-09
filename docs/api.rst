API Reference
=============

.. autoclass:: zangar.Schema
.. autofunction:: zangar.ensure
.. autofunction:: zangar.transform
.. autofunction:: zangar.ref
.. autofunction:: zangar.isinstance

Base Types
----------

.. automodule:: zangar
    :members: str, int, float, bool, datetime, list, none, any

Conversions
-----------

.. automodule:: zangar.to
    :members: str, int, float, datetime

Structures
----------

.. autoclass:: zangar.struct
.. autoclass:: zangar.mstruct
.. autoclass:: zangar.dataclass
.. autoclass:: zangar.field
.. autofunction:: zangar.required_fields
.. autofunction:: zangar.optional_fields
.. autofunction:: zangar.pick_fields
.. autofunction:: zangar.omit_fields

Private
-------

.. autoclass:: zangar._core.SchemaBase

.. automodule:: zangar._types
    :members: 
    :show-inheritance:
    :imported-members:

Messages
--------

.. autoclass:: zangar.MessageContext
    :members:
.. autoclass:: zangar.DefaultMessage
