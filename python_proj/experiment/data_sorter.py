"""
Implements sorting alorithm to iterate through time series event gathered with GrimoireLab chronologically.
"""

from datetime import datetime
import json
from os import path, makedirs, remove
from sys import argv

from python_proj.experiment.util import parallelize_tasks

base_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/{feature}/"
input_file_name = "{owner}--{repo_name}.json"
output_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/{feature}/sorted.json"
real_base_path = None
thread_count = 1


temp_storage_path = "./data/temp/sorting_buckets/{bucket}.dat"
temp_dir = path.dirname(temp_storage_path.format(bucket="0"))
if not path.exists(temp_dir):
    makedirs(temp_dir)


def get_nested(dictionary: dict, recursive_key: list[str]):
    current = dictionary
    for key in recursive_key:
        if not key in current:
            return None
        current = current[key]
    return current


def iterate_and_split(filter_path: str, datetime_key: list[str]) -> set[str]:
    ymds = set()
    with open(filter_path, "r") as filter_file:
        for file in filter_file:
            # Creates file path.
            repo_split = file.strip().split("/")
            owner = repo_split[0]
            repo_name = repo_split[-1]
            entries_path = real_base_path + \
                input_file_name.format(owner=owner, repo_name=repo_name)
            if not path.exists(entries_path):
                print(f'Skipping {repo_split} as it does not exist.')
                continue
            # Iterates through entries.
            with open(entries_path, "r") as entries_file:
                j_data = json.loads(entries_file.read())
                for entry in j_data:
                    try:
                        closed_at = get_nested(entry, datetime_key)
                        if closed_at is None:
                            print(
                                f'Skipping entry without closed date {repo_split}.')
                            continue
                        try:
                            # Used in GitHub
                            dt_closed_at = datetime.strptime(
                                closed_at, "%Y-%m-%dT%H:%M:%SZ")
                        except:
                            # Used in GitLab.
                            dt_closed_at = datetime.strptime(
                                closed_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                            )
                        ymd = dt_closed_at.strftime("%Y-%m-%d")
                        if not ymd in ymds:
                            ymds.add(ymd)
                        r_temp_storage_path = temp_storage_path.format(
                            bucket=ymd)
                        with open(r_temp_storage_path, "a+") as temp_storage_file:
                            temp_storage_file.write(f'{json.dumps(entry)}\n')
                    except:
                        print(json.dumps(entry))
                        raise
    return ymds


def parallel_sort(ymds: set[str]):
    def sort_key(entry: dict):
        return get_nested(entry, datetime_key)

    def sort_entries(ymd: str):
        bucket_path = temp_storage_path.format(bucket=ymd)
        with open(bucket_path, "w") as bucket_file:
            entries = [json.loads(line.strip()) for line in bucket_file]
            entries.sort(key=sort_key)
            newlines = [f'{json.dumps(entry)}\n' for entry in entries]
            bucket_file.writelines(newlines)

    parallelize_tasks(ymds, sort_entries, thread_count)


def write_sorted_buckets(ymds: set):
    sorted_ymds = list(ymds)
    sorted_ymds.sort()
    r_output_path = output_path.format(eco=eco_name, feature=feature_name)
    with open(r_output_path, "a+") as output_file:
        for ymd in sorted_ymds:
            bucket_path = temp_storage_path.format(bucket=ymd)
            with open(bucket_path, "r") as bucket_file:
                output_file.writelines(bucket_file)
            remove(bucket_path)


def sort_data(file_name: str, datetime_key: list[str], feature_name: str, eco_name: str):
    global real_base_path, input_file_name
    real_base_path = base_path.format(eco=eco_name, feature=feature_name)
    ymds = iterate_and_split(file_name, datetime_key)
    parallel_sort(ymds)
    write_sorted_buckets(ymds)


if __name__ == "__main__":
    datetime_key = argv[argv.index("-k") + 1].strip().split(",")
    filter_file = argv[argv.index("-d") + 1]
    eco_name = argv[argv.index('-e') + 1]
    feature_name = argv[argv.index('-f') + 1]
    thread_count = int(argv[argv.index('-t') + 1])
    sort_data(filter_file, datetime_key, feature_name, eco_name)
