import os
import importlib.util

from .builder import *
from .environment import Environment
from .main import Nanobuild
from .target import Target
from .utility import Utility


def run(*targets, environ=os.environ):
    Nanobuild().run(*targets, environ=environ)


def import_file(file_name):
    """Imports given file as a module, and returns the module."""
    spec = importlib.util.spec_from_file_location("module.name", "file_name")
    imported_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported_module)
    return imported_module
