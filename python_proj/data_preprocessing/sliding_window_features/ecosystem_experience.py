"""
Implements the features tracking the ecosystem experience of an individual;
i.e., the experience they acquired through submitting PRs, issues, and comments.
"""

from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature, PullRequestSuccess
from python_proj.utils.util import has_keys, SafeDict


class EcosystemExperience(SlidingWindowFeature):
    """Base class for ecosystem experience features."""

    def project_is_ignored_for_cumulative_experience(self, current_project_id, other_project_id) -> bool:
        """Returns true if the experience current and other project are the same."""
        return current_project_id == other_project_id


# Pull requests.


class EcosystemExperienceSubmitterPullRequestSuccessRate(EcosystemExperience):
    """
    Calculates the experience of the pull request submitter in terms of 
    pull request success rate inside the ecosystem, excluding intra-project experience.
    """

    def __init__(self) -> None:
        self._user_to_project_success_rate: SafeDict[str, SafeDict[str, PullRequestSuccess]] = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={'default_value': PullRequestSuccess})

    def __handle(self, entry: dict, sign: int):
        # New user.
        user_id = entry["user_data"]["id"]
        project = entry["__source_path"]
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
        current_project = entry["__source_path"]
        for project_key, success_rate in self._user_to_project_success_rate[user_id].items():
            # Ignores intra-project experience.
            if self.project_is_ignored_for_cumulative_experience(current_project, project_key):
                continue
            cumulative_success_rate.merged += success_rate.merged
            cumulative_success_rate.unmerged += success_rate.unmerged
        return cumulative_success_rate

    def get_feature(self, entry: dict) -> float:
        cumulative_success_rate = self._get_cumulative_success_rate(entry)
        return cumulative_success_rate.get_success_rate()

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["user_data", "__source_path", "merged"])


class EcosystemExperienceSubmitterPullRequestSubmissionCount(EcosystemExperienceSubmitterPullRequestSuccessRate):
    """
    Calculates the experience of a developer using the total number of pull requests submitted
    in the ecosystem, excluding intra-project pull requests.
    """

    def get_feature(self, entry: dict) -> Any:
        cumulative_success_rate = self._get_cumulative_success_rate(entry)
        return cumulative_success_rate.get_total()


class EcosystemExperienceSubmitterPullRequestCommentCount(EcosystemExperience):
    """
    Counts the number of times a person has commented on a pull request, at an
    ecosystem level, excluding intra-project experience. It counts the total number; i.e.,
    when someone comments on a pull request twice, it will count as two.
    """

    def __init__(self) -> None:
        self._user_to_project_pr_comment_count: SafeDict[int, SafeDict[str, int]] = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={'default_value': 0})

    def _handle(self, entry: dict, sign: int):
        if entry["comments"] == 0:
            return
        project = entry["__source_path"]
        for comment in entry["comments_data"]:
            commenter_id = comment["user_data"]["id"]
            self._user_to_project_pr_comment_count[commenter_id][project] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self._handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> int:
        user_id = entry["user_data"]["id"]
        current_project = entry["__source_path"]
        total_experience = 0
        for project, experience in self._user_to_project_pr_comment_count[user_id].items():
            # Ignores intra-project experience.
            if self.project_is_ignored_for_cumulative_experience(current_project, project):
                continue
            total_experience += experience
        return total_experience

    def is_valid_entry(self, entry: dict) -> bool:
        has_basics = has_keys(entry, ['comments', '__source_path'])
        if not has_basics:
            return False
        if entry['comments'] > 0:
            # Entries where comments = 0, have no ``comments_data`` field.
            return has_keys(entry, ['comments_data'])
        return True


class EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(EcosystemExperienceSubmitterPullRequestCommentCount):
    """
    Counts the number of times a person has commented on a pull request, at an
    ecosystem level, excluding intra-project experience. This class differs from
    ``SubmitterEcosystemExperiencePullRequestCommentCount`` as it does NOT count 
    the total number of comments (i.e., if someone commented on a PR twice, it counts two), 
    and instead only counts participating in discussion (i.e., those two comments count as 1).

    Functionally, this class does all the same things as ``SubmitterEcosystemExperiencePullRequestDiscussionParticipationCount``
    though, hence why it inherits it and only overrides ``_handle``.
    """

    def _handle(self, entry: dict, sign: int):
        if entry["comments"] == 0:
            return
        project = entry["__source_path"]
        unique_commmenters = {comment['user_data']['id']
                              for comment in entry['comments_data']}
        for commenter_id in unique_commmenters:
            self._user_to_project_pr_comment_count[commenter_id][project] += sign


# Issue


class EcosystemExperienceSubmitterIssueSubmissionCount(EcosystemExperience):
    """
    Tracks the user's experience in terms of total number of submitted issues,
    at an ecosystem level, excluding intra-project experience.
    """

    def __init__(self) -> None:
        self._user_to_project_success_rate: SafeDict[int, SafeDict[str, int]] = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={'default_value': 0}
        )

    def _handle(self, entry: dict, sign: int):
        user_id = entry["user_data"]["id"]
        project = entry["__source_path"]
        self._user_to_project_success_rate[user_id][project] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self._handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> int:
        user_id = entry["user_data"]["id"]
        current_project = entry["__source_path"]
        total_experience = 0
        for project, experience in self._user_to_project_success_rate[user_id].items():
            # Ignores intra-project experience.
            if self.project_is_ignored_for_cumulative_experience(current_project, project):
                continue
            total_experience += experience
        return total_experience

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data', "__source_path"])


class EcosystemExperienceSubmitterIssueCommentCount(EcosystemExperienceSubmitterPullRequestCommentCount):
    """
    The handled datastructure is exactly the same as that for PRs,
    so there is no need whatsoever to re-implement this behaviour for issues.
    The class is just here to ensure the feature has a different name.

    Counts the number of comments on issues at an ecosystem level, excluding 
    intra-project experience. It counts the number of comments; i.e., if a person 
    commented on the same issue twice, it will count two experience entries.
    """


class EcosystemExperienceSubmitterIssueDiscussionParticipationCount(EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount):
    """
    This predictor is functionally exactly the same as ``SubmitterEcosystemExperiencePullRequestDiscussionParticipationCount``,
    and is only implemented as a separate class for its name.
    """


def build_eco_experience():
    eco_exp_pr_sw_features = [
        EcosystemExperienceSubmitterPullRequestSuccessRate(),
        EcosystemExperienceSubmitterPullRequestSubmissionCount(),
        EcosystemExperienceSubmitterPullRequestCommentCount(),
        # Participation count is almost the same thing as comment count.
        # SubmitterEcosystemExperiencePullRequestDiscussionParticipationCount(),
    ]
    eco_exp_issue_sw_features = [
        EcosystemExperienceSubmitterIssueSubmissionCount(),
        EcosystemExperienceSubmitterIssueCommentCount(),
        # SubmitterEcosystemExperienceIssueDiscussionParticipationCount(),
    ]
    return eco_exp_pr_sw_features, eco_exp_issue_sw_features


ECO_EXP_PR_SW_FEATURES, ECO_EXP_ISSUE_SW_FEATURES = build_eco_experience()
