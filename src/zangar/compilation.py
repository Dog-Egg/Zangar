from __future__ import annotations

from typing import Callable

from zangar._core import SchemaBase
from zangar.utils.misc import assign_oas


class _ScopedDict(dict):
    __parent: _ScopedDict | None = None
    _compile: Callable

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, value):
        assert self.__parent is None
        self.__parent = value


class OpenAPI30Compiler:
    def compile(self, schema: SchemaBase):
        return self._compile(schema)

    def _compile(self, schema: SchemaBase, parent: _ScopedDict | None = None):
        rv = _ScopedDict()
        rv._compile = self._compile
        if parent is not None:
            rv.parent = parent

        for n in schema._iterate_chain():
            meta = n._meta
            if "oas" in meta:
                oas = meta["oas"]
                assign_oas(rv, oas)
        return rv
