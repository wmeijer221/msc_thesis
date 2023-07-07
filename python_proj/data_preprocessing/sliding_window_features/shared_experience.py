
from numbers import Number
from typing import Any, Tuple, Callable

from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import get_nested_many, SafeDict


class SharedExperienceFeature(SlidingWindowFeature):
    def __init__(self,
                 nested_source_keys: list[str | Callable[[dict], str]],
                 nested_target_keys: list[str | Callable[[dict], str]],
                 is_inversed: bool = False) -> None:
        super().__init__()

        if is_inversed:
            self.__nested_target_keys = nested_source_keys
            self.__nested_source_keys = nested_target_keys
        else:
            self.__nested_source_keys = nested_source_keys
            self.__nested_target_keys = nested_target_keys

        self.__shared_experiences = SafeDict(default_value=SafeDict,
                                             default_value_constructor_kwargs={
                                                 'default_value': 0,
                                                 "delete_when_default": True
                                             },
                                             delete_when_default=True)

    def _get_us_and_vs(self, entry: dict) -> Tuple[list[int], list[int]]:
        def __get_nodes(nested_key: list[str | Callable[[dict], str]]) -> list[int]:
            # It resolves the callables in the nested key.
            r_nested_key = []
            for key in nested_key:
                if isinstance(key, Callable):
                    key = key(entry)
                r_nested_key.append(key)
            # Gets all nodes.
            new_nodes = get_nested_many(entry, r_nested_key)
            if new_nodes is None:
                return []
            elif not isinstance(new_nodes, list):
                new_nodes = [new_nodes]
            return new_nodes

        source_ids = __get_nodes(self.__nested_source_keys)
        target_ids = __get_nodes(self.__nested_target_keys)

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
        source_id = entry['user_data']['id']
        integrator_key = get_integrator_key(entry)
        target_id = entry[integrator_key]['id']
        return self.__shared_experiences[source_id][target_id]

# Pull request


class SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(SharedExperienceFeature):
    """
    Shared experience feature accounting for pull requests that have been 
    submitted by U and integrated by V.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["user_data", "id"],
            [get_integrator_key, "id"],
            is_inversed
        )


class SharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator):
    """
    Shared experience feature accounting for pull requests that have been 
    submitted by V and integrated by U.
    """

    def __init__(self) -> None:
        super().__init__(True)


class SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(SharedExperienceFeature):
    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["user_data", "id"],
            ["comments_data", "id"],
            is_inversed
        )

    def add_entry(self, entry: dict):
        if entry['comments'] > 0:
            super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry['comments'] > 0:
            super().remove_entry(entry)


class SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator):
    def __init__(self) -> None:
        super().__init__(True)


class SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(SharedExperienceFeature):
    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["comments_data", "id"],
            ["comments_data", "id"],
            is_inversed
        )

# Issues


class SharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator):
    """
    Is functionally exactly the same as the parent class. 
    This class is implemented just to give the feature a unique name.
    """


class SharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter):
    """
    Is functionally exactly the same as the parent class. 
    This class is implemented just to give the feature a unique name.
    """


class SharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter):
    """
    Is functionally exactly the same as the parent class. 
    This class is implemented just to give the feature a unique name.
    """


def build_se_features():
    """Factory method to builds all features."""

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
