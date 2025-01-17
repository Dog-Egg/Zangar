from ._types import Float, Integer, List, String
from .exceptions import ValidationError


class ListConversion(List):
    def _convert(self, value):
        return list(value)


# Note: This function will be referenced by documentations
def int_convert(value):
    f = float(value)
    i = int(f)
    if f != i:
        raise ValidationError(f"{value!r} is not a valid integer")
    return i


class IntegerConversion(Integer):
    def _convert(self, value):
        return int_convert(value)


class StringConversion(String):
    def _convert(self, value):
        return str(value)


class FloatConversion(Float):
    def _convert(self, value):
        return float(value)


class Namespace:
    str = StringConversion
    int = IntegerConversion
    float = FloatConversion
    list = ListConversion


to = Namespace()
