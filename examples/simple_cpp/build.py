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
objects_alias = env.Phony(objects, 'my_alias_for_objects')
binary = env.CXXLink(objects_alias, 'test')

nb.run(binary)
