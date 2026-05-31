from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
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
    'run', 'import_file', '__version__', '__build__',
    'Alias', 'Builder', 'Environment', 'Nanobuild', 'Target', 'Utility',
    'ASBuilder', 'CBuilder', 'CXXBuilder', 'PhonyBuilder', 'CopyBuilder', 'CommandBuilder',
    'StaticLinkBuilder', 'LDLinkBuilder', 'CCLinkBuilder', 'CXXLinkBuilder',
]


def _detect_version() -> str:
    """Resolve the package version. The VERSION file is the single source of truth in a source
    checkout; an installed package falls back to its baked-in metadata."""
    version_file = Path(__file__).resolve().parents[2] / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return version("nanobuild")
        except PackageNotFoundError:
            return "0.0.0"
    except ImportError:
        return "0.0.0"


def _detect_build() -> str:
    """Build identifier (CI run number + commit), written to a generated _buildinfo module at
    release time. Returns 'dev' for ordinary source/installed builds."""
    try:
        module = importlib.import_module("nanobuild._buildinfo")
        return str(module.BUILD)
    except (ImportError, AttributeError):
        return "dev"


__version__ = _detect_version()
__build__ = _detect_build()


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
