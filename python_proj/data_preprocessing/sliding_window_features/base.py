from typing import Any
from dataclasses import dataclass


class Feature:
    """
    Base class for data features.
    """

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_feature(self, entry: dict) -> Any:
        raise NotImplementedError()

    def is_valid_entry(self, entry: dict) -> bool:
        return True


class SlidingWindowFeature(Feature):
    def add_entry(self, entry: dict):
        raise NotImplementedError()

    def remove_entry(self, entry: dict):
        raise NotImplementedError()


class PullRequestIsMerged(Feature):
    """The dependent variable; whether the pull request is merged."""

    def get_feature(self, entry: dict) -> bool:
        return entry["merged"]


class PostRunFeature:
    def late_init(self):
        """called to do a late init."""
        raise NotImplementedError()


@dataclass
class PullRequestSuccess:
    merged: int = 0
    unmerged: int = 0

    def get_total(self) -> int:
        return self.merged + self.unmerged

    def get_success_rate(self) -> float:
        if (total := self.get_total()) == 0:
            return 0.0
        else:
            return self.merged / total
