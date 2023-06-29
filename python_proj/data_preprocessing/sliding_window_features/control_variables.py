from datetime import datetime

from python_proj.data_preprocessing.sliding_window_features.base import *
from python_proj.utils.exp_utils import get_integrator_key, get_owner_and_repo_from_source_path
from python_proj.utils.util import safe_contains_key, has_keys, SafeDict


class ControlIntegratedBySameUser(Feature):
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


class ControlPullRequestLifeTimeInMinutes(Feature):
    """The lifetime of the pull request in minutes."""

    TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def get_feature(self, entry: dict) -> float:
        created_at = datetime.strptime(entry['created_at'], self.TS_FORMAT)
        closed_at = datetime.strptime(entry['closed_at'], self.TS_FORMAT)
        deltatime = closed_at - created_at
        lifetime_in_minutes = deltatime.total_seconds() / 60
        return lifetime_in_minutes

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["created_at", "closed_at"]) \
            and self.get_feature(entry) > 0


class ControlIntraProjectPullRequestExperienceOfIntegrator(SlidingWindowFeature):
    """Experience of the integrated measured in pull requests
    they handled inside the project (i.e., intra-project)."""

    def __init__(self) -> None:
        self.__projects_to_integrator_experience: SafeDict[str, SafeDict[int, int]] = \
            SafeDict(default_value=SafeDict,
                     default_value_constructor_kwargs={'default_value': 0})

    def handle(self, entry: dict, sign: int):
        project = entry["__source_path"]
        integrator_key = get_integrator_key(entry)
        self.__projects_to_integrator_experience[project][integrator_key] += sign

    def add_entry(self, entry: dict):
        self.handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> int:
        project = entry["__source_path"]
        integrator_key = get_integrator_key(entry)
        return self.__projects_to_integrator_experience[project][integrator_key]

    def is_valid_entry(self, entry: dict) -> bool:
        integrator_key = get_integrator_key(entry)
        return has_keys(entry, [integrator_key, "__source_path"])


class ControlPullRequestHasComments(Feature):
    """Whether the pull request has comments."""

    def get_feature(self, entry: dict) -> bool:
        return entry["comments"] > 0

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["comments"])


class ControlNumberOfCommitsInPullRequest(Feature):
    """The number of commmits in the pull request."""

    def get_feature(self, entry: dict) -> int:
        return entry['commits']

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["commits"])


class ControlPullRequestHasCommentByExternalUser(Feature):
    """
    Whether the pull request has a comment form someone who is 
    not the integrator, the submitter or a project contributor.
    """

    def __init__(self) -> None:
        self._contributors_per_project = SafeDict(default_value=set)

    def __add_submitter(self, entry: dict):
        if not entry['merged']:
            return
        submitter_id = entry["user_data"]["id"]
        (owner, repo) = get_owner_and_repo_from_source_path(
            entry["__source_path"])
        project = f'{owner}/{repo}'
        self._contributors_per_project[project].add(submitter_id)

    def __has_external_comment(self, entry: dict) -> bool:
        if entry["comments"] == 0:
            return False

        submitter_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        integrator_id = entry[integrator_key]["id"]
        (owner, repo) = get_owner_and_repo_from_source_path(
            entry["__source_path"])
        project = f'{owner}/{repo}'
        project_contributors = self._contributors_per_project[project]

        for comment in entry["comments_data"]:
            commenter_id = comment["user_data"]["id"]
            if (commenter_id != submitter_id
                    and commenter_id != integrator_id
                    and commenter_id not in project_contributors):
                return True

        return False

    def get_feature(self, entry: dict) -> bool:
        has_external_comment = self.__has_external_comment(entry)
        self.__add_submitter(entry)
        return has_external_comment

    def is_valid_entry(self, entry: dict) -> bool:
        integrator_key = get_integrator_key(entry)
        has_main_keys = has_keys(
            entry, ["comments", "user_data", integrator_key,
                    "__source_path", 'merged'])
        if not has_main_keys:
            return False
        if entry['comments'] > 0:
            if not has_keys(entry, ["comments_data"]):
                return False
        has_sub_keys = has_keys(entry[integrator_key], ["id"])
        return has_sub_keys


class ControlHasHashTagInDescription(Feature):
    """Whether the title or the body contain a #; i.e., a reference to an issue."""

    def get_feature(self, entry: dict) -> bool:
        return safe_contains_key(entry["title"], key="#") \
            or ("body" in entry  # some PRs don't have a body.
                and safe_contains_key(entry["body"], key="#"))

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ["title"])


CONTROL_PR_SW_FEATURES: list[SlidingWindowFeature] = [
    # prior_review_num
    ControlIntraProjectPullRequestExperienceOfIntegrator()
]

CONTROL_PR_FEATURES: list[Feature] = [
    ControlIntegratedBySameUser(),                 # same_user
    ControlPullRequestLifeTimeInMinutes(),         # lifetime_minutes
    ControlPullRequestHasComments(),               # has_comments
    ControlNumberOfCommitsInPullRequest(),         # num_commits
    ControlPullRequestHasCommentByExternalUser(),  # other_comment
    ControlHasHashTagInDescription()               # hash_tag
]
