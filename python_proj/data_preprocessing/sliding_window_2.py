"""
Implements a sliding window algorithm used to generate training datasets
consisting of various intra and ecosystem-wide PR merge predictors. See
the method at the bottom of this script for the relevant command line
parameters.
"""

import itertools
import json
import tempfile
import shutil

from csv import reader, writer
from datetime import datetime, timedelta
from typing import Generator, Callable, Tuple, TypeVar, Any

import python_proj.utils.exp_utils as exp_utils

from python_proj.data_preprocessing.sliding_window_features import *
from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.util import *

T = TypeVar("T")

PR = 'pull-requests'
ISSUE = 'issues'


def slide_through_window(iterator: Generator[T, None, None],
                         datetime_key: Callable[[T], datetime],
                         window_size: timedelta | None = None) \
        -> Generator[Tuple[list[T], T], None, None]:
    """Slides through an iterator, keeping track of a set timewindow."""

    window: dict[datetime, list[T]] = {}

    for new_entry in iterator:
        # If window size is undefined, we don't need
        # to keep track of the window and can just
        # return the newest entry.
        if window_size is None:
            value_out = ([], new_entry)
            yield value_out
            continue

        # Determines boundaries of the current window.
        new_entry_date: datetime = datetime_key(new_entry)
        window_start: datetime = new_entry_date - window_size

        # Collects pruned entries.
        pruned_keys = []
        pruned_entries = []
        for entry_timestamps, entry_ids in window.items():
            if entry_timestamps < window_start:
                pruned_keys.append(entry_timestamps)
                pruned_entries.extend(entry_ids)

        value_out = (pruned_entries, new_entry)
        yield value_out

        # Prunes window
        for entry_timestamps in pruned_keys:
            del window[entry_timestamps]

        # Adds new entry
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


def __get_features():
    intra_pr_features = [
        *CONTROL_PR_FEATURES,
        *PR_FEATURES_OTHER,
        # *SNA_PR_FEATURES,
    ]
    sliding_window_features_pr = [
        *CONTROL_PR_SW_FEATURES,
        *IP_PR_SW_FEATURES,
        *ECO_EXP_PR_SW_FEATURES,
        *SNA_PR_SW_FEATURES,
        *DECO_EXP_PR_SW_FEATURES,
        *IDECO_EXP_PR_SW_FEATURES,
    ]
    sliding_window_features_issue = [
        *ECO_EXP_ISSUE_SW_FEATURES,
        *IP_ISSUE_SW_FEATURES,
        *SNA_ISSUE_SW_FEATURES,
        *DECO_EXP_ISSUE_SW_FEATURES,
        *IDECO_EXP_ISSUE_SW_FEATURES,
    ]
    feature_count = len(intra_pr_features) + \
        len(sliding_window_features_pr) + len(sliding_window_features_issue)
    print(f'{feature_count=}')
    return intra_pr_features, sliding_window_features_pr, sliding_window_features_issue


# def __get_second_run_features():
#     post_pr_features = [
#         *SNA_POST_PR_FEATURES
#     ]
#     sliding_window_features_pr = [
#         *SNA_PR_SW_FEATURES,
#     ]
#     sliding_window_features_issue = [
#         *SNA_ISSUE_SW_FEATURES,
#     ]

#     return post_pr_features, sliding_window_features_issue, sliding_window_features_pr


def generate_dataset(pr_dataset_names: list[str],
                     issue_dataset_names: list[str],
                     intra_pr_features: list[Feature],
                     pr_features: list[SlidingWindowFeature],
                     issue_features: list[SlidingWindowFeature],
                     window_size: timedelta) \
        -> Generator[list[Any], None, None]:
    """
    Generates dataset using the input files,
    the provided features, and the given time window.
    """

    dataset_names = list(itertools.chain(
        pr_dataset_names, issue_dataset_names))
    dataset_types = [PR if i < len(pr_dataset_names)
                     else ISSUE
                     for i in range(len(dataset_names))]
    dataset_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        dataset_names, dataset_types, dataset_types)

    def __get_closed_by(entry: dict) -> datetime:
        closed_by = entry["closed_at"]
        dt_closed_at = datetime.strptime(closed_by, "%Y-%m-%dT%H:%M:%SZ")
        return dt_closed_at

    # Iterables for easy iteration.
    all_features: list[Feature] = [*intra_pr_features,
                                   *pr_features,
                                   *issue_features]

    # Generates header.
    header = [feature.get_name() for feature in all_features]
    header = ["ID", "Project Name", "Submitter ID",
              "PR Number", "Closed At", *header]
    yield list(header)

    # Iterates through window, updating features on the go.
    window_iterator = slide_through_window(
        dataset_iterator, __get_closed_by, window_size)
    for pruned_entries, new_entry in window_iterator:
        try:
            # Removes pruned entries.
            for pruned_entry in pruned_entries:
                pruned_entry_is_pr = pruned_entry["__data_type"] == PR
                sliding_features = pr_features if pruned_entry_is_pr else issue_features
                for feature in sliding_features:
                    feature.remove_entry(pruned_entry)

            # Generates data points if currently dealing with a PR.
            new_entry_is_pr = new_entry["__data_type"] == PR
            if new_entry_is_pr:
                data_point = []
                for feature in all_features:
                    feature_value = feature.get_feature(new_entry)
                    data_point.append(feature_value)
                # Appends meta data to the entry for bookkeeping.
                preamble = __get_preamble(new_entry)
                yield [*preamble, *data_point]

            # Adds new entry.
            sliding_features = pr_features if new_entry_is_pr else issue_features
            for feature in sliding_features:
                feature.add_entry(new_entry)
        except:
            # print(f'{json.dumps(new_entry)=}')
            # print(f'{json.dumps(pruned_entries)=}')
            raise


def build_dataset(pr_dataset_names: list[str],
                  issue_dataset_names: list[str],
                  output_dataset_path: str,
                  window_size_in_days: int):
    """
    Writes all data entries to a training data file
    using all considered predictive features using
    data that lies within the given time window.
    """

    # Selects relevant features.
    intra_pr_features, sliding_window_features_pr, sliding_window_features_issue = __get_features()

    # Creates iterator.
    window_size = None
    if window_size_in_days is not None:
        window_size = timedelta(days=window_size_in_days)
    dataset_iterator = generate_dataset(
        pr_dataset_names,
        issue_dataset_names,
        intra_pr_features,
        sliding_window_features_pr,
        sliding_window_features_issue,
        window_size
    )

    # Outputs dataset.
    with open(output_dataset_path, "w+", encoding='utf-8') as output_dataset:
        csv_writer = writer(output_dataset)
        for datapoint in dataset_iterator:
            csv_writer.writerow(datapoint)

    # # Second run.
    # post_pr_features, sliding_window_features_issue, sliding_window_features_pr = __get_second_run_features()
    # for entry in itertools.chain(post_pr_features, sliding_window_features_pr, sliding_window_features_issue):
    #     if isinstance(entry, PostRunFeature):
    #         entry.late_init()

    # second_dataset_iterator = generate_dataset(
    #     pr_dataset_names,
    #     issue_dataset_names,
    #     post_pr_features,
    #     sliding_window_features_pr,
    #     sliding_window_features_issue,
    #     window_size
    # )
    # # Outputs dataset.
    # temp_out = tempfile.NamedTemporaryFile('w+', delete=False)
    # print(f'Storing temp data in "{temp_out.name}".')
    # with open(output_dataset_path, 'r', encoding='utf-8') as input_dataset:
    #     csv_writer = writer(temp_out)
    #     csv_reader = reader(input_dataset)

    #     # creates new header, skipping duplicate fields.
    #     old_header = next(csv_reader)
    #     new_header = next(second_dataset_iterator)
    #     novel_field_indices = [i for i, field in enumerate(new_header)
    #                     if field not in old_header]
    #     novel_fields = [new_header[i] for i in novel_field_indices]
    #     csv_writer.writerow([*old_header, *novel_fields])

    #     # Writes data point.
    #     for old_entry, new_entry in zip(csv_reader, second_dataset_iterator):
    #         novel_entries = [new_entry[i] for i in novel_field_indices]
    #         csv_writer.writerow([*old_entry, *novel_entries])

    # shutil.move(temp_out.name, output_dataset_path)


def sliding_window(thread_count: int = 1):
    """
    Loads relevant command line arguments, uses
    those to generate a training dataset, and outputs
    it to an output file.

    Possible arguments:
    -e:     ecosystem (optional, default='npm')
    -pd:    pull request input dataset. This is the chronological dataset (optional, default='').
    -id:    issues input dataset. This is the chronological dataset (optional, default='').
    -o:     name of the outputted training dataset (optional, default='test_dataset').
    -w:     the size of the used sliding window in days (optional, default=None).
    """

    exp_utils.load_paths_for_eco()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']

    # Sets path for output dataset.
    output_dataset_name = safe_get_argv(
        key="-o", default="test_dataset")
    output_dataset_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=output_dataset_name)
    print(f'Output path: "{output_dataset_path}".')

    days = safe_get_argv(key="-w", default=None, data_type=int)

    start_time = datetime.now()

    if thread_count == 1:
        build_dataset(
            input_pr_dataset_names,
            input_issue_dataset_names,
            output_dataset_path,
            days
        )
    else:
        raise NotImplementedError()
    end_time = datetime.now()
    delta_time = end_time - start_time
    print(f'Ran from {start_time} till {end_time} ({delta_time}).')


def remove_invalid_entries(input_pr_dataset_names: list[str],
                           input_issue_dataset_names: list[str]):
    """
    Removes invalid entries from the dataset. These are entries that
    cannot be processed by any of the selected features.
    """

    intra_pr_features, sliding_window_features_pr, sliding_window_features_issue = __get_features()
    pr_features = [*intra_pr_features, *sliding_window_features_pr]

    def __remove_invalid_entries(data_type: str, dataset_names: list[str], features: list[Feature]):
        for dataset_name in dataset_names:
            data_iterator = exp_utils.iterate_through_chronological_data(
                data_type=data_type, file_name=dataset_name)
            output_file_name = f"{dataset_name}_no_invalid"
            output_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
                data_type=data_type, file_name=output_file_name)
            print(f'Outputting in {output_path}')
            removed_count = 0
            total_entries = 0
            invalid_entries = SafeDict(default_value=0)
            with open(output_path, "w+", encoding='utf-8') as output_file:
                for entry in data_iterator:
                    total_entries += 1
                    is_valid = True
                    for feature in features:
                        if not feature.is_valid_entry(entry):
                            is_valid = False
                            # Bookkeeping of why something is removed.
                            invalid_entries[feature.get_name()] += 1
                    # Outputs valid entries.
                    if is_valid:
                        output_file.write(f'{json.dumps(entry)}\n')
                    else:
                        removed_count += 1
            perc = 100 * removed_count / total_entries
            print(
                f'Removed {removed_count}/{total_entries} ({perc:.03f}%) in {data_type}/{dataset_name} because:')
            print(json.dumps(invalid_entries, indent=4))

    __remove_invalid_entries(data_type='pull-requests',
                             dataset_names=input_pr_dataset_names,
                             features=pr_features)
    __remove_invalid_entries(data_type='issues',
                             dataset_names=input_issue_dataset_names,
                             features=sliding_window_features_issue)


if __name__ == "__main__":
    mode = safe_get_argv(key='-m', default='s')
    print(f'Starting in mode: {mode}.')
    match(mode):
        case 's':
            sliding_window()
        case 'r':
            exp_utils.load_paths_for_eco()
            # Sets path for chronological input data
            __input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                                        if entry != '']
            __input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                           if entry != '']
            remove_invalid_entries(
                __input_pr_dataset_names, __input_issue_dataset_names)
        case _:
            raise ValueError(f"Invalid mode {mode}.")
