#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(
    CCFLAGS=['-g']
)

targets = {}
nb.import_file('bird/build.py', targets=targets, env=env.for_subdir('bird'))
nb.import_file('not_bird/build.py', targets=targets, env=env.for_subdir('not_bird'))
nb.import_file('main/build.py', targets=targets, env=env.for_subdir('main'))

print(targets)
binary = env.CXXLink(targets.values(), 'test')

nb.run(binary)
