import nb

env = nb.Environment(
    CCFLAGS=['-g']
)

sources = env.source_glob('**/*.cpp')
objects = env.CXX(sources)
binary = env.CXXLink(objects, 'test')

nb.run(binary)
