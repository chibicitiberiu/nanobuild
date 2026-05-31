"""Determinism guardrails.

A build system must produce the *same* build.ninja for the same inputs, run after
run and machine after machine. These tests pin that contract down. They currently
fail because:

  * rule names embed ``id(environment)`` (a memory address), so they differ every run;
  * ``Environment.source_glob`` returns results in filesystem order, which is not stable.

Once those are fixed, these tests lock the behaviour in.
"""
from helpers import render, sample_targets


def test_same_graph_renders_identically(tmp_path):
    """Two independently constructed-but-identical graphs must render byte-for-byte the same."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.cpp").write_text("int a();\n")
    (src / "b.cpp").write_text("int b();\n")

    first = render(sample_targets(src, tmp_path / "build"))
    second = render(sample_targets(src, tmp_path / "build"))

    assert first == second


def test_source_glob_is_sorted(tmp_path):
    """source_glob must return a deterministic (sorted) ordering regardless of fs order."""
    import nanobuild as nb

    # Create files in an order unlikely to match sorted order.
    for name in ["z.cpp", "a.cpp", "m.cpp", "b.cpp"]:
        (tmp_path / name).write_text("\n")

    env = nb.Environment(source_dir=str(tmp_path))
    result = env.source_glob("*.cpp")
    names = [p.name for p in result]

    assert names == sorted(names)


def test_glob_order_does_not_leak_into_link_command(tmp_path):
    """The order of object files in a link command must be stable across runs."""
    import nanobuild as nb

    for name in ["z.cpp", "a.cpp", "m.cpp"]:
        (tmp_path / name).write_text("\n")

    def build():
        env = nb.Environment(source_dir=str(tmp_path), build_dir=str(tmp_path / "build"))
        objs = env.CXX(env.source_glob("*.cpp"))
        return env.CXXLink(objs, "app")

    assert render(build()) == render(build())
