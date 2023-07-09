

import itertools

from typing import Any, Tuple, Callable
import networkx as nx

import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import SlidingWindowFeature, Feature
from python_proj.utils.util import get_nested_many


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
                         u: int, v: int,
                         sign: int):
        """Adds a single edge, ignoring self-loops."""
        if u == v:
            return

        # Increments counter.
        edge_data = self._graph.get_edge_data(u, v, default={})
        if self.edge_label in edge_data:
            edge_data[self.edge_label] += sign
        else:
            edge_data[self.edge_label] = sign

        if edge_data[self.edge_label] == 0:
            del edge_data[self.edge_label]

        if len(edge_data) > 0:
            # Updates edge.
            self._graph.add_edge(u, v, **edge_data)
        else:
            # removes edge when it's dead.
            self._graph.remove_edge(u, v)

        # Removes singular nodes.
        if nx.is_isolate(self._graph, u):
            self._graph.remove_node(u)
        if nx.is_isolate(self._graph, v):
            self._graph.remove_node(v)

    def _add_remove_edges(self,
                          sources: int | list[int],
                          targets: int | list[int],
                          sign: int):
        """Adds multiple edges, pairwise."""
        if isinstance(sources, int):
            sources = [sources]
        if isinstance(targets, int):
            targets = [targets]
        self._add_nodes(itertools.chain(sources, targets))
        for source in sources:
            for target in targets:
                self._add_remove_edge(source, target, sign)

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

        sources = __get_nodes(self.__nested_source_keys)
        targets = __get_nodes(self.__nested_target_keys)

        return sources, targets

    def add_entry(self, entry: dict):
        sources, targets = self._get_us_and_vs(entry)
        self._add_remove_edges(sources, targets, sign=1)

    def remove_entry(self, entry: dict):
        sources, targets = self._get_us_and_vs(entry)
        self._add_remove_edges(sources, targets, sign=-1)

    def is_output_feature(self) -> bool:
        return False


class PRIntegratorToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         [exp_utils.get_integrator_key, 'id'],
                         ['user_data', 'id'])


class PRCommenterToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'id'],
                         ['user_data', 'id'])


class PRCommenterToCommenter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'id'],
                         ['comments_data', 'id'])


class IssueCommenterToSubmitter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'id'],
                         ['user_data', 'id'])


class IssueCommenterToCommenter(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph,
                         ['comments_data', 'id'],
                         ['comments_data', 'id'])


class SNACentralityFeature(Feature):
    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph


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

    def __init__(self, graph: nx.DiGraph,
                 connecting_edge_type: SNAFeature,
                 experience_edge_type: SNAFeature,
                 count_in_degree: bool) -> None:
        super().__init__(graph)
        self.__connecting_edge_type = connecting_edge_type.edge_label
        self.__experience_edge_type = experience_edge_type.edge_label
        # Sets the used function to collect the correct experience degree.
        # i.e., in-degree or out-degree.
        self.__get_exp_edge_data = self._graph.in_edges if count_in_degree else self._graph.out_edges

    def get_feature(self, entry: dict) -> Any:
        submitter_id = entry['user_data']['id']

        # Gets the relevant incoming edges.
        connected_neighbors = []
        for (neighbor_id, _) in self._graph.in_edges(nbunch=[submitter_id]):
            edge_data = self._graph.get_edge_data(neighbor_id, submitter_id)
            if edge_data is None or self.__connecting_edge_type not in edge_data:
                continue
            connected_neighbors.append(neighbor_id)

        # Counts first-order degree.
        degree = 0
        for (source, target) in self.__get_exp_edge_data(nbunch=connected_neighbors):
            edge_data = self._graph.get_edge_data(source, target)
            if edge_data is None or self.__experience_edge_type not in edge_data:
                continue
            degree += edge_data[self.__experience_edge_type]

        return degree

    def get_name(self) -> str:
        original_name = super().get_name()
        return f'{original_name}({self.__connecting_edge_type}.{self.__experience_edge_type})'


class WeightedFirstOrderDegreeCentrality(SNACentralityFeature):
    def __init__(
        self, graph: nx.DiGraph,
            edges: list[type],
            weights: list[int],
            count_in_degree: bool
    ) -> None:
        super().__init__(graph)


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

    edges = itertools.chain(pr_graph, issue_graph)
    local_centrality_measures = [FirstOrderDegreeCentrality(graph, t1, t2, is_in)
                                 for t1 in edges for t2 in edges for is_in in [True, False]]
    # local_centrality_measures.extend([
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), True),
    #     WeightedFirstOrderDegreeCentrality(
    #         graph, edges, [1] * len(edges), False)
    # ])

    return pr_graph, issue_graph, global_centrality_measures, local_centrality_measures
