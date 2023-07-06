
"""
Implements the sliding window algorithm specifically for the social network analysis bits.
The main difference here is that it's paralellized.

What I want this thing to do:
- Do data parallelization so I can split up the dataset.
    - A chunk should be the size of one time window, however, requires 
      padding of the length of the time window before as well.
- Create a directed graph within this time window.
    - Edges: 
        - integrator -> submitter
        - commenter -> submitter
        - commenter -> commenter with respect to time.

        
NOTE: This was a nice attempt, but it doesn't really work.
"""

from collections import deque
import csv
from datetime import datetime, timedelta
import itertools
import json
import os

from typing import Tuple, Generator, Callable
import networkx as nx

from python_proj.utils.arg_utils import safe_get_argv, get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.data_preprocessing.sliding_window_features import SlidingWindowFeature
from python_proj.utils.mt_utils import parallelize_tasks
from python_proj.utils.util import Counter, get_nested_many, tuple_chain, intermediary_chain, safe_makedirs


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

def create_data_chunk_stream(
    issue_file_names: list[str],
    pr_file_names: list[str],
    window_size: timedelta,
    base_path: str,
) -> Generator[str, None, None]:
    chunk_counter = Counter(start_value=0)

    def __make_chunk_next_file():
        chunk_file_path = base_path + str(chunk_counter.get_next())
        return open(chunk_file_path, "w+", encoding='utf-8')

    current_chunk_file = __make_chunk_next_file()
    next_chunk_file = __make_chunk_next_file()

    data_iterator = exp_utils.iterate_through_multiple_chronological_issue_pr_datasets(
        issue_file_names, pr_file_names)

    chunk_start_timestamp: datetime = None
    dt_format = "%Y-%m-%dT%H:%M:%SZ"

    for entry in data_iterator:
        timestamp = datetime.strptime(entry['closed_at'], dt_format)

        if chunk_start_timestamp is None:
            chunk_start_timestamp = timestamp

        chunk_delta = timestamp - chunk_start_timestamp
        if chunk_delta > window_size:
            chunk_start_timestamp = timestamp
            current_chunk_file.close()
            current_chunk_name = current_chunk_file.name
            print(f'Finished creating chunk "{current_chunk_name}".')
            yield current_chunk_name
            current_chunk_file = next_chunk_file
            next_chunk_file = __make_chunk_next_file()

        line = f'{json.dumps(entry)}\n'
        current_chunk_file.write(line)
        next_chunk_file.write(line)

    next_chunk_file.close()
    next_chunk_name = next_chunk_file.name
    print(f'Finished creating last chunk "{current_chunk_name}".')
    yield next_chunk_name


def handle_chunk(task: Tuple[str | None, str],
                 time_window: timedelta,
                 base_path: str,
                 *_, **__):
    previous_chunk, current_chunk = task
    print(f'Starting with chunks: {previous_chunk=}, {current_chunk=}')

    chunk_name = os.path.basename(current_chunk)
    output_path = base_path + chunk_name

    graph = nx.DiGraph()
    pr_features: list[SNAFeature] = [PRIntegratorToSubmitter(graph),
                                     PRCommenterToSubmitter(graph),
                                     PRCommenterToCommenter(graph)]
    issue_features: list[SNAFeature] = [IssueCommenterToSubmitter(graph),
                                        IssueCommenterToCommenter(graph)]
    centrality_metrics: list[SNAFeature] = [PageRankCentrality(graph)]

    datetime_format = "%Y-%m-%dT%H:%M:%SZ"

    window: dict[datetime, list[dict]] = {}
    window_keys = deque()

    # Adds the entire previous chunk, and constructs the initial window.
    if not previous_chunk is None:
        with open(previous_chunk, "r", encoding='utf-8') as input_file:
            for line in input_file:
                new_entry = json.loads(line)

                # Handles timestamping
                new_entry_date = datetime.strptime(
                    new_entry['closed_at'], datetime_format)

                # Adds new entry to window.
                if new_entry_date not in window:
                    window[new_entry_date] = []
                window[new_entry_date].append(new_entry)
                window_keys.append(new_entry_date)

                # Updates model
                if new_entry['__data_type'] == 'issues':
                    for feature in issue_features:
                        feature.add_entry(new_entry)
                else:
                    for feature in pr_features:
                        feature.add_entry(new_entry)

    print(f'Loaded first half for chunks: {previous_chunk=}, {current_chunk=}')

    # Iterates through the current chunks entries.
    with open(output_path, "w+", encoding='utf-8') as output_file:
        csv_writer = csv.writer(output_file)

        # Writes header.
        header = [feature.get_name() for feature in centrality_metrics]
        csv_writer.writerow(header)

        with open(current_chunk, "r", encoding='utf-8') as input_file:
            for line in input_file:
                new_entry = json.loads(line)

                # Parses the entry's timestamp.
                new_entry_date = datetime.strptime(
                    new_entry['closed_at'], datetime_format)

                # Collects to-be-pruned entries.
                pruned_entries = []
                new_window_start = new_entry_date - time_window
                broke_loop = False
                while len(window_keys) > 0:
                    potential_pruned_key = window_keys.popleft()
                    if potential_pruned_key >= new_window_start:
                        broke_loop = True
                        break
                    # when the key is added to the linked list twice,
                    # it'll already be deleted.
                    if potential_pruned_key not in window:
                        continue
                    new_pruned_entries = window[potential_pruned_key]
                    pruned_entries.extend(new_pruned_entries)
                    del window[potential_pruned_key]
                # If the loop was broken, it means we popped one too
                # many, so the last one is added again.
                if broke_loop:
                    window_keys.appendleft(potential_pruned_key)

                # Prunes entries.
                for pruned_entry in pruned_entries:
                    if pruned_entry['__data_type'] == 'issues':
                        for feature in issue_features:
                            feature.remove_entry(pruned_entry)
                    else:
                        for feature in pr_features:
                            feature.remove_entry(pruned_entry)

                # Calculates features if it's a PR.
                if new_entry["__data_type"] == "pull-requests":
                    data_point = [None] * len(centrality_metrics)
                    for index, feature in enumerate(centrality_metrics):
                        data_point[index] = feature.get_feature(new_entry)
                    csv_writer.writerow(data_point)

                # Adds new entry.
                if new_entry['__data_type'] == 'issues':
                    for feature in issue_features:
                        feature.add_entry(new_entry)
                else:
                    for feature in pr_features:
                        feature.add_entry(new_entry)

                window_keys.append(new_entry_date)
                if new_entry_date not in window:
                    window[new_entry_date] = []
                window[new_entry_date].append(new_entry)

    print(f'Finished processing all chunks: {previous_chunk=}, {current_chunk=}')



def sliding_window():
    exp_utils.load_paths_for_eco()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']
    output_file_name = get_argv(key='-o')
    output_path = exp_utils.TRAIN_DATASET_PATH(file_name=output_file_name)
    print(f'Using output path "{output_path}".')

    days = safe_get_argv(key="-w", default=None, data_type=int)
    window_delta = timedelta(days=days)
    thread_count = safe_get_argv(key='-t', default=1, data_type=int)

    chunk_base_path = exp_utils.BASE_PATH + "/temp/sna_chunks/"
    chunk_output_base_path = exp_utils.BASE_PATH + "/temp/sna_output/"
    print(f'Using chunk base path: "{chunk_base_path}".')
    print(f'Using chunk output base path: "{chunk_output_base_path}".')

    # Creates relevant directories.
    safe_makedirs(os.path.dirname(output_path))
    safe_makedirs(chunk_base_path)
    safe_makedirs(chunk_output_base_path)

    # intermediary method of the generator that stores chunk
    # file names to delete them later.
    chunk_file_names = []

    def __add_entry_to_list(chunk_file_name: str):
        print(f'Received new chunk file: "{chunk_file_name}".')
        chunk_file_names.append(chunk_file_name)

    # creates data iterator.
    chunk_generator = create_data_chunk_stream(input_issue_dataset_names,
                                               input_pr_dataset_names,
                                               window_delta,
                                               chunk_base_path)
    chunk_generator = intermediary_chain(chunk_generator, __add_entry_to_list)
    chunk_generator = tuple_chain(chunk_generator, yield_first=True)

    parallelize_tasks(
        chunk_generator,
        handle_chunk,
        thread_count,
        # kwargs:
        time_window=window_delta,
        base_path=chunk_output_base_path
    )

    # Prunes all chunk data files.
    for file in chunk_file_names:
        os.remove(file)

    # Combines the output of each file to the final output file
    # and removes the chunk output file.
    with open(output_path, "w+", encoding='utf-8')as output_file:
        for chunk_file in chunk_file_names:
            file_name = os.path.basename(chunk_file)
            chunk_output_path = chunk_output_base_path + file_name
            with open(chunk_output_path, "r", encoding='utf-8') as input_file:
                output_file.writelines(input_file)
            os.remove(chunk_output_path)


if __name__ == "__main__":
    mode = safe_get_argv(key='-m', default='s')
    print(f'Starting in mode: {mode}.')
    match(mode):
        case 's':
            sliding_window()
        case _:
            raise ValueError(f"Invalid mode {mode}.")
