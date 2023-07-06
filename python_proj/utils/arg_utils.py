"""
Implements utility functions for dealing with command-line arguments.
"""

from sys import argv

from python_proj.utils.util import safe_index


def safe_get_argv(key: str, default: object = None, data_type: type = str) -> object:
    if (idx := safe_index(argv, key)) >= 0:
        return data_type(argv[idx + 1])
    return default


def get_argv(key: str) -> str:
    try:
        return argv[argv.index(key) + 1]
    except KeyError as ex:
        raise Exception(f'Mandatory commandline argument {key} not set.', ex)

def get_argv_flag(key: str) -> bool:
    return safe_index(argv, key) >= 0
