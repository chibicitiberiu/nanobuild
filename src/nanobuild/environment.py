from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from .alias import Alias
from .builder import (
    ASBuilder,
    Builder,
    CBuilder,
    CCLinkBuilder,
    CommandBuilder,
    CopyBuilder,
    CXXBuilder,
    CXXLinkBuilder,
    LDLinkBuilder,
    PhonyBuilder,
    StaticLinkBuilder,
)
from .target import InputLike, Target
from .utility import Utility

# Accepted forms for a builder's ``output`` argument: an explicit name/path, a callable that maps
# each input to an output (batch mode, single-input builders only), or None (autogenerate/phony).
OutputArg = Union[str, Path, Callable[[Any], Union[str, Path]], None]


class Environment(object):

    DEFAULT_BUILDERS: Tuple[Builder, ...] = (
        ASBuilder(),
        CBuilder(),
        CXXBuilder(),
        LDLinkBuilder(),
        CCLinkBuilder(),
        CXXLinkBuilder(),
        StaticLinkBuilder(),
        PhonyBuilder(),
        CopyBuilder(),
        CommandBuilder()
    )

    def __init__(self,
                 source_dir: Union[str, Path] = '.',
                 build_dir: Union[str, Path] = 'build',
                 args: Optional[Dict[str, Any]] = None,
                 builders: Optional[Iterable[Builder]] = None,
                 **kwargs: Any) -> None:
        """
        Create a new Environment
        :param source_dir: Directory where source files are located. Defaults to current working directory.
        :param build_dir: Directory where build files will be placed. Defaults to 'build' directory, relative to current
        working directory.
        :param args: Dictionary containing options and their values.
        :param builders: List of custom builders to be added to this environment, in addition to all the built-in ones.
        :param kwargs: All other named arguments will be appended to the list of options.
        """
        self.source_dir: Path = Path(source_dir)
        self.build_dir: Path = Path(build_dir)
        self.__args: Dict[str, Any] = {}

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

    def get(self, key: str) -> Any:
        """
        Gets value of an option
        :param key: Name of option
        :return: Value of option
        """
        return self[key]

    def __getitem__(self, key: str) -> Any:
        """
        Gets value of an option
        :param key: Name of option
        :return: Value of option
        """
        try:
            return self.__args[key]
        except KeyError:
            available = ', '.join(sorted(self.__args)) or '(none)'
            raise KeyError(f"No option named {key!r}. Defined options: {available}") from None

    def set(self, key: str, value: Any) -> None:
        """
        Sets value of an option. If option already exists, its value is replaced.
        :param key: Name of option
        :param value: New value of option
        :return: None
        """
        self.__args.__setitem__(key, value)

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Sets value of an option. If option already exists, its value is replaced.
        :param key: Name of option
        :param value: New value of option
        :return: None
        """
        self.__args.__setitem__(key, value)

    def append(self, **kwargs: Any) -> None:
        """
        Appends given values to options.

        If an option does not exist, it is added to the dictionary with the given value.
        If an option already exists, the new value is combined with the existing one using
        the addition operator (+), e.g. lists are concatenated and strings are joined.

        :param kwargs: Options to append, as named arguments.
        :return: None
        """
        for key, value in kwargs.items():
            if key in self.__args.keys():
                self.__args[key] += value
            else:
                self.__args[key] = value

    def replace(self, **kwargs: Any) -> None:
        self.__args.update(kwargs)

    def pop(self, key: str) -> Any:
        return self.__args.pop(key)

    def __delitem__(self, key: str) -> None:
        self.__args.__delitem__(key)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        return iter(self.__args.items())

    #
    # Misc operations
    #
    def clone(self,
              source_dir: Optional[Union[str, Path]] = None,
              build_dir: Optional[Union[str, Path]] = None,
              args: Optional[Dict[str, Any]] = None,
              builders: Optional[Iterable[Builder]] = None,
              **kwargs: Any) -> 'Environment':
        """Returns a deep copy of this environment."""
        new_env = Environment()
        new_env.source_dir = Path(source_dir) if source_dir is not None else self.source_dir
        new_env.build_dir = Path(build_dir) if build_dir is not None else self.build_dir

        new_env.__args = deepcopy(self.__args)
        if args is not None:
            new_env.replace(**args)
        if kwargs is not None:
            new_env.replace(**kwargs)

        new_env.builders = deepcopy(self.builders)
        if builders is not None:
            new_env.add_builders(*builders)

        return new_env

    def __repr__(self) -> str:
        return self.__args.__repr__()

    #
    # Files
    #
    def source(self, path: Union[str, Path]) -> Path:
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

    def source_glob(self, pattern: str) -> List[Path]:
        """
        Returns a sorted list of paths in the source directory matching the given glob pattern.

        Results are sorted so that the generated build is reproducible regardless of the order
        in which the underlying filesystem happens to enumerate directory entries.
        """
        return sorted(self.source_dir.glob(pattern))

    def dest(self, path: Union[str, Path]) -> Path:
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
    def add_builders(self, *builders: Builder) -> None:
        for builder in builders:
            for name in Utility.flatten_list(builder.name):
                self.builders[name] = builder

    def preprocess_inputs(self, inputs: Optional[InputLike]) -> List[Union[Path, Target]]:
        new_inputs: List[Union[Path, Target]] = []
        for input in Utility.flatten_list(inputs):
            if isinstance(input, str):
                new_inputs.append(self.source(input))
            else:
                new_inputs.append(input)
        return new_inputs

    def _resolve_output(self, output: Union[str, Path]) -> Path:
        """Resolve an output name to a Path: strings are placed under the build directory."""
        if isinstance(output, str):
            return self.dest(output)
        return output

    def build(self,
              builder_id: str,
              inputs: InputLike,
              output: OutputArg = None,
              deps: Optional[InputLike] = None,
              **kwargs: Any) -> List[Target]:
        if builder_id not in self.builders:
            available = ', '.join(sorted(self.builders))
            raise ValueError(f"Unknown builder {builder_id!r}. Available builders: {available}")
        builder = self.builders[builder_id]

        # The per-invocation command for Command targets travels as a kwarg so the public call
        # signature stays uniform; pull it out before the rest of kwargs become option overrides.
        command = kwargs.pop('command', None)
        if isinstance(builder, CommandBuilder) and command is None:
            raise ValueError("The Command builder requires a 'command=...' argument.")

        prepared_inputs = self.preprocess_inputs(inputs)
        prepared_deps = self.preprocess_inputs(deps)
        targets: List[Target] = []

        # Build env
        env = self
        if kwargs is not None and len(kwargs) > 0:
            env = self.clone(**kwargs)

        # Handle phony targets
        if isinstance(builder, PhonyBuilder):
            if output is None or callable(output):
                raise ValueError(f"{builder_id} target requires an alias name as its output.")
            targets.append(Target(builder_id, prepared_inputs, Alias(str(output)), prepared_deps, env))

        elif callable(output):
            # Batch mode: map a single-input builder over each input, deriving the output per item.
            if builder.multi_input:
                raise ValueError(
                    f"Builder {builder_id!r} consumes all its inputs into a single output; "
                    f"a per-input output function only works with single-input builders.")
            for input_item in prepared_inputs:
                source = input_item.output if isinstance(input_item, Target) else input_item
                resolved = self._resolve_output(output(source))
                targets.append(Target(builder_id, input_item, resolved, prepared_deps, env, command=command))
            return targets

        elif output is None:
            # No output given: only builders that can derive one from each input are allowed.
            if builder.multi_input or not builder.autogenerate_output:
                raise ValueError(
                    f"Builder {builder_id!r} requires an explicit output file name "
                    f"(it cannot generate one automatically).")

            # builder can autogenerate outputs, so we can emit multiple targets
            for input_item in prepared_inputs:
                # obtain output file from input
                input_file: Union[Path, Target, None] = input_item
                if isinstance(input_item, Target):
                    input_file = input_item.output if isinstance(input_item.output, Path) else None

                if isinstance(input_file, Path) and input_file.is_relative_to(self.source_dir):
                    input_file = self.dest(input_file.relative_to(self.source_dir))

                output_item = builder.generate_output_file(input_file) if isinstance(input_file, Path) else None
                targets.append(Target(builder_id, input_item, output_item, prepared_deps, env))
            return targets

        else:
            targets.append(Target(builder_id, prepared_inputs, self._resolve_output(output),
                                  prepared_deps, env, command=command))

        return targets

    def __getattr__(self, item: str) -> Callable[..., List[Target]]:
        # Internal/dunder probes (copy, pickle, ...) must raise AttributeError without touching
        # self.builders, which is itself looked up here and would otherwise recurse before __init__.
        if item.startswith('_'):
            raise AttributeError(item)
        builders = self.__dict__.get('builders', {})
        if item in builders:
            return lambda inputs, output=None, **kwargs: self.build(item, inputs, output, **kwargs)
        available = ', '.join(sorted(builders)) or '(none)'
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute or builder {item!r}. "
            f"Available builders: {available}")

    def prepare(self) -> Dict[str, str]:
        final: Dict[str, str] = {}
        for key, value in self.__args.items():
            final[key] = Utility.flatten_args_list(value)
        return final

    def for_subdir(self,
                   subdir: Union[str, Path],
                   build_subdir: Optional[Union[str, Path]] = None,
                   deep_clone: bool = False) -> 'Environment':
        """Returns a sub-environment that is linked to the same variables and builders.

        :arg subdir The subdirectory
        :arg build_subdir The subdirectory to be used for build. If this is not set, subdir is used for both source
        and build dirs.
        :arg deep_clone If true, a deep clone is created instead of a shallow clone.
        """
        source_dir = self.source(subdir)
        build_dir = self.dest(build_subdir or subdir)

        if deep_clone:
            # clone() already produces independent (deep-copied) options and builders;
            # leave them isolated from the parent.
            new_env = self.clone(source_dir=source_dir,
                                 build_dir=build_dir)
        else:
            # Shallow: share the parent's option store and builders by reference, so changes
            # made through either environment are visible in both.
            new_env = Environment(source_dir=source_dir,
                                  build_dir=build_dir)
            new_env.__args = self.__args
            new_env.builders = self.builders
        return new_env
