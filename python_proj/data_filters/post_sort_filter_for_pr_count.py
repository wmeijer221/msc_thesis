import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv, safe_get_argv


def calculate_prs_per_project(input_name: str) -> dict[str, int]:
    ds_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        dataset_names=input_name)
    pr_count_per_project = {}
    for entry in ds_iterator:
        project = entry["__source_path"]
        if project not in pr_count_per_project:
            pr_count_per_project[project] = 0
        pr_count_per_project[project] += 1
    return pr_count_per_project


def filter_for_pr_count(prs_per_project: dict[str, int],
                        input_name: str,
                        output_path: str,
                        pr_threshold: int):
    with open(output_path, "w+") as output_file:
        ds_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
            data_sources=[input_name],
            dataset_types=[''])
        for entry in ds_iterator:
            project = entry["__source_path"]
            if prs_per_project[project] < pr_threshold:
                continue
            output_file.write(json.dumps(entry))


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    input_paths = [entry.strip() for entry in get_argv(
        key="-i").split(",") if entry.strip() != ""]
    output_path = exp_utils.build_data_path_from_argv(file_name_key='-o')

    pr_threshold = safe_get_argv(key="-p", default=5, data_type=int)
    print(f'PR Threshold set to {pr_threshold}.')

    prs_per_project = calculate_prs_per_project(input_paths)
    filter_for_pr_count(prs_per_project, input_paths,
                        output_path, pr_threshold)
