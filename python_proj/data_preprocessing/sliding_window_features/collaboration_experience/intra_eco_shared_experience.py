"""
Extends SharedExperience to distinguish between
intra-project and ecosystem-wide experience.
"""

from typing import Callable
from itertools import product

from wmeijer_utils.collections.safe_dict import SafeDict
from wmeijer_utils.collections.dict_access import better_get_nested_many
from wmeijer_utils.collections.list_access import resolve_callables_in_list

from python_proj.utils.exp_utils import (
    get_repository_name_from_source_path,
    SOURCE_PATH_KEY,
    get_integrator_key,
)
from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.shared_experience import (
    SharedExperienceFeature,
)


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

    def _get_nodes(
        self, entry: dict, nested_key: list[str | Callable[[dict], str]]
    ) -> list[int]:
        """Gets all nodes related to the nested key."""
        resolved_nested_key = resolve_callables_in_list(nested_key, entry)
        nodes = better_get_nested_many(entry, list(resolved_nested_key))
        return nodes

    def _handle(self, entry: dict, sign: int) -> None:
        """Adds new edges."""
        source_ids = self._get_nodes(entry, self._nested_source_keys)
        target_ids = self._get_nodes(entry, self._nested_target_keys)
        repo_name = get_repository_name_from_source_path(entry[SOURCE_PATH_KEY])
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
        repo_name = get_repository_name_from_source_path(entry[SOURCE_PATH_KEY])
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
        repo_name = get_repository_name_from_source_path(entry[SOURCE_PATH_KEY])
        shared_exp: SafeDict = self._shared_experience[source_id][target_id]
        eco_exp = sum(value for key, value in shared_exp.items() if key != repo_name)
        return eco_exp
