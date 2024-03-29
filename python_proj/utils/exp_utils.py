"""
Implements utility functions for the general experiment.
"""

from functools import partial
from datetime import datetime
from os import getenv
import json
from typing import Iterator
from numbers import Number
import math


from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.util import OpenMany, ordered_chain

SOURCE_PATH_KEY = "__source_path"

# Default argv keys.
ECO_KEY = "-e"
DATA_SOURCE_KEY = "-d"
FILE_NAME_KEY = "-f"

BASE_PATH = getenv("EXPERIMENT_BASE_PATH", default="./data/")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Default file paths.
PROJECTS_WITH_REPO_PATH: str | partial[str] = \
    BASE_PATH + \
    "libraries/{eco}-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
RAW_DATA_PATH: str | partial[str] = BASE_PATH + \
    "libraries/{eco}-libraries-1.6.0-2020-01-12/{data_type}/{owner}--{repo}{ext}.json"
FILTER_PATH: str | partial[str] = BASE_PATH + \
    "libraries/{eco}-libraries-1.6.0-2020-01-12/predictors/included_projects{filter_type}.csv"
CHRONOLOGICAL_DATASET_PATH: str | partial[
    str] = BASE_PATH + "libraries/{eco}-libraries-1.6.0-2020-01-12/{data_type}/{file_name}.json"
FIGURE_PATH = BASE_PATH + \
    "figures/demographics/{eco}/{data_source}/{file_name}/{figure_name}.png"
TRAIN_DATASET_PATH = BASE_PATH + \
    "libraries/{eco}-libraries-1.6.0-2020-01-12/{file_name}.csv"

LIBRARIES_IO_DATASET_END_DATE = datetime(year=2020, month=1, day=12)

PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS = \
    ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp',
     'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL',
     'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp',
     'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count',
     'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count',
     'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description',
     'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp',
     'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size',
     'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?',
     'Repository Wiki enabled?', 'Repository Pages enabled?', 'Repository Forks Count',
     'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch',
     'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner',
     'Repository License', 'Repository Contributors Count', 'Repository Readme filename',
     'Repository Changelog filename', 'Repository Contributing guidelines filename',
     'Repository License filename', 'Repository Code of Conduct filename',
     'Repository Security Threat Model filename', 'Repository Security Audit filename',
     'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank',
     'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?',
     'Repository Logo URL', 'Repository Keywords']

# Finds indices of relevant fields.
repo_host_type_index = PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS.index(
    "Repository Host Type")
repo_name_index = PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS.index(
    "Repository Name with Owner")
is_fork_index = PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS.index(
    "Repository Fork?")
# HACK: Somehow the index is misaligned by 1.
prs_enabled_index = PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS.index(
    "Repository Pull requests enabled?") + 1


def load_paths_for_all_argv():
    load_paths_for_eco()
    load_paths_for_data_path()
    load_paths_for_file_name()


ECO_IS_LOADED = False


def load_paths_for_eco(eco_key: str = ECO_KEY, eco: str | None = None):
    global PROJECTS_WITH_REPO_PATH, RAW_DATA_PATH, FILTER_PATH, CHRONOLOGICAL_DATASET_PATH, \
        FIGURE_PATH, TRAIN_DATASET_PATH, ECO_IS_LOADED

    if ECO_IS_LOADED:
        return

    ECO_IS_LOADED = True

    if eco is None:
        eco = safe_get_argv(eco_key, "npm")

    PROJECTS_WITH_REPO_PATH = partial(PROJECTS_WITH_REPO_PATH.format, eco=eco)
    RAW_DATA_PATH = partial(RAW_DATA_PATH.format, eco=eco)
    FILTER_PATH = partial(FILTER_PATH.format, eco=eco)
    CHRONOLOGICAL_DATASET_PATH = partial(
        CHRONOLOGICAL_DATASET_PATH.format, eco=eco)
    FIGURE_PATH = partial(FIGURE_PATH.format, eco=eco)
    TRAIN_DATASET_PATH = partial(TRAIN_DATASET_PATH.format, eco=eco)


DATA_SOURCE_IS_LOADED = False
# TODO: rename this to "data_source" for consistency


def load_paths_for_data_path(data_source_key: str = DATA_SOURCE_KEY, data_source: str | None = None):
    global RAW_DATA_PATH, CHRONOLOGICAL_DATASET_PATH, FIGURE_PATH, TRAIN_DATASET_PATH, DATA_SOURCE_IS_LOADED

    if DATA_SOURCE_IS_LOADED:
        return

    DATA_SOURCE_IS_LOADED = True

    if data_source is None:
        data_source = safe_get_argv(data_source_key, "pull-requests")
    # Assumes ``load_paths_for_eco`` has been called.
    RAW_DATA_PATH = partial(RAW_DATA_PATH, data_type=data_source)
    CHRONOLOGICAL_DATASET_PATH = partial(
        CHRONOLOGICAL_DATASET_PATH, data_type=data_source)
    FIGURE_PATH = partial(FIGURE_PATH, data_source=data_source)
    TRAIN_DATASET_PATH = partial(TRAIN_DATASET_PATH, data_source=data_source)


FILE_NAME_IS_LOADED = False


def load_paths_for_file_name(file_name_key: str = FILE_NAME_KEY, file_name: str | None = None):
    global CHRONOLOGICAL_DATASET_PATH, FIGURE_PATH, FILE_NAME_IS_LOADED

    if FILE_NAME_IS_LOADED:
        return
    FILE_NAME_IS_LOADED = True

    if file_name is None:
        file_name = safe_get_argv(file_name_key, default="sorted")

    # TODO: This should be partial.
    CHRONOLOGICAL_DATASET_PATH = CHRONOLOGICAL_DATASET_PATH(
        file_name=file_name)
    FIGURE_PATH = partial(FIGURE_PATH, file_name=file_name)


def build_data_path_from_argv(eco_key: str = ECO_KEY, data_source_key: str = DATA_SOURCE_KEY,
                              file_name_key: str = FILE_NAME_KEY, file_ext: str = ".json"):
    base_path = BASE_PATH + \
        'libraries/{eco}-libraries-1.6.0-2020-01-12/{data_source}/{file_name}{file_ext}'
    eco = safe_get_argv(eco_key, default="npm")
    data_source = safe_get_argv(data_source_key, default="pull-requests")
    file_name = safe_get_argv(file_name_key, default='sorted')
    return base_path.format(eco=eco,
                            data_source=data_source,
                            file_name=file_name,
                            file_ext=file_ext)


def get_gh_tokens(gh_token_count) -> list[str]:
    all_gh_tokens = [getenv(f"GITHUB_TOKEN_{i}")
                     for i in range(1, gh_token_count + 1)]
    tokens = list(all_gh_tokens)

    if any([token is None for token in tokens]):
        raise Exception("A GH token is none!")

    return list(all_gh_tokens)


def get_gl_token() -> str:
    token = getenv("GITLAB_TOKEN_1")
    if token is None:
        raise Exception("GL token is none!")
    return token


def get_my_tokens(all_tokens: list, job_index: int, job_count: int) -> list:
    def is_my_token(token_index) -> bool:
        return token_index % job_count == job_index

    token_count = len(all_tokens)
    if token_count == 1 or job_count == 1:
        return all_tokens
    return list([token for token_index, token in enumerate(all_tokens)
                 if is_my_token(token_index)])


def get_eco(eco_key: str = ECO_KEY):
    return safe_get_argv(eco_key, default="npm")


def get_data_source(data_source_key: str = DATA_SOURCE_KEY):
    return safe_get_argv(data_source_key, default="pull-requests")


def get_file_name(file_name_key: str = FILE_NAME_KEY):
    return safe_get_argv(file_name_key, default="sorted")


def iterate_through_chronological_data(data_type=None,
                                       file_name=None):
    if not data_type is None and not file_name is None:
        input_path = CHRONOLOGICAL_DATASET_PATH(
            data_type=data_type, file_name=file_name)
    else:
        input_path = CHRONOLOGICAL_DATASET_PATH
    print(f'Iterating through "{input_path}".')
    with open(input_path, "r", encoding='utf-8') as input_file:
        for line in input_file:
            try:
                yield json.loads(line.strip())
            except Exception as ex:
                ex.add_note(line)
                raise


def iterate_through_multiple_chronological_datasets(dataset_names: list[str],
                                                    dataset_types: list[str] | None = None,
                                                    data_sources: list[str] | None = None,
                                                    print_progress_interval: int = 50000) \
        -> Iterator[dict]:
    "Assumes partial paths have been loaded up to the specific dataset names."

    if dataset_types is None:
        dataset_types = [''] * len(dataset_names)

    # TODO: There is no reason for dataset_types and data_sources to be separate parameters; they represent the same thing.
    if len(dataset_names) != len(dataset_types) \
            or (data_sources and len(dataset_names) != len(data_sources)):
        raise ValueError("input data has different lengths.")

    dt_format = "%Y-%m-%dT%H:%M:%SZ"

    def __key(entry: dict) -> Number:
        closed_at = entry["closed_at"]
        dt_closed_at = datetime.strptime(closed_at, dt_format)
        return dt_closed_at.timestamp()

    def __file_iterator(file) -> Iterator[dict]:
        for line in file:
            try:
                stripped_line = line.strip()
                yield json.loads(stripped_line)
            except json.JSONDecodeError:
                print(f'JSONDecodeError with {file=}')
                print(f'JSONDecodeError with {stripped_line=}')
                raise

    if data_sources is None:
        r_dataset_names = [CHRONOLOGICAL_DATASET_PATH(file_name=dataset_name)
                           for dataset_name in dataset_names]
    else:
        r_dataset_names = [CHRONOLOGICAL_DATASET_PATH(file_name=dataset_name, data_type=data_source)
                           for (dataset_name, data_source) in zip(dataset_names, data_sources)]

    print(
        f'Iterating through {len(r_dataset_names)} datasets: {r_dataset_names}')

    with OpenMany(r_dataset_names, mode="r") as dataset_files:
        dataset_iterators = [__file_iterator(dataset_file)
                             for dataset_file in dataset_files]
        for index, (file_idx, entry) in enumerate(ordered_chain(dataset_iterators, key=__key)):
            if index % print_progress_interval == 0:
                print(
                    f'Iterating through {index + 1}st chronological data entry.')
            dataset_type = dataset_types[file_idx]
            entry["__data_type"] = dataset_type
            yield entry


def iterate_through_multiple_chronological_issue_pr_datasets(
    issue_dataset_names: list[str],
    pull_request_dataset_names: list[str],
    issue_key: str = "issues",
    pr_key: str = "pull-requests",
    print_progress_interval: int = 50000
):
    """Iterates through various PR and issue datasets setting the correct datasource keys."""
    data_source = [issue_key] * len(issue_dataset_names)
    data_source.extend([pr_key] * len(pull_request_dataset_names))
    dataset_names = [*issue_dataset_names, *pull_request_dataset_names]
    return iterate_through_multiple_chronological_datasets(
        dataset_names,
        dataset_types=data_source,
        data_sources=data_source,
        print_progress_interval=print_progress_interval)


def get_integrator_key(entry):
    return "merged_by_data" if entry["merged"] else "closed_by"


def get_owner_and_repo_from_source_path(source_path) -> tuple[str, str]:
    """
    Helper method for string magic. 
    Returns ``(owner, repo)``.
    """
    file_name_with_ext = source_path.split("/")[-1]
    file_name = ".".join(file_name_with_ext.split(".")[:-1])
    owner_repo = file_name.split("--")
    return (owner_repo[0], owner_repo[1])

def get_repository_name_from_source_path(source_path) -> str:
    owner, repo = get_owner_and_repo_from_source_path(source_path)
    return f'{owner}/{repo}'

def log_transform(number: Number) -> Number:
    """Applies log-tranfsorm on the number."""
    return math.log10(1 + number)
