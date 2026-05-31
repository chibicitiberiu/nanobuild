from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set, TextIO, Tuple, Union

import ninja_syntax

from .alias import Alias
from .environment import Environment
from .target import Target
from .utility import Utility


class Nanobuild(object):
    def __init__(self) -> None:
        self.__environments: Dict[int, Environment] = {}
        self.__cwd: Path = Path(".")

    def _preprocess(self, *targets: object) -> None:
        for target in targets:
            if isinstance(target, Target):
                if id(target.environment) not in self.__environments.keys():
                    self.__environments[id(target.environment)] = target.environment
                self._preprocess(*target.inputs)
                self._preprocess(*target.deps)

    def _normpath(self, path: Union[Path, Alias]) -> str:
        if isinstance(path, Alias):
            return str(path)
        else:
            try:
                return str(path.relative_to(self.__cwd))
            except ValueError:
                return str(path)

    def _collect_used_rules(self, *targets: object) -> Set[Tuple[int, str]]:
        """Return the set of ``(environment id, builder_id)`` pairs actually used by the graph.

        Only these become ninja rules, so build.ninja doesn't carry rules for builders that the
        build never invokes. ``Phony`` is excluded because it maps to ninja's built-in rule.
        """
        used: Set[Tuple[int, str]] = set()
        queue: List[object] = list(targets)
        while queue:
            target = queue.pop(0)
            if not isinstance(target, Target):
                continue
            if target.builder_id != 'Phony':
                used.add((id(target.environment), target.builder_id))
            queue.extend(target.inputs)
            queue.extend(target.deps)
        return used

    def generate_ninja(self, *targets: object) -> str:
        """
        Renders the ``build.ninja`` contents for the given targets and returns them as a string.

        This performs no I/O beyond reading the target graph, and does not invoke ninja. It is the
        single source of truth for what gets written to ``build.ninja`` (see :meth:`_generate_build_ninja`),
        which makes the generated output easy to snapshot and assert on in tests.
        """
        flat = Utility.flatten_list(targets)
        self._preprocess(*flat)
        out = io.StringIO()
        self._write_ninja(out, *flat)
        return out.getvalue()

    def _generate_build_ninja(self, *targets: object) -> None:
        with open('build.ninja', 'w') as out:
            out.write(self.generate_ninja(*targets))

    def _write_ninja(self, out: TextIO, *targets: Target) -> None:
        writer = ninja_syntax.Writer(out)

        # Assign each environment a stable index based on the order it is discovered while
        # walking the target graph. Using id(env) here would embed a memory address into the
        # rule names, making build.ninja differ on every run; the index keeps it reproducible.
        env_index: Dict[int, int] = {env_id: i for i, env_id in enumerate(self.__environments.keys())}

        # Emit options as ninja variables (one namespaced block per environment) and reference
        # them from the rules, rather than expanding flag values inline. This keeps build.ninja
        # readable and lets the values be inspected/overridden at the ninja level. Variable names
        # are prefixed with the environment index so distinct environments don't collide. Only the
        # builders actually used by the graph get a rule (and therefore a variable block).
        used = self._collect_used_rules(*targets)
        for env_id, env in self.__environments.items():
            i = env_index[env_id]
            env_used = {builder_id for (eid, builder_id) in used if eid == env_id}
            if not env_used:
                continue
            options = env.prepare()

            writer.comment(f"environment {i}")
            for key, value in options.items():
                writer.variable(f"e{i}_{key}", value)
            writer.newline()

            # {OPTION} placeholders become ninja variable references; {IN}/{OUT} are special.
            substitutions: Dict[str, str] = {key: f"${{e{i}_{key}}}" for key in options}
            substitutions['IN'] = '$in'
            substitutions['OUT'] = '$out'

            for key, builder in env.builders.items():
                if key not in env_used:
                    continue
                command = builder.generate()
                # Builders without a command (e.g. Phony) map to ninja's built-in rules, not a rule of our own.
                if command is None:
                    continue
                writer.rule(f"{key}_{i}", command.format_map(substitutions))
            writer.newline()

        # generate build
        queue: List[Target] = [*targets]
        while len(queue) > 0:
            target = queue.pop(0)
            inputs: List[str] = []
            order_only: List[str] = []

            for input in target.inputs:
                if isinstance(input, Target):
                    if input.output is not None:
                        inputs.append(self._normpath(input.output))
                    queue.append(input)
                elif isinstance(input, Path):
                    inputs.append(self._normpath(input))
                else:
                    inputs.append(str(input))

            for dep in target.deps:
                if isinstance(dep, Target):
                    if dep.output is not None:
                        order_only.append(self._normpath(dep.output))
                    queue.append(dep)
                elif isinstance(dep, Path):
                    order_only.append(self._normpath(dep))
                else:
                    order_only.append(str(dep))

            output = target.output
            output_str: Optional[str] = self._normpath(output) if output is not None else None

            rule_name = f"{target.builder_id}_{env_index[id(target.environment)]}"
            if target.builder_id == 'Phony':
                rule_name = 'phony'

            writer.build(outputs=output_str,
                         rule=rule_name,
                         inputs=inputs,
                         order_only=order_only)

    def run(self, *targets: object, environ: Mapping[str, str] = os.environ) -> None:
        self._generate_build_ninja(*targets)

        # run ninja, pass argv
        try:
            subprocess.run(['ninja', *sys.argv[1:]], env=environ).check_returncode()
        except FileNotFoundError:
            print('Could not find ninja executable! Is ninja installed?', file=sys.stderr)
            sys.exit(1)
