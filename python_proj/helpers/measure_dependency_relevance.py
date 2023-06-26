
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

from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import load_dependency_map


def calculate_periphery_to_core_dependencies():
    exp_utils.load_paths_for_eco()
    dependency_map, inv_dependency_map, project_name_to_id_map = load_dependency_map()

    periphery_filters = [entry for entry in get_argv(
        key="-p").split(",") if entry != ""]
    core_filter = get_argv(key='-f')

    periphery_filter_paths = [exp_utils.FILTER_PATH(filter_name=filter_name)
                              for filter_name in periphery_filters]
    core_filter_path = exp_utils.FILTER_PATH(filter_name=core_filter)

    with open(core_filter_path, "r", encoding='utf-8') as core_file:
        core_projects = {project_name_to_id_map[entry.strip()]
                         for entry in core_file}

    dependency_counter = {proj: {'dep': 0, 'inv_dep': 0}
                          for proj in periphery_filter_paths}
    no_mapping_key = 'No Mapping'
    dependency_counter[no_mapping_key] = 0

    with OpenMany(periphery_filter_paths, "r", encoding='utf-8') as periphery_files:
        for (periphery_file, filter_path) in zip(periphery_files, periphery_filter_paths):
            for entry in periphery_file.readlines():
                entry = entry.strip()

                if not entry in project_name_to_id_map:
                    dependency_counter[no_mapping_key] += 1
                    continue

                entry_id = project_name_to_id_map[entry]
                dependencies = dependency_map[entry_id]
                for dependency in dependencies:
                    if dependency in core_projects:
                        dependency_counter[filter_path]['dep'] += 1
                        break
                inv_dependencies = inv_dependency_map[entry_id]
                for dependency in inv_dependencies:
                    if dependency in core_projects:
                        dependency_counter[filter_path]['inv_dep'] += 1
                        break

    print(json.dumps(dependency_counter, indent=4))
    return dependency_counter


if __name__ == "__main__":
    calculate_periphery_to_core_dependencies()
