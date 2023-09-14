from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, getcontext

from models import RunResult, Status, TestGroup

# Setting the precision
precision = 50
getcontext().prec = precision


class Scorer(ABC):
    @abstractmethod
    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        ...

    @staticmethod
    def from_request(test_groups: list[TestGroup] | None = None) -> 'Scorer':
        return SubtaskScorer(test_groups=test_groups) if test_groups else PerTestScorer()


class PerTestScorer(Scorer):
    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        length = Decimal(len(test_results))
        test_scores = [Decimal(t.score) / length for t in test_results]
        return float(sum(test_scores)), [float(score) for score in test_scores]


@dataclass
class SubtaskScorer(Scorer):
    test_groups: list[TestGroup]

    def score(self, test_results: list[RunResult]) -> tuple[float, list[float]]:
        scores = []
        results = test_results[:]
        for test_group in self.test_groups:
            oks = [int(test_result.status == Status.OK) for test_result in results[:test_group.count]]
            points_per_test = (
                Decimal(test_group.points_per_test) or
                Decimal(min(oks)) * (Decimal(test_group.points) / test_group.count)
            )
            scores += [float(points_per_test * ok) for ok in oks]
            del results[:test_group.count]
        return float(sum(scores)), scores
