import glob
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict

import boto3

from checkers import Checker
from models import Status, SubmissionResult, TestCase, CodeRunRequest, TestResult
from util import extract_s3_zip

ROOT = Path('/tmp/')
s3 = boto3.resource('s3')
bucket = s3.Bucket('lambda-judge-bucket')
aws_lambda = boto3.client('lambda')


def check_equality(code: Dict[str, str], language: str, memory_limit: int, time_limit: int,
                   problem: Optional[str], test_cases: Optional[List[TestCase]],
                   return_outputs: bool, return_compile_outputs: bool, stop_on_first_fail: bool,
                   comparison_mode: str, float_precision: float, delimiter: Optional[str]) -> SubmissionResult:
    print('checking...:', locals())
    if problem:
        save_path = ROOT / f'{problem}.zip'
        extract_path = extract_s3_zip(bucket, bucket_path=f'problems/{problem}.zip', save_path=save_path, cached=True)
        test_inputs = [Path(p).read_text() for p in sorted(glob.glob(f'{extract_path}/*.i.txt'))]
        test_targets = [Path(p).read_text() for p in sorted(glob.glob(f'{extract_path}/*.o.txt'))]
        # Cleanup
        shutil.rmtree(save_path, ignore_errors=True)
        shutil.rmtree(extract_path, ignore_errors=True)

    elif test_cases:
        test_inputs = [t.input for t in test_cases]
        test_targets = [t.target for t in test_cases]
    else:
        raise ValueError('Either `problem` or `test_cases` need to be provided!')

    # TODO: is there a better way to name the function?
    res = aws_lambda.invoke(FunctionName='lambdaJudge-CodeRunner-tJGzU2gt8KXd', Payload=CodeRunRequest(
        code=code, language=language, memory_limit=memory_limit, time_limit=time_limit,
        test_inputs=test_inputs
    ).to_json())['Payload'].read().decode('utf-8')
    print('res:', res)
    res = json.loads(res)

    compilation: TestResult = TestResult.from_json(res['compilation'])
    print('Compilation:', compilation)
    if compilation.status == Status.COMPILATION_ERROR:
        return SubmissionResult(status=Status.COMPILATION_ERROR,
                                memory=res.memory[0], time=res.time[0], score=0,
                                compile_outputs=res.compile_outputs)

    test_results: List[TestResult] = TestResult.schema().loads(res['results'], many=True)
    print('test_results:', test_results)
    checker = Checker.from_mode(comparison_mode, float_precision=float_precision, delimiter=delimiter)
    assert len(test_inputs) == len(test_targets) == len(test_results)
    for i, t, r in zip(test_inputs, test_targets, test_results):
        if r.status == Status.OK and not checker.is_correct(inputs=t, output=r.outputs, target=t):
            r.status = Status.WA

    # Aggregate all the results across test cases
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    nb_success = sum(x.status == Status.OK for x in test_results)
    max_memory = max(x.memory for x in test_results)
    max_time = max(x.time for x in test_results)
    return SubmissionResult(
        status=Status.OK if failed_test is None else test_results[failed_test].status,
        memory=max_memory,
        time=max_time,
        score=100 * nb_success / len(test_inputs),
        outputs=[x.outputs for x in test_results] if return_outputs else None,
        compile_outputs=compilation.outputs if return_compile_outputs else None)
