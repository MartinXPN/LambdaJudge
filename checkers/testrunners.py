from dataclasses import dataclass
from pathlib import Path
from typing import List

from checkers import EqualityChecker
from models import SubmissionResult, Status
from process import Process


@dataclass
class TestRunner:
    executable_path: Path
    time_limit: float
    memory_limit_mb: int
    checker: EqualityChecker
    stop_on_first_fail: bool

    def from_files(self, input_paths: List[Path], target_paths: List[Path]) -> List[SubmissionResult]:
        all_inputs, all_targets = [], []
        for input_file, target_file in zip(input_paths, target_paths):
            print('Test files:', input_file, target_file)
            with open(input_file, 'r') as f:
                all_inputs.append(f.read())
            with open(target_file, 'r') as f:
                all_targets.append(f.read())

        return self.from_tests(all_inputs, all_targets)

    def from_tests(self, inputs: List[str], targets: List[str]) -> List[SubmissionResult]:
        test_results = []
        for test_input, test_target in zip(inputs, targets):
            result = self.run_test(test_input=test_input, test_target=test_target)
            test_results.append(result)
            if result.status != Status.OK and self.stop_on_first_fail:
                break
        return test_results

    def run_test(self, test_input, test_target) -> SubmissionResult:
        test_res = Process(f'echo "{test_input}" | {self.executable_path}',
                           timeout=self.time_limit,
                           memory_limit_mb=self.memory_limit_mb).run()
        if test_res.return_code != 0 or (not test_res.outputs and test_res.errors):
            print('Errs:', test_res.errors)
            print('Return code:', test_res.return_code)
            return SubmissionResult(
                status=Status.MLE if test_res.max_rss > self.memory_limit_mb or test_res.errors == Status.MLE
                else Status.TLE if 1.1 * test_res.total_time > self.time_limit or test_res.errors == Status.TLE
                else Status.RUNTIME_ERROR,
                memory=test_res.max_rss,
                time=test_res.total_time,
                score=0,
                outputs=test_res.outputs,
                compile_outputs=None
            )

        output = test_res.outputs.strip()
        is_same = self.checker.is_same(output, test_target)
        return SubmissionResult(
            status=Status.OK if is_same else Status.WA,
            memory=test_res.max_rss,
            time=test_res.total_time,
            score=0 if is_same else 100,
            outputs=test_res.outputs,
            compile_outputs=None
        )
