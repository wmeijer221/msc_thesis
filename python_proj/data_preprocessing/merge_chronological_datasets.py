from datetime import datetime
import json
from numbers import Number

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import OpenMany, ordered_chain
from python_proj.utils.arg_utils import get_argv


def merge_chronological_datasets(file_names: list[str], output_path: str):
    dt_format = "%Y-%m-%dT%H:%M:%SZ"

    def __key(entry: dict) -> Number:
        j_data = json.loads(entry.strip())
        closed_by = j_data["closed_at"]
        dt_closed_by = datetime.strptime(closed_by, dt_format)
        return dt_closed_by.timestamp()

    with open(output_path, "w+") as output_file:
        with OpenMany(file_names, mode="r") as input_files:
            for entry in ordered_chain(input_files, key=__key):
                output_file.write(entry)


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    file_names = exp_utils.get_file_name().split(",")
    base_path = exp_utils.CHRONOLOGICAL_DATASET_PATH
    file_paths = [base_path(file_name=file_name)
                  for file_name in file_names]

    output_name = get_argv(key="-o")
    output_path = base_path(file_name=output_name)

    merge_chronological_datasets(file_paths, output_path)
