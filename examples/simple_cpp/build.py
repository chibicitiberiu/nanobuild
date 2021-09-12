#!/usr/bin/env python3
import nanobuild as nb

env = nb.Environment(
    CCFLAGS=['-g']
)

sources = env.source_glob('**/*.cpp')
headers = [
    env.source_glob('**/*.hpp'),
    env.source_glob('**/*.h'),
]
objects = env.CXX(sources, deps=headers)
binary = env.CXXLink(objects, 'test')

nb.run(binary)
