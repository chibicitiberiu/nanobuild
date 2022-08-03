import abc
from pathlib import Path
from typing import Union, List, Optional, Dict, Any


class Builder(abc.ABC):
    """
    A builder can generate a command (or list of commands) that take inputs and generate outputs.
    Think of it as a "recipe" in make.
    """
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
            'CXXFLAGS': [],
            'CFLAGS': [],
        }

    def generate(self) -> Optional[str]:
        return "{CXX} {CXXFLAGS} {CFLAGS} -c -o {OUT} {IN}"

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