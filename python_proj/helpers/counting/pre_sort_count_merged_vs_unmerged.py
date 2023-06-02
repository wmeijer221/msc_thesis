
from os import path
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv, get_argv_flag


def count_merged_vs_unmerged(filter_name: str, file_ext: str):
    filter_path = exp_utils.FILTER_PATH(filter_type=filter_name)
    with open(filter_path, "r") as filter_file:
        filter = {entry.strip() for entry in filter_file}

    total = 0
    merged = 0
    unmerged = 0
    has_closed_by = 0
    has_merged_by_data = 0

    for entry in filter:
        split = entry.split("/")
        owner, repo = split[0], split[1]
        file_path = exp_utils.RAW_DATA_PATH(
            owner=owner, repo=repo, ext=file_ext)
        if not path.exists(file_path):
            continue

        with open(file_path, "r") as input_file:
            j_data = json.loads(input_file.read())
            total += 1
            for entry in j_data:
                is_merged = entry['merged']
                integrator_key = exp_utils.get_integrator_key(entry)
                if is_merged:
                    merged += 1
                    if integrator_key in entry:
                        has_merged_by_data += 1
                else:
                    unmerged += 1
                    if integrator_key in entry:
                        has_closed_by += 1

    print(f'Found {total} PRs.')
    print(
        f'Found {merged} merged PRs, of which {has_merged_by_data} have merged_by_data.')
    print(
        f'Found {unmerged} unmerged PRs, of which {has_closed_by} have closed_by.')


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    filter_name = exp_utils.get_file_name()
    ext = safe_get_argv(key='-x', default="")
    count_entries = get_argv_flag('-c')
    count_merged_vs_unmerged(filter_name, ext, count_entries)
