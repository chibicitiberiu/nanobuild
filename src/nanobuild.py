import abc
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Iterable, Union, List

import ninja_syntax


class Utility:
    @staticmethod
    def flatten_list(data):
        new_list = []

        if data is None:
            return new_list

        elif (not isinstance(data, Iterable)) or isinstance(data, str):
            new_list.append(data)

        else:
            for item in data:
                if item is None:
                    continue
                elif isinstance(item, Iterable) and not isinstance(item, str):
                    new_list.extend(Utility.flatten_list(item))
                else:
                    new_list.append(item)

        return new_list

    @staticmethod
    def flatten_args_list(args, quote_spaces: bool = True):
        if isinstance(args, str):
            return args

        args = Utility.flatten_list(args)
        s = ''
        for arg in args:
            if quote_spaces and ' ' in arg:
                s += f'"{arg}" '
            else:
                s += str(arg) + ' '
        return s.strip()


class Builder(abc.ABC):
    name: Union[str, List[str]] = 'default'
    multi_input = False
    autogenerate_output = False

    def default_vars(self) -> Dict[str, Any]:
        return {}

    @abc.abstractmethod
    def generate(self) -> Optional[str]:
        pass

    def generate_output_file(self, source: Path) -> Optional[Path]:
        return None


class ASBuilder(Builder):
    name = 'AS'
    multi_input = False
    autogenerate_output = True

    def default_vars(self):
        return {
            'AS': 'as',
            'ASFLAGS': []
        }

    def generate(self) -> Optional[str]:
        return "{AS} {ASFLAGS} -o {OUT} {IN}"

    def generate_output_file(self, source: Path) -> Optional[Path]:
        return source.with_suffix('.o')


class CBuilder(Builder):
    name = 'CC'
    multi_input = False
    autogenerate_output = True

    def default_vars(self):
        return {
            'CC': 'gcc',
            'CCFLAGS': [],
            'CFLAGS': []
        }

    def generate(self) -> Optional[str]:
        return "{CC} {CCFLAGS} {CFLAGS} -c -o {OUT} {IN}"

    def generate_output_file(self, source: Path) -> Optional[Path]:
        return source.with_suffix('.o')


class CXXBuilder(Builder):
    name = ['CPP', 'CXX']
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


class PhonyBuilder(Builder):
    name = 'Phony'
    multi_input = True
    autogenerate_output = False

    def generate(self) -> Optional[str]:
        return None


class StaticLinkBuilder(Builder):
    name = 'StaticLink'
    multi_input = True
    autogenerate_output = False

    def default_vars(self):
        return {
            'AR': 'ar',
        }

    def generate(self) -> Optional[str]:
        return "{AR} -o {OUT} {IN}"


class LDLinkBuilder(Builder):
    name = 'LDLink'
    multi_input = True
    autogenerate_output = False

    def default_vars(self):
        return {
            'LD': 'ld',
            'LINKFLAGS': [],
            'LIBS': []
        }

    def generate(self) -> Optional[str]:
        return "{LD} {LINKFLAGS} -o {OUT} {IN} {LIBS}"


class CCLinkBuilder(Builder):
    name = 'CCLink'
    multi_input = True
    autogenerate_output = False

    def default_vars(self):
        return {
            'CC': 'gcc',
            'LINKFLAGS': [],
            'LIBS': []
        }

    def generate(self) -> Optional[str]:
        return "{CC} {LINKFLAGS} -o {OUT} {IN} {LIBS}"


class CXXLinkBuilder(Builder):
    name = ['CPPLink', 'CXXLink']
    multi_input = True
    autogenerate_output = False

    def default_vars(self):
        return {
            'CXX': 'g++',
            'LINKFLAGS': [],
            'LIBS': []
        }

    def generate(self) -> Optional[str]:
        return "{CXX} {LINKFLAGS} -o {OUT} {IN} {LIBS}"


class Target(abc.ABC):
    def __init__(self, builder_id, inputs, output, deps, environment):
        self.builder_id = builder_id
        self.output = output
        self.inputs = Utility.flatten_list(inputs)
        self.deps = Utility.flatten_list(deps)
        self.environment = environment


class Environment(object):

    DEFAULT_BUILDERS = (
        ASBuilder(),
        CBuilder(),
        CXXBuilder(),
        CXXBuilder(),
        LDLinkBuilder(),
        CCLinkBuilder(),
        CXXLinkBuilder(),
        StaticLinkBuilder(),
        #PhonyBuilder()
    )

    def __init__(self,
                 source_dir: Union[str, Path] = '.',
                 build_dir: Union[str, Path] = 'build',
                 args: Optional[Dict[str, Any]] = None,
                 environment: Optional[Dict[str, Any]] = None,
                 builders: Optional[Iterable[Builder]] = None,
                 **kwargs):

        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)
        self.__args: Dict[str, object] = {}
        self.env: Dict[str, Any] = environment or os.environ.copy()

        # setup builders
        self.builders: Dict[str, Builder] = {}
        self.add_builders(Environment.DEFAULT_BUILDERS)
        if builders is not None:
            self.add_builders(builders)

        # add builder default vars
        for builder in self.builders.values():
            self.__args.update(builder.default_vars())

        # add args and kwargs
        if args is not None:
            self.__args.update(args)
        if kwargs is not None:
            self.__args.update(kwargs)

    #
    # property setters/getters
    #

    def get(self, key):
        return self.__args.__getitem__(key)

    def __getitem__(self, key):
        return self.__args.__getitem__(key)

    def set(self, key, value):
        return self.__args.__setitem__(key, value)

    def __setitem__(self, key, value):
        self.__args.__setitem__(key, value)

    def append(self, **kwargs):
        for key, value in kwargs:
            if key in self.__args.keys():
                self.__args[key] += value
            else:
                self.__args[key] = value

    def replace(self, **kwargs):
        self.__args.update(kwargs)

    def pop(self, key):
        return self.__args.pop(key)

    def __delitem__(self, key):
        self.__args.__delitem__(key)

    def __iter__(self):
        return self.__args.items()

    #
    # env setters/getters
    #

    def get_env(self, key):
        return self.env.__getitem__(key)

    def set_env(self, key, value):
        return self.env.__setitem__(key, value)

    def append_env(self, **kwargs):
        for key, value in kwargs:
            if key in self.env.keys():
                self.env[key] += value
            else:
                self.env[key] = value

    def replace_env(self, **kwargs):
        self.env.update(kwargs)

    def pop_env(self, key):
        return self.env.pop(key)

    #
    # Misc operations
    #
    def clone(self) -> 'Environment':
        new_env = Environment()
        new_env.__args = self.__args.copy()
        new_env.env = self.env.copy()
        new_env.builders = self.builders.copy()
        return new_env

    def __repr__(self):
        return self.__args.__repr__()

    #
    # Files
    #
    def source(self, path: Union[str, Path]):
        """
        Returns a Path object relative to the source directory.
        :param path:
        :return:
        """
        if isinstance(path, str) and os.path.isabs(path):
            return Path(path)
        if isinstance(path, Path) and path.is_absolute():
            return path
        return Path(self.source_dir, path)

    def source_glob(self, pattern):
        return list(self.source_dir.glob(pattern))

    def dest(self, path: Union[str, Path]):
        """
        Returns a Path object relative to the destination directory.
        :param path:
        :return:
        """
        if isinstance(path, str) and os.path.isabs(path):
            return Path(path)
        if isinstance(path, Path) and path.is_absolute():
            return path
        return Path(self.build_dir, path)

    #
    # Builders
    #
    def add_builders(self, builders: Iterable[Builder]):
        for builder in builders:
            for name in Utility.flatten_list(builder.name):
                self.builders[name] = builder

    def preprocess_inputs(self, inputs):
        inputs = Utility.flatten_list(inputs)
        new_inputs = []
        for input in inputs:
            if isinstance(input, str):
                new_inputs.append(self.source(input))
            else:
                new_inputs.append(input)
        return new_inputs

    def build(self, builder_id, inputs, output=None, deps = None, **kwargs) -> List[Target]:
        builder = self.builders[builder_id]
        inputs = self.preprocess_inputs(inputs)
        deps = self.preprocess_inputs(deps)
        targets = []

        # Build env
        env = self
        if kwargs is not None and len(kwargs) > 0:
            env = self.clone()
            env.replace(**kwargs)

        # No output, we must be able to generate it
        if output is None and not builder.multi_input:
            if builder.autogenerate_output:
                # builder can autogenerate outputs, so we can emit multiple targets
                for input_item in inputs:
                    # obtain output file from input
                    input_file = input_item
                    if isinstance(input_item, Target):
                        input_file = input_item.output

                    if input_file.is_relative_to(self.source_dir):
                        input_file = self.dest(input_file.relative_to(self.source_dir))

                    output_item = builder.generate_output_file(input_file)
                    targets.append(Target(builder_id, input_item, output_item, deps, env))
                return targets
            else:
                raise ValueError("This builder only supports 1 input file!")

        if output is not None and isinstance(output, str):
            output = self.dest(output)

        # Simple case
        targets.append(Target(builder_id, inputs, output, deps, env))
        return targets

    def __getattr__(self, item):
        if item in self.builders.keys():
            return lambda inputs, output=None, **kwargs: self.build(item, inputs, output, **kwargs)
        raise AttributeError

    def prepare(self):
        final = {}
        for key, value in self.__args.items():
            final[key] = Utility.flatten_args_list(value)
        return final


class Nanobuild(object):
    def __init__(self):
        self.__environments: Dict[int, Environment] = {}

    def _preprocess(self, *targets):
        for target in targets:
            if isinstance(target, Target):
                if id(target.environment) not in self.__environments.keys():
                    self.__environments[id(target.environment)] = target.environment
                self._preprocess(*target.inputs)
                self._preprocess(*target.deps)

    def _generate_build_ninja(self, *targets):
        with open('build.ninja', 'w') as out:
            writer = ninja_syntax.Writer(out)

            # generate rules
            for env_id, env in self.__environments.items():
                for key, builder in env.builders.items():
                    env.set('IN', '$in')
                    env.set('OUT', '$out')
                    cmd = builder.generate().format_map(env.prepare())
                    writer.rule(f"{key}{env_id}", cmd)

            # generate build
            queue = [*targets]
            while len(queue) > 0:
                target = queue.pop(0)
                inputs = []
                order_only = []

                for input in target.inputs:
                    if isinstance(input, Target):
                        if input.output is None:
                            # TODO: process phony targets
                            pass
                        else:
                            inputs.append(str(input.output.resolve()))
                        queue.append(input)
                    elif isinstance(input, Path):
                        inputs.append(str(input.resolve()))
                    else:
                        inputs.append(str(input))

                for dep in target.deps:
                    if isinstance(dep, Target):
                        if dep.output is None:
                            # TODO: process phony targets
                            pass
                        else:
                            order_only.append(str(dep.output.resolve()))
                        queue.append(dep)
                    elif isinstance(dep, Path):
                        order_only.append(str(dep.resolve()))
                    else:
                        order_only.append(str(dep))

                output = target.output
                if output is not None and isinstance(output, Path):
                    output = str(output.resolve())

                writer.build(outputs=output,
                             rule=f"{target.builder_id}{id(target.environment)}",
                             inputs=inputs,
                             order_only=order_only)

            writer.close()

    def run(self, *targets):
        targets = Utility.flatten_list(targets)
        self._preprocess(*targets)
        self._generate_build_ninja(*targets)

        # run ninja, pass argv
        subprocess.run(['ninja', *sys.argv[1:]]).check_returncode()


def run(*targets):
    Nanobuild().run(*targets)
