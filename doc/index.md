# nanobuild

A very simple and customizable build system made in Python that generates [Ninja](https://ninja-build.org/).

nanobuild lets you describe a build in plain Python — using environments, options, and builders —
and emits a `build.ninja` file that Ninja then executes. It aims to be lightweight and easy to
control, while giving you the full power of Python for customization.

## Installation

```
python3 -m pip install nanobuild
```

## A first build

```python
#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(CCFLAGS=['-g'])

sources = env.source_glob('**/*.cpp')
objects = env.CXX(sources)
binary  = env.CXXLink(objects, 'app')

nb.run(binary)
```

Running `./build.py` generates `build.ninja` and invokes Ninja to build `app`.

## Where to next

- **[Environments](environments.md)** — creating, cloning and customizing environments, options, and paths.
- **[Builders](builders.md)** — the built-in builders (compilers, linkers, `Copy`, `Command`, `Phony`/`Depends`) and how to write your own.
- **[Submodules](submodules.md)** — multi-directory builds with `for_subdir` and `import_file`.

The source lives on [GitHub](https://github.com/chibicitiberiu/nanobuild).
