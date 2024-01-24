from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.ecosystem_experience_decorator import EcosystemExperienceDecorator
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import *


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


# Issue feature


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

