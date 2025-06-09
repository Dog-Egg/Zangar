import datetime

from ._types import ZangarDatetime, ZangarFloat, ZangarInt, ZangarList, ZangarStr
from .exceptions import ValidationError

try:
    from dateutil.parser import isoparser
except ImportError:
    pass
else:
    dt_parser = isoparser("T")


class ZangarToList(ZangarList):
    def _convert(self, value):
        return list(value)


# Note: This function will be referenced by documentations
def int_convert(value):
    f = float(value)
    i = int(f)
    if f != i:
        raise ValidationError(f"{value!r} is not a valid integer")
    return i


class ZangarToInt(ZangarInt):
    def _convert(self, value):
        return int_convert(value)


class ZangarToStr(ZangarStr):
    def _convert(self, value):
        return str(value)


class ZangarToFloat(ZangarFloat):
    def _convert(self, value):
        return float(value)


class ZangarToDatetime(ZangarDatetime):
    def _convert(self, value):
        if isinstance(value, datetime.datetime):
            return value
        return dt_parser.isoparse(value)


class Namespace:
    str = ZangarToStr
    int = ZangarToInt
    float = ZangarToFloat
    list = ZangarToList
    datetime = ZangarToDatetime


to = Namespace()
