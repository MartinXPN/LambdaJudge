from abc import abstractmethod

from models import Status, TestGroup


class AbstractScorer:
    @abstractmethod
    def get_score(self, test_results: list[Status], test_scores: list[int]) -> float:
        raise NotImplementedError()
    
class PerTestScorer(AbstractScorer):
    def get_score(self, test_results: list[Status], test_scores: list[int]) -> float:
        return sum(test_scores) / len(test_scores)

class SubtaskScorer(AbstractScorer):
    def __init__(self, test_groups: list[TestGroup]):
        self.test_groups = test_groups
        
    def get_score(self, test_results: list[Status], test_scores: list[int]) -> float:
        score = 0
        test_results = test_results[:]
        for test_group in self.test_groups:
            oks = [int(test_result.status == Status.OK) for test_result in test_results[:test_group.count]]
            score += sum(oks) * test_group.points_per_test + min(oks) * test_group.points
            del test_results[:test_group.count]
        return score
