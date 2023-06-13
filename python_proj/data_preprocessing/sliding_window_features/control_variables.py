from datetime import datetime
from typing import Any

from python_proj.data_preprocessing.sliding_window_features.base import *
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import safe_contains_key, has_keys


class IsMerged(Feature):
    """
    Whether the PR is merged. 
    Not a control variable, but I had to put it somewhere.
    """

    def get_feature(self, entry: dict) -> bool:
        return entry["merged"]

    def is_valid_entry(self, entry: dict) -> bool:
        return "merged" in entry


class IntegratedBySameUser(Feature):
    """Whether the PR is integrated by the same person."""

    def get_feature(self, entry: dict) -> bool:
        submitter_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        integrator_id = entry[integrator_key]["id"]
        same_user = submitter_id == integrator_id
        return same_user

    def is_valid_entry(self, entry: dict) -> bool:
        integrator_key = get_integrator_key(entry)
        has_main_keys = has_keys(entry, [integrator_key, "user_data"])
        if not has_main_keys:
            return False
        has_sub_keys = has_keys(entry[integrator_key], ['id'])
        return has_sub_keys


class PullRequestLifeTimeInMinutes(Feature):
    """The lifetime of the pull request in minutes."""

    TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def get_feature(self, entry: dict) -> float:
        created_at = datetime.strptime(entry['created_at'], self.TS_FORMAT)
        closed_at = datetime.strptime(entry['closed_at'], self.TS_FORMAT)
        deltatime = closed_at - created_at
        lifetime_in_minutes = deltatime.total_seconds() / 60
        return lifetime_in_minutes

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["created_at", "closed_at"])


class IntraProjectPullRequestExperienceOfIntegrator(SlidingWindowFeature):
    """Experience of the integrated measured in pull requests
    they handled inside the project (i.e., intra-project)."""

    def __init__(self) -> None:
        self.__projects_to_integrator_experience: dict[str, dict[int, int]] = {
        }

    def handle(self, entry: dict, sign: int):
        project = entry["__source_path"]
        # handle missing key.
        if project not in self.__projects_to_integrator_experience:
            self.__projects_to_integrator_experience[project] = {}

        # handle missing key.
        integrator_key = get_integrator_key(entry)
        if integrator_key not in self.__projects_to_integrator_experience[project]:
            self.__projects_to_integrator_experience[project][integrator_key] = 0

        self.__projects_to_integrator_experience[project][integrator_key] += sign

    def add_entry(self, entry: dict):
        self.handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> int:
        project = entry["__source_path"]
        integrator_key = get_integrator_key(entry)
        try:
            return self.__projects_to_integrator_experience[project][integrator_key]
        except KeyError:
            return 0

    def is_valid_entry(self, entry: dict) -> bool:
        integrator_key = get_integrator_key(entry)
        return has_keys(entry, [integrator_key, "__source_path"])


class PullRequestHasComments(Feature):
    """Whether the pull request has comments."""

    def get_feature(self, entry: dict) -> bool:
        return entry["comments"] > 0

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["comments"])


class NumberOfCommitsInPullRequest(Feature):
    """The number of commmits in the pull request."""

    def get_feature(self, entry: dict) -> int:
        return entry['commits']

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["commits"])


class IntraProjectPullRequestSuccessRateSubmitter(SlidingWindowFeature):
    """The success rate of the submitter of the pull request at 
    an intra-project level. This measure is used as a proxy for "core member"
    as these two variables correlate (Zhang, 2022) and this feature is
    easier to calculate."""

    def __init__(self) -> None:
        self.__projects_to_integrator_experience: dict[str,
                                                       dict[int, PullRequestSuccess]] = {}

    def handle(self, entry: dict, sign: int):
        project = entry["__source_path"]

        if project not in self.__projects_to_integrator_experience:
            self.__projects_to_integrator_experience[project] = {}

        submitter = entry["user_data"]["id"]
        if submitter not in self.__projects_to_integrator_experience[project]:
            self.__projects_to_integrator_experience[project][submitter] = PullRequestSuccess(
            )

        if entry["merged"]:
            self.__projects_to_integrator_experience[project][submitter].merged += sign
        else:
            # Yes future me, this should be a ``+= sign`` as we count
            # the number of unmerged PRs the sign will be +/- based on whether we remove the entry.
            # The only way this could be ``-=`` is if we would aggregate merged and unmerged entries
            # somehow, which we don't.
            self.__projects_to_integrator_experience[project][submitter].unmerged += sign

    def add_entry(self, entry: dict):
        self.handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> float:
        project = entry["__source_path"]
        submitter = entry["user_data"]["id"]

        try:
            dev_success_rate = self.__projects_to_integrator_experience[project][submitter]
            return dev_success_rate.get_success_rate()
        except KeyError:
            return 0

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["__source_path", "user_data", "merged"])


class PullRequestHasCommentByExternalUser(Feature):
    """
    Whether the pull request has a comment form someone who is 
    not the reviewer/integrator or the submitter.
    """

    def get_feature(self, entry: dict) -> bool:
        if entry["comments"] == 0:
            return False
        submitter_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        integrator_id = entry[integrator_key]["id"]
        for comment in entry["comments_data"]:
            commenter_id = comment["user_data"]["id"]
            if commenter_id != submitter_id \
                    and commenter_id != integrator_id:
                return True
        return False

    def is_valid_entry(self, entry: dict) -> bool:
        integrator_key = get_integrator_key(entry)
        has_main_keys = has_keys(
            entry, ["comments", "user_data", integrator_key])
        if not has_main_keys:
            return False
        if entry['comments'] > 0:
            if not has_keys(entry, ["comments_data"]):
                return False
        has_sub_keys = has_keys(entry[integrator_key], ["id"])
        return has_sub_keys


class HasHashTagInDescription(Feature):
    """Whether the title or the body contain a #; i.e., a reference to an issue."""

    def get_feature(self, entry: dict) -> bool:
        return safe_contains_key(entry["title"], "#") \
            or ("body" in entry  # some PRs don't have a body.
                and safe_contains_key(entry["body"], "#"))

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["title"])


CONTROL_PR_SW_FEATURES: list[SlidingWindowFeature] = [
    # prior_review_num
    IntraProjectPullRequestExperienceOfIntegrator(),
    # requester_succ_rate; core_member proxy
    IntraProjectPullRequestSuccessRateSubmitter()
]

CONTROL_PR_FEATURES: list[Feature] = [
    IsMerged(),
    IntegratedBySameUser(),                 # same_user
    PullRequestLifeTimeInMinutes(),         # lifetime_minutes
    PullRequestHasComments(),               # has_comments
    NumberOfCommitsInPullRequest(),         # num_commits
    PullRequestHasCommentByExternalUser(),  # other_comment
    HasHashTagInDescription()               # hash_tag
]

ALL_FEATURES: list[Feature] = [
    *CONTROL_PR_SW_FEATURES,
    *CONTROL_PR_FEATURES
]
