
import python_proj.utils.exp_utils as exp_utils


def count_my_chronological_dataset_entries() -> int:
    count = 0
    for _ in exp_utils.iterate_through_chronological_data():
        count += 1
    print(f'{count=}')
    return count


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    count_my_chronological_dataset_entries()
