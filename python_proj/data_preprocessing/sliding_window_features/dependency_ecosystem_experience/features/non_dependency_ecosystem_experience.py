"""
Implements concrete wrapper for all non-dependency experience variables.
"""

from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.decorators import (
    NonDependencyEcosystemExperienceDecorator,
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


class NonDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSubmissionCount,
        )


class NonDependencyEcosystemExperienceSubmitterPullRequestSuccessRate(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestSuccessRate,
        )


class NonDependencyEcosystemExperienceSubmitterPullRequestCommentCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestCommentCount,
        )


class NonDependencyEcosystemExperienceSubmitterPullRequestDiscussionParticipationCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterPullRequestDiscussionParticipationCount,
        )


# Issue feature


class NonDependencyEcosystemExperienceSubmitterIssueSubmissionCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueSubmissionCount,
        )


class NonDependencyEcosystemExperienceSubmitterIssueCommentCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueCommentCount,
        )


class NonDependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(
    NonDependencyEcosystemExperienceDecorator
):
    def __init__(self) -> None:
        super().__init__(
            inner_component=EcosystemExperienceSubmitterIssueDiscussionParticipationCount,
        )
