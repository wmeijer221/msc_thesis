"""
Extends SharedExperience to distinguish between
intra-project and ecosystem-wide experience.
"""

from typing import List, Tuple
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
        for source_id, target_id in product(source_ids, target_ids):
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


# if __name__ == "__main__":
#     from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.concrete_implementations.intra_shared_experience import (
#         build_features as intra_build_features,
#     )
#     from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.concrete_implementations.eco_shared_experience import (
#         build_features as eco_build_features,
#     )

#     def build_features() -> (
#         Tuple[List[SharedExperienceFeature], List[SharedExperienceFeature]]
#     ):
#         ipr, iiss = intra_build_features()
#         epr, eiss = eco_build_features()
#         pr_features = [*ipr, *epr]
#         iss_features = [*iiss, *eiss]
#         return pr_features, iss_features

#     __se_pr_sw_features, __se_issue_sw_features = build_features()

#     test_entry = {
#         "user_data": {"id": 1235},
#         "merged_by_data": {"id": 4949},
#         "closed_by": {"id": 4949},
#         "comments": 2,
#         "comments_data": [
#             {"user_data": {"id": 1235}},
#             {"user_data": {"id": 4949}},
#             {"user_data": {"id": 2582}},
#         ],
#         "merged": True,
#         SOURCE_PATH_KEY: "./asdf/owner--repo-name.json",
#     }

#     import itertools

#     for f in itertools.chain(__se_pr_sw_features, __se_issue_sw_features):
#         q: SharedExperienceFeature = f
#         q.add_entry(test_entry)
#         print(f"{q.get_name()}: {q.get_feature(test_entry)}")
