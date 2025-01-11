"""
This is the successor candidate for `intra_eco_shared_experience`.
"""


from typing import List, Tuple, Callable
from numbers import Number

from itertools import product
from wmutils.collections.safe_dict import SafeDict
from wmutils.collections.dict_access import better_get_nested_many
from wmutils.collections.list_access import resolve_callables_in_list


from python_proj.utils.exp_utils import (
    get_repository_name_from_source_path,
    SOURCE_PATH_KEY,
    get_integrator_key,
)

from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.shared_experience import (
    SharedExperienceFeature,
)

from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.no_bots.norm_so_degree_centrality import get_bot_ids


class IntraProjectSharedExperienceFeature(SharedExperienceFeature):
    """
    Tracks shared experience at an intra-project level.
    """

    def __init__(
        self,
        nested_source_keys: list[str | Callable[[dict], str]],
        nested_target_keys: list[str | Callable[[dict], str]],
        is_inversed: bool = False,
    ) -> None:
        super().__init__(nested_source_keys, nested_target_keys, is_inversed)
        self.__banned_nodes = set()
        self._shared_experience = SafeDict(
            default_value=SafeDict,
            default_value_constructor_kwargs={
                "default_value": SafeDict,
                "default_value_constructor_kwargs": {
                    "default_value": 0,
                    "delete_when_default": True,
                },
            },
        )

    def set_banned_nodes(self, banned_nodes: list):
        assert not banned_nodes is None
        self.__banned_nodes = set(banned_nodes)

    def _get_nodes(
        self, entry: dict, nested_key: list[str | Callable[[dict], str]]
    ) -> list[int]:
        """Gets all nodes related to the nested key."""
        resolved_nested_key = resolve_callables_in_list(nested_key, entry)
        nodes = better_get_nested_many(entry, list(resolved_nested_key))
        nodes = [node for node in nodes if node not in self.__banned_nodes]
        return nodes

    def _handle(self, entry: dict, sign: int) -> None:
        """Adds new edges."""
        source_ids = self._get_nodes(entry, self._nested_source_keys)
        target_ids = self._get_nodes(entry, self._nested_target_keys)
        repo_name = get_repository_name_from_source_path(
            entry[SOURCE_PATH_KEY])
        # Creates pairs of nodes between nodes if they are not equal.
        pairs = product(source_ids, target_ids)
        pairs = (
            (source_id, target_id)
            for source_id, target_id in pairs
            if source_id != target_id
        )
        for source_id, target_id in pairs:
            self._shared_experience[source_id][target_id][repo_name] += sign

    def get_feature(self, entry: dict) -> int:
        source_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        target_id = entry[integrator_key]["id"]
        repo_name = get_repository_name_from_source_path(
            entry[SOURCE_PATH_KEY])
        intra_exp = self._shared_experience[source_id][target_id][repo_name]
        return intra_exp


class EcosystemSharedExperienceFeature(IntraProjectSharedExperienceFeature):
    """
    Calculates shared experience at an ecosystem level,
    excluding intra-project experience.
    """

    def get_feature(self, entry: dict) -> int:
        source_id = entry["user_data"]["id"]
        integrator_key = get_integrator_key(entry)
        target_id = entry[integrator_key]["id"]
        repo_name = get_repository_name_from_source_path(
            entry[SOURCE_PATH_KEY])
        shared_exp: SafeDict = self._shared_experience[source_id][target_id]
        eco_exp = sum(value for key, value in shared_exp.items()
                      if key != repo_name)
        return eco_exp


# Pull request


class EcosystemSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(
    EcosystemSharedExperienceFeature
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by U and integrated by V.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(["user_data", "id"], [
            get_integrator_key, "id"], is_inversed)


class EcosystemSharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(
    EcosystemSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by V and integrated by U (i.e., the inverse role-distribution).
    """

    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class EcosystemSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(
    EcosystemSharedExperienceFeature
):
    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["user_data", "id"], ["comments_data", "user_data", "id"], is_inversed
        )

    def _handle(self, entry: dict, sign: Number):
        if entry["comments"] > 0:
            super()._handle(entry, sign)


class EcosystemSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(
    EcosystemSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class EcosystemSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(
    EcosystemSharedExperienceFeature
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


class EcosystemSharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(
    EcosystemSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class EcosystemSharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(
    EcosystemSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class EcosystemSharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(
    EcosystemSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


def build_eco_se_features() -> (
    Tuple[
        List[EcosystemSharedExperienceFeature], List[EcosystemSharedExperienceFeature]
    ]
):
    """Factory method for ecosystem shared experience features"""
    pr_features = [
        EcosystemSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(),
        EcosystemSharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(),
        EcosystemSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(),
        EcosystemSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(),
        EcosystemSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(),
    ]
    iss_features = [
        EcosystemSharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(),
        EcosystemSharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(),
        EcosystemSharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(),
    ]

    all_features: list[EcosystemSharedExperienceFeature] = [
        *pr_features, *iss_features]
    bot_ids = get_bot_ids()
    for feature in all_features:
        feature.set_banned_nodes(bot_ids)

    return pr_features, iss_features
