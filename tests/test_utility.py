"""Unit tests for nanobuild.utility.Utility."""
from pathlib import Path

from nanobuild import Utility


class TestFlattenList:
    def test_none_returns_empty(self):
        assert Utility.flatten_list(None) == []

    def test_string_is_not_split(self):
        assert Utility.flatten_list("abc") == ["abc"]

    def test_scalar_is_wrapped(self):
        assert Utility.flatten_list(5) == [5]

    def test_nested_lists_are_flattened(self):
        assert Utility.flatten_list([1, [2, [3, 4]], 5]) == [1, 2, 3, 4, 5]

    def test_none_items_are_dropped(self):
        assert Utility.flatten_list([1, None, 2, [None, 3]]) == [1, 2, 3]

    def test_strings_inside_list_kept_whole(self):
        assert Utility.flatten_list(["-g", ["-O2", "-Wall"]]) == ["-g", "-O2", "-Wall"]


class TestFlattenArgsList:
    def test_string_passthrough(self):
        assert Utility.flatten_args_list("already a string") == "already a string"

    def test_list_joined_by_spaces(self):
        assert Utility.flatten_args_list(["-g", "-O2"]) == "-g -O2"

    def test_nested_list_flattened(self):
        assert Utility.flatten_args_list(["-g", ["-O2", "-Wall"]]) == "-g -O2 -Wall"

    def test_items_with_spaces_are_quoted(self):
        assert Utility.flatten_args_list(["-I", "my dir"]) == '-I "my dir"'

    def test_quoting_can_be_disabled(self):
        assert Utility.flatten_args_list(["my dir"], quote_spaces=False) == "my dir"


class TestPathToString:
    def test_none_returns_none(self):
        assert Utility.path_to_string(None) is None

    def test_path_is_resolved_to_absolute(self):
        result = Utility.path_to_string(Path("foo/bar.c"))
        assert Path(result).is_absolute()
        assert result.endswith("bar.c") or result.endswith("bar.c".replace("/", "\\"))

    def test_plain_string_passthrough(self):
        assert Utility.path_to_string("some/string") == "some/string"
