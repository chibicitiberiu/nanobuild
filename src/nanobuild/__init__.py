from __future__ import annotations

import importlib.util
import os
from types import ModuleType
from typing import Any, Mapping

from .alias import Alias
from .builder import (
    ASBuilder,
    Builder,
    CBuilder,
    CCLinkBuilder,
    CommandBuilder,
    CopyBuilder,
    CXXBuilder,
    CXXLinkBuilder,
    LDLinkBuilder,
    PhonyBuilder,
    StaticLinkBuilder,
)
from .environment import Environment
from .main import Nanobuild
from .target import Target
from .utility import Utility

__all__ = [
    'run', 'import_file',
    'Alias', 'Builder', 'Environment', 'Nanobuild', 'Target', 'Utility',
    'ASBuilder', 'CBuilder', 'CXXBuilder', 'PhonyBuilder', 'CopyBuilder', 'CommandBuilder',
    'StaticLinkBuilder', 'LDLinkBuilder', 'CCLinkBuilder', 'CXXLinkBuilder',
]


def run(*targets: object, environ: Mapping[str, str] = os.environ) -> None:
    Nanobuild().run(*targets, environ=environ)


def import_file(file_name: str, **kwargs: Any) -> ModuleType:
    """
    Imports given file as a module, and returns the module.

    :param file_name: path to submodule's build.py
    :arg kwargs Variables which will be injected into the module before it is executed.
    """
    spec = importlib.util.spec_from_file_location("module.name", file_name)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_name!r}")
    imported_module = importlib.util.module_from_spec(spec)

    for key, value in kwargs.items():
        if isinstance(value, Environment):
            value = value.for_subdir(os.path.dirname(file_name))
        setattr(imported_module, key, value)

    spec.loader.exec_module(imported_module)
    return imported_module
