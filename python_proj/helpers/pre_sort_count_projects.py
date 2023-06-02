from os import path
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv


def count_projects(filter_name: str, file_ext: str):
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
        with open(file_path, "r") as input_file:
            j_data = json.loads(input_file)
            entries += len(j_data)

    print(f'{counted}/{total} projects found with {entries} data entries.')


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    filter_name = exp_utils.get_file_name()
    ext = safe_get_argv(key='-x', default="")
    count_projects(filter_name, ext)
