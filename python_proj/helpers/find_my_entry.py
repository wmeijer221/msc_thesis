
import json
from python_proj.utils.arg_utils import get_argv
import python_proj.utils.exp_utils as exp_utils


def find_in(file: str, id: int):
    file_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(file_name=file)

    for entry in exp_utils.iterate_through_chronological_data(data_type="pull-requests", file_name=file):
        if entry['id'] == id:
            print(json.dumps(entry, indent=4))
            break


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()
    id = get_argv('-id')
    file = get_argv('-f')

    find_in(file, id)
