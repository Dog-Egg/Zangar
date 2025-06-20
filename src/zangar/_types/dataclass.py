from __future__ import annotations

import dataclasses
import typing as t
from collections.abc import Mapping

from .._core import Schema
from .structures import ZangarField, ZangarStruct


class ZangarDataclass(Schema["dataclasses._DataclassT"]):
    """Convert a `dataclasses.dataclass` into a Zangar schema for data validation,
    and the resulting output is an instance of that dataclass.

    Args:
        cls: The dataclass to convert.
    """

    def __init__(self, cls: type[dataclasses._DataclassT], /):
        self.__struct = ZangarStruct(_parse_dataclass(cls))
        super().__init__(prev=self.__struct.transform(lambda d: cls(**d)))

    @property
    def fields(self):
        """The fields of the dataclass."""
        return self.__struct.fields


def _parse_dataclass(
    cls: type[dataclasses._DataclassT],
) -> Mapping[str, ZangarField]:
    dc_fields = dataclasses.fields(cls)
    struct_fields: dict[str, ZangarField] = {}
    metadata_key = "zangar"

    for dc_field in dc_fields:
        if metadata_key not in dc_field.metadata:
            raise RuntimeError(
                f"Need to add {metadata_key!r} metadata to the {dc_field.name!r} field"
            )

        metadata = dc_field.metadata[metadata_key]
        struct_field = ZangarField(**metadata)

        default: t.Any = ZangarField._empty
        if dc_field.default is not dataclasses.MISSING:
            default = dc_field.default
        elif dc_field.default_factory is not dataclasses.MISSING:
            default = dc_field.default_factory
        if default is not ZangarField._empty:
            struct_field = struct_field.optional(default=default)
        struct_fields[dc_field.name] = struct_field

    return struct_fields
