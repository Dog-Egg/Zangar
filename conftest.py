from doctest import ELLIPSIS

from sybil import Sybil
from sybil.parsers.markdown import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser


def setup(namespace: dict):
    import zangar

    namespace["z"] = zangar


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.md", "*.py"],
    setup=setup,
).pytest()
