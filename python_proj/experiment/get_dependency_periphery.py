
"""
The goal of this script is to generate a list of projects that either depend
on the already included project, or where said included projects depend on.
It uses the libraries.io dependency data.
"""

from csv import reader, writer
from sys import argv
import json

import python_proj.experiment.replication_study.retrieve_pull_requests as rpr

eco = 'npm'


def do():
    # TODO: include the repository dependencies somehow?
    dependencies_path = f"./data/libraries/{eco}-libraries-1.6.0-2020-01-12/dependencies-1.6.0-2020-01-12.csv"
    dependencies_file = open(dependencies_path, "r")
    dependencies_reader = reader(dependencies_file)

    fields = [
        "ID",
        # Focal project fields.
        "Platform",
        "Project Name",
        "Project ID",
        "Version Number",
        "Version ID",

        # Other project fields; i.e., the project the dependency is on.
        "Dependency Name",
        "Dependency Platform",
        "Dependency Kind",
        "Optional Dependency",
        "Dependency Requirements",
        "Dependency Project ID"
    ]

    focal_project_name_index = fields.index("Project Name")
    focal_dependency_platform_index = fields.index("Platform")
    focal_id_index = fields.index("Project ID")
    other_project_name_index = fields.index("Dependency Name")
    other_dependency_platform_index = fields.index("Dependency Platform")
    other_id_index = fields.index("Dependency Project ID")

    # Output for filter files.
    output_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/predictors/included_projects_{o_type}.csv"

    focal_to_other_path = output_path.format(o_type="focal_to_other", eco=eco)
    focal_to_other_file = open(focal_to_other_path, "w+")
    other_to_focal_path = output_path.format(o_type="other_to_focal", eco=eco)
    other_to_focal_file = open(other_to_focal_path, "w+")

    # Output for all relevant dependencies.
    dependencies_path = f"./data/libraries/{eco}-libraries-1.6.0-2020-01-12/predictors/dependencies.json"
    dependencies_file = open(dependencies_path, "w+")

    # The filter file listing the included projects.
    filter_path = rpr.filter_path.format(filter_type="")
    filter_file = open(filter_path, "r")
    included_projects = {entry.strip().split(
        "/")[-1].lower() for entry in filter_file}

    # Collects all relevant dependencies and stores them in a temporary file.
    dependencies = {}
    projects_that_core_depends_on = set()
    projects_that_depend_on_core = set()
    for entry in dependencies_reader:
        # Only conosiders intra-ecosystem dependencies.
        if entry[focal_dependency_platform_index].lower() != eco \
                or entry[other_dependency_platform_index].lower() != eco:
            continue
        
        focal_id = entry[focal_id_index]
        other_id = entry[other_id_index]
        added_dependency = False

        # Adds projects that core projects depend on.
        focal_project_name = entry[focal_project_name_index].lower()
        if focal_project_name in included_projects:
            projects_that_core_depends_on.add(other_id)
            added_dependency = True

        # Adds projects that depend on core projects.
        other_project_name = entry[other_project_name_index].lower()
        if other_project_name in included_projects:
            projects_that_depend_on_core.add(focal_id)
            added_dependency = True

        # Adds dependency in general if it's relevant.
        if added_dependency:
            focal_id = entry[focal_id_index]
            if not focal_id in dependencies:
                dependencies[focal_id] = []
            # Skips duplicates.
            if not other_id in dependencies[focal_id]:
                dependencies[focal_id].append(other_id)

    # Combines the collected data with repository details to generate filter files.
    dependencies = {}
    id_to_repo_name = {}
    with open(rpr.input_path, "r") as input_file:
        input_reader = reader(input_file)
        project_id_index = rpr.headers.index("ID")
        repo_host_type_index = rpr.headers.index("Repository Host Type")
        repo_name_index = rpr.headers.index("Repository Name with Owner")
        platform_idx = rpr.headers.index('Platform')
        for entry in input_reader:
            # Ignores forks and projects without a repository listing.
            # Ignores non-GitHub projects.
            # Ignores non-ecosystem entries
            if not rpr.matches_inclusion_criteria(entry) \
                or entry[repo_host_type_index].lower() != 'github' \
                    or entry[platform_idx].lower() != eco:
                continue

            repo_id = entry[project_id_index]
            repo_name = entry[repo_name_index]

            added_dependency = False

            if repo_id in projects_that_core_depends_on:
                focal_to_other_file.write(f'{repo_name}\n')
                added_dependency = True

            if repo_id in projects_that_depend_on_core:
                other_to_focal_file.write(f'{repo_name}\n')
                added_dependency = True

            # Adds id to repo name if dependency is relevant.
            if added_dependency:
                id_to_repo_name[repo_id.strip()] = repo_name.strip()

    # Generates general dependency file.
    stringified_dependencies = {}
    dependency_count = 0
    for focal_id, other_ids in dependencies.items():
        if not focal_id in id_to_repo_name:
            continue

        focal_name = id_to_repo_name[focal_id]
        stringified_dependencies[focal_name] = []
        for other_id in other_ids:
            if not other_id in id_to_repo_name:
                continue

            other_name = id_to_repo_name[other_id]
            stringified_dependencies[focal_name].append(other_name)

            dependency_count += 1
            if dependency_count % 1000 == 0:
                print(
                    f"Added dependency from {focal_name} to {other_name} ({dependency_count}).")

    dependencies_file.write(json.dumps(stringified_dependencies, indent=2))

    # Closes all relevant files again.
    focal_to_other_file.close()
    other_to_focal_file.close()
    filter_file.close()
    dependencies_file.close()


def remove_default_inclusion_list():
    filter_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/predictors/included_projects{o_type}.csv"

    general_path = filter_path.format(o_type="", eco=eco)
    general_file = open(general_path, "r")
    general_inclusion = {entry.strip() for entry in general_file}

    def __filter(o_type: str = ""):
        actual_otuput_path = filter_path.format(o_type=o_type, eco=eco)
        filter_file = open(actual_otuput_path, "r")
        inclusion_list = {entry.strip() for entry in filter_file}
        return inclusion_list.difference(general_inclusion)

    focal_to_other = __filter("_focal_to_other")
    other_to_focal = __filter("_other_to_focal")

    def __write(name: str, entries: set):
        output_path = filter_path.format(eco=eco, o_type=f"{name}_without_core")
        with open(output_path, "w+") as output_file:
            for entry in entries:
                output_file.write(f'{entry}\n')

    __write("_focal_to_other", focal_to_other)
    __write("_other_to_focal", other_to_focal)


if __name__ == "__main__":
    try:
        eco = argv[argv.index("-e") + 1]
    except:
        eco = 'npm'

    print(f'Starting with ecosystem: {eco}.')

    do()
    remove_default_inclusion_list()
