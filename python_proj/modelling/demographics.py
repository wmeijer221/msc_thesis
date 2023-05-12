"""
Outdated: This only works on the .json data, which isn't great to work with.
TODO: implement this to work with the .csv dataset.
"""

import json
from datetime import datetime
import matplotlib.pyplot as plt
from sys import argv

from python_proj.data_retrieval.retrieve_pull_requests import end_date

base_data_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{list}.json"
data_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json"


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

            if dt_closed_at > end_date:
                continue

            # Adds key
            dt_year_month = datetime(
                year=dt_closed_at.year, month=dt_closed_at.month, day=1)
            if not dt_year_month in buckets:
                buckets[dt_year_month] = 0

            # counts entry
            buckets[dt_year_month] += 1

    plt.plot(buckets.keys(), buckets.values())
    plt.title('Closed Pull Requests Per Month')
    plt.xlabel('Month')
    plt.ylabel('Closed Pull Requests')
    plt.show()


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
    print(f'{len(entries) - people}/{len(entries):.03f} ({(len(entries) - people) / len(entries)}%) are responsible for {100 - percentiles[0] * 100}% of the PRs')

    plt.title('Closed Pull Requests Per project')
    plt.xlabel('Project')
    plt.ylabel('Closed Pull Requests')
    plt.show()
    

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
    print(f'{len(entries) - people}/{len(entries):.03f} ({(len(entries) - people) / len(entries)}%) are responsible for {100 - percentiles[0] * 100}% of the PRs')

    plt.title('Closed Pull Requests Per User')
    plt.xlabel('User')
    plt.ylabel('Closed Pull Requests')
    plt.show()
    
    for entry in entries[-(len(entries) - people):]:
        # print(entry)
        j_out =  id_to_data[entry[0]]
        j_out['pull_request_count'] = entry[1]
        print(json.dumps(j_out))


if __name__ == "__main__":
    if (idx := argv.index('-i')) > -1:
        file = argv[idx + 1]
        data_path = base_data_path.format(list=file)

    # prs_over_time()
    # prs_per_project()
    prs_per_user()
