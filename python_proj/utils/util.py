"""
Implements general utility functions.
"""

from typing import Any, Tuple, TypeVar, Generator, Callable
from numbers import Number
import io
import numpy
import math


def safe_add_list_element(dictionary: dict[Any, list], key, value):
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]


def safe_add_set_element(dictionary: dict[Any, set], key, value):
    if key in dictionary:
        dictionary[key].add(value)
    else:
        dictionary[key] = set()
        dictionary[key].add(value)


def get_nested(obj: dict, key: list[str]) -> Any | None:
    """
    Returns value corresponding to the key by recursively
    searching in the given dictionary.

    :params obj: The used dictionary.
    :params key: The query key.
    """

    current = obj
    for key in key:
        if not key in current:
            return None
        current = current[key]
    return current


def safe_index(list: list, entry: object) -> int:
    try:
        return list.index(entry)
    except ValueError:
        return -1


def safe_contains_key(text: str, key: str) -> bool:
    """
    Returns true if the ``text`` contains the ``key``.
    """

    try:
        text.index(key)
        return True
    except:
        return False


def safe_get(source: dict, key: Any, default: Any | None = None) -> Any:
    if key in source:
        return source[key]
    return default


class OpenMany:
    def __init__(self, file_paths: list[str], *args, **kwargs) -> None:
        self.file_paths: list[str] = file_paths
        self.files: list[io.IOBase] = [None] * len(file_paths)
        self.__args = args
        self.__kwargs = kwargs

    def __enter__(self) -> list[io.IOBase]:
        for index, file_path in enumerate(self.file_paths):
            self.files[index] = open(file_path, *self.__args, **self.__kwargs)
        return self.files

    def __exit__(self, type, value, traceback) -> None:
        for file in self.files:
            file.close()


T = TypeVar("T")


def ordered_chain(iterables: list[Generator[T, None, None]],
                  key: Callable[[T, T], Number]) \
        -> Generator[Tuple[int, T], None, None]:
    """
    Iterates through multiple generators in a chained fashion,
    iterating through them in an ordered fashion. Assumes the
    individual generators are sorted already.

    :param list[Generator[T]] iterables: The lists that are being chained.
    :param Callable[[T], Number] key: Method that is used for ordering
    iterable elements.
    """



    current_elements = [next(iterables[idx]) for idx in range(len(iterables))]
    stop_iterations = 0

    def __key_wrapper(entry):
        return math.inf if entry is None else key(entry)

    while stop_iterations != len(iterables):
        current_idx = numpy.argmin([__key_wrapper(ele)
                                   for ele in current_elements])
        yield current_idx, current_elements[current_idx]
        try:
            current_elements[current_idx] = next(iterables[current_idx])
        except StopIteration:
            stop_iterations += 1
            current_elements[current_idx] = None
