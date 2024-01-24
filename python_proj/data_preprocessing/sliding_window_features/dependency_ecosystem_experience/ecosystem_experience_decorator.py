from typing import Any

from python_proj.data_preprocessing.sliding_window_features.base import SlidingWindowFeature
from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience import safe_load_dependency_map, DEPENDENCY_MAP, PROJECT_NAME_TO_ID
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import EcosystemExperience


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
            current_project_name,
            other_project_name
    ) -> bool:
        """
        Returns true if the project should be ignored. It does so when the two 
        project keys are identical, when regular dependencies are used and the 
        current project has no dependency on the other project, or when inversed 
        dependencies are used and the other project has no dependency on the current project.
        """
        
        # TODO: This method renames its parameters to "name" instead of "id". I don't think thats's quite right.

        # Ignores intra-project experience; you can't have a self-dependency anyways.
        if current_project_name == other_project_name:
            return True

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
