import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import coderunners.scoring as scoring
import coderunners.util as util
import models


class TestUtil:
    def test_is_float(self):
        assert util.is_float('3.4') is True
        assert util.is_float('not float') is False
        assert util.is_float('NaN') is True
        assert util.is_float('4') is True

    def test_save_code(self):
        code = {
            'main.cpp': 'File 1',
            'another.cpp': 'File 2',
            'dir': {
                'third.cpp': 'File 3'
            }
        }
        with TemporaryDirectory() as save_dir:
            save_dir = Path(save_dir)
            saved_paths = util.save_code(save_dir, code)
            assert saved_paths == [save_dir / 'main.cpp', save_dir / 'another.cpp', save_dir / 'dir' / 'third.cpp']

            # Assert the files have been created successfully
            with open(save_dir / 'main.cpp') as f:
                assert f.read() == 'File 1'
            with open(save_dir / 'another.cpp') as f:
                assert f.read() == 'File 2'
            with open(save_dir / 'dir' / 'third.cpp') as f:
                assert f.read() == 'File 3'

            # Assert that redundant files do not exist
            assert not (save_dir / 'hello.py').exists()
            assert not (save_dir / 'main').is_dir()
            assert (save_dir / 'dir').is_dir()

    def test_save_code_fails(self):
        """ Anything other than string: string or string: dict should fail """
        code = {'hello.py': ['something', 'something else']}
        with pytest.raises(TypeError):
            with TemporaryDirectory() as save_dir:
                save_dir = Path(save_dir)
                # noinspection PyTypeChecker
                util.save_code(save_dir, code)

    def test_return_code_to_status(self):
        assert util.return_code2status.get(137) == 'SIGKILL'


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
