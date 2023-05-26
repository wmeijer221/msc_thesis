from csv import writer
from datetime import datetime, timedelta
from itertools import chain
import json
from typing import Generator, Tuple, Dict, Any, List
from uuid import uuid3, NAMESPACE_OID

from python_proj.utils.util import get_nested
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv

import python_proj.data_preprocessing.sliding_window_features.control_variables as cvars
import python_proj.data_preprocessing.sliding_window_features.ecosystem_experience as ecovars
from python_proj.data_preprocessing.sliding_window_features.base import IsMerged, SlidingWindowFeature, Feature

input_file = None
output_file = None


def slide_through_timeframe(file_name: str,
                            key_to_date: list[str],
                            window_size: timedelta = None) \
        -> Generator[Tuple[Dict[str, Dict], Dict], None, None]:
    # Hardcoded as this is an analysis-custom field added in the data sorter.
    source_key = "__source_path"
    window = {}

    ts_format = "%Y-%m-%dT%H:%M:%SZ"
    with open(file_name, "r") as input_file:
        # Iterates through input file.
        # Assumes that the input file is sorted.
        for line in input_file:
            j_entry = json.loads(line)
            new_date = get_nested(j_entry, key_to_date)
            dt_new_date = datetime.strptime(new_date, ts_format)

            def prune_window():
                # Prunes outdated entries in window.
                pruned_entries = {}
                for source, entry in window.items():
                    # Iterate through window to find outdated.
                    entry_date = get_nested(entry, key_to_date)
                    dt_entry_date = datetime.strptime(entry_date, ts_format)
                    delta = dt_new_date - dt_entry_date
                    if delta > window_size:
                        pruned_entries[source] = entry
                for source, entry in pruned_entries.items():
                    # Iterate through window to prune outdated.
                    del window[source]
                return pruned_entries

            # Prunes entries only if there's a window.
            if window_size is None:
                yield ({}, j_entry)
                continue

            pruned_entries = prune_window()

            # Add new key
            new_source = j_entry[source_key]
            window[new_source] = j_entry

            # Outputs iterable.
            yield (pruned_entries, j_entry)


def data_set_generator(intra_pr_features: list[Feature],
                       sliding_window_features: list[SlidingWindowFeature],
                       window_size: timedelta = None) \
        -> Generator[list[str], list[Any], None]:
    """
    Generates the dataset, updating the intra-PR and sliding window 
    features with respect to the provided window size.
    """

    file_name = exp_utils.CHRONOLOGICAL_DATASET_PATH
    closed_at_key = ["closed_at"]

    # Outputs header.
    all_features = list(chain(intra_pr_features, sliding_window_features))
    data_headers = [field.get_name() for field in all_features]
    yield ['UUID', 'PR-Source', 'PR-ID', "User-ID", "Closed-At", *data_headers]

    # Generates data.
    for pruned_entries, new_entry in slide_through_timeframe(file_name, closed_at_key, window_size):
        # Generates data point by iterating through all field factories.
        data_point = [None] * len(all_features)

        try:
            # Handles intra-pr features.
            for index, feature in enumerate(intra_pr_features):
                value = feature.get_feature(new_entry)
                data_point[index] = value

            # Handles sliding window features.
            for index, field in enumerate(sliding_window_features, start=len(intra_pr_features)):
                for entry in pruned_entries.values():
                    field.remove_entry(entry)
                data_point[index] = field.get_feature(new_entry)
                # This has to be added AFTERWARDS; else you'll have data leakage.
                field.add_entry(new_entry)
        except Exception as ex:
            print(new_entry)
            raise ex

        # Gets bookkeeping variables.
        pr_source = new_entry['__source_path'].split(
            "/")[-1].split('.')[0].replace("--", '/')
        uid = new_entry["user_data"]["id"]
        prid = new_entry['id']
        uuid = str(uuid3(NAMESPACE_OID, f'{uid}_{prid}_{pr_source}'))
        closed_at = new_entry["closed_at"]
        yield [uuid, pr_source, prid, uid, closed_at, *data_point]


def get_all_features() -> 'Tuple(List[Feature], List[SlidingWindowFeature])':
    intra_features = [IsMerged(), *cvars.INTRA_PR_FEATURES]
    swindow_features = [*cvars.SLIDING_WINDOW_FEATURES,
                        *ecovars.SLIDING_WINDOW_FEATURES]
    return intra_features, swindow_features


def build_cumulative_dataset():
    output_path = exp_utils.TRAIN_DATASET_PATH(file_name="cumulative_dataset")
    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        intra_features, swindow_features = get_all_features()
        for index, entry in enumerate(data_set_generator(intra_features, swindow_features)):
            csv_writer.writerow(entry)
            # if index == 10:
            #     break


def build_windowed_dataset(days: int):
    output_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=f"windowed_{days}d_dataset")
    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        intra_features, swindow_features = get_all_features()
        ninety_days = timedelta(days=90)
        for _, entry in enumerate(data_set_generator(swindow_features, intra_features, window_size=ninety_days)):
            csv_writer.writerow(entry)


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    mode = safe_get_argv(key="-m", default="c")
    match mode:
        case 'c':
            build_cumulative_dataset()
        case 'w':
            days = safe_get_argv(key="-d", default=20, data_type=int)
            build_windowed_dataset(days)
        case _:
            raise ValueError(f"Invalid mode {mode}.")
