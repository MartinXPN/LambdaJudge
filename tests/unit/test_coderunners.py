from pathlib import Path
from unittest import mock

import coderunners.scoring as scoring
import coderunners.util as util
import models


class TestUtil:
    def test_is_float(self):
        assert util.is_float("3.4") is True
        assert util.is_float("not float") is False

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_save_code(self, mock_file: mock.MagicMock):
        save_dir = Path('/tmp/mydir')
        code = {'main.cpp': 'Hello', 'another.cpp': 'World'}

        saved_paths = util.save_code(save_dir, code)
        assert saved_paths == [Path('/tmp/mydir/main.cpp'), Path('/tmp/mydir/another.cpp')]

        mock_file.return_value.write.assert_has_calls([mock.call('Hello'), mock.call('World')])


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

        test_results = [models.RunResult(status=models.Status.OK, score=100, **
                                         self.RUN_RESULT_KWARGS) for _ in range(6)]

        scorer = scoring.SubtaskScorer(test_groups)

        assert scorer.score(test_results) == (100, [20, 20, 15, 15, 15, 15])

        test_results[0].status = models.Status.WA

        assert scorer.score(test_results) == (60, [0, 0, 15, 15, 15, 15])

    def test_subtask_scorer_with_points_per_test(self):
        test_groups = [
            models.TestGroup(points=0, points_per_test=20, count=2),
            models.TestGroup(points=0, points_per_test=15, count=4)
        ]

        test_results = [models.RunResult(status=models.Status.OK, score=100, **
                                         self.RUN_RESULT_KWARGS) for _ in range(6)]
        test_results[0].status = models.Status.WA

        scorer = scoring.SubtaskScorer(test_groups)

        assert scorer.score(test_results) == (80, [0, 20, 15, 15, 15, 15])
