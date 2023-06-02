from os import path
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv, get_argv_flag


def count_projects(filter_name: str, file_ext: str, count_entries: bool):
    filter_path = exp_utils.FILTER_PATH(filter_type=filter_name)
    with open(filter_path, "r") as filter_file:
        filter = {entry.strip() for entry in filter_file}

    total = len(filter)
    counted = 0
    entries = 0
    for entry in filter:
        split = entry.split("/")
        owner, repo = split[0], split[1]
        file_path = exp_utils.RAW_DATA_PATH(
            owner=owner, repo=repo, ext=file_ext)
        if not path.exists(file_path):
            continue
        counted += 1
        if not count_entries:
            continue
        with open(file_path, "r") as input_file:
            j_data = json.loads(input_file.read())
            entries += len(j_data)

    if count_entries:
        print(
            f'{counted}/{total} projects found with {entries} data entries for filter {filter_name}.')
    else:
        print(f'{counted}/{total} projects found for filter {filter_name}.')


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    filter_name = exp_utils.get_file_name()
    ext = safe_get_argv(key='-x', default="")
    count_entries = get_argv_flag('-c')
    count_projects(filter_name, ext, count_entries)
