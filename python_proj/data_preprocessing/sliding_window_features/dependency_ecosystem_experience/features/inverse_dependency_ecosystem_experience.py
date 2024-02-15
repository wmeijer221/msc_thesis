"""
Implements concrete wrapper for all inverse dependency experience variables.
"""

from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.decorators import (
    DependencyEcosystemExperienceDecorator,
)
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import (
    EcosystemExperienceSubmitterPullRequestSubmissionCount,
    EcosystemExperienceSubmitterPullRequestSuccessRate,
    EcosystemExperienceSubmitterPullRequestCommentCount,
    EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount,
    EcosystemExperienceSubmitterIssueSubmissionCount,
    EcosystemExperienceSubmitterIssueCommentCount,
    EcosystemExperienceSubmitterIssueDiscussionParticipationCount,
)
# Inversed dependency pull requests


class InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSubmissionCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSuccessRate,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestCommentCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount,
            use_reversed_dependencies=True
        )


# Issue feature


class InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueSubmissionCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterIssueCommentCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueCommentCount,
            use_reversed_dependencies=True
        )


class InversedDependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(DependencyEcosystemExperienceDecorator):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueDiscussionParticipationCount,
            use_reversed_dependencies=True
        )

