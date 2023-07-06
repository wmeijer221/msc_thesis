
"""
Implements the sliding window algorithm specifically for the social network analysis bits.
The main difference here is that it's paralellized.
"""

from python_proj.utils.arg_utils import safe_get_argv

if __name__ == "__main__":
    mode = safe_get_argv(key='-m', default='s')
    print(f'Starting in mode: {mode}.')
    match(mode):
        case 's':
            sliding_window()
        case _:
            raise ValueError(f"Invalid mode {mode}.")


