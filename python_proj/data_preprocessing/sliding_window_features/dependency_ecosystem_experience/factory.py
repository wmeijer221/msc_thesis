from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.dependency_ecosystem_experience import *
from python_proj.data_preprocessing.sliding_window_features.dependency_ecosystem_experience.inverse_dependency_ecosystem_experience import *


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
