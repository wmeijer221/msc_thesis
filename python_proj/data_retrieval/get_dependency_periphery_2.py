

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import OpenMany
from python_proj.utils.arg_utils import get_argv

from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import safe_load_dependency_map


def get_dependency_periphery(
        source_project_list_name: str,
        filter_project_list_names: list[str]):

    # loads source
    source_project_list_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids', owner='proj', repo='list', ext=source_project_list_name)
    with open(source_project_list_path, "r", encoding='utf-8') as source_project_file:
        projects = {entry.strip() for entry in source_project_file}

    # loads projects
    filter_project_paths = [exp_utils.FILTER_PATH(filter_name=entry)
                            for entry in filter_project_list_names]
    with OpenMany(filter_project_paths, "r", encoding='utf-8') as filter_project_files:
        filtered_projects = set()
        for filter_project_file in filter_project_files:
            for entry in filter_project_file:
                entry = entry.strip()
                filtered_projects.add(entry)

    dependencies, inv_dependencies, project_name_to_id = safe_load_dependency_map()

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
                if source_project in filtered_projects:
                    continue
                potential_dependency_projects.add(source_project)

        # Adds inverse dependencies.
        if project_id in inv_dependencies:
            # Adds inverse project dependencies
            inv_project_dependencies = inv_dependencies[project_id]
            for sink_project in inv_project_dependencies:
                # Ignores filtered projects (i.e., previously collected ones)
                if sink_project in filtered_projects:
                    continue
                potential_inv_dependency_projects.add(sink_project)

    print(f'{len(potential_dependency_projects)=}')
    print(f'{len(potential_inv_dependency_projects)=}')


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()

    __source_project_list_name = get_argv(key="-s")
    __filter_project_list_names = [entry.strip()
                                   for entry in get_argv(key='-f').split(",")]

    get_dependency_periphery(__source_project_list_name,
                             __filter_project_list_names)
