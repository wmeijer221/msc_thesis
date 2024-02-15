"""
A little test to implement time-respecting betweenness centrality.
"""

import matplotlib.pyplot as plt
import networkx as nx
from numbers import Number


class TimedGraph(nx.MultiDiGraph):
    """
    Decorator for graph with timed edges.
    """

    def __init__(self, incoming_graph_data=None, multigraph_input=None, **attr) -> None:
        super().__init__(incoming_graph_data, multigraph_input, **attr)

    def add_edge(self, u_for_edge, v_for_edge, timestamp: Number, key=None, **attr):
        return super().add_edge(u_for_edge, v_for_edge, key, timestamp=timestamp, **attr)


def chronological_dijkstra(graph: TimedGraph, source, target):
    # Implement Dijkstra's algorithm with chronological ordering based on edge timestamps
    visited = set()
    paths = {source: ([], 0)}  # {node: (path from source, cumulative weight)}
    while paths:
        node, (path, _) = min(paths.items(), key=lambda x: x[1][1])
        if node == target:
            return path + [node]
        visited.add(node)
        del paths[node]
        for successor, edge_attrs in graph[node].items():
            for _, edge_attr in edge_attrs.items():
                if successor not in visited:
                    new_weight = edge_attr.get('timestamp', 0)
                    new_path = path + [node]
                    if successor not in paths or new_weight < paths[successor][1]:
                        paths[successor] = (new_path, new_weight)


def neighborhood_betweenness_centrality(graph, node, radius):
    neighborhood = nx.ego_graph(graph, node, radius=radius, undirected=True)
    total = 0
    between = 0
    for source in neighborhood.nodes():
        if source == node:
            continue
        for target in neighborhood.nodes():
            if target == node:
                continue
            path = chronological_dijkstra(neighborhood, source, target)
            total += 1
            if path and node in path:
                between += 1
    return between / total


if __name__ == "__main__":

    graph = nx.MultiDiGraph()
    timed_graph = TimedGraph(graph)

    timed_graph.add_nodes_from(["A", "B", "C", "D", "E", "F", "G", "H"])

    # Adding edges with timestamps as attributes
    timed_graph.add_edge("A", "B", timestamp=1630000000)
    timed_graph.add_edge("A", "C", timestamp=1631000000)
    timed_graph.add_edge("B", "D", timestamp=1632000000)
    timed_graph.add_edge("C", "D", timestamp=1633000000)
    timed_graph.add_edge("B", "E", timestamp=1634000000)
    timed_graph.add_edge("D", "E", timestamp=1635000000)
    timed_graph.add_edge("E", "F", timestamp=1636000000)
    timed_graph.add_edge("C", "F", timestamp=1637000000)
    timed_graph.add_edge("B", "G", timestamp=1638000000)
    timed_graph.add_edge("F", "G", timestamp=1639000000)
    timed_graph.add_edge("G", "H", timestamp=1640000000)
    timed_graph.add_edge("E", "H", timestamp=1641000000)
    timed_graph.add_edge("A", "H", timestamp=1642000000)

    for node in timed_graph.nodes():
        betweenness = neighborhood_betweenness_centrality(
            timed_graph, node, radius=2)
        print(f'{node=}, {betweenness=}')
