from __future__ import annotations

from ._common import empty


class ValidationError(Exception):
    def __init__(self, message):
        if message is empty:
            peer_messages = []
        else:
            peer_messages = [message]
        self.__peer_messages: list = peer_messages
        self.__child_errors: dict[int | str, ValidationError] = {}

    def _set_peer(self, error: ValidationError):
        self.__peer_messages.extend(error.__peer_messages)
        self.__child_errors.update(error.__child_errors)

    def _set_child(self, key: str | int, error: ValidationError):
        assert key not in self.__child_errors
        self.__child_errors[key] = error

    def __str__(self):
        return str(self.format_errors())  # pragma: no cover

    def _empty(self) -> bool:
        return not self.__peer_messages and not self.__child_errors

    def format_errors(self) -> list:
        rv = []
        if self.__peer_messages:
            rv.append(dict(msgs=self.__peer_messages))

        if self.__child_errors:
            fields = []

            def recursion(err: ValidationError, path: list):
                for k, e in err.__child_errors.items():
                    loc = path[:]
                    loc.append(k)
                    if e.__peer_messages:
                        fields.append(
                            {
                                "loc": loc,
                                "msgs": e.__peer_messages,
                            }
                        )
                    if err.__child_errors:
                        recursion(e, loc)

            recursion(self, [])
            rv.extend(fields)

        return rv
