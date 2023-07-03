import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv


def count_unique(input_ds_names: str):
    iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        input_ds_names)
    unique = set()
    total = 0
    for entry in iterator:
        id = entry['id']
        unique.add(id)
        total += 1

    unique_count = len(unique)

    print(f'{unique_count=}, {total=}.')


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()
    __input_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                             if entry != '']
    count_unique(__input_dataset_names)
