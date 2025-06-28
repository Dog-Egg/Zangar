from __future__ import annotations

import warnings
from collections.abc import Callable
from contextvars import ContextVar, Token
from dataclasses import astuple, dataclass, field
from typing import Any


class DefaultMessages:
    __token: Token

    def __init__(self) -> None:
        warnings.warn(
            "DefaultMessages is deprecated, use MessageContext instead",
            DeprecationWarning,
            stacklevel=2,
        )

    def __enter__(self):
        self.__token = _deprected_var.set(self)

    def __exit__(self, *args, **kwargs):
        _deprected_var.reset(self.__token)

    def default(self, name: str, value: Any, ctx: dict):
        return MessageContext().process_message(DefaultMessage(name, value, ctx))


_deprected_var: ContextVar[DefaultMessages] = ContextVar("default_messages")


_DEFAULT_MESSAGES = {
    "unknown_field": "Unknown field",
    "field_required": "This field is required",
    "type_check": "Expected {ctx[expected_type].__name__}, received {value.__class__.__name__}",
    "type_convertion": "Cannot convert the value {value!r} to {ctx[expected_type].__name__}",
    "transform_failed": "{ctx[exc]}",
    "str_min": "The minimum length of the string is {ctx[min]}",
    "str_max": "The maximum length of the string is {ctx[max]}",
    "number_gte": "The value should be greater than or equal to {ctx[gte]}",
    "number_gt": "The value should be greater than {ctx[gt]}",
    "number_lte": "The value should be less than or equal to {ctx[lte]}",
    "number_lt": "The value should be less than {ctx[lt]}",
    "datetime_is_aware": "The datetime should be aware",
    "datetime_is_naive": "The datetime should be naive",
}


class MessageContext:
    """The message context object can be used to modify Zangar's default messages,
    and can also be extended to handle custom message types.
    """

    __token: Token

    def __enter__(self):
        self.__token = _message_ctx_var.set(self)

    def __exit__(self, *args, **kwargs):
        _message_ctx_var.reset(self.__token)

    # pylint: disable-next=too-many-return-statements,too-many-branches
    def process_message(self, message):
        """Process the message.

        Args:
            message: The message to process.

        Returns:
            The processed message.
        """
        if not isinstance(message, DefaultMessage):
            return message

        key, value, ctx = astuple(message)
        if key in _DEFAULT_MESSAGES:
            return _DEFAULT_MESSAGES[key].format(value=value, ctx=ctx)
        return "Invalid value"


_message_ctx_var: ContextVar[MessageContext] = ContextVar(
    "message_ctx", default=MessageContext()
)


def process_message(message: Any | Callable[[Any], Any] | None, value: Any):
    if callable(message):
        message = message(value)
    try:
        # 兼容
        deprected = _deprected_var.get()
    except LookupError:
        message_ctx = _message_ctx_var.get()
        return message_ctx.process_message(message)

    if isinstance(message, DefaultMessage):
        return deprected.default(message.key, message.value, message.ctx)
    return message


@dataclass
class DefaultMessage:
    """This is the wrapper class for Zangar’s default messages.
    You should not use it directly in your code,
    it exists solely for modifying Zangar’s built-in messages.
    """

    key: str
    value: Any
    ctx: dict = field(default_factory=dict)
