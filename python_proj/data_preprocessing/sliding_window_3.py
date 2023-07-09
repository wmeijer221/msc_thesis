"""
Version 3 of the sliding window algorithm. This time it's multithreaded
as that's way faster and I don't want to wait three days for my results.

Implements a sliding window algorithm used to generate training datasets
consisting of various intra and ecosystem-wide PR merge predictors. See
the method at the bottom of this script for the relevant command line
parameters.
"""

from collections import deque
import csv
from datetime import datetime, timedelta
import json
import os
from typing import Tuple, Iterator, Callable

import python_proj.data_preprocessing.sliding_window_features as swf
from python_proj.utils.arg_utils import safe_get_argv, get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import SlidingWindowFeature, Feature
from python_proj.utils.mt_utils import parallelize_tasks
from python_proj.utils.util import Counter, tuple_chain,\
    chain_with_intermediary_callback, safe_makedirs


def __create_data_chunk_stream(
    issue_file_names: list[str],
    pr_file_names: list[str],
    window_size: timedelta,
    base_path: str,
) -> Iterator[str]:
    chunk_counter = Counter(start_value=0)

    def __make_next_chunk_file():
        chunk_file_path = base_path + str(chunk_counter.get_next())
        return open(chunk_file_path, "w+", encoding='utf-8')

    current_chunk_file = __make_next_chunk_file()

    data_iterator = exp_utils.iterate_through_multiple_chronological_issue_pr_datasets(
        issue_file_names, pr_file_names)

    chunk_start_timestamp: datetime = None
    dt_format = "%Y-%m-%dT%H:%M:%SZ"

    for entry in data_iterator:
        timestamp = datetime.strptime(entry['closed_at'], dt_format)

        if chunk_start_timestamp is None:
            chunk_start_timestamp = timestamp

        chunk_delta = timestamp - chunk_start_timestamp
        if chunk_delta > window_size:
            chunk_start_timestamp = timestamp
            current_chunk_file.close()
            current_chunk_name = current_chunk_file.name
            print(f'Finished creating chunk "{current_chunk_name}".')
            yield current_chunk_name
            current_chunk_file = __make_next_chunk_file()

        line = f'{json.dumps(entry)}\n'
        current_chunk_file.write(line)

    print(f'Finished creating last chunk "{current_chunk_name}".')
    current_chunk_name = current_chunk_file.name

    current_chunk_file.close()

    yield current_chunk_name


def __create_window_from_file(
    input_file_path: str | None,
    issue_sw_features: list[SlidingWindowFeature],
    pr_sw_features: list[SlidingWindowFeature]
) -> Tuple[dict[datetime, list[dict]], deque[datetime]]:
    """
    Fills the sliding window features with all entries in the input file.
    Assumes that the input file spans the size of the analysis time window.
    """

    # Creates window
    window: dict[datetime, list[dict]] = {}
    window_keys = deque()

    if input_file_path is None:
        return window, window_keys

    # Adds the entire previous chunk, and constructs the initial window.
    with open(input_file_path, "r", encoding='utf-8') as input_file:
        for line in input_file:
            new_entry = json.loads(line)
            __add_entry(
                new_entry,
                window_keys,
                window,
                pr_sw_features,
                issue_sw_features
            )

    return window, window_keys


def __prune_entries(
        new_entry: datetime,
        time_window: timedelta,
        window_keys: deque,
        window: dict[datetime, list[dict]],
        issue_sw_features: list[SlidingWindowFeature],
        pr_sw_features: list[SlidingWindowFeature]
):
    """
    Prunes entries from the time window. Updates the bookkeeping files
    as well as the sliding window features.
    """

    # Parses the entry's timestamp.
    new_entry_date = datetime.strptime(
        new_entry['closed_at'], exp_utils.DATETIME_FORMAT)

    # Collects to-be-pruned entries.
    pruned_entries = []
    new_window_start = new_entry_date - time_window
    broke_loop = False
    while len(window_keys) > 0:
        potential_pruned_key = window_keys.popleft()
        if potential_pruned_key > new_window_start:
            broke_loop = True
            break

        # when the key is added to the linked list twice,
        # it'll already be deleted.
        if potential_pruned_key not in window:
            continue

        # Adds the entry to the list of pruned entries.
        new_pruned_entries = window[potential_pruned_key]
        pruned_entries.extend(new_pruned_entries)
        del window[potential_pruned_key]

    # If the loop was broken, it means we popped one too
    # many, so the last one is added again.
    if broke_loop:
        window_keys.appendleft(potential_pruned_key)

    # Prunes entries.
    for pruned_entry in pruned_entries:
        is_issue = pruned_entry['__data_type'] == 'issues'
        sw_features = issue_sw_features if is_issue else pr_sw_features
        for feature in sw_features:
            feature.remove_entry(pruned_entry)


def __add_entry(
    new_entry: dict,
    window_keys: deque,
    window: dict[datetime, list[dict]],
    pr_sw_features: list[SlidingWindowFeature],
    issue_sw_features: list[SlidingWindowFeature]
):

    # Adds new entry.
    is_pr = new_entry["__data_type"] == "pull-requests"
    sw_features = pr_sw_features if is_pr else issue_sw_features
    for feature in sw_features:
        feature.add_entry(new_entry)

    # Parses the entry's timestamp.
    new_entry_date = datetime.strptime(
        new_entry['closed_at'], exp_utils.DATETIME_FORMAT)

    window_keys.append(new_entry_date)
    if new_entry_date not in window:
        window[new_entry_date] = []
    window[new_entry_date].append(new_entry)


def __get_preamble(entry: dict) -> list:
    (owner, repo) = exp_utils.get_owner_and_repo_from_source_path(
        entry['__source_path'])
    project = f'{owner}/{repo}'
    submitter_id = entry['user_data']['id']
    closed_at = entry['closed_at']
    return [entry['id'], project, submitter_id, entry['number'], closed_at]


def __handle_new_entry(
        new_entry: dict,
        time_window: timedelta,
        window_keys: deque,
        window: dict[datetime, list[dict]],
        issue_sw_features: list[SlidingWindowFeature],
        pr_sw_features: list[SlidingWindowFeature],
        output_features: list[Feature],
        csv_writer: csv.writer):

    __prune_entries(
        new_entry, time_window,
        window_keys, window,
        issue_sw_features,
        pr_sw_features
    )

    # Calculates features if it's a PR.
    is_pr = new_entry["__data_type"] == "pull-requests"
    if is_pr:
        data_point = [None] * len(output_features)
        for index, feature in enumerate(output_features):
            data_point[index] = feature.get_feature(new_entry)
        preamble = __get_preamble(new_entry)
        data_point = [*preamble, *data_point]
        csv_writer.writerow(data_point)

    __add_entry(
        new_entry,
        window_keys,
        window,
        pr_sw_features,
        issue_sw_features
    )


def __get_output_features(pr_features: list[Feature],
                          pr_sw_features: list[SlidingWindowFeature],
                          issue_sw_features: list[SlidingWindowFeature]) -> list[Feature]:
    all_features: list[Feature] = [
        *pr_features, *pr_sw_features, *issue_sw_features]
    output_features = [
        feature for feature in all_features if feature.is_output_feature()]
    return list(output_features), all_features


def __handle_chunk(
    task: Tuple[str | None, str],
    time_window: timedelta,
    task_id: int,
    base_path: str,
    feature_factory: Callable[[], Tuple[list[SlidingWindowFeature],
                                        list[SlidingWindowFeature],
                                        list[Feature]]],
    *_, **__
):

    previous_chunk, current_chunk = task
    print(
        f'Task-{task_id}: Starting with chunks: {previous_chunk=}, {current_chunk=}')

    issue_sw_features, pr_sw_features, pr_features = feature_factory()

    # output path name.
    chunk_name = os.path.basename(current_chunk)
    output_path = base_path + chunk_name
    print(f'Task-{task_id}: Outputting in "{output_path}".')

    # Selects output features
    output_features, _ = __get_output_features(
        pr_features, pr_sw_features, issue_sw_features)

    # Creates initial window.
    window, window_keys = __create_window_from_file(
        previous_chunk, issue_sw_features, pr_sw_features)

    print(f'Task-{task_id}: Loaded previous chunk: "{previous_chunk}".')

    # Iterates through the current chunks entries.
    with open(output_path, "w+", encoding='utf-8') as output_file:
        csv_writer = csv.writer(output_file)
        with open(current_chunk, "r", encoding='utf-8') as input_file:
            # Iterates through all entries and handles those.
            for line in input_file:
                new_entry = json.loads(line)
                __handle_new_entry(
                    new_entry,
                    time_window,
                    window_keys,
                    window,
                    issue_sw_features,
                    pr_sw_features,
                    output_features,
                    csv_writer
                )

    print(
        f'Task-{task_id}: Finished processing chunk: {previous_chunk=}, {current_chunk=}')


def __merge_chunk_results(
    output_path: str,
    chunk_file_names: str,
    chunk_output_base_path: str,
    output_features: list[Feature]
):
    # Combines the output of each file to the final output file
    # and removes the chunk output file.
    with open(output_path, "w+", encoding='utf-8')as output_file:
        # Create header
        header = [feature.get_name() for feature in output_features]
        header = ["ID", "Project Name", "Submitter ID",
                  "PR Number", "Closed At", *header]
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(header)

        # Merge entries.
        for chunk_file in chunk_file_names:
            file_name = os.path.basename(chunk_file)
            chunk_output_path = chunk_output_base_path + file_name
            print(f'Merging "{chunk_output_path}".')
            with open(chunk_output_path, "r", encoding='utf-8') as input_file:
                output_file.writelines(input_file)
            os.remove(chunk_output_path)
    print(f'Output path: "{output_path}".')


def create_sliding_window_dataset(
    output_path: str,
    chunk_base_path: str,
    chunk_output_base_path: str,
    input_issue_dataset_names: list[str],
    input_pr_dataset_names: list[str],
    feature_factory: Callable[[], Tuple[list[SlidingWindowFeature],
                                        list[SlidingWindowFeature],
                                        list[Feature]]],
    window_size_in_days: int,
    thread_count: int
):
    """
    Creates sliding window dataset using a multithreaded solution.
    """

    print(f'Using output path "{output_path}".')
    print(f'Using chunk base path: "{chunk_base_path}".')
    print(f'Using chunk output base path: "{chunk_output_base_path}".')

    window_delta = timedelta(days=window_size_in_days)

    # Creates relevant directories.
    safe_makedirs(os.path.dirname(output_path))
    safe_makedirs(chunk_base_path)
    safe_makedirs(chunk_output_base_path)

    # Creates data iterator.
    chunk_generator = __create_data_chunk_stream(input_issue_dataset_names,
                                                 input_pr_dataset_names,
                                                 window_delta,
                                                 chunk_base_path)
    chunk_file_names = []
    chunk_generator = chain_with_intermediary_callback(
        chunk_generator, chunk_file_names.append)
    chunk_generator = tuple_chain(chunk_generator, yield_first=True)

    # Selects output features
    # NOTE: they're loaded before the parallelization so that the
    # threads don't have to load the global vars separately.
    issue_sw_features, pr_sw_features, pr_features = feature_factory()
    output_features, all_features = __get_output_features(
        pr_features, pr_sw_features, issue_sw_features)
    print(f'Loaded {len(output_features)}/{len(all_features)} output features.')

    # Runs all tasks.
    parallelize_tasks(
        chunk_generator,
        __handle_chunk,
        thread_count,
        # kwargs:
        time_window=window_delta,
        base_path=chunk_output_base_path,
        feature_factory=feature_factory
    )

    # Prunes all chunk data files.
    for file in chunk_file_names:
        os.remove(file)

    __merge_chunk_results(
        output_path,
        chunk_file_names,
        chunk_output_base_path,
        output_features
    )

    print("Done!")


def all_features_factory() -> Tuple[list[SlidingWindowFeature],
                                    list[SlidingWindowFeature],
                                    list[Feature]]:
    """
    Standard factory method for all features.
    """

    other_pr = swf.build_other_features()
    control_sw, control = swf.build_control_variables()
    ip_issue, ip_pr = swf.build_intra_project_features()
    se_pr, se_issue = swf.build_se_features()
    eco_pr, eco_issue = swf.build_eco_experience()
    deco_pr, deco_issue, ideco_pr, ideco_issue = swf.build_deco_features()
    sna_pr_graph, sna_issue_graph, centrality_features, local_centrality_measures = swf.build_centrality_features()

    issue_sw_features = [
        *ip_issue,
        *se_issue,
        *eco_issue,
        *deco_issue,
        *ideco_issue,
        *sna_issue_graph,
    ]

    pr_sw_features = [
        *control_sw,
        *ip_pr,
        *se_pr,
        *eco_pr,
        *deco_pr,
        *ideco_pr,
        *sna_pr_graph,
    ]

    pr_features = [
        *other_pr,
        *control,
        *local_centrality_measures
    ]

    return issue_sw_features, pr_sw_features, pr_features


def cmd_create_sliding_window_dataset():
    """
    Wrapper method for ``create_sliding_window_dataset``.
    Generates sliding window dataset using parameters from the command line.
    """

    exp_utils.load_paths_for_eco()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']
    output_file_name = get_argv(key='-o')
    output_path = exp_utils.TRAIN_DATASET_PATH(file_name=output_file_name)

    window_size_in_days = safe_get_argv(key="-w", default=None, data_type=int)
    thread_count = safe_get_argv(key='-t', default=1, data_type=int)

    chunk_base_path = exp_utils.BASE_PATH + "/temp/sna_chunks/"
    chunk_output_base_path = exp_utils.BASE_PATH + "/temp/sna_output/"

    start = datetime.now()

    create_sliding_window_dataset(
        output_path,
        chunk_base_path,
        chunk_output_base_path,
        input_issue_dataset_names,
        input_pr_dataset_names,
        all_features_factory,
        window_size_in_days,
        thread_count
    )

    deltatime = datetime.now() - start
    print(f'Runtime: {deltatime}.')

    return output_path


if __name__ == '__main__':
    cmd_create_sliding_window_dataset()
