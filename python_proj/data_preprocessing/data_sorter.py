"""
Implements sorting alorithm to iterate through time series event gathered with GrimoireLab chronologically.

It speeds up the whole process by generating buckets of data based on dd-mm-yy timestamps, which are then 
sorted in parallel.
Ultimately, these sorted files are then merged into one chronological data file.
"""

from datetime import datetime
from functools import partial
import json
from os import path, makedirs, remove

from python_proj.utils import *


def _iterate_and_split(filter_path: str,
                       input_data_path: partial[str],
                       datetime_key: list[str],
                       temp_storage_path: str) \
        -> set[str]:
    ymds = set()
    with open(filter_path, "r") as filter_file:
        # Iterates through all included files.
        for file in filter_file:
            # Creates file path.
            repo_split = file.strip().split("/")
            owner = repo_split[0]
            repo_name = repo_split[-1]
            entries_path = input_data_path(repo=repo_name, owner=owner)
            if not path.exists(entries_path):
                print(f'Skipping {repo_split} as it does not exist.')
                continue

            # Loads the issue/PR data file.
            with open(entries_path, "r") as entries_file:
                try:
                    j_data = json.loads(entries_file.read())
                except json.JSONDecodeError:
                    print(f'Json decode error with: {entries_path}')
                    raise

                # Iterates through pulls/issues in the input file.
                for entry in j_data:
                    try:
                        event_timestamp = utils.get_nested(entry, datetime_key)
                        if event_timestamp is None:
                            print(
                                f'Skipping entry without key "{datetime_key}" {repo_split}.')
                            continue

                        # HACK: Preserves original file path so you can filter
                        # data to its owner/repo tuple.
                        entry['__source_path'] = entries_path

                        # Loads used timestamp, which is used to create a data bucket.
                        dt_event_timestamp = datetime.strptime(
                            event_timestamp, "%Y-%m-%dT%H:%M:%SZ")
                        ymd = dt_event_timestamp.strftime("%Y-%m-%d")
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


def _parallel_sort(ymds: set[str],
                   temp_storage_path: str,
                   datetime_key: list[str],
                   thread_count: int):
    
    def _sort_key(entry: dict):
        return utils.get_nested(entry, datetime_key)

    def _sort_entries(task: str, task_id: int, total_tasks: int, *args, **kwargs):
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

    mt_utils.parallelize_tasks(ymds, _sort_entries, thread_count)


def _write_sorted_buckets(ymds: set,
                          output_path: str,
                          temp_storage_path: str):
    sorted_ymds = list(ymds)
    sorted_ymds.sort()
    with open(output_path, "a+") as output_file:
        for ymd in sorted_ymds:
            bucket_path = temp_storage_path.format(bucket=ymd)
            with open(bucket_path, "r") as bucket_file:
                output_file.writelines(bucket_file)
            remove(bucket_path)
    print(f'Stored it at: {output_path}')


def sort_data(filter_path: str,
              input_data_path: partial[str],
              datetime_key: list[str],
              output_path: str,
              temp_storage_path: str,
              thread_count: int):

    print("Starting bucket creation.")
    ymds = _iterate_and_split(filter_path, input_data_path,
                              datetime_key, temp_storage_path)

    print("Starting parallel bucket sort.")
    _parallel_sort(ymds, temp_storage_path,
                   datetime_key, thread_count)

    print("Merging buckets.")
    _write_sorted_buckets(ymds, output_path,
                          temp_storage_path)

    print("Done!")


def cmd_data_sorter():
    """
    Cmd params:
    -x: extension of the entered raw data files.
    -n: output file name.
    -q: filter file name.
    -k: date time key.
    -t: thread_count
    -d: data source type
    -e: ecosystem
    """
    
    # Does partial exp_utils init.
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    # Loads file name for input files.
    entries_ext = arg_utils.safe_get_argv(key="-x", default="")
    entries_path = partial(exp_utils.RAW_DATA_PATH, ext=entries_ext)

    # Loads name for chronological data file (i.e., the output file).
    # TODO: replace this with ``exp_utils``
    chrono_file_name = arg_utils.safe_get_argv(key="-n", default="")
    chrono_file_name = f'sorted{chrono_file_name}'
    chrono_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        file_name=chrono_file_name)

    # Loads the relevant filter file.
    filter_type = arg_utils.safe_get_argv(key="-q", default="")
    filter_path = exp_utils.FILTER_PATH(filter_type=filter_type)

    # Loads other arguments.
    datetime_key = arg_utils.get_argv(key="-k").strip().split(",")
    thread_count = arg_utils.safe_get_argv(key="-t", default=1, data_type=int)

    # Sets the temporary storage location.
    temp_storage_path = exp_utils.BASE_PATH + \
        "temp/sorting_buckets/{bucket}.dat"
    temp_dir = path.dirname(temp_storage_path.format(bucket="0"))
    if not path.exists(temp_dir):
        makedirs(temp_dir)

    # Runs the whole thing!
    sort_data(filter_path, entries_path, datetime_key,
              chrono_path, temp_storage_path, thread_count)


if __name__ == "__main__":
    cmd_data_sorter()
