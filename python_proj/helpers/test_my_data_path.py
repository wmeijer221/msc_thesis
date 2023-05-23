"""
Sanity check script to make sure you set the EXPERIMENT_BASE_PATH properly.
"""

from os import path
import python_proj.utils.exp_utils as exp_utils


def test_my_data_path():
    exp_utils.load_paths_for_all_argv()
    test_path = exp_utils.CHRONOLOGICAL_DATASET_PATH
    if not path.exists(test_path):
        raise Exception(f"PATH \"{test_path}\" does not exist.")
    print("All is good.")


if __name__ == "__main__":
    test_my_data_path()
