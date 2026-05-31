"""Shared pytest fixtures for the nanobuild test suite.

Plain helper functions live in ``tests/helpers.py`` so they can be imported directly;
this module holds fixtures only.
"""
import pytest


@pytest.fixture
def make_c_project(tmp_path):
    """Create a small C/C++ source tree under tmp_path and return its root.

    The returned project has a deterministic set of source files so that tests
    which exercise globbing / linking can assert on a stable, known input set.
    """
    def _make(files=None):
        files = files or {
            "a.cpp": "int a() { return 1; }\n",
            "b.cpp": "int b() { return 2; }\n",
            "sub/c.cpp": "int c() { return 3; }\n",
            "header.hpp": "#pragma once\n",
        }
        root = tmp_path / "project"
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return root

    return _make
