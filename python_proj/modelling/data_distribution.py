import numpy as np
from matplotlib import pyplot as plt
from csv import reader
import itertools
from sys import argv
from datetime import datetime
import math
from typing import Callable, Any, Dict

file = argv[argv.index('-i') + 1]

data_path = f'./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{file}.csv'


def get_data_iterator():
    with open(data_path, "r") as data_file:
        for entry in reader(data_file):
            yield entry


mode = argv[argv.index('-m') + 1]


if 'd' in mode:
    def show_distribution_per_x(get_key: Callable[[Dict], Any],
                                title: str,
                                show_sorted: bool,
                                top_percentile: float):
        dataset = get_data_iterator()

        distribution = {}
        next(dataset)  # skips header
        for entry in dataset:
            key = get_key(entry)
            if key not in distribution:
                distribution[key] = 0
            distribution[key] += 1

        if show_sorted:
            distribution = list(distribution.items())
            distribution.sort(key=lambda x: x[1])
            distribution = {index: value for index,
                            (_, value) in enumerate(distribution)}

        plt.cla()
        plt.title(f"Distribution closed PRs across {title}.")
        plt.xlabel(title)
        plt.ylabel('frequency')

        plt.plot(distribution.keys(), distribution.values(), label='frequency')

        if top_percentile > 0:
            inverse_percentile = 1.0 - top_percentile
            key_count = len(distribution)
            top_keys = math.floor(key_count * inverse_percentile)
            v_min = 9999999999999999
            v_max = -9999999999999999
            total = 0
            percentile_total = 0
            for index, (key, entry) in enumerate(distribution.items()):
                v_min = min(v_min, entry)
                v_max = max(v_max, entry)
                total += entry
                if index < top_keys:
                    percentile_total += entry
            percentile_total = 1.0 - (percentile_total / total)

            label = f'{inverse_percentile*100:.00f}th percentile (contains {percentile_total * 100:.01f}% of the data)'
            plt.vlines([top_keys], v_min, v_max, colors='r',
                       linestyles='--', label=label)

        plt.legend()
        plt.show()

    def month_key(entry: dict):
        closed_at = datetime.strptime(entry[4], "%Y-%m-%dT%H:%M:%SZ")
        by_month = datetime(year=closed_at.year, month=closed_at.month, day=1)
        return by_month

    show_distribution_per_x(month_key,
                            title="time in months",
                            show_sorted=False,
                            top_percentile=-1)

    show_distribution_per_x(lambda entry: entry[1],
                            title="projects",
                            show_sorted=True,
                            top_percentile=0.03)

    show_distribution_per_x(lambda entry: entry[3],
                            title="users",
                            show_sorted=True,
                            top_percentile=0.03)

    # Distribution across projects.
    distribution_by_project = {}


if 'f' in mode:
    dataset = get_data_iterator()
    headers = next(dataset)
    first_entry = next(dataset)

    # The first 5 fields are ignored as they're metadata or the dependent variable.
    start_index = 6
    merged_index = 5
    data_types = [None] * (len(headers) - start_index)

    def try_parse_float(element: str) -> float:
        try:
            return float(element)
        except:
            return None

    # Figure out whether it's qualitative or quantitative
    for index, element in enumerate(first_entry[start_index:]):
        number = try_parse_float(str(element))
        if isinstance(number, float):
            data_types[index] = 'qt'
        else:
            data_types[index] = 'ql'

        print(f'{headers[index + start_index]} is {data_types[index]}.')

    # Iterates through data.
    data = {field: [] for field in headers[start_index:]}
    is_merged = []
    for j, entry in enumerate(itertools.chain([first_entry], dataset)):
        # print(entry[start_index:])
        for index, field in enumerate(entry[start_index:]):
            header = headers[index + start_index]
            if data_types[index] == 'qt':
                data[header].append(float(field))
            else:
                data[header].append(str(field))
            pr_is_merged = entry[merged_index] == 'True'
            is_merged.append(pr_is_merged)

    # Generates images.
    for index, (field, entries) in enumerate(data.items()):
        plt.cla()
        plt.title(f"Distribution of {field}")
        plt.xlabel(f'{field}')
        plt.ylabel('frequency')

        # plt.figure()
        # plt.title(field)
        if data_types[index] == 'qt':
            merged_entries = [entry for i,
                              entry in enumerate(entries) if is_merged[i]]
            unmerged_entries = [entry for i, entry in enumerate(
                entries) if not is_merged[i]]

            colors = ['#00BFFF', '#FF9999']
            (bin_counts, bins, _) = plt.hist([merged_entries, unmerged_entries],
                                    histtype='barstacked', bins=100, color=colors, label=['Merged', 'Not Merged'])

            plt.gca().set(
                title=f'Frequency Histogram {field}', ylabel='Frequency')
            plt.legend()
            plt.show()

            # PROPORTIONS

            plt.cla()

            # Sample data
            data_merged = np.array(bin_counts[0])
            data_unmerged = np.array(bin_counts[1])
            categories = [''] * len(bins[0:-1]) 

            # Pairwise division
            division = data_merged / (data_merged + data_unmerged)
            division2 = data_unmerged / (data_merged + data_unmerged)

            print(division)
            
        else:
            bin_counts = {}
            for entry in entries:
                if not entry in bin_counts:
                    bin_counts[entry] = 0
                bin_counts[entry] += 1
            plt.bar(bin_counts.keys(), bin_counts.values())
        plt.show()
