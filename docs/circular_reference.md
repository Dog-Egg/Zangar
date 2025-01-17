When validating data that involves circular references, `ref` can be used to define the parts that are circularly referenced.

For example:

There is a simple tree structure here.

```python
from types import SimpleNamespace
import zangar as z

class Node(SimpleNamespace): ...

tree = Node(
    name='n1',
    children=[
        Node(name='n2'),
        Node(
            name='n3',
            children=[Node(name='n4')]
        ),
])
```

You might naturally think of defining the schema of this tree with the following code.

However, in Python, this definition is incorrect.

```py hl_lines="4"
>>> node_schema = z.object({
...     'name': z.str(),
...     'children': z.field(
...         z.list(node_schema)
...     ).optional()
... })
Traceback (most recent call last):
NameError: name 'node_schema' is not defined

```

The correct approach is to use `ref` to replace the parts that are circularly referenced.

```py hl_lines="4"
>>> node_schema = z.object({
...     'name': z.str(),
...     'children': z.field(
...         z.list(z.ref('node_schema'))
...     ).optional()
... })

>>> node_schema.parse(tree)
{'name': 'n1', 'children': [{'name': 'n2'}, {'name': 'n3', 'children': [{'name': 'n4'}]}]}

```
