"""
Counts the number of projects that are dependent on and the number
of projects that have a dependency within the dataset.


"""

import csv

from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import safe_load_dependency_map

from python_proj.utils.util import invert_dict
from python_proj.utils.arg_utils import get_argv
import python_proj.utils.exp_utils as exp_utils

exp_utils.load_paths_for_eco()

# data loading
data_file_path = get_argv(key='-f')
data_file = open(data_file_path, "r", encoding='utf-8')
csv_reader = csv.reader(data_file)

# Finds relevant index.
header = next(csv_reader)
proj_idx = header.index('Project Name')

dependency_mapping, project_name_to_id = safe_load_dependency_map()

# loads relevant projects.
unique_projects = set()
for entry in csv_reader:
    project_name = entry[proj_idx].lower()
    if not project_name in project_name_to_id:
        continue
    proj_id = project_name_to_id[project_name]
    unique_projects.add(proj_id)
project_id_to_name = invert_dict(project_name_to_id)
del project_name_to_id

incoming_dependencies = set()
outgoing_dependencies = set()
for project_id in unique_projects:
    if not project_id in dependency_mapping:
        continue

    # Tests whether dependnecy is in dataset.
    dependencies = dependency_mapping[project_id]
    for dependency_id in dependencies:
        if dependency_id in unique_projects:
            incoming_dependencies.add(dependency_id)
            outgoing_dependencies.add(project_id)
            break
del dependency_mapping

print(f'{len(outgoing_dependencies)=}, {len(incoming_dependencies)=}.')

with open("./tmp_incoming_dependencies.txt", "w+", encoding='utf-8') as output_file:
    lines = [project_id_to_name[project_id] for project_id in incoming_dependencies]
    output_file.writelines(lines)
    