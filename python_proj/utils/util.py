"""
Implements general utility functions.
"""

from typing import Any


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
