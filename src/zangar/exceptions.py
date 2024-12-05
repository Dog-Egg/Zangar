from __future__ import annotations

from ._common import empty


class ValidationError(Exception):
    def __init__(self, message):
        if message is empty:
            error_messages = []
        else:
            error_messages = [message]
        self.__error_messages: list = error_messages
        self.__field_errors: dict[int | str, ValidationError] = {}

    def _concat(self, error: ValidationError):
        self.__error_messages.extend(error.__error_messages)

    def _setitem(self, key: str | int, error: ValidationError):
        assert key not in self.__field_errors
        self.__field_errors[key] = error

    def __str__(self):
        return str(self.format_errors())  # pragma: no cover

    def _empty(self) -> bool:
        return not self.__error_messages and not self.__field_errors

    def format_errors(self) -> list:
        rv = []
        if self.__error_messages:
            rv.append(dict(msgs=self.__error_messages))

        if self.__field_errors:
            fields = []

            def recursion(err: ValidationError, path: list):
                for k, e in err.__field_errors.items():
                    loc = path[:]
                    loc.append(k)
                    if e.__error_messages:
                        fields.append(
                            {
                                "loc": loc,
                                "msgs": e.__error_messages,
                            }
                        )
                    if err.__field_errors:
                        recursion(e, loc)

            recursion(self, [])
            rv.extend(fields)

        return rv
