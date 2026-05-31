"""Golden-file (snapshot) tests for generated build.ninja.

The generated ninja text is the deterministic contract of the build system, so we pin a
known graph's output against a checked-in golden file. Path separators are normalised to
'/' before comparison so the same golden works regardless of the host OS.

To regenerate the golden file after an intentional change:

    python -m tests.regen_golden     # (or re-run with REGEN=1, see below)
"""
import os
from pathlib import Path

from helpers import render

import nanobuild as nb

GOLDEN_DIR = Path(__file__).parent / "golden"


def _normalize(text: str) -> str:
    return text.replace("\\", "/")


def build_simple_graph():
    """A small but representative graph: compile two sources, alias them, link an executable."""
    env = nb.Environment(source_dir="src", build_dir="build", CCFLAGS=["-g"])
    objects = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
    alias = env.Phony(objects, "objs")
    return env.CXXLink(alias, "app")


def test_simple_graph_matches_golden():
    actual = _normalize(render(build_simple_graph()))
    golden_path = GOLDEN_DIR / "simple.ninja"

    if os.environ.get("REGEN"):
        golden_path.parent.mkdir(exist_ok=True)
        golden_path.write_text(actual)

    expected = golden_path.read_text()
    assert actual == expected
