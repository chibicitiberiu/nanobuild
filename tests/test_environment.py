"""Unit tests for nanobuild.environment.Environment.

Many of these assertions are taken directly from the worked examples in
``doc/environments.md`` so that the documentation and the implementation stay in sync.
"""
from pathlib import Path

import pytest

import nanobuild as nb


class TestOptions:
    def test_constructor_kwargs_become_options(self):
        env = nb.Environment(CXX="clang++")
        assert env["CXX"] == "clang++"

    def test_constructor_args_dict(self):
        env = nb.Environment(args={"CC": "clang"})
        assert env["CC"] == "clang"

    def test_get_set_roundtrip(self):
        env = nb.Environment()
        env.set("CFLAGS", ["-O2"])
        assert env.get("CFLAGS") == ["-O2"]

    def test_item_access(self):
        env = nb.Environment()
        env["CFLAGS"] = ["-O2"]
        env["CFLAGS"] += ["-g"]
        assert env["CFLAGS"] == ["-O2", "-g"]

    def test_pop_and_delete(self):
        env = nb.Environment(FOO="bar")
        assert env.pop("FOO") == "bar"
        env["BAZ"] = 1
        del env["BAZ"]
        with pytest.raises(KeyError):
            _ = env["BAZ"]

    def test_iter_yields_pairs(self):
        env = nb.Environment(FOO="bar")
        items = dict(iter(env))
        assert items["FOO"] == "bar"


class TestReplaceAppend:
    """From doc/environments.md 'Customizing options'."""

    def test_replace_overwrites(self):
        env = nb.Environment(CFLAGS=["-g"], SOMESTRING="foo")
        env1 = env.clone()
        env1.replace(CFLAGS=["-O2"], SOMESTRING="bar")
        assert env1["CFLAGS"] == ["-O2"]
        assert env1["SOMESTRING"] == "bar"

    def test_append_combines(self):
        env = nb.Environment(CFLAGS=["-g"], SOMESTRING="foo")
        env2 = env.clone()
        env2.append(CFLAGS=["-O2"], SOMESTRING="bar")
        assert env2["CFLAGS"] == ["-g", "-O2"]
        assert env2["SOMESTRING"] == "foobar"

    def test_append_creates_missing_option(self):
        env = nb.Environment()
        env.append(NEW=["x"])
        assert env["NEW"] == ["x"]


class TestClone:
    """From doc/environments.md 'Cloning environments'."""

    def test_clone_is_independent(self):
        env = nb.Environment(CFLAGS=["-O2"])
        debug = env.clone(CONFIGURATION="debug")
        debug.append(CFLAGS=["-g"])
        release = env.clone(CONFIGURATION="release")
        release.append(CFLAGS=["-Wall"])

        assert env["CFLAGS"] == ["-O2"]
        assert debug["CFLAGS"] == ["-O2", "-g"]
        assert release["CFLAGS"] == ["-O2", "-Wall"]

    def test_clone_kwargs_replace(self):
        env = nb.Environment(CXX="g++")
        clang = env.clone(CXX="clang++")
        assert env["CXX"] == "g++"
        assert clang["CXX"] == "clang++"

    def test_clone_overrides_dirs(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        other = env.clone(source_dir="other")
        assert other.source_dir == Path("other")
        assert other.build_dir == Path("build")


class TestForSubdir:
    """From doc/environments.md 'Submodule workflow'."""

    def test_subdir_paths(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        sub = env.for_subdir("mylib")
        assert sub.source_dir == Path("src/mylib")
        assert sub.build_dir == Path("build/mylib")

    def test_subdir_separate_build_dir(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        sub = env.for_subdir("mylib", "build_mylib")
        assert sub.source_dir == Path("src/mylib")
        assert sub.build_dir == Path("build/build_mylib")

    def test_shallow_shares_options(self):
        """Shallow sub-environments share the parent's option store (documented behaviour)."""
        env = nb.Environment(CFLAGS=["-O2"])
        module1 = env.for_subdir("module1")

        env.append(CFLAGS=["-g"])
        module1.append(CFLAGS=["-Wall"])

        assert env["CFLAGS"] == ["-O2", "-g", "-Wall"]
        assert module1["CFLAGS"] == ["-O2", "-g", "-Wall"]

    def test_deep_clone_is_isolated(self):
        """deep_clone=True must NOT share options with the parent (documented behaviour)."""
        env = nb.Environment(CFLAGS=["-O2"])
        module2 = env.for_subdir("module2", deep_clone=True)

        env.append(CFLAGS=["-g"])
        module2.append(CFLAGS=["-Werror"])

        assert env["CFLAGS"] == ["-O2", "-g"]
        assert module2["CFLAGS"] == ["-O2", "-Werror"]


class TestPaths:
    def test_source_prefixes_source_dir(self):
        env = nb.Environment(source_dir="src")
        assert env.source("a.c") == Path("src/a.c")

    def test_dest_prefixes_build_dir(self):
        env = nb.Environment(build_dir="build")
        assert env.dest("a.o") == Path("build/a.o")

    def test_absolute_paths_are_left_alone(self, tmp_path):
        env = nb.Environment(source_dir="src")
        abs_path = tmp_path / "x.c"
        assert env.source(str(abs_path)) == Path(str(abs_path))
