from csv import writer
from datetime import datetime, timedelta
from itertools import chain
from typing import Generator, Tuple, Dict, Any, List
import json
from uuid import uuid3, NAMESPACE_OID

from python_proj.utils.util import get_nested
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv, get_argv

import python_proj.data_preprocessing.sliding_window_features.control_variables as cvars
import python_proj.data_preprocessing.sliding_window_features.ecosystem_experience as ecovars
from python_proj.data_preprocessing.sliding_window_features.base import IsMerged, SlidingWindowFeature, Feature

input_file = None
output_file = None


def slide_through_timeframe(dataset_names: list[str],
                            dataset_types: list[str],
                            key_to_date: list[str],
                            window_size: timedelta = None) \
        -> Generator[Tuple[Dict[str, Dict], Dict], None, None]:
    # Hardcoded as this is an analysis-custom field added in the data sorter.
    source_key = "__source_path"
    window = {}

    ts_format = "%Y-%m-%dT%H:%M:%SZ"

    for entry in exp_utils.iterate_through_multiple_chronological_datasets(dataset_names, dataset_types):
        new_date = get_nested(entry, key_to_date)
        dt_new_date = datetime.strptime(new_date, ts_format)

        # HACK: This should be unnecessary if the integrator key is always present in each entry.
        integrator_key = exp_utils.get_integrator_key(entry)
        if integrator_key not in entry:
            # print(json.dumps(entry))
            continue

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
            yield ({}, entry)
            continue

        pruned_entries = prune_window()

        # Add new key
        new_source = entry[source_key]
        window[new_source] = entry

        # Outputs iterable.
        yield (pruned_entries, entry)


def data_set_generator(intra_pr_features: list[Feature],
                       sw_features_prs: list[SlidingWindowFeature],
                       sw_features_issues: list[SlidingWindowFeature],
                       dataset_names: list[str],
                       dataset_types: list[str],
                       window_size: timedelta = None) \
        -> Generator[list[str], list[Any], None]:
    """
    Generates the dataset, updating the intra-PR and sliding window 
    features with respect to the provided window size.
    """

    closed_at_key = ["closed_at"]

    # Outputs header.
    all_features = list(chain(intra_pr_features, sw_features_prs, sw_features_issues))

    print(f'Loaded {len(all_features)} features.')

    data_headers = [field.get_name() for field in all_features]
    yield ['UUID', 'PR-Source', 'PR-ID', "User-ID", "Closed-At", *data_headers]

    # Generates data.
    for pruned_entries, new_entry in slide_through_timeframe(dataset_names, dataset_types,
                                                             closed_at_key, window_size):
        # Generates data point by iterating through all field factories.

        entry_is_pr = new_entry["__data_type"] == "pr"
        
        try:

            # Selects to-be-updated sliding window features
            # based on whether we're processing a pull request.
            sw_features = sw_features_prs if entry_is_pr \
                else sw_features_issues

            # Removes pruned entries from sliding window.
            for sw_feature in sw_features:
                for entry in pruned_entries.values():
                    sw_feature.remove_entry(entry)

            # Retrieves feature values if necessary.
            if entry_is_pr:
                data_point = [None] * len(all_features)
                for index, feature in enumerate(all_features):
                    data_point[index] = feature.get_feature(new_entry)

            # Adds new entry to sliding window.
            for sw_feature in sw_features:
                sw_feature.add_entry(new_entry)

        except:
            print("I FAILED")
            print(json.dumps(new_entry))
            raise
        
        if not entry_is_pr:
            continue

        # Gets bookkeeping variables.
        pr_source = new_entry['__source_path'].split(
            "/")[-1].split('.')[0].replace("--", '/')
        uid = new_entry["user_data"]["id"]
        prid = new_entry['id']
        uuid = str(uuid3(NAMESPACE_OID, f'{uid}_{prid}_{pr_source}'))
        closed_at = new_entry["closed_at"]
        yield [uuid, pr_source, prid, uid, closed_at, *data_point]


def get_all_features() -> 'Tuple(List[Feature], List[SlidingWindowFeature], List[SlidingWindowFeature])':
    intra_features = [IsMerged(), *cvars.INTRA_PR_FEATURES]
    sw_features_pr = [*cvars.SLIDING_WINDOW_FEATURES,
                      *ecovars.SLIDING_WINDOW_FEATURES]
    sw_features_issue = []
    return intra_features, sw_features_pr, sw_features_issue


def build_dataset(output_dataset_name: str,
                  input_dataset_names: list[str],
                  input_dataset_types: list[str],
                  window_size_in_days: int | None):
    output_name = f"{output_dataset_name}_cumulative_dataset" if window_size_in_days is None \
        else f"{output_dataset_name}_windowed_{window_size_in_days}d_dataset"
    output_path = exp_utils.TRAIN_DATASET_PATH(file_name=output_name)

    print(f'Outputting at: {output_path}')

    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        intra_features, sw_features_pr, sw_features_issue = get_all_features()
        for entry in data_set_generator(intra_features, sw_features_pr, sw_features_issue,
                                        input_dataset_names, input_dataset_types):
            csv_writer.writerow(entry)


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    output_dataset_name = get_argv(key="-n")

    input_dataset_names = exp_utils.get_file_name().split(",")
    input_dataset_types = get_argv(key='-t').split(",")

    days = safe_get_argv(key='-d', default=None, data_type=int)

    build_dataset(output_dataset_name, input_dataset_names,
                  input_dataset_types, days)
