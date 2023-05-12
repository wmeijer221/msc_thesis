from datetime import datetime, timedelta
from typing import Generator, Tuple, Dict, Any, Callable
import json
from csv import writer
from uuid import uuid3, NAMESPACE_OID
from dataclasses import dataclass
from sys import argv

from python_proj.utils.util import get_nested


def slide_through_timeframe(file_name: str, key_to_date: list[str], window_size: timedelta = None) -> Generator[Tuple[Dict[str, Dict], Dict], None, None]:
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


class DataFieldFactory:
    # TODO: change to constructor argument.
    key_to_user_id: list[str] = None
    _values: dict[str, Any] = None

    def __init__(self, constructor_type: Callable[[None], Any]) -> None:
        self._constructor_type = constructor_type
        self._values = {}

    def get_name(self) -> str:
        return self.__class__.__name__

    def get(self, entry: dict) -> Any:
        raise Exception("Not implemented.")

    def add(self, entry: dict):
        raise Exception("Not implemented.")

    def remove(self, entry: dict):
        raise Exception("Not implemented.")

    def get_user_id(self, entry: dict) -> str:
        uid = get_nested(entry, self.key_to_user_id)
        if not uid in self._values:
            new_entry = self._constructor_type()
            self._values[uid] = new_entry
        return uid


class IntraPRFieldFactory(DataFieldFactory):
    def __init__(self) -> None:
        def entry_constructor(): return None
        super().__init__(entry_constructor)

    def add(self, entry: dict):
        pass

    def remove(self, entry: dict):
        pass


class DepPRIsMerged(IntraPRFieldFactory):
    def get(self, entry: dict) -> Any:
        return bool(entry['merged'])


class ContSameUser(IntraPRFieldFactory):
    """
    Implements control variable suggested by Zhang (2022) whether
    the pull request is integrated by the same person.
    """

    MERGED_BUT_UNKNOWN = "merged_but_unknown"
    NOT_MERGED = "not_merged"
    MERGED_AND_DIFFERENT = "merged_and_different"
    MERGED_AND_SAME = "merged_and_same"

    def get(self, entry: dict) -> Any:
        merged = get_nested(entry, ['merged'])
        is_merged = bool(merged)
        if is_merged:
            uid = get_nested(entry, self.key_to_user_id)
            i_uid = get_nested(entry, ['merged_by_data', 'id'])
            if i_uid is None:
                # Old PRs miss this data I think.
                return self.MERGED_BUT_UNKNOWN
            elif uid == i_uid:
                return self.MERGED_AND_SAME
            else:
                return self.MERGED_AND_DIFFERENT
        else:
            return self.NOT_MERGED


class ContLifetime(IntraPRFieldFactory):
    """
    Implements control variable suggested by Zhang (2022);
    the lifetime of the PR in minutes.
    """

    def get(self, entry: str) -> Any:
        ts_format = "%Y-%m-%dT%H:%M:%SZ"
        created_at = datetime.strptime(entry['created_at'], ts_format)
        closed_at = datetime.strptime(entry['closed_at'], ts_format)

        dt = closed_at - created_at
        lifetime_in_minutes = dt.total_seconds() / 60

        return lifetime_in_minutes


class ContPriorReviewNum(DataFieldFactory):
    """
    FOR THIS CONTROL VARIABLE TO MAKE SENSE, THE PR's 
    CORRESPONDING ISSUE DATA MUST BE DOWNLOADED AS WELL,
    THIS HAS A ``closed_by`` FIELD.
    """

    _integrator_experience: dict[str, dict[str, int]] = None
    # HACK: Sensitive to incorrect state bugs.
    _last: list[str] = None

    def __init__(self) -> None:
        super().__init__(lambda: None)
        self._integrator_experience = {}
        self._last = []

    def handle(self, entry: dict, entry_change: int):
        iid = get_nested(entry, ["merged_by_data", "id"])

        if iid is None:
            self._last = []
            return

        if not iid in self._integrator_experience:
            self._integrator_experience[iid] = {}

        project = entry["__source_path"]
        if not project in self._integrator_experience[iid]:
            self._integrator_experience[iid][project] = 0

        self._integrator_experience[iid][project] += entry_change
        self._last = [iid, project]

    def add(self, entry: dict):
        self.handle(entry, 1)

    def remove(self, entry: dict):
        self.handle(entry, -1)

    def get(self, _: str) -> Any:
        if len(self._last) == 0:
            return "no_integrator_data"
        experience = get_nested(self._integrator_experience, self._last)
        if experience is None:
            return 0
        else:
            return experience


class ContHasComments(IntraPRFieldFactory):
    def get(self, entry: dict) -> Any:
        comment_count = entry['comments']
        return comment_count > 0


class ContNumCommits(IntraPRFieldFactory):
    def get(self, entry: dict) -> Any:
        # commit_count = entry['commits']
        # if commit_count > 200:
        #     print(entry)

        return entry['commits']


class ContDevSuccessRate(DataFieldFactory):
    @dataclass
    class SuccessRate:
        count: int = 0.0
        success_rate: float = 0.0

        def set(self, count: int, success_rate: float):
            self.count = count
            self.success_rate = success_rate

    def __init__(self) -> None:
        super().__init__(lambda: {})

    def handle(self, entry: dict, sign: int):
        uid = self.get_user_id(entry)
        project_id = get_nested(entry, ['__source_path'])

        # Adds entry if non-existent.
        if not project_id in self._values[uid]:
            self._values[uid][project_id] = ContDevSuccessRate.SuccessRate()

        count = self._values[uid][project_id].count
        success_rate = self._values[uid][project_id].success_rate

        is_merged = bool(entry['merged'])
        success_rate = success_rate * count + (sign if is_merged else 0)
        count += sign
        if count > 0:
            success_rate /= count
        else:
            success_rate = 0.0

        self._values[uid][project_id].set(count, success_rate)

    def add(self, entry: dict):
        self.handle(entry, sign=1)

    def remove(self, entry: dict):
        self.handle(entry, sign=-1)

    def get(self, entry: dict) -> Any:
        uid = self.get_user_id(entry)
        user_data = self._values[uid]
        project_id = get_nested(entry, ['__source_path'])
        project_data = user_data[project_id]
        return project_data.success_rate


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
    file_name = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json"
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
    output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/cumulative_dataset.csv"
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
    output_path = f"./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/windowed_{days}d_dataset.csv"
    with open(output_path, "w+") as output_file:
        csv_writer = writer(output_file)
        # TODO: add ``ContPriorReviewNum``, ``ContSameUser`` when its finished.
        fields = [DepPRIsMerged, ContLifetime, ContHasComments, ContNumCommits,
                  ContDevSuccessRate, PRCountEco, PRAcceptanceRateEco]
        ninety_days = timedelta(days=90)
        for index, entry in enumerate(data_set_iterator(fields, window_size=ninety_days)):
            csv_writer.writerow(entry)
            # if index == 10:
            #     break


if __name__ == "__main__":
    mode = argv[argv.index("-m") + 1]
    match mode:
        case 'c':
            build_cumulative_dataset()
        case 'w':
            days = int(argv[argv.index('-d') + 1])
            build_windowed_dataset(days)
