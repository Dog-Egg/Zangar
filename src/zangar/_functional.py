import sys

from ._core import Schema


def ref(name: str, /):
    frame = sys._getframe(1)

    def transform(value):
        schema: Schema = frame.f_locals[name]
        return schema.parse(value)

    return Schema().transform(transform)
