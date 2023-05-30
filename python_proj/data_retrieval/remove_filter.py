"""
Allows you to remove all entries in one filter file from another one, 
making sure there is no overlap.

commandline arguments:
``-a``: the list that entries are removed from.
``-b``: the list whose entries are removed.
``-o``: the name of the output filter.

For each of these, you only need to provide a filter name;
not a full path.
"""

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv


def remove_filter(filter_path_a: str, filter_path_b: str, output_path: str):
    filter_a = open(filter_path_a, "r")
    filter_b = open(filter_path_b, "r")

    set_a = {entry.strip() for entry in filter_a}
    set_b = {entry.strip() for entry in filter_b}

    result = set_a.difference(set_b)

    with open(output_path, "w+") as output_file:
        for entry in result:
            output_file.write(f'{entry}\n')

    filter_a.close()
    filter_b.close()


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    filter_path = exp_utils.FILTER_PATH
    filter_a = filter_path(filter_type=get_argv("-a"))
    filter_b = filter_path(filter_type=get_argv("-b"))
    filter_out = filter_path(filter_type=get_argv("-o"))
    remove_filter(filter_a, filter_b, filter_out)
