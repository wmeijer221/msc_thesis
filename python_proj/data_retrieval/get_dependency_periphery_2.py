"""
Generates project lists for dependency and inverse dependency projects.


Periphery 2 counts, using all included projects filtering 
for all previously used fitlers.
Counts (after filtering):
len(potential_dependency_projects)=24559
len(potential_inv_dependency_projects)=372428

Considering inv dep project have 53% fewer projects, we'd have
to sample (24559 / 0.53) = 51550 projects.
There's no time for this probably, so we'll sample half of this; i.e.:
12280 dependency projects.
25775 inv dependency projects.
"""


import random

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import OpenMany
from python_proj.utils.arg_utils import get_argv

from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import safe_load_dependency_map


def get_dependency_periphery(
        source_project_list_name: str,
        filter_project_list_names: list[str],
        dependency_projects_out_name: str,
        inv_dependency_projects_out_name: str,
        dep_sample_size: int,
        inv_sample_size: int):

    # loads source
    source_project_list_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids', owner='proj', repo='list', ext=source_project_list_name)
    with open(source_project_list_path, "r", encoding='utf-8') as source_project_file:
        projects = {entry.strip() for entry in source_project_file}

    # loads projects
    filter_project_paths = [exp_utils.FILTER_PATH(filter_type=entry)
                            for entry in filter_project_list_names]
    with OpenMany(filter_project_paths, "r", encoding='utf-8') as filter_project_files:
        filtered_projects = set()
        for filter_project_file in filter_project_files:
            for entry in filter_project_file:
                entry = entry.strip()
                filtered_projects.add(entry)

    dependencies, inv_dependencies, project_name_to_id = safe_load_dependency_map()
    project_id_to_name = {id: name for name, id in project_name_to_id.items()}

    # Creates list of dependency projects.
    potential_dependency_projects = set()
    potential_inv_dependency_projects = set()
    for project_name in projects:
        if not project_name in project_name_to_id:
            continue
        project_id = project_name_to_id[project_name]

        # Adds project dependencies
        if project_id in dependencies:
            project_dependencies = dependencies[project_id]
            for source_project in project_dependencies:
                # Ignores filtered projects (i.e., previously collected ones)
                if source_project in filtered_projects \
                        or source_project not in project_id_to_name:
                    continue
                potential_dependency_projects.add(source_project)

        # Adds inverse dependencies.
        if project_id in inv_dependencies:
            # Adds inverse project dependencies
            inv_project_dependencies = inv_dependencies[project_id]
            for sink_project in inv_project_dependencies:
                # Ignores filtered projects (i.e., previously collected ones)
                # or when there's no id to the name.
                if sink_project in filtered_projects \
                        or sink_project not in project_id_to_name:
                    continue
                potential_inv_dependency_projects.add(sink_project)

    print(f'{len(potential_dependency_projects)=}')
    print(f'{len(potential_inv_dependency_projects)=}')

    # Writes dependencies
    dependency_output_path = exp_utils.FILTER_PATH(
        filter_type=dependency_projects_out_name)
    with open(dependency_output_path, "w+", encoding='utf-8') as dep_out_file:
        dep_sample = random.sample(
            potential_dependency_projects, dep_sample_size)
        for project_id in dep_sample:
            project_name = project_id_to_name[project_id]
            dep_out_file.write(f'{project_name}\n')

    # Writes inv dependencies
    inv_dependency_output_path = exp_utils.FILTER_PATH(
        filter_type=inv_dependency_projects_out_name)
    with open(inv_dependency_output_path, "w+", encoding='utf-8') as inv_dep_out_file:
        inv_dep_sample = random.sample(
            potential_inv_dependency_projects, inv_sample_size)
        for project_id in inv_dep_sample:
            project_name = project_id_to_name[project_id]
            inv_dep_out_file.write(f'{project_name}\n')


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()

    __source_project_list_name = get_argv(key="-s")
    __filter_project_list_names = [entry.strip()
                                   for entry in get_argv(key='-f').split(",")]

    __dependency_projects_out_name = get_argv(key='-do')
    __inv_dependency_projects_out_name = get_argv(key="-io")

    __dep_sample_size = get_argv(key='-ds')
    __inv_dep_sample_size = get_argv(key='-is')

    get_dependency_periphery(__source_project_list_name,
                             __filter_project_list_names,
                             __dependency_projects_out_name,
                             __inv_dependency_projects_out_name,
                             __dep_sample_size,
                             __inv_dep_sample_size)
