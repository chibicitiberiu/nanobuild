"""Tests for target-graph construction via Environment.build / env.<Builder>()."""
from pathlib import Path

import pytest

import nanobuild as nb
from nanobuild.alias import Alias
from nanobuild.target import Target


class TestAutogenerateOutput:
    def test_single_compile_autogenerates_object(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        targets = env.CC(env.source("a.c"))
        assert len(targets) == 1
        assert targets[0].output == Path("build/a.o")

    def test_multiple_inputs_emit_one_target_each(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        targets = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
        outputs = [t.output for t in targets]
        assert outputs == [Path("build/a.o"), Path("build/b.o")]


class TestExplicitOutput:
    def test_linker_requires_and_uses_output(self):
        env = nb.Environment(build_dir="build")
        objs = env.CXX([env.source("a.cpp")])
        targets = env.CXXLink(objs, "app")
        assert len(targets) == 1
        assert targets[0].output == Path("build/app")

    def test_string_output_is_placed_in_build_dir(self):
        env = nb.Environment(build_dir="out")
        objs = env.CXX([env.source("a.cpp")])
        target = env.CXXLink(objs, "prog")[0]
        assert target.output == Path("out/prog")


class TestPhony:
    def test_phony_requires_alias_name(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        with pytest.raises(ValueError):
            env.Phony(objs)

    def test_phony_output_is_alias(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        target = env.Phony(objs, "my_alias")[0]
        assert isinstance(target.output, Alias)
        assert str(target.output) == "my_alias"


class TestDeps:
    def test_deps_are_recorded(self):
        env = nb.Environment(source_dir="src")
        headers = [env.source("h.hpp")]
        target = env.CXX([env.source("a.cpp")], deps=headers)[0]
        assert Path("src/h.hpp") in target.deps


class TestPerTargetKwargs:
    def test_kwargs_clone_environment_without_mutating_original(self):
        env = nb.Environment(CXXFLAGS=["-O2"])
        target = env.CXX([env.source("a.cpp")], CXXFLAGS=["-O0"])[0]
        # original environment untouched
        assert env["CXXFLAGS"] == ["-O2"]
        # target carries a distinct environment with the override
        assert target.environment is not env
        assert target.environment["CXXFLAGS"] == ["-O0"]


class TestTargetsAreChainable:
    def test_targets_feed_into_other_targets(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        link = env.CXXLink(objs, "app")[0]
        assert all(isinstance(o, Target) for o in objs)
        assert objs[0] in link.inputs
