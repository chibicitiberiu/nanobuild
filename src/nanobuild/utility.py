from __future__ import annotations

import pathlib
from typing import Any, Iterable, List, Optional, Union


class Utility:
    """Small stateless helpers used throughout nanobuild."""

    @staticmethod
    def flatten_list(data: Any) -> List[Any]:
        """Flatten arbitrarily nested iterables into a single list.

        Strings are treated as scalars (never iterated character-by-character), ``None``
        is treated as an empty list, and ``None`` items inside a list are dropped.

        The element type is genuinely heterogeneous (paths, targets, option values, ...),
        so the return type is ``List[Any]``.
        """
        new_list: List[Any] = []

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
    def flatten_args_list(args: Any, quote_spaces: bool = True) -> str:
        """Flatten and join a list of arguments into a single command-line string.

        Each argument is stringified and joined with spaces. When ``quote_spaces`` is true,
        arguments that contain spaces are wrapped in double quotes so they survive as a single
        token. A string passed directly is returned unchanged.
        """
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
    def path_to_string(path: Union[str, pathlib.Path, None]) -> Optional[str]:
        """Convert a path-like value to a string, resolving :class:`~pathlib.Path` to an absolute path.

        Returns ``None`` unchanged; non-Path values are stringified as-is.
        """
        if path is None:
            return None

        if isinstance(path, pathlib.Path):
            return str(path.resolve())

        return str(path)
