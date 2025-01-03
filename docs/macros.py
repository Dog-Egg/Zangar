import importlib
import inspect
import operator
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent / "src"))


def define_env(env):
    "Hook function"

    @env.macro
    def source_code(import_name):
        obj = import_string(import_name)
        return inspect.getsource(obj)


def import_string(obj_path: str):
    if ":" in obj_path:
        module, obj = obj_path.rsplit(":", 1)
    elif "." in obj_path:
        module, obj = obj_path.rsplit(".", 1)
    else:
        raise ValueError(f"{obj_path} is not a valid import path")

    return operator.attrgetter(obj)(importlib.import_module(module))
