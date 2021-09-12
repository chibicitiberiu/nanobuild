# Nanobuild

A very simple and customizable build system made in Python that generates Ninja.

### Installation

```
python3 -m pip install nanobuild
```

### Why another build system?

Modern build systems are cool, but for system programming where you need fine control over what gets compiled and how, a lot of build systems are inadequate and very difficult to control. CMake has dozens of variables that will change depending on the host configuration, and because of that it often feels like playing whack-a-mole whenever something about the build changes. Make is probably the best suited for that, but its syntax and features leave a lot to be desired. SCons is also a very good option, but you often feel like you're fighting the build system and it's not as fast as Ninja.

All of these reasons combined made me want to build my own build system that is simple to use, is built upon a powerful scripting language like Python that allows an infinite degree of customization, and is very lightweight.

### Example usage

##### build.py:

```Python
#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(
    CCFLAGS=['-g']
)

sources = env.source_glob('**/*.cpp')
objects = env.CXX(sources)
binary = env.CXXLink(objects, 'test')

nb.run(binary)
```

Usage: `./build.py`

### Environments

One of the core concepts in *nanobuild* is the `Environment`, which is essentially a collection of options and builders. Any number of environments can be created. The `clone` method can be used to create copies of an environment. The `append` and `replace` methods are convenient ways of adding many variables using named arguments:

```Python
env = nb.Environment(...)
env.append(CFLAGS = ['-g', '-O3'], LIBS = ['-lpng'])
env.replace(CXX = 'clang')
```

The source and build directories are also configured through the environment. The convenient `source` and `dest` methods can be used to generate file paths to things in the source directory, or in the build directory.

```Python
sources = [ env.source('a.c'), env.source('b.c') ]
sources += env.source_glob('**/*.cpp')                   # glob is also supported

build_file = env.dest('a.o')                             # relative to build directory
```

The builders can also be accessed through the environment. Currently, these built-in builders exist:

* `AS`
* `CC`
* `CPP` (or `CXX`)
* `LDLink`
* `CCLink`
* `CXXLink`
* `StaticLink`
* `Phony` (currently broken)

To invoke a builder, you just have to invoke `env.Builder_Name(inputs, output, **kwargs)`. The function will return a `Target` object (or a list of target objects) that can be used as inputs to other targets.

Some builders (`AS`, `CC`, `CPP` and `CXX`) will generate their own output files, in these cases specifying the output isn't necessary. Currently this is the only way of calling these builders with multiple inputs; if you want to set your own target, you have to call the builder for each input file individually.

### Creating custom builders

To create a custom builder, just derive from the `Builder` class.

Here is an example of how a builder looks like:

```Python
class CXXBuilder(Builder):
    multi_input = False
    autogenerate_output = True

    def default_vars(self):
        return {
            'CXX': 'g++',
            'CCFLAGS': [],
            'CXXFLAGS': []
        }

    def generate(self) -> Optional[str]:
        return "{CXX} {CCFLAGS} {CXXFLAGS} -c -o {OUT} {IN}"

    def generate_output_file(self, source: Path) -> Optional[Path]:
        return source.with_suffix('.o')
```

This is the C++ builder. As you can see, a builder will have some default options that will be added to the Environment (these can be overriden by the user). The generate function generates a command that will be used in the ninja script; this uses the `str.format_map` builtin function, and will replace all the `{ }` statements with variables from the environment.

The `{IN}` and `{OUT}` variables are special (and reserved), and they will be replaced with the input and output files of the command.

Some builders can only take in a single source file (like the CXX builder in this example), which is why `multi_input = False`. Other builders, like the linker will take multiple inputs, so in that case `multi_input` should be set to True.

The `autogenerate_output` tells nanobuild if this builder can generate an output file path from a source file path (i.e. replace .cpp with .o). Builders that have this capability should implement the `generate_output_file` method. The way this mechanism works is that nanobuild can take a list of input files, and if it detects that the builder isn't multi-input but it can generate output files, it will do that instead.

### TODOs

* find a more graceful way of handling batches (i.e. multiple input files to builders that can only take single inputs)
* more builtin builders
* better error handling
* store variables in `build.ninja`