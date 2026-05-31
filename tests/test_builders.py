"""Unit tests for the built-in builders and their command templates."""
from pathlib import Path

import nanobuild as nb
from nanobuild.builder import (
    ASBuilder,
    CBuilder,
    CCLinkBuilder,
    CopyBuilder,
    CXXBuilder,
    CXXLinkBuilder,
    LDLinkBuilder,
    PhonyBuilder,
    StaticLinkBuilder,
)


class TestCommandTemplates:
    def test_as_command(self):
        assert ASBuilder().generate() == "{AS} {ASFLAGS} -o {OUT} {IN}"

    def test_cc_command(self):
        assert CBuilder().generate() == "{CC} {CCFLAGS} {CFLAGS} -c -o {OUT} {IN}"

    def test_cxx_command(self):
        assert CXXBuilder().generate() == "{CXX} {CXXFLAGS} {CFLAGS} -c -o {OUT} {IN}"

    def test_static_link_command(self):
        assert StaticLinkBuilder().generate() == "{AR} -o {OUT} {IN}"

    def test_phony_has_no_command(self):
        assert PhonyBuilder().generate() is None

    def test_copy_command_is_platform_appropriate(self):
        import os

        command = CopyBuilder().generate()
        assert command is not None
        assert "{IN}" in command and "{OUT}" in command
        assert command.startswith("copy" if os.name == "nt" else "cp")


class TestOutputGeneration:
    def test_compilers_emit_object_files(self):
        for builder in (ASBuilder(), CBuilder(), CXXBuilder()):
            assert builder.generate_output_file(Path("foo/bar.cpp")) == Path("foo/bar.o")

    def test_linkers_do_not_autogenerate(self):
        for builder in (LDLinkBuilder(), CCLinkBuilder(), CXXLinkBuilder(), StaticLinkBuilder()):
            assert builder.autogenerate_output is False
            assert builder.multi_input is True


class TestBuilderRegistration:
    def test_all_documented_builders_are_available(self):
        env = nb.Environment()
        expected = {"AS", "CC", "CPP", "CXX", "LDLink", "CCLink",
                    "CPPLink", "CXXLink", "StaticLink", "Phony", "Copy"}
        assert expected <= set(env.builders.keys())

    def test_cxx_aliases_share_one_builder(self):
        env = nb.Environment()
        assert env.builders["CPP"] is env.builders["CXX"]

    def test_custom_builder_can_be_added(self):
        class MyBuilder(nb.Builder):
            name = "Touch"

            def generate(self):
                return "touch {OUT}"

        env = nb.Environment(builders=[MyBuilder()])
        assert "Touch" in env.builders

    def test_builder_default_vars_present(self):
        env = nb.Environment()
        # Defaults injected from builders
        assert env["CC"] == "gcc"
        assert env["CXX"] == "g++"
        assert env["AR"] == "ar"
