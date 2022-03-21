from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional

from models import Status, TestGroup, RunResult


class AbstractScorer(ABC):
    @abstractmethod
    def get_score(self, test_results: list[RunResult]) -> float:
        ...

    @staticmethod
    def from_request(test_groups: Optional[list[TestGroup]] = None) -> 'AbstractScorer':
        return SubtaskScorer(test_groups=test_groups) if test_groups else PerTestScorer()


class PerTestScorer(AbstractScorer):
    def get_score(self, test_results: list[RunResult]) -> float:
        test_scores = [t.score for t in test_results]
        return sum(test_scores) / len(test_scores)


@dataclass
class SubtaskScorer(AbstractScorer):
    test_groups: list[TestGroup]

    def get_score(self, test_results: list[RunResult]) -> float:
        score = 0
        results = test_results[:]
        for test_group in self.test_groups:
            oks = [int(test_result.status == Status.OK) for test_result in results[:test_group.count]]
            score += sum(oks) * test_group.points_per_test + min(oks) * test_group.points
            del results[:test_group.count]
        return score
