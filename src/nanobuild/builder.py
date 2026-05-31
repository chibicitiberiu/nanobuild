from __future__ import annotations

import abc
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Option defaults a builder contributes to an environment: each option is either a scalar
# string (e.g. the compiler name) or a list of string flags.
Vars = Dict[str, Union[str, List[str]]]


class Builder(abc.ABC):
    """
    A builder can generate a command (or list of commands) that take inputs and generate outputs.
    Think of it as a "recipe" in make.
    """
    name: Union[str, List[str]] = 'default'
    multi_input: bool = False
    autogenerate_output: bool = False

    def default_vars(self) -> Vars:
        """
        Gets the default variables that will be injected in the environment.
        :return:
        """
        return {}

    @abc.abstractmethod
    def generate(self) -> Optional[str]:
        """
        Generates the command used to build {IN} into {OUT}.
        Variables can be accessed using {var_name}
        :return:
        """
        pass

    def generate_output_file(self, source: Path) -> Optional[Path]:
        """
        Generates an output file name from an input file name.
        Path doesn't need to be changed, it is handled automatically.

        Usually, this means using `source.with_suffix` to change the extension.
        :param source: Source path
        :return: Output path
        """
        return None


class ASBuilder(Builder):
    name = 'AS'
    multi_input = False
    autogenerate_output = True

    def default_vars(self) -> Vars:
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

    def default_vars(self) -> Vars:
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

    def default_vars(self) -> Vars:
        return {
            'CXX': 'g++',
            'CXXFLAGS': [],
            'CFLAGS': [],
        }

    def generate(self) -> Optional[str]:
        return "{CXX} {CXXFLAGS} {CFLAGS} -c -o {OUT} {IN}"

    def generate_output_file(self, source: Path) -> Optional[Path]:
        return source.with_suffix('.o')


class PhonyBuilder(Builder):
    # 'Depends' is an alias: a phony node is most often used purely to pin build ordering,
    # for which "Depends" reads more naturally than "Phony".
    name = ['Phony', 'Depends']
    multi_input = True
    autogenerate_output = False

    def generate(self) -> Optional[str]:
        return None


class CommandBuilder(Builder):
    """Runs an arbitrary, per-invocation shell command.

    Supply the command via the ``command=`` argument, e.g.
    ``env.Command(inputs, 'disk.img', command='dd if={IN} of={OUT} bs=512')``. Use ``{IN}`` and
    ``{OUT}`` for the inputs and output; bake any other values into the string with ordinary Python.
    Unlike the other builders the command is per-target, so each distinct command becomes its own
    ninja rule.
    """
    name = 'Command'
    multi_input = True
    autogenerate_output = False

    def generate(self) -> Optional[str]:
        # No shared template: the command is provided per target (see Environment.build).
        return None


class CopyBuilder(Builder):
    """Copies a single input file to its output location.

    The command is chosen for the host platform at generation time. Ninja creates the output's
    parent directory automatically, so no explicit ``mkdir`` step is needed.
    """
    name = 'Copy'
    multi_input = False
    autogenerate_output = False

    def generate(self) -> Optional[str]:
        if os.name == 'nt':
            return "copy /Y {IN} {OUT}"
        return "cp {IN} {OUT}"


class StaticLinkBuilder(Builder):
    name = 'StaticLink'
    multi_input = True
    autogenerate_output = False

    def default_vars(self) -> Vars:
        return {
            'AR': 'ar',
        }

    def generate(self) -> Optional[str]:
        return "{AR} -o {OUT} {IN}"


class LDLinkBuilder(Builder):
    name = 'LDLink'
    multi_input = True
    autogenerate_output = False

    def default_vars(self) -> Vars:
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

    def default_vars(self) -> Vars:
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

    def default_vars(self) -> Vars:
        return {
            'CXX': 'g++',
            'LINKFLAGS': [],
            'LIBS': []
        }

    def generate(self) -> Optional[str]:
        return "{CXX} {LINKFLAGS} -o {OUT} {IN} {LIBS}"


__all__ = [
    'Builder', 'Vars',
    'ASBuilder', 'CBuilder', 'CXXBuilder', 'PhonyBuilder', 'CopyBuilder', 'CommandBuilder',
    'StaticLinkBuilder', 'LDLinkBuilder', 'CCLinkBuilder', 'CXXLinkBuilder',
]
