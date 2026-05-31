"""End-to-end integration test: generate build.ninja and actually build with ninja.

Skipped automatically when ninja or a C++ compiler is not available, so the rest of the
suite stays hermetic and CI without a toolchain still goes green.
"""
import shutil
import subprocess

import pytest

import nanobuild as nb
from nanobuild.main import Nanobuild

ninja = shutil.which("ninja")
gpp = shutil.which("g++")

pytestmark = pytest.mark.skipif(
    not (ninja and gpp),
    reason="requires both ninja and g++ on PATH",
)


def test_compiles_and_links_real_program(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.cpp").write_text(
        "int add(int);\n"
        "int main() { return add(0); }\n"
    )
    (src / "add.cpp").write_text("int add(int x) { return x; }\n")

    monkeypatch.chdir(tmp_path)
    env = nb.Environment(source_dir=str(src), build_dir=str(tmp_path / "build"))
    objects = env.CXX(env.source_glob("*.cpp"))
    binary = env.CXXLink(objects, "app")

    (tmp_path / "build.ninja").write_text(Nanobuild().generate_ninja(binary))
    result = subprocess.run([ninja], cwd=tmp_path, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    produced = list((tmp_path / "build").glob("app*"))
    assert produced, "expected linked executable to be produced"
