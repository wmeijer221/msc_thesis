from typing import Any

from python_proj.data_preprocessing.sliding_window_features.base import (
    SlidingWindowFeature,
)

from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience import (
    safe_load_dependency_map,
)
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import (
    EcosystemExperience,
)


class EcosystemExperienceDecorator(SlidingWindowFeature):
    """
    Decorator class that hijacks the ``project_is_ignored_for_cumulative_experience``
    method of ``EcosystemExperience``. Inheriting classes can apply more stringent project
    filters (e.g., dependency experience).
    Don't use this class directly, use one of its inheriting classes.
    """

    def __init__(
        # TODO: `use_reversed_dependencies` is only relevant for inheriting classes. Move this parameter.
        self,
        inner_component: type,
    ) -> None:
        """
        :param inner_component: The component type that's being decorated.
        :param use_reversed_dependencies: The ``DEPENDENCY`` mapping is used or
        the ``INV_DEPENDENCY`` mapping. The former being the projects the focal
        project depends on, and the latter the projects that depend on the focal project.
        """

        # initializes singletons.
        self._dependency_map, self._project_name_to_id = safe_load_dependency_map()

        # Loads inner component and hijacks ignore function.
        self.__inner_component: EcosystemExperience = inner_component()
        self.__inner_component.project_is_ignored_for_cumulative_experience = (
            self._project_is_ignored_for_cumulative_experience
        )

    def _project_is_ignored_for_cumulative_experience(
        self, current_project_name: str, other_project_name: str
    ) -> bool:
        raise NotImplementedError(
            "You cannot use `EcosystemExperienceDecorator` directly, use one of its subclasses instead."
        )

    def _has_dependency_on(self, focal_project: str, other_project: str) -> bool:
        """Returns true if `focal_project` has an outgoing dependency on `other_project`."""
        # Returns false if they aren't identifiable.
        if (
            not focal_project in self._project_name_to_id
            or other_project not in self._project_name_to_id
        ):
            return False
        # Returns false if there are no dependencies.
        focal_id = self._project_name_to_id[focal_project]
        if focal_id not in self._dependency_map:
            return False
        # Returns whether there is a dependency.
        other_id = self._project_name_to_id[other_project]
        has_dependency = other_id in self._dependency_map[focal_id]
        return has_dependency

    def add_entry(self, entry: dict):
        return self.__inner_component.add_entry(entry)

    def remove_entry(self, entry: dict):
        return self.__inner_component.remove_entry(entry)

    def get_feature(self, entry: dict) -> Any:
        return self.__inner_component.get_feature(entry)

    def is_valid_entry(self, entry: dict) -> bool:
        return self.__inner_component.is_valid_entry(entry)


class DependencyEcosystemExperienceDecorator(EcosystemExperienceDecorator):
    """
    objects applies a much more stringent filter:
    excluding all projects where there are no dependencies.
    """

    def __init__(self, inner_component: type, use_reversed_dependencies: bool) -> None:
        self._use_reversed_dependencies = use_reversed_dependencies
        super().__init__(inner_component)

    def _project_is_ignored_for_cumulative_experience(
        self, current_project_name, other_project_name
    ) -> bool:
        """
        Returns true if the project should be ignored. It does so when the two
        project keys are identical, when regular dependencies are used and the
        current project has no dependency on the other project, or when inversed
        dependencies are used and the other project has no dependency on the current project.
        """

        # Ignores intra-project experience; you can't have a self-dependency anyways.
        if current_project_name == other_project_name:
            return True

        # Sets the order of parameters if inverse dependencies are used.
        # With dependency A --(depends on)--> B, you have that DEP(A) = [B]
        # and that INV_DEP(B) = [A]; Here the depending project is the focal
        # project and the project that's depended on the other project.
        (focal_name, other_name) = (
            (other_project_name, current_project_name)
            if self._use_reversed_dependencies
            else (current_project_name, other_project_name)
        )

        has_dependency = self._has_dependency_on(focal_name, other_name)
        # reminder: it's a filter method, so true means the data is ignored.
        return not has_dependency


class NonDependencyEcosystemExperienceDecorator(EcosystemExperienceDecorator):
    """
    Applies filter for non-dependency experience; i.e., such that
    there is no incoming dependency AND no outgoing dependency.
    """

    def _project_is_ignored_for_cumulative_experience(
        self, current_project_name: str, other_project_name: str
    ) -> bool:
        # Ignores intra-project experience; you can't have a self-dependency anyways.
        if current_project_name == other_project_name:
            return True

        in_dependency = self._has_dependency_on(
            current_project_name, other_project_name
        )
        out_dependency = self._has_dependency_on(
            other_project_name, current_project_name
        )

        return in_dependency or out_dependency
