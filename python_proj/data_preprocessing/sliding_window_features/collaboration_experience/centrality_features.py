"""
Implements global centrality features for the collaboration network.
It counts both intra-project and ecosystem-wide experience.
"""

from warnings import warn

import itertools
from itertools import product

from collections import deque
import datetime as dt
from typing import Any, Dict, Tuple, Callable, Iterator
import networkx as nx

import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import (
    SlidingWindowFeature,
    Feature,
)
from python_proj.utils.util import (
    better_get_nested_many,
    resolve_callables_in_list,
    stepped_enumerate,
)


class SNAFeature(SlidingWindowFeature):
    def __init__(
        self,
        graph: nx.DiGraph,
        nested_source_keys: list[str | Callable[[dict], str]],
        nested_target_keys: list[str | Callable[[dict], str]],
    ) -> None:
        super().__init__()

        self._graph = graph
        self.__nested_source_keys = nested_source_keys
        self.__nested_target_keys = nested_target_keys

        self.edge_label = self.__class__.__name__

        # Bookkeeping variable.
        self.total_edge_count = 0

    def _add_nodes(self, nodes: int | list[int]):
        if isinstance(nodes, int):
            nodes = [nodes]
        for node in nodes:
            if not self._graph.has_node(node):
                self._graph.add_node(node)

    def _add_remove_edge(
        self, source_node: int, target_node: int, edge_timestamp: float, add_entry: bool
    ):
        """Adds a single edge, ignoring self-loops."""
        if source_node == target_node:
            return

        # Grabs all edge data.
        edge_data = self._graph.get_edge_data(source_node, target_node, default={})

        # Adds queue if not existing yet.
        if self.edge_label not in edge_data:
            edge_data[self.edge_label] = deque()

        edge_timestamps: deque = edge_data[self.edge_label]
        if add_entry:
            edge_timestamps.append(edge_timestamp)
            self.total_edge_count += 1
        else:
            if len(edge_timestamps) == 1:
                # Deletes it to preserve some memory.
                del edge_data[self.edge_label]
            else:
                # Entries are always removed chronologically,
                # So if something has to be popped, it's always
                # the right one.
                edge_timestamps.popleft()

        if len(edge_data) > 0:
            # Updates edge.
            self._graph.add_edge(source_node, target_node, **edge_data)
        else:
            # removes edge when it's dead to preserve some memory.
            self._graph.remove_edge(source_node, target_node)

        # Removes singular nodes to preserve some memory.
        if nx.is_isolate(self._graph, source_node):
            self._graph.remove_node(source_node)
        if nx.is_isolate(self._graph, target_node):
            self._graph.remove_node(target_node)

    def _add_remove_edges(
        self,
        sources: int | list[int],
        targets: int | list[int],
        edge_timestamp: float,
        add_entries: bool,
    ):
        """Adds multiple edges, pairwise."""
        if isinstance(sources, int):
            sources = [sources]
        if isinstance(targets, int):
            targets = [targets]
        self._add_nodes(itertools.chain(sources, targets))
        for source, target in product(sources, targets):
            self._add_remove_edge(source, target, edge_timestamp, add_entries)

    def _get_us_and_vs(self, entry: dict) -> Tuple[list[int], list[int]]:
        def __get_nodes(nested_key: list[str | Callable[[dict], str]]) -> list[int]:
            # It resolves the callables in the nested key and gets related nodes.
            real_nested_key = resolve_callables_in_list(nested_key, entry)
            new_nodes = better_get_nested_many(entry, list(real_nested_key))
            return new_nodes

        sources = __get_nodes(self.__nested_source_keys)
        targets = __get_nodes(self.__nested_target_keys)

        return sources, targets

    def add_entry(self, entry: dict):
        sources, targets = self._get_us_and_vs(entry)
        edge_timestamp: dt.datetime = entry["__dt_closed_at"]
        self._add_remove_edges(sources, targets, edge_timestamp.timestamp(), True)

    def remove_entry(self, entry: dict):
        sources, targets = self._get_us_and_vs(entry)
        edge_timestamp: dt.datetime = entry["__dt_closed_at"]
        self._add_remove_edges(sources, targets, edge_timestamp.timestamp(), False)

    def is_output_feature(self) -> bool:
        return False

    def get_feature(self, entry: dict) -> None:
        return


class PRIntegratorToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(
            graph, [exp_utils.get_integrator_key, "id"], ["user_data", "id"]
        )


class PRCommenterToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(
            graph, ["comments_data", "user_data", "id"], ["user_data", "id"]
        )

    def add_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry["comments"] == 0:
            return
        super().remove_entry(entry)


class PRCommenterToCommenter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(
            graph,
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


class IssueCommenterToSubmitter(PRCommenterToSubmitter):
    """Only here for the name."""


class IssueCommenterToCommenter(PRCommenterToCommenter):
    """Only here for the name."""


class SNACentralityFeature(Feature):
    """
    Base class for centrality features.
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph

    def get_feature(self, entry: dict) -> Any:
        raise NotImplementedError()


class FirstOrderDegreeCentralityV2(SNACentralityFeature):
    """
    Improves on the original first-order degree centrality by calculating
    everything in one go instead of separately, by iterating through the
    existing data rather than the interesting data which might or might not
    be there, and by not iterating through the data multiple times.
    It's a little more unintuitive, but about 3 to 4 times quicker.
    """

    def __init__(
        self, graph: nx.DiGraph, edge_types: list[SNAFeature], count_in_degree: bool
    ) -> None:
        super().__init__(graph)

        # Determines whether the in- or out-degree is used.
        self._count_in_degree = count_in_degree
        self._get_exp_edge_data = (
            self._graph.in_edges if count_in_degree else self._graph.out_edges
        )

        # Creates an enumerated dict to track edge types.
        # The index is used to generate the output vector.
        self._edges: dict[str, int] = {
            edge.get_name(): i for i, edge in enumerate(edge_types)
        }

    def get_name(self) -> Iterator[str]:
        base_name = super().get_name()
        in_out = "In" if self._count_in_degree else "Out"
        for connecting_edge in self._edges.keys():
            for experience_edge in self._edges.keys():
                yield f"{base_name}({connecting_edge}.{experience_edge}-{in_out})"

    def is_ignored_connecting_edge(
        self, source_id: int, target_id: int, timestamp: float, edge_type: str
    ) -> bool:
        """Returns true if the edge should be ignored."""
        # HACK: This is only here to get the intra vs. ecosystem experience subclasses to work.
        return False

    def get_feature(self, entry: dict) -> list[int]:
        submitter_id = entry["user_data"]["id"]

        # Allocates the output vector.
        total_degree = [0] * (len(self._edges) ** 2)

        # Iterates through all incoming edges.
        in_edges = self._graph.in_edges(nbunch=[submitter_id])
        for neighbour_id, _ in in_edges:
            edge_data = self._graph.get_edge_data(
                neighbour_id, submitter_id, default={}
            )

            # Iterates through all of the edge types with the current neighbor.
            for connecting_edge_type, timestamped_connecting_edges in edge_data.items():

                # HACK: This is only here to get the intra vs. ecosystem experience subclasses to work.
                # If the connecting edge type is ignored, it's not considered.
                timestamped_connecting_edges = [
                    timestamp
                    for timestamp in timestamped_connecting_edges
                    if not self.is_ignored_connecting_edge(
                        neighbour_id, submitter_id, timestamp, connecting_edge_type
                    )
                ]

                # If the key is not tracked, it is skipped.
                if connecting_edge_type not in self._edges:
                    continue
                connecting_edge_index = (
                    len(self._edges) * self._edges[connecting_edge_type]
                )
                timestamped_edge_count = len(timestamped_connecting_edges)

                # Creates first-order (fo) edge iterator in which
                # submitter is not involved.
                fo_edges = self._get_exp_edge_data(neighbour_id)
                fo_edges = [
                    (fo_source, fo_target)
                    for (fo_source, fo_target) in fo_edges
                    if fo_source != submitter_id and fo_target != submitter_id
                ]

                # Iterates through all first-order edges.
                for fo_source, fo_target in fo_edges:
                    fo_edge_data = self._graph.get_edge_data(
                        fo_source, fo_target, default={}
                    )

                    for (
                        experience_edge_type,
                        timestamped_experience_edges,
                    ) in fo_edge_data.items():
                        # If it's not tracked, it's skipped.
                        if experience_edge_type not in self._edges:
                            continue
                        experience_edge_index = self._edges[experience_edge_type]

                        # Iterates through all connecting edges to sum the degree.
                        # As the edges are stored chronologically, only one iteration
                        # needs to be done as, if the experience edge was counted for the first,
                        # it will be, by definition, counted for the rest as well, so it's just
                        # multiplied by the number of relevant edges intead.
                        degree = 0
                        for (
                            remaining_connected_edge_count,
                            connecting_edge_timestamp,
                        ) in stepped_enumerate(
                            timestamped_connecting_edges,
                            start=timestamped_edge_count,
                            step=-1,
                        ):
                            for (
                                experience_edge_timestamp
                            ) in timestamped_experience_edges:
                                if (
                                    experience_edge_timestamp
                                    >= connecting_edge_timestamp
                                ):
                                    break

                                # Adds the weight.
                                degree += remaining_connected_edge_count

                        # Sets the output.
                        output_index = connecting_edge_index + experience_edge_index
                        total_degree[output_index] = degree

        return total_degree


def build_centrality_features():
    """Factory method for centrality features."""

    warn("This is deprecated", DeprecationWarning, stacklevel=2)

    # TODO: replace this with a ``MultiDiGraph``
    graph = nx.DiGraph()

    pr_graph = [
        PRIntegratorToSubmitter(graph),
        PRCommenterToSubmitter(graph),
        PRCommenterToCommenter(graph),
    ]

    issue_graph = [IssueCommenterToCommenter(graph), IssueCommenterToSubmitter(graph)]

    global_centrality_measures = []

    local_centrality_measures = [
        FirstOrderDegreeCentralityV2(
            graph, itertools.chain(pr_graph, issue_graph), count_in_degree=True
        ),
        FirstOrderDegreeCentralityV2(
            graph, itertools.chain(pr_graph, issue_graph), count_in_degree=False
        ),
    ]

    # local_centrality_measures.extend([
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), True),
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), False)
    # ])

    return pr_graph, issue_graph, global_centrality_measures, local_centrality_measures


def get_total_count_from_features(features: list[SNAFeature]) -> Dict[str, int]:
    return {feature.get_name(): feature.total_edge_count for feature in features}
