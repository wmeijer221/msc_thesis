"""
Implements various data filters for GitHub data
acquired with GrimoireLab Perceval.
"""

from python_proj.data_retrieval.gl_filters.gl_filters import BaseFilter


class UserFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["login", "id", "gravatar_id",
                        "type", "site_admin", "name", "company",
                        "email", "twitter_username", "organizations"]

        self._listsubfilter_fields = {
            OrganizationFilter: ["organizations"]
        }


class CommentFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["id", "created_at",
                        "updated_at", "author_association", "body"]
        self._subfilter_fields = {
            UserFilter: ["user_data", "assignee_data"]
        }


class IssueFilter (BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["id", "number", "title", "state",
                        "locked", "assignee", "milestone", "comments",
                        "created_at", "updated_at", "closed_at",
                        "author_association", "active_lock_reason", "body", "state_reason"]
        self._subfilter_fields = {
            UserFilter: ["user_data"]
        }
        self._listsubfilter_fields = {
            CommentFilter: ["comments_data"]
        }


class PullFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["id", "number", "state", "created_at", "updated_at", "closed_at",
                        "merged_at", "requested_reviewers", "requested_teams",
                        "milestone", "author_association", "auto_merge", "active_lock_reason",
                        "merged", "mergeable", "rebaseable", "mergeable_state",
                        "comments", "review_comments", "commits", "additions",
                        "deletions", "changed_files"]

        self._subfilter_fields = {
            UserFilter: ["user_data", "merged_by_data", "assignee"],
            ReviewFilter: ["reviews_data"]
        }

        self._listsubfilter_fields = {
            UserFilter: ["assignees", "requested_reviewers_data"],
            ReviewCommentFilter: ["review_comments_data"]
        }


class ReviewCommentFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["id", "diff_hunk", "commit_id",
                        "original_commit_id", "created_at", "updated_at", "body"]

        self._subfilter_fields = {
            UserFilter: ["user_data"]
        }


class OrganizationFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["login", "id", "description"]


class ReviewFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["id", "body", "state",
                        "author_association", "submitted_at", "commit_id"]

        self._subfilter_fields = {
            UserFilter: ["user_data"]
        }
