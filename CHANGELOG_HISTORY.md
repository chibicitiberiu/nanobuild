# Changelog history

## 0.4.1 - 2026-05-31

- Added a Documentation link (https://chibicitiberiu.github.io/nanobuild/) to the package's PyPI
  metadata and the README.

## 0.4 - 2026-05-31

- Added a `Command` builder for arbitrary, per-invocation shell build steps
  (`env.Command(inputs, output, command="...")`), e.g. generating disk images or installing a bootloader.
- Added a cross-platform `Copy` builder.
- Added `Depends` as an alias for `Phony`, for pinning build ordering.
- Batch mapping: a builder's `output=` argument now accepts a callable, mapping a single-input
  builder over a list of inputs and deriving each output (generalises the `%.o: %.c` pattern).
- Options are now stored as variables in the generated `build.ninja`, and only builders actually
  used by the graph emit a rule.
- Deterministic `build.ninja` output: stable rule names and sorted `source_glob`.
- Shared/diamond dependencies are now emitted once (previously produced duplicate build statements).
- Friendlier error messages (unknown builder, missing option, missing output).
- Full type hints across the codebase, checked with mypy and ruff.
- Added an automated test suite and CI.
- Fixed `for_subdir(deep_clone=True)` which previously shared the parent's options.

Released versions are prepended below automatically by the release workflow (newest first).
