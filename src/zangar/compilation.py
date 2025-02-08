from __future__ import annotations

import inspect
from collections.abc import Hashable
from functools import partial
from typing import Callable

from zangar._core import SchemaBase, Union
from zangar._types import (
    Any,
    Boolean,
    Datetime,
    Float,
    Integer,
    List,
    NoneType,
    Object,
    String,
)


def _iter_union(union: Union):
    for i in union._schemas:
        if isinstance(i, Union):
            yield from _iter_union(i)
        else:
            yield i


class OpenAPI30Compiler:
    def compile(self, schema: SchemaBase):
        return self._compile(schema)

    def _compile_object(self, schema, spec, _):
        spec.update(type="object")
        properties = {}
        required = []
        for name, field in schema._fields.items():
            key = name if field._alias is None else field._alias
            properties[key] = self._compile(field._schema, spec)
            if field._default is not field._empty and not callable(field._default):
                properties[key].update(default=field._default)
            if field._required:
                required.append(key)
        if properties:
            spec.update(properties=properties)
        if required:
            spec.update(required=required)

    def _compile_list(self, schema, spec, _):
        spec.update(
            type="array",
            items=self._compile(schema._item),
        )

    def _compile_union(self, schema, spec, _):
        results = list(
            filter(
                lambda i: i,
                [self._compile(s, spec) for s in _iter_union(schema)],
            )
        )
        if len(results) > 1:
            spec.update(anyOf=results)
        elif len(results) == 1:
            spec.update(results[0])

    def _compile_any(self, _, spec, __):
        spec.update(nullable=True)

    def _compile_datetime(self, _, spec, __):
        spec.update(
            type="string",
            format="date-time",
        )

    def _compile_none(self, _, spec, parent):
        if isinstance(parent, dict):
            parent["nullable"] = True
        else:
            spec.update(
                enum=[None],
            )

    def _compile_other(self, _, spec, __, type):
        spec.update(
            type={
                String: "string",
                Integer: "integer",
                Float: "number",
                Boolean: "boolean",
            }[type]
        )

    _compilation_methods: dict[Hashable, Callable] = {
        Object: _compile_object,
        List: _compile_list,
        Union: _compile_union,
        Any: _compile_any,
        Datetime: _compile_datetime,
        NoneType: _compile_none,
        String: partial(_compile_other, type=String),
        Integer: partial(_compile_other, type=Integer),
        Float: partial(_compile_other, type=Float),
        Boolean: partial(_compile_other, type=Boolean),
    }

    def _compile(self, schema: SchemaBase, parent: dict | None = None):
        rv: dict = {}
        for n in schema._iterate_chain():
            for c in inspect.getmro(n.__class__):
                if c in self._compilation_methods:
                    self._compilation_methods[c](self, n, rv, parent)
                    break

            meta = n._meta
            if "$min" in meta:
                rv.update(minLength=meta["$min"])
            if "$max" in meta:
                rv.update(maxLength=meta["$max"])
            if "$gt" in meta:
                rv.update(minimum=meta["$gt"], exclusiveMinimum=True)
            if "$gte" in meta:
                rv.update(minimum=meta["$gte"])
            if "$lt" in meta:
                rv.update(maximum=meta["$lt"], exclusiveMaximum=True)
            if "$lte" in meta:
                rv.update(maximum=meta["$lte"])

            if "oas" in meta:
                rv.update(meta["oas"])
        return rv
