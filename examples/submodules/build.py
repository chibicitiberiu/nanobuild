#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(
    CCFLAGS=['-g']
)

targets = {}
nb.import_file('bird/build.py', targets=targets, env=env)
nb.import_file('not_bird/build.py', targets=targets, env=env)
nb.import_file('main/build.py', targets=targets, env=env)

binary = env.CXXLink(targets.values(), 'test')

nb.run(binary)
