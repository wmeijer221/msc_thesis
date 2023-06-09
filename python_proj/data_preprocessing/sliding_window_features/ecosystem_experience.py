"""
Implements the features tracking the ecosystem experience of an individual;
i.e., the experience they acquired through submitting PRs, issues, and comments.
"""

from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature, PullRequestSuccess
from python_proj.utils.util import has_keys, SafeDict


class SubmitterEcosystemExperiencePullRequestSuccessRate(SlidingWindowFeature):
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


class SubmitterEcosystemExperiencePullRequestCount(SubmitterEcosystemExperiencePullRequestSuccessRate):
    """
    Calculates the experience of a developer using the total number of pull requests submitted
    in the ecosystem, excluding intra-project pull requests.
    """

    def get_feature(self, entry: dict) -> Any:
        cumulative_success_rate = self._get_cumulative_success_rate(entry)
        return cumulative_success_rate.get_total()


class SubmitterEcosystemExperienceIssueSubmissions(SlidingWindowFeature):
    """
    Tracks the user's experience in terms of total
    number of submitted issues.
    """

    _user_to_project_issue_submitted_count: dict[int, dict[str, int]] = {}

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
        self._user_to_project_issue_submitted_count[user_id][project] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, 1)

    def remove_entry(self, entry: dict):
        self._handle(entry, -1)

    def get_feature(self, entry: dict) -> int:
        user_id = entry["user_data"]["id"]
        if user_id not in self._user_to_project_issue_submitted_count:
            return 0
        current_project = entry["__source_path"]
        total = 0
        for project, experience in self._user_to_project_issue_submitted_count[user_id].items():
            if project == current_project:
                continue
            total += experience
        return experience

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data', "__source_path"])


class SubmitterEcosystemExperiencePullRequestCommentCount(SlidingWindowFeature):
    """Counts the number of times a person has commented on a pull request."""

    _user_to_project_pr_comment_count: SafeDict[int, SafeDict[str, int]] = SafeDict(
        default_value=SafeDict,
        default_value_constructor_kwargs={'default_value': 0})

    def _handle(self, entry: dict, sign: int):
        if entry["comments"] == 0:
            return

        project = entry["__source_path"]
        for comment in entry["comments_data"]:
            commenter = comment["user_data"]
            commenter_id = commenter['id']
            self._user_to_project_pr_comment_count[commenter_id][project] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, 1)

    def remove_entry(self, entry: dict):
        self._handle(entry, -1)

    def get_feature(self, entry: dict) -> int:
        user_id = entry["user_data"]["id"]
        current_project = entry["__source_path"]
        total = 0
        for project, experience in self._user_to_project_pr_comment_count[user_id].items():
            if project == current_project:
                continue
            total += experience
        return experience

    def is_valid_entry(self, entry: dict) -> bool:
        has_basics = has_keys(entry, ['comments', '__source_path'])
        if not has_basics:
            return False
        return has_keys(entry, ['comments_data'])


class SubmitterEcosystemExperienceCommentsOnIssues(SubmitterEcosystemExperiencePullRequestCommentCount):
    """
    The handled datastructure is exactly the same as that for PRs,
    so there is no need whatsoever to re-implement this behaviour for issues.
    The class is just here to ensure the feature has a different name.
    """


PR_SLIDING_WINDOW_FEATURES = [
    SubmitterEcosystemExperiencePullRequestCount(),
    SubmitterEcosystemExperiencePullRequestSuccessRate(),
    SubmitterEcosystemExperiencePullRequestCommentCount(),
]

ISSUE_SLIDING_WINDOW_FEATURES = [
    SubmitterEcosystemExperienceIssueSubmissions(),
    SubmitterEcosystemExperienceCommentsOnIssues(),
]
