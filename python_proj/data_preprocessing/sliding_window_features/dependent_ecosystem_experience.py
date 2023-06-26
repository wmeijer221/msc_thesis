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
INV_DEPENDENCY_MAP: SafeDict[str, set[str]] = None
PROJECT_NAME_TO_ID: dict[int, str] = None


def __attempt_quick_load_dependency_map() -> Tuple[bool, str]:
    global DEPENDENCY_MAP, INV_DEPENDENCY_MAP, PROJECT_NAME_TO_ID

    print("Attempting quick load dependencies.")

    # Attempts to load "quick-load" dependency map
    # if it exists. This is much faster than iterating
    # through the whole 15GB datafile.
    ql_dependency_file_name = "ql_dependencies"
    ql_dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=ql_dependency_file_name)

    print(f'Loading projects and dependencies from: {ql_dependency_path}.')

    if not path.exists(ql_dependency_path):
        print("Can't do quick load.")
        return False, ql_dependency_path

    try:
        with open(ql_dependency_path, "r", encoding='utf-8') as input_file:
            j_data = json.loads(input_file.read())
            DEPENDENCY_MAP = j_data["dependency_map"]
            INV_DEPENDENCY_MAP = j_data["inv_dependency_map"]
            PROJECT_NAME_TO_ID = j_data["project_name_to_id"]

        print("Finished quick load!")

        return True, ql_dependency_path
    except Exception as ex:
        print(f"Coulnd't quick load due to error: {ex}.")
        return False, ql_dependency_path


def __slow_load_dependency_map(output_path: str):
    global DEPENDENCY_MAP, INV_DEPENDENCY_MAP, PROJECT_NAME_TO_ID

    print("Starting the slow load dependencies.")

    DEPENDENCY_MAP = SafeDict(default_value=set)
    INV_DEPENDENCY_MAP = SafeDict(default_value=set)

    # Loads proj id -> proj name mapping.
    project_with_repo_details_file_name = "projects_with_repository_fields-1.6.0-2020-01-12"
    project_file_name = exp_utils.TRAIN_DATASET_PATH(
        file_name=project_with_repo_details_file_name)

    print(f'Loading projects from: {project_file_name}.')

    PROJECT_NAME_TO_ID = {}
    repo_name_index = exp_utils.repo_name_index
    with open(project_file_name, "r", encoding='utf-8') as project_file:
        csv_reader = reader(project_file)
        for project in csv_reader:
            repo_id = project[0]
            repo_name = project[repo_name_index].lower()
            PROJECT_NAME_TO_ID[repo_name] = repo_id

    # Loads dependencies by reading the 15GB file; which is slow.
    dependency_file_name = "dependencies-1.6.0-2020-01-12"
    dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=dependency_file_name)

    dependency_count = 0

    print(f'Loading dependencies from: {dependency_path}.')

    with open(dependency_path, "r", encoding='utf-8') as input_file:
        csv_reader = reader(input_file)
        header = next(csv_reader)
        focal_project_name_idx = header.index("Project ID")
        other_project_id_idx = header.index("Dependency Project ID")
        for dependency in csv_reader:
            other_project_id = dependency[other_project_id_idx].lower()
            focal_project_id = dependency[focal_project_name_idx].lower()
            DEPENDENCY_MAP[focal_project_id].add(other_project_id)
            INV_DEPENDENCY_MAP[other_project_id].add(focal_project_id)
            dependency_count += 1

    # Loads repo depdnencies from so-many GB data file; which is also slow.
    repo_dependency_file_name = "repository_dependencies-1.6.0-2020-01-12"
    repo_dependency_path = exp_utils.TRAIN_DATASET_PATH(
        file_name=repo_dependency_file_name)

    print(f'Loading repo dependencies from "{repo_dependency_path}".')

    with open(repo_dependency_path, "r", encoding="utf-8") as repo_dependency_file:
        csv_reader = reader(repo_dependency_file)
        header = next(csv_reader)
        missing_projects = 0
        for dependency in csv_reader:
            dependee_repo_name = dependency[2].lower()
            if not dependee_repo_name in PROJECT_NAME_TO_ID:
                missing_projects += 1
                continue
            dependee_id = PROJECT_NAME_TO_ID[dependee_repo_name]
            dependency_id = dependency[-1]
            DEPENDENCY_MAP[dependee_id].add(dependency_id)
            INV_DEPENDENCY_MAP[dependency_id].add(dependee_id)
            dependency_count += 1
        print(f'{missing_projects=}')

    print(f'Loaded {dependency_count} dependencies.')
    print(f"Creating quick load file at {output_path}.")

    # Transforms sets to lists as sets aren't JSON serializable.
    for key in DEPENDENCY_MAP.keys():
        DEPENDENCY_MAP[key] = list(DEPENDENCY_MAP[key])
    for key in INV_DEPENDENCY_MAP.keys():
        INV_DEPENDENCY_MAP[key] = list(INV_DEPENDENCY_MAP[key])

    # Writes the output to a quick-load file.
    ql_dependency_map = {
        "dependency_map": DEPENDENCY_MAP,
        "inv_dependency_map": INV_DEPENDENCY_MAP,
        "project_name_to_id": PROJECT_NAME_TO_ID
    }
    with open(output_path, "w+", encoding='utf-8') as output_file:
        output_file.write(json.dumps(ql_dependency_map))

    print("Finished slow load!")


def load_dependency_map() \
    -> Tuple[SafeDict[str, set[str]],
             SafeDict[str, set[str]],
             dict[str, int]]:
    """
    Loads the dependency map. The distinguishment between quick 
    and slow-load is largely there to make debugging faster.
    """

    exp_utils.load_paths_for_eco()
    start = datetime.datetime.now()
    ql_success, ql_dependency_path = __attempt_quick_load_dependency_map()
    if not ql_success:
        __slow_load_dependency_map(ql_dependency_path)
    timedelta = datetime.datetime.now() - start
    print(
        f'Loaded {len(PROJECT_NAME_TO_ID)} projects and {len(DEPENDENCY_MAP)} projects with dependencies.')
    print(f'Loaded dependency data in {timedelta}.')

    return DEPENDENCY_MAP, INV_DEPENDENCY_MAP, PROJECT_NAME_TO_ID


class EcosystemExperienceDecorator(SlidingWindowFeature):
    """
    Decorator class that hijacks the ``project_is_ignored_for_cumulative_experience`` 
    method of ``EcosystemExperience`` objects and replaces it with a much more 
    stringent filter: excluding all projects where there are no dependencies.
    """

    def __init__(self, inner_component: type, use_reversed_dependencies: bool = False) -> None:
        global DEPENDENCY_MAP, PROJECT_NAME_TO_ID

        # initialized singleton.
        if any(ele is None for ele in
               [DEPENDENCY_MAP, INV_DEPENDENCY_MAP, PROJECT_NAME_TO_ID]):
            load_dependency_map()

        self.__inner_component: EcosystemExperience = inner_component()
        self.__inner_component.project_is_ignored_for_cumulative_experience = \
            self._project_is_ignored_for_cumulative_experience

        self.__use_incoming_dependencies: bool = use_reversed_dependencies

    def _project_is_ignored_for_cumulative_experience(self, current_project_id, other_project_id) -> bool:
        # Ignores intra-project experience.
        if current_project_id == other_project_id:
            return False

        # Translates source file data to project IDs.
        focal_project = "/".join(exp_utils.get_owner_and_repo_from_source_path(
            current_project_id)).lower()
        other_project = "/".join(exp_utils.get_owner_and_repo_from_source_path(
            other_project_id)).lower()

        (focal, other) = (other_project, focal_project) \
            if self.__use_incoming_dependencies \
            else (focal_project, other_project)

        if focal not in PROJECT_NAME_TO_ID or other:
            return True

        focal_project_id = PROJECT_NAME_TO_ID[focal]

        # Selects relevant dependency map (inv vs. regular).
        dependency_map = INV_DEPENDENCY_MAP \
            if self.__use_incoming_dependencies \
            else DEPENDENCY_MAP

        # If the focal project has no known dependencies,
        # the experience is ignored.
        if focal_project not in dependency_map:
            return True

        # Projects without a dependency are ignored.
        other_project_id = PROJECT_NAME_TO_ID[other]
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


# Regular dependency ecosystem experience features.


class SubmitterDependencyEcosystemExperiencePullRequestSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestSubmissionCount,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperiencePullRequestSuccessRate(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestSuccessRate,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperiencePullRequestCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestCommentCount,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperiencePullRequestDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestDiscussionParticipationCount,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperienceIssueSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueSubmissionCount,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperienceIssueCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueCommentCount,
            use_reversed_dependencies=False
        )


class SubmitterDependencyEcosystemExperienceIssueDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueDiscussionParticipationCount,
            use_reversed_dependencies=False
        )


# Inversed dependency ecosystem experience.


class SubmitterInversedDependencyEcosystemExperiencePullRequestSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestSubmissionCount,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperiencePullRequestSuccessRate(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestSuccessRate,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperiencePullRequestCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestCommentCount,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperiencePullRequestDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperiencePullRequestDiscussionParticipationCount,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperienceIssueSubmissionCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueSubmissionCount,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperienceIssueCommentCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueCommentCount,
            use_reversed_dependencies=True
        )


class SubmitterInversedDependencyEcosystemExperienceIssueDiscussionParticipationCount(EcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=SubmitterEcosystemExperienceIssueDiscussionParticipationCount,
            use_reversed_dependencies=True
        )


DECO_EXP_PR_SW_FEATURES = [
    SubmitterDependencyEcosystemExperiencePullRequestSubmissionCount(),
    SubmitterDependencyEcosystemExperiencePullRequestSuccessRate(),
    SubmitterDependencyEcosystemExperiencePullRequestCommentCount(),
    SubmitterDependencyEcosystemExperiencePullRequestDiscussionParticipationCount(),
]

DECO_EXP_ISSUE_SW_FEATURES = [
    SubmitterDependencyEcosystemExperienceIssueSubmissionCount(),
    SubmitterDependencyEcosystemExperienceIssueCommentCount(),
    SubmitterDependencyEcosystemExperienceIssueDiscussionParticipationCount(),
]


IDECO_EXP_PR_SW_FEATURES = [
    SubmitterInversedDependencyEcosystemExperiencePullRequestSubmissionCount(),
    SubmitterInversedDependencyEcosystemExperiencePullRequestSuccessRate(),
    SubmitterInversedDependencyEcosystemExperiencePullRequestCommentCount(),
    SubmitterInversedDependencyEcosystemExperiencePullRequestDiscussionParticipationCount(),
]

IDECO_EXP_ISSUE_SW_FEATURES = [
    SubmitterInversedDependencyEcosystemExperienceIssueSubmissionCount(),
    SubmitterInversedDependencyEcosystemExperienceIssueCommentCount(),
    SubmitterInversedDependencyEcosystemExperienceIssueDiscussionParticipationCount(),
]
