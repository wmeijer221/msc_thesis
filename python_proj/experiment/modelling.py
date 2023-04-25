import numpy as np
from matplotlib import pyplot as plt
from csv import reader
import itertools
import random

# Loads data
data_path = './data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/cumulative_dataset.csv'
data_file = open(data_path, "r")
dataset = reader(data_file)


headers = next(dataset)
first_entry = next(dataset)

# The first 5 fields are ignored as they're metadata or the dependent variable.
start_index = 5
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
for j, entry in enumerate(itertools.chain([first_entry], dataset)):
    # print(entry[start_index:])
    for index, field in enumerate(entry[start_index:]):
        header = headers[index + start_index]
        if data_types[index] == 'qt':
            data[header].append(float(field))
        else:
            data[header].append(str(field))

# Generates images.
for index, (field, entries) in enumerate(data.items()):
    plt.figure()
    plt.title(field)
    if data_types[index] == 'qt':
        plt.hist(entries, bins=1000)
        plt.gca().set(title=f'Frequency Histogram {field}', ylabel='Frequency')
    else:
        counts = {}
        for entry in entries:
            if not entry in counts:
                counts[entry] = 0
            counts[entry] += 1
        plt.bar(counts.keys(), counts.values())
    plt.show()
