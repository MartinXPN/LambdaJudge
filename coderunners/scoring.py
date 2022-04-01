from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from models import RunResult, Status, TestGroup


class AbstractScorer(ABC):
    @abstractmethod
    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        ...

    @staticmethod
    def from_request(test_groups: Optional[list[TestGroup]] = None) -> 'AbstractScorer':
        return SubtaskScorer(test_groups=test_groups) if test_groups else PerTestScorer()


class PerTestScorer(AbstractScorer):
    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        test_scores = [t.score / len(test_results) for t in test_results]
        return sum(test_scores), test_scores


@dataclass
class SubtaskScorer(AbstractScorer):
    test_groups: list[TestGroup]

    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        scores = []
        results = test_results[:]
        for test_group in self.test_groups:
            oks = [int(test_result.status == Status.OK) for test_result in results[:test_group.count]]
            points_per_test = test_group.points_per_test or min(oks) * (test_group.points / test_group.count)
            scores += [points_per_test * ok for ok in oks]
            del results[:test_group.count]
        return sum(scores), scores
