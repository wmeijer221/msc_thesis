"""
Filters the put in chronological 
data file using a filter file.
"""

import itertools
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv


def filter_input_data_with_project_filter(
        input_data_paths: list[str],
        input_filter_path: str,
        output_data_path: str
):
    """Filters input data using the filter path."""
    with open(input_filter_path, "r", encoding='utf-8') as filter_file:
        projects = {entry.strip().lower() for entry in filter_file}
    with open(output_data_path, "w+", encoding='utf-8') as output_file:
        total = 0
        written = 0

        for entry in exp_utils.iterate_through_multiple_chronological_datasets(input_data_paths):
            total += 1
            owner, repo = exp_utils.get_owner_and_repo_from_source_path(
                entry["__source_path"])
            project = f'{owner}/{repo}'.lower()
            if project in projects:
                written += 1
                output_file.writelines(json.dumps(entry) + "\n")

        written_perc = 100 * written / total
        print(f"Kept {written}/{total} ({written_perc:03f}%).")


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']
    all_dataset_names = list(itertools.chain(
        input_pr_dataset_names, input_issue_dataset_names))
    print(f'Using input data: {all_dataset_names}.')

    filter_file_name = safe_get_argv(key="-f", default="")
    filter_file_path = exp_utils.FILTER_PATH(filter_type=filter_file_name)
    print(f'Using filter "{filter_file_path}".')

    # Sets path for output dataset.
    output_dataset_name = safe_get_argv(
        key="-o", default="test_dataset")
    output_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        data_type="", file_name=output_dataset_name)
    print(f'Output path: "{exp_utils.TRAIN_DATASET_PATH}".')

    exp_utils.load_paths_for_data_path()

    filter_input_data_with_project_filter(
        all_dataset_names, filter_file_path, output_path)
