"""
Implements various data filters for GitLab data
acquired with GrimoireLab Perceval.
"""

from python_proj.experiment.filters.gl_filters import BaseFilter


class MergeRequestFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
