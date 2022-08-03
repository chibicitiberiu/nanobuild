import os
from pathlib import Path

from nanobuild import Utility


def MkdirCommand(path):
    """
    Provides cross-platform mkdir command.
    :param dir: Directory to create
    :return:
    """
    if os.name == 'nt':
        return Utility.flatten_args_list(['md', Utility.path_to_string(path)])
    else:
        return Utility.flatten_args_list(['mkdir', '-p', Utility.path_to_string(path)])


def CopyCommand(sources, target, recursive=False, create_dirs=True):
    """
    Provides cross-platform copy command.
    :return:
    """
    sources = Utility.flatten_list(sources)
    commands = []

    # create dirs
    if create_dirs:
        if len(sources) > 1:
            commands.append(MkdirCommand(target))
        else:
            if isinstance(target, Path):
                commands.append(MkdirCommand(target.parent))
            else:
                dir_to_create, _ = os.path.split(str(target))
                commands.append(MkdirCommand(dir_to_create))

    if os.name == 'nt':
        for source in sources:
            cmd = ['xcopy']
            if recursive:
                cmd.append('/E')
            cmd.append(Utility.path_to_string(source))
            cmd.append(Utility.path_to_string(target))
            commands.append(Utility.flatten_args_list(cmd))
    else:
        cmd = ['cp']
        if recursive:
            cmd.append('-r')
        for source in sources:
            cmd.append(Utility.path_to_string(source))
        cmd.append(Utility.path_to_string(target))
        commands.append(Utility.flatten_args_list(cmd))

    return commands
