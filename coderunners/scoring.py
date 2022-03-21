from abc import abstractmethod, ABC
from dataclasses import dataclass

from models import Status, TestGroup


class AbstractScorer(ABC):
    @abstractmethod
    def get_score(self, test_results: list[Status], test_scores: list[float]) -> float:
        raise NotImplementedError()
    
    @staticmethod
    def from_request(test_groups) -> 'AbstractScorer':
        return SubtaskScorer(test_groups=test_groups) if test_groups else PerTestScorer()
    
class PerTestScorer(AbstractScorer):
    def get_score(self, test_results: list[Status], test_scores: list[float]) -> float:
        return sum(test_scores) / len(test_scores)

@dataclass
class SubtaskScorer(AbstractScorer):
    test_groups: list[TestGroup] = None
    
    def get_score(self, test_results: list[Status], test_scores: list[float]) -> float:
        score = 0
        test_results = test_results[:]
        for test_group in self.test_groups:
            oks = [int(test_result.status == Status.OK) for test_result in test_results[:test_group.count]]
            score += sum(oks) * test_group.points_per_test + min(oks) * test_group.points
            del test_results[:test_group.count]
        return score
