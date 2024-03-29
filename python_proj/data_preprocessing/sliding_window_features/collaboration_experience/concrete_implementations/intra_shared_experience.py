"""
Implements the concrete intra project shared experience features.
"""

from typing import List, Tuple
from numbers import Number

from python_proj.utils.exp_utils import get_integrator_key
from python_proj.data_preprocessing.sliding_window_features.collaboration_experience.intra_eco_shared_experience import (
    IntraProjectSharedExperienceFeature,
)


# Pull request


class IntraProjectSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(
    IntraProjectSharedExperienceFeature
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by U and integrated by V.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(["user_data", "id"], [get_integrator_key, "id"], is_inversed)


class IntraProjectSharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(
    IntraProjectSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator
):
    """
    Shared experience feature accounting for pull requests that have been
    submitted by V and integrated by U (i.e., the inverse role-distribution).
    """

    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class IntraProjectSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(
    IntraProjectSharedExperienceFeature
):
    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["user_data", "id"], ["comments_data", "user_data", "id"], is_inversed
        )

    def _handle(self, entry: dict, sign: Number):
        if entry["comments"] > 0:
            super()._handle(entry, sign)


class IntraProjectSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(
    IntraProjectSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    def __init__(self) -> None:
        super().__init__(is_inversed=True)


class IntraProjectSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(
    IntraProjectSharedExperienceFeature
):
    """
    Counts the number of times the submitter and integrator have both participated in a pull request discussion.
    This does not need an inverse, as the implementation of the parent class creates edges for every permutation
    of commenters; i.e., (u, v) and (v, u) are both added here.
    """

    def __init__(self, is_inversed: bool = False) -> None:
        super().__init__(
            ["comments_data", "user_data", "id"],
            ["comments_data", "user_data", "id"],
            is_inversed,
        )

    def _handle(self, entry: dict, sign: Number):
        if entry["comments"] > 0:
            super()._handle(entry, sign)


# Issues


class IntraProjectSharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(
    IntraProjectSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class IntraProjectSharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(
    IntraProjectSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


class IntraProjectSharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(
    IntraProjectSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter
):
    """
    Is functionally exactly the same as the parent class.
    This class is implemented just to give the feature a unique name.
    """


def build_intra_se_features() -> Tuple[
    List[IntraProjectSharedExperienceFeature],
    List[IntraProjectSharedExperienceFeature],
]:
    """Factory method for intra-project shared experience features."""
    pr_features = [
        IntraProjectSharedExperiencePullRequestSubmittedBySubmitterIntegratedByIntegrator(),
        IntraProjectSharedExperiencePullRequestSubmittedByIntegratorIntegratedBySubmitter(),
        IntraProjectSharedExperiencePullRequestSubmittedBySubmitterCommentedOnByIntegrator(),
        IntraProjectSharedExperiencePullRequestSubmittedByIntegratorCommentedOnBySubmitter(),
        IntraProjectSharedExperiencePullRequestDiscussionParticipationByIntegratorAndSubmitter(),
    ]
    iss_features = [
        IntraProjectSharedExperienceIssueSubmittedBySubmitterCommentedOnByIntegrator(),
        IntraProjectSharedExperienceIssueSubmittedByIntegratorCommentedOnBySubmitter(),
        IntraProjectSharedExperienceIssueDiscussionParticipationByIntegratorAndSubmitter(),
    ]
    return pr_features, iss_features
