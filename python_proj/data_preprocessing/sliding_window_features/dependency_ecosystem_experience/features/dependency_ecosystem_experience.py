"""
Implements concrete wrapper for all dependency experience variables.
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


class DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSubmissionCount,
            use_reversed_dependencies=False,
        )


class DependencyEcosystemExperienceSubmitterPullRequestSuccessRate(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSuccessRate,
            use_reversed_dependencies=False,
        )


class DependencyEcosystemExperienceSubmitterPullRequestCommentCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestCommentCount,
            use_reversed_dependencies=False,
        )


class DependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount,
            use_reversed_dependencies=False,
        )


# dependency issues


class DependencyEcosystemExperienceSubmitterIssueSubmissionCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueSubmissionCount,
            use_reversed_dependencies=False,
        )


class DependencyEcosystemExperienceSubmitterIssueCommentCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueCommentCount,
            use_reversed_dependencies=False,
        )


class DependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(
    DependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueDiscussionParticipationCount,
            use_reversed_dependencies=False,
        )
