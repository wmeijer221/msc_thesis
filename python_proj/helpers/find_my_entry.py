
import json
from python_proj.utils.arg_utils import get_argv
import python_proj.utils.exp_utils as exp_utils


def load(file: str):
    data = {}
    for entry in exp_utils.iterate_through_chronological_data(data_type="pull-requests", file_name=file):
        data[entry['id']] = entry
    return data


def find_in(file: str, id: int):
    for entry in exp_utils.iterate_through_chronological_data(data_type="pull-requests", file_name=file):
        if entry['id'] == id:
            print(json.dumps(entry, indent=4))
            break


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()
    file = get_argv('-f')

    data = load(file)

    while True:
        try:
            id = input('fill in PR id:')
            id = int(id)
            if id in data:
                print(json.dumps(data[id], indent=4))
            else:
                print('doesnt exist')
        except KeyboardInterrupt:
            raise
        finally:
            continue
