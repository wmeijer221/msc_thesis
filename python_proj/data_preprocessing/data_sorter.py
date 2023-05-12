"""
Implements sorting alorithm to iterate through time series event gathered with GrimoireLab chronologically.
"""

from datetime import datetime
import json
from os import path, makedirs, remove

from python_proj.utils.arg_utils import safe_get_argv, get_argv
from python_proj.utils.mt_utils import parallelize_tasks

base_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/{feature}/"
input_file_name = "{owner}--{repo_name}{ext}.json"
output_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/{feature}/sorted{filter_name}.json"
real_base_path = None
thread_count = 1


temp_storage_path = "./data/temp/sorting_buckets/{bucket}.dat"
temp_dir = path.dirname(temp_storage_path.format(bucket="0"))
if not path.exists(temp_dir):
    makedirs(temp_dir)


def _get_nested(dictionary: dict, recursive_key: list[str]):
    current = dictionary
    for key in recursive_key:
        if not key in current:
            return None
        current = current[key]
    return current


def _iterate_and_split(filter_path: str, datetime_key: list[str], ext: str) -> set[str]:
    ymds = set()
    with open(filter_path, "r") as filter_file:
        for file in filter_file:
            # Creates file path.
            repo_split = file.strip().split("/")
            owner = repo_split[0]
            repo_name = repo_split[-1]
            entries_path = real_base_path + \
                input_file_name.format(
                    owner=owner, repo_name=repo_name, ext=ext)
            if not path.exists(entries_path):
                print(f'Skipping {repo_split} as it does not exist.')
                continue
            # Iterates through entries.
            with open(entries_path, "r") as entries_file:
                try:
                    j_data = json.loads(entries_file.read())
                except json.JSONDecodeError:
                    print(f'Json decode error with: {entries_path}')
                    raise
                for entry in j_data:
                    try:
                        closed_at = _get_nested(entry, datetime_key)
                        if closed_at is None:
                            print(
                                f'Skipping entry without key "{datetime_key}" {repo_split}.')
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
                        entry['__source_path'] = entries_path
                        with open(r_temp_storage_path, "a+") as temp_storage_file:
                            temp_storage_file.write(f'{json.dumps(entry)}\n')
                    except:
                        print(json.dumps(entry))
                        raise
    return ymds


def _parallel_sort(ymds: set[str]):
    def _sort_key(entry: dict):
        return _get_nested(entry, datetime_key)

    def _sort_entries(task: str, task_id: int, total_tasks: int):
        ymd = task
        print(f'Starting with task ({task_id}/{total_tasks}) "{ymd}"')
        bucket_path = temp_storage_path.format(bucket=ymd)
        # Reads unsorted data
        with open(bucket_path, "r") as bucket_file:
            entries = [json.loads(line.strip()) for line in bucket_file]
        remove(bucket_path)
        entries.sort(key=_sort_key)
        # Writes sorted data
        with open(bucket_path, 'w+') as bucket_file:
            newlines = [f'{json.dumps(entry)}\n' for entry in entries]
            bucket_file.writelines(newlines)

    parallelize_tasks(ymds, _sort_entries, thread_count)


def _write_sorted_buckets(ymds: set, filter_name: str):
    sorted_ymds = list(ymds)
    sorted_ymds.sort()
    r_output_path = output_path.format(
        eco=eco_name, feature=feature_name, filter_name=filter_name)
    with open(r_output_path, "a+") as output_file:
        for ymd in sorted_ymds:
            bucket_path = temp_storage_path.format(bucket=ymd)
            with open(bucket_path, "r") as bucket_file:
                output_file.writelines(bucket_file)
            remove(bucket_path)
    print(f'Stored it at: {r_output_path}')


def sort_data(file_name: str, datetime_key: list[str], feature_name: str, eco_name: str, ext: str, filter_name: str):
    global real_base_path, input_file_name
    real_base_path = base_path.format(eco=eco_name, feature=feature_name)

    print("Starting bucket creation.")
    ymds = _iterate_and_split(file_name, datetime_key, ext)

    print("Starting parallel bucket sort.")
    _parallel_sort(ymds)

    print("Merging buckets.")
    _write_sorted_buckets(ymds, filter_name)
    print("Done!")


if __name__ == "__main__":
    datetime_key = get_argv("-k").strip().split(",")
    filter_file = get_argv("-d")
    eco_name = get_argv('-e')
    feature_name = get_argv('-f')
    thread_count = int(get_argv('-t'))
    ext = safe_get_argv("-x", default="")
    filter_name = safe_get_argv("-n", default="")

    sort_data(filter_file, datetime_key, feature_name,
              eco_name, ext, filter_name)
