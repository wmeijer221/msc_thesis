from typing import Callable, Any
from python_proj.utils.util import get_nested
from dataclasses import dataclass


class Feature:
    """
    Base class for data features.
    """

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_feature(self, entry: dict) -> Any:
        raise NotImplementedError()


class SlidingWindowFeature(Feature):
    def add_entry(self, entry: dict):
        raise NotImplementedError()

    def remove_entry(self, entry: dict):
        raise NotImplementedError()


class IsMerged(Feature):
    """The dependent variable; whether the pull request is merged."""

    def get_feature(self, entry: dict) -> bool:
        return entry["merged"]


@dataclass
class PullRequestSuccess:
    merged: int = 0
    unmerged: int = 0

    def get_total(self):
        return self.merged + self.unmerged

    def get_success_rate(self):
        self.merged / (self.merged + self.unmerged)


def get_integrator_key(entry):
    return "merged_by" if entry["merged"] else "closed_by"
