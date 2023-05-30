"""
Implements two testing scripts, one to test different pull 
request threshold settings, and one to count comments per user.
"""

import json

from python_proj.utils.arg_utils import safe_get_argv
import python_proj.utils.exp_utils as exp_utils

exp_utils.load_paths_for_all_argv()
input_path = exp_utils.CHRONOLOGICAL_DATASET_PATH


def test_pr_thresholds(thresholds: list[int]) -> dict[str, int]:
    input_file = open(input_path, "r")

    pr_counts = {}

    for line in input_file:
        entry = json.loads(line)
        src = entry["__source_path"]
        if src not in pr_counts:
            pr_counts[src] = 0
        pr_counts[src] += 1

    # tested_thresholds = [5, 15, 30]
    entries_per_threshold = {t: (0, 0) for t in thresholds}

    for _, entry in pr_counts.items():
        for threshold in thresholds:
            if entry >= threshold:
                old_count = entries_per_threshold[threshold]
                new_count = (old_count[0] + 1, old_count[1] + entry)
                entries_per_threshold[threshold] = new_count

    print(entries_per_threshold)
    return pr_counts


def build_filter_list_from_pr_counts(pr_counts: dict[str, int],
                                     output_path: str):
    with open(output_path, "w+") as output_file:
        for project in pr_counts.keys():
            (owner, repo) = exp_utils.get_owner_and_repo_from_source_path(project)
            filter_entry = f'{owner}/{repo}\n'
            output_file.write(filter_entry)


def count_comments_per_user():
    input_file = open(input_path, "r")

    count = {}

    for line in input_file:
        entry = json.loads(line)

        cdata_key = "comments_data"
        if cdata_key not in entry:
            continue

        for comment in entry[cdata_key]:
            user_id = comment["user_data"]["id"]
            if user_id not in count:
                count[user_id] = 0
            count[user_id] += 1

    print(count)


def test_duplicate_entries(input_path: str):
    unique = set()
    dupes = 0
    with open(input_path, 'r') as input_file:
        for entry in input_file:
            j_entry = json.loads(entry)
            unique_key = f'{j_entry["__source_path"]}--{j_entry["id"]}'
            if unique_key in unique:
                dupes += 1
            else:
                unique.add(unique_key)
    print(f'{dupes=}, {len(unique)=}.')


if __name__ == "__main__":
    mode = safe_get_argv('-m', default="t")

    match mode:
        case "t":
            ts_arg = safe_get_argv('-t', default="5,15,30")
            thresholds = [int(entry) for entry in ts_arg.split(",")]
            pr_counts = test_pr_thresholds(thresholds)
        case "c":
            count_comments_per_user()
        case "f":
            threshold = safe_get_argv('-t', default=5, data_type=int)
            output_file_name = safe_get_argv(key="-o", default="")
            output_path = f'{exp_utils.BASE_PATH}/predictions/included_projects_{output_file_name}_{threshold}.csv'
            pr_counts = test_pr_thresholds([threshold])
            build_filter_list_from_pr_counts(pr_counts, output_path)
        case "d":
            test_duplicate_entries(input_path)
