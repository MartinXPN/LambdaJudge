import coderunners.scoring as scoring
import models


class TestScoring:

    RUN_RESULT_KWARGS = {'memory': 1, 'time': 1, 'return_code': 0}

    def test_per_test_scorer(self):
        scorer = scoring.PerTestScorer()

        test_results = [
            models.RunResult(status=models.Status.WA, score=20, **self.RUN_RESULT_KWARGS),
            models.RunResult(status=models.Status.OK, score=100, **self.RUN_RESULT_KWARGS),
        ]
        assert scorer.score(test_results) == (60, [10, 50])

    def test_subtask_scorer_with_points(self):

        test_groups = [
            models.TestGroup(points=40, points_per_test=0, count=2),
            models.TestGroup(points=60, points_per_test=0, count=4)
        ]

        test_results = [models.RunResult(
            status=models.Status.OK, score=100, **self.RUN_RESULT_KWARGS
        ) for _ in range(6)]

        scorer = scoring.SubtaskScorer(test_groups)

        assert scorer.score(test_results) == (100, [20, 20, 15, 15, 15, 15])
        test_results[0].status = models.Status.WA
        assert scorer.score(test_results) == (60, [0, 0, 15, 15, 15, 15])

    def test_subtask_scorer_with_points_per_test(self):
        test_groups = [
            models.TestGroup(points=0, points_per_test=20, count=2),
            models.TestGroup(points=0, points_per_test=15, count=4)
        ]

        test_results = [models.RunResult(
            status=models.Status.OK, score=100, **self.RUN_RESULT_KWARGS
        ) for _ in range(6)]
        test_results[0].status = models.Status.WA
        scorer = scoring.SubtaskScorer(test_groups)
        assert scorer.score(test_results) == (80, [0, 20, 15, 15, 15, 15])
