import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv, safe_get_argv


def calculate_prs_per_project(input_names: list[str]) -> dict[str, int]:
    """Calculates prs per project"""
    ds_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        dataset_names=input_names)
    pr_count_per_project = {}
    for entry in ds_iterator:
        project = entry["__source_path"]
        if project not in pr_count_per_project:
            pr_count_per_project[project] = 0
        pr_count_per_project[project] += 1
    return pr_count_per_project


def filter_for_pr_count(prs_per_project: dict[str, int],
                        input_names: list[str],
                        output_path: str,
                        pr_threshold: int):
    """Filters chronological PR dataset to only include projects with sufficient prs."""
    print(f'Outputting to "{output_path}".')
    with open(output_path, "w+", encoding='utf-8') as output_file:
        ds_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
            dataset_names=input_names)
        written = 0
        total = 0
        for entry in ds_iterator:
            total += 1
            project = entry["__source_path"]
            if prs_per_project[project] < pr_threshold:
                continue
            output_file.write(f'{json.dumps(entry)}\n')
            written += 1
    written_perc = 100 * written / total
    print(f'Kept {written}/{total} ({written_perc:03f}%).')


def post_sort_filter_for_pr_count(input_file_names: list[str],
                                  output_file_path: str,
                                  pr_threshold: int):
    prs_per_project = calculate_prs_per_project(input_file_names)
    filter_for_pr_count(prs_per_project, input_file_names,
                        output_file_path, pr_threshold)


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    __input_paths = [entry.strip() for entry in get_argv(
        key="-i").split(",") if entry.strip() != ""]

    __output_path = exp_utils.build_data_path_from_argv(file_name_key='-o')
    print(f'Outputting at "{__output_path}".')

    __pr_threshold = safe_get_argv(key="-p", default=5, data_type=int)
    print(f'PR Threshold set to {__pr_threshold}.')

    post_sort_filter_for_pr_count(__input_paths, __output_path, __pr_threshold)
