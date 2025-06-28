import abc
import typing as t

from zangar._core import Schema
from zangar._messages import DefaultMessage

T = t.TypeVar("T")


class TypeSchema(Schema[T], abc.ABC):

    @abc.abstractmethod
    def _expected_type(self) -> type: ...

    def _convert(self, value):
        return value

    def __init__(self, *, message=None, **kwargs):
        expected_type = self._expected_type()
        super().__init__(
            **kwargs,
            prev=Schema()
            .transform(
                self._convert,
                message=(
                    message
                    if message is not None
                    else lambda value: DefaultMessage(
                        key="type_convertion",
                        value=value,
                        ctx={"expected_type": expected_type},
                    )
                ),
            )
            .ensure(
                lambda x: isinstance(x, expected_type),
                message=(
                    message
                    if message is not None
                    else lambda value: DefaultMessage(
                        key="type_check",
                        ctx={"expected_type": expected_type},
                        value=value,
                    )
                ),
            )
            .transform(self._pretransform),
        )

    def _pretransform(self, value):
        return value
