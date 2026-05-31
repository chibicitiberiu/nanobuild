"""Tests for the friendlier error handling (feature #5)."""
import copy

import pytest

import nanobuild as nb


class TestUnknownBuilder:
    def test_attribute_error_lists_available_builders(self):
        env = nb.Environment()
        with pytest.raises(AttributeError) as exc:
            env.Nope([])
        assert "Nope" in str(exc.value)
        assert "CXX" in str(exc.value)  # available builders are suggested

    def test_build_with_unknown_id_raises_value_error(self):
        env = nb.Environment()
        with pytest.raises(ValueError) as exc:
            env.build("DoesNotExist", [])
        assert "DoesNotExist" in str(exc.value)

    def test_dunder_lookups_do_not_recurse(self):
        # copy.deepcopy probes attributes like __deepcopy__/__getstate__ via __getattr__;
        # this must raise AttributeError cleanly rather than recursing on self.builders.
        env = nb.Environment(CFLAGS=["-g"])
        clone = copy.deepcopy(env)
        assert clone["CFLAGS"] == ["-g"]


class TestMissingOption:
    def test_missing_option_message_is_helpful(self):
        env = nb.Environment()
        with pytest.raises(KeyError) as exc:
            _ = env["NOSUCH"]
        assert "NOSUCH" in str(exc.value)

    def test_get_uses_same_path(self):
        env = nb.Environment()
        with pytest.raises(KeyError):
            env.get("NOSUCH")


class TestOutputRequired:
    def test_multi_input_builder_without_output_raises(self):
        env = nb.Environment()
        objs = env.CXX([env.source("a.cpp")])
        with pytest.raises(ValueError) as exc:
            env.CXXLink(objs)
        assert "explicit output" in str(exc.value)

    def test_copy_without_output_raises(self):
        env = nb.Environment()
        with pytest.raises(ValueError) as exc:
            env.Copy(env.source("a.txt"))
        assert "explicit output" in str(exc.value)
