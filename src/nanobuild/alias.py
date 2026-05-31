from __future__ import annotations


class Alias(object):
    """A symbolic name for a build target that has no real file output.

    Phony targets (see :class:`nanobuild.builder.PhonyBuilder`) group other targets under a
    single name without producing a file on disk. Wrapping the name in ``Alias`` lets the rest
    of nanobuild distinguish "this is a logical name" from "this is a real output :class:`~pathlib.Path`",
    so paths get normalised relative to the working directory while aliases are emitted verbatim.
    """

    def __init__(self, alias: str) -> None:
        self.alias: str = alias

    def __repr__(self) -> str:
        return self.alias
