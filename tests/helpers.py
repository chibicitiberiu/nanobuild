"""Plain (non-fixture) helpers shared across the nanobuild test suite."""
import nanobuild as nb
from nanobuild.main import Nanobuild


def render(*targets) -> str:
    """Render the build.ninja text for the given targets without touching the filesystem."""
    return Nanobuild().generate_ninja(*targets)


def sample_targets(source_dir, build_dir):
    """Build a representative target graph: compile two sources, link them.

    Returns the final link target. Used by determinism / golden tests so the
    exact same logical graph can be produced from independent Environment objects.
    """
    env = nb.Environment(source_dir=str(source_dir), build_dir=str(build_dir), CCFLAGS=["-g"])
    objects = env.CXX([env.source("a.cpp"), env.source("b.cpp")])
    return env.CXXLink(objects, "app")
