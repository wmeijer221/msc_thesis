from csv import reader
import datetime
import json
from os import path
from typing import Any, Tuple

from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import EcosystemExperience
from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import *
import python_proj.utils.exp_utils as exp_utils


DEPENDENCY_MAP: SafeDict[str, set[str]] = None
PROJECT_NAME_TO_ID: dict[int, str] = None


def __attempt_quick_load_dependency_map() -> Tuple[bool, str,
                                                   SafeDict[str,
                                                            set[str]] | None,
                                                   dict[str, int] | None]:
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
    ql_dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=ql_dependency_file_name)

    print(f'Loading projects and dependencies from: "{ql_dependency_path}".')

    if not path.exists(ql_dependency_path):
        print("Can't do quick load.")
        return False, ql_dependency_path, None, None

    try:
        with open(ql_dependency_path, "r", encoding='utf-8') as input_file:
            j_data = json.loads(input_file.read())
            dependency_map = SafeDict(initial_mapping=j_data["dependency_map"],
                                      default_value=set)
            project_name_to_id = j_data["project_name_to_id"]

        print("Finished quick load!")

        return True, ql_dependency_path, dependency_map, project_name_to_id
    except Exception as ex:
        print(f"Coulnd't quick load due to error: {ex}.")
        return False, ql_dependency_path, None, None


def __slow_load_dependency_map(output_path: str) \
    -> Tuple[SafeDict[str, set[str]],
             dict[str, int]]:
    """
    Loads all depedency data from the libraries.io dataset.
    This includes the project dependencies and the repository dependencies.
    Both are included to create a full picture. It also writes the results 
    to a quick-load file, so the next run is much faster.
    """

    print("Starting the slow load dependencies.")

    dependency_map = SafeDict(default_value=set)

    # Loads proj id -> proj name mapping.
    project_with_repo_details_file_name = "projects_with_repository_fields-1.6.0-2020-01-12"
    project_file_name = exp_utils.TRAIN_DATASET_PATH(
        file_name=project_with_repo_details_file_name)

    # Creates a mapping of project names to IDs as dependencies are
    # stored in IDs, and the PR data works only uses names.
    print(f'Loading projects from: "{project_file_name}".')
    project_name_to_id = {}
    repo_name_index = exp_utils.repo_name_index
    with open(project_file_name, "r", encoding='utf-8') as project_file:
        csv_reader = reader(project_file)
        for project in csv_reader:
            repo_id = project[0]
            repo_name = project[repo_name_index].lower()
            project_name_to_id[repo_name] = repo_id

    dependency_count = 0

    # Loads project dependencies as logged by NPM.
    dependency_file_name = "dependencies-1.6.0-2020-01-12"
    dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=dependency_file_name)
    print(f'Loading dependencies from: {dependency_path}.')
    with open(dependency_path, "r", encoding='utf-8') as input_file:
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
        file_name=repo_dependency_file_name)
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
        print(f'{missing_projects=}')

    print(f'Loaded {dependency_count} dependencies.')
    print(f"Creating quick load file at '{output_path}'.")

    # Transforms sets to lists as sets aren't JSON serializable.
    for key in dependency_map.keys():
        dependency_map[key] = list(dependency_map[key])

    # Writes the output to a quick-load file.
    ql_dependency_map = {
        "dependency_map": dependency_map,
        "project_name_to_id": project_name_to_id
    }
    with open(output_path, "w+", encoding='utf-8') as output_file:
        output_file.write(json.dumps(ql_dependency_map))

    print("Finished slow load!")

    return dependency_map, project_name_to_id


def load_dependency_map() \
    -> Tuple[SafeDict[str, set[str]],
             dict[str, int]]:
    """
    Loads the dependency map by first attempting the quick way,
    and if that fails by loading the slow way.
    """

    exp_utils.load_paths_for_eco()
    start = datetime.datetime.now()
    ql_success, ql_dependency_path, dependency_map, project_name_to_id = __attempt_quick_load_dependency_map()
    if not ql_success:
        dependency_map, project_name_to_id = __slow_load_dependency_map(
            ql_dependency_path)
    timedelta = datetime.datetime.now() - start
    print(
        f'Loaded {len(project_name_to_id)} projects and {len(dependency_map)} projects with dependencies.')
    print(f'Loaded dependency data in {timedelta}.')

    return dependency_map, project_name_to_id


def safe_load_dependency_map() \
    -> Tuple[SafeDict[str, set[str]],
             dict[str, int]]:
    """
    Returns the dependency map that in mamory and
    loads it from the filesystem if it hasn't been loaded yet.
    """

    if DEPENDENCY_MAP is None or PROJECT_NAME_TO_ID is None:
        return load_dependency_map()
    else:
        return DEPENDENCY_MAP, PROJECT_NAME_TO_ID


class EcosystemExperienceDecorator(SlidingWindowFeature):
    """
    Decorator class that hijacks the ``project_is_ignored_for_cumulative_experience`` 
    method of ``EcosystemExperience`` objects and replaces it with a much more 
    stringent filter: excluding all projects where there are no dependencies.
    """

    def __init__(self, inner_component: type, use_reversed_dependencies: bool = False) -> None:
        """
        :param inner_component: The component type that's being decorated.
        :param use_reversed_dependencies: The ``DEPENDENCY`` mapping is used or
        the ``INV_DEPENDENCY`` mapping. The former being the projects the focal
        project depends on, and the latter the projects that depend on the focal project.
        """

        # initializes singletons.
        safe_load_dependency_map()

        # Loads inner component and hijacks ignore function.
        self.__inner_component: EcosystemExperience = inner_component()
        self.__inner_component.project_is_ignored_for_cumulative_experience = \
            self._project_is_ignored_for_cumulative_experience

        self.__use_reversed_dependencies: bool = use_reversed_dependencies

    def _project_is_ignored_for_cumulative_experience(
            self,
            current_project_key,
            other_project_key
    ) -> bool:
        """
        Returns true if the project should be ignored. It does so when the two 
        project keys are identical, when regular dependencies are used and the 
        current project has no dependency on the other project, or when inversed 
        dependencies are used and the other project has no dependency on the current project.
        """

        # Ignores intra-project experience; you can't have a self-dependency anyways.
        if current_project_key == other_project_key:
            return True

        # Translates source file data to project IDs.
        current_project_name = "/".join(exp_utils.get_owner_and_repo_from_source_path(
            current_project_key)).lower()
        other_project_name = "/".join(exp_utils.get_owner_and_repo_from_source_path(
            other_project_key)).lower()

        # Sets the order of parameters if inverse dependencies are used.
        # With dependency A --(depends on)--> B, you have that DEP(A) = [B]
        # and that INV_DEP(B) = [A]; Here the depending project is the focal
        # project and the project that's depended on the other project.
        (focal_name, other_name) = (other_project_name, current_project_name) \
            if self.__use_reversed_dependencies \
            else (current_project_name, other_project_name)

        # Selects relevant dependency map (inv vs. regular).
        dependency_map = DEPENDENCY_MAP

        # Ignores dependencies that are unknown.
        if focal_name not in PROJECT_NAME_TO_ID \
                or other_name not in PROJECT_NAME_TO_ID:
            return True

        focal_project_id = PROJECT_NAME_TO_ID[focal_name]
        other_project_id = PROJECT_NAME_TO_ID[other_name]

        # If the focal project has no known dependencies,
        # the experience is ignored.
        if focal_project_id not in dependency_map:
            return True

        # Projects without a dependency are ignored; i.e., the inverse of has_dependency.
        has_dependency = other_project_id in dependency_map[focal_project_id]
        return not has_dependency

    def add_entry(self, entry: dict):
        return self.__inner_component.add_entry(entry)

    def remove_entry(self, entry: dict):
        return self.__inner_component.remove_entry(entry)

    def get_feature(self, entry: dict) -> Any:
        return self.__inner_component.get_feature(entry)

    def is_valid_entry(self, entry: dict) -> bool:
        return self.__inner_component.is_valid_entry(entry)


# dependency pull requests.


class DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSubmissionCount
        )


class DependencyEcosystemExperienceSubmitterPullRequestSuccessRate(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSuccessRate
        )


class DependencyEcosystemExperienceSubmitterPullRequestCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestCommentCount
        )


class DependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount
        )


# dependency issues


class DependencyEcosystemExperienceSubmitterIssueSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueSubmissionCount
        )


class DependencyEcosystemExperienceSubmitterIssueCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueCommentCount
        )


class DependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueDiscussionParticipationCount
        )


# Inversed dependency pull requests


class InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSubmissionCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSuccessRate,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestCommentCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueSubmissionCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterIssueCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueCommentCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueDiscussionParticipationCount,
            use_reversed_dependencies=True
        )


def build_deco_features():
    """
    Factory method for all features.
    """

    # Discussion participation features are left out as they're
    # essentially the same as comment count.
    deco_pr = [
        DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(),
        DependencyEcosystemExperienceSubmitterPullRequestSuccessRate(),
        DependencyEcosystemExperienceSubmitterPullRequestCommentCount(),
        # DependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(),
    ]
    deco_issue = [
        DependencyEcosystemExperienceSubmitterIssueSubmissionCount(),
        DependencyEcosystemExperienceSubmitterIssueCommentCount(),
        # DependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(),
    ]

    ideco_pr = [
        InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(),
        InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate(),
        InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount(),
        # InversedDependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(),
    ]
    ideco_issue = [
        InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount(),
        InversedDependencyEcosystemExperienceSubmitterIssueCommentCount(),
        # InversedDependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(),
    ]

    return deco_pr, deco_issue, ideco_pr, ideco_issue


DEPENDENCY_MAP, PROJECT_NAME_TO_ID = safe_load_dependency_map()

DECO_EXP_PR_SW_FEATURES, DECO_EXP_ISSUE_SW_FEATURES, \
    IDECO_EXP_PR_SW_FEATURES, IDECO_EXP_ISSUE_SW_FEATURES = build_deco_features()
