from datetime import datetime, timedelta
from typing import Generator, Tuple, Dict, Any, Callable
import json
from csv import writer
from uuid import uuid3, NAMESPACE_OID
from dataclasses import dataclass
from sys import argv

from python_proj.utils.util import get_nested
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv



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


class PRCountEco(ContDevSuccessRate):
    """
    Counts the number of PRs per person inside the ecosystem.
    Returns the number of PRs that are made outside of the project
    (i.e., the get function excludes intra project PRs).
    """

    def get(self, entry: dict) -> Any:
        uid = self.get_user_id(entry)
        user_data = self._values[uid]
        project_id = get_nested(entry, ['__source_path'])
        pr_count = 0
        for project, entry in user_data.items():
            if project == project_id:
                continue
            pr_count += int(entry.count)
        return pr_count


class PRAcceptanceRateEco(ContDevSuccessRate):
    def get(self, entry: dict) -> Any:
        uid = self.get_user_id(entry)
        user_data = self._values[uid]
        project_id = get_nested(entry, ['__source_path'])
        eco_sr = ContDevSuccessRate.SuccessRate()
        for project, entry in user_data.items():
            if project == project_id:
                continue
            eco_sr.success_rate += entry.success_rate * entry.count
            eco_sr.count += entry.count
        if eco_sr.count > 0:
            eco_sr.success_rate /= eco_sr.count
        return eco_sr.success_rate


def data_set_iterator(data_fields: list[type], window_size: timedelta = None) -> Generator[list[str], list[Any], None]:
    file_name = exp_utils.CHRONOLOGICAL_DATASET_PATH
    closed_at_key = ["closed_at"]

    # Initializes fields.
    fields = [field() for field in data_fields]
    key_to_user_id = ['user_data', 'id']
    for field in fields:
        field.key_to_user_id = ['user_data', 'id']

    # Outputs header.
    data_headers = [field.get_name() for field in fields]
    yield ['UUID', 'PR-Source', 'PR-ID', "User-ID", "Closed-At", *data_headers]

    # Generates data.
    for pruned_entries, new_entry in slide_through_timeframe(file_name, closed_at_key, window_size):
        # Generates data point by iterating through all field factories.
        data_point = [None] * len(fields)
        uid = get_nested(new_entry, key_to_user_id)
        prid = new_entry['id']
        pr_source = new_entry['__source_path'].split(
            "/")[-1].split('.')[0].replace("--", '/')
        uuid = str(uuid3(NAMESPACE_OID, f'{uid}_{prid}_{pr_source}'))
        for index, field in enumerate(fields):
            # Updates fields
            for entry in pruned_entries.values():
                field.remove(entry)
            field.add(new_entry)

            # Gets relevant data for this data entry.
            data_point[index] = field.get(new_entry)
        closed_at = get_nested(new_entry, closed_at_key)
        yield [uuid, pr_source, prid, uid, closed_at, *data_point]


def build_cumulative_dataset():
    output_path = exp_utils.TRAIN_DATASET_PATH(file_name="cumulative_dataset")
    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        # TODO: add ``ContPriorReviewNum``, ``ContSameUser`` when its finished.
        fields = [DepPRIsMerged, ContLifetime, ContHasComments, ContNumCommits,
                  ContDevSuccessRate, PRCountEco, PRAcceptanceRateEco]
        # fields = [ContNumCommits]
        for index, entry in enumerate(data_set_iterator(fields)):
            csv_writer.writerow(entry)
            # if index == 10:
            #     break


def build_windowed_dataset(days: int):
    output_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=f"windowed_{days}d_dataset")
    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        # TODO: add ``ContPriorReviewNum``, ``ContSameUser`` when its finished.
        fields = [DepPRIsMerged, ContLifetime, ContHasComments, ContNumCommits,
                  ContDevSuccessRate, PRCountEco, PRAcceptanceRateEco]
        ninety_days = timedelta(days=90)
        for _, entry in enumerate(data_set_iterator(fields, window_size=ninety_days)):
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
