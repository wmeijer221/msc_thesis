"""
Implements SNA metrics that respect multithreading.
"""

import itertools
from typing import Any, Tuple, Callable

import datetime
import networkx as nx

from python_proj.data_preprocessing.sliding_window_features.base \
    import SlidingWindowFeature
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import get_nested_many, SafeDict


TIMESTAMP_KEY = "edge_timestamps"


class SNAFeature(SlidingWindowFeature):
    """
    Base class for social network analysis features, minimizing redundant 
    code. Implementing classes only need to override the source_keys lists 
    and the edge label to work. In the context of these classes, when 
    retrieving the feature's value, ``u`` is always the pull request submitter
    and ``v`` the pull request integrator.
    """

    def __init__(self, graph: nx.DiGraph,
                 edge_count_per_type: dict[str, int],
                 total_edge_count_per_type: dict[str, int],
                 nested_source_keys: list[str | Callable[[dict], str]],
                 nested_target_keys: list[str | Callable[[dict], str]]) -> None:
        self.graph = graph
        self.edge_count_per_type = edge_count_per_type
        self.total_edge_count_per_type = total_edge_count_per_type

        self._edge_label: str = self.__class__.__name__
        self._nested_source_keys: list[list[str |
                                            Callable[[dict], str]]] = nested_source_keys
        self._nested_target_keys: list[list[str |
                                            Callable[[dict], str]]] = nested_target_keys
        self._inversed: bool = False

        # "Register" local instance to edge counter.
        if self._edge_label not in self.edge_count_per_type:
            self.edge_count_per_type[self._edge_label] = 0
            self.total_edge_count_per_type[self._edge_label] = 0

    def _add_nodes(self, nodes: int | list[int]):
        if isinstance(nodes, int):
            nodes = [nodes]
        for node in nodes:
            if not self.graph.has_node(node):
                self.graph.add_node(node)

    def _add_remove_edge(self,
                         u: int, v: int,
                         activity_id: int,
                         activity_timestamp: datetime,
                         sign: int):
        """Adds a single edge, ignoring self-loops."""
        if u == v:
            return

        # TODO: This stuff with the counter and the timestamp sets can be merged.

        # Increments counter.
        edge_data = self.graph.get_edge_data(u, v, default={})
        if self._edge_label in edge_data:
            edge_data[self._edge_label] += sign
        else:
            edge_data[self._edge_label] = sign

        # Adds timestamped edge.
        # TODO: This will not work at an "all time data" scale.
        if TIMESTAMP_KEY not in edge_data:
            edge_data[TIMESTAMP_KEY] = SafeDict(default_value=dict)
        if sign > 0:
            edge_data[TIMESTAMP_KEY][self._edge_label][activity_id] = activity_timestamp
        else:
            del edge_data[TIMESTAMP_KEY][self._edge_label][activity_id]

        # Updates edge.
        self.graph.add_edge(u, v, **edge_data)
        self.edge_count_per_type[self._edge_label] += sign
        if sign > 0:
            self.total_edge_count_per_type[self._edge_label] += sign
        self._recalculate_weight(u, v)

    def _add_remove_edges(self,
                          us: int | list[int],
                          vs: int | list[int],
                          activity_id: int,
                          activity_timestamp: datetime,
                          sign: int):
        """Adds multiple edges, pairwise."""
        if isinstance(us, int):
            us = [us]
        if isinstance(vs, int):
            vs = [vs]
        self._add_nodes(itertools.chain(us, vs))
        for u in us:
            for v in vs:
                self._add_remove_edge(
                    u, v,
                    activity_id, activity_timestamp,
                    sign)

    def _recalculate_weight(self, u: int, v: int):
        # TODO: enable this again if this turns out to be relevant.
        # Right now it's just unnecessary commputation.
        return

        edge_data = self.graph.get_edge_data(u, v, default={})
        weight = 0.0
        for key, value in self.edge_count_per_type.items():
            if key in edge_data:
                weight += edge_data[key] / (1 + value)
        edge_data['weight'] = weight
        self.graph.add_edge(u, v, **edge_data)

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

        us = __get_nodes(self._nested_source_keys)
        vs = __get_nodes(self._nested_target_keys)

        if self._inversed:
            us, vs = vs, us

        return us, vs

    def add_entry(self, entry: dict):
        us, vs = self._get_us_and_vs(entry)
        activity_id = entry['id']
        timestamp = datetime.datetime.strptime(
            entry['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
        self._add_remove_edges(us, vs,
                               activity_id, timestamp,
                               sign=1)

    def remove_entry(self, entry: dict):
        us, vs = self._get_us_and_vs(entry)
        activity_id = entry['id']
        timestamp = datetime.datetime.strptime(
            entry['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
        self._add_remove_edges(us, vs,
                               activity_id, timestamp,
                               sign=-1)

    def get_feature(self, entry: dict, ordered: bool = False) -> Any:
        submitter_id = entry['user_data']['id']
        integrator_key = get_integrator_key(entry)
        integrator_id = entry[integrator_key]['id']
        if ordered and integrator_id < submitter_id:
            edge_data = self.graph.get_edge_data(
                integrator_id, submitter_id, default={})
        else:
            edge_data = self.graph.get_edge_data(
                submitter_id, integrator_id, default={})
        degree = edge_data[self._edge_label] \
            if self._edge_label in edge_data \
            else 0
        return degree


class PRIntegratorToPRSubmitter(SNAFeature):
    """Directed edge from integrator to submitter."""

    def __init__(
        self,
            graph: nx.DiGraph,
            edge_count_per_type: dict[str, int],
            total_edge_count_per_type: dict[str, int]
    ) -> None:

        super().__init__(
            graph,
            edge_count_per_type,
            total_edge_count_per_type,
            ["user_data", "id"],
            [get_integrator_key, "id"]
        )


class PRCommenterToPRSubmitter(SNAFeature):
    """Directed edge from commenter to PR submitter."""

    def __init__(
        self,
            graph: nx.DiGraph,
            edge_count_per_type: dict[str, int],
            total_edge_count_per_type: dict[str, int]
    ) -> None:

        super().__init__(
            graph,
            edge_count_per_type,
            total_edge_count_per_type,
            ["comments_data", "id"],
            ['user_data', "id"]
        )


class PRCommenterToPRCommenter(SNAFeature):
    """Directed edge from commenter to PR submitter."""

    def __init__(
        self,
            graph: nx.DiGraph,
            edge_count_per_type: dict[str, int],
            total_edge_count_per_type: dict[str, int]
    ) -> None:

        super().__init__(
            graph,
            edge_count_per_type,
            total_edge_count_per_type,
            ["comments_data", "id"],
            ['comments_data', "id"]
        )


class ISCommenterToISSubmitter(PRCommenterToPRSubmitter):
    """Just here for the name."""


class ISCommenterToISCommenter(PRCommenterToPRCommenter):
    """Just here for the name."""


def build_sna_features():
    """Factory method to builds all features."""

    graph = nx.DiGraph()
    edge_count_per_type = {}
    total_edge_count_per_type = {}

    issue_features = [
        ISCommenterToISSubmitter(graph, edge_count_per_type,
                                 total_edge_count_per_type),
        ISCommenterToISCommenter(graph, edge_count_per_type,
                                 total_edge_count_per_type)
    ]

    pr_features = [
        PRIntegratorToPRSubmitter(graph, edge_count_per_type,
                                  total_edge_count_per_type),
        PRCommenterToPRSubmitter(graph, edge_count_per_type,
                                 total_edge_count_per_type),
        PRCommenterToPRCommenter(graph, edge_count_per_type,
                                 total_edge_count_per_type)
    ]

    return issue_features, pr_features
