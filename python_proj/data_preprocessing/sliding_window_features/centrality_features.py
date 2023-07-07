

import itertools

from typing import Tuple, Callable
import networkx as nx

import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import SlidingWindowFeature
from python_proj.utils.util import get_nested_many


class SNAFeature(SlidingWindowFeature):
    def __init__(self, graph: nx.DiGraph,
                 nested_source_keys: list[str | Callable[[dict], str]],
                 nested_target_keys: list[str | Callable[[dict], str]]) -> None:
        super().__init__()

        self._graph = graph
        self.__nested_source_keys = nested_source_keys
        self.__nested_target_keys = nested_target_keys

        self.__edge_label = self.__class__.__name__

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
        if self.__edge_label in edge_data:
            edge_data[self.__edge_label] += sign
        else:
            edge_data[self.__edge_label] = sign

        if edge_data[self.__edge_label] == 0:
            del edge_data[self.__edge_label]

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


class HITSCentrality(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph, None, None)

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


class PageRankCentrality(SNAFeature):
    def __init__(self, graph: nx.DiGraph) -> None:
        super().__init__(graph, None, None)

    def get_feature(self, entry: dict) -> str:
        submitter_id = entry['user_data']['id']
        if not self._graph.has_node(submitter_id):
            return 0.0

        pagreank = nx.pagerank(self._graph)
        return pagreank[submitter_id]


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

    centrality_measures = [
        PageRankCentrality(graph),
        HITSCentrality(graph)
    ]

    return pr_graph, issue_graph, centrality_measures
