`OpenAPI30Compiler`: Compiles a Zangar schema to OpenAPI 3.0.x schema object.

```python
import zangar as z
from zangar.compilation import OpenAPI30Compiler

assert OpenAPI30Compiler().compile(
    z.object({
        "name": z.str(),
        "age": z.int().gte(0),
        "address": z.object({
            "street": z.str(),
            "city": z.str(),
            "state": z.str(),
        })
    })
) == {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'age': {
            'type': 'integer',
            'minimum': 0
        },
        'address': {
            'type': 'object',
            'properties': {
                'street': {'type': 'string'},
                'city': {'type': 'string'},
                'state': {'type': 'string'}
            },
            'required': ['street', 'city', 'state']
        }
    },
    'required': ['name', 'age', 'address']
}
```
