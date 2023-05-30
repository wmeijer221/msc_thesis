"""
Implements utility functions for the general experiment.
"""

from functools import partial
from datetime import datetime
from os import getenv
import json

from python_proj.utils.arg_utils import safe_get_argv

# Default argv keys.
ECO_KEY = "-e"
DATA_SOURCE_KEY = "-d"
FILE_NAME_KEY = "-f"

BASE_PATH = getenv("EXPERIMENT_BASE_PATH", default="./data/")

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
    "libraries/{eco}-libraries-1.6.0-2020-01-12/{data_source}/{file_name}.csv"

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


def load_paths_for_eco(eco_key: str = ECO_KEY):
    global PROJECTS_WITH_REPO_PATH, RAW_DATA_PATH, FILTER_PATH, CHRONOLOGICAL_DATASET_PATH, \
        FIGURE_PATH, TRAIN_DATASET_PATH

    eco = safe_get_argv(eco_key, "npm")

    PROJECTS_WITH_REPO_PATH = partial(PROJECTS_WITH_REPO_PATH.format, eco=eco)
    RAW_DATA_PATH = partial(RAW_DATA_PATH.format, eco=eco)
    FILTER_PATH = partial(FILTER_PATH.format, eco=eco)
    CHRONOLOGICAL_DATASET_PATH = partial(
        CHRONOLOGICAL_DATASET_PATH.format, eco=eco)
    FIGURE_PATH = partial(FIGURE_PATH.format, eco=eco)
    TRAIN_DATASET_PATH = partial(TRAIN_DATASET_PATH.format, eco=eco)


# TODO: rename this to "data_source" for consistency
def load_paths_for_data_path(data_source_key: str = DATA_SOURCE_KEY):
    global RAW_DATA_PATH, CHRONOLOGICAL_DATASET_PATH, FIGURE_PATH, TRAIN_DATASET_PATH

    data_source = safe_get_argv(data_source_key, "pull-requests")
    # Assumes ``load_paths_for_eco`` has been called.
    RAW_DATA_PATH = partial(RAW_DATA_PATH, data_type=data_source)
    CHRONOLOGICAL_DATASET_PATH = partial(
        CHRONOLOGICAL_DATASET_PATH, data_type=data_source)
    FIGURE_PATH = partial(FIGURE_PATH, data_source=data_source)
    TRAIN_DATASET_PATH = partial(TRAIN_DATASET_PATH, data_source=data_source)


def load_paths_for_file_name(file_name_key: str = FILE_NAME_KEY):
    global CHRONOLOGICAL_DATASET_PATH, FIGURE_PATH

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


def iterate_through_chronological_data():
    print(f'Iterating through "{CHRONOLOGICAL_DATASET_PATH}".')
    with open(CHRONOLOGICAL_DATASET_PATH, "r") as input_file:
        for line in input_file:
            try:
                yield json.loads(line.strip())
            except Exception as ex:
                ex.add_note(line)
                raise


def get_integrator_key(entry):
    return "merged_by" if entry["merged"] else "closed_by"


def get_owner_and_repo_from_source_path(source_path) -> tuple[str, str]:
    """
    Helper method for string magic. 
    Returns ``(owner, repo)``.
    """
    file_name_with_ext = source_path.split("/")[-1]
    file_name = ".".join(file_name_with_ext.split(".")[:-1])
    owner_repo = file_name.split("--")
    return (owner_repo[0], owner_repo[1])
