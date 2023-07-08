from python_proj.utils.mt_utils import parallelize_tasks
from sys import argv
import csv
from typing import Any, Callable, Tuple

import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature
from python_proj.utils.arg_utils import safe_get_argv

import python_proj.data_preprocessing.sliding_window_2 as sw2
import python_proj.data_preprocessing.sliding_window_3 as sw3


exp_utils.load_paths_for_eco()

# Sets path for chronological input data
input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                          if entry != '']
input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                             if entry != '']

output_dataset_name = safe_get_argv(
    key="-o", default="test_dataset")
output_dataset_path_sw2 = exp_utils.TRAIN_DATASET_PATH(
    file_name=f'{output_dataset_name}_sw2')
output_dataset_path_sw3 = exp_utils.TRAIN_DATASET_PATH(
    file_name=f'{output_dataset_name}_sw3')

window_size_in_days = safe_get_argv(key="-w", default=None, data_type=int)

thread_count = safe_get_argv(key='-t', default=3, data_type=int)


def run_task(task: Tuple[Callable, dict]):
    task, kwargs = task
    task(**kwargs)


class TestWindowSizeFeature(SlidingWindowFeature):
    def __init__(self) -> None:
        self.count_per_type = {"issues": 0, "pull-requests": 0}

    def add_entry(self, entry: dict):
        t = entry["__data_type"]
        self.count_per_type[t] += 1

    def remove_entry(self, entry: dict):
        t = entry["__data_type"]
        self.count_per_type[t] -= 1

    def get_feature(self, entry: dict) -> Any:
        return self.count_per_type


def my_feature_factory():
    feat = TestWindowSizeFeature()
    pr_sw = [feat]
    is_sw = [feat]
    pr = []
    return pr, pr_sw, is_sw


task_sw2 = (sw2.generate_dataset, {'pr_dataset_names': input_pr_dataset_names,
                                   'issue_dataset_names': input_issue_dataset_names,
                                   'output_dataset_path': output_dataset_path_sw2,
                                   'window_size_in_days': window_size_in_days,
                                   'feature_factory': my_feature_factory})

task_sw3 = (sw3.create_sliding_window_dataset, {'output_path': output_dataset_path_sw3,
                                                'chunk_base_path': exp_utils.BASE_PATH + "/temp/sna_chunks/",
                                                'chunk_output_base_path':  exp_utils.BASE_PATH + "/temp/sna_output/",
                                                'input_issue_dataset_names': input_issue_dataset_names,
                                                'input_pr_dataset_names': input_pr_dataset_names,
                                                'feature_factory': my_feature_factory,
                                                'window_size_in_days': window_size_in_days,
                                                'thread_count': thread_count})

tasks = [task_sw2, task_sw3]
parallelize_tasks(tasks, run_task, 2)


with open(output_dataset_path_sw2, "r", encoding='utf-8') as sw2_file:
    sw2_reader = csv.reader(sw2_file)
    with open(output_dataset_path_sw3, "r", encoding='utf-8') as sw3_file:
        sw3_reader = csv.reader(sw3_file)

        zipped_reader = zip(sw2_reader, sw3_reader)
        header, sw3_header = next(zipped_reader)

        sw2_header_to_sw3_header_idx_mapping = {header: sw3_header.index(header)
                                                for header in header}

        for sw2_entry, sw3_entry in zipped_reader:
            for sw2_idx, header in enumerate(header):
                sw3_idx = sw2_header_to_sw3_header_idx_mapping[sw2_idx]

                sw2_entry = sw2_entry[sw2_idx]
                sw3_entry = sw3_entry[sw3_idx]

                if sw2_entry != sw3_entry:
                    print(f'{header}: {sw2_entry}, {sw3_entry}')
