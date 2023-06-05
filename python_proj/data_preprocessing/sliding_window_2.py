from datetime import datetime, timedelta
from typing import Generator, Callable, Tuple, TypeVar, Any
import itertools
from csv import writer

from python_proj.data_preprocessing.sliding_window_features.base import Feature, SlidingWindowFeature
from python_proj.data_preprocessing.sliding_window_features.control_variables import SLIDING_WINDOW_FEATURES, INTRA_PR_FEATURES
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import SLIDING_WINDOW_FEATURES as SLIDING_WINDOW_FEATURES_ECO
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv, get_argv

T = TypeVar("T")


def slide_through_window(iterator: Generator[T, None, None],
                         key: Callable[[T], datetime],
                         window_size: timedelta | None = None) \
        -> Generator[Tuple[list[T], T], None, None]:
    """Slides through an iterator, keeping track of a set timewindow."""

    window: dict[datetime, list[T]] = {}

    for new_entry in iterator:
        # If window size is undefined, we don't need
        # to keep track of the window and can just
        # return the newest entry.
        if window_size is None:
            yield ([], new_entry)
            continue

        # Determines boundaries of the current window.
        new_entry_date: datetime = key(new_entry)
        window_start: datetime = new_entry_date - window_size

        # Collects pruned entries.
        pruned_keys = []
        pruned_entries = []
        for key, value in window.items():
            if key < window_start:
                pruned_keys.append(key)
                pruned_entries.extend(value)

        yield (pruned_entries, new_entry)

        # Prunes window
        for key in pruned_keys:
            del window[key]

        # Adds new entry
        if new_entry_date not in window:
            window[new_entry_date] = []
        window[new_entry_date].append(new_entry)


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
    dataset_types = ["pr" if i < len(pr_dataset_names)
                     else "issue"
                     for i in range(len(dataset_names))]
    dataset_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        dataset_names, dataset_types)

    def __get_closed_by(entry: dict) -> datetime:
        closed_by = entry["closed_by"]
        dt_closed_by = datetime.strptime(closed_by, "%Y-%m-%dT%H:%M:%SZ")
        return dt_closed_by

    # Iterables for easy iteration.
    all_features: list[Feature] = [*intra_pr_features,
                                   *pr_features,
                                   *issue_features]

    # Generates header.
    header = [feature.get_name() for feature in all_features]
    yield list(header)

    # Used to track the number of invalid entries.
    invalid_entries: dict[str, int] = {
        feature.get_name(): 0 for feature in all_features}

    # Iterates through window, updating features on the go.
    window_iterator = slide_through_window(
        dataset_iterator, __get_closed_by, window_size)
    for pruned_entries, new_entry in window_iterator:
        print(new_entry)
        # Selects relevant sliding features.
        entry_is_pr = new_entry["__data_type"] == "pr"
        sliding_features = pr_features if entry_is_pr else issue_features

        # Removes pruned entries.
        for feature in sliding_features:
            for pruned_entry in pruned_entries:
                if feature.is_valid_entry(pruned_entry):
                    feature.remove_entry(pruned_entry)

        # Generates data points if currently dealing with a PR.
        if entry_is_pr:
            data_point = []
            for feature in all_features:
                if feature.is_valid_entry(new_entry):
                    feature_value = feature.get_feature(new_entry)
                    data_point.append(feature_value)
            yield list(data_point)

        # Adds new entry.
        for feature in sliding_features:
            if feature.is_valid_entry(new_entry):
                feature.add_entry(new_entry)
            else:
                # Updates the invalid entries count for bookkeeping.
                feature_name = feature.get_name()
                invalid_entries[feature_name] += 1

    # Prints the invalid entries count for bookkeeping.
    print(f'{invalid_entries=}')


def build_dataset(pr_dataset_names: list[str],
                  issue_dataset_names: list[str],
                  window_size_in_days: int):
    """
    Writes all data entries to a training data file 
    using all considered predictive features using 
    data that lies within the given time window.
    """

    # Selects relevant features.
    intra_pr_features = [*INTRA_PR_FEATURES]
    sliding_window_features_pr = [
        *SLIDING_WINDOW_FEATURES, *SLIDING_WINDOW_FEATURES_ECO]
    sliding_window_features_issue = []

    # Creates iterator.
    window_size = None
    if window_size_in_days is not None:
        window_size = timedelta(days=window_size_in_days)
    dataset_iterator = generate_dataset(pr_dataset_names,
                                        issue_dataset_names,
                                        intra_pr_features,
                                        sliding_window_features_pr,
                                        sliding_window_features_issue,
                                        window_size)

    # Outputs dataset.
    output_dataset_name = exp_utils.TRAIN_DATASET_PATH
    with open(output_dataset_name, "w+") as output_dataset:
        csv_writer = writer(output_dataset)
        for datapoint in dataset_iterator:
            csv_writer.writerow(datapoint)


def sliding_window():
    """
    Loads relevant command line arguments, uses 
    those to generate a training dataset, and outputs
    it to an output file.

    Possible arguments:
    -e:     ecosystem (optional, default='npm')
    -d:     data source (optional, default='pull-requests')
    -pd:    input dataset. This is the chronological dataset (optional, default='').
    -pi:    input dataset. This is the chronological dataset (optional, default='').
    -o:     name of the outputted training dataset (optional, default='training_dataset_{today}').
    -w:     the size of the used sliding window in days (optional, default=None).
    """

    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']

    # Sets path for output dataset.
    dt_now = datetime.now().strftime("%d-%m-%Y")
    output_dataset_name = safe_get_argv(
        key="-o", default=f"training_dataset_{dt_now}")
    exp_utils.TRAIN_DATASET_PATH = exp_utils.TRAIN_DATASET_PATH(
        file_name=output_dataset_name)

    days = safe_get_argv(key="-w", default=None, data_type=int)

    build_dataset(input_pr_dataset_names, input_issue_dataset_names, days)


if __name__ == "__main__":
    sliding_window()
