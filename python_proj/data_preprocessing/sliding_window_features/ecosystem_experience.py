
from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import *


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
            self._user_to_project_success_rate[user_id][project].merged -= sign

    def add_entry(self, entry: dict):
        self.__handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.__handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> float:
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_success_rate:
            return 0.0
        project = entry["__source_path"]
        cumulative_success_rate = PullRequestSuccess()
        for key, value in self._user_to_project_success_rate[user_id].items():
            if key == project:
                continue
            cumulative_success_rate.merged += value.merged
            cumulative_success_rate.unmerged += value.unmerged
        return cumulative_success_rate.get_success_rate()


class SubmitterExperienceEcosystemPullRequestCount(SubmitterExperienceEcosystemPullRequestSuccessRate):
    """
    Calculates the experience of a developer using the total number of pull requests submitted
    in the ecosystem, excluding intra-project pull requests.
    """

    def get_feature(self, entry: dict) -> Any:
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_success_rate:
            return 0.0
        project = entry["__source_path"]
        cumulative_success_rate = PullRequestSuccess()
        for key, value in self._user_to_project_success_rate[user_id].items():
            if key == project:
                continue
            cumulative_success_rate.merged += value.merged
            cumulative_success_rate.unmerged += value.unmerged
        return cumulative_success_rate.get_total()


SLIDING_WINDOW_FEATURES = [
    SubmitterExperienceEcosystemPullRequestCount(),
    SubmitterExperienceEcosystemPullRequestSuccessRate()
]
