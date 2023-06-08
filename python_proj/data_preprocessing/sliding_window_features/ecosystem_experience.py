
from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import *
from python_proj.utils.util import has_keys


class SubmitterExperienceEcosystemPullRequestSuccessRate(SlidingWindowFeature):
    """
    Calculates the experience of the pull request submitter in terms of 
    pull request success rate inside the ecosystem, excluding intra-project experience.
    """

    _user_to_project_success_rate: dict[int,
                                        dict[str, PullRequestSuccess]] = {}

    def __handle(self, entry: dict, sign: int):
        # New user.
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_success_rate:
            self._user_to_project_success_rate[user_id] = {}
        # New project.
        project = entry["__source_path"]
        if project not in self._user_to_project_success_rate[user_id]:
            self._user_to_project_success_rate[user_id][project] = PullRequestSuccess(
            )
        # Handles entry
        if entry["merged"]:
            self._user_to_project_success_rate[user_id][project].merged += sign
        else:
            self._user_to_project_success_rate[user_id][project].unmerged += sign

    def add_entry(self, entry: dict):
        self.__handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.__handle(entry, sign=-1)

    def _get_cumulative_success_rate(self, entry: dict) -> PullRequestSuccess:
        """
        Builds a cumulative ``PullRequestSuccess`` object including all 
        success entries of the person in the ecosystem, excluding intra-project
        experience. 
        """

        cumulative_success_rate = PullRequestSuccess()

        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_success_rate:
            return cumulative_success_rate
        current_project = entry["__source_path"]
        for project_key, success_rate in self._user_to_project_success_rate[user_id].items():
            if project_key == current_project:
                # Ignores all intra-project experience to
                # emphasize ecosystem experience.
                continue
            cumulative_success_rate.merged += success_rate.merged
            cumulative_success_rate.unmerged += success_rate.unmerged
        return cumulative_success_rate

    def get_feature(self, entry: dict) -> float:
        cumulative_success_rate = self._get_cumulative_success_rate(entry)
        return cumulative_success_rate.get_success_rate()

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["user_data", "__source_path", "merged"])


class SubmitterExperienceEcosystemPullRequestCount(SubmitterExperienceEcosystemPullRequestSuccessRate):
    """
    Calculates the experience of a developer using the total number of pull requests submitted
    in the ecosystem, excluding intra-project pull requests.
    """

    def get_feature(self, entry: dict) -> Any:
        cumulative_success_rate = self._get_cumulative_success_rate(entry)
        return cumulative_success_rate.get_total()


class SubmitterExperienceEcosystemIssueSubmissions(SlidingWindowFeature):
    """
    Tracks the user's experience in terms of total
    number of submitted issues.
    """

    _user_to_issue_submitted_count: dict[int, dict[str, int]] = {}

    def _handle(self, entry: dict, sign: int):
        # New user.
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_success_rate:
            self._user_to_project_success_rate[user_id] = {}
        # New project.
        project = entry["__source_path"]
        if project not in self._user_to_project_success_rate[user_id]:
            self._user_to_project_success_rate[user_id][project] = PullRequestSuccess(
            )
        self._user_to_issue_submitted_count[user_id][project] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, 1)

    def remove_entry(self, entry: dict):
        self._handle(entry, -1)

    def get_feature(self, entry: dict) -> int:
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_issue_submitted_count:
            return 0
        current_project = entry["__source_path"]
        total = 0
        for project, experience in self._user_to_issue_submitted_count[user_id].items():
            if project == current_project:
                continue
            total += experience
        return experience

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data', "__source_path"])


PR_SLIDING_WINDOW_FEATURES = [
    SubmitterExperienceEcosystemPullRequestCount(),
    SubmitterExperienceEcosystemPullRequestSuccessRate()
]

ISSUE_SLIDING_WINDOW_FEATURES = [
    SubmitterExperienceEcosystemIssueSubmissions(),
]
