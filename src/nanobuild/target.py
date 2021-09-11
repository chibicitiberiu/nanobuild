import abc
from .utility import Utility


class Target(abc.ABC):
    def __init__(self, builder_id, inputs, output, deps, environment):
        self.builder_id = builder_id
        self.output = output
        self.inputs = Utility.flatten_list(inputs)
        self.deps = Utility.flatten_list(deps)
        self.environment = environment
