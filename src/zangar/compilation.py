from __future__ import annotations

from datetime import datetime
from typing import Generator

from zangar._core import Schema


class OpenAPI30Compiler:
    def compile(self, schema):
        return self._compile(schema)

    # pylint: disable=too-many-branches
    def _compile(self, schema: Schema, parent: dict | None = None):
        rv: dict = {}
        for meta in _iterate_meta(schema):
            if "type" in meta:
                if meta["type"] is type(None):
                    if isinstance(parent, dict):
                        parent["nullable"] = True
                    else:
                        rv.update(
                            enum=[None],
                        )
                else:
                    if meta["type"] is datetime:
                        rv.update(
                            type="string",
                            format="date-time",
                        )
                    elif meta["type"] is object:
                        rv.update(nullable=True)  # any type
                    else:
                        rv["type"] = {
                            str: "string",
                            int: "integer",
                            float: "number",
                            bool: "boolean",
                        }[meta["type"]]
            if "item" in meta:
                rv.update(
                    type="array",
                    items=self._compile(meta["item"]),
                )
            if "fields" in meta:
                properties = {}
                required = []
                for name, field in meta["fields"].items():
                    key = name if field._alias is None else field._alias
                    properties[key] = self._compile(field._schema, rv)
                    if field._default is not field._empty and not callable(
                        field._default
                    ):
                        properties[key].update(default=field._default)
                    if field._required:
                        required.append(key)
                rv.update(type="object")
                if properties:
                    rv.update(properties=properties)
                if required:
                    rv.update(required=required)
            if "union" in meta:
                results = list(
                    filter(lambda i: i, [self._compile(s, rv) for s in meta["union"]])
                )
                if len(results) > 1:
                    rv.update(anyOf=results)
                elif len(results) == 1:
                    rv.update(results[0])
            if "min" in meta:
                rv.update(minLength=meta["min"])
            if "max" in meta:
                rv.update(maxLength=meta["max"])
            if "gt" in meta:
                rv.update(minimum=meta["gt"], exclusiveMinimum=True)
            if "gte" in meta:
                rv.update(minimum=meta["gte"])
            if "lt" in meta:
                rv.update(maximum=meta["lt"], exclusiveMaximum=True)
            if "lte" in meta:
                rv.update(maximum=meta["lte"])
        return rv


def _iterate_meta(schema: Schema) -> Generator[dict, None, None]:
    for n in schema._iterate_chain():
        if n._meta:
            yield n._meta
