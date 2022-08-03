import os
from copy import deepcopy
from pathlib import Path
from typing import Union, List, Optional, Dict, Any, Iterable

from .utility import Utility
from .target import Target
from .builder import Builder, ASBuilder, CBuilder, CXXBuilder, LDLinkBuilder, CCLinkBuilder, CXXLinkBuilder, \
    StaticLinkBuilder


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
                 builders: Optional[Iterable[Builder]] = None,
                 **kwargs):

        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)
        self.__args: Dict[str, object] = {}

        # setup builders
        self.builders: Dict[str, Builder] = {}
        self.add_builders(*Environment.DEFAULT_BUILDERS)
        if builders is not None:
            self.add_builders(*builders)

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
        for key, value in kwargs.items():
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
    # Misc operations
    #
    def clone(self) -> 'Environment':
        """Returns a deep copy of this environment."""
        new_env = Environment()
        new_env.source_dir = self.source_dir
        new_env.build_dir = self.build_dir
        new_env.__args = deepcopy(self.__args)
        new_env.builders = deepcopy(self.builders)
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
    def add_builders(self, *builders):
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

    def build(self, builder_id, inputs, output=None, deps=None, **kwargs) -> List[Target]:
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

    def for_subdir(self, subdir, buildsubdir=None):
        """Returns a sub-environment that is linked to the same variables and builders.

        :arg subdir The subdirectory
        :arg buildsubdir The subdirectory to be used for build. If this is not set, subdir is used for both source
        and build dirs.
        """
        new_env = Environment()
        new_env.source_dir = self.source(subdir)
        new_env.build_dir = self.dest(buildsubdir or subdir)
        new_env.__args = self.__args
        new_env.builders = self.builders
        return new_env
