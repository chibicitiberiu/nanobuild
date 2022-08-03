import os
import importlib.util

from .builder import *
from .environment import Environment
from .main import Nanobuild
from .target import Target
from .utility import Utility


def run(*targets, environ=os.environ):
    Nanobuild().run(*targets, environ=environ)


def import_file(file_name, **kwargs):
    """
    Imports given file as a module, and returns the module.

    :param file_name: path to submodule's build.py
    :arg kwargs Variables which will be injected into the module before it is executed.
    """
    spec = importlib.util.spec_from_file_location("module.name", file_name)
    imported_module = importlib.util.module_from_spec(spec)

    for key, value in kwargs.items():
        if isinstance(value, Environment):
            value = value.for_subdir(os.path.dirname(file_name))
        setattr(imported_module, key, value)

    spec.loader.exec_module(imported_module)
    return imported_module
