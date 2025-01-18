import csv
from itertools import chain, product
from pathlib import Path
from typing import Tuple, Set, List, Iterable, Iterator, Dict

from networkx import DiGraph
from wmutils.collections.safe_dict import SafeDict

import python_proj.utils.exp_utils as exp_utils

from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.centrality_features import SNAFeature
from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.intra_eco_centrality import _build_edge_key, SNACentralityFeature, PRIntegratorToSubmitterV2, PRCommenterToCommenterV2, PRCommenterToSubmitterV2, IssueCommenterToSubmitterV2, IssueCommenterToCommenterV2


class NormalizedSecondOrderEcosystemDegreeCentrality(SNACentralityFeature):
    """
    Note: this is not multi-layer degree centrality.
    That can only be calculated after the fact as it
    requires the total number of included edges for
    each layer. Instead, we return the individual
    values $d(x, p, \lambda, \mu)$.
    """

    def __init__(self, graph: DiGraph, edge_to_project_mapping: dict, edge_types: list[SNAFeature]) -> None:
        super().__init__(graph)
        self._edge_to_project_mapping: dict = edge_to_project_mapping
        self._edge_types = edge_types

    def add_entry(self, *args, **kwargs):
        # This class doesn't process any data entries itself, it relies on the entries of `self._edge_types`.
        return

    def remove_entry(self, *args, **kwargs):
        # This class doesn't process any data entries itself, it relies on the entries of `self._edge_types`.
        return

    def get_name(self) -> Iterator[str]:
        base_name = super().get_name()
        for la, mu in product(self._edge_types, self._edge_types):
            name = f'{base_name}({la.get_name()}.{mu.get_name()})'
            yield name

    def get_feature(self, entry: dict) -> list[int]:
        x = entry["user_data"]["id"]
        repo_path = entry[exp_utils.SOURCE_PATH_KEY]
        p = exp_utils.get_repository_name_from_source_path(repo_path)

        card_R_la, d_la_mu = self.calculate_d_la_mu(x, p)

        results = self.generate_output_vector(card_R_la, d_la_mu)
        return results

    def calculate_d_la_mu(self, x: int, p: str) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
        card_R_la = SafeDict(default_value=0)
        d_la_mu = SafeDict(SafeDict, default_value_constructor_kwargs={
            'default_value': 0.0})

        # Collects the neighbors from incoming and outgoing edges; i.e., R.
        R = self.get_neighbors(x)
        for y in R:
            E_xy = self.get_edges_between(x, y)

            # Iterates through all edges that connect with the neighbor;
            # This is stil the outer loop.
            for la, T_xy in E_xy:
                for e_t in T_xy:
                    # Filters out edges in the same project.
                    q_key = _build_edge_key(y, x, e_t, la)
                    if q_key in self._edge_to_project_mapping:
                        q = self._edge_to_project_mapping[q_key]
                    else:
                        q_key_2 = _build_edge_key(x, y, e_t, la)
                        q = self._edge_to_project_mapping[q_key_2]
                    if p == q:
                        break

                    # Any element that reaches beyond this point is an element of R_\lambda(x, p).

                    # Updates the counter, used to normalize the entry ($1/|R_\lambda(x, p)|$).
                    card_R_la[la] += 1
                    nb_degree = self.calculate_nb_degree(x, y, e_t)
                    for mu, d in nb_degree.items():
                        d_la_mu[la][mu] += d

        return card_R_la, d_la_mu

    def calculate_nb_degree(self, x: int,  y: int, t: float) -> Dict[str, int]:
        """
        Calculates $e_\mu = (|E_\mu(y)| - |E_\mu(y, x)|)$ differentiating
        between each layer of the graph, for a single neighbor $y$.
        """

        e_mu = SafeDict(default_value=0)
        # Collects the neighbors from incoming and outgoing edges; i.e., R.
        # and removes all entries that are x.
        E = self.get_neighbors(y)
        E = (z for z in E if z != x)
        for z in E:
            E_yz = self.get_edges_between(y, z)
            # Per edge, it retrieves the timed edges, and iterates through those.
            for mu, T_yz in E_yz:
                for e_t in T_yz:
                    # Ignores non-chronological edges.
                    if e_t >= t:
                        continue
                    e_mu[mu] += 1
        return e_mu

    def get_neighbors(self, x: int) -> Set[int]:
        # Collects the neighbors from incoming and outgoing edges; i.e., R.
        # The first element of the in_edge_tuple is the neighbor.
        e_in = self._graph.in_edges(nbunch=[x])
        e_in = ((v, u) for u, v in e_in)
        # The second element of the out_edge tuple is the neighbor.
        e_out = self._graph.out_edges(nbunch=[x])
        nbs = {neighbor_id for _, neighbor_id in chain(e_in, e_out)}
        return nbs

    def get_edges_between(self, x: int, y: int) -> List[Dict]:
        def __helper_get_edges_between() -> Iterable[Tuple[str, Iterable[float]]]:
            """Helper method to iterate through all edges connnecting x and y."""
            E_in = self._graph.get_edge_data(x, y)
            if not E_in is None:
                yield from E_in.items()
            E_out = self._graph.get_edge_data(y, x)
            if not E_out is None:
                yield from E_out.items()

        def __helper_filter_duplicates(edges) -> Iterable[Tuple[str, Iterable[float]]]:
            # NOTE: The implementation of SNAFeature, which this class relies on does not consider duplicate edges.
            # However, these do affect the calculations, so need to be accounted for.
            # Characteristics of a duplicate edge are: same source and target node, same time stamp, same layer.
            # Within the context of this method, this comes down to testing their timestamps.
            for layer, edges in edges:
                exclusion_list = set()
                unique_edges = []
                for edge in edges:
                    if edge in exclusion_list:
                        continue
                    exclusion_list.add(edge)
                    unique_edges.append(edge)
                yield layer, unique_edges

        edges = __helper_get_edges_between()
        edges = __helper_filter_duplicates(edges)
        edges = list(edges)
        return edges

    def generate_output_vector(self, card_R_la: Dict[str, int], d_la_mu: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
        # Normalizes the data and adds it to an output vector.
        out = []
        for la, mu in product(self._edge_types, self._edge_types):
            l = la.get_name()
            m = mu.get_name()
            if card_R_la[l] == 0:
                norm_d_la_mu = 0
            else:
                norm_d_la_mu = d_la_mu[l][m] / card_R_la[l]
            out.append(norm_d_la_mu)
        return out


def get_bot_ids():
    # Loads bot IDs and bans them.
    bot_path = Path(exp_utils.BASE_PATH).absolute() \
        .joinpath("bot_data").joinpath("all_bot_ids.csv").absolute()
    print(f'Loading bot IDs from "{str(bot_path)}".')
    with open(bot_path, 'r', encoding='utf-8') as bot_file:
        csv_reader = csv.reader(bot_file)
        # skips header
        _ = next(csv_reader)
        bot_ids = {int(row[0]) for row in csv_reader}
    print(f'Loaded list of {len(bot_ids)} bot IDs.')
    return bot_ids


def build_so_degree_features() -> (
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
    activity_graphs: list[SNAFeature] = [*pr_graph, *issue_graph]

    bot_ids = get_bot_ids()
    for g in activity_graphs:
        g.set_banned_nodes(bot_ids)

    # Builds our feature.
    centr_features = [
        NormalizedSecondOrderEcosystemDegreeCentrality(
            graph, edge_to_project_mapping, activity_graphs)
    ]

    return pr_graph, issue_graph, centr_features
