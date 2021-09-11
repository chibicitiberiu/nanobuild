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
            if quote_spaces and ' ' in arg:
                s += f'"{arg}" '
            else:
                s += str(arg) + ' '
        return s.strip()