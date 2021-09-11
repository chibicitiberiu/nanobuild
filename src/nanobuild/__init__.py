import os

from .builder import *
from .environment import Environment
from .main import Nanobuild
from .target import Target
from .utility import Utility


def run(*targets, environ=os.environ):
    Nanobuild().run(*targets, environ=environ)
