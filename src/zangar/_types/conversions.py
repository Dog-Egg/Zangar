import datetime

from zangar.exceptions import ValidationError

from .primitives import ZangarDatetime, ZangarFloat, ZangarInt, ZangarList, ZangarStr

try:
    from dateutil.parser import isoparser
except ImportError:  # pragma: no cover
    pass
else:
    dt_parser = isoparser("T")


class ZangarToList(ZangarList):
    """Convert the data to `list`.

    .. code-block::

        >>> z.to.list().parse((1, 2, 3))
        [1, 2, 3]

        # equivalent to:
        >>> z.transform(list).parse((1, 2, 3))
        [1, 2, 3]
    """

    def _convert(self, value):
        return list(value)


# Note: This function will be referenced by documentations
def int_convert(value):
    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.isdigit():
        return int(value)

    f = float(value)
    i = int(f)
    if f != i:
        raise ValidationError(f"{value!r} is not a valid integer")
    return i


class ZangarToInt(ZangarInt):
    """Convert the data to `int`.

    .. code-block::

        >>> z.to.int().parse('1.0')
        1

        # equivalent to:
        >>> z.transform(lambda x: int(float(x))).parse('1.0')
        1

    .. code-block::

        >>> z.to.int().parse(1.1)
        Traceback (most recent call last):
            ...
        zangar.exceptions.ValidationError: [{'msgs': ['1.1 is not a valid integer']}]
    """

    def _convert(self, value):
        return int_convert(value)


class ZangarToStr(ZangarStr):
    """Convert the data to `str`.

    .. code-block::

        >>> z.to.str().parse(1)
        '1'

        # equivalent to:
        >>> z.transform(str).parse(1)
        '1'
    """

    def _convert(self, value):
        return str(value)


class ZangarToFloat(ZangarFloat):
    """Convert the data to `float`.

    .. code-block::

        >>> z.to.float().parse('1')
        1.0

        # equivalent to:
        >>> z.transform(float).parse('1')
        1.0
    """

    def _convert(self, value):
        return float(value)


class ZangarToDatetime(ZangarDatetime):
    """Convert the data to `datetime.datetime`.
    It can parse a `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601>`_ datetime string.

    This feature is implemented using `python-dateutil <https://dateutil.readthedocs.io/>`_ .

    .. code-block::

        >>> z.to.datetime().parse('20040503T173008+08')
        datetime.datetime(2004, 5, 3, 17, 30, 8, tzinfo=tzoffset(None, 28800))
    """

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
