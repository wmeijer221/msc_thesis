
import itertools
import networkx as nx
from typing import Any, Tuple, Callable

from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature, Feature
from python_proj.utils.exp_utils import get_integrator_key
from python_proj.utils.util import has_keys, get_nested_many


G: nx.DiGraph = None
EDGE_COUNT_PER_TYPE: dict = None


class SNAFeature(SlidingWindowFeature):
    """
    Base class for social network analysis features, minimizing redundant 
    code. Implementing classes only need to override the source_keys lists 
    and the edge label to work. In the context of these classes, when 
    retrieving the feature's value, ``u`` is always the pull request submitter
    and ``v`` the pull request integrator.
    """

    def __init__(self) -> None:
        global G, EDGE_COUNT_PER_TYPE
        # Dreate singleton graph.
        if G is None:
            G = nx.DiGraph()

        # Dreate singleton edge counter.
        if EDGE_COUNT_PER_TYPE is None:
            EDGE_COUNT_PER_TYPE = {}

        self._edge_label: str = self.__class__.__name__
        self._nested_source_keys: list[list[str | Callable[[dict], str]]] = []
        self._nested_target_keys: list[list[str | Callable[[dict], str]]] = []
        self._inversed: bool = False

        # "Register" local instance to edge counter.
        if self._edge_label not in EDGE_COUNT_PER_TYPE:
            EDGE_COUNT_PER_TYPE[self._edge_label] = 0

    def _add_nodes(self, nodes: int | list[int]):
        if isinstance(nodes, int):
            nodes = [nodes]
        for node in nodes:
            if not G.has_node(node):
                G.add_node(node)

    def _add_remove_edge(self,
                         u: int, v: int,
                         label: str,
                         sign: int):
        """Adds a single edge, ignoring self-loops."""
        if u == v:
            return
        edge_data = G.get_edge_data(u, v, default={})
        if label in edge_data:
            edge_data[label] += sign
        else:
            edge_data[label] = sign
        G.add_edge(u, v, **edge_data)
        EDGE_COUNT_PER_TYPE[self._edge_label] += sign
        self._recalculate_weight(u, v)

    def _add_remove_edges(self,
                          us: int | list[int],
                          vs: int | list[int],
                          label: str,
                          sign: int):
        """Adds multiple edges, pairwise."""
        if isinstance(us, int):
            us = [us]
        if isinstance(vs, int):
            vs = [vs]
        self._add_nodes(itertools.chain(us, vs))
        for u in us:
            for v in vs:
                self._add_remove_edge(u, v, label, sign)

    def _recalculate_weight(self, u: int, v: int):
        edge_data = G.get_edge_data(u, v, default={})
        weight = 0.0
        for key, value in EDGE_COUNT_PER_TYPE.items():
            if key in edge_data:
                weight += edge_data[key] / (1 + value)
        edge_data['weight'] = weight
        G.add_edge(u, v, **edge_data)

    def _get_us_and_vs(self, entry: dict) -> Tuple[list[int], list[int]]:
        def __get_nodes(nested_keys: list[list[str | Callable[[dict], str]]]) -> list[int]:
            nodes = []
            for nested_key in nested_keys:
                r_nested_key = []
                for key in nested_key:
                    if isinstance(key, Callable):
                        key = key(entry)
                    r_nested_key.append(key)
                node = get_nested_many(entry, r_nested_key)
                if node is None:
                    continue
                elif isinstance(node, list):
                    nodes.extend(node)
                else:
                    nodes.append(node)
            return nodes

        if self._inversed:
            us = __get_nodes(self._nested_target_keys)
            vs = __get_nodes(self._nested_source_keys)
        else:
            us = __get_nodes(self._nested_source_keys)
            vs = __get_nodes(self._nested_target_keys)
        return us, vs

    def add_entry(self, entry: dict):
        us, vs = self._get_us_and_vs(entry)
        self._add_remove_edges(us, vs, self._edge_label, sign=1)

    def remove_entry(self, entry: dict):
        us, vs = self._get_us_and_vs(entry)
        self._add_remove_edges(us, vs, self._edge_label, sign=-1)

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

    def _add_remove_edge(self, u: int, v: int, label: str, sign: int):
        # Every edge is added twice because it's done
        # pair-wise, so the sign is halved.
        r_sign = sign * 0.5
        if u < v:
            super()._add_remove_edge(u, v, label, r_sign)
        else:
            super()._add_remove_edge(v, u, label, r_sign)

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


class TransitiveExperienceSubmitter(Feature):
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
        TransitiveExperienceSubmitter(),
    ]

    sna_issue_sw_features = [
        SharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(),
        SharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(),
        SharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(),
    ]

    return sna_pr_sw_features, sna_pr_features, sna_issue_sw_features


SNA_PR_SW_FEATURES, SNA_PR_FEATURES, SNA_ISSUE_SW_FEATURES = build_sna_features()
