from typing import Dict, Sequence


def _seq_but_not_str(obj):
    return isinstance(obj, Sequence) and \
        not isinstance(obj, (str, bytes, bytearray))


def safe_set(source: dict, target: dict, key: str):
    if source is None or len(source) == 0:
        return
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    target[key] = source[key]


def safe_set_with_filter(source: dict, target: dict, filter_type: type, key: str, **kwargs):
    if source is None or len(source) == 0:
        return
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    filter = filter_type(**kwargs)
    target[key] = filter.filter(source[key])


def safe_set_many_with_filter(source: dict, target: dict, filter_type: type, key: str, **kwargs):
    if source is None or len(source) == 0:
        return
    if not key in source:
        print(f"Missing filter key: {key}")
        return
    source_list = source[key]
    if not isinstance(source_list, list):
        print(f'Field not a list: {key}')
        return
    target_list = []
    filter = filter_type(**kwargs)
    for entry in source_list:
        target_list.append(filter.filter(entry))
    target[key] = target_list


class BaseFilter:
    _fields: list[str] = []
    _subfilter_fields: Dict[type, list[str]] = {}
    _listsubfilter_fields: Dict[type, list[str]] = {}
    _target: dict = {}
    _source: dict = None

    __kwargs = {}

    def __init__(self, ignore_empty: bool = False) -> None:
        """
        :param ignore_empty: Whether empty fields (i.e., empty arrays, empty dictionaries, and null-values) should be ignored or not.
        """
        
        self._ignore_empty = ignore_empty
        self.__kwargs["ignore_empty"] = ignore_empty

    def filter(self, entry) -> dict:
        if entry is None:
            return None
        self._source = entry
        self._target = {}
        self.__filter_fields()
        self.__filter_subfilter_fields()
        self.__filter_subfilter_lists()
        return self._target

    def _is_empty(self, field):
        if not self._ignore_empty:
            return False
        if not field in self._source:
            return True
        source_field = self._source[field]
        return source_field is None or \
            (_seq_but_not_str(source_field) and len(source_field) == 0) or \
            (isinstance(source_field, dict) and len(source_field) == 0)

    def __filter_fields(self):
        non_empty_fields = [field for field in self._fields
                            if not self._is_empty(field)]
        for field in non_empty_fields:
            safe_set(self._source, self._target, field)

    def __filter_subfilter_fields(self):
        for filter, fields in self._subfilter_fields.items():
            non_empty_fields = [field for field in fields
                                if not self._is_empty(field)]
            for field in non_empty_fields:
                safe_set_with_filter(
                    self._source, self._target, filter, field, **self.__kwargs)

    def __filter_subfilter_lists(self):
        for filter, fields in self._listsubfilter_fields.items():
            non_empty_fields = [field for field in fields
                                if not self._is_empty(field)]
            for field in non_empty_fields:
                safe_set_many_with_filter(
                    self._source, self._target, filter, field, **self.__kwargs)
