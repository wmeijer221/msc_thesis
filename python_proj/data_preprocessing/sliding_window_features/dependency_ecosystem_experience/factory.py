"""
Implements simply factory returning instances of all (non-/inverse) dependency experience fields.
"""

from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.features.dependency_ecosystem_experience import *
from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.features.inverse_dependency_ecosystem_experience import *
from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.features.non_dependency_ecosystem_experience import *

# dependency pull requests.


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
        # TODO: I merged non-dependency ecosystem experience with the dependency experience return value. This is incorrect, but these factories are messy to begin with.
        NonDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount(),
        NonDependencyEcosystemExperienceSubmitterPullRequestSuccessRate(),
        NonDependencyEcosystemExperienceSubmitterPullRequestCommentCount,
    ]
    deco_issue = [
        DependencyEcosystemExperienceSubmitterIssueSubmissionCount(),
        DependencyEcosystemExperienceSubmitterIssueCommentCount(),
        # DependencyEcosystemExperienceSubmitterIssueDiscussionParticipationCount(),
        # TODO: Same problem as described above.
        NonDependencyEcosystemExperienceSubmitterIssueSubmissionCount(),
        NonDependencyEcosystemExperienceSubmitterIssueCommentCount(),
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
