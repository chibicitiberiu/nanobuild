"""Tests for the Depends alias, batch output callable, and Command builder."""
from pathlib import Path

import pytest
from helpers import render

import nanobuild as nb


class TestDependsAlias:
    def test_depends_is_a_phony_alias(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        target = env.Depends(objs, "stage1")[0]
        # Same behaviour as Phony: output is an alias, builder is the phony builder.
        from nanobuild.alias import Alias
        assert isinstance(target.output, Alias)
        assert str(target.output) == "stage1"

    def test_depends_renders_as_phony_rule(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        objs = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
        text = render(env.Depends(objs, "stage1"))
        assert "build stage1: phony" in text
        # No custom rule is emitted for the alias.
        assert "Depends_0" not in text and "Phony_0" not in text


class TestBatchOutputCallable:
    def test_callable_maps_each_input(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        objs = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
        backups = env.Copy(objs, output=lambda p: p.with_suffix(".o.bak"))
        outputs = sorted(str(t.output) for t in backups)
        assert outputs == [str(Path("build/a.o.bak")), str(Path("build/b.o.bak"))]

    def test_callable_on_multi_input_builder_raises(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        with pytest.raises(ValueError) as exc:
            env.CXXLink(objs, output=lambda p: p)
        assert "single-input" in str(exc.value)

    def test_string_returned_by_callable_goes_to_build_dir(self):
        env = nb.Environment(source_dir="src", build_dir="out")
        srcs = [env.source("a.cpp")]
        targets = env.Copy(srcs, output=lambda p: p.name + ".copy")
        assert targets[0].output == Path("out/a.cpp.copy")


class TestCommandBuilder:
    def test_command_requires_command_argument(self):
        env = nb.Environment()
        with pytest.raises(ValueError) as exc:
            env.Command(env.source("a.bin"), "out.bin")
        assert "command" in str(exc.value)

    def test_command_requires_output(self):
        env = nb.Environment()
        with pytest.raises(ValueError) as exc:
            env.Command(env.source("a.bin"), command="cp {IN} {OUT}")
        assert "explicit output" in str(exc.value)

    def test_command_renders_rule_with_in_out_translated(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        target = env.Command(env.source("a.img"), "disk.img",
                             command="dd if={IN} of={OUT} bs=512")
        text = render(target)
        assert "rule Command_0" in text
        assert "command = dd if=$in of=$out bs=512" in text
        assert "build build/disk.img: Command_0 src/a.img" in text.replace("\\", "/")

    def test_identical_commands_share_one_rule(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        a = env.Command(env.source("a.in"), "a.out", command="touch {OUT}")
        b = env.Command(env.source("b.in"), "b.out", command="touch {OUT}")
        text = render([a, b])
        assert text.count("rule Command_0") == 1
        assert "rule Command_1" not in text

    def test_distinct_commands_get_distinct_rules(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        a = env.Command(env.source("a.in"), "a.out", command="touch {OUT}")
        b = env.Command(env.source("b.in"), "b.out", command="echo hi > {OUT}")
        text = render([a, b])
        assert "rule Command_0" in text
        assert "rule Command_1" in text

    def test_literal_braces_in_command_are_preserved(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        target = env.Command(env.source("a.in"), "a.out",
                             command="find {IN} -exec cp {} {OUT} ;")
        text = render(target)
        # {IN}/{OUT} translated, but the literal {} left intact.
        assert "find $in -exec cp {} $out ;" in text


class TestSharedTargetDedup:
    def test_diamond_dependency_emits_each_target_once(self):
        env = nb.Environment(source_dir="src", build_dir="build")
        objs = env.CXX([env.source("a.cpp")])
        # objs feeds both a Copy and a Depends node -> diamond.
        env.Copy(objs, output=lambda p: p.with_suffix(".bak"))
        stage = env.Depends(objs, "stage")
        text = render([stage, env.Copy(objs, output=lambda p: p.with_suffix(".bak2"))])
        # The single object build statement must appear exactly once despite multiple referrers.
        assert text.replace("\\", "/").count("build build/a.o: CXX_0") == 1
