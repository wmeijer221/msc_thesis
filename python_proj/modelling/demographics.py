"""
Outdated: This only works on the .json data, which isn't great to work with.
TODO: implement this to work with the .csv dataset.
"""

from datetime import datetime
import json
import matplotlib.pyplot as plt
from os import path, makedirs

from python_proj.utils.arg_utils import safe_get_argv
import python_proj.utils.exp_utils as exp_utils

# Loads relevant paths.
exp_utils.load_paths_for_all_argv()
data_path = exp_utils.CHRONOLOGICAL_DATASET_PATH
figure_path = exp_utils.FIGURE_PATH

figure_folder = path.dirname(figure_path(figure_name="_"))
if not path.exists(figure_folder):
    makedirs(figure_folder)


def prs_over_time():
    buckets: dict[datetime, int] = {}
    with open(data_path, "r") as data_file:
        for entry in data_file:
            j_entry = json.loads(entry)
            closed_at = j_entry['closed_at']
            try:
                # Used in GitHub
                dt_closed_at = datetime.strptime(
                    closed_at, "%Y-%m-%dT%H:%M:%SZ")
            except:
                # Used in GitLab.
                dt_closed_at = datetime.strptime(
                    closed_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                )

            if dt_closed_at > exp_utils.LIBRARIES_IO_DATASET_END_DATE:
                continue

            # Adds key
            dt_year_month = datetime(
                year=dt_closed_at.year, month=dt_closed_at.month, day=1)
            if not dt_year_month in buckets:
                buckets[dt_year_month] = 0

            # counts entry
            buckets[dt_year_month] += 1

    plt.cla()
    plt.plot(buckets.keys(), buckets.values())
    plt.title('Closed Pull Requests Per Month')
    plt.xlabel('Month')
    plt.ylabel('Closed Pull Requests')
    output_path = figure_path(figure_name='prs_over_time')
    plt.savefig(fname=output_path)
    print(f'Stored figure at {output_path}')


def prs_per_project():
    buckets: dict[str, int] = {}

    total = 0
    with open(data_path, "r") as data_file:
        for entry in data_file:
            j_entry = json.loads(entry)

            source_file = j_entry['__source_path']

            if not source_file in buckets:
                buckets[source_file] = 0

            buckets[source_file] += 1
            total += 1

    plt.cla()

    entries = list(buckets.items())
    entries.sort(key=lambda x: x[1])
    x_axis = range(len(entries))
    y_axis = [entry[1] for entry in entries]
    plt.plot(x_axis, y_axis)

    perc_count = 0
    percentiles = [0.4]
    current_perc = 0
    vlines = []
    people = 0
    for index, (id, count) in enumerate(entries):
        perc_count += count
        people += 1
        target_perc = percentiles[current_perc] * total
        if perc_count >= target_perc:
            vlines.append(index)
            current_perc += 1
            if current_perc >= len(percentiles):
                break

    plt.vlines(vlines, 0, entries[-1][1], linestyles='dashed', colors='red')
    print(
        f'{len(entries) - people}/{len(entries):.03f} ({100 * ((len(entries) - people) / len(entries)):.03f}%) are responsible for {100 - percentiles[0] * 100}% of the PRs')

    plt.title('Closed Pull Requests Per project')
    plt.xlabel('Project')
    plt.ylabel('Closed Pull Requests')
    output_path = figure_path(figure_name='prs_per_project')
    plt.savefig(fname=output_path)
    print(f'Stored figure at {output_path}')


def prs_per_user():
    buckets: dict[datetime, int] = {}
    id_to_data = {}
    total = 0
    with open(data_path, "r") as data_file:
        for entry in data_file:
            j_entry = json.loads(entry)

            # Ignored GL entries.
            if 'user_data' not in j_entry:
                continue

            user_data = j_entry["user_data"]
            user_id = user_data["id"]

            if user_id not in buckets:
                buckets[user_id] = 0
                id_to_data[user_id] = user_data

            buckets[user_id] += 1
            total += 1

    plt.cla()

    entries = list(buckets.items())
    entries.sort(key=lambda x: x[1])
    x_axis = range(len(entries))
    y_axis = [entry[1] for entry in entries]
    plt.plot(x_axis, y_axis)

    perc_count = 0
    percentiles = [0.4]
    current_perc = 0
    vlines = []
    people = 0
    for index, (id, count) in enumerate(entries):
        perc_count += count
        people += 1
        target_perc = percentiles[current_perc] * total
        if perc_count >= target_perc:
            vlines.append(index)
            current_perc += 1
            if current_perc >= len(percentiles):
                break

    plt.vlines(vlines, 0, entries[-1][1], linestyles='dashed', colors='red')
    print(
        f'{len(entries) - people}/{len(entries):.03f} ({100*((len(entries) - people) / len(entries)):.03f}%) are responsible for {100 - percentiles[0] * 100}% of the PRs')

    plt.title('Closed Pull Requests Per User')
    plt.xlabel('User')
    plt.ylabel('Closed Pull Requests')
    output_path = figure_path(figure_name='prs_per_user')
    plt.savefig(fname=output_path)
    print(f'Stored figure at {output_path}')

    print_top_users = safe_get_argv("-p", "n").lower()
    if print_top_users != "y":
        return

    for entry in entries[-(len(entries) - people):]:
        # print(entry)
        j_out = id_to_data[entry[0]]
        j_out['pull_request_count'] = entry[1]
        print(json.dumps(j_out))


if __name__ == "__main__":
    mode = safe_get_argv(key='-m', default="t")

    match mode:
        case "t":
            prs_over_time()
        case "u":
            prs_per_user()
        case "p":
            prs_per_project()
        case "a":
            prs_over_time()
            prs_per_user()
            prs_per_project()
        case _:
            raise ValueError(f"Invalid mode {mode}.")
