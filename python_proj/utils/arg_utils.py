"""
Implements utility functions for dealing with command-line arguments.
"""

from sys import argv

from python_proj.utils.util import safe_index


def safe_get_argv(key: str, default: object = None) -> object:
    if (idx := safe_index(argv, key)) >= 0:
        return argv[idx + 1]
    return default


def get_argv(key: str) -> str:
    return argv[argv.index(key) + 1]


def get_argv_flag(key: str) -> bool:
    return argv.index(key) >= 0
