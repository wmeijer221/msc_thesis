"""
Implements shared experience features.
It counts both intra-project and ecosystem-wide experience.
"""

from warnings import warn

from numbers import Number
from typing import Any, Tuple, Callable

from wmutils.collections.safe_dict import SafeDict

from python_proj.data_preprocessing.sliding_window_features.base import (
    SlidingWindowFeature,
)
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import better_get_nested_many, resolve_callables_in_list


class SharedExperienceFeature(SlidingWindowFeature):
    """
    Base class for shared experience.
    It takes source keys, and target keys and adds an entry for
    connection it can find in a data entry. It ignored self-loops.
    """

    def __init__(
        self,
        nested_source_keys: list[str | Callable[[dict], str]],
        nested_target_keys: list[str | Callable[[dict], str]],
        is_inversed: bool = False,
    ) -> None:
        super().__init__()

        if is_inversed:
            self._nested_source_keys = nested_target_keys
            self._nested_target_keys = nested_source_keys
        else:
            self._nested_source_keys = nested_source_keys
            self._nested_target_keys = nested_target_keys

        self.__shared_experiences = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={
                "default_value": 0,
                "delete_when_default": True,
            },
            delete_when_default=True,
        )

    def _get_us_and_vs(self, entry: dict) -> Tuple[list[int], list[int]]:
        """Generates two lists of source and target keys related to this class."""

        def __get_nodes(nested_key: list[str | Callable[[dict], str]]) -> list[int]:
            """Gets all nodes related to the nested key."""
            resolved_nested_key = resolve_callables_in_list(nested_key, entry)
            nodes = better_get_nested_many(entry, list(resolved_nested_key))
            return nodes

        source_ids = __get_nodes(self._nested_source_keys)
        target_ids = __get_nodes(self._nested_target_keys)

        return source_ids, target_ids

    def _handle(self, entry: dict, sign: Number):
        source_ids, target_ids = self._get_us_and_vs(entry)

        for source_id in source_ids:
            for target_id in target_ids:
                if source_id == target_id:
                    continue
                self.__shared_experiences[source_id][target_id] += sign

    def add_entry(self, entry: dict):
        self._handle(entry, 1)

    def remove_entry(self, entry: dict):
        self._handle(entry, -1)

    def get_feature(self, entry: dict) -> Any:
        source_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        target_id = entry[integrator_key]["id"]
        return self.__shared_experiences[source_id][target_id]


# Pull request


class SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(
    SharedExperienceFeature
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by U and integrated by V.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(["user_data", "id"], [get_integrator_key, "id"], is_inversed)


class SharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(
    SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by V and integrated by U (i.e., the inverse role-distribution).
    """

    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(
    SharedExperienceFeature
):
    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["user_data", "id"], ["comments_data", "user_data", "id"], is_inversed
        )

    def _handle(self, entry: dict, sign: Number):
        if entry["comments"] > 0:
            super()._handle(entry, sign)


class SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(
    SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(
    SharedExperienceFeature
):
    """
    Counts the number of times the submitter and integrator have both participated in a pull request discussion.
    This does not need an inverse, as the implementation of the parent class creates edges for every permutation
    of commenters; i.e., (u, v) and (v, u) are both added here.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["comments_data", "user_data", "id"],
            ["comments_data", "user_data", "id"],
            is_inversed,
        )

    def _handle(self, entry: dict, sign: Number):
        if entry["comments"] > 0:
            super()._handle(entry, sign)


# Issues


class SharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(
    SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class SharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(
    SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class SharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(
    SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


def build_se_features():
    """Factory method to builds all features."""

    warn("This is deprecated", DeprecationWarning, stacklevel=2)

    se_pr_sw_features = [
        SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(),
        SharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(),
        SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(),
        SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(),
        SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(),
    ]
    se_issue_sw_features = [
        SharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(),
        SharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(),
        SharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(),
    ]

    return se_pr_sw_features, se_issue_sw_features
