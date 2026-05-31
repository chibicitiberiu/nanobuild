# Submodules / multi-directory builds

Larger projects are usually split across subdirectories, each with its own sources. nanobuild
supports this with two cooperating pieces:

* `Environment.for_subdir(...)` — derive an environment whose source/build directories point at a
  subdirectory (see [Environments → Submodule workflow](environments.md#submodule-workflow));
* `nanobuild.import_file(...)` — execute another `build.py` as a module, injecting variables (such as
  the environment) into it.

## `import_file`

```Python
import_file(file_name, **kwargs)
```

`import_file` loads the Python file at `file_name`, sets each keyword argument as a module-level
variable inside it, then executes it and returns the module. There is one important convenience: any
keyword argument that is an `Environment` is automatically rewritten with `for_subdir(<that file's
directory>)` before injection, so each submodule receives an environment already scoped to its own
folder.

## Example

This mirrors `examples/submodules`. The top-level `build.py` wires the submodules together:

```Python
#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(CCFLAGS=['-g'])

targets = {}
nb.import_file('bird/build.py',     targets=targets, env=env)
nb.import_file('not_bird/build.py', targets=targets, env=env)
nb.import_file('main/build.py',     targets=targets, env=env)

binary = env.CXXLink(targets.values(), 'test')
nb.run(binary)
```

A submodule's `build.py` (e.g. `bird/build.py`) receives `env` already scoped to `bird/` and
contributes its targets to the shared `targets` dictionary:

```Python
from typing import Dict
import nanobuild as nb

# These are injected by import_file; the annotations just keep editors happy.
env: nb.Environment
targets: Dict

sources = env.source_glob('**/*.cpp')
headers = [
    env.source_glob('**/*.hpp'),
    env.source_glob('**/*.h'),
]

targets['bird'] = env.CXX(sources, deps=headers)
```

Because the injected `env` is a *shallow* sub-environment by default, option changes made in one
module are visible in the others (handy for global flags). If a submodule needs its own isolated
options, create a deep clone — see
[Environments → Submodule workflow](environments.md#submodule-workflow) and the `deep_clone`
argument.

See also: [Environments](environments.md) · [Builders](builders.md).
