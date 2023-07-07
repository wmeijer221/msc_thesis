from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature, PullRequestSuccess
from python_proj.utils.util import SafeDict, has_keys


class IntraProjectSubmitterPullRequestSubmissionCount(SlidingWindowFeature):
    """Intra PR submitted."""

    def __init__(self) -> None:
        self.pr_counts_per_user_per_project = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={'default_value': 0}
        )

    def __handle(self, entry: dict, sign: int):
        submitter_id = entry["user_data"]["id"]
        project = entry["__source_path"]
        self.pr_counts_per_user_per_project[submitter_id][project] += sign

    def add_entry(self, entry: dict):
        self.__handle(entry, 1)

    def remove_entry(self, entry: dict):
        self.__handle(entry, -1)

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data', "__source_path"])

    def get_feature(self, entry: dict) -> Any:
        submitter_id = entry["user_data"]["id"]
        project = entry["__source_path"]
        return self.pr_counts_per_user_per_project[submitter_id][project]


class IntraProjectSubmitterPullRequestSuccessRate(SlidingWindowFeature):
    """
    The success rate of the submitter of the pull request at 
    an intra-project level. This measure is used as a proxy for "core member"
    as these two variables correlate (Zhang, 2022) and this feature is
    easier to calculate.

    # requester_succ_rate; core_member proxy
    ControlIntraProjectPullRequestSuccessRateSubmitter()
    """

    def __init__(self) -> None:
        self.__projects_to_integrator_experience: SafeDict[str, SafeDict[int, PullRequestSuccess]] \
            = SafeDict(default_value=SafeDict,
                       default_value_constructor_kwargs={"default_value": PullRequestSuccess})

    def handle(self, entry: dict, sign: int):
        project = entry["__source_path"]
        submitter_id = entry["user_data"]["id"]
        if entry["merged"]:
            self.__projects_to_integrator_experience[project][submitter_id].merged += sign
        else:
            self.__projects_to_integrator_experience[project][submitter_id].unmerged += sign

    def add_entry(self, entry: dict):
        self.handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> float:
        project = entry["__source_path"]
        submitter = entry["user_data"]["id"]
        dev_success_rate = self.__projects_to_integrator_experience[project][submitter]
        return dev_success_rate.get_success_rate()

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["__source_path", "user_data", "merged"])


class IntraProjectSubmitterPullRequestCommentCount(SlidingWindowFeature):
    """The number of comments made no pull requests at an intra-project level."""

    def __init__(self) -> None:
        self.comment_counts_per_user_per_project = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={'default_value': 0}
        )

    def __handle(self, entry: dict, sign: int):
        if entry['comments'] == 0:
            return
        project = entry['__source_path']
        for comment in entry['comments_data']:
            commenter_id = comment['user_data']["id"]
            self.comment_counts_per_user_per_project[commenter_id][project] += sign

    def add_entry(self, entry: dict):
        self.__handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.__handle(entry, sign=-1)

    def is_valid_entry(self, entry: dict) -> bool:
        has_basics = has_keys(entry, ['comments'])
        if has_basics:
            if entry['comments'] > 0:
                return has_keys(entry, ['comments_data'])
        return False

    def get_feature(self, entry: dict) -> Any:
        submitter_id = entry['user_data']["id"]
        project = entry["__source_path"]
        return self.comment_counts_per_user_per_project[submitter_id][project]


class IntraProjectSubmitterIssueSubmissionCount(IntraProjectSubmitterPullRequestSubmissionCount):
    """Has the exact same implementation as parent class. just implemented for a different name."""


class IntraProjectSubmitterIssueCommentCount(IntraProjectSubmitterPullRequestCommentCount):
    """Has the exact same implementation as parent class. just implemented for a different name."""


def build_intra_project_features():
    """Factory method."""
    ip_issue_sw_features = [
        IntraProjectSubmitterIssueSubmissionCount(),
        IntraProjectSubmitterIssueCommentCount()
    ]
    ip_pr_sw_features = [
        IntraProjectSubmitterPullRequestSubmissionCount(),
        IntraProjectSubmitterPullRequestSuccessRate(),
        IntraProjectSubmitterPullRequestCommentCount()
    ]
    return ip_issue_sw_features, ip_pr_sw_features
