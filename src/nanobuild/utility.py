import pathlib
from typing import Iterable


class Utility:
    @staticmethod
    def flatten_list(data):
        new_list = []

        if data is None:
            return new_list

        elif (not isinstance(data, Iterable)) or isinstance(data, str):
            new_list.append(data)

        else:
            for item in data:
                if item is None:
                    continue
                elif isinstance(item, Iterable) and not isinstance(item, str):
                    new_list.extend(Utility.flatten_list(item))
                else:
                    new_list.append(item)

        return new_list

    @staticmethod
    def flatten_args_list(args, quote_spaces: bool = True):
        if isinstance(args, str):
            return args

        args = Utility.flatten_list(args)
        s = ''
        for arg in args:
            sarg = str(arg)
            if quote_spaces and ' ' in sarg:
                s += f'"{sarg}" '
            else:
                s += f'{sarg} '

        return s.strip()

    @staticmethod
    def path_to_string(path):
        if path is None:
            return None

        if isinstance(path, pathlib.Path):
            return str(path.resolve())

        return str(path)
