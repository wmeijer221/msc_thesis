from python_proj.experiment.replication_study.retrieve_pull_requests import end_date
import json
from sys import argv
from datetime import datetime

input_path = './data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted.json'
output_path = './data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json'


def load_data():
    data = []
    with open(input_path, "r") as input_data:
        for line in input_data:
            line = line.strip()
            j_entry = json.loads(line)
            data.append(j_entry)
    return data


def build_filters(filter_keys: str):
    filters = {
        'p': filter_for_github,
        'd': filter_by_close_date,
        'b': filter_for_bots
    }
    filters = [filters[key] for key in filter_keys]
    return filters


def filter_by_close_date(entry):
    closed_at_key = 'closed_at'
    if not closed_at_key in entry:
        return False
    closed_date = entry[closed_at_key]
    closed_at_dt = datetime.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
    return closed_at_dt <= end_date


def filter_for_github(entry):
    created_at_key = 'created_at'
    created_date = entry[created_at_key]
    # HACK: GitLab uses a different time format. I've got no better way to test for GH PRs, though.
    try:
        datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except:
        pass
    finally:
        return False


def filter_for_bots(entry):
    return True


def filter_data(data: list, filters: list) -> list:
    filtered_data = []
    filtered_by = [0] * len(filters)
    for entry in data:
        is_included = True
        for index, filter in enumerate(filters):
            if not filter(entry):
                filtered_by[index] += 1
                is_included = False
                break
        if is_included:
            filtered_data.append(entry)
    print(filtered_by)
    return filtered_data


def write_data(data: list):
    with open(output_path, "w+") as output_file:
        for entry in data:
            output_file.write(f'{json.dumps(entry)}\n')


if __name__ == "__main__":
    mode = argv[argv.index('-m') + 1]

    filters = build_filters(mode)
    data = load_data()
    print(f'Start size: {len(data)}.')

    filtered_data = filter_data(data, filters)
    print(f'Filtered size: {len(filtered_data)}.')
    write_data(filtered_data)
