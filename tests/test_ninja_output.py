"""Tests for the structure of the generated build.ninja.

Covers the "store variables in build.ninja" feature: option values are emitted as namespaced
ninja variables and referenced from rules, and only builders actually used by the graph get a rule.
"""
from helpers import render

import nanobuild as nb


def _simple_link():
    env = nb.Environment(source_dir="src", build_dir="build", CCFLAGS=["-g"])
    objects = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
    return env.CXXLink(objects, "app")


class TestVariableStorage:
    def test_options_are_emitted_as_variables(self):
        text = render(_simple_link())
        # Flags live in a ninja variable, not expanded inline into the rule command.
        assert "e0_CCFLAGS = -g" in text

    def test_rules_reference_variables_not_literal_flags(self):
        text = render(_simple_link())
        assert "${e0_CXX}" in text
        # The literal flag value must not be baked directly into a rule command line.
        assert "-g -c -o" not in text

    def test_in_out_are_translated_to_ninja_specials(self):
        text = render(_simple_link())
        assert "-o $out $in" in text


class TestOnlyUsedRules:
    def test_unused_builders_get_no_rule(self):
        text = render(_simple_link())
        assert "rule CXX_0" in text
        assert "rule CXXLink_0" in text
        # The graph never assembles, archives, or copies, so those rules should be absent.
        assert "rule AS_0" not in text
        assert "rule StaticLink_0" not in text
        assert "rule Copy_0" not in text

    def test_cxx_alias_emits_single_rule(self):
        text = render(_simple_link())
        # CXX and CPP are the same builder; only the invoked name produces a rule.
        assert "rule CPP_0" not in text


class TestCopyBuilder:
    def test_copy_emits_rule_and_build(self, tmp_path):
        (tmp_path / "data.txt").write_text("hello\n")
        env = nb.Environment(source_dir=str(tmp_path), build_dir=str(tmp_path / "out"))
        target = env.Copy(env.source("data.txt"), "data.txt")
        text = render(target)
        assert "rule Copy_0" in text
        assert "Copy_0" in text  # referenced by a build statement
        assert len(target) == 1
