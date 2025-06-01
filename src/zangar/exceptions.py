from __future__ import annotations


class ValidationError(Exception):
    def __init__(self, message=None):
        if message is None:
            peer_messages = []
        else:
            peer_messages = [message]
        self.__peer_messages: list = peer_messages
        self.__child_errors: dict[int | str, ValidationError] = {}

    def _set_peer_err(self, error: ValidationError):
        self.__peer_messages.extend(error.__peer_messages)

        for k, v in error.__child_errors.items():
            if k in self.__child_errors:
                self.__child_errors[k]._set_peer_err(v)
            else:
                self.__child_errors[k] = v

    def _set_child_err(self, key: str | int, error: ValidationError):
        assert key not in self.__child_errors
        self.__child_errors[key] = error

    def _has_child_err(self) -> bool:
        return bool(self.__child_errors)

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
