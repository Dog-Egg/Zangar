from __future__ import annotations


class ValidationError(Exception):
    """Base validation error class that can store messages and sub errors."""

    def __init__(self, message=None):
        self.message = message
        self._sub_errors: dict[int | str, ValidationError] = {}

    def _empty(self):
        """Check if this error has no message and no sub errors."""
        return self.message is None and not self._sub_errors

    def __str__(self):
        return str(self.format_errors())

    def _set_sub_error(self, key: str | int, error: ValidationError):
        """Set a sub error at the given key."""
        assert key not in self._sub_errors
        self._sub_errors[key] = error

    def __or__(self, other):
        """Combine errors with OR operator (keep both separately)."""
        return ValidationOrError(self, other)

    def __and__(self, other):
        """Combine errors with AND operator (merge together)."""
        return ValidationAndError(self, other)

    def format_errors(self):
        """Format errors into a list of error dictionaries."""
        # If has sub errors, format them with location paths
        if self._sub_errors:
            return self._format_sub_errors()

        # Otherwise, format as simple message
        msgs = [] if self.message is None else [self.message]
        return [{"msgs": msgs}]

    def _format_sub_errors(self):
        """Format sub errors with location paths."""
        result = []
        for key, error in self._sub_errors.items():
            for err_dict in error.format_errors():
                formatted = {**err_dict}
                # Prepend key to location path
                if "loc" in formatted:
                    formatted["loc"] = [key] + formatted["loc"]
                else:
                    formatted["loc"] = [key]
                result.append(formatted)
        return result


class ValidationOrError(ValidationError):
    """Internal class for OR operation: keeps errors separate."""

    def __init__(self, *errors: ValidationError):
        super().__init__()
        self.errors = errors

    def format_errors(self):
        """Collect all errors from OR chain, flattening nested OR operations."""
        result = []
        self._collect_or_errors(result)
        return result

    def _collect_or_errors(self, result):
        """Recursively collect errors from OR chain."""
        for err in self.errors:
            if isinstance(err, ValidationOrError):
                err._collect_or_errors(result)
            elif not err._empty():
                result.extend(err.format_errors())


class ValidationAndError(ValidationError):
    """Internal class for AND operation: merges errors together."""

    def __init__(self, *errors: ValidationError):
        super().__init__()
        self.errors = errors

    def _empty(self):
        return False

    def format_errors(self):
        """Collect all messages and errors from AND chain, merging them."""
        msgs = []
        all_errors = []
        self._collect_and_errors(msgs, all_errors)

        # If there are errors with location paths, return them
        if any("loc" in err for err in all_errors):
            return all_errors

        # Otherwise return just the messages
        return [{"msgs": msgs}]

    def _collect_and_errors(self, msgs, all_errors):
        """Recursively collect messages and errors from AND chain."""
        for err in self.errors:
            if isinstance(err, ValidationAndError):
                err._collect_and_errors(msgs, all_errors)
            else:
                if err.message is not None:
                    msgs.append(err.message)
                # Collect formatted errors
                for err_item in err.format_errors():
                    if err_item.get("msgs") or "loc" in err_item:
                        all_errors.append(err_item)
