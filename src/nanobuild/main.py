import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

import ninja_syntax

from .target import Target
from .utility import Utility
from .environment import Environment


class Nanobuild(object):
    def __init__(self):
        self.__environments: Dict[int, Environment] = {}
        self.__cwd = Path(".")

    def _preprocess(self, *targets):
        for target in targets:
            if isinstance(target, Target):
                if id(target.environment) not in self.__environments.keys():
                    self.__environments[id(target.environment)] = target.environment
                self._preprocess(*target.inputs)
                self._preprocess(*target.deps)

    def _normpath(self, path: Path):
        return str(path.relative_to(self.__cwd))

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
                            inputs.append(self._normpath(input.output))
                        queue.append(input)
                    elif isinstance(input, Path):
                        inputs.append(self._normpath(input))
                    else:
                        inputs.append(str(input))

                for dep in target.deps:
                    if isinstance(dep, Target):
                        if dep.output is None:
                            # TODO: process phony targets
                            pass
                        else:
                            order_only.append(self._normpath(dep.output))
                        queue.append(dep)
                    elif isinstance(dep, Path):
                        order_only.append(self._normpath(dep))
                    else:
                        order_only.append(str(dep))

                output = target.output
                if output is not None and isinstance(output, Path):
                    output = self._normpath(output)

                writer.build(outputs=output,
                             rule=f"{target.builder_id}{id(target.environment)}",
                             inputs=inputs,
                             order_only=order_only)

            writer.close()

    def run(self, *targets, environ=os.environ):
        targets = Utility.flatten_list(targets)
        self._preprocess(*targets)
        self._generate_build_ninja(*targets)

        # run ninja, pass argv
        subprocess.run(['ninja', *sys.argv[1:]], env=environ).check_returncode()
