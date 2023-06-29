from typing import Any

from python_proj.data_preprocessing.sliding_window_features.base import Feature
from python_proj.utils.util import SafeDict, has_keys


class PullRequestIsMerged(Feature):
    """
    Whether the PR is merged. 
    Not a control variable, but I had to put it somewhere.
    """

    def get_feature(self, entry: dict) -> bool:
        return entry["merged"]

    def is_valid_entry(self, entry: dict) -> bool:
        return "merged" in entry


class SubmitterIsFirstTimeContributor(Feature):
    """
    Whether the contributor of this pull request submits a
    pr for the first time in the project.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__submitters_per_project = SafeDict(default_value=set)

    def get_feature(self, entry: dict) -> Any:
        project = entry['__source_path']
        submitter_id = entry['user_data']['id']
        is_first_time_contributor = submitter_id \
            not in self.__submitters_per_project[project]
        self.__submitters_per_project[project].add(submitter_id)
        return is_first_time_contributor

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data', "__source_path"])


def build_other_features():
    """Feature factory method."""
    pr_features_other = [
        PullRequestIsMerged(),
        SubmitterIsFirstTimeContributor(),
    ]
    return pr_features_other


PR_FEATURES_OTHER = build_other_features()
