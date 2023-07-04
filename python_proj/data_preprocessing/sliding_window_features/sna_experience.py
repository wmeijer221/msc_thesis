import datetime
import itertools
import networkx as nx
from typing import Any, Tuple, Callable

from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature, Feature, PostRunFeature
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import has_keys, get_nested_many, SafeDict


G: nx.DiGraph = None

# Edges are removed when a sliding window is used.
EDGE_COUNT_PER_TYPE: dict = None
# Edges aren't removed when a sliding window is used.
TOTAL_EDGE_COUNT_PER_TYPE: dict = None


TIMESTAMP_KEY = "edge_timestamps"


class SNAFeature(SlidingWindowFeature):
    """
    Base class for social network analysis features, minimizing redundant 
    code. Implementing classes only need to override the source_keys lists 
    and the edge label to work. In the context of these classes, when 
    retrieving the feature's value, ``u`` is always the pull request submitter
    and ``v`` the pull request integrator.
    """

    def __init__(self) -> None:
        global G, EDGE_COUNT_PER_TYPE, TOTAL_EDGE_COUNT_PER_TYPE
        # Dreate singleton graph.
        if G is None:
            G = nx.DiGraph()

        # Dreate singleton edge counter.
        if EDGE_COUNT_PER_TYPE is None:
            EDGE_COUNT_PER_TYPE = {}
            TOTAL_EDGE_COUNT_PER_TYPE = {}

        self._edge_label: str = self.__class__.__name__
        self._nested_source_keys: list[list[str | Callable[[dict], str]]] = []
        self._nested_target_keys: list[list[str | Callable[[dict], str]]] = []
        self._inversed: bool = False

        # "Register" local instance to edge counter.
        if self._edge_label not in EDGE_COUNT_PER_TYPE:
            EDGE_COUNT_PER_TYPE[self._edge_label] = 0
            TOTAL_EDGE_COUNT_PER_TYPE[self._edge_label] = 0

    def _add_nodes(self, nodes: int | list[int]):
        if isinstance(nodes, int):
            nodes = [nodes]
        for node in nodes:
            if not G.has_node(node):
                G.add_node(node)

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
        edge_data = G.get_edge_data(u, v, default={})
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
        G.add_edge(u, v, **edge_data)
        EDGE_COUNT_PER_TYPE[self._edge_label] += sign
        if sign > 0:
            TOTAL_EDGE_COUNT_PER_TYPE[self._edge_label] += sign
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

        edge_data = G.get_edge_data(u, v, default={})
        weight = 0.0
        for key, value in EDGE_COUNT_PER_TYPE.items():
            if key in edge_data:
                weight += edge_data[key] / (1 + value)
        edge_data['weight'] = weight
        G.add_edge(u, v, **edge_data)

    def _get_us_and_vs(self, entry: dict) -> Tuple[list[int], list[int]]:
        def __get_nodes(nested_keys: list[list[str | Callable[[dict], str]]]) -> list[int]:
            # TODO: This is set up assuming there are multiple nested keys,
            # however, none of the predictors use this, so it could be removed.
            # NOTE: reates one edge per activity.
            nodes = set()
            for nested_key in nested_keys:
                # It resolves the callables in the nested key.
                r_nested_key = []
                for key in nested_key:
                    if isinstance(key, Callable):
                        key = key(entry)
                    r_nested_key.append(key)
                # Gets all nodes.
                new_nodes = get_nested_many(entry, r_nested_key)
                if new_nodes is None:
                    continue
                elif isinstance(new_nodes, list):
                    nodes.update(new_nodes)
                else:
                    nodes.add(new_nodes)
            return list(nodes)

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
            edge_data = G.get_edge_data(
                integrator_id, submitter_id, default={})
        else:
            edge_data = G.get_edge_data(
                submitter_id, integrator_id, default={})
        degree = edge_data[self._edge_label] \
            if self._edge_label in edge_data \
            else 0
        return degree


# Pull request


class SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(SNAFeature):
    """
    Shared experience feature accounting for pull requests that have been 
    submitted by U and integrated by V.
    """

    def __init__(self) -> None:
        super().__init__()
        self._nested_source_keys = [["user_data", "id"]]
        self._nested_target_keys = [[get_integrator_key, "id"]]

    def is_valid_entry(self, entry: dict) -> bool:
        if has_keys(entry, ['user_data']):
            integrator_key = get_integrator_key(entry)
            return has_keys(entry, [integrator_key])
        return False


class SharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator):
    """
    Shared experience feature accounting for pull requests that have been 
    submitted by V and integrated by U.
    """

    def __init__(self) -> None:
        super().__init__()
        self._inversed = True


class SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(SNAFeature):
    def __init__(self) -> None:
        super().__init__()
        self._nested_source_keys = [["user_data", "id"]]
        self._nested_target_keys = [["comments_data", "id"]]

    def add_entry(self, entry: dict):
        if entry['comments'] > 0:
            super().add_entry(entry)

    def remove_entry(self, entry: dict):
        if entry['comments'] > 0:
            super().remove_entry(entry)

    def is_valid_entry(self, entry: dict) -> bool:
        if has_keys(entry, ["comments", "user_data"]):
            if entry['comments'] == 0:
                return True
            return has_keys(entry, ["comments_data"])
        return False


class SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator):
    def __init__(self) -> None:
        super().__init__()
        self._inversed = True


class SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(SNAFeature):
    def __init__(self) -> None:
        super().__init__()
        self._nested_source_keys = [["comments_data", "id"]]
        self._nested_target_keys = [["comments_data", "id"]]

    def _add_remove_edge(self, u: int, v: int,
                         activity_id: int, activity_timestamp: datetime,
                         sign: int):
        # Every edge is added twice because it's done
        # pair-wise, so the sign is halved.

        r_sign = sign * 0.5
        super()._add_remove_edge(u, v, activity_id, activity_timestamp, r_sign)

    def get_feature(self, entry: dict) -> Any:
        return super().get_feature(entry, ordered=True)


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


# Centrality


class PageRankCentrality(Feature):
    """
    Calculates the transitive experience of the submitter. 
    Aggregating all other SNA shared experiences through PageRank centrality.
    """

    def get_feature(self, entry: dict) -> float:
        user_id = entry['user_data']['id']
        pr = nx.pagerank(G, alpha=0.85, weight="weight")
        if user_id in pr:
            return pr[user_id]
        else:
            return 0

    def is_valid_entry(self, entry: dict) -> bool:
        return has_keys(entry, ['user_data'])


class WeightedMultiLayerFirstOrderDegreeCentrality(Feature, PostRunFeature):
    """
    Calculates the first-order multilayer degree centrality of the current window.

    i.e.: C^t(a) = \sum^L_{l, m} \sum^{N^{(1)}_l(a)}_{b} w_l \cdot e^t_l(a, b) \cdot w_m \cdot (d_m(b) - e^t_l(a, b))
    Where: w_l = 1 - \frac{|E_l|}{\sum_{E_m} |E_m|}
    """

    def late_init(self):
        """
        Called when the first sliding window iteration is done.
        It calculated the used weights and resets this whole file.
        """

        global TOTAL_EDGE_COUNT_PER_TYPE, EDGE_COUNT_PER_TYPE, G, \
            SNA_PR_SW_FEATURES, SNA_PR_FEATURES, SNA_ISSUE_SW_FEATURES,\
            SNA_POST_PR_FEATURES

        total_edges = sum(TOTAL_EDGE_COUNT_PER_TYPE.values())
        self.__edge_weight = {edge_type: 1 - (edge_couont / total_edges)
                              for edge_type, edge_couont in TOTAL_EDGE_COUNT_PER_TYPE.items()}

        # Resets singletons.
        TOTAL_EDGE_COUNT_PER_TYPE = None
        EDGE_COUNT_PER_TYPE = None
        G = None

        # Resets features.
        SNA_PR_SW_FEATURES, SNA_PR_FEATURES, SNA_ISSUE_SW_FEATURES, SNA_POST_PR_FEATURES = build_sna_features()

    def __is_time_respecting(self,
                             edge_data: dict, conn_edge_label: str,
                             fo_edge_data: dict, exp_edge_label: str
                             ) -> bool:
        # TODO Create a solid definition for this.
        return True

    def get_feature(self, entry: dict) -> float:
        focal_id = entry['user_data']['id']

        edge_types = self.__edge_weight.keys()
        neighbor_ids = G.neighbors(focal_id)
        centrality = 0.0

        # Iterates through all neighbors of the focal node (loop b)
        for neighbor_id in neighbor_ids:
            # Wrapped in a SafeDict for simplicity (ditto for the inner-loop).
            conn_edge_data = SafeDict(
                map=G.get_edge_data(focal_id, neighbor_id),
                default_value=0)

            # Iterates through all edge types for the connection (loop l)
            for conn_edge_label in edge_types:
                conn_intensity = conn_edge_data[conn_edge_label]
                conn_weight = self.__edge_weight[conn_edge_label]
                conn_factor = conn_weight * conn_intensity

                # Iterates through all edge types for the experience (loop m)
                for exp_edge_label in edge_types:
                    fo_neighbors_ids = G.neighbors(neighbor_id)

                    # Calculates the experience (i.e., first-order degree),
                    # by iterating through all the edges of the neighbors.
                    for fo_neighbor_id in fo_neighbors_ids:
                        # Ignores all edges with the focal node.
                        # This is equivalent to subtracting them later.
                        if fo_neighbor_id == focal_id:
                            continue

                        fo_edge_data = SafeDict(
                            map=G.get_edge_data(neighbor_id, fo_neighbor_id),
                            default_value=0)

                        if not self.__is_time_respecting(conn_edge_data, conn_edge_label,
                                                         fo_edge_data, exp_edge_label):
                            continue

                        fo_conn_intensity = fo_edge_data[exp_edge_label]
                        fo_conn_weight = self.__edge_weight[exp_edge_label]
                        fo_conn_factor = fo_conn_weight * fo_conn_intensity

                        centrality += conn_factor * fo_conn_factor

        return centrality


def build_sna_features():
    """Factory method to builds all features."""
    sna_pr_sw_features = [
        SharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(),
        SharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(),
        SharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(),
        SharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(),
        SharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(),
    ]

    sna_pr_features = [
        PageRankCentrality(),
    ]

    sna_issue_sw_features = [
        SharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(),
        SharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(),
        SharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(),
    ]

    post_pr_features = [
        WeightedMultiLayerFirstOrderDegreeCentrality()
    ]

    return sna_pr_sw_features, sna_pr_features, sna_issue_sw_features, post_pr_features


SNA_PR_SW_FEATURES, SNA_PR_FEATURES,\
    SNA_ISSUE_SW_FEATURES, SNA_POST_PR_FEATURES = build_sna_features()
