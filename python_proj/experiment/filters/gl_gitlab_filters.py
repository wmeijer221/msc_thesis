from python_proj.experiment.filters.gl_filters import BaseFilter


class MergeRequestFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "iid", "state", "created_at", "updated_at", "milestone",
                        "merge_status", "detailed_merge_status", "discussion_locked", "reference", "changes_count"]

        # TODO: Figure out what to do with the following fields: merged_by, merge_user, merged_at, merge_user, closed_by, closed_at, author, assignees, assignee, reviewers,

        self._listsubfilter_fields = {
            NotesFilter: ["notes_data"],
            VersionsFilter: ["versions_data"]
        }


class UserFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._fields = ["id", "username", "name", "state", "avatar_url"]


class NotesFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # TODO: THIS


class VersionsFilter(BaseFilter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # TODO: THIS
