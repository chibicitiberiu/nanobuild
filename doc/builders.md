# Builders

A **builder** is a recipe: it knows how to turn one or more input files into output files by
running a command. Builders are the nanobuild equivalent of a rule in `make` or a `Builder` in
SCons. Every [environment](environments.md) carries a set of builders, and invoking one produces
[targets](#targets) that form the build graph.

## Invoking a builder

Builders are accessed as methods on an environment. The general form is:

```Python
targets = env.<BuilderName>(inputs, output=None, deps=None, **kwargs)
```

* `inputs` — a file path, a string, a `Target`, or an (arbitrarily nested) list of these. Strings
  are resolved relative to the environment's source directory.
* `output` — the output file name (resolved relative to the build directory). For some builders
  this is optional; see [output handling](#single-input-vs-multi-input) below.
* `deps` — *order-only* dependencies: files that must be built first but that do not, on their own,
  force a rebuild (header files are the typical case).
* `**kwargs` — any extra named arguments temporarily override environment options **for this call
  only** (nanobuild clones the environment internally, so the original is left untouched).

The return value is always a **list of `Target` objects**, even when only one is produced. Targets
can be passed as `inputs` to other builders, which is how dependencies are chained:

```Python
objects = env.CXX(env.source_glob('**/*.cpp'))   # many .o targets
binary  = env.CXXLink(objects, 'app')            # one executable target
nb.run(binary)
```

## Built-in builders

| Builder            | Option(s) used                     | Command                                       | Multi-input | Autogenerates output |
|--------------------|------------------------------------|-----------------------------------------------|:-----------:|:--------------------:|
| `AS`               | `AS`, `ASFLAGS`                    | `{AS} {ASFLAGS} -o {OUT} {IN}`                | no          | yes (`.o`)           |
| `CC`               | `CC`, `CCFLAGS`, `CFLAGS`          | `{CC} {CCFLAGS} {CFLAGS} -c -o {OUT} {IN}`    | no          | yes (`.o`)           |
| `CPP` / `CXX`      | `CXX`, `CXXFLAGS`, `CFLAGS`        | `{CXX} {CXXFLAGS} {CFLAGS} -c -o {OUT} {IN}`  | no          | yes (`.o`)           |
| `LDLink`           | `LD`, `LINKFLAGS`, `LIBS`          | `{LD} {LINKFLAGS} -o {OUT} {IN} {LIBS}`       | yes         | no                   |
| `CCLink`           | `CC`, `LINKFLAGS`, `LIBS`          | `{CC} {LINKFLAGS} -o {OUT} {IN} {LIBS}`       | yes         | no                   |
| `CPPLink` / `CXXLink` | `CXX`, `LINKFLAGS`, `LIBS`      | `{CXX} {LINKFLAGS} -o {OUT} {IN} {LIBS}`      | yes         | no                   |
| `StaticLink`       | `AR`                               | `{AR} -o {OUT} {IN}`                          | yes         | no                   |
| `Phony` / `Depends`| —                                  | (no command)                                  | yes         | no                   |
| `Copy`             | —                                  | `cp {IN} {OUT}` / `copy /Y {IN} {OUT}`        | no          | no                   |
| `Command`          | —                                  | (supplied per call via `command=`)            | yes         | no                   |

`CPP` and `CXX` are two names for the same C++ compile builder; likewise `CPPLink` and `CXXLink`,
and `Phony` and `Depends`.

`Copy` copies a single input file to its output (the command is chosen for the host platform).
Ninja creates the output's parent directory automatically, so no separate `mkdir` step is needed:

```Python
env.Copy(env.source('config.default.ini'), 'config.ini')
```

### Single-input vs multi-input

Builders that **autogenerate output** (`AS`, `CC`, `CPP`/`CXX`) can derive an output file name from
each input (e.g. `foo.cpp` → `build/foo.o`). You can therefore hand them a whole list of sources and
get one target per source back, without naming any outputs:

```Python
objects = env.CXX(env.source_glob('**/*.cpp'))   # one .o target per .cpp
```

Builders that are **multi-input** (the linkers and `StaticLink`) take many inputs but produce a
single output, so you must supply the `output` name:

```Python
binary = env.CXXLink(objects, 'app')
```

### Batch mapping with an output function

For a single-input builder you can pass a **callable** as `output` to map it over a list of inputs,
deriving each output from its input. This is the general form of the `%.o: %.c` pattern for any
builder (not just the compilers, which already autogenerate `.o` names):

```Python
# copy every header into the build dir, preserving names
env.Copy(env.source_glob('include/*.h'), output=lambda src: src.name)
```

The function receives each input path and returns the output name (a `str`, resolved against the
build directory, or a `Path`). This only works for single-input builders — multi-input builders
consume all their inputs into one output.

### Phony / Depends targets

`Phony` groups several targets under a single symbolic name without producing a file. The `output`
argument is required and is interpreted as the alias name:

```Python
objects = env.CXX(env.source_glob('**/*.cpp'))
all_objs = env.Phony(objects, 'objects')          # an alias, not a file
binary  = env.CXXLink(all_objs, 'app')
```

`Depends` is an alias for `Phony` that reads more naturally when the intent is purely to pin build
ordering (a fake node that other targets depend on). In the generated `build.ninja` both become
ninja's built-in `phony` rule.

### Command (arbitrary shell steps)

`Command` runs a one-off shell command, for build steps that aren't covered by a dedicated builder
(generating a disk image, installing a bootloader, running `objcopy`, ...). Supply the command via
`command=`, using `{IN}`/`{OUT}` for the inputs and output:

```Python
kernel = env.CXXLink(objects, 'kernel.elf')
image  = env.Command(kernel, 'disk.img', command='dd if={IN} of={OUT} bs=512 conv=notrunc')
```

Each distinct command becomes its own ninja rule (identical commands are shared). Only `{IN}` and
`{OUT}` are substituted, so literal braces in the command are left untouched; bake any other values
into the string with ordinary Python (e.g. an f-string).

## Creating custom builders

To create a custom builder, derive from `Builder` and implement `generate`:

```Python
import nanobuild as nb

class CXXBuilder(nb.Builder):
    name = ['CPP', 'CXX']          # one or more names the builder is invoked by
    multi_input = False            # True if the command accepts many inputs at once
    autogenerate_output = True     # True if it can derive an output path from an input

    def default_vars(self):
        # Options added to every environment that uses this builder (user-overridable).
        return {
            'CXX': 'g++',
            'CXXFLAGS': [],
            'CFLAGS': [],
        }

    def generate(self):
        # The command template. {NAME} placeholders are filled from environment options.
        return "{CXX} {CXXFLAGS} {CFLAGS} -c -o {OUT} {IN}"

    def generate_output_file(self, source):
        # Only needed when autogenerate_output is True.
        return source.with_suffix('.o')
```

Register a custom builder by passing it to an environment (or `clone` / `add_builders`):

```Python
env = nb.Environment(builders=[MyBuilder()])
```

### Key concepts

* **`name`** — the attribute name(s) the builder is invoked by on an environment. May be a single
  string or a list of aliases.
* **`generate()`** — returns the command template used in the ninja rule. Placeholders written as
  `{NAME}` are substituted from environment options via `str.format_map`.
* **`{IN}` and `{OUT}`** — reserved placeholders, replaced with the rule's input and output files.
* **`default_vars()`** — options the builder contributes to the environment. They are merged in when
  the environment is created and can be overridden by the user.
* **`multi_input`** — `False` if the command handles a single input file; `True` for commands like
  linkers that consume many inputs at once.
* **`autogenerate_output`** — `True` if the builder can compute an output path from an input path.
  Such builders should implement `generate_output_file`. When a single-input builder receives a list
  of inputs, nanobuild uses this to emit one target per input automatically.

### How options reach the generated rules

Option values are not baked into rule commands. Instead, each environment's options are written to
`build.ninja` as ninja variables (namespaced by environment, e.g. `e0_CXXFLAGS`), and the rules
reference them:

```ninja
e0_CXXFLAGS = -O2
rule CXX_0
  command = ${e0_CXX} ${e0_CXXFLAGS} ${e0_CFLAGS} -c -o $out $in
```

This keeps the generated file readable and lets you inspect (or override) values at the ninja level.
`{IN}`/`{OUT}` map to ninja's built-in `$in`/`$out`. Only builders actually used by the graph get a
rule, so `build.ninja` doesn't carry rules for builders the build never invokes.

## Targets

Every builder invocation returns a list of `Target` objects. A target records its builder, inputs,
order-only dependencies, output, and the environment it belongs to. Pass targets as inputs to other
builders to build up the dependency graph, and pass the final target(s) to `nb.run(...)` to generate
`build.ninja` and run ninja.

See also: [Environments](environments.md).
