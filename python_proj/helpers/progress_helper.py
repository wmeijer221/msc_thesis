"""
Implements a number of methods that help tracking
the progress of the data retrieval process.
"""


from sys import argv
from csv import reader
from copy import deepcopy

from python_proj.utils.exp_utils import BASE_PATH

data_path = BASE_PATH + "libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
filter_path = BASE_PATH + "libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects_dl.csv"


def find(name: str):
    with open(data_path, "r") as input_file:
        csv_reader = reader(input_file)
        i = 0
        results = []
        for entry in csv_reader:
            proj_name = entry[22].lower()
            # print(proj_name)
            if proj_name == name:
                results.append(i)
            i += 1
    if len(results) == 1:
        return results[0]
    else:
        return results


def count_filtered_after(name: str):
    with open(data_path, "r") as input_file:
        csv_reader = reader(input_file)

        with open(filter_path, "r") as filter_file:
            included = set([entry.strip() for entry in filter_file])

            unique_before = set()
            unique_total = set()
            for entry in csv_reader:
                proj_name = entry[22].lower()
                if proj_name == name:
                    unique_before = deepcopy(unique_total)
                elif proj_name in included:
                    unique_total.add(proj_name)

    return len(unique_before), len(unique_total)


if __name__ == "__main__":

    mode = argv[argv.index("-m") + 1]
    name = argv[argv.index("-t") + 1].lower()
    match mode:
        case "f":
            index = find(name)
            print(f'{name=} is at {index=}')
        case "l":
            filtered_before, filtered_total = count_filtered_after(name)
            prc = (filtered_before / filtered_total) * 100
            print(f'{name}: {filtered_before} / {filtered_total} ({prc:.3f}%)')
        case "a":
            index = find(name)
            print(f'{name=} is at {index=}')
            filtered_before, filtered_total = count_filtered_after(name)
            prc = (filtered_before / filtered_total) * 100
            print(f'{name}: {filtered_before} / {filtered_total} ({prc:.3f}%)')
