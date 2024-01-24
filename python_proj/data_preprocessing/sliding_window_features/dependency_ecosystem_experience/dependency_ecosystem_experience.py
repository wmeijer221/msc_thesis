from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.ecosystem_experience_decorator import EcosystemExperienceDecorator
from python_proj.data_preprocessing.sliding_window_features.ecosystem_experience import *


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

