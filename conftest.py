from doctest import ELLIPSIS

from sybil import Sybil
from sybil.parsers.markdown import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser
from sybil.parsers.rest import PythonCodeBlockParser as RstCodeBlockParser


def setup(namespace: dict):
    import zangar

    namespace["z"] = zangar


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        RstCodeBlockParser(),
        PythonCodeBlockParser(),
    ],
    patterns=["*.md", "*.py", "*.rst"],
    setup=setup,
).pytest()
