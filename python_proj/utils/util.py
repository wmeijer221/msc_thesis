"""
Implements general utility functions.
"""

import regex as re
from typing import Any, Tuple, TypeVar, Callable, Iterator, Sequence, Generic
from numbers import Number
import io
import numpy
import math
import os
import matplotlib.pyplot as plt


def has_keys(d: dict, keys: list) -> bool:
    return all((key in d for key in keys))


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
    for key_element in key:
        if not key_element in current:
            return None
        current = current[key_element]
    return current


def get_nested_many(obj: dict, key: list[str]) -> list[Any] | Any | None:
    """Same idea as ``get_nested``, however, when a variable is a list it iterates through all of them."""
    print("Depricated: ``get_nested_many`` should be replaced with ``better_get_nested_many``.")
    current = obj
    for key_index, key_element in enumerate(key):
        if isinstance(current, list):
            return [get_nested_many(element, key[key_index:])
                    for element in current]
        if not key_element in current:
            return None
        current = current[key_element]
    return current


def better_get_nested_many(obj: dict, key: list[str], raise_on_missing_key: bool = True) -> list[Any]:
    """
    Same thing as ``get_nested_many`` but always returns a list.
    """

    current = obj
    for key_index, key_element in enumerate(key):
        if isinstance(current, list):
            all_inner = [better_get_nested_many(element, key[key_index:], raise_on_missing_key)
                         for element in current]
            combined = []
            for inner in all_inner:
                combined.extend(inner)
            return combined
        elif not key_element in current:
            if raise_on_missing_key:
                raise KeyError(
                    f"Missing key {key_element} in object {current}.")
            return []
        else:
            current = current[key_element]
    if isinstance(current, list):
        return current
    else:
        return [current]


def resolve_callables_in_list(coll: Iterator[Any | Callable], *args, **kwargs) -> Iterator[Any]:
    for entry in coll:
        if isinstance(entry, Callable):
            entry = entry(*args, **kwargs)
        yield entry


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


def ordered_chain(iterables: list[Iterator[T]],
                  key: Callable[[T, T], Number]) \
        -> Iterator[Tuple[int, T]]:
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


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class SafeDict(dict, Generic[_KT, _VT]):
    """
    Standard dictionary data structure that adds a default value to a key if it doesn't exist yet.
    """

    def __init__(self, default_value, default_value_constructor_args: list[Any] | None = None,
                 default_value_constructor_kwargs: dict[str,
                                                        Any] | None = None,
                 initial_mapping: dict[_KT, _VT] | None = None,
                 delete_when_default: bool = False,
                 *args, **kwargs):
        """
        :param default_value: the default value for entries. 
        If this is a ``type``, it will call said type's constructor, and if it's callable, it will call it.
        :param default_value_constructor_args: The constructor arguments for the default value.
        Only relevant if its constructor is called or the default value is callable.
        :param default_value_constructor_kwargs: Named constructor arguments for the default value.
        Only relevant if its constructor is called.
        :param map: Can be set to come with a pre-filled mapping. 
        :param *args, **kwargs: Constructor arguments for the inner datastructure of the dictionary.
        These can be anything that can be passed to the constructor of a ``dict``.
        :param delete_when_default: Deletes entries whenever they are equal to the default value to preserve memory.
        Only use this when you don't intend to use the len() as this might be misleading. This is only set when the
        default value is not a ``callable`` or a ``type``.
        """

        if not initial_mapping is None:
            super().__init__(initial_mapping)

        self.__default_value: Any = default_value
        self.__default_value_constructor_args: list = [] if default_value_constructor_args is None \
            else default_value_constructor_args
        self.__default_value_constructor_kwargs: dict = {} if default_value_constructor_kwargs is None \
            else default_value_constructor_kwargs
        self.__delete_when_default: bool = False

        if isinstance(default_value, type):
            self.__get_default_value = lambda: self.__default_value(
                *self.__default_value_constructor_args,
                **self.__default_value_constructor_kwargs)
        elif isinstance(default_value, Callable):
            self.__get_default_value = lambda: self.__default_value(*self.__default_value_constructor_args,
                                                                    **self.__default_value_constructor_kwargs)
        else:
            self.__get_default_value = lambda: self.__default_value
            self.__delete_when_default: bool = delete_when_default

        super().__init__(*args, **kwargs)

    def __getitem__(self, __key: _KT) -> None:
        if not __key in self:
            value = self.__get_default_value()
            super().__setitem__(__key, value)
        return super().__getitem__(__key)

    def __setitem__(self, __key: _KT, __value: _VT) -> None:
        if self.__delete_when_default and __value == self.__default_value:
            super().__delitem__(__key)
        else:
            super().__setitem__(__key, __value)


def safe_save_fig(output_path):
    """Helper method to safe figures in a potentially non-existent directory."""
    dir_name = os.path.dirname(output_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    plt.savefig(output_path)


def subtract_dict(original: dict[Any, Number], subtracted: dict[Any, Number]) -> dict[Any, Number]:
    ""'Subtracts the values of one dict from another.'""
    key_intersect = set(original.keys()).intersection(subtracted.keys())
    if len(key_intersect) != len(original) or len(key_intersect) != len(subtracted):
        raise ValueError("Elements don't have the same keys.")
    return {key: original[key] - subtracted[key] for key in key_intersect}


class Counter:
    """Simple tool for picking the next number in line."""

    def __init__(self, start_value: int = 42, increment: int = 1) -> None:
        self.__current_value = start_value
        self.__increment = increment

    def get_next(self):
        self.__current_value += self.__increment
        return self.__current_value


def tuple_chain(
    iterator: Iterator[T],
    yield_first: bool = False,
    yield_last: bool = False
) -> Iterator[Tuple[T | None, T | None]]:
    """Returns tuples of entries. Given [a, b, c, d], it outputs [(a,b), (b,c), (c,d)]"""
    if not isinstance(iterator, Iterator):
        iterator = iter(iterator)

    previous = None
    current = next(iterator)

    if yield_first:
        yield previous, current

    for entry in iterator:
        previous = current
        current = entry
        yield previous, current

    if yield_last:
        yield current, None


def chain_with_intermediary_callback(
    generator: Iterator[T],
    callback: Callable[[T], None]
) -> Iterator[T]:
    """Calls the specified function before yielding the entry like normal."""
    for entry in generator:
        callback(entry)
        yield entry


def safe_makedirs(dirname: str):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def stepped_enumerate(
    collection: Iterator[T],
    start: Number = 0,
    step: Number = 1
) -> Iterator[Tuple[Number, T]]:
    current = start
    for entry in collection:
        yield (current, entry)
        current += step


def flatten(iterator: Iterator[Iterator | Any]) -> Iterator[Any]:
    """
    Flattens Iterator with nested Iterators.
    """

    for element in iterator:
        if isinstance(element, Iterator | Sequence) \
                and not isinstance(element, str):
            for inner_element in flatten(element):
                yield inner_element
        else:
            yield element


def lies_between(x, start, end) -> bool:
    return x >= start and x <= end


def get_matching(collection: Iterator[str], expr: str) -> Iterator[str]:
    """Returns all entries that match the expression"""
    for entry in collection:
        if re.match(expr, entry):
            yield entry


def invert_dict(d: dict) -> dict:
    return {value: key for key, value in d.items()}
