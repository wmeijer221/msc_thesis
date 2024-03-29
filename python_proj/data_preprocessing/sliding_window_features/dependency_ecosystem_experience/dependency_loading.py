"""
Used to load dependency data.
To avoid repeated data loading (which takes quite a long time),
you should probably use `safe_load_dependency_map()`.
"""

from os import path
from typing import Tuple, Iterator

from csv import reader
import datetime
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import SafeDict

DEPENDENCY_MAP: SafeDict[int, set[int]] = None
PROJECT_NAME_TO_ID: dict[str, int] = None


def __attempt_quick_load_dependency_map() -> (
    Tuple[bool, str, SafeDict[int, list[int]] | None, dict[str, int] | None]
):
    """
    Attempts to load the file in which the summarized dependency data is stored.
    Using this file is much, much faster than loading the libraries.io datasets
    as it's an order of magnitude smaller (reading 2GB of data instead of ~25GB).
    """

    print("Attempting quick load dependencies.")

    # Attempts to load "quick-load" dependency map
    # if it exists. This is much faster than iterating
    # through the whole 15GB datafile.
    ql_dependency_file_name = "ql_dependencies"
    ql_dependency_path = exp_utils.TRAIN_DATASET_PATH(file_name=ql_dependency_file_name)

    print(f'Loading projects and dependencies from: "{ql_dependency_path}".')

    if not path.exists(ql_dependency_path):
        print("Can't do quick load.")
        return False, ql_dependency_path, None, None

    try:
        with open(ql_dependency_path, "r", encoding="utf-8") as input_file:
            j_data = json.loads(input_file.read())
            dependency_map = SafeDict(
                initial_mapping=j_data["dependency_map"], default_value=set
            )
            project_name_to_id = j_data["project_name_to_id"]

        print("Finished quick load!")

        return True, ql_dependency_path, dependency_map, project_name_to_id
    except Exception as ex:
        print(f"Coulnd't quick load due to error: {ex}.")
        return False, ql_dependency_path, None, None


def __slow_load_dependency_map(
    output_path: str,
) -> Tuple[SafeDict[int, set[int]], dict[str, int]]:
    """
    Loads all depedency data from the libraries.io dataset.
    This includes the project dependencies and the repository dependencies.
    Both are included to create a full picture. It also writes the results
    to a quick-load file, so the next run is much faster.
    """

    print("Starting the slow load dependencies.")

    dependency_map = SafeDict(default_value=set)

    # Loads proj id -> proj name mapping.
    project_with_repo_details_file_name = (
        "projects_with_repository_fields-1.6.0-2020-01-12"
    )
    project_file_name = exp_utils.TRAIN_DATASET_PATH(
        file_name=project_with_repo_details_file_name
    )

    # Creates a mapping of project names to IDs as dependencies are
    # stored in IDs, and the PR data works only uses names.
    print(f'Loading projects from: "{project_file_name}".')
    project_name_to_id = {}
    repo_name_index = exp_utils.repo_name_index
    with open(project_file_name, "r", encoding="utf-8") as project_file:
        csv_reader = reader(project_file)
        for project in csv_reader:
            repo_id = project[0]
            repo_name = project[repo_name_index].lower()
            project_name_to_id[repo_name] = repo_id

    dependency_count = 0

    # Loads project dependencies as logged by NPM.
    dependency_file_name = "dependencies-1.6.0-2020-01-12"
    dependency_path = exp_utils.TRAIN_DATASET_PATH(file_name=dependency_file_name)
    print(f"Loading dependencies from: {dependency_path}.")
    with open(dependency_path, "r", encoding="utf-8") as input_file:
        csv_reader = reader(input_file)
        header = next(csv_reader)
        focal_project_id_idx = header.index("Project ID")
        other_project_id_idx = header.index("Dependency Project ID")
        for dependency in csv_reader:
            other_project_id = dependency[other_project_id_idx].lower()
            focal_project_id = dependency[focal_project_id_idx].lower()
            # Some projects have self-dependencies. These are ignored.
            if other_project_id == focal_project_id:
                continue
            dependency_map[focal_project_id].add(other_project_id)
            dependency_count += 1

    # Loads repository dependencies as logged in the respective social coding platform (e.g. GitHub).
    repo_dependency_file_name = "repository_dependencies-1.6.0-2020-01-12"
    repo_dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=repo_dependency_file_name
    )
    print(f'Loading repo dependencies from "{repo_dependency_path}".')
    with open(repo_dependency_path, "r", encoding="utf-8") as repo_dependency_file:
        csv_reader = reader(repo_dependency_file)
        header = next(csv_reader)
        missing_projects = 0
        repository_name_owner_idx = header.index("Repository Name with Owner")
        dependency_id_idx = header.index("Dependency Project ID")
        for dependency in csv_reader:
            dependee_repo_name = dependency[repository_name_owner_idx].lower()
            if not dependee_repo_name in project_name_to_id:
                missing_projects += 1
                continue
            dependency_id = dependency[dependency_id_idx]
            # For projects that are not present in the dataset, this is an empty string.
            if dependency_id == "":
                continue
            dependee_id = project_name_to_id[dependee_repo_name]
            dependency_map[dependee_id].add(dependency_id)
            dependency_count += 1
        print(f"{missing_projects=}")

    print(f"Loaded {dependency_count} dependencies.")
    print(f"Creating quick load file at '{output_path}'.")

    # Transforms sets to lists as sets aren't JSON serializable.
    for key in dependency_map.keys():
        dependency_map[key] = list(dependency_map[key])

    # Writes the output to a quick-load file.
    ql_dependency_map = {
        "dependency_map": dependency_map,
        "project_name_to_id": project_name_to_id,
    }
    with open(output_path, "w+", encoding="utf-8") as output_file:
        output_file.write(json.dumps(ql_dependency_map))

    print("Finished slow load!")

    return dependency_map, project_name_to_id


def load_dependency_map() -> Tuple[SafeDict[int, set[int]], dict[str, int]]:
    """
    Loads the dependency map by first attempting the quick way,
    and if that fails by loading the slow way.
    """

    global DEPENDENCY_MAP, PROJECT_NAME_TO_ID

    exp_utils.load_paths_for_eco()
    start = datetime.datetime.now()
    ql_success, ql_dependency_path, dependency_map, project_name_to_id = (
        __attempt_quick_load_dependency_map()
    )
    if not ql_success:
        dependency_map, project_name_to_id = __slow_load_dependency_map(
            ql_dependency_path
        )
    timedelta = datetime.datetime.now() - start
    print(
        f"Loaded {len(project_name_to_id)} projects and {len(dependency_map)} projects with dependencies."
    )
    print(f"Loaded dependency data in {timedelta}.")

    DEPENDENCY_MAP = dependency_map
    PROJECT_NAME_TO_ID = project_name_to_id

    return dependency_map, project_name_to_id


def safe_load_dependency_map() -> Tuple[SafeDict[int, set[int]], dict[str, int]]:
    """
    Returns the dependency map that in mamory and
    loads it from the filesystem if it hasn't been loaded yet.
    """

    # TODO: One of these functions lies about its return type, returning lists instead of sets as the inner dictionary value.
    if DEPENDENCY_MAP is None or PROJECT_NAME_TO_ID is None:
        return load_dependency_map()
    else:
        return DEPENDENCY_MAP, PROJECT_NAME_TO_ID


def calculate_transitive_dependency_map(
    dependencies: SafeDict[int, list[int]], max_iter: int = 10_000
) -> SafeDict[int, set[int]]:
    """
    Calculates the transitive closure of the input dependencies;
    i.e., cascading dependencies.
    """

    # HACK: Changes inner type to set instead of list.
    for key in dependencies.keys():
        dependencies[key] = set(dependencies[key])

    # Calculates transitive dependencies.
    not_converged = True
    iter = 0
    while not_converged:
        iter += 1
        print(f'Starting iteration {iter}/{max_iter}.')
        not_converged = __calculate_transitive_dependency_map(dependencies)
        if iter >= max_iter:
            print(f"Could not converge in {max_iter} iterations.")
            break
    print(f"Calculated transitive dependency map in {iter} iterations.")
    return dependencies


def __calculate_transitive_dependency_map(
    dependencies: SafeDict[int, set[int]]
) -> bool:
    """
    Helper function applyling one round of transitive dependency merging.
    Returns true if a dependency was added.
    """

    was_updated = False

    project_ids = set(dependencies.keys())

    for project_id in project_ids:
        deps = dependencies[project_id]
        old_dep_count = len(deps)

        for dep_id in deps:
            if dep_id not in dependencies:
                continue
            cascade_deps = dependencies[dep_id]
            dependencies[project_id] = dependencies[project_id].union(cascade_deps)

        new_dep_count = len(dependencies[project_id])
        if new_dep_count != old_dep_count:
            was_updated = True

    return was_updated


def filter_dependencies(
    included_projects: Iterator[int | str], map_name_to_id: bool = False
) -> Tuple[SafeDict[int, set[int]], dict[str, int]]:
    """
    Filters all dependency fromm the singleton dependency
    map that are not included in the provided list. Returns
    the updated singletons.
    """
    global DEPENDENCY_MAP, PROJECT_NAME_TO_ID

    dependency_map, project_name_to_id = safe_load_dependency_map()

    # HACK: Changes inner type to set instead of list.
    for key in dependency_map.keys():
        dependency_map[key] = set(dependency_map[key])

    # Applies project name to id mapping.
    if map_name_to_id:
        included_projects = set(
            project_name_to_id[proj_name.lower()]
            for proj_name in included_projects
            if proj_name.lower() in project_name_to_id
        )
        print(f"No. included projects after mapping: {len(included_projects)}.")

    # Filters to-be singletons
    dependency_map = {
        proj_id: dependency_map[proj_id].intersection(included_projects)
        for proj_id in included_projects
        if proj_id in dependency_map
    }
    project_name_to_id = {
        proj_name: proj_id
        for proj_name, proj_id in project_name_to_id.items()
        if proj_id in included_projects
    }

    # Overwrites singletons.
    DEPENDENCY_MAP = dependency_map
    PROJECT_NAME_TO_ID = project_name_to_id

    return dependency_map, project_name_to_id
