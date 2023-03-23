from os import path, makedirs
from joblib import Parallel, delayed
import datetime
import math
from csv import reader
import itertools
from sys import argv
from time import sleep

import python_proj.experiment.replication_study.filter_projects as fp
from python_proj.experiment.util import safe_index

input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/"


job_count = -1
chunk_size = -1
total_lines = -1


if not path.exists(output_path):
    makedirs(output_path)

with open(input_path, "r", encoding="utf-8") as input_file:
    in_memory_file = input_file.read().splitlines()
    for count, _ in enumerate(in_memory_file):
        pass
    total_lines = count


def calculate(index: int, is_final_chunk: bool, output_file):
    chunk_start = index * chunk_size
    chunk_end = total_lines if is_final_chunk else (index + 1) * chunk_size

    print(f"Thread {index} - {chunk_start}:{chunk_end}")

    input_reader = reader(in_memory_file, quotechar='"')
    
    for entry in itertools.islice(input_reader, chunk_start, chunk_end):
        repo_name = entry[fp.repo_name_index]
        if repo_name == '':
            continue

        # print(f'Starting with {repo_name}')

        proj_name = entry[fp.proj_name_index]
        failed = True
        while failed:
            try:
                suff_dls = fp.has_sufficient_monthly_downloads(
                    fp.download_start_date, fp.download_end_date, proj_name, 10000)
                failed = False
            except:
                print("Something went wrong...")
                sleep(5)

        if not suff_dls:
            continue

        print(f"Found one: {repo_name}.")
        output_file.writeline(f'{repo_name}\n')
        output_file.flush()
        sleep(1)

    output_file.close()


def run(job_count, cs: int = None):
    global chunk_size, total_lines

    if cs == None:
        chunk_size = math.floor(total_lines % job_count)
    else:
        # Indicates a test run.
        chunk_size = cs
        total_lines = cs * job_count

    print(f'Running with {job_count=}, {chunk_size=}.')

    o_file = [
        open(f"{output_path}included_projects_dl_{index}.csv", "w+", encoding="utf-8")
        for index in range(job_count)
    ]

    start = datetime.datetime.now()
    Parallel(n_jobs=job_count)(delayed(calculate)(i, i == job_count - 1, o_file[i])
                               for i in range(job_count))
    delta_time = datetime.datetime.now() - start
    print(f'{delta_time=}')
    return delta_time


if __name__ == "__main__":
    if (m_index := safe_index(argv, "-m")) >= 0:
        mode = argv[m_index + 1].lower()
        print(f'Starting in mode {mode}.')

        if mode == "t":
            thread_tests = [int(entry)
                            for entry in argv[argv.index("-t") + 1].split(",")]
            print(f'Testing with threads: {thread_tests}.')
            cs = int(argv[argv.index("-c") + 1])
            results = {}
            for thread in thread_tests:
                delta_time = run(thread, cs=cs)
                results[thread] = delta_time
            print(f'{results=}')

        elif mode == "r":
            threads = argv[argv.index("-t") + 1]
            run(threads)
        else:
            raise ValueError(f"Invalid mode {mode}.")
