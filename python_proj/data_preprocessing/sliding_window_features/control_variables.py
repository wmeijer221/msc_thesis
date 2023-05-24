from datetime import datetime
from typing import Any

from python_proj.data_preprocessing.sliding_window_features.base import *


class IntegratedBySameUser(Feature):
    """Whether the PR is integrated by the same person."""

    def get_feature(self, entry: dict) -> bool:
        submitter = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        integrator = entry[integrator_key]["id"]
        same_user = submitter == integrator
        return same_user


class PullRequestLifeTimeInMinutes(Feature):
    """The lifetime of the pull request in minutes."""

    def get_feature(self, entry: dict) -> float:
        ts_format = "%Y-%m-%dT%H:%M:%SZ"
        created_at = datetime.strptime(entry['created_at'], ts_format)
        closed_at = datetime.strptime(entry['closed_at'], ts_format)
        deltatime = closed_at - created_at
        lifetime_in_minutes = deltatime.total_seconds() / 60
        return lifetime_in_minutes


class IntraProjectPullRequestExperienceOfIntegrator(SlidingWindowFeature):
    """Experience of the integrated measured in pull requests
    they handled inside the project (i.e., intra-project)."""

    __projects_to_integrator_experience: dict[str, dict[int, int]] = {}

    def handle(self, entry: dict, sign: int):
        project = entry["__source_path"]
        # handle missing key.
        if project not in self.__projects_to_integrator_experience:
            self.__projects_to_integrator_experience[project] = {}

        integrator_key = get_integrator_key(entry)
        # handle missing key.
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


class PullRequestHasComments(Feature):
    """Whether the pull request has comments."""

    def get_feature(self, entry: dict) -> bool:
        return entry["comments"] > 0


class NumberOfCommitsInPullRequest(Feature):
    """The number of commmits in the pull request."""

    def get_feature(self, entry: dict) -> int:
        return entry['commits']


class IntraProjectPullRequestSuccessRateSubmitter(SlidingWindowFeature):
    """The success rate of the submitter of the pull request at 
    an intra-project level. This measure is used as a proxy for "core member"
    as these two variables correlate (Zhang, 2022) and this feature is
    easier to calculate."""

    __projects_to_integrator_experience: dict[str,
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
            self.__projects_to_integrator_experience[project][submitter].merged -= sign

    def add_entry(self, entry: dict):
        self.handle(entry, sign=1)

    def remove_entry(self, entry: dict):
        self.handle(entry, sign=-1)

    def get_feature(self, entry: dict) -> float:
        project = entry["__source_path"]
        submitter = entry["user_data"]["id"]

        try:
            dev_success_rate = self.__projects_to_integrator_experience[project][submitter]
            return dev_success_rate.success_rate()
        except KeyError:
            return 0


class PullRequestHasCommentByExternalUser(Feature):
    """Whether the pull request has a comment form someone who is 
    not the reviewer/integrator or the submitter."""

    def get_feature(self, entry: dict) -> bool:
        if entry["comments"] == 0:
            return False
        submitter = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        integrator = entry[integrator_key]["id"]
        for comment in entry["comments_data"]:
            commenter = comment["user_data"]["id"]
            if commenter != submitter and commenter != integrator:
                return True
        return False


class CIPipelineExists(Feature):
    def get_feature(self, entry: dict) -> Any:
        raise NotImplementedError()
        return super().get_feature(entry)


class HasHashTagInDescription(Feature):
    """Whether the title or the body contain a #; i.e., a reference to an issue."""

    def get_feature(self, entry: dict) -> bool:
        return entry["title"].index("#") > -1\
            or entry["body"].index("#") > -1


all_control_varialbes = [IntegratedBySameUser(),
                     PullRequestLifeTimeInMinutes(),
                     IntraProjectPullRequestExperienceOfIntegrator(),
                     PullRequestHasComments(),
                     NumberOfCommitsInPullRequest(),
                     IntraProjectPullRequestSuccessRateSubmitter(),
                     PullRequestHasCommentByExternalUser(),
                     #  CIPipelineExists(), # TODO: THIS
                     HasHashTagInDescription()]
