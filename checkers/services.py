import gzip
from typing import Optional, List, Dict

import boto3

from checkers import Checker
from coderunners import CodeRunner, CodeRunRequest
from models import Status, SubmissionResult, TestCase, RunResult

s3 = boto3.resource('s3')
aws_lambda = boto3.client('lambda')


def check_equality(code: Dict[str, str], language: str, memory_limit: int, time_limit: int,
                   problem: Optional[str], test_cases: Optional[List[TestCase]],
                   aggregate_results: bool, return_outputs: bool, return_compile_outputs: bool,
                   comparison_mode: str, float_precision: float, delimiter: Optional[str]) -> SubmissionResult:
    print('checking...:', locals())
    if problem:
        gzipped_tests = s3.Object('lambda-judge-bucket', f'problems/{problem}.gz').get()['Body'].read()
        json_tests = gzip.decompress(gzipped_tests).decode('utf-8')
        test_cases = TestCase.schema().loads(json_tests, many=True)

    test_inputs = [t.input for t in test_cases]
    test_targets = [t.target for t in test_cases]
    assert len(test_inputs) == len(test_targets)

    coderunner = CodeRunner.from_language(language=language)
    res = coderunner.invoke(aws_lambda, request=CodeRunRequest(
        code=code, language=language,
        memory_limit=memory_limit, time_limit=time_limit,
        program_inputs=test_inputs
    ))

    compilation: RunResult = RunResult.from_json(res['compilation'])
    print('Compilation:', compilation)
    if compilation.status != Status.OK:
        return SubmissionResult(status=compilation.status,
                                memory=compilation.memory, time=compilation.time, score=0,
                                compile_outputs=(compilation.outputs or '') + '\n' + (compilation.errors or ''))

    test_results: List[RunResult] = RunResult.schema().loads(res['results'], many=True)
    print('test_results:', test_results)
    checker = Checker.from_mode(comparison_mode, float_precision=float_precision, delimiter=delimiter)

    for i, t, r in zip(test_inputs, test_targets, test_results):
        if r.status == Status.OK and not checker.is_correct(inputs=t, output=r.outputs, target=t):
            r.status = Status.WA

    # Aggregate all the results across test cases
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    status = Status.OK if failed_test is None else test_results[failed_test].status
    nb_success = sum(t.status == Status.OK for t in test_results)
    max_memory = max(t.memory for t in test_results)
    max_time = max(t.time for t in test_results)
    return SubmissionResult(
        status=status if aggregate_results else [t.status for t in test_results],
        memory=max_memory if aggregate_results else [t.memory for t in test_results],
        time=max_time if aggregate_results else [t.time for t in test_results],
        score=100 * nb_success / len(test_inputs),
        outputs=[(t.outputs or '') + '\n' + (t.errors or '') for t in test_results] if return_outputs else None,
        compile_outputs=compilation.outputs if return_compile_outputs else None)
