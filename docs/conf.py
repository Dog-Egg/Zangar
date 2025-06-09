import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

project = "Zangar"

default_role = "py:obj"
nitpicky = True
nitpick_ignore_regex = {
    (r"py:.*", r"zangar\._.*"),
}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

html_theme = "agogo"
