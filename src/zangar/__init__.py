from zangar.utils.version import get_version as __get_version

from ._alias import *
from ._conversions import to
from ._core import SchemaBase as Schema
from ._core import ref
from ._messages import DefaultMessages
from .dataclass import dataclass
from .exceptions import ValidationError

__version__ = __get_version((0, 1, 0, "alpha", 0))
