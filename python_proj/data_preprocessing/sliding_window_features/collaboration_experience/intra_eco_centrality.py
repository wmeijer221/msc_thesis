"""
Implements Second-order degree centrality for the collaboration networs. This is 
done two-fold: 1) only considering intra-project connecting edges, and 2) only
considering ecosystem connectin edges.

All of these classes are tightly coupled with the old centrality features,
overriding only the behaviors necessary to make the additional checks.
"""

from typing import Callable, Tuple, List
from networkx import DiGraph

from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.centrality_features import (
    SNAFeature,
    SNACentralityFeature,
    FirstOrderDegreeCentralityV2,
)

from python_proj.utils.exp_utils import (
    get_integrator_key,
    SOURCE_PATH_KEY,
    get_repository_name_from_source_path,
)


class SNAFeatureV2(SNAFeature):
    """
    Implements new SNA feature that keeps track of projects in
    which development activities are performed.
    """

    def __init__(
        self,
        graph: DiGraph,
        edge_to_project_mapping: dict,
        nested_source_keys: list[str | Callable[[dict], str]],
        nested_target_keys: list[str | Callable[[dict], str]],
    ) -> None:
        super().__init__(graph, nested_source_keys, nested_target_keys)
        self._edge_to_project_mapping: dict = edge_to_project_mapping
        # HACK: It assumes the right entry is set before the `_add_remove_edge` is called, which will break down when inherited incorrectly.
        self._current_entry: None | dict = None

    def _build_edge_key(
        self, source_node: int, target_node: int, timestamp: float
    ) -> int:
        return _build_edge_key(source_node, target_node, timestamp, self.edge_label)

    def _add_remove_edge(
        self, source_node: int, target_node: int, edge_timestamp: float, add_entry: bool
    ):
        super()._add_remove_edge(source_node, target_node, edge_timestamp, add_entry)
        edge_key = self._build_edge_key(source_node, target_node, edge_timestamp)
        repo_name = get_repository_name_from_source_path(
            self._current_entry[SOURCE_PATH_KEY]
        )
        if add_entry:
            self._edge_to_project_mapping[edge_key] = repo_name
        elif edge_key in self._edge_to_project_mapping:
            del self._edge_to_project_mapping[edge_key]

    def add_entry(self, entry: dict):
        self._current_entry = entry
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        self._current_entry = entry
        super().remove_entry(entry)


class PRIntegratorToSubmitterV2(SNAFeatureV2):
    def __init__(self, graph: DiGraph, edge_to_project_mapping: dict) -> None:
        super().__init__(
            graph,
            edge_to_project_mapping,
            [get_integrator_key, "id"],
            ["user_data", "id"],
        )


class PRCommenterToSubmitterV2(SNAFeatureV2):
    def __init__(self, graph: DiGraph, edge_to_project_mapping: dict) -> None:
        super().__init__(
            graph,
            edge_to_project_mapping,
            ["comments_data", "user_data", "id"],
            ["user_data", "id"],
        )

    def add_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().remove_entry(entry)


class PRCommenterToCommenterV2(SNAFeatureV2):
    def __init__(self, graph: DiGraph, edge_to_project_mapping: dict) -> None:
        super().__init__(
            graph,
            edge_to_project_mapping,
            ["comments_data", "user_data", "id"],
            ["comments_data", "user_data", "id"],
        )

    def add_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().remove_entry(entry)


class IssueCommenterToSubmitterV2(PRCommenterToSubmitterV2):
    """Only here for the name."""


class IssueCommenterToCommenterV2(PRCommenterToCommenterV2):
    """Only here for the name."""


class IntraProjectSecondOrderInDegreeCentrality(FirstOrderDegreeCentralityV2):
    """
    Second-order degree centrality feature,
    only considering intra-project connecting edges.
    """

    def __init__(
        self,
        graph: DiGraph,
        edge_to_project_mapping: dict,
        edge_types: List[SNAFeature],
        count_in_degree: bool = True,
    ) -> None:
        super().__init__(graph, edge_types, count_in_degree)
        self._edge_to_project_mapping = edge_to_project_mapping
        # HACK: Same problem as in `SNAFeatureV2`.
        self._current_entry: None | dict = None

    def is_ignored_connecting_edge(
        self,
        source_id: int,
        target_id: int,
        timestamp: float,
        edge_type: str,
    ) -> bool:
        current_repo = get_repository_name_from_source_path(
            self._current_entry[SOURCE_PATH_KEY]
        )
        edge_key = _build_edge_key(source_id, target_id, timestamp, edge_type)
        edge_repo = self._edge_to_project_mapping[edge_key]
        return current_repo != edge_repo

    def get_feature(self, entry: dict) -> List[int]:
        self._current_entry = entry
        return super().get_feature(entry)


class IntraProjectSecondOrderOutDegreeCentrality(
    IntraProjectSecondOrderInDegreeCentrality
):
    """Here for the name."""

    def __init__(
        self,
        graph: DiGraph,
        edge_to_project_mapping: dict,
        edge_types: List[SNAFeature],
        count_in_degree: bool = False,
    ) -> None:
        super().__init__(graph, edge_to_project_mapping, edge_types, count_in_degree)


class EcosystemSecondOrderInDegreeCentrality(IntraProjectSecondOrderInDegreeCentrality):
    """
    Second-order degree centrality feature,
    only considering ecosystem connecting edges.
    """

    def is_ignored_connecting_edge(
        self,
        source_id: int,
        target_id: int,
        timestamp: float,
        edge_type: str,
    ) -> bool:
        # Inverts the result from the intra-project filter, as anything that's
        # not intra-project must be in the rest of the ecosystem.
        return not super().is_ignored_connecting_edge(
            source_id, target_id, timestamp, edge_type
        )


class EcosystemSecondOrderOutDegreeCentrality(EcosystemSecondOrderInDegreeCentrality):
    """Here for the name"""

    def __init__(
        self,
        graph: DiGraph,
        edge_to_project_mapping: dict,
        edge_types: List[SNAFeature],
        count_in_degree: bool = False,
    ) -> None:
        super().__init__(graph, edge_to_project_mapping, edge_types, count_in_degree)


def _build_edge_key(
    source_node: int, target_node: int, timestamp: float, edge_type: str
) -> int:
    """Builds a key based on the given variables."""
    key = f"{source_node}:{target_node}:{timestamp}:{edge_type}"
    return hash(key)


def build_intra_eco_centrality_features() -> (
    Tuple[List[SNAFeature], List[SNAFeature], List[SNACentralityFeature]]
):
    """Factory methods for the centrality features V2."""

    edge_to_project_mapping = dict()
    graph = DiGraph()

    pr_graph = [
        PRIntegratorToSubmitterV2(graph, edge_to_project_mapping),
        PRCommenterToSubmitterV2(graph, edge_to_project_mapping),
        PRCommenterToCommenterV2(graph, edge_to_project_mapping),
    ]

    issue_graph = [
        IssueCommenterToCommenterV2(graph, edge_to_project_mapping),
        IssueCommenterToSubmitterV2(graph, edge_to_project_mapping),
    ]

    activity_graphs = [*pr_graph, *issue_graph]

    centr_features = [
        IntraProjectSecondOrderInDegreeCentrality(
            graph, edge_to_project_mapping, activity_graphs
        ),
        IntraProjectSecondOrderOutDegreeCentrality(
            graph, edge_to_project_mapping, activity_graphs
        ),
        EcosystemSecondOrderInDegreeCentrality(
            graph, edge_to_project_mapping, activity_graphs
        ),
        EcosystemSecondOrderOutDegreeCentrality(
            graph, edge_to_project_mapping, activity_graphs
        ),
    ]

    return pr_graph, issue_graph, centr_features
