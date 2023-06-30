
from python_proj.data_preprocessing.sliding_window_features.dependent_ecosystem_experience import safe_load_dependency_map


dep, inv_dep, proj_to_id = safe_load_dependency_map()

self_dependencies = 0
for project, dependencies in dep.items():
    if project in dependencies:
        self_dependencies += 1


self_inv_dependencies = 0
for project, dependencies in inv_dep.items():
    if project in dependencies:
        self_inv_dependencies += 1


print(f'{self_dependencies=}, {self_inv_dependencies=}')
