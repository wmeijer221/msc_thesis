"""
Filters out duplicate entries.
"""

import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv


def filter_unique(input_ds_names: list[str], output_ds_name: str):
    iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        input_ds_names)
    unique = set()
    total = 0
    output_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        file_name=output_ds_name)
    print(f'Output path: "{output_path}".')
    with open(output_path, "w+", encoding='utf-8') as output_file:
        for entry in iterator:
            total += 1
            activity_id = entry['id']
            if activity_id in unique:
                continue
            unique.add(activity_id)
            output_file.write(json.dumps(entry) + "\n")

    unique_count = len(unique)
    print(f'{unique_count=}, {total=}, lost={total-unique_count}.')


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    __input_names = safe_get_argv(key="-pd", default="")
    __input_dataset_names = [entry for entry in __input_names.split(",")
                             if entry != '']

    __output_ds_name = safe_get_argv(key='-o', default="")

    if len(__input_dataset_names) != len(__input_dataset_names):
        raise ValueError()

    filter_unique(__input_dataset_names, __output_ds_name)
