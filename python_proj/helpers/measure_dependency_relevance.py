
"""
When observing the data collection process, it becomes apparent that
periphery projects are sampled from a list of projects that is filtered
after collecting the periphery. A consequence of this is that the collected 
projects potentially have no dependencies on the core set of projects, 
which could be problematic for the results.

This script identifies how many of these projects have a dependency on the 
core projects and thus how much of a problem this actually is.

"""

import json

from python_proj.utils.arg_utils import get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import OpenMany

from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import safe_load_dependency_map


def calculate_periphery_to_core_dependencies(
    included_projects_filter_name: str,
    core_filter_name: str,
    periphery_filter_names: list[str]
):
    """
    Calculates the number of projects that have a dependency.
    Included projects  represent the projects that are actually part of the data set (i.e., post-filter).
    Core and periphery projects speak for themselves.
    """

    exp_utils.load_paths_for_eco()

    dependency_map, inv_dependency_map, project_name_to_id_map = safe_load_dependency_map()

    included_projects_filter_path = exp_utils.RAW_DATA_PATH(
        data_type="user-ids",
        owner='proj',
        repo="list",
        ext=included_projects_filter_name
    )
    with open(included_projects_filter_path, "r", encoding='utf-8') as included_projects_file:
        included_projects = {project_name_to_id_map[entry.strip().lower()]
                             for entry in included_projects_file
                             if entry.strip().lower() in project_name_to_id_map}

    core_filter_path = exp_utils.FILTER_PATH(filter_type=core_filter_name)
    with open(core_filter_path, "r", encoding='utf-8') as core_file:
        core_projects = {project_name_to_id_map[entry.strip().lower()]
                         for entry in core_file
                         if entry.strip().lower() in project_name_to_id_map}

    periphery_filter_paths = [exp_utils.FILTER_PATH(filter_type=filter_name)
                              for filter_name in periphery_filter_names]

    no_mapping_key = 'No Mapping'
    not_included_key = 'Not Included'
    dependency_counter = {proj: {'dep': 0, 'inv_dep': 0, no_mapping_key: 0, not_included_key: 0}
                          for proj in periphery_filter_paths}

    with OpenMany(periphery_filter_paths, "r", encoding='utf-8') as periphery_files:
        for (periphery_file, filter_path) in zip(periphery_files, periphery_filter_paths):
            for entry in periphery_file.readlines():
                entry = entry.strip().lower()

                if not entry in project_name_to_id_map:
                    dependency_counter[filter_path][no_mapping_key] += 1
                    continue

                entry_id = project_name_to_id_map[entry]

                if not entry_id in included_projects:
                    dependency_counter[filter_path][not_included_key] += 1
                    continue

                if entry_id in dependency_map:
                    # if it has listed dependencies.
                    dependees = dependency_map[entry_id]
                    for dependee in dependees:
                        if dependee in core_projects:
                            dependency_counter[filter_path]['dep'] += 1
                            break

                if entry_id in inv_dependency_map:
                    # if it has projects depending on it.
                    inv_dependencies = inv_dependency_map[entry_id]
                    for dependee in inv_dependencies:
                        if dependee in core_projects:
                            dependency_counter[filter_path]['inv_dep'] += 1
                            break

    print("Overview of dependencies from and to the CORE dataset:\n" +
          json.dumps(dependency_counter, indent=4))

    project_paths = [*periphery_filter_paths, core_filter_path]
    with OpenMany(project_paths, "r", encoding='utf-8') as project_files:
        project_ids = set()
        for project_file in project_files:
            for entry in project_file:
                entry = entry.strip().lower()
                if not entry in project_name_to_id_map:
                    continue
                project_ids.add(entry)
        print(f'{len(project_ids)=}')

        projects_with_a_dependency = 0
        projects_with_a_dependendee = 0

        for entry in project_ids:

            if entry in dependency_map:
                dependees = dependency_map[entry]
                for dependee in dependees:
                    if dependee in project_ids:
                        projects_with_a_dependency += 1
                        break

            if entry in inv_dependency_map:
                dependees = dependency_map[entry]
                for dependee in dependees:
                    if dependee in project_ids:
                        projects_with_a_dependendee += 1
                        break

        print(f'{projects_with_a_dependency=}, {projects_with_a_dependendee=}.')


if __name__ == "__main__":
    __periphery_filter_names = [entry for entry in get_argv(
        key="-p").split(",") if entry != ""]
    __core_filter_name = get_argv(key='-f')
    __included_projects_name = get_argv(key='-i')

    calculate_periphery_to_core_dependencies(
        __included_projects_name,
        __core_filter_name,
        __periphery_filter_names)
