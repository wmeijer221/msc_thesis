"""
As there are multiple "post_sort_*" scripts now, it's becomming 
a hassle to deal with all of them. This script combines them, 
hoping it doesn't turn into a x + 1 problem.
"""

from importlib import reload
from functools import partial

from python_proj.utils.arg_utils import get_argv, safe_get_argv
from python_proj.utils.mt_utils import parallelize_tasks
import python_proj.utils.exp_utils as exp_utils

from python_proj.data_filters.post_sort_filters import apply_post_sort_filter
from python_proj.data_filters.post_sort_filter_for_pr_count import post_sort_filter_for_pr_count
from python_proj.data_filters.post_sort_filter_for_projects import filter_input_data_with_project_filter
from python_proj.data_preprocessing.sliding_window_2 import remove_invalid_entries, build_dataset
from python_proj.helpers.create_project_user_list import create_project_user_list
from python_proj.data_filters.post_sort_filter_unique import filter_unique


def __stage_simple_filter(
        filter_mode: str,
        output_path_flag: str,
        input_chronological_pr_datasets: list[str],
        input_chronological_issue_datasets: list[str]
):
    # Applies the basic filter on all input chronological datasets.
    print(f"Stage 1: Starting simple filter in mode '{filter_mode}'.")

    def __do_basic_filter(task, *_, **__):
        data_type, input_file_name = task[0], task[1]
        input_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
            data_type=data_type, file_name=input_file_name)
        output_file_name = f'{input_file_name}_out_{output_path_flag}'
        output_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
            data_type=data_type, file_name=output_file_name
        )
        apply_post_sort_filter(input_path, output_path, filter_mode)
    tasks = list([('pull-requests', file_name)
                 for file_name in input_chronological_pr_datasets])
    tasks.extend([('issues', file_name)
                 for file_name in input_chronological_issue_datasets])
    parallelize_tasks(tasks, __do_basic_filter, thread_count=len(tasks))


def __stage_pr_count_filter(
    min_pr_count: int,
    output_path_flag: str,
    input_chronological_pr_datasets: list[str],
    output_name_final_datasets: str
):
    # Applies PR count filter
    print(f'Stage 2: Starting PR count filter with threshold {min_pr_count}.')
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()  # sets it to the default: pull-requests
    input_file_names = [f'{input_file_name}_out_{output_path_flag}'
                        for input_file_name in input_chronological_pr_datasets]
    output_pr_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        file_name=output_name_final_datasets)
    post_sort_filter_for_pr_count(
        input_file_names, output_pr_path, min_pr_count)
    print(f'{output_pr_path=}')


def __stage_create_project_list(
        output_name_final_datasets: str,
        output_path_flag: str
) -> str:
    # Sieves project names from the created pull request file.
    print("Stage 3: Creating project list.")
    reload(exp_utils)
    exp_utils.load_paths_for_eco()
    projects_path = create_project_user_list(
        input_pr_dataset_names=[output_name_final_datasets],
        input_issue_dataset_names=[],
        ext=output_path_flag
    )
    print(f'{projects_path=}')
    return projects_path


def __stage_filter_issues_with_projects(
    output_path_flag: str,
    input_chronological_issue_datasets: list[str],
    output_name_final_datasets: str,
    projects_path: str
):
    # filters issue dataset with project list.
    print('Stage 4: Filtering issues with filter list.')
    exp_utils.load_paths_for_data_path(data_source='issues')
    issue_dataset_names = [f'{dataset_in}_out_{output_path_flag}'
                           for dataset_in in input_chronological_issue_datasets]
    output_issue_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        data_type='issues',
        file_name=output_name_final_datasets
    )
    print(f'{output_issue_path=}')
    filter_input_data_with_project_filter(
        issue_dataset_names,
        projects_path,
        output_issue_path
    )


def __stage_remove_invalid_entries_final_datasets(output_name_final_datasets: str):
    # Invalid entry filtering
    print("Stage 5: Removing invalid entries from issues and PRs.")
    reload(exp_utils)
    exp_utils.load_paths_for_eco()
    remove_invalid_entries(
        [output_name_final_datasets],
        [output_name_final_datasets]
    )


def __stage_remove_duplicates(input_name_final_datasets: str,
                              output_name_final_datasets: str):
    print("Stage 6: removing duplicates from PR and issue sets.")
    reload(exp_utils)
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()
    filter_unique([input_name_final_datasets], output_name_final_datasets)
    reload(exp_utils)
    exp_utils.load_paths_for_eco()
    # HACK: loading data path after this will definitely break it.
    # HACK: The only reason this is reloaded is to deal with issues vs. PRs. This is way too implicit.
    exp_utils.CHRONOLOGICAL_DATASET_PATH = partial(
        exp_utils.CHRONOLOGICAL_DATASET_PATH, data_type='issues')
    filter_unique([input_name_final_datasets], output_name_final_datasets)
    reload(exp_utils)


def __stage_create_sliding_window_dataset(
    windows: list[int | None],
    output_path_flag: str,
    output_name_final_datasets: str
):
    # Create sliding window dataset.
    print(
        f"Stage 6: Creating sliding window datasets with windows: {windows}.")

    exp_utils.load_paths_for_eco()

    def __create_training_dataset(task, *_, **__):
        window = task
        output_train_dataset_path = exp_utils.TRAIN_DATASET_PATH(
            file_name=f'dataset_{window}_days_{output_path_flag}')
        print(f'{output_train_dataset_path=}')
        build_dataset(
            pr_dataset_names=[f'{output_name_final_datasets}_no_invalid'],
            issue_dataset_names=[f'{output_name_final_datasets}_no_invalid'],
            output_dataset_path=output_train_dataset_path,
            window_size_in_days=window
        )
    parallelize_tasks(
        tasks=windows,
        on_message_received=__create_training_dataset,
        thread_count=len(windows)
    )


def apply_post_sort_all(
    input_chronological_pr_datasets: list[str],
    input_chronological_issue_datasets: list[str],
    output_path_flag: str,
    min_pr_count: int,
    filter_mode: str,
    windows: list[str | None]
):
    """Applies all post-sort filters to the input datasets."""

    __stage_simple_filter(
        filter_mode,
        output_path_flag,
        input_chronological_pr_datasets,
        input_chronological_issue_datasets
    )

    output_name_final_datasets = f'sorted_{output_path_flag}_min_{min_pr_count}_prs'

    __stage_pr_count_filter(
        min_pr_count,
        output_path_flag,
        input_chronological_pr_datasets,
        output_name_final_datasets
    )

    projects_path = __stage_create_project_list(
        output_name_final_datasets,
        output_path_flag
    )

    __stage_filter_issues_with_projects(
        output_path_flag,
        input_chronological_issue_datasets,
        output_name_final_datasets,
        projects_path
    )

    __stage_remove_invalid_entries_final_datasets(output_name_final_datasets)

    output_name_final_datasets_no_dupes = f'{output_name_final_datasets}_no_dupes'
    __stage_remove_duplicates(output_name_final_datasets, 
                              output_name_final_datasets_no_dupes)

    # __stage_create_sliding_window_dataset(
    #     windows,
    #     output_path_flag,
    #     output_name_final_datasets_no_dupes
    # )

    print("Done!")


if __name__ == "__main__":
    __input_chronological_pr_datasets = list([entry for entry in get_argv(
        key='--chron_in_pr').split(",") if entry != ""])
    __input_chronological_issue_datasets = list([entry for entry in get_argv(
        key='--chron_in_issue').split(",") if entry != ""])
    __dataset_tag = get_argv(key='--tag')
    __windows = [None if entry == 'all' else int(entry)
                 for entry in get_argv(key='--windows').split(",")]
    __min_prs = safe_get_argv(key='--min_prs', default=5, data_type=int)
    __filter_mode = safe_get_argv(key='--filter_mode', default="pcuadgbn")
    apply_post_sort_all(
        __input_chronological_pr_datasets,
        __input_chronological_issue_datasets,
        __dataset_tag,
        __min_prs,
        __filter_mode,
        __windows
    )
