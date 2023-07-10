

import itertools

from collections import deque
import datetime as dt
from typing import Any, Tuple, Callable, Iterator
import networkx as nx

import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import SlidingWindowFeature, Feature
from python_proj.utils.util import better_get_nested_many, resolve_callables_in_list


class SNAFeature(SlidingWindowFeature):
    def __init__(self, graph: nx.DiGraph,
                 nested_source_keys: list[str | Callable[[dict], str]],
                 nested_target_keys: list[str | Callable[[dict], str]]) -> None:
        super().__init__()

        self._graph = graph
        self.__nested_source_keys = nested_source_keys
        self.__nested_target_keys = nested_target_keys

        self.edge_label = self.__class__.__name__

    def _add_nodes(self, nodes: int | list[int]):
        if isinstance(nodes, int):
            nodes = [nodes]
        for node in nodes:
            if not self._graph.has_node(node):
                self._graph.add_node(node)

    def _add_remove_edge(self,
                         source_node: int, target_node: int,
                         edge_timestamp: float,
                         add_entry: bool):
        """Adds a single edge, ignoring self-loops."""
        if source_node == target_node:
            return

        # Grabs all edge data.
        edge_data = self._graph.get_edge_data(
            source_node, target_node, default={})

        # Adds queue if not existing yet.
        if self.edge_label not in edge_data:
            edge_data[self.edge_label] = deque()

        edge_timestamps: deque = edge_data[self.edge_label]
        if add_entry:
            edge_timestamps.append(edge_timestamp)
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

    def _add_remove_edges(self,
                          sources: int | list[int],
                          targets: int | list[int],
                          edge_timestamp: float,
                          add_entries: bool):
        """Adds multiple edges, pairwise."""
        if isinstance(sources, int):
            sources = [sources]
        if isinstance(targets, int):
            targets = [targets]
        self._add_nodes(itertools.chain(sources, targets))
        for source in sources:
            for target in targets:
                self._add_remove_edge(source, target,
                                      edge_timestamp, add_entries)

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
        edge_timestamp: dt.datetime = entry['__dt_closed_at']
        self._add_remove_edges(sources, targets,
                               edge_timestamp.timestamp(), True)

    def remove_entry(self, entry: dict):
        sources, targets = self._get_us_and_vs(entry)
        edge_timestamp: dt.datetime = entry['__dt_closed_at']
        self._add_remove_edges(sources, targets,
                               edge_timestamp.timestamp(), False)

    def is_output_feature(self) -> bool:
        return False

    def get_feature(self, entry: dict) -> None:
        return


class PRIntegratorToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         [exp_utils.get_integrator_key, 'id'],
                         ['user_data', 'id'])


class PRCommenterToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'user_data', 'id'],
                         ['user_data', 'id'])

    def add_entry(self, entry: dict):
        if entry['comments'] == 0:
            return
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry['comments'] == 0:
            return
        super().remove_entry(entry)


class PRCommenterToCommenter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'user_data', 'id'],
                         ['comments_data', 'user_data', 'id'])

    def add_entry(self, entry: dict):
        if entry['comments'] == 0:
            return
        super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry['comments'] == 0:
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

    def get_time_respecting_degree(
        self,
        edges: Iterator[Tuple[int, int]],
        edge_type: str,
        end_timestamp: float
    ) -> int:
        """
        Calculates the time-respecting degree; i.e., the number of edges
        that occurred prior to the ``end_time`` (exclusive).
        """

        degree = 0
        # Iterates through all edges.
        for (source, target) in edges:
            edge_data = self._graph.get_edge_data(source, target, default={})

            # The type not being in there is equivalent to the edge not existing.
            if edge_type not in edge_data:
                continue

            timestamped_edges: deque[float] = edge_data[edge_type]
            for timestamped_edge in timestamped_edges:
                # If the timestamp is after, it happened in the future.
                # It's an >= instead of a > as the current even shouldn't
                # accidentally be included either.
                if timestamped_edge >= end_timestamp:
                    # It breaks as all entries in the edge list are
                    # chronological, so the following will be after as well.
                    break
                degree += 1
        return degree


class HITSCentrality(SNACentralityFeature):
    def get_feature(self, entry: dict) -> str:
        submitter_id = entry['user_data']['id']
        if not self._graph.has_node(submitter_id):
            return 0.0, 0.0

        hubs, authorities = nx.hits(self._graph)
        return hubs[submitter_id], authorities[submitter_id]

    def get_name(self) -> str:
        base_name = super().get_name()
        hub_name = base_name + ".hub"
        auth_name = base_name + ".auth"
        return hub_name, auth_name


class PageRankCentrality(SNACentralityFeature):
    def get_feature(self, entry: dict) -> str:
        submitter_id = entry['user_data']['id']
        if not self._graph.has_node(submitter_id):
            return 0.0

        pagreank = nx.pagerank(self._graph)
        return pagreank[submitter_id]


class FirstOrderDegreeCentrality(SNACentralityFeature):
    """
    Calculates the first-order degree centrality of a given connecting + experience edge.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        connecting_edge_type: SNAFeature,
        experience_edge_type: SNAFeature,
        count_in_degree: bool
    ) -> None:
        super().__init__(graph)

        # Sets the labels interested in.
        self.__connecting_edge_type = connecting_edge_type.edge_label
        self.__experience_edge_type = experience_edge_type.edge_label

        # Sets the used function to collect the correct experience degree.
        # i.e., in-degree or out-degree.
        self.__count_in_degree = count_in_degree
        self.__get_exp_edge_data = self._graph.in_edges if count_in_degree \
            else self._graph.out_edges

    def get_feature(self, entry: dict) -> int:
        submitter_id = entry['user_data']['id']

        total_degree = 0
        # Iterates through all incoming edges of the focal node.
        in_edges = self._graph.in_edges(nbunch=[submitter_id])

        # The target id is ignored as that's the ``submitter_id``.
        for (neighbour_id, _) in in_edges:
            edge_data = self._graph.get_edge_data(
                neighbour_id, submitter_id, default={})
            # If the connecting edge type is not in there it means the
            # edge does not exist.
            if self.__connecting_edge_type not in edge_data:
                continue

            # fo = first-order

            # Gets the incoming/outgoing edges of the neighbor node.
            fo_edges = self.__get_exp_edge_data(nbunch=[neighbour_id])

            # Removes all edges that connect with the focal node.
            fo_edges = [(source, target) for (source, target) in fo_edges
                        if source != submitter_id and target != submitter_id]

            # Iterates through all time stamped edges as it considers
            # each of these separately.
            timestamped_edges: deque[float] = edge_data[self.__connecting_edge_type]
            for edge_timestamp in timestamped_edges:

                # Calculates the time-respecting degree and updates the total.
                degree = self.get_time_respecting_degree(
                    edges=fo_edges,
                    edge_type=self.__experience_edge_type,
                    end_timestamp=edge_timestamp
                )
                total_degree += degree

        return total_degree

    def get_name(self) -> str:
        original_name = super().get_name()
        is_in = "In" if self.__count_in_degree else "Out"
        return f'{original_name}({self.__connecting_edge_type}.{self.__experience_edge_type}-{is_in})'


class WeightedFirstOrderDegreeCentrality(SNACentralityFeature):
    """Calculates the weighted first-order degree centrality."""

    # TODO: Implement this.
    def __init__(
        self, graph: nx.DiGraph,
            edges: list[type],
            weights: list[int],
            count_in_degree: bool
    ) -> None:
        super().__init__(graph)

    def get_feature(self, entry: dict) -> Any:
        raise NotImplementedError()


def build_centrality_features():
    """Factory method for centrality features."""

    graph = nx.DiGraph()

    pr_graph = [
        PRIntegratorToSubmitter(graph),
        PRCommenterToSubmitter(graph),
        PRCommenterToCommenter(graph)
    ]

    issue_graph = [
        IssueCommenterToCommenter(graph),
        IssueCommenterToSubmitter(graph)
    ]

    global_centrality_measures = [
        PageRankCentrality(graph),
        HITSCentrality(graph)
    ]

    edges = list(itertools.chain(pr_graph, issue_graph))
    local_centrality_measures = []
    for connecting_edge_type in edges:
        for experience_edge_type in edges:
            for count_in_degree in [True, False]:
                local_centrality_measures.append(
                    FirstOrderDegreeCentrality(graph, connecting_edge_type, experience_edge_type, count_in_degree))

    # local_centrality_measures.extend([
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), True),
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), False)
    # ])

    return pr_graph, issue_graph, global_centrality_measures, local_centrality_measures
