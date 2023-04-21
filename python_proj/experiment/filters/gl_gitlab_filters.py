"""
Implements various data filters for GitLab data
acquired with GrimoireLab Perceval.
"""

from python_proj.experiment.filters.gl_filters import BaseFilter


class IssueFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fields = ["state", "description", "milestone" "project_id", "type", "updated_at", "closed_at", "id", "title", "created_at", "moved_to_id", "iid", "labels", "upvotes", "downvotes", "merge_requests_count",
                        "user_notes_count", "due_date", "time_stats", "has_tasks", "task_status", "discussion_locked", "issue_type", "severity", "task_completion_count", "weight", "epic", "iteration", "health_status"]

        # TODO: replace ``epic``, iteration, health_status (all three premium only), ``milestone``,  ``time_stats`` and ``task_completion_count`` with dedicated filter?

        self._subfilter_fields = {
            UserFilter: ["author", "assignee", "closed_by"],
        }

        self._listsubfilter_fields = {
            UserFilter: ["assignees"]
        }


class MergeRequestFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        MileStoneFilter().__init__(**kwargs)

        self._fields = ["id", "iid", "state", "created_at", "updated_at",
                        "milestone", "merge_status", "detailed_merge_status",
                        "discussion_locked", "reference", "changes_count",
                        "merged_at", "closed_at"]

        self._subfilter_fields = {
            UserFilter: ["author", "merge_user", "closed_by", "assignee"]
        }

        self._listsubfilter_fields = {
            NotesFilter: ["notes_data"],
            VersionsFilter: ["versions_data"],
            UserFilter: ["assignees", "reviewers"]
        }


class UserFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "username", "name", "state", "avatar_url"]


class NotesFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "body", "created_at",
                        "updated_at", "system", "noteable_id", "noteable_iid"]

        self._subfilter_fields = {
            UserFilter: ["author"]
        }


class VersionsFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "created_at", "real_size"]

        self._listsubfilter_fields = {
            CommitFilter: ["commits"]
        }


class CommitFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "created_at", "author_name",
                        "author_email", "committer_name", "committer_email"]


class MileStoneFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # TODO: this.
