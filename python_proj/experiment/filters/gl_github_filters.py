from typing import Dict

"""
Implements various data filters for GitHub data
acquired with GrimoireLab Perceval.
"""


def safe_set(source: dict, target: dict, key: str):
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    target[key] = source[key]


def safe_set_with_filter(source: dict, target: dict, filter: 'BaseFilter', key: str):
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    target[key] = filter.filter(source[key])


def safe_set_many_with_filter(source: dict, target: dict, filter: 'BaseFilter', key: str):
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    source_list = source[key]
    if not isinstance(source_list, list):
        print(f'Field not a list: {key}')
        return
    target_list = []
    for entry in source_list:
        target_list.append(filter.filter(entry))
    target[key] = target_list


class BaseFilter:
    _fields: list[str] = []
    _subfilter_fields: Dict['BaseFilter', list[str]] = {}
    _listsubfilter_fields: Dict['BaseFilter', list[str]] = {}
    _target: dict = {}
    _source: dict = None

    def filter(self, entry) -> dict:
        if entry is None:
            return None
        self._source = entry
        self._target = {}
        self.__filter_fields()
        self.__filter_subfilter_fields()
        self.__filter_subfilter_lists()
        return self._target

    def __filter_fields(self):
        for field in self._fields:
            safe_set(self._source, self._target, field)

    def __filter_subfilter_fields(self):
        for filter, fields in self._subfilter_fields.items():
            for field in fields:
                safe_set_with_filter(self._source, self._target, filter, field)

    def __filter_subfilter_lists(self):
        for filter, fields in self._listsubfilter_fields.items():
            for field in fields:
                safe_set_many_with_filter(
                    self._source, self._target, filter, field)


class UserFilter(BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        self._fields = ["login", "id", "node_id", "gravatar_id",
                        "type", "site_admin", "name", "company",
                        "email", "twitter_username", "organizations"]


class CommentFilter(BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        self._fields = ["id", "node_id", "created_at",
                        "updated_at", "author_association", "body"]
        self._subfilter_fields = {
            UserFilter(): ["user_data", "assignee_data"]
        }


class IssueFilter (BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        self._fields = ["id", "node_id", "number", "title", "state",
                        "locked", "assignee", "milestone", "comments",
                        "created_at", "updated_at", "closed_at",
                        "author_association", "active_lock_reason", "body",
                        "state_reason"]
        self._subfilter_fields = {
            UserFilter(): ["user_data"]
        }
        self._listsubfilter_fields = {
            CommentFilter(): ["comments_data"]
        }


class PullFilter(BaseFilter):
    def __init__(self) -> None:
        super().__init__()
        # TODO: review_comments_data AND reviews_data
        self._fields = ["id", "node_id", "number", "state", "locked",
                        "title", "created_at", "updated_at", "closed_at",
                        "merged_at", "requested_reviewers", "requested_teams",
                        "milestone", "author_association", "auto_merge", "active_lock_reason",
                        "merged", "mergeable", "rebaseable", "mergeable_state",
                        "comments", "review_comments", "commits", "additions",
                        "deletions", "changed_files", "review_comments_data",
                        "reviews_data"]

        self._subfilter_fields = {
            UserFilter(): ["user_data", "merged_by_data", "assignee"]
        }
        self._listsubfilter_fields = {
            UserFilter(): ["assignees", "requested_reviewers_data"]
        }
