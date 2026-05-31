# Environments

One of the core concepts in *nanobuild* is the `Environment`, which is a collection of options and builders.

## Creating environments

### The constructor

```Python
import nanobuild as nb
env = nb.Environment()
```

The constructor allows setting options in 2 ways, using the `args` named argument which accepts a dictionary, or using named arguments.

```Python
import nanobuild as nb
env = nb.Environment(CXX='g++',
                     args={
                         'CC': 'gcc'
                     })
```

The `source_dir` and `build_dir` arguments allow changing the directory where the source code is located, and where the build files will be placed. These are, of course, optional; by default, the current working directory will be used as the `source_dir`, and a `build` directory will be used for the build files.

```Python
import nanobuild as nb
env = nb.Environment(source_dir='src',
                     build_dir='build')
```

The `builders` argument allows adding custom builders. See [the page about environments](environments.md) for more details.

### Cloning environments

Another method of creating an environment is to clone an existing one, which can be done through the `clone` method. This will create a deep copy of the current environment.

```Python
import nanobuild as nb
env = nb.Environment(CFLAGS='-O2')
# ...

debug = env.clone(CONFIGURATION='debug')
debug.append(CFLAGS=['-g'])

release = env.clone(CONFIGURATION='release')
release.append(CFLAGS=['-Wall'])

print(env['CFLAGS'])                    # ['-O2']
print(debug['CFLAGS'])                  # ['-O2', '-g']
print(release['CFLAGS'])                # ['-O2', '-Wall']
```

The `clone` method has the same arguments as the constructor, and they allow customizing the cloned environment:

* the `source_dir` or `build_dir` arguments allow modifying the directory where source files are located, and where build files will be placed.
* builders in the `builders` argument will be added, as if the `add_builders` method was called.  
* `args` and any other named argument (`kwargs`) will replace variables that already exist in the environment, as if the `replace` method was called.

### Submodule workflow

The `for_subdir` method allows creating an environment that shares all the options and builders with the existing environment, but the source and build directories are a subdirectory of the directory set in the current environment.

```Python
import nanobuild as nb
env = nb.Environment(source_dir='src',
                     build_dir='build')
# ...

mylib_env1 = env.for_subdir('mylib')                     # source_dir is now 'src/mylib'
                                                         # build_dir is now 'build/mylib'
                                        
mylib_env2 = env.for_subdir('mylib', 'build_mylib')      # source_dir is now 'src/mylib'
                                                         # build_dir is now 'build/build_mylib'

mylib_env3 = env.for_subdir('mylib',                     # same as above, but using named argument
                            build_subdir='build_mylib')
```

Note that any changes to the options or builders of one environment will be reflected in all the other ones. If this behavior is not desired, set `deep_clone=True`.

```Python
import nanobuild as nb
env = nb.Environment(CFLAGS=['-O2'])
module1_env = env.for_subdir('module1')
module2_env = env.for_subdir('module2', deep_clone=True)

print(env['CFLAGS'])                    # ['-O2']
print(module1_env['CFLAGS'])            # ['-O2']
print(module2_env['CFLAGS'])            # ['-O2']

env.append(CFLAGS=['-g'])
module1_env.append(CFLAGS=['-Wall'])
module2_env.append(CFLAGS=['-Werror'])

print(env['CFLAGS'])                    # ['-O2', '-g', '-Wall']
print(module1_env['CFLAGS'])            # ['-O2', '-g', '-Wall']
print(module2_env['CFLAGS'])            # ['-O2', '-Werror']
```

## Customizing options

Options can be customized in a number of ways. Environments allow setting options using the same way as dictionaries:

```Python
import nanobuild as nb
env = nb.Environment()

env.set('CFLAGS', ['-O2'])
env.set('CFLAGS', env.get('CFLAGS') + ['-g'])
# or
env['CFLAGS'] = ['-O2']
env['CFLAGS'] += ['-g']

# Deleting is also possible:
env.pop('CFLAGS')
# or
del env['CFLAGS']
```

To set multiple options at the same time, there are 2 convenient methods: `replace` and `append`. For both, if the provided option doesn't exist, it is created with the given value. However, if the option already exists:

* the `replace` method will behave in a similar way to `dict.update`: it will replace the value of the existing option with the provided one.
* the `append` method will append to the existing variable, the value provided (through the use of the + operator)

```Python
import nanobuild as nb
env = nb.Environment(CFLAGS=['-g'],
                     SOMESTRING='foo')

env1 = env.clone()
env1.replace(CFLAGS=['-O2'],
             SOMESTRING='bar')
print(env1['CFLAGS'])           # ['-O2']
print(env1['SOMESTRING'])       # bar

env2 = env.clone()
env2.append(CFLAGS=['-O2'],
            SOMESTRING='bar')
print(env2['CFLAGS'])           # ['-g', '-O2']
print(env2['SOMESTRING'])       # foobar
```

## Locating files

The source and build directories are configured through the environment. The convenient `source`
and `dest` methods generate file paths to things in the source directory, or in the build directory:

```Python
sources = [ env.source('a.c'), env.source('b.c') ]
sources += env.source_glob('**/*.cpp')                   # glob is also supported

build_file = env.dest('a.o')                             # relative to build directory
```

`source_glob` returns its matches in sorted order, so the resulting build is reproducible regardless
of the order the underlying filesystem reports files in. Absolute paths passed to `source`/`dest` are
returned unchanged.

## Building things

To get something to build, you invoke a builder through the environment:

```Python
targets = env.<BuilderName>(inputs, output=None, deps=None, **kwargs)
```

Each call returns a list of `Target` objects, which can be passed as inputs to other builders to
form the dependency graph. The built-in builders are `AS`, `CC`, `CPP`/`CXX`, `LDLink`, `CCLink`,
`CPPLink`/`CXXLink`, `StaticLink`, `Phony`, and `Copy`. A full reference — including each builder's command,
options, output handling, and how to write your own — lives in **[Builders](builders.md)**.

```Python
objects = env.CXX(env.source_glob('**/*.cpp'))   # compile every .cpp to a .o
binary  = env.CXXLink(objects, 'app')            # link the objects into an executable
nb.run(binary)                                   # generate build.ninja and run ninja
```

Extra named arguments (`**kwargs`) override environment options for that single call only, by
internally cloning the environment — the original environment is left untouched:

```Python
# build just this file without optimisation, leaving env's CXXFLAGS intact
debug_obj = env.CXX(env.source('tricky.cpp'), CXXFLAGS=['-O0', '-g'])
```
