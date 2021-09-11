from typing import Dict

import nanobuild as nb

# make editors happy
env: nb.Environment
targets: Dict

sources = env.source_glob('**/*.cpp')
headers = [
    env.source_glob('**/*.hpp'),
    env.source_glob('**/*.h'),
]

targets['not_bird'] = env.CXX(sources, deps=headers)