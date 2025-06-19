from __future__ import annotations

import copy
import typing as t
import warnings
from collections.abc import Callable, Iterable, Mapping
from functools import partial
from operator import getitem
from types import MappingProxyType

from zangar._core import Schema, SchemaBase
from zangar._messages import DefaultMessage, get_message
from zangar.exceptions import ValidationError

from .base import TypeSchema

T = t.TypeVar("T")

_empty: t.Any = object()


class ZangarField(t.Generic[T]):
    """A field in a struct.

    Args:
        schema: The schema of the field.
        alias: The alias of the field.
        getter: A custom function used to obtain the field value.
    """

    _empty = _empty

    def __init__(
        self,
        schema: SchemaBase[T],
        *,
        alias: str | None = None,
        getter: Callable[[t.Any], t.Any] | None = None,
    ) -> None:
        self._schema = schema
        self.__alias = alias
        self._getter = getter
        self._required = True
        self._required_message = None
        self._default: Callable[[], T] | T = _empty

    def _get_default(self):
        if callable(self._default):
            return self._default()
        return self._default

    @property
    def _alias(self):
        return self.__alias

    def parse(self, value, /):
        return self._schema.parse(value)

    def optional(self, *, default: T | Callable[[], T] = _empty):
        self._required = False
        self._default = default
        return self

    def required(self, /, *, message=None):
        self._required = True
        if message is not None:
            self._required_message = message
        return self


class StructMethods(Schema[T]):
    def __init__(
        self,
        *args,
        name_to_alias: dict[str, str],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.__name_to_alias = name_to_alias

    def ensure_fields(
        self,
        fieldnames: list[str],
        func: Callable[[T], bool],
        /,
        *,
        message: t.Any | Callable[[T], t.Any] = None,
    ):
        """Validate the fields.

        Args:
            fieldnames: The names of the fields to validate.
            func: The function to validate the fields.
            message: The error message to display when the validation fails.
        """

        def inner_func(value):
            if func(value):
                return True
            error = ValidationError()
            for fieldname in fieldnames:
                error._set_child_err(
                    self.__name_to_alias[fieldname],
                    ValidationError(
                        get_message(
                            (
                                message
                                if message is not None
                                else DefaultMessage(name="ensure_failed")
                            ),
                            value=value,
                        )
                    ),
                )
            raise error

        return StructMethods(
            prev=self.ensure(inner_func), name_to_alias=self.__name_to_alias
        )


class ZangarStruct(TypeSchema[dict], StructMethods[dict]):
    """This is a schema with fields. It can parse any object and return a dict.

    Args:
        fields: The fields of the struct.
    """

    def _expected_type(self) -> type:
        return object

    def __init__(
        self,
        fields: (
            Mapping[str, ZangarField]
            | Mapping[str, SchemaBase]
            | Mapping[str, ZangarField | SchemaBase]
        ),
        /,
    ):
        _fields: dict[str, ZangarField] = {}
        for name, field in fields.items():
            if not isinstance(field, ZangarField):
                _fields[name] = ZangarField(field)
            else:
                _fields[name] = field
        self.__fields = MappingProxyType(_fields)

        self._name_to_alias, self._alias_to_name = {}, {}
        for name, field in self.fields.items():
            alias = field._alias or name
            self._name_to_alias[name] = alias
            self._alias_to_name[alias] = name

        super().__init__(name_to_alias=self._name_to_alias)

    @property
    def fields(self) -> Mapping[str, ZangarField]:
        """The fields of the struct."""
        return self.__fields

    def extend(self, fields: dict[str, ZangarField | SchemaBase], /):
        """Extend the struct with additional fields.

        DEPRECATED: this method will be removed in the future.

        Args:
            fields: The fields to add.
        """
        warnings.warn(
            "Deprecated",
            DeprecationWarning,
            stacklevel=2,
        )

        new_fields: dict[str, ZangarField | SchemaBase] = {}
        new_fields.update(self.fields)
        new_fields.update(fields)
        return self.__class__(new_fields)

    def required_fields(
        self, fieldnames: Iterable[str] | None = None, /
    ) -> ZangarStruct:
        """Make the specified fields required.

        DEPRECATED: this method will be removed in the future.

        Args:
            fieldnames: The names of the fields to make required.
                If not provided, all fields will be made required.
        """
        warnings.warn(
            "Deprecated, use function `required_fields` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__class__(required_fields(self.fields, fieldnames))

    def optional_fields(
        self, fieldnames: Iterable[str] | None = None, /
    ) -> ZangarStruct:
        """Make the specified fields optional.

        DEPRECATED: this method will be removed in the future.

        Args:
            fieldnames: The names of the fields to make optional.
                If not provided, all fields will be made optional.
        """
        warnings.warn(
            "Deprecated, use function `optional_fields` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__class__(optional_fields(self.fields, fieldnames))

    def pick_fields(self, fieldnames: Iterable[str], /) -> ZangarStruct:
        """Pick the specified fields.

        DEPRECATED: this method will be removed in the future.

        Args:
            fieldnames: The names of the fields to pick.
        """
        warnings.warn(
            "Deprecated, use function `pick_fields` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__class__(pick_fields(self.fields, fieldnames))

    def omit_fields(self, fieldnames: Iterable[str], /) -> ZangarStruct:
        """Pick all fields except the specified ones.

        DEPRECATED: this method will be removed in the future.

        Args:
            fieldnames: The names of the fields to omit.
        """
        warnings.warn(
            "Deprecated, use function `omit_fields` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__class__(omit_fields(self.fields, fieldnames))

    def _pretransform(self, value):
        rv = {}
        error = ValidationError()

        getter: t.Callable[[t.Any], t.Any]

        for fieldname, field in self.fields.items():
            alias = self._name_to_alias[fieldname]

            # getter
            if field._getter is None:
                getter = partial(_getter, key=alias)
            else:
                getter = field._getter

            field_value = getter(value)
            if field_value is _empty:
                if field._required:
                    error._set_child_err(
                        alias,
                        ValidationError(
                            get_message(
                                message=(
                                    field._required_message
                                    if field._required_message is not None
                                    else DefaultMessage(name="field_required")
                                ),
                                value=None,
                            )
                        ),
                    )
                    continue

                default = field._get_default()
                if default is not ZangarField._empty:
                    rv[fieldname] = default
            else:
                try:
                    field_value = field.parse(field_value)
                except ValidationError as e:
                    error._set_child_err(alias, e)
                else:
                    rv[fieldname] = field_value

        if not error._empty():
            raise error

        return rv


def _getter(value, key):
    if isinstance(value, Mapping):
        try:
            return getitem(value, key)
        except KeyError:
            return _empty
    else:
        try:
            return getattr(value, key)
        except AttributeError:
            return _empty


class ZangarObject(ZangarStruct):
    """Deprecated, use `ZangarStruct` instead."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            "Object is deprecated, use Struct instead",
            DeprecationWarning,
            stacklevel=2,
        )


class ZangarMappingStruct(ZangarStruct):
    """Only supports parsing `Mapping` objects.

    Args:
        unknown (str): The behavior when encountering unknown fields.

            - "include": Include unknown fields in the parsed result.
            - "exclude": Exclude unknown fields from the parsed result.
            - "raise": Raise an error when encountering unknown fields.
    """

    def __init__(
        self,
        *args,
        unknown: t.Literal["include", "exclude", "raise"] = "exclude",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        assert unknown in {"include", "exclude", "raise"}
        self.__unknown = unknown

    def _expected_type(self) -> type:
        return Mapping

    def _pretransform(self, value):
        assert isinstance(value, Mapping)
        rv = super()._pretransform(value)

        keys = _get_keys(self.fields)
        if self.__unknown == "raise":
            error = ValidationError()
            for key in value:
                if key not in keys:
                    error._set_child_err(
                        key,
                        ValidationError(
                            get_message(
                                message=DefaultMessage(name="unknown_field"),
                                value=key,
                            )
                        ),
                    )
            if not error._empty():
                raise error

        elif self.__unknown == "include":
            for key in value:
                if key not in keys:
                    rv[key] = value[key]
        elif self.__unknown == "exclude":  # pragma: no cover
            pass
        else:
            raise NotImplementedError

        return rv


def _get_keys(fields: Mapping[str, ZangarField]) -> set[str]:
    rv = set()
    for name, field in fields.items():
        if field._alias is None:
            rv.add(name)
        else:
            rv.add(field._alias)
    return rv


Fields: t.TypeAlias = t.Mapping[str, ZangarField]


def _check_fieldnames(fields: Fields, names: Iterable[str] | None, /):
    if not names:
        return
    for name in names:
        if name not in fields:
            raise ValueError(f"Field {name!r} not found in the struct schema")


def required_fields(fields: Fields, names: Iterable[str] | None = None, /) -> Fields:
    """Make the specified fields required.

    Args:
        fields: The fields to make required.
        names: The names of the fields to make required.
            If not provided, all fields will be made required.
    """

    _check_fieldnames(fields, names)
    copy_fields: dict[str, ZangarField] = {}
    for name, field in fields.items():
        copy_field = copy.copy(field)
        if names is None or name in names:
            copy_field.required()
        else:
            copy_field.optional()
        copy_fields[name] = copy_field
    return copy_fields


def optional_fields(fields: Fields, names: Iterable[str] | None = None, /) -> Fields:
    """Make the specified fields optional.

    Args:
        fields: The fields to make optional.
        names: The names of the fields to make optional.
            If not provided, all fields will be made optional.
    """
    _check_fieldnames(fields, names)
    if names is None:
        return required_fields(fields, [])
    return required_fields(fields, set(fields) - set(names))


def pick_fields(fields: Fields, names: Iterable[str], /) -> Fields:
    """Pick the specified fields.

    Args:
        fields: The fields to pick from.
        names: The names of the fields to pick.
    """
    _check_fieldnames(fields, names)
    copy_fields = {}
    for name in names:
        copy_fields[name] = copy.copy(fields[name])
    return copy_fields


def omit_fields(fields: Fields, names: Iterable[str], /) -> Fields:
    """Pick all fields except the specified ones.

    Args:
        fields: The fields to omit from.
        names: The names of the fields to omit.
    """
    _check_fieldnames(fields, names)
    return pick_fields(fields, set(fields) - set(names))
