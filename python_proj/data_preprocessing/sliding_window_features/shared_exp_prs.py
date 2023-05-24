
from typing import Any
from python_proj.data_preprocessing.sliding_window_features.base import *


class SubmitterExperienceEcosystemPullRequestSuccessRate(SlidingWindowFeature):
    def __handle(self, entry: dict, sign: int):
        pass

    def add_entry(self, entry: dict):
        return super().add_entry(entry)

    def remove_entry(self, entry: dict):
        return super().remove_entry(entry)

    def get_feature(self, entry: dict) -> Any:
        return super().get_feature(entry)


class SubmitterExperienceEcosystemPullRequestCount(SubmitterExperienceEcosystemPullRequestSuccessRate):
    def get_feature(self, entry: dict) -> Any:
        pass
