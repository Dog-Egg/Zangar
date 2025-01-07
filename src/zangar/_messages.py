from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any


class DefaultMessages:
    __token: Token

    def __enter__(self):
        self.__token = _default_messages_var.set(self)

    def __exit__(self, *args, **kwargs):
        _default_messages_var.reset(self.__token)

    # pylint: disable-next=too-many-return-statements
    def default(self, name: str, value: Any, ctx: dict):
        if name == "field_required":
            return "This field is required"

        if name == "type_check":
            return f"Expected {ctx['expected_type'].__name__}, received {type(value).__name__}"

        if name == "type_convertion":
            return (
                f"Cannot convert the value {value!r} to {ctx['expected_type'].__name__}"
            )

        if name == "transform_failed":
            return str(ctx["exc"])

        if name == "str_min":
            return f"The minimum length of the string is {ctx['min']}"

        if name == "str_max":
            return f"The maximum length of the string is {ctx['max']}"

        if name == "number_gte":
            return f"The value should be greater than or equal to {ctx['gte']}"

        if name == "number_gt":
            return f"The value should be greater than {ctx['gt']}"

        if name == "number_lte":
            return f"The value should be less than or equal to {ctx['lte']}"

        if name == "number_lt":
            return f"The value should be less than {ctx['lt']}"

        return "Invalid value"


_default_messages_var: ContextVar[DefaultMessages] = ContextVar(
    "default_messages", default=DefaultMessages()
)


def get_message(
    name: str,
    message: Any | Callable[[Any], Any] | None,
    value: Any,
    ctx: dict | None = None,
):
    if message is None:
        default_messages = _default_messages_var.get()
        return default_messages.default(name=name, value=value, ctx=ctx or {})
    if callable(message):
        return message(value)
    return message


@dataclass
class IncompleteMessage:
    name: str
    ctx: dict
