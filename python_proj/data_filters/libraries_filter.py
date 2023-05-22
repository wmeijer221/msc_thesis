"""
This script split the data in https://libraries.io/data (version 1.6.0)
into separate files for each of the libraries instead of on.

To get this to work:
1. Download the dataset and extract it at
   ``./data/libraries/libraries-1.6.0-2020-01-12``
2. Run this script.
3. Wait...
"""

import csv
from os import makedirs, path, remove
from sys import maxsize
from typing import Dict, Any

from python_proj.utils.exp_utils import BASE_PATH

csv.field_size_limit(maxsize)

suffix = "-1.6.0-2020-01-12"
input_path = f"{BASE_PATH}libraries/libraries{suffix}"
data_input_path = BASE_PATH + "libraries/libraries{suffix}/{data_file}{suffix}.csv"
output_path = BASE_PATH + "libraries/{platform}-libraries{suffix}"
file_path = "{folder_path}/{file_name}{suffix}.csv"

platform_filter = ["npm"]

data_files = ["dependencies", "projects_with_repository_fields",
              "repository_dependencies", "tags", "versions"]

# platform -> (datatype -> outputfile)
platform_files: Dict[str, Dict[str, Any]] = {}

# Helper mapings.
project_id_to_platform: Dict[int, str] = {}
project_repo_id_to_platform: Dict[int, str] = {}


class Devnull(object):
    """
    Helper class for writing to non-files.
    """

    def write(self, *_):
        pass


def add_new_platform(platform: str):
    """
    Creates folder and files for a platform.
    """

    is_tracked_platform = platform.lower() in platform_filter

    folder_path = output_path.format(platform=platform, suffix=suffix).lower()
    if is_tracked_platform and not path.exists(folder_path):
        makedirs(folder_path)

    def make_file(file_name: str):
        if not is_tracked_platform:
            return Devnull()

        output_path = file_path.format(
            folder_path=folder_path,
            file_name=file_name,
            suffix=suffix)

        if path.exists(output_path):
            remove(output_path)
        return open(output_path, "a+", encoding="utf-8", newline="")

    platform_files[platform] = {key: csv.writer(
        make_file(key), quotechar='"') for key in data_files}


def split_projects():
    """
    Splits the ``projects`` file and fills helper mappings
    with data so the data files can be split.
    """

    print(f'Starting with: projects_with_repository_fields.')
    add_new_platform("unknown")
    file_name = "projects_with_repository_fields"
    with open(f"{input_path}/{file_name}{suffix}.csv", "r", encoding="utf-8") as project_in:
        csv_reader = csv.reader(project_in, quotechar='"')
        next(csv_reader)
        for entry in csv_reader:
            platform = entry[1]
            if not platform in platform_files:
                add_new_platform(platform)
            # Adds helper mappings.
            project_id_to_platform[entry[0]] = entry[1]
            project_repo_id_to_platform[entry[20]] = entry[1]
            # Writes entry to platform file.
            csv_writer = platform_files[platform][file_name]
            csv_writer.writerow(entry)


def write_header(data_file: str, header: list):
    """
    Writes the header in all the platforms' data files.
    """

    for files in platform_files.values():
        files[data_file].writerow(header)


# Per data file, has a map to identify an entry's platform.
project_key = {
    # "projects_with_repository_fields": lambda entry: entry[1],
    "versions": lambda entry: entry[1],
    # "repositories": lambda entry: project_repo_id_to_platform[entry[0]],
    "tags": lambda entry: project_repo_id_to_platform[entry[3]],
    "repository_dependencies": lambda entry: project_repo_id_to_platform[entry[3]],
    "dependencies": lambda entry: entry[1],
}


def split_data():
    """
    Split the data files per platform.
    """

    for data_file, get_platform in project_key.items():
        print(f'Starting with: {data_file}.')
        with open(data_input_path.format(data_file=data_file, suffix=suffix), "r", encoding="utf-8") as input_file:
            csv_reader = csv.reader(input_file, quotechar='"')
            header = next(csv_reader)
            write_header(data_file, header)
            for entry in csv_reader:
                try:
                    platform = get_platform(entry)
                except KeyError:
                    platform = "unknown"
                csv_writer = platform_files[platform][data_file]
                csv_writer.writerow(entry)


if __name__ == "__main__":
    split_projects()
    split_data()

# licenses, repository, repository ID, repository host type, repository name with owner, repository fork, repository created, repository issues, repository license, repository status, repository pull requests enabled
