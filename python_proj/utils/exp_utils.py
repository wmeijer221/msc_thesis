"""
Implements utility functions for the general experiment.
"""

from functools import partial
from datetime import datetime
from os import getenv

from python_proj.utils.arg_utils import safe_get_argv

# Default argv keys.
ECO_KEY = "-e"
DATA_SOURCE_KEY = "-d"
FILE_NAME_KEY = "-f"

# Default file paths.
PROJECTS_WITH_REPO_PATH = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
RAW_DATA_PATH = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/{data_type}/{owner}--{repo}{ext}.json"
FILTER_PATH = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/predictors/included_projects{filter_type}.csv"


def load_paths_for_eco(eco_key: str = ECO_KEY):
    global PROJECTS_WITH_REPO_PATH, RAW_DATA_PATH, FILTER_PATH

    eco = safe_get_argv(eco_key, "npm")

    PROJECTS_WITH_REPO_PATH = partial(PROJECTS_WITH_REPO_PATH.format, eco=eco)
    RAW_DATA_PATH = partial(RAW_DATA_PATH.format, eco=eco)
    FILTER_PATH = partial(FILTER_PATH.format, eco=eco)


def load_paths_for_data_path(data_source_key: str = DATA_SOURCE_KEY):
    global RAW_DATA_PATH

    data_source = safe_get_argv(data_source_key, "pull-requests")
    # Assumes the eco has been loaded already.
    RAW_DATA_PATH = partial(RAW_DATA_PATH, data_type=data_source)


def build_data_path_from_argv(eco_key: str = ECO_KEY, data_source_key: str = DATA_SOURCE_KEY,
                              file_name_key: str = FILE_NAME_KEY, file_ext: str = ".json"):
    base_path = './data/libraries/{eco}-libraries-1.6.0-2020-01-12/{data_source}/{file_name}{file_ext}'
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
