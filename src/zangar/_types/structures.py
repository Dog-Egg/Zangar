from __future__ import annotations

import copy
import typing as t
import warnings
from collections.abc import Callable, Iterable, Mapping
from operator import getitem
from types import MappingProxyType

from zangar._core import Schema, SchemaBase
from zangar._messages import DefaultMessage, process_message
from zangar.exceptions import ValidationError

from .base import TypeSchema

T = t.TypeVar("T")

_empty: t.Any = object()


class ZangarField(t.Generic[T]):
    """A field in a struct.

    Args:
        schema: The schema of the field.
        alias: The field alias name, if not `None`, will be used to construct the parsed field name.
        getter: A custom function used to obtain the field value.
            If the function you provided raises an `Exception`,
            the field will be treated as having no value retrieved.
    """

    _empty = _empty

    def __init__(
        self,
        schema: SchemaBase[T],
        *,
        alias: str | None = None,
        getter: Callable[[t.Any], t.Any] | None = None,
    ) -> None:
        self.__schema = schema
        self.__alias = alias
        self.__getter = getter
        self._required = True
        self.__required_message = None
        self._default: Callable[[], T] | T = _empty

    @property
    def alias(self) -> str | None:
        return self.__alias

    @property
    def schema(self):
        return self.__schema

    def __call__(self, obj, key: str):
        if self.__getter is None:
            value = _getter(obj, key)
        else:
            try:
                value = self.__getter(obj)
            # pylint: disable-next=broad-exception-caught
            except Exception:
                value = self._empty

        if value is self._empty:
            if self._required:
                raise ValidationError(
                    process_message(
                        (
                            self.__required_message
                            if self.__required_message is not None
                            else DefaultMessage(key="field_required", value=None)
                        ),
                        value=None,
                    )
                )
            if callable(self._default):
                return self._default()
            return self._default
        return self.__schema.parse(value)

    def optional(self, *, default: T | Callable[[], T] = _empty):
        self._required = False
        self._default = default
        return self

    def required(self, /, *, message=None):
        self._required = True
        if message is not None:
            self.__required_message = message
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

        def inner_func(fieldval):
            if func(fieldval):
                return True
            error = ValidationError()
            for fieldname in fieldnames:
                error._set_child_err(
                    self.__name_to_alias[fieldname],
                    ValidationError(
                        process_message(
                            (
                                message
                                if message is not None
                                else DefaultMessage(key="ensure_failed", value=fieldval)
                            ),
                            value=fieldval,
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
        fields: UnnormalizedFields,
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
            alias = field.alias or name
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

        for fieldname, field in self.fields.items():
            key = fieldname if field.alias is None else field.alias
            try:
                fieldvalue = field(value, key)
            except ValidationError as e:
                error._set_child_err(key, e)
            else:
                if fieldvalue is not _empty:
                    rv[fieldname] = fieldvalue

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
            for k, v in value.items():
                if k not in keys:
                    error._set_child_err(
                        k,
                        ValidationError(
                            process_message(
                                message=DefaultMessage(key="unknown_field", value=v),
                                value=v,
                            )
                        ),
                    )
            if not error._empty():
                raise error

        elif self.__unknown == "include":
            for k in value:
                if k not in keys:
                    rv[k] = value[k]
        elif self.__unknown == "exclude":  # pragma: no cover
            pass
        else:
            raise NotImplementedError

        return rv


def _get_keys(fields: Mapping[str, ZangarField]) -> set[str]:
    rv = set()
    for name, field in fields.items():
        if field.alias is None:
            rv.add(name)
        else:
            rv.add(field.alias)
    return rv


Fields: t.TypeAlias = t.Mapping[str, ZangarField]
UnnormalizedFields: t.TypeAlias = t.Mapping[str, t.Union[ZangarField, SchemaBase]]


def _normalize_fields(fields: UnnormalizedFields) -> Fields:
    _fields = {}
    for name, field in fields.items():
        if not isinstance(field, ZangarField):
            _fields[name] = ZangarField(field)
        else:
            _fields[name] = field
    return _fields


def _check_fieldnames(fields: UnnormalizedFields, names: Iterable[str] | None, /):
    if not names:
        return
    for name in names:
        if name not in fields:
            raise ValueError(f"Field {name!r} not found in the struct schema")


def required_fields(
    fields: UnnormalizedFields, names: Iterable[str] | None = None, /
) -> Fields:
    """Make the specified fields required.

    Args:
        fields: The fields to make required.
        names: The names of the fields to make required.
            If not provided, all fields will be made required.
    """

    _check_fieldnames(fields, names)
    fields = _normalize_fields(fields)
    copy_fields = {}
    for name, field in fields.items():
        copy_field = copy.copy(field)
        if names is None or name in names:
            copy_field.required()
        else:
            copy_field.optional()
        copy_fields[name] = copy_field
    return copy_fields


def optional_fields(
    fields: UnnormalizedFields, names: Iterable[str] | None = None, /
) -> Fields:
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


def pick_fields(fields: UnnormalizedFields, names: Iterable[str], /) -> Fields:
    """Pick the specified fields.

    Args:
        fields: The fields to pick from.
        names: The names of the fields to pick.
    """
    _check_fieldnames(fields, names)
    fields = _normalize_fields(fields)
    copy_fields = {}
    for name in names:
        copy_fields[name] = copy.copy(fields[name])
    return copy_fields


def omit_fields(fields: UnnormalizedFields, names: Iterable[str], /) -> Fields:
    """Pick all fields except the specified ones.

    Args:
        fields: The fields to omit from.
        names: The names of the fields to omit.
    """
    _check_fieldnames(fields, names)
    return pick_fields(fields, set(fields) - set(names))
